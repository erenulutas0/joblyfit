"""Kimlik doğrulaması istemeyen public iş ilanı API'leri (D-023).

Dördü de resmî, dokümante ve kayıtsız kullanılabilir uçlardır. Her birinin
kullanım şartı **farklıdır** ve bu farklar Source Registry'de
``attribution_required`` / ``min_poll_hours`` / ``redistribution_policy``
alanlarında tutulur — kod dışında bir yerde tutulursa ihlal sessizce olur.

* **Arbeitsagentur** (DE) — Almanya İş Ajansı'nın resmî iş arama servisi.
  Mavi yaka kapsamı en geniş kaynak. Liste yanıtı **açıklama metni içermez**;
  şart çıkarımı başlık + meslek adı üzerinden yapılır ve bu arayüzde belirtilir.
* **Arbeitnow** (DE/AB) — ATS'lerden agrege eder, açıklama metni içerir.
* **The Muse** (ABD ağırlıklı) — key'siz saatte 500 istek; ToS §3.4 gereği
  ilana **geri bağlantı zorunludur**.
* **Himalayas** (global uzaktan) — ``expiryDate`` alanı taşır; süresi geçmiş
  ilanları ayıklamak için doğrudan kullanılır.

Hiçbiri scraping değildir: hepsi yayıncının kendi belgelediği JSON uçlarıdır ve
yanıtları ilanın kendi sayfasına giden URL taşır.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from ..pipeline import RawPosting
from .ats import USER_AGENT, FetchError, _throttle, html_to_text

TIMEOUT = 25


def _get(url: str, headers: dict | None = None) -> object:
    host = url.split("/")[2]
    _throttle(host)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise FetchError(f"{url} → HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise FetchError(f"{url} → {e.reason}") from e


def _date(value: str | None) -> str | None:
    """ISO benzeri bir tarihi ``YYYY-MM-DD``'ye indirger. Ayrıştırılamazsa None."""
    if not value:
        return None
    s = str(value).strip().replace("Z", "+00:00")
    for parse in (
        lambda x: datetime.fromisoformat(x),
        lambda x: datetime.strptime(x[:10], "%Y-%m-%d"),
    ):
        try:
            return parse(s).date().isoformat()
        except Exception:
            continue
    return None


# --------------------------------------------------------------------------
# Arbeitsagentur (DE) — mavi yaka kapsamı
# --------------------------------------------------------------------------

#: Yayınlanmış statik anahtar; kullanıcıya özel değildir, kayıt gerektirmez.
#: Kanıt: jobsuche.api.bund.dev
_BA_KEY = {"X-API-Key": "jobboerse-jobsuche"}
_BA_BASE = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"

#: Aranacak meslek terimleri. Sözlükteki mavi yaka kümelerini karşılar; her
#: terim ayrı bir sorgu olduğu için liste bilinçli olarak kısa tutulur.
BA_QUERIES: tuple[str, ...] = (
    "Lagerhelfer", "Berufskraftfahrer", "Produktionshelfer", "Elektriker",
    "Schweisser", "Koch", "Pflegehelfer", "Reinigungskraft", "Verkäufer",
    "Kraftfahrer", "Servicekraft", "Kommissionierer", "Softwareentwickler",
)


def fetch_arbeitsagentur(source_id: str, *, per_query: int = 25) -> list[RawPosting]:
    out: list[RawPosting] = []
    for was in BA_QUERIES:
        q = urllib.parse.urlencode({"was": was, "size": per_query, "page": 1})
        data = _get(f"{_BA_BASE}?{q}", _BA_KEY)
        for j in (data or {}).get("stellenangebote", []):
            ort = (j.get("arbeitsort") or {})
            city = " ".join(
                x for x in (ort.get("ort"), ort.get("region"), "Deutschland") if x
            )
            ref = j.get("refnr") or ""
            url = j.get("externeUrl") or (
                "https://www.arbeitsagentur.de/jobsuche/jobdetail/"
                + urllib.parse.quote(ref, safe="")
            )
            out.append(
                RawPosting(
                    source_id=source_id,
                    source_posting_ref=ref,
                    url=url,
                    title=j.get("titel") or j.get("beruf") or "",
                    employer=j.get("arbeitgeber") or "Belirtilmemiş",
                    city=city,
                    occupation_id="",
                    posted_at=_date(j.get("aktuelleVeroeffentlichungsdatum")),
                    # Liste ucu açıklama vermez; meslek adı tek ek sinyaldir.
                    description=j.get("beruf") or "",
                )
            )
    return out


