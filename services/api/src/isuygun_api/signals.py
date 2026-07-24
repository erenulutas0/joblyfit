"""Anonim sinyal deposu: eşleşme geri bildirimi + başvuru olayları (D-059).

İki tablo, iki amaç:

* ``match_feedback`` — "bu eşleşme isabetli miydi?" (👍/👎 + sebep). T-006b'nin
  (golden set / kalibrasyon) ham maddesi: bizim bandımızla kullanıcının
  yargısının **uyuşmadığı** satırlar, kalibrasyon hatasının tam adresidir.
* ``apply_events`` — başvuru → yanıt/görüşme/teklif/red olayları. İleride
  işveren yanıt oranına dönüşür ("hayalet ilan" şüphesini tahminden kanıta
  çevirir); hacim eşiği dolmadan HİÇBİR yerde gösterilmez.

Tasarım kısıtları:

* **Kişisel veri yok.** Kimlik, ad, e-posta, IP alınmaz ve saklanmaz. Kayıtlar
  oturuma/kullanıcıya bağlanamaz — bilinçli olarak: bağlanabilse KVKK yükü ve
  güven maliyeti sinyalin değerini aşardı.
* **İlan anlık kopyalanır.** İlanlar 45 günde korpustan düşer (D-024); job_id
  tek başına 45 gün sonra hiçbir şey ifade etmez. Başlık/işveren yazım anında
  korpustan (yoksa istemcinin gönderdiğinden) kopyalanır.
* Yazımlar nadirdir; bağlantı tembel açılır ve kilitle korunur. Profil deposu
  PostgreSQL olsa bile sinyaller SQLite'ta kalır — analiz çevrimdışı yapılır,
  operasyonel bağımlılık eklemeye değmez.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

_DDL = """
CREATE TABLE IF NOT EXISTS match_feedback(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  job_id TEXT NOT NULL,
  title TEXT, employer TEXT,
  band TEXT,
  verdict TEXT NOT NULL,
  reason TEXT
);
CREATE TABLE IF NOT EXISTS apply_events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  job_id TEXT NOT NULL,
  title TEXT, employer TEXT,
  event TEXT NOT NULL,
  days_since_apply INTEGER
);
"""

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _db_target() -> str:
    """Sinyal veritabanının yeri.

    Testler profil deposunu ``ISUYGUN_DB=:memory:`` ile bellekte tutar; sinyaller
    de aynı hijyene uyar — test koşusu geliştiricinin diskine iz bırakmaz.
    """
    explicit = os.environ.get("ISUYGUN_SIGNALS_DB", "").strip()
    if explicit:
        return explicit
    if os.environ.get("ISUYGUN_DB", "") == ":memory:":
        return ":memory:"
    root = Path(__file__).resolve().parents[4] / ".data"
    root.mkdir(parents=True, exist_ok=True)
    return str(root / "signals.db")


def _get() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_db_target(), check_same_thread=False)
        _conn.executescript(_DDL)
        _conn.commit()
    return _conn


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def record_feedback(*, job_id: str, band: str | None, verdict: str,
                    reason: str | None, title: str, employer: str) -> None:
    with _lock:
        c = _get()
        c.execute(
            "INSERT INTO match_feedback(created_at, job_id, title, employer,"
            " band, verdict, reason) VALUES (?,?,?,?,?,?,?)",
            (_now(), job_id[:200], title[:200], employer[:200],
             (band or "")[:20] or None, verdict, (reason or "")[:120] or None),
        )
        c.commit()


def record_apply_event(*, job_id: str, event: str, days_since_apply: int | None,
                       title: str, employer: str) -> None:
    with _lock:
        c = _get()
        c.execute(
            "INSERT INTO apply_events(created_at, job_id, title, employer,"
            " event, days_since_apply) VALUES (?,?,?,?,?,?)",
            (_now(), job_id[:200], title[:200], employer[:200], event,
             days_since_apply),
        )
        c.commit()


def counts() -> dict:
    """Test ve bakım için kaba sayaçlar — kayıt içeriği dönmez."""
    with _lock:
        c = _get()
        fb = c.execute("SELECT COUNT(*) FROM match_feedback").fetchone()[0]
        ev = c.execute("SELECT COUNT(*) FROM apply_events").fetchone()[0]
    return {"match_feedback": fb, "apply_events": ev}
