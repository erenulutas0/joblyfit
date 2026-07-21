"""ATS public job board adapter'ları — Lever, Greenhouse, Recruitee.

Bu uçlar şirketlerin **kendi kariyer sayfalarını kurmaları için** yayınladığı
kimlik doğrulaması istemeyen public API'lerdir. Kanıt:

* ``api.lever.co/robots.txt`` → ``User-agent: * / Allow: / / Crawl-delay: 1``
* ``boards-api.greenhouse.io/robots.txt`` → yalnızca ``/embed/`` disallow
* ``<firma>.recruitee.com/robots.txt`` → yalnızca ``/v/`` disallow
* Greenhouse job board API dokümanı, uçların amacını
  *"build careers pages with a unique look and feel"* diye tanımlar.

Yanıtlar ilanın **kendi sayfasına** giden URL taşır (``hostedUrl`` /
``absolute_url`` / ``careers_url``); kullanıcıyı oraya yönlendirmek bu uçların
amaçlanan kullanımıdır.

**Kısıtlar bilinçlidir ve gevşetilmez:**

* ``Crawl-delay: 1`` uygulanır (:data:`MIN_INTERVAL`).
* Login, CAPTCHA, bot-detection veya paywall içeren hiçbir uç eklenmez (D-002).
* Yalnızca Source Registry'de kayıtlı ve izinli board'lar çekilir; kapı
  :func:`registry.assert_fetchable`'dır.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser

from ..pipeline import RawPosting

# HTTP başlıkları latin-1 ile kodlanır; Türkçe karakter kullanılamaz.
USER_AGENT = "isuygun-bot/0.1 (job matching; links back to the original posting)"

#: ``api.lever.co/robots.txt`` → ``Crawl-delay: 1``. Host başına asgari aralık.
MIN_INTERVAL = 1.0
TIMEOUT = 15

_last_call: dict[str, float] = {}


class FetchError(RuntimeError):
    """Kaynak beklenen yanıtı vermedi. Sessizce yutulmaz — ingest raporuna girer."""


def _throttle(host: str) -> None:
    prev = _last_call.get(host)
    if prev is not None:
        wait = MIN_INTERVAL - (time.monotonic() - prev)
        if wait > 0:
            time.sleep(wait)
    _last_call[host] = time.monotonic()


def fetch_json(url: str) -> object:
    host = url.split("/")[2]
    _throttle(host)
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            if r.status != 200:
                raise FetchError(f"{url} → HTTP {r.status}")
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        # 403/401 erişim değişikliği sinyalidir; sessizce geçilmez.
        raise FetchError(f"{url} → HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise FetchError(f"{url} → {e.reason}") from e


# --------------------------------------------------------------------------
# HTML → düz metin (ilan açıklamaları HTML olarak geliyor)
# --------------------------------------------------------------------------


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in ("br", "p", "li", "div", "h1", "h2", "h3", "h4", "tr"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    p = _Text()
    p.feed(html or "")
    text = "".join(p.parts)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


# --------------------------------------------------------------------------
# Board tanımı
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Board:
    """Registry'de izinli tek bir şirket panosu."""

    source_id: str
    platform: str      # lever | greenhouse | recruitee
    slug: str
    employer: str


def _lever(board: Board) -> list[RawPosting]:
    data = fetch_json(f"https://api.lever.co/v0/postings/{board.slug}?mode=json")
    if not isinstance(data, list):
        raise FetchError(f"{board.slug}: liste bekleniyordu")
    out = []
    for j in data:
        cats = j.get("categories") or {}
        out.append(
            RawPosting(
                source_id=board.source_id,
                source_posting_ref=str(j.get("id", "")),
                url=j.get("hostedUrl") or j.get("applyUrl") or "",
                title=j.get("text") or "",
                employer=board.employer,
                city=cats.get("location") or "",
                arrangement=j.get("workplaceType") or "",
                occupation_id="",           # extract katmanı dolduracak
                posted_at=_ms_to_date(j.get("createdAt")),
                description=_lever_description(j),
            )
        )
    return out


