"""Ingestion pipeline — fetch → parse → normalize → extract → dedupe.

ARCHITECTURE.md → Akış A'daki sıranın kod karşılığı. Extraction ayrı bir alt
sistem değil, normalize adımının parçasıdır (audit ARC-01 düzeltmesi).

Şu an yalnızca ``fixture`` adapter'ı çalıştırılabilir (D-018). Gerçek bir
source adapter eklendiğinde bu pipeline değişmez — yalnızca ``fetch`` katmanı
değişir; bu, adapter'ın izole edilmiş olmasının amacıdır.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from itertools import combinations
from pathlib import Path

from isuygun_core.domain import JobPosting, Requirement

from . import registry

# --------------------------------------------------------------------------
# Employer identity resolution (audit SCR-01 / ARC-04)
# --------------------------------------------------------------------------

# Türkçe harfleri ASCII karşılığına indirger.
#
# Burada bilinçli olarak ``unicodedata.normalize("NFKD", ...)`` KULLANILMAZ:
# NFKD "ş" harfini "s" + birleşen çengele ayırır; sonraki noktalama temizliği
# çengeli silince "şirketi" → "s irketi" olur ve kelime sınırı bozulur. Ayrıca
# Python'da ``"İ".casefold()`` birleşen noktalı "i̇" üretir. Türkçe metinde
# katlama açık bir tabloyla yapılmalıdır.
_TR_FOLD = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i", "İ": "i",
    "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
    "â": "a", "Â": "a", "î": "i", "Î": "i", "û": "u", "Û": "u",
})


def fold(raw: str) -> str:
    """Karşılaştırma için metni katlar: Türkçe harf → ASCII, küçük harf.

    "Gıda" ≡ "GIDA" ≡ "Gida" — kaynaklar üçünü de yazıyor.
    """
    s = unicodedata.normalize("NFC", raw)
    return s.translate(_TR_FOLD).lower()


def _words(raw: str) -> list[str]:
    return re.findall(r"\w+", fold(raw), flags=re.UNICODE)


# Türkçe ticaret unvanlarında hukuki form **sona** gelir. Yalnızca sondan
# soyarız; ortadaki kelimeleri silmek gerçek isim parçalarını yok edebilir.
_LEGAL_SUFFIXES: tuple[tuple[str, ...], ...] = (
    ("anonim", "sirketi"), ("limited", "sirketi"), ("kollektif", "sirketi"),
    ("a", "s"), ("ltd", "sti"), ("as",), ("ltd",), ("sti",),
    ("sanayi", "ve", "ticaret"), ("san", "ve", "tic"),
    ("sanayi",), ("ticaret",), ("san",), ("tic",),
    ("sirketi",), ("sirket",),
)


def normalize_employer(raw: str) -> str:
    """İşveren adını karşılaştırılabilir hale getirir.

    "Kuzey Hat Lojistik A.Ş." ≡ "KUZEY HAT LOJİSTİK ANONİM ŞİRKETİ"
    Bu olmadan duplicate blocking anahtarı çalışmaz (FR-206 / audit SCR-01).
    """
    tokens = _words(raw)
    changed = True
    while changed and tokens:
        changed = False
        for suffix in _LEGAL_SUFFIXES:
            n = len(suffix)
            if len(tokens) > n and tuple(tokens[-n:]) == suffix:
                tokens = tokens[:-n]
                changed = True
                break
    return " ".join(tokens)


def normalize_title(raw: str) -> str:
    s = re.sub(r"\(.*?\)", " ", raw)        # "(Bölgesel Rota)" gibi ekleri at
    return " ".join(_words(s))


# --------------------------------------------------------------------------
# Raw → normalized
# --------------------------------------------------------------------------


@dataclass(slots=True)
class RawPosting:
    """Adapter'ın ürettiği ham kayıt — henüz normalize edilmemiş."""

    source_id: str
    source_posting_ref: str
    url: str
    title: str
    employer: str
    city: str
    district: str = ""
    arrangement: str = ""
    occupation_id: str = ""
    posted_at: str | None = None
    description: str = ""
    is_public_sector: bool = False
    raw_requirements: list[dict] = field(default_factory=list)


