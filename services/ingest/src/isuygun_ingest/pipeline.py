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
import urllib.parse
from dataclasses import dataclass, field
from datetime import date, datetime
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
    """Başlığı karşılaştırılabilir hale getirir — ama **içerik atmadan**.

    Parantez içi ekler bilinçli olarak korunur. Atıldığında "Software Engineer"
    ile "Software Engineer (New Grad)" aynı anahtara düşüyor ve Geçit A bunları
    tek ilana indirgiyordu; oysa bunlar farklı pozisyonlar.

    Buradaki asimetri kararı belirler: kaçırılan bir birleştirme kullanıcıya
    ilanı iki kez gösterir, yanlış birleştirme ise **gerçek bir ilanı ondan
    tamamen gizler**. İkincisi daha ağır bir hatadır.
    """
    return " ".join(_words(raw))


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
    #: Kaynağın ilanı son güncellediği tarih. `posted_at` ile karıştırılmaz:
    #: biri "ne zaman açıldı", diğeri "hâlâ ilgileniliyor mu" sorusunu
    #: yanıtlar ve ikisi karıştırılınca eski ilan taze görünür.
    refreshed_at: str | None = None
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
    #: Kaynağın son güncelleme tarihi — "hâlâ ilgileniliyor mu" sinyali.
    #: Tazelik bunun üzerinden ölçülür; **yaş** ise `posted_at`ten. İkisini
    #: karıştırmak, 96 gündür açık bir ilanı "5 gün önce" göstermekti.
    refreshed_at: str | None
    fetched_at: str
    provenance: dict
    #: İlan metninden okunan maaş. `None` iki şey olabilir; ayrımı
    #: `salary_status` taşır — "yazmamış" ile "okuyamadım" aynı şey değildir.
    #: Çalışma biçimi / istihdam türü / deneyim seviyesi. Üçü de ``None``
    #: olabilir ve bu "belirtilmemiş" demektir — varsayılan değil.
    work_arrangement: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    salary: object | None = None
    #: found | not_stated | unreadable
    salary_status: str = "not_stated"
    #: Ayrımcı/dışlayıcı dil işaretleri (D-042). Boş = temiz. Hüküm değil,
    #: bilgilendirme; işaretler Türkiye/aggregator verisiyle görünür.
    fairness_flags: tuple = ()
    #: Metin token'ları. Blok içi karşılaştırma O(n²) olduğu için her çiftte
    #: yeniden hesaplamak pahalıydı; bir kez üretilip saklanır.
    _tokens_cache: set | None = None

    @property
    def tokens(self) -> set:
        if self._tokens_cache is None:
            self._tokens_cache = _tokens(self.job_text)
        return self._tokens_cache

    @property
    def blocking_key_a(self) -> str:
        """Geçit A: employer + title + location (SCRAPING_SYSTEM §6)."""
        return f"{self.employer_key}|{self.title_key}|{self.city_key}"

    @property
    def url_key(self) -> str:
        """Geçit U: normalize edilmiş ilan URL'i — **kaynaklar arası** dedupe.

        Toplayıcılar (Jooble) çoğu zaman ilanın **asıl** sayfasına link verir;
        biz aynı ilanı şirketin ATS'sinden de doğrudan çekiyor olabiliriz. İki
        kayıt aynı URL'e çözülüyorsa **tanım gereği aynı ilandır** — bu, içerik
        benzerliğinin aksine yanlış-birleştirme riski taşımaz (D-039).

        Yalnızca **belirli bir ilana** işaret eden URL'ler anahtar üretir: yol
        bileşeni olmayan (çıplak alan adı) ya da boş URL'ler ``""`` döner ve
        birleştirmede kullanılmaz — yoksa aynı kariyer ana sayfasını paylaşan
        farklı ilanlar yanlışlıkla tek sayılırdı.
        """
        return _normalize_url(self.url)

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


#: Saf takip parametreleri — ilanı ayırt etmezler, atılır. Bunların DIŞINDAKİ
#: her şey korunur; özellikle iş kimliği (``gh_jid`` gibi) çünkü çoğu şirket
#: kendi kariyer sayfasında ilanı **query'de** ayırt eder
#: (``stripe.com/jobs/search?gh_jid=123``). Kimliği atmak, bir şirketin bütün
#: ilanlarını tek URL'e çökertip **yanlış birleştirir** — bu, gerçek ilanları
#: gizleyen ağır hatadır (gerçek korpusta 40 Stripe ilanı böyle çökmüştü).
_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "mc_cid", "mc_eid", "gh_src", "utm",
})