# --------------------------------------------------------------------------
# Arbeitnow (DE/AB)
# --------------------------------------------------------------------------


def fetch_arbeitnow(source_id: str, *, pages: int = 3) -> list[RawPosting]:
    out: list[RawPosting] = []
    for page in range(1, pages + 1):
        data = _get(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
        rows = (data or {}).get("data", [])
        if not rows:
            break
        for j in rows:
            out.append(
                RawPosting(
                    source_id=source_id,
                    source_posting_ref=str(j.get("slug", "")),
                    url=j.get("url") or "",
                    title=j.get("title") or "",
                    employer=j.get("company_name") or "Belirtilmemiş",
                    city=j.get("location") or "",
                    arrangement="Uzaktan" if j.get("remote") else "",
                    occupation_id="",
                    posted_at=_date(
                        datetime.fromtimestamp(j["created_at"]).isoformat()
                        if isinstance(j.get("created_at"), (int, float))
                        else j.get("created_at")
                    ),
                    description=html_to_text(j.get("description", "")),
                )
            )
    return out


# --------------------------------------------------------------------------
# The Muse (ABD) — atıf zorunlu
# --------------------------------------------------------------------------


def fetch_themuse(source_id: str, *, pages: int = 5) -> list[RawPosting]:
    out: list[RawPosting] = []
    for page in range(1, pages + 1):
        data = _get(f"https://www.themuse.com/api/public/jobs?page={page}")
        for j in (data or {}).get("results", []):
            locs = [l.get("name", "") for l in (j.get("locations") or [])]
            out.append(
                RawPosting(
                    source_id=source_id,
                    source_posting_ref=str(j.get("id", "")),
                    url=(j.get("refs") or {}).get("landing_page") or "",
                    title=j.get("name") or "",
                    employer=(j.get("company") or {}).get("name") or "Belirtilmemiş",
                    city=locs[0] if locs else "",
                    occupation_id="",
                    posted_at=_date(j.get("publication_date")),
                    description=html_to_text(j.get("contents", "")),
                )
            )
    return out


# --------------------------------------------------------------------------
# Himalayas (uzaktan) — expiryDate taşır
# --------------------------------------------------------------------------


def fetch_himalayas(source_id: str, *, pages: int = 8, limit: int = 20) -> list[RawPosting]:
    out: list[RawPosting] = []
    for page in range(pages):
        data = _get(f"https://himalayas.app/jobs/api?limit={limit}&offset={page * limit}")
        rows = (data or {}).get("jobs", [])
        if not rows:
            break
        for j in rows:
            expiry = _date(j.get("expiryDate"))
            if expiry and expiry < datetime.now().date().isoformat():
                continue  # kaynağın kendisi süresinin geçtiğini söylüyor
            restr = j.get("locationRestrictions") or []
            out.append(
                RawPosting(
                    source_id=source_id,
                    source_posting_ref=str(j.get("guid", "")),
                    url=j.get("applicationLink") or j.get("guid") or "",
                    title=j.get("title") or "",
                    employer=j.get("companyName") or "Belirtilmemiş",
                    city=("Remote — " + ", ".join(restr[:2])) if restr else "Remote",
                    arrangement="Uzaktan",
                    occupation_id="",
                    posted_at=_date(j.get("pubDate")),
                    description=html_to_text(j.get("description", ""))
                    or (j.get("excerpt") or ""),
                )
            )
    return out


FETCHERS = {
    "src-api-arbeitsagentur": fetch_arbeitsagentur,
    "src-api-arbeitnow": fetch_arbeitnow,
    "src-api-themuse": fetch_themuse,
    "src-api-himalayas": fetch_himalayas,
}