@dataclass(slots=True)
class NormalizedPosting:
    job: JobPosting
    employer_key: str
    title_key: str
    city_key: str
    content_fingerprint: str
    job_text: str
    url: str
    posted_at: str | None
    fetched_at: str
    provenance: dict

    @property
    def blocking_key_a(self) -> str:
        """Geçit A: employer + title + location (SCRAPING_SYSTEM §6)."""
        return f"{self.employer_key}|{self.title_key}|{self.city_key}"

    @property
    def blocking_key_b(self) -> str:
        """Geçit B: employer'DAN ve başlıktan BAĞIMSIZ aday bloğu.

        Kasıtlı olarak **kaba**dır. Agency, işvereni gizleyip başlığı
        değiştirdiğinde A geçidi bu iki kaydı hiç karşılaştırmaz; B geçidi
        onları aynı bloğa sokar, karar ise :func:`content_similarity` ile
        verilir. Blocking ile matching'i ayırmak, yeniden yazılmış (birebir
        olmayan) kopyaların da yakalanmasını sağlar — audit SCR-02.
        """
        return f"{self.city_key}|{self.job.occupation_id}"


def _fingerprint(text: str) -> str:
    return hashlib.sha256(" ".join(sorted(_tokens(text))).encode()).hexdigest()


def _tokens(text: str) -> set[str]:
    return set(_words(text))


# Blok içi eşleşme eşiği. Kalibrasyon hedefidir, evrensel doğru değildir —
# T-021 gerçek korpusla ölçüldüğünde yeniden ayarlanır (OPEN-09).
CONTENT_SIMILARITY_THRESHOLD = 0.75


def content_similarity(a: NormalizedPosting, b: NormalizedPosting) -> float:
    """İki ilanın metin örtüşmesi (Jaccard). 1.0 = birebir aynı metin."""
    ta, tb = _tokens(a.job_text), _tokens(b.job_text)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def normalize(raw: RawPosting, *, adapter_version: str) -> NormalizedPosting:
    reqs = tuple(
        Requirement(
            key=r["key"],
            label=r["label"],
            kind=r.get("kind", "required"),
            category=r.get("category", "skill"),
            min_years=r.get("min_years"),
            extraction_confidence=r.get("confidence", 1.0),
            is_legal_eligibility=r.get("is_legal_eligibility", False),
            source_span=r.get("span"),
        )
        for r in raw.raw_requirements
    )
    job = JobPosting(
        job_id=f"{raw.source_id}:{raw.source_posting_ref}",
        title=raw.title,
        employer=raw.employer,
        city=raw.city,
        occupation_id=raw.occupation_id,
        source=registry.get(raw.source_id).name,
        requirements=reqs,
        is_public_sector=raw.is_public_sector,
    )
    return NormalizedPosting(
        job=job,
        employer_key=normalize_employer(raw.employer),
        title_key=normalize_title(raw.title),
        city_key=" ".join(_words(raw.city)),
        content_fingerprint=_fingerprint(raw.description),
        job_text=raw.description,
        url=raw.url,
        posted_at=raw.posted_at,
        fetched_at=datetime.now().isoformat(timespec="seconds"),
        provenance={
            "source_id": raw.source_id,
            "source_posting_ref": raw.source_posting_ref,
            "adapter_version": adapter_version,
        },
    )


# --------------------------------------------------------------------------
# Duplicate detection — çoklu blocking geçidi (audit SCR-02)
# --------------------------------------------------------------------------


# Blok içi karşılaştırma O(n²) olduğundan blok büyüklüğü sınırlanır. Sınır
# aşılırsa kayıtlar sessizce atılmaz; `oversized_blocks` olarak raporlanır.
MAX_BLOCK_SIZE = 200


