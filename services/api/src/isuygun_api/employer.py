"""İşveren doğrudan ilan girişi — gönderim + moderasyon kuyruğu (D-078).

**Neden var:** ölçüm. Aggregator kaynakları ilan başına ortalama **1,3 şart**
veriyor (Careerjet'in 120 karakterlik özetinde 0,96'ya düşüyor) ve kanıt tavanı
(D-022) tek şartla en fazla "şartlı eşleşme" verdiği için bantlar tek bir
kovada yığılıyor. İşveren şartları **yapılandırılmış** girdiğinde ilan başına
5-6 şart olur ve bantlar gerçekten ayrışır. Yani bu, hacim değil **ayırt
edicilik** kazancıdır — hiçbir aggregator veremez.

**Neden hesap YOK:** e-posta gönderme altyapımız yok, dolayısıyla işverenin
kimliğini doğrulayamayız. Parola/oturum/sıfırlama içeren bir giriş sistemi
kurmak, doğrulayamadığımız bir kimlik için büyük bir güvenlik yüzeyi açmak
olurdu. Bunun yerine: **açık gönderim formu → moderasyon kuyruğu → onay**.
Onaylanmayan hiçbir ilan korpusa girmez. Bu, self-servis yayından yavaştır ve
öyle olması bilinçlidir.

**Ayrımcı ifade BLOKLANIR, yalnızca işaretlenmez.** Üçüncü taraf akışlarında
ayrımcı dili *işaretliyoruz* çünkü o ilanları biz yayımlamıyoruz, yalnızca
dizinliyoruz. Burada yayımcı BİZİZ; "her 28 Türkiye ilanından 1'inde ayrımcı
ifade var" diye ölçüm yayımlayan bir ürünün kendi panosunda aynı ifadeye izin
vermesi, iddiasını çürütür.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

_DDL = """
CREATE TABLE IF NOT EXISTS employer_postings(
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL,              -- pending | approved | rejected
  employer TEXT NOT NULL,
  contact TEXT NOT NULL,             -- işverenin bıraktığı iletişim (yayımlanmaz)
  title TEXT NOT NULL,
  city TEXT NOT NULL,
  description TEXT NOT NULL,
  apply_url TEXT,
  requirements TEXT NOT NULL,        -- JSON: [{key, kind}]
  salary_text TEXT,
  deadline TEXT,                     -- YYYY-MM-DD (son başvuru)
  work_arrangement TEXT,
  employment_type TEXT,
  experience_level TEXT,
  fairness TEXT,                     -- JSON: yumuşak uyarılar (kayda geçer)
  moderator_note TEXT,
  decided_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_emp_status ON employer_postings(status);
"""

#: `kind` alanı çekirdeğin beklediği değerlerle SINIRLI. Serbest metin kabul
#: etmek, bilinmeyen bir `kind`in ağırlık tablosunda sessizce 1.0'a düşmesi
#: demekti (KIND_WEIGHT.get(..., 1.0)) — yani "hard" yazım hatası şartı
#: yumuşatırdı.
GECERLI_KIND = ("hard", "required", "preferred")
GECERLI_ARRANGEMENT = ("remote", "hybrid", "onsite")
GECERLI_EMPLOYMENT = ("full_time", "part_time", "contract", "internship")
GECERLI_LEVEL = ("intern", "junior", "mid", "senior", "lead", "architect", "executive")

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _db_path() -> Path:
    ozel = os.getenv("ISUYGUN_EMPLOYER_DB")
    if ozel:
        return Path(ozel)
    return Path(__file__).resolve().parents[4] / ".data" / "employer.db"


def _db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        yol = _db_path()
        yol.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(yol), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(_DDL)
        _conn.commit()
    return _conn


def reset_for_tests() -> None:
    """Testler arası temiz durum. Yalnızca test yolunda çağrılır."""
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
            _conn = None


class Reddedildi(Exception):
    """Gönderim kabul edilmedi. ``sebep`` kullanıcıya gösterilir."""

    def __init__(self, sebep: str, kanit: str = "") -> None:
        super().__init__(sebep)
        self.sebep = sebep
        self.kanit = kanit


def submit(*, employer: str, contact: str, title: str, city: str,
           description: str, requirements: list[dict],
           apply_url: str | None = None, salary_text: str | None = None,
           deadline: str | None = None, work_arrangement: str | None = None,
           employment_type: str | None = None,
           experience_level: str | None = None) -> tuple[str, list[dict]]:
    """İlanı **kuyruğa** alır. Döner: ``(id, yumuşak_uyarılar)``.

    Onaylanana kadar hiçbir yerde görünmez. Ayrımcı ifade (hard) varsa
    ``Reddedildi`` fırlatır — kayda bile alınmaz, çünkü kaydetmek onu bir gün
    yanlışlıkla onaylanabilir kılar.
    """
    from isuygun_ingest import fairness

    def _kirp(s: str | None, n: int) -> str | None:
        if s is None:
            return None
        s = " ".join(str(s).split())
        return s[:n] or None

    employer = _kirp(employer, 120) or ""
    title = _kirp(title, 160) or ""
    city = _kirp(city, 80) or ""
    contact = _kirp(contact, 160) or ""
    description = " ".join(str(description or "").split())[:6000]

    for ad, deger in (("işveren adı", employer), ("ilan başlığı", title),
                      ("şehir", city), ("iletişim", contact)):
        if not deger:
            raise Reddedildi(f"{ad} zorunlu.")
    if len(description) < 80:
        raise Reddedildi(
            "İlan metni en az 80 karakter olmalı. Kısa metinden şart "
            "okunamıyor ve ilan 'değerlendirilemedi' yığınına düşer — "
            "kimseye faydası olmaz.")

    # AYRIMCI İFADE: yayımcı biz olduğumuz için burada BLOKLANIR.
    for f in fairness.scan(title, description):
        if f.severity == "hard":
            raise Reddedildi(
                "İlan metninde dışlayıcı bir ifade var ve bu panoda "
                "yayımlamıyoruz. İfadeyi kaldırıp tekrar gönderebilirsin. "
                f"Gerekçe: {f.note}",
                kanit=f.evidence)
    yumusak = [{"category": f.category, "note": f.note, "evidence": f.evidence}
               for f in fairness.scan(title, description)]

    temiz_req: list[dict] = []
    gorulen: set[str] = set()
    for r in (requirements or [])[:40]:
        key = str(r.get("key") or "").strip()
        kind = str(r.get("kind") or "required").strip()
        if not key or key in gorulen:
            continue
        if kind not in GECERLI_KIND:
            raise Reddedildi(f"Geçersiz şart türü: {kind!r}")
        gorulen.add(key)
        temiz_req.append({"key": key, "kind": kind})
    if not temiz_req:
        raise Reddedildi(
            "En az bir şart seçmelisin. Şartsız ilan, adayın kendini "
            "karşılaştırabileceği hiçbir şey sunmaz — bu panonun tek amacı o.")

    if deadline:
        try:
            date.fromisoformat(deadline)
        except ValueError:
            raise Reddedildi("Son başvuru tarihi YYYY-AA-GG biçiminde olmalı.")
    for ad, deger, gecerli in (("çalışma biçimi", work_arrangement, GECERLI_ARRANGEMENT),
                               ("istihdam türü", employment_type, GECERLI_EMPLOYMENT),
                               ("kıdem", experience_level, GECERLI_LEVEL)):
        if deger and deger not in gecerli:
            raise Reddedildi(f"Geçersiz {ad}: {deger!r}")

    pid = f"emp-{uuid.uuid4().hex[:16]}"
    with _lock:
        _db().execute(
            "INSERT INTO employer_postings(id, created_at, status, employer, contact,"
            " title, city, description, apply_url, requirements, salary_text, deadline,"
            " work_arrangement, employment_type, experience_level, fairness)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (pid, datetime.now(timezone.utc).isoformat(timespec="seconds"), "pending",
             employer, contact, title, city, description, _kirp(apply_url, 500),
             json.dumps(temiz_req, ensure_ascii=False), _kirp(salary_text, 120),
             deadline, work_arrangement, employment_type, experience_level,
             json.dumps(yumusak, ensure_ascii=False)))
        _db().commit()
    return pid, yumusak


def liste(status: str = "pending", limit: int = 200) -> list[dict]:
    with _lock:
        cur = _db().execute(
            "SELECT * FROM employer_postings WHERE status=? ORDER BY created_at DESC"
            " LIMIT ?", (status, max(1, min(500, limit))))
        return [dict(r) for r in cur.fetchall()]


def moderate(pid: str, action: str, note: str = "") -> bool:
    """``approve`` | ``reject``. Döner: kayıt bulundu mu."""
    if action not in ("approve", "reject"):
        raise ValueError(f"bilinmeyen eylem: {action!r}")
    yeni = "approved" if action == "approve" else "rejected"
    with _lock:
        cur = _db().execute(
            "UPDATE employer_postings SET status=?, moderator_note=?, decided_at=?"
            " WHERE id=? AND status='pending'",
            (yeni, " ".join(str(note or "").split())[:500],
             datetime.now(timezone.utc).isoformat(timespec="seconds"), pid))
        _db().commit()
        return cur.rowcount > 0


def to_postings() -> list:
    """Onaylı ilanları korpusa katılabilir ``NormalizedPosting`` listesine çevirir.

    Süresi geçmiş ilan DÖNMEZ: işverenin yazdığı son başvuru tarihi geçtiyse
    ilan ölüdür ve göstermek kullanıcının zamanını çalar. (Üçüncü taraf
    akışlarında böyle bir tarih genelde yok; orada 45 günlük tazelik penceresi
    aynı işi yapıyor — D-024.)
    """
    from isuygun_core.domain import JobPosting, Requirement
    from isuygun_ingest.lexicon import BY_KEY
    from isuygun_ingest.pipeline import NormalizedPosting, fold

    bugun = date.today()
    out = []
    for r in liste("approved", limit=500):
        if r["deadline"]:
            try:
                if date.fromisoformat(r["deadline"]) < bugun:
                    continue
            except ValueError:
                pass

        reqs = []
        kumeler: list[str] = []
        for item in json.loads(r["requirements"] or "[]"):
            term = BY_KEY.get(item["key"])
            if term is None:      # sözlükten kalkmış anahtar — sessizce atlanır
                continue
            reqs.append(Requirement(
                key=term.key, label=term.label, kind=item["kind"],
                category=term.category,
                # İşveren şartı ELLE seçti: çıkarım belirsizliği yok. Metinden
                # okunan şartlarda 1.0 olmayabilir (FS-4), burada 1.0 dürüst.
                extraction_confidence=1.0))
            kumeler.append(term.cluster)
        if not reqs:
            continue

        occupation = max(set(kumeler), key=kumeler.count) if kumeler else "genel"
        job = JobPosting(
            job_id=r["id"], title=r["title"], employer=r["employer"],
            city=r["city"], occupation_id=occupation,
            source="İşveren (doğrudan)", requirements=tuple(reqs),
            experience_level=r["experience_level"])
        out.append(NormalizedPosting(
            job=job,
            employer_key=fold(r["employer"]), title_key=fold(r["title"]),
            city_key=fold(r["city"]),
            content_fingerprint=r["id"],
            job_text=r["description"],
            # Başvuru bağlantısı yoksa iletişim işverende kalır; uydurma bir
            # URL üretmiyoruz — arayüz "başvuru bilgisi ilanda" der.
            url=r["apply_url"] or "",
            posted_at=r["created_at"], refreshed_at=r["created_at"],
            fetched_at=r["created_at"],
            provenance={"source_id": "src-direct-employer",
                        "board": "joblyfit/işveren",
                        "employer": r["employer"],
                        "deadline": r["deadline"]},
            work_arrangement=r["work_arrangement"],
            employment_type=r["employment_type"],
            experience_level=r["experience_level"]))
    return out
