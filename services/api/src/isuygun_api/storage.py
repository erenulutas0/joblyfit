"""Profil kalıcılığı — depolama arayüzü ve SQLite uygulaması.

**ADR-001'in hedefi PostgreSQL'dir ve bu modül onu değiştirmez.** Burada iki
şey ayrılır: API katmanının konuştuğu *arayüz* (:class:`ProfileStore`) ve o
arayüzün *uygulaması*. PostgreSQL uygulaması yazıldığında değişecek tek yer
:func:`open_store`'dur; API ve arayüz katmanı hiç dokunulmadan çalışır.

SQLite'ın şimdi seçilmesinin gerekçesi teknik değil, **doğrulanabilirlik**:
bu makinede Docker daemon çalışmıyor, dolayısıyla PostgreSQL kodu yazılsa bile
koşturulup sınanamazdı. Çalıştığı görülmemiş altyapı kodu teslim etmek, çalışan
bir şey teslim etmek değildir.

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

    def close(self) -> None:
        self._db.close()


class MemoryProfileStore:
    """Kalıcılık yok. Testlerde ve disk yazılamadığında kullanılır."""

    def __init__(self) -> None:
        self._profiles: dict[str, CareerProfile] = {}
        self._suggestions: dict[str, list[dict]] = {}

    def load(self, profile_id: str) -> CareerProfile:
        return self._profiles.get(profile_id) or CareerProfile(profile_id=profile_id)

    def save(self, profile: CareerProfile) -> None:
        self._profiles[profile.profile_id] = profile

    def load_suggestions(self, profile_id: str) -> list[dict]:
        return list(self._suggestions.get(profile_id, []))

    def save_suggestions(self, profile_id: str, items: list[dict]) -> None:
        self._suggestions[profile_id] = list(items)

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


def open_store(path: Path | None) -> ProfileStore:
    """Kalıcı depoyu açar; açılamazsa belleğe düşer.

    Disk yazılamadığında uygulamanın **çalışmaya devam etmesi** tercih edilir —
    ama bu sessiz olmaz: çağıran taraf hangi depoyu aldığını görür ve arayüzde
    belirtir.
    """
    if path is None:
        return MemoryProfileStore()
    try:
        return SqliteProfileStore(path=path)
    except Exception:
        return MemoryProfileStore()
