"""Profil kalıcılığı — depolama arayüzü ve uygulamaları.

**ADR-001'in hedefi PostgreSQL'dir ve bu modül onu değiştirmez.** Burada iki
şey ayrılır: API katmanının konuştuğu *arayüz* (:class:`ProfileStore`) ve o
arayüzün *uygulaması*. PostgreSQL uygulaması yazıldığında değişecek tek yer
:func:`open_store`'dur; API ve arayüz katmanı hiç dokunulmadan çalışır.

Üç uygulama var ve :func:`open_store` aralarında **düşerek** seçer:
PostgreSQL (ADR-001 hedefi) → SQLite (dosya) → bellek. Zincirin amacı,
veritabanı erişilemez olduğunda uygulamanın çalışmaya devam etmesidir; ama bu
sessiz olmaz — arayüz hangi deponun kullanıldığını gösterir.

Kalıcı kılınan şey **yalnızca kullanıcı profilidir**. İlan korpusu burada
tutulmaz: o dış kaynaktan gelir, tazeliği vardır ve `.cache/` altında ayrı
yönetilir (D-024).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from isuygun_core.domain import CareerProfile, ProfileFact, VerificationState

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
    profile_id      TEXT PRIMARY KEY,
    occupation_ids  TEXT NOT NULL DEFAULT ''
);

-- İsimli profillerin üst verisi (D-045). Kullanıcı birden çok profil tutar
-- ("Eren-Computer Engineer", "Eren-Mavi yaka") ve aralarında geçiş yapar.
-- Buradaki alanlar matching'e GİRMEZ; yalnızca onboarding tercihleri ve
-- gösterim içindir. `attrs` esnek bir JSON kovasıdır (bölge, özel anahtar
-- kelimeler) — şema her yeni tercih için değişmesin diye.
CREATE TABLE IF NOT EXISTS profile_meta (
    profile_id  TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    collar      TEXT,
    attrs       TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (profile_id) REFERENCES profile(profile_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS profile_fact (
    profile_id   TEXT NOT NULL,
    key          TEXT NOT NULL,
    category     TEXT NOT NULL,
    verification TEXT NOT NULL,
    years        REAL,
    PRIMARY KEY (profile_id, key),
    FOREIGN KEY (profile_id) REFERENCES profile(profile_id) ON DELETE CASCADE
);

-- CV'den gelen ama kullanıcı onayından geçmemiş öneriler. Profil tablosundan
-- ayrı tutulur: bunlar **profil verisi değildir** ve matching'e giremez (T-016).
CREATE TABLE IF NOT EXISTS cv_suggestion (
    profile_id  TEXT NOT NULL,
    key         TEXT NOT NULL,
    payload     TEXT NOT NULL,
    PRIMARY KEY (profile_id, key)
);
"""


class ProfileStore(Protocol):
    """API katmanının gördüğü sözleşme. Uygulamadan bağımsızdır."""

    def load(self, profile_id: str) -> CareerProfile: ...
    def save(self, profile: CareerProfile) -> None: ...
    def load_suggestions(self, profile_id: str) -> list[dict]: ...
    def save_suggestions(self, profile_id: str, items: list[dict]) -> None: ...
    # -- isimli profiller (D-045) --
    def list_profiles(self) -> list[dict]: ...
    def save_meta(self, meta: dict) -> None: ...
    def delete_profile(self, profile_id: str) -> None: ...
    def close(self) -> None: ...