def cluster(
    postings: list[NormalizedPosting],
) -> tuple[dict[str, list[NormalizedPosting]], list[str]]:
    """Aynı gerçek ilanın kopyalarını tek canonical altında toplar.

    İki aşamalı standart record-linkage yapısı:

    1. **Blocking** — hangi çiftlerin karşılaştırılacağını belirler. İki
       bağımsız geçit vardır; B geçidi employer ve başlıktan bağımsızdır.
    2. **Matching** — A geçidinde anahtar eşitliği yeterlidir (yüksek kesinlik);
       B geçidinde karar metin benzerliğiyle verilir.

    Tek anahtarlı bir tasarım, agency'nin işvereni gizleyip başlığı değiştirdiği
    kopyaları **hiç karşılaştırmadan** kaçırırdı (audit SCR-02).

    Döndürür: (canonical_id → kopyalar, sınırı aşan blok anahtarları).
    """
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for p in postings:
        parent.setdefault(p.job.job_id, p.job.job_id)

    # Geçit A — anahtar eşitliği doğrudan birleştirir.
    buckets_a: dict[str, list[NormalizedPosting]] = {}
    for p in postings:
        buckets_a.setdefault(p.blocking_key_a, []).append(p)
    for group in buckets_a.values():
        for other in group[1:]:
            union(group[0].job.job_id, other.job.job_id)

    # Geçit B — kaba blok + çift bazlı içerik karşılaştırması.
    oversized: list[str] = []
    buckets_b: dict[str, list[NormalizedPosting]] = {}
    for p in postings:
        buckets_b.setdefault(p.blocking_key_b, []).append(p)
    for key, group in buckets_b.items():
        if len(group) > MAX_BLOCK_SIZE:
            oversized.append(key)
            continue
        for x, y in combinations(group, 2):
            if content_similarity(x, y) >= CONTENT_SIMILARITY_THRESHOLD:
                union(x.job.job_id, y.job.job_id)

    clusters: dict[str, list[NormalizedPosting]] = {}
    for p in postings:
        clusters.setdefault(find(p.job.job_id), []).append(p)
    return clusters, oversized


# --------------------------------------------------------------------------
# Fixture adapter — D-018 kapsamında tek çalıştırılabilir kaynak
# --------------------------------------------------------------------------

ADAPTER_VERSION = "fixture-0.1.0"

# Repo kökü: .../services/ingest/src/isuygun_ingest/pipeline.py → 4 seviye yukarı
REPO_ROOT = Path(__file__).resolve().parents[4]


def pick_canonical(group: list[NormalizedPosting]) -> NormalizedPosting:
    """Kopya kümesinden kullanıcıya gösterilecek kaydı seçer.

    İşvereni açıkça yazan kayıt tercih edilir; agency'nin gizlediği sürüm
    kullanıcıya daha az bilgi verir (FR-206). Eşitlikte en erken yayın tarihi.
    """
    # employer_key katlanmış olduğu için işaretler de katlanmış yazılır.
    _ANON = ("gizli", "belirtilmemis", "firma adi", "gizli firma")

    def rank(p: NormalizedPosting) -> tuple[int, str]:
        anonymous = any(w in p.employer_key for w in _ANON)
        return (1 if anonymous else 0, p.posted_at or "9999")

    return min(group, key=rank)


def run_fixture_ingest(source_id: str = "src-fixture-001", root: Path | None = None) -> dict:
    """Fixture korpusunu okuyup pipeline'dan geçirir.

    Ağ erişimi YOKTUR. ``assert_fetchable`` yine de çağrılır — gerçek bir
    kaynağa geçildiğinde aynı kapıdan geçilmesini garanti etmek için.
    """
    rec = registry.assert_fetchable(source_id)
    base = root or REPO_ROOT
    fixture_path = base / (rec.fixture_dir or "")
    if not fixture_path.is_dir():
        raise FileNotFoundError(f"Fixture dizini yok: {fixture_path}")

    raws: list[RawPosting] = []
    for f in sorted(fixture_path.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        raws.append(RawPosting(source_id=source_id, **data))

    normalized = [normalize(r, adapter_version=ADAPTER_VERSION) for r in raws]
    clusters, oversized = cluster(normalized)
    canonical = {cid: pick_canonical(group) for cid, group in clusters.items()}

    return {
        "source": rec.name,
        "fetched": len(raws),
        "normalized": len(normalized),
        "canonical": len(clusters),
        "duplicates_merged": len(normalized) - len(clusters),
        "oversized_blocks": oversized,
        "postings": normalized,
        "clusters": clusters,
        "canonical_postings": canonical,
    }