def _lever_description(j: dict) -> str:
    """İlanın gerçek gövdesini kurar.

    ``descriptionPlain`` çoğu ilanda **yalnızca şirket tanıtımıdır** ve aynı
    firmanın bütün ilanlarında birebir aynıdır. Yalnızca onu kullanmak iki
    soruna yol açıyordu: (1) şart çıkarımı boş kalıyordu, (2) içerik parmak izi
    aynı çıktığı için farklı ilanlar duplicate sanılıyordu — "Instore Sales
    Manager" ile "Senior AML Analyst" %100 benzer görünüyordu.

    Asıl içerik ``lists`` altındaki bölümlerdedir. Bölüm başlıkları korunur;
    extract katmanı "Qualifications" gibi başlıkları zorunluluk sinyali olarak
    kullanır.
    """
    parts: list[str] = []
    for section in j.get("lists") or []:
        head = (section.get("text") or "").strip()
        body = html_to_text(section.get("content", ""))
        if body:
            parts.append(f"## {head}\n{body}" if head else body)
    if parts:
        return "\n\n".join(parts)
    # lists yoksa gövdeye düş.
    return j.get("descriptionPlain") or html_to_text(j.get("description", ""))


def _greenhouse(board: Board) -> list[RawPosting]:
    data = fetch_json(
        f"https://boards-api.greenhouse.io/v1/boards/{board.slug}/jobs?content=true"
    )
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    out = []
    for j in jobs:
        out.append(
            RawPosting(
                source_id=board.source_id,
                source_posting_ref=str(j.get("id", "")),
                url=j.get("absolute_url") or "",
                title=j.get("title") or "",
                employer=board.employer,
                city=(j.get("location") or {}).get("name") or "",
                occupation_id="",
                posted_at=(j.get("updated_at") or "")[:10] or None,
                description=html_to_text(_unescape(j.get("content", ""))),
            )
        )
    return out


def _recruitee(board: Board) -> list[RawPosting]:
    data = fetch_json(f"https://{board.slug}.recruitee.com/api/offers/")
    offers = data.get("offers", []) if isinstance(data, dict) else []
    out = []
    for j in offers:
        city = " ".join(x for x in (j.get("city"), j.get("country")) if x)
        out.append(
            RawPosting(
                source_id=board.source_id,
                source_posting_ref=str(j.get("id", "")),
                url=j.get("careers_url") or j.get("careers_apply_url") or "",
                title=j.get("title") or "",
                employer=board.employer,
                city=city,
                occupation_id="",
                posted_at=(j.get("published_at") or "")[:10] or None,
                description=html_to_text(j.get("description", "")),
            )
        )
    return out


def _ashby(board: Board) -> list[RawPosting]:
    data = fetch_json(
        f"https://api.ashbyhq.com/posting-api/job-board/{board.slug}?includeCompensation=false"
    )
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    out = []
    for j in jobs:
        out.append(
            RawPosting(
                source_id=board.source_id,
                source_posting_ref=str(j.get("id", "")),
                url=j.get("jobUrl") or j.get("applyUrl") or "",
                title=j.get("title") or "",
                employer=board.employer,
                city=j.get("location") or "",
                arrangement=j.get("workplaceType") or "",
                occupation_id="",
                posted_at=(j.get("publishedAt") or "")[:10] or None,
                description=html_to_text(j.get("descriptionHtml", ""))
                or (j.get("descriptionPlain") or ""),
            )
        )
    return out


FETCHERS = {"lever": _lever, "greenhouse": _greenhouse,
            "recruitee": _recruitee, "ashby": _ashby}

#: Pano başına alınacak en yeni ilan sayısı. Tek bir dev şirketin 780 ilanı
#: feed'i doldurup diğer 70 işvereni görünmez kılıyordu; sınır çeşitliliği korur.
#: Kırpma **sessiz değildir** — ingest raporunda `truncated` olarak görünür.
MAX_PER_BOARD = 40


def fetch_board(board: Board, *, limit: int = MAX_PER_BOARD) -> tuple[list[RawPosting], int]:
    """Panoyu çeker. Döner: (ilanlar, kırpılan sayı)."""
    fetch = FETCHERS.get(board.platform)
    if fetch is None:
        raise FetchError(f"Bilinmeyen platform: {board.platform!r}")
    items = fetch(board)
    total = len(items)
    if limit and total > limit:
        # En yeniler önce. Tarihi olmayanlar sona düşer.
        items.sort(key=lambda r: r.posted_at or "", reverse=True)
        items = items[:limit]
    return items, total - len(items)


def _ms_to_date(ms) -> str | None:
    if not ms:
        return None
    from datetime import datetime, timezone

    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


def _unescape(s: str) -> str:
    import html as _h

    return _h.unescape(s or "")