@dataclass
class SqliteProfileStore:
    """Dosya tabanlı kalıcılık. Süreç kapansa da profil kalır."""

    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False: uvicorn istekleri thread pool'da koşuyor.
        # Yazma işlemleri kısa ve seyrek; SQLite'ın kendi kilidi yeterli.
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.executescript(SCHEMA)
        self._db.commit()

    # -- profil ------------------------------------------------------------

    def load(self, profile_id: str) -> CareerProfile:
        row = self._db.execute(
            "SELECT occupation_ids FROM profile WHERE profile_id = ?", (profile_id,)
        ).fetchone()
        occupations = tuple(
            o for o in (row[0].split("\x1f") if row and row[0] else []) if o
        )
        facts = tuple(
            ProfileFact(
                key=k,
                category=c,
                verification=_as_verification(v),
                years=y,
            )
            for k, c, v, y in self._db.execute(
                "SELECT key, category, verification, years FROM profile_fact "
                "WHERE profile_id = ? ORDER BY key",
                (profile_id,),
            )
        )
        return CareerProfile(profile_id=profile_id, occupation_ids=occupations, facts=facts)

    def save(self, profile: CareerProfile) -> None:
        """Profili bütün olarak yazar.

        Alan alan güncelleme yerine tam yazım tercih edildi: profil küçüktür ve
        kısmi güncelleme, silinen bir alanın veritabanında kalması gibi sessiz
        tutarsızlıklara açıktır.
        """
        with self._db:
            self._db.execute(
                "INSERT INTO profile (profile_id, occupation_ids) VALUES (?, ?) "
                "ON CONFLICT(profile_id) DO UPDATE SET occupation_ids = excluded.occupation_ids",
                (profile.profile_id, "\x1f".join(profile.occupation_ids)),
            )
            self._db.execute(
                "DELETE FROM profile_fact WHERE profile_id = ?", (profile.profile_id,)
            )
            self._db.executemany(
                "INSERT INTO profile_fact (profile_id, key, category, verification, years) "
                "VALUES (?, ?, ?, ?, ?)",
                [(profile.profile_id, f.key, f.category, f.verification, f.years)
                 for f in profile.facts],
            )

    # -- CV önerileri ------------------------------------------------------

    def load_suggestions(self, profile_id: str) -> list[dict]:
        import json

        return [
            json.loads(p)
            for (p,) in self._db.execute(
                "SELECT payload FROM cv_suggestion WHERE profile_id = ? ORDER BY key",
                (profile_id,),
            )
        ]

    def save_suggestions(self, profile_id: str, items: list[dict]) -> None:
        import json

        with self._db:
            self._db.execute(
                "DELETE FROM cv_suggestion WHERE profile_id = ?", (profile_id,)
            )
            self._db.executemany(
                "INSERT INTO cv_suggestion (profile_id, key, payload) VALUES (?, ?, ?)",
                [(profile_id, i["key"], json.dumps(i, ensure_ascii=False))
                 for i in items],
            )

    # -- isimli profiller (D-045) ------------------------------------------

    def list_profiles(self) -> list[dict]:
        import json

        rows = self._db.execute(
            "SELECT profile_id, name, collar, attrs, created_at "
            "FROM profile_meta ORDER BY created_at"
        ).fetchall()
        return [
            {"id": pid, "name": name, "collar": collar,
             "attrs": json.loads(attrs or "{}"), "created_at": created}
            for pid, name, collar, attrs, created in rows
        ]

    def save_meta(self, meta: dict) -> None:
        import json

        with self._db:
            # FK için profil satırı var olmalı; yeni profilde henüz save()
            # çağrılmamış olabilir.
            self._db.execute(
                "INSERT OR IGNORE INTO profile (profile_id) VALUES (?)", (meta["id"],)
            )
            self._db.execute(
                "INSERT INTO profile_meta (profile_id, name, collar, attrs, created_at) "
                "VALUES (?, ?, ?, ?, ?) ON CONFLICT(profile_id) DO UPDATE SET "
                "name = excluded.name, collar = excluded.collar, attrs = excluded.attrs",
                (meta["id"], meta["name"], meta.get("collar"),
                 json.dumps(meta.get("attrs", {}), ensure_ascii=False),
                 meta.get("created_at", "")),
            )

    def delete_profile(self, profile_id: str) -> None:
        with self._db:
            # ON DELETE CASCADE fact/meta'yı siler; cv_suggestion FK'siz, elle.
            self._db.execute("DELETE FROM cv_suggestion WHERE profile_id = ?", (profile_id,))
            self._db.execute("DELETE FROM profile WHERE profile_id = ?", (profile_id,))

    def close(self) -> None:
        self._db.close()


