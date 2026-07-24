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
* **Jooble** (TR + global) — Türkiye hacminin ana kaynağı (D-038). Toplayıcı:
  Kariyer.net/SecretCV gibi panolardan agrege eder ve her ilan kaynağa giden
  ``link`` taşır. Tek anahtar isteyen kaynak; anahtar **ortam değişkeninden**
  okunur (``ISUYGUN_JOOBLE_KEY``), koda gömülmez, yoksa temizce atlanır.

Hiçbiri scraping değildir: hepsi yayıncının kendi belgelediği JSON uçlarıdır ve
yanıtları ilanın kendi sayfasına giden URL taşır.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from ..pipeline import RawPosting
from .ats import USER_AGENT, FetchError, _throttle, html_to_text

TIMEOUT = 40


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
    except Exception as e:
        raise FetchError(f"{url} → {type(e).__name__}: {e}") from e


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
    """13 ayrı meslek sorgusu yapar; her biri bağımsızdır.

    Sorgular tek bir ``try`` içinde olduğunda tek bir zaman aşımı **on üçünü
    birden** siliyordu — gerçek bir koşuda Almanya mavi yaka ilanlarının tamamı
    böyle kayboldu. Kaynağın tamamen erişilemez olduğu durum ayrı: hiçbir sorgu
    tutmazsa hata yükseltilir, çünkü sessizce boş dönmek kaynağın kapandığını
    gizler.
    """
    out: list[RawPosting] = []
    failures: list[str] = []
    for was in BA_QUERIES:
        q = urllib.parse.urlencode({"was": was, "size": per_query, "page": 1})
        try:
            data = _get(f"{_BA_BASE}?{q}", _BA_KEY)
        except FetchError as e:
            failures.append(f"{was}: {str(e)[-60:]}")
            continue
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

    if failures and not out:
        raise FetchError(
            f"Arbeitsagentur: {len(failures)}/{len(BA_QUERIES)} sorgu başarısız, "
            f"hiç ilan alınamadı — {failures[0]}"
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
                    # Epoch **UTC** olarak çözülür. Yerel saat kullanmak, saat
                    # dilimine göre tarihi bir gün kaydırır ve tazelik filtresi
                    # sınırdaki ilanlarda yanlış karar verir (D-024).
                    posted_at=_date(
                        datetime.fromtimestamp(
                            j["created_at"], tz=timezone.utc
                        ).isoformat()
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


# --------------------------------------------------------------------------
# Jooble (TR + global) — toplayıcı, Türkiye hacminin ana kaynağı (D-038)
# --------------------------------------------------------------------------

#: Jooble anahtarı ortam değişkeninden okunur — koda gömülmez. Yoksa kaynak
#: temizce atlanır.
_JOOBLE_ENV = "ISUYGUN_JOOBLE_KEY"

#: Jooble **ülke sitesi başına ayrı indeks ve ayrı anahtar** kullanır (D-041).
#: Uluslararası ``jooble.org`` Türkiye'yi tanımaz — "Turkey"yi ABD'deki bir
#: kasaba (Turkey, NC) sanır ve İstanbul/Ankara için 0 döner. Gerçek Türkiye
#: ilanları ``tr.jooble.org``'dadır ve o kendi anahtarını ister. Host ve konum
#: bu yüzden yapılandırılabilir; varsayılan Türkiye hedefidir.
_JOOBLE_HOST_ENV = "ISUYGUN_JOOBLE_HOST"
_JOOBLE_LOC_ENV = "ISUYGUN_JOOBLE_LOCATION"
_JOOBLE_HOST_DEFAULT = "tr.jooble.org"
_JOOBLE_LOC_DEFAULT = "Türkiye"


def _mask_key(text: str) -> str:
    """URL'deki API anahtarını gizler: ``/api/<token>`` → ``/api/***``.

    Anahtar hata mesajına sızarsa ingest raporuna, oradan arayüze ve önbelleğe
    yazılır. Hiçbir hata metni ham anahtarı taşımamalı.
    """
    import re as _re

    return _re.sub(r"(/api/)[^/\s?]+", r"\1***", text)

#: Türkiye'yi geniş taramak için meslek tohumları. Jooble ``keywords`` +
#: ``location`` **ikisini de** zorunlu tutuyor; tek geniş sorgu yerine kümelerimizi
#: karşılayan tohumlar kullanılır. Bölge-özgüllük sorgudan DEĞİL, dönen ilanın
#: ``location`` alanından gelir (regions.py sınıflandırır, şehir filtresi çalışır)
#: — böylece tüm Türkiye tek çekimde taranır, il il sorgu gerekmez.
#: TÜRKÇE KARAKTER KRİTİK (2026-07-24 ölçümü): ``"yazilim"`` 10 ilan döndürürken
#: ``"yazılım"`` 985 döndürüyor — 98 kat fark. Jooble Türkçe gövdeyi harfi harfine
#: eşliyor; ASCII'ye sadeleştirme buradaki hacmi yok eder. Tohumlar bu yüzden
#: tam Türkçe yazılır ve öyle kalmalıdır.
JOOBLE_QUERIES: tuple[str, ...] = (
    # Boş sorgu = tüm ülke indeksi (ölçüm: totalCount 11338). Anahtar
    # kelimelerimizin hiçbirine uymayan ilanlar YALNIZCA buradan gelir; ilk
    # sırada çünkü en geniş kapsamı en az istekle verir.
    "",
    "yazılım", "muhasebe", "satış", "pazarlama", "insan kaynakları",
    "mühendis", "sürücü şoför", "hemşire sağlık", "mağaza satış danışmanı",
    "üretim operatör", "depo lojistik", "garson aşçı", "öğretmen",
    "çağrı merkezi", "temizlik güvenlik",
)


def _post_json(url: str, payload: dict) -> object:
    """POST + JSON gövde. `_get` yalnızca GET; Jooble POST ister."""
    host = url.split("/")[2]
    _throttle(host)
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise FetchError(_mask_key(f"{url} → HTTP {e.code}")) from e
    except urllib.error.URLError as e:
        raise FetchError(_mask_key(f"{url} → {e.reason}")) from e
    except Exception as e:
        raise FetchError(_mask_key(f"{url} → {type(e).__name__}: {e}")) from e


def _jooble_description(j: dict) -> str:
    """Snippet + maaş + tür'ü tek metne toplar.

    Jooble yalnızca **snippet** verir (tam açıklama değil). Maaş ve çalışma
    türü ayrı alanlardadır; bunları metne katarsak mevcut çıkarıcılar
    (salary.py, jobmeta.py) onları görür — ayrı bir eşleme yazmaya gerek kalmaz.
    Maaş satırı Türkçe "Maaş:" ile yazılır ki salary.py'nin bağlam kontrolü
    tetiklensin.
    """
    parts: list[str] = []
    salary = (j.get("salary") or "").strip()
    if salary:
        parts.append(f"Maaş: {salary}")
    jtype = (j.get("type") or "").strip()
    if jtype:
        parts.append(f"Çalışma türü: {jtype}")
    snippet = html_to_text(j.get("snippet") or "")
    if snippet:
        parts.append(snippet)
    return "\n".join(parts)


def fetch_jooble(source_id: str, *, queries: tuple[str, ...] = JOOBLE_QUERIES,
                 location: str | None = None, per_page: int = 100,
                 pages: int = 10, max_requests: int = 120) -> list[RawPosting]:
    """Jooble ülke sitesinden ilanlar. Her tohum sorgusu bağımsızdır.

    Varsayılanlar **ölçülmüş** API sınırlarıdır (tr.jooble.org, 2026-07-24):

    * ``per_page=100`` — tavan. 500 istenirse API sessizce 20'ye düşürür.
    * ``pages=10`` — tek sorgu ~10 sayfada kesilir (sayfa 12 boş döner). Yani
      hiçbir sorgu 1000'den fazla ilan veremez; ülke indeksi 11338 olsa bile.
      Hacim bu yüzden **tek geniş sorgudan değil**, örtüşen tohumların
      birleşiminden gelir.
    * ``max_requests`` — anahtarın 500 istek sınırı var (dönemi belirsiz).
      Bütçe dolunca çekim durur; kalan tohumlar bir sonraki tazelemeye kalır.

    **Host ülke sitesidir ve anahtarla eşleşmelidir (D-041):** ``tr.jooble.org``
    anahtarı Türkiye ilanlarını verir; ``jooble.org`` (uluslararası) anahtarı
    Türkiye'yi tanımaz. Host ``ISUYGUN_JOOBLE_HOST``, konum
    ``ISUYGUN_JOOBLE_LOCATION`` ile ayarlanır.

    Anahtar yoksa kaynak atlanır ama **sessizce değil**: hata ingest raporunda
    görünür. Anahtar URL'de olduğu için hata mesajları maskelenir (:func:`_mask_key`).

    Geniş tohum sorguları örtüşür; batch içinde ``id`` ile tekilleştirilir.
    """
    import os

    key = os.environ.get(_JOOBLE_ENV, "").strip()
    if not key:
        raise FetchError(
            f"{_JOOBLE_ENV} tanımlı değil — Jooble atlandı. Ücretsiz anahtar: "
            "jooble.org/api/about, sonra .env.local'e ekle."
        )

    host = os.environ.get(_JOOBLE_HOST_ENV, "").strip() or _JOOBLE_HOST_DEFAULT
    if location is None:
        location = os.environ.get(_JOOBLE_LOC_ENV, "").strip() or _JOOBLE_LOC_DEFAULT
    url = f"https://{host}/api/{key}"
    out: list[RawPosting] = []
    seen: set[str] = set()
    failures: list[str] = []
    used = 0    # harcanan istek sayısı — anahtarın 500 sınırını aşmamak için

    for kw in queries:
        if used >= max_requests:
            break
        for page in range(1, pages + 1):
            if used >= max_requests:
                break
            payload = {"keywords": kw, "location": location,
                       "page": page, "ResultOnPage": per_page}
            used += 1
            try:
                data = _post_json(url, payload)
            except FetchError as e:
                failures.append(f"{kw} s{page}: {str(e)[-50:]}")
                break   # bu tohumun sonraki sayfalarını deneme
            jobs = (data or {}).get("jobs", []) if isinstance(data, dict) else []
            if not jobs:
                break   # sayfa bitti
            for j in jobs:
                jid = str(j.get("id") or j.get("link") or "")
                if not jid or jid in seen:
                    continue
                seen.add(jid)
                out.append(
                    RawPosting(
                        source_id=source_id,
                        source_posting_ref=jid,
                        url=j.get("link") or "",
                        title=j.get("title") or "",
                        employer=j.get("company") or "Belirtilmemiş",
                        city=j.get("location") or location,
                        occupation_id="",
                        # Jooble `updated` = kaynağın son görülme tarihi, ilk
                        # yayın DEĞİL. D-035: yaşı bilmiyoruz (posted_at=None,
                        # elenmez), tazeliği refreshed_at'ten ölçeriz.
                        posted_at=None,
                        refreshed_at=_date(j.get("updated")),
                        description=_jooble_description(j),
                    )
                )

    if failures and not out:
        hint = ""
        if "403" in failures[0]:
            hint = (f" — anahtar '{host}' için geçersiz olabilir; ülke sitesi "
                    f"anahtarla eşleşmeli (bkz. ISUYGUN_JOOBLE_HOST, D-041).")
        raise FetchError(
            f"Jooble ({host}): {len(failures)}/{len(queries)} sorgu başarısız, "
            f"hiç ilan alınamadı — {failures[0]}{hint}"
        )
    # Sorgular başarılı ama hiç ilan yok: sessiz dönmek yanıltıcı olurdu.
    # En olası sebep host/konum/anahtar uyumsuzluğu (ör. jooble.org anahtarı
    # 'Türkiye'yi tanımıyor); kullanıcı bunu bilmeli.
    if not out and not failures:
        raise FetchError(
            f"Jooble ({host}, konum='{location}'): sorgular çalıştı ama 0 ilan "
            f"döndü. Muhtemelen host/anahtar ülke uyumsuzluğu — Türkiye için "
            f"tr.jooble.org anahtarı gerekir (ISUYGUN_JOOBLE_HOST, D-041)."
        )
    return out


FETCHERS = {
    "src-api-arbeitsagentur": fetch_arbeitsagentur,
    "src-api-arbeitnow": fetch_arbeitnow,
    "src-api-themuse": fetch_themuse,
    "src-api-himalayas": fetch_himalayas,
    "src-api-jooble": fetch_jooble,
}