def _normalize_url(url: str) -> str:
    """URL'i **kaynaklar arası** karşılaştırma için normalize eder.

    Şema + ``www.`` atılır, host küçük harf, fragment atılır. Query'den yalnızca
    takip parametreleri çıkarılır; kalanı (özellikle iş kimliği) korunur ve
    sıralanır.

    **Anahtar yalnızca URL belirli bir ilana işaret ediyorsa üretilir:** ya
    ayırt edici bir query parametresi vardır, ya da yolun son segmenti bir
    kimlik taşır (rakam içerir). İkisi de yoksa — ``/careers/apply`` gibi genel
    bir kariyer sayfası — ``""`` döner ve birleştirmede kullanılmaz. Bu şart,
    aynı genel sayfayı paylaşan farklı ilanların yanlış birleşmesini önler.
    """
    if not url:
        return ""
    try:
        p = urllib.parse.urlsplit(url.strip())
    except ValueError:
        return ""
    host = (p.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return ""
    path = "/".join(s for s in (p.path or "").split("/") if s)
    kept = sorted((k, v) for k, v in urllib.parse.parse_qsl(p.query)
                  if k.lower() not in _TRACKING_PARAMS)
    query = "&".join(f"{k}={v}" for k, v in kept)

    last = path.rsplit("/", 1)[-1] if path else ""
    id_in_path = any(c.isdigit() for c in last)
    if not path or (not query and not id_in_path):
        return ""      # genel kariyer sayfası — belirli bir ilan değil
    return f"{host}/{path}" + (f"?{query}" if query else "")


#: Kaynak güvenilirlik/zenginlik katmanı — düşük = daha yetkili. Aynı ilan
#: birden çok kaynakta çıkarsa en zengin kopya kalır (D-039): doğrudan şirket
#: ATS'si tam açıklama + gerçek işveren + ilk-yayın tarihi taşır; toplayıcı
#: yalnızca snippet ve "son görülme" verir.
def _source_tier(job_id: str) -> int:
    sid = job_id.split(":", 1)[0]
    if sid.startswith("src-ats-"):
        return 0                        # doğrudan şirket panosu — en zengin
    if sid == "src-api-jooble":
        return 3                        # toplayıcı: snippet + işveren gizli olabilir
    if sid == "src-api-arbeitsagentur":
        return 2                        # açıklama metni yok
    return 1                            # açıklamalı public API'ler / fixture


def _fingerprint(text: str) -> str:
    return hashlib.sha256(" ".join(sorted(_tokens(text))).encode()).hexdigest()


def _tokens(text: str) -> set[str]:
    return set(_words(text))


# Blok içi eşleşme eşiği. Kalibrasyon hedefidir, evrensel doğru değildir —
# T-021 gerçek korpusla ölçüldüğünde yeniden ayarlanır (OPEN-09).
CONTENT_SIMILARITY_THRESHOLD = 0.75


def content_similarity(a: NormalizedPosting, b: NormalizedPosting) -> float:
    """İki ilanın metin örtüşmesi (Jaccard). 1.0 = birebir aynı metin."""
    ta, tb = a.tokens, b.tokens
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# Geçit B'de başlıkların da bir miktar örtüşmesi beklenir. Agency kopyası
# başlığı değiştirir ama tanınmaz hale getirmez ("Muhasebe Uzmanı" →
# "Finans ve Muhasebe Uzmanı Aranıyor").
TITLE_SIMILARITY_FLOOR = 0.3


def _title_similarity(a: NormalizedPosting, b: NormalizedPosting) -> float:
    ta, tb = set(a.title_key.split()), set(b.title_key.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


_ANON_MARKERS = ("gizli", "belirtilmemis", "firma adi", "confidential")


def _is_anonymous(p: NormalizedPosting) -> bool:
    return any(m in p.employer_key for m in _ANON_MARKERS)


def may_pair_via_gate_b(a: NormalizedPosting, b: NormalizedPosting) -> bool:
    """Geçit B'nin bu çifti değerlendirmeye alıp almayacağı.

    Geçit B **işveren gizlendiğinde** devreye girer. İki ilan aynı ve bilinen
    işverene aitse Geçit A zaten yetkilidir; B'nin araya girmesi aynı şirketin
    farklı ilanlarını birleştirir. Gerçekte olan buydu: iyzico'nun "Instore
    Sales Manager" ve "Senior AML Analyst" ilanları, paylaşılan şirket
    tanıtımı yüzünden %100 benzer çıkıp tek ilana indirgeniyordu.
    """
    same_known_employer = (
        a.employer_key == b.employer_key
        and a.employer_key
        and not _is_anonymous(a)
    )
    if same_known_employer:
        return False
    return _title_similarity(a, b) >= TITLE_SIMILARITY_FLOOR


def normalize(raw: RawPosting, *, adapter_version: str) -> NormalizedPosting:
    if raw.raw_requirements:
        # Fixture'lar şartları hazır verir.
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
        occupation = raw.occupation_id
    else:
        # Gerçek ilanlar serbest metindir; şartlar sözlükten çıkarılır.
        # Extraction ayrı bir alt sistem değil, normalize'ın parçasıdır (ARC-01).
        from .extract import extract_requirements, infer_occupation

        reqs = extract_requirements(raw.title, raw.description)
        occupation = raw.occupation_id or infer_occupation(raw.title, reqs)
    from . import fairness as _fair
    from . import jobmeta as _jm
    from . import salary as _sal

    _meta = _jm.detect(title=raw.title, city=raw.city, description=raw.description,
                       source_arrangement=raw.arrangement)
    _fairness = tuple(_fair.scan(raw.title, raw.description))
    _salary = _sal.extract(raw.description)
    _salary_status = (
        "found" if _salary
        else ("unreadable" if _sal.mentions_money(raw.description) else "not_stated")
    )

    job = JobPosting(
        job_id=f"{raw.source_id}:{raw.source_posting_ref}",
        title=raw.title,
        employer=raw.employer,
        city=raw.city,
        occupation_id=occupation,
        source=registry.get(raw.source_id).name,
        requirements=reqs,
        is_public_sector=raw.is_public_sector,
        # Kıdem eşleşmeye girer (D-063): "Senior" bir rol, metinde yazmasa da
        # örtük bir kıdem şartıdır. `NormalizedPosting.experience_level` filtre
        # ve rozet için duruyor; burada job'a da geçmesi gerekiyor çünkü
        # `match()` yalnızca JobPosting görür.
        experience_level=_meta.experience_level,
    )
    return NormalizedPosting(
        job=job,
        employer_key=normalize_employer(raw.employer),
        title_key=normalize_title(raw.title),
        city_key=" ".join(_words(raw.city)),
        content_fingerprint=_fingerprint(raw.description),
        job_text=raw.description,
        work_arrangement=_meta.work_arrangement,
        employment_type=_meta.employment_type,
        experience_level=_meta.experience_level,
        salary=_salary,
        salary_status=_salary_status,
        fairness_flags=_fairness,
        url=raw.url,
        posted_at=raw.posted_at,
        refreshed_at=raw.refreshed_at,
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

    # Geçit U — aynı normalize URL = aynı ilan (D-039). Kaynaklar arası temel
    # dedupe lever'i: toplayıcının kaynağa verdiği link, bizim doğrudan çektiğimiz
    # ATS URL'iyle çakışırsa iki kayıt tek sayılır. URL eşitliği tanım gereği
    # kesindir; içerik benzerliğinin aksine yanlış-birleştirme riski taşımaz.
    buckets_u: dict[str, list[NormalizedPosting]] = {}
    for p in postings:
        k = p.url_key
        if k:
            buckets_u.setdefault(k, []).append(p)
    for group in buckets_u.values():
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
            if not may_pair_via_gate_b(x, y):
                continue
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

    Öncelik sırası: (1) **kaynak katmanı** — doğrudan şirket ATS'si toplayıcıya
    yeğlenir, çünkü tam açıklama + gerçek işveren + ilk-yayın tarihi taşır;
    toplayıcı yalnızca snippet verir. (2) İşvereni açıkça yazan kayıt (agency'nin
    gizlediği sürüm daha az bilgi verir, FR-206). (3) En erken yayın tarihi.
    """
    # employer_key katlanmış olduğu için işaretler de katlanmış yazılır.
    _ANON = ("gizli", "belirtilmemis", "firma adi", "gizli firma")

    def rank(p: NormalizedPosting) -> tuple[int, int, str]:
        anonymous = any(w in p.employer_key for w in _ANON)
        return (_source_tier(p.job.job_id), 1 if anonymous else 0,
                p.posted_at or "9999")

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


# --------------------------------------------------------------------------
# Gerçek kaynak ingest'i (D-020)
# --------------------------------------------------------------------------

LIVE_ADAPTER_VERSION = "ats-0.1.0"

# --------------------------------------------------------------------------
# Tazelik (D-024)
# --------------------------------------------------------------------------
#
# Bir iş ilanı, yayınlandıktan sonra süresiz geçerli değildir. Kaynakların çoğu
# kapanan ilanı listeden düşürür ama hepsi düşürmez ve düşürme gecikebilir.
# Yayın tarihi eskiyen ilan **gösterilmez**: kullanıcıyı kapanmış bir ilana
# yönlendirmek, ona hiç ilan göstermemekten daha kötüdür.
#
# Tarihi **bilinmeyen** ilan atılmaz — bu bir `unknown` durumudur ve D-011'in
# aynı mantığı burada da geçerlidir: bilmemek, kötü olduğunu varsaymak için
# gerekçe değildir. Böyle ilanlar gösterilir ama "tarih bilinmiyor" olarak
# işaretlenir ve tarihe göre sıralamada sona düşer.
MAX_AGE_DAYS = 45


def age_in_days(posted_at: str | None, *, today: date | None = None) -> int | None:
    """İlanın yaşı (gün). Tarih yoksa veya ayrıştırılamıyorsa None."""
    if not posted_at:
        return None
    try:
        d = date.fromisoformat(str(posted_at)[:10])
    except ValueError:
        return None
    return max(0, ((today or date.today()) - d).days)


def is_fresh(posting: NormalizedPosting, max_age_days: int = MAX_AGE_DAYS) -> bool:
    """İlan hâlâ gösterilecek kadar canlı mı? Tarihi bilinmeyen ilan **elenmez**.

    Eleme **son hareket** tarihine bakar (`refreshed_at`, yoksa `posted_at`),
    ilanın yaşına değil. İkisi bilinçli olarak ayrılmıştır:

    * **Yaş** (`posted_at`) kullanıcıya gösterilir: "bu ilan 96 gündür açık"
      bilmesi gereken bir şeydir ve hayalet ilan şüphesinin temelidir.
    * **Canlılık** (`refreshed_at`) elemeyi belirler: ATS ilanı hâlâ
      listeliyorsa ve işveren dokunmaya devam ediyorsa, ilan açıktır.

    Elemeyi yaşa bağlamak, açık olduğunu bildiğimiz ilanların %45'ini
    gizlerdi — kullanıcıya yardım değil, fırsat saklamak olurdu. Doğru
    davranış: göstermek ama yaşını **açıkça** söylemek.
    """
    age = age_in_days(posting.refreshed_at or posting.posted_at)
    return age is None or age <= max_age_days


def days_open(posting: NormalizedPosting) -> int | None:
    """İlanın kaç gündür açık olduğu — gerçek yayın tarihinden."""
    return age_in_days(posting.posted_at)

def _fetch_all_boards(boards) -> tuple[list, list[dict], list[dict]]:
    """Panoları çeker. Aynı host'a ait istekler sıralı, farklı host'lar paralel.

    ``Crawl-delay: 1`` **host başınadır**; 70 panoyu tek sırada çekmek 70+ saniye
    sürerdi. Host'lara bölmek gecikmeyi korurken süreyi platform sayısına düşürür.
    """
    from concurrent.futures import ThreadPoolExecutor

    from .adapters.ats import Board, FetchError, fetch_board

    by_platform: dict[str, list] = {}
    for source_id, platform, slug, employer in boards:
        by_platform.setdefault(platform, []).append(
            Board(source_id=source_id, platform=platform, slug=slug, employer=employer)
        )

    raws, fetched, errors = [], [], []

    def run_platform(group):
        local_raws, local_fetched, local_errors = [], [], []
        for board in group:
            try:
                registry.assert_fetchable(board.source_id)
                items, truncated = fetch_board(board)
            except Exception as e:
                # Tek bir pano bütün koşuyu düşüremez. Hata **yutulmuyor**;
                # `errors` listesine girip ingest raporunda ve arayüzde görünüyor.
                # `source_id` meta'ya yazılır (D-065): kısmi tazeleme, hangi
                # kaydın hangi kaynağa ait olduğunu bilmeden eski meta'yı
                # koruyamaz. Pano meta'sı "platform/slug", API meta'sı
                # source_id kullanıyordu — geri eşleme güvenilir değildi.
                local_errors.append({"board": f"{board.platform}/{board.slug}",
                                     "source_id": board.source_id,
                                     "error": f"{type(e).__name__}: {e}"[:200]})
                continue
            local_raws.extend(items)
            local_fetched.append({"board": f"{board.platform}/{board.slug}",
                                  "source_id": board.source_id,
                                  "employer": board.employer,
                                  "count": len(items), "truncated": truncated})
        return local_raws, local_fetched, local_errors

    with ThreadPoolExecutor(max_workers=len(by_platform) or 1) as ex:
        for r, f, e in ex.map(run_platform, by_platform.values()):
            raws.extend(r); fetched.extend(f); errors.extend(e)

    return raws, fetched, errors


def _board_source(entry: dict) -> str | None:
    """Meta/hata kaydının kaynağı. Kısmi tazeleme (D-065) buna dayanır."""
    return entry.get("source_id")


def _fetch_api_sources(only: set[str] | None = None
                       ) -> tuple[list, list[dict], list[dict]]:
    """Pano tabanlı olmayan izinli API kaynakları (D-023).

    ``only`` verilirse yalnızca o kaynaklar çekilir — ``min_poll_hours``
    süresi gelmeyenler atlanır (D-065).
    """
    from .adapters.public_apis import FETCHERS

    raws, meta, errors = [], [], []
    for rec in registry.api_sources():
        if only is not None and rec.source_id not in only:
            continue
        fetch = FETCHERS.get(rec.source_id)
        if fetch is None:
            continue
        try:
            registry.assert_fetchable(rec.source_id)
            items = fetch(rec.source_id)
        except Exception as e:
            errors.append({"board": rec.name, "source_id": rec.source_id,
                           "error": str(e)[:160]})
            continue
        raws.extend(items)
        meta.append({"board": rec.source_id, "source_id": rec.source_id,
                     "employer": rec.name, "count": len(items), "truncated": 0})
    return raws, meta, errors


def _cache_path(root: Path | None = None) -> Path:
    return (root or REPO_ROOT) / ".cache" / "ats_postings.json"


def _due_sources(son_cekim: dict[str, str], simdi: datetime | None = None
                 ) -> tuple[set[str], dict[str, float]]:
    """Hangi kaynakların çekim zamanı geldi? (D-065)

    Her kaynak kaydı ``min_poll_hours`` beyan eder ama bu alan bugüne kadar
    **hiçbir yerde uygulanmıyordu** — yalnızca testte "> 0" diye kontrol
    ediliyordu. Sonuç: global tazeleme aralığı (6 saat) bütün kaynaklara
    dayatılıyordu. Jooble bunu somut bir riske çeviriyor: kayıtta 12 saat
    yazıyor, anahtarın 500 istek sınırı var ve her çekim ~120 istek harcıyor —
    6 saatte bir çekim günde 480 istek eder, yani sınıra yapışır.

    Döner: (zamanı gelen source_id kümesi, atlanan kaynak → kalan saat).
    """
    simdi = simdi or datetime.now()
    gelen: set[str] = set()
    atlanan: dict[str, float] = {}
    for rec in registry.REGISTRY.values():
        aralik = rec.min_poll_hours
        ts = son_cekim.get(rec.source_id)
        if not ts:
            gelen.add(rec.source_id)      # hiç çekilmemiş → sırası
            continue
        try:
            gecen = (simdi - datetime.fromisoformat(ts)).total_seconds() / 3600
        except Exception:
            gelen.add(rec.source_id)      # bozuk damga → güvenli taraf: çek
            continue
        if gecen >= aralik:
            gelen.add(rec.source_id)
        else:
            atlanan[rec.source_id] = round(aralik - gecen, 2)
    return gelen, atlanan


# Okuma/yazma :mod:`cache` modülüne taşındı; oradaki asıl mesele hız değil
# **geçersizleştirme**: çıkarım mantığı değiştiğinde işlenmiş kayıtlar bayat
# kalırsa, yapılan değişikliğin etkisi hiç görünmez.


def run_live_ingest(
    *,
    include_fixtures: bool = False,
    cache_hours: float = 6.0,
    force_refresh: bool = False,
    stale_ok: bool = False,
    max_age_days: int = MAX_AGE_DAYS,
) -> dict:
    """Registry'de izinli ATS panolarından **gerçek** ilanları çeker.

    Her pano için :func:`registry.assert_fetchable` çağrılır — kapı budur.
    Bir pano hata verirse kayıtlar sessizce atılmaz; ``errors`` listesine girer
    (access-change sinyali olabilir).

    Bölge filtresi **uygulanmaz**: hangi bölgenin gösterileceği kullanıcının
    kararıdır (D-009 — pazara özgü davranış core'a gömülmez). Her ilan
    :mod:`regions` ile etiketlenir ve filtreleme arayüzde yapılır.
    """
    from . import cache as _cache

    path = _cache_path()
    # ``stale_ok``: yaş kontrolünü atla ve **ne varsa** onu kullan — ağ beklemeden.
    # Amaç, açılışta siteyi anında ayağa kaldırmak: eski cache hemen servis
    # edilir, tazeleme arka planda yapılır (D-047). Yaşı geçmiş cache "yok"
    # sayılıp yeniden çekilirse site dakikalarca kapalı kalıyordu.
    #
    # ``accept_stale_logic``: açılışta parmak izi eşleşmese de ne varsa kullan
    # (D-055). Aksi hâlde ingest koduna dokunan her dağıtım korpusu SIFIRLIYOR;
    # canlıda bu yaşandı ve site "0 ilan" gösterdi.
    effective_hours = 1e12 if stale_ok else cache_hours
    cached = None if force_refresh else _cache.read(
        path, effective_hours, accept_stale_logic=stale_ok)
    from_cache = cached is not None
    stale_logic = bool(cached and cached.get("stale_logic"))
    # Çıkarım mantığı değişmişse işlenmiş kayıtlar geçersizdir; ham kayıtlar
    # yine de kullanılır — yeniden **çekim** gerekmez, yalnızca yeniden çıkarım.
    reused_extraction = bool(cached and cached["postings"])

    son_cekim: dict[str, str] = {}
    atlanan: dict[str, float] = {}
    if cached is None:
        if stale_ok:
            # Hızlı mod + cache yok: ağa çıkmayız. Site (varsa fixture'la) açılır,
            # gerçek veri arka plan yenilemesinde gelir.
            raws, fetched_boards, errors = [], [], []
        else:
            # KISMİ TAZELEME (D-065): önbellek bayat ama içindeki her kaynağın
            # ham kayıtları bayat değil. Yaş sınırı OLMADAN okuyup, yalnızca
            # ``min_poll_hours`` süresi geçmiş kaynakları çekeriz; kalanların
            # kayıtları korunur. Böylece kaynak kaydındaki nezaket aralığı
            # gerçekten uygulanır ve Jooble'ın istek bütçesi yarıya iner.
            onceki = _cache.read(path, 1e12, accept_stale_logic=True)
            eski_raws = onceki["raws"] if onceki else []
            eski_meta = onceki["meta"] if onceki else {}
            son_cekim = dict(eski_meta.get("source_fetched_at") or {})
            gelen, atlanan = _due_sources(son_cekim)

            raws = [r for r in eski_raws
                    if r.source_id in atlanan]          # sırası gelmeyenler korunur
            # Meta/hata kayıtları da korunur. NOT: `source_id` alanı D-065 ile
            # eklendi; ondan ÖNCE yazılmış bir önbellekte bu alan yok ve o
            # kayıtlar bir kez düşer (ilanlar düşmez — RawPosting.source_id
            # gerçek bir alan). Kaynak bir sonraki çekiminde meta'sı geri gelir.
            fetched_boards = [b for b in (eski_meta.get("boards") or [])
                              if _board_source(b) in atlanan]
            errors = [e for e in (eski_meta.get("errors") or [])
                      if _board_source(e) in atlanan]

            due_boards = [b for b in registry.BOARDS if b[0] in gelen]
            if due_boards:
                b_raws, b_meta, b_err = _fetch_all_boards(due_boards)
                raws.extend(b_raws)
                fetched_boards.extend(b_meta)
                errors.extend(b_err)
            api_raws, api_meta, api_errors = _fetch_api_sources(only=gelen)
            raws.extend(api_raws)
            fetched_boards.extend(api_meta)
            errors.extend(api_errors)

            simdi = datetime.now().isoformat(timespec="seconds")
            for sid in gelen:
                son_cekim[sid] = simdi
    else:
        raws = cached["raws"]
        fetched_boards = cached["meta"].get("boards", [])
        errors = cached["meta"].get("errors", [])
        son_cekim = dict(cached["meta"].get("source_fetched_at") or {})

    if reused_extraction:
        normalized = cached["postings"]
    else:
        normalized = [normalize(r, adapter_version=LIVE_ADAPTER_VERSION) for r in raws]
        if raws:
            _cache.write(path, raws=raws, postings=normalized,
                         meta={"boards": fetched_boards, "errors": errors,
                               # Kaynak başına son çekim damgası (D-065) —
                               # kısmi tazelemenin belleği. Yazılmazsa her
                               # koşuda her şey "sırası gelmiş" sayılır.
                               "source_fetched_at": son_cekim})

    fetched_total = len(normalized)

    # D-024: süresi geçmiş ilan gösterilmez. Eleme sessiz değildir.
    fresh = [p for p in normalized if is_fresh(p, max_age_days)]
    stale_dropped = len(normalized) - len(fresh)
    normalized = fresh

    if include_fixtures:
        normalized.extend(run_fixture_ingest()["postings"])

    clusters, oversized = cluster(normalized)
    canonical = {cid: pick_canonical(group) for cid, group in clusters.items()}

    return {
        "source": "ATS public API'leri" + (" + fixture" if include_fixtures else ""),
        "boards": fetched_boards,
        "errors": errors,
        "from_cache": from_cache,
        "reused_extraction": reused_extraction,
        # Nezaket aralığı yüzünden bu koşuda atlanan kaynaklar (D-065).
        # **Sessiz değil**: /api/health ve Kaynaklar sayfası bunu gösterebilir;
        # "kaynak neden güncellenmedi" sorusunun cevabı burada.
        "skipped_sources": atlanan,
        # Açılışta eski mantıkla işlenmiş önbellek kullanıldı mı (D-055).
        # Sessiz kalmaz: arayüz/health bunu gösterir, arka plan tazelemesi
        # bitince kendiliğinden False'a döner.
        #
        # `reused_extraction` ŞARTI (D-083). Bayrak yalnızca önbellek
        # OKUMASINDAN hesaplanıyordu ve yanlış rapor veriyordu: sözlük
        # değiştikten sonraki tazelemede parmak izi tutmaz (`stale_logic`
        # True), ama tam da bu yüzden işlenmiş kayıtlar atılıp YENİDEN
        # ÇIKARIM yapılır. Yani bellekteki korpus taze, bayrak "bayat" diyor.
        #
        # D-082 dağıtımında canlıda görüldü: yeni token'lar ilanlardan
        # okunuyordu (kimya mühendisi ilanları eşleşiyordu) ama /api/health
        # hâlâ `stale_logic: true` gösteriyordu. Operatör için bu, doğru bir
        # dağıtıma güvenmemek ya da gereksiz bir tazeleme daha tetiklemek
        # demek. Doğru soru "önbellek bayat mıydı" değil, "SERVİS ETTİĞİMİZ
        # korpus bayat mantıkla mı üretildi".
        "stale_logic": stale_logic and reused_extraction,
        "fetched": fetched_total,
        "stale_dropped": stale_dropped,
        "max_age_days": max_age_days,
        "truncated": sum(b.get("truncated", 0) for b in fetched_boards),
        "canonical": len(clusters),
        "duplicates_merged": len(normalized) - len(clusters),
        "oversized_blocks": oversized,
        "postings": normalized,
        "clusters": clusters,
        "canonical_postings": canonical,
    }