class MemoryProfileStore:
    """Kalıcılık yok. Testlerde ve disk yazılamadığında kullanılır."""

    def __init__(self) -> None:
        self._profiles: dict[str, CareerProfile] = {}
        self._suggestions: dict[str, list[dict]] = {}
        self._meta: dict[str, dict] = {}

    def load(self, profile_id: str) -> CareerProfile:
        return self._profiles.get(profile_id) or CareerProfile(profile_id=profile_id)

    def save(self, profile: CareerProfile) -> None:
        self._profiles[profile.profile_id] = profile

    def load_suggestions(self, profile_id: str) -> list[dict]:
        return list(self._suggestions.get(profile_id, []))

    def save_suggestions(self, profile_id: str, items: list[dict]) -> None:
        self._suggestions[profile_id] = list(items)

    def list_profiles(self) -> list[dict]:
        return sorted(self._meta.values(), key=lambda m: m.get("created_at", ""))

    def save_meta(self, meta: dict) -> None:
        self._meta[meta["id"]] = dict(meta)

    def delete_profile(self, profile_id: str) -> None:
        self._profiles.pop(profile_id, None)
        self._suggestions.pop(profile_id, None)
        self._meta.pop(profile_id, None)

    def close(self) -> None:
        pass


_VALID: frozenset[str] = frozenset({"unverified", "user_asserted", "verified"})


def _as_verification(value: str) -> VerificationState:
    """Veritabanından gelen değeri doğrular.

    Tanınmayan bir değer **en güvenli** duruma düşürülür: doğrulanmamış.
    Sessizce `verified` kabul etmek, D-012'nin bütün gate mantığını veritabanı
    üzerinden atlatılabilir yapardı.
    """
    return value if value in _VALID else "unverified"  # type: ignore[return-value]


@dataclass
class PostgresProfileStore:
    """ADR-001'in hedef uygulaması.

    SQLite sürümüyle **aynı semantiği** taşır: kaydetme tam yazımdır, öneriler
    ayrı tabloda durur ve tanınmayan bir doğrulama değeri en güvenli duruma
    düşer. Şemadaki CHECK kısıtı ikinci bir kattır; ikisi de tutmalıdır çünkü
    veritabanına doğrudan yazan bir yol uygulama katmanını atlar.
    """

    dsn: str

    def __post_init__(self) -> None:
        import psycopg

        # `connect_timeout` ZORUNLU: Postgres kapalıyken (docker up değil)
        # bağlantı "refused" yerine asılı kalabiliyordu (localhost IPv6 gecikmesi)
        # ve `STORE = Store()` import'ta donuyor, sunucu hiç açılmıyordu. Düşme
        # zinciri (Postgres → SQLite → bellek, D-027) ancak connect HIZLI
        # başarısız olursa çalışır (D-048).
        self._db = psycopg.connect(self.dsn, autocommit=True, connect_timeout=3)

    def load(self, profile_id: str) -> CareerProfile:
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT occupation_ids FROM profile WHERE profile_id = %s", (profile_id,)
            )
            row = cur.fetchone()
            occupations = tuple(row[0]) if row and row[0] else ()

            cur.execute(
                "SELECT key, category, verification, years FROM profile_fact "
                "WHERE profile_id = %s ORDER BY key",
                (profile_id,),
            )
            facts = tuple(
                ProfileFact(key=k, category=c, verification=_as_verification(v), years=y)
                for k, c, v, y in cur.fetchall()
            )
        return CareerProfile(profile_id=profile_id, occupation_ids=occupations, facts=facts)

    def save(self, profile: CareerProfile) -> None:
        # Tek işlem: sil + ekle yarıda kalırsa profil boş kalmamalı.
        with self._db.transaction(), self._db.cursor() as cur:
            cur.execute(
                "INSERT INTO profile (profile_id, occupation_ids) VALUES (%s, %s) "
                "ON CONFLICT (profile_id) DO UPDATE "
                "SET occupation_ids = EXCLUDED.occupation_ids, updated_at = now()",
                (profile.profile_id, list(profile.occupation_ids)),
            )
            cur.execute(
                "DELETE FROM profile_fact WHERE profile_id = %s", (profile.profile_id,)
            )
            if profile.facts:
                cur.executemany(
                    "INSERT INTO profile_fact "
                    "(profile_id, key, category, verification, years) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    [(profile.profile_id, f.key, f.category, f.verification, f.years)
                     for f in profile.facts],
                )

    def load_suggestions(self, profile_id: str) -> list[dict]:
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT payload FROM cv_suggestion WHERE profile_id = %s ORDER BY key",
                (profile_id,),
            )
            return [r[0] for r in cur.fetchall()]

    def save_suggestions(self, profile_id: str, items: list[dict]) -> None:
        import json

        with self._db.transaction(), self._db.cursor() as cur:
            cur.execute("DELETE FROM cv_suggestion WHERE profile_id = %s", (profile_id,))
            if items:
                cur.executemany(
                    "INSERT INTO cv_suggestion (profile_id, key, payload) "
                    "VALUES (%s, %s, %s::jsonb)",
                    [(profile_id, i["key"], json.dumps(i, ensure_ascii=False))
                     for i in items],
                )

    def list_profiles(self) -> list[dict]:
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT profile_id, name, collar, attrs, created_at "
                "FROM profile_meta ORDER BY created_at"
            )
            return [
                {"id": pid, "name": name, "collar": collar,
                 "attrs": attrs or {}, "created_at": str(created or "")}
                for pid, name, collar, attrs, created in cur.fetchall()
            ]

    def save_meta(self, meta: dict) -> None:
        import json

        with self._db.transaction(), self._db.cursor() as cur:
            cur.execute(
                "INSERT INTO profile (profile_id) VALUES (%s) ON CONFLICT DO NOTHING",
                (meta["id"],),
            )
            cur.execute(
                "INSERT INTO profile_meta (profile_id, name, collar, attrs) "
                "VALUES (%s, %s, %s, %s::jsonb) ON CONFLICT (profile_id) DO UPDATE SET "
                "name = EXCLUDED.name, collar = EXCLUDED.collar, attrs = EXCLUDED.attrs",
                (meta["id"], meta["name"], meta.get("collar"),
                 json.dumps(meta.get("attrs", {}), ensure_ascii=False)),
            )

    def delete_profile(self, profile_id: str) -> None:
        with self._db.transaction(), self._db.cursor() as cur:
            cur.execute("DELETE FROM cv_suggestion WHERE profile_id = %s", (profile_id,))
            cur.execute("DELETE FROM profile WHERE profile_id = %s", (profile_id,))

    def close(self) -> None:
        self._db.close()


def open_store(path: Path | None, dsn: str | None = None) -> ProfileStore:
    """Kalıcı depoyu açar; açılamazsa bir alt seçeneğe düşer.

    Sıra: PostgreSQL → SQLite → bellek. Veritabanı erişilemez olduğunda
    uygulamanın **çalışmaya devam etmesi** tercih edilir — ama bu sessiz olmaz:
    çağıran taraf hangi depoyu aldığını görür ve arayüz onu yazar.
    """
    if dsn:
        try:
            return PostgresProfileStore(dsn=dsn)
        except Exception:
            pass   # SQLite'a düş
    if path is None:
        return MemoryProfileStore()
    try:
        return SqliteProfileStore(path=path)
    except Exception:
        return MemoryProfileStore()
