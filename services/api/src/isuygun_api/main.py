"""İşe Uygun API.

Bu katman iş kuralı **içermez**. Değerlendirme mantığının tamamı
``isuygun_core``'da, ilan toplama mantığının tamamı ``isuygun_ingest``'tedir.
API yalnızca onları HTTP'ye açar — kural burada tekrar edilirse iki yerde
birbirinden sapar.

OpenAPI şeması ``/openapi.json`` adresinden alınır; TypeScript tipleri bundan
üretilir (ADR-001 şema kayması önlemi).
"""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException, Response, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from isuygun_core import build_explanation, match
from isuygun_core.domain import (
    GATE_RELEVANT_CATEGORIES,
    NON_DISCRIMINATIVE_CATEGORIES,
    CareerProfile,
    JobPosting,
    MatchBand,
    ProfileFact,
)
from isuygun_ingest import regions, registry, search
from isuygun_ingest.pipeline import age_in_days

from . import signals
from .cv import read_cv
from .store import STORE


def _classic_enabled() -> bool:
    """Eski (sunucu-profilli) yüzey açık mı?

    D-059: profiller istemciye taşındı; sunucudaki tek-global-profil uçları
    ancak ``ISUYGUN_CLASSIC=1`` ile açılır. Üretimde kapalı kalır — açık olsaydı
    /classic'e giren herkes aynı profili paylaşmaya devam ederdi (canlıda
    doğrulanan gizlilik açığı). Geliştirmede launch.json açar; testler
    conftest'te açar. Her istekte okunur ki testler monkeypatch'leyebilsin.
    """
    return os.environ.get("ISUYGUN_CLASSIC", "") == "1"

MAX_CV_BYTES = 10 * 1024 * 1024


def _now_iso() -> str:
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")

def _load_local_env() -> None:
    """`.env.local` varsa ortam değişkenlerine yükler.

    Sırlar (Jooble API anahtarı gibi) **git'e girmemeli**; `.env.local`
    .gitignore'dadır ve koda gömülmez. Zaten tanımlı bir değişken **ezilmez**:
    dış ortam (launch.json / sistem) önceliklidir, böylece CI veya prod'da
    dosya olmadan da çalışır.
    """
    path = Path(__file__).resolve().parents[4] / ".env.local"
    if not path.is_file():
        return
    # utf-8-sig: Windows PowerShell 5.1'in `Out-File -Encoding utf8`'i dosya
    # başına BOM ekler; düz utf-8 ile okunursa ilk anahtarın adına görünmez bir
    # önek yapışır ve değişken hiç eşleşmez. utf-8-sig BOM'u sessizce yer.
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip().lstrip("﻿")
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


@asynccontextmanager
async def lifespan(_: FastAPI):
    import asyncio

    _load_local_env()
    # Açılış siteyi ASLA dakikalarca kapalı tutmamalı (D-047). Önce eski cache'le
    # anında ayağa kalk; ağ çekimini (gerekirse) arka planda yap ve sonucu yerine
    # koy. Cache 6 saatten eskiyse eskiden `STORE.load()` senkron re-fetch yapıyor
    # ve site ~7 dk boyunca hiç yanıt vermiyordu.
    #
    # ``include_fixtures=False``: fixture'lar dev-only test verisidir (D-018) ve
    # üretim imajına kopyalanmaz. Taze bir prod container'da cache boşken bunları
    # istemek "Fixture dizini yok" ile açılışı çökertiyordu — canlı sitede
    # istenmeyen "geliştirme" ilanları da göstermezler.
    STORE.load(stale_ok=True, include_fixtures=False)

    async def _bg_refresh():
        # Açılışta bir kez tazele, sonra periyodik (D-049). Canlı sunucu uzun
        # süre ayakta kaldığından, tazelemeyi yalnızca açılışa bağlamak korpusu
        # günlerce bayat bırakırdı. Aralık cache TTL'iyle (6 saat) uyumlu.
        hours = float(os.environ.get("ISUYGUN_REFRESH_HOURS", "6") or 6)
        while True:
            # Durum DIŞARIDAN görünür olmalı (D-055). Eskiden hata `pass` ile
            # yutuluyordu: canlıda korpus 0 ilanda kaldı ve tazelemenin çalışıp
            # çalışmadığını, çöküp çökmediğini anlamanın hiçbir yolu yoktu —
            # /api/health "ok" diyor, site boş.
            STORE.refresh_state = {"status": "running",
                                   "started_at": _now_iso(), "error": None}
            try:
                await asyncio.to_thread(STORE.refresh)
                STORE.refresh_state = {"status": "ok", "finished_at": _now_iso(),
                                       "error": None}
            except Exception as e:
                # Eski korpus yerinde kalır ama sebep artık kayıtlı.
                STORE.refresh_state = {"status": "failed", "finished_at": _now_iso(),
                                       "error": f"{type(e).__name__}: {e}"[:300]}
            await asyncio.sleep(max(0.5, hours) * 3600)

    task = asyncio.create_task(_bg_refresh())
    yield
    task.cancel()


app = FastAPI(
    lifespan=lifespan,
    title="JoblyFit API",
    version="0.1.0",
    description=(
        "Fixture veriyle çalışan MVP çekirdeği. Gerçek ilan kaynağına bağlı "
        "DEĞİLDİR (D-018)."
    ),
)


#: Sunucu-profilli eski yüzeyin uçları (D-059). Ortak tek profile okuyup
#: yazarlar; ziyaretçi izolasyonu olmadığı için üretimde kapatılırlar.
#: (yöntem, yol-öneki) çiftleri; None = her yöntem.
_LEGACY_RULES: tuple[tuple[str | None, str], ...] = (
    (None, "/api/profile"),      # /api/profile, /api/profile/*, /api/profiles*
    ("GET", "/api/feed"),        # global profille feed
    ("POST", "/api/jobs/evaluate"),
    (None, "/classic"),
)


@app.middleware("http")
async def _legacy_gate(request, call_next):
    """``ISUYGUN_CLASSIC=1`` değilse eski yüzeyi 404'e kapatır.

    Middleware tercih edildi çünkü tek tek route'lara bağımlılık eklemek ~12
    dokunuş demekti ve birini atlamak sessiz bir gizlilik deliği olurdu; tek
    liste, tek karar noktası. Testler bayrağı conftest'te açar.
    """
    if not _classic_enabled():
        path = request.url.path
        for method, prefix in _LEGACY_RULES:
            if path.startswith(prefix) and (method is None or request.method == method):
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    {"detail": "Bu uç emekli (D-059): profiller artık istemcide. "
                               "Geliştirme için ISUYGUN_CLASSIC=1."},
                    status_code=404,
                )
    return await call_next(request)


# --------------------------------------------------------------------------
# Şemalar — OpenAPI çıktısının kaynağı
# --------------------------------------------------------------------------


class ExplanationLineOut(BaseModel):
    text: str
    evidence: str
    action_label: str | None = None


class FairnessFlagOut(BaseModel):
    category: str
    note: str
    evidence: str
    severity: str = "hard"


class JobSummary(BaseModel):
    job_id: str
    title: str
    employer: str
    city: str
    occupation_id: str
    source: str
    url: str
    posted_at: str | None = None
    is_public_sector: bool
    duplicate_count: int = Field(1, description="Bu ilanın kaç kopyası birleştirildi")
    band: str | None = Field(None, description="null ise değerlendirme yapılamadı")
    band_label: str | None = None
    confidence_label: str | None = None
    listing_only: bool = False
    insufficient_data: bool = False
    met_count: int = 0
    unmet_count: int = 0
    unknown_count: int = 0
    worth_applying: str = ""
    worth_applying_rule: str = ""
    #: Kartta gösterilecek kısa şart önizlemesi
    top_requirements: list[str] = []
    matched_requirements: list[str] = []
    #: Konumdan türetilen bölge etiketleri (bir ilan birden fazlasına ait olabilir)
    regions: list[str] = []
    #: İlan konumundan çıkarılan **il/şehir** (D-056). Ham `city` filtre için
    #: kullanılamaz: aynı il beş ayrı yazımla geliyor ("İstanbul",
    #: "İstanbul Avrupa", "İstanbul, Kadıköy"…) ve her biri ayrı seçenek gibi
    #: görünüyordu. Boş = şehir belirtilmemiş; bu uydurulmaz (D-011).
    city_group: str = ""
    #: Aynı rolün diğer konumları. Bunlar **ayrı ilanlardır** (her birinin kendi
    #: URL'i var) ve birleştirilmez; yalnızca listede tek satır olarak gösterilir.
    other_locations: list[str] = []
    #: İlanın yaşı (gün) — **gerçek ilk yayın** tarihinden. null = bilinmiyor.
    age_days: int | None = None
    #: Kaynağın ilanı son güncellediği tarihten bu yana geçen gün. Elemede bu
    #: kullanılır; `age_days` ise kullanıcıya gösterilir. İkisini karıştırmak,
    #: 96 gündür açık bir ilanı "5 gün önce" göstermekti (D-035).
    refreshed_days: int | None = None
    #: İlan uzun süredir mi açık? Hayalet ilan şüphesinin somut göstergesi.
    long_open: bool = False
    #: İlanda yazan maaş — kaynaktaki birimiyle, dönüştürülmeden.
    salary_text: str | None = None
    #: found | not_stated | unreadable. "Yazmamış" ile "okuyamadım" ayrıdır:
    #: ikincisini ilkine katmak, maaşını yazan ilana haksızlık olurdu (D-029).
    salary_status: str = "not_stated"
    #: Maaşın para birimi ve yıllık karşılığı. Asgari maaş filtresi bunları
    #: kullanır ama **yalnızca tek para birimi içinde**: kur çevirisi yapmadan
    #: karşılaştırma yanlış, çeviri yapmak ise uydurma olurdu (D-029).
    salary_currency: str | None = None
    salary_min_yearly: float | None = None
    #: remote | hybrid | onsite | null. null "ofisten" DEĞİL, "belirtilmemiş".
    work_arrangement: str | None = None
    #: part_time | contract | internship | null (tam zamanlı varsayılmaz)
    employment_type: str | None = None
    #: Kıdem basamağı: intern | junior | mid | senior | lead | architect |
    #: executive | null. null "orta seviye" DEĞİL, "belirtilmemiş" — ilanların
    #: çoğu başlıkta kıdem söylemez ve bunu uydurmuyoruz (D-011).
    experience_level: str | None = None
    #: Ayrımcı/dışlayıcı dil işaretleri (D-042). Boş = temiz. Hüküm değil,
    #: bilgilendirme; kullanıcıya haklarını hatırlatır.
    fairness_flags: list[FairnessFlagOut] = []


class JobDetail(JobSummary):
    description: str = Field("", description="İlanın kaynaktaki tam metni")
    why: list[str] = []
    met: list[ExplanationLineOut] = []
    unmet: list[ExplanationLineOut] = []
    unknown: list[ExplanationLineOut] = []
    legal_eligibility_notices: list[str] = []
    verification_notice: str | None = None
    listing_only_note: str | None = None
    insufficient_data_note: str | None = None
    disclaimer: str


class FeedOut(BaseModel):
    evaluated: list[JobSummary]
    unevaluated: list[JobSummary] = Field(
        default_factory=list,
        description=(
            "Profil bilgisi yetmediği için değerlendirilemeyen ilanlar (D-019). "
            "Bunlar 'uymuyor' DEĞİLDİR ve bant üzerinden sıralanamaz — OPEN-22."
        ),
    )
    profile_is_empty: bool
    #: Profil kalıcı mı? False ise sunucu kapanınca kaybolur — arayüz uyarır.
    profile_is_persistent: bool = True
    #: Hangi depo kullanılıyor: postgres | sqlite | memory
    profile_backend: str = "memory"
    ingest: dict
    #: Arayüzdeki filtre seçenekleri — korpustan türetilir, sabit liste değil.
    facets: dict = Field(default_factory=dict)


class CatalogItemOut(BaseModel):
    key: str
    label: str
    category: str
    category_label: str
    occupation_id: str
    occupation_label: str
    asks_years: bool
    needs_verification: bool


class FactOut(BaseModel):
    key: str
    label: str
    category: str
    verification: str
    years: float | None = None
    counts_as_present: bool


class ProfileOut(BaseModel):
    occupation_ids: list[str]
    facts: list[FactOut]
    pending_cv_suggestions: list[dict]


class FactIn(BaseModel):
    key: str
    years: float | None = None
    verified: bool = False


class OccupationsIn(BaseModel):
    occupation_ids: list[str]


class PastedJobIn(BaseModel):
    """Kullanıcının elle getirdiği ilan metni.

    **Bu bir scraping ucu değildir.** Sunucu hiçbir adrese istek atmaz; metni
    kullanıcı kendi ekranından kopyalayıp yapıştırır. `url` yalnızca kullanıcının
    geri dönebilmesi için saklanır ve **çekilmez**.
    """

    text: str = Field(..., min_length=40,
                      description="İlanın metni — kullanıcı tarafından yapıştırılır")
    title: str = ""
    employer: str = ""
    city: str = ""
    url: str = ""


class SourceOut(BaseModel):
    source_id: str
    name: str
    access_method: str
    scraping_permission: str
    policy_risk: str
    status: str
    may_fetch_network: bool
    note: str
    permission_evidence: str = ""
    attribution_required: bool = False
    redistribution_policy: str = ""


# --------------------------------------------------------------------------
# Yardımcılar
# --------------------------------------------------------------------------

_BAND_ORDER = {MatchBand.STRONG: 0, MatchBand.GOOD: 1, MatchBand.CONDITIONAL: 2,
               MatchBand.WEAK: 3}

# D-008 — kalibre edilmiş meslek kümeleri. Hiçbiri golden set'le ölçülmedi
# (T-006b açık), bu yüzden liste bilinçli olarak **boştur**: her ilan düşük
# confidence ile gösterilir. Kalibre olmadan "yüksek güven" demek, ölçülmemiş
# bir şeye güven iddia etmek olurdu.
_CALIBRATED: set[str] = set()


def _evaluate(posting, profile: CareerProfile):
    """Tek ilanı verilen profile karşı değerlendirir.

    Profil artık parametre (D-059): eskiden buradan STORE.profile okunuyordu ve
    o tek global profil bütün ziyaretçiler arasında paylaşılıyordu — B, A'nın
    becerileriyle hesaplanmış eşleşmeler görüyordu.
    """
    job = posting.job
    result = match(
        job,
        profile,
        calibrated_occupation=job.occupation_id in _CALIBRATED,
    )
    return result, build_explanation(result)


#: İstemcinin gönderdiği geçici profil (D-059). Sunucuda SAKLANMAZ: istek
#: süresince değerlendirmeye girer, sonra yok olur. Kalıcı kopya kullanıcının
#: tarayıcısındadır.
class ProfilePayload(BaseModel):
    facts: list[FactIn] = []
    occupation_ids: list[str] = []


def _profile_from_payload(body: ProfilePayload | None) -> CareerProfile:
    """Gövdeden geçici :class:`CareerProfile` kurar.

    Sunucu tarafı kuralları burada da geçerlidir — HTTP sınırından gelen veri
    onları esnetemez:

    * Yasal uygunluk alanları (D-013) sessizce atlanır: istemci ``legal_*``
      gönderse bile profile girmez, skora değmez.
    * Katalogda olmayan anahtar atlanır (eski istemci / bozuk veri).
    * ``verified`` bayrağı istemci beyanıdır; bugünkü doğrulama da zaten
      simülasyondur (D-012 notu arayüzde). Yanlış beyan yalnızca beyan edenin
      kendi sonuçlarını etkiler.
    """
    facts: list[ProfileFact] = []
    if body is not None:
        for f in body.facts[:200]:
            item = STORE.catalog_item(f.key)
            if item is None or item.is_legal_eligibility:
                continue
            years = None
            if f.years is not None:
                years = max(0.0, min(60.0, float(f.years)))
            facts.append(ProfileFact(
                key=f.key, category=item.category,
                verification="verified" if f.verified else "user_asserted",
                years=years,
            ))
    return CareerProfile(
        profile_id="istemci",
        facts=tuple(facts),
        occupation_ids=tuple((body.occupation_ids if body else [])[:50]),
    )


def _role_key(employer: str, title: str) -> tuple[str, str]:
    """Liste satırının kimliği.

    Tek yerde tanımlı: hem gösterim birleştirmesi hem de "kaç ilan açılır"
    sayımı bunu kullanır. İki yerde ayrı yazılsaydı biri değişince diğeri
    sessizce sapardı ve sonuç yine yanlış sayı olurdu.
    """
    return (employer.casefold(), title.casefold())


def _group_by_role(items: list[JobSummary]) -> list[JobSummary]:
    """Aynı işverenin aynı rolünü farklı konumlarda tek satıra indirir.

    Greenhouse gibi sistemlerde bir rol her konum için ayrı ilan olarak
    yayınlanır; feed'de "AI Infrastructure Engineer" üç kez görünüyordu.
    Bunlar **duplicate değildir** (ayrı URL, ayrı konum), bu yüzden ingest
    katmanında birleştirilmezler — burada yalnızca *gösterim* birleştirilir ve
    diğer konumlar ``other_locations``'ta korunur.
    """
    out: list[JobSummary] = []
    seen: dict[tuple[str, str], JobSummary] = {}
    for j in items:
        key = _role_key(j.employer, j.title)
        first = seen.get(key)
        if first is None:
            seen[key] = j
            out.append(j)
        elif j.city and j.city not in first.other_locations and j.city != first.city:
            first.other_locations.append(j.city)
    return out


def _canonicalize_cities(*groups: list[JobSummary]) -> None:
    """``city_group`` anahtarlarını tek bir **gösterim adına** çevirir (D-056).

    Aynı il farklı yazımlarla geliyor ("İstanbul" / "Istanbul" / "İSTANBUL").
    Anahtar hepsini birleştirir ama ekranda tek bir ad görünmeli; en çok
    kullanılan yazım kazanır. Sabit bir il listesi tutmak yerine korpustan
    türetilir: liste Türkiye dışında da (243 ABD, 421 Avrupa şehri) çalışır ve
    yeni bir şehir geldiğinde elle güncelleme gerektirmez.
    """
    from collections import Counter

    aday: dict[str, Counter] = {}
    for g in groups:
        for j in g:
            if j.city_group:
                aday.setdefault(j.city_group, Counter())[
                    regions.city_of(j.city)[1]] += 1
    ad = {k: c.most_common(1)[0][0] for k, c in aday.items() if c}
    for g in groups:
        for j in g:
            if j.city_group:
                j.city_group = ad.get(j.city_group, j.city_group)


def _absorb_into(items: list[JobSummary],
                 winners: list[JobSummary]) -> list[JobSummary]:
    """``winners``'ta zaten olan rolleri ``items``'tan düşürür (D-055).

    Düşen satırın konumu kaybolmaz: kazanan satırın ``other_locations``'ına
    eklenir. Böylece "3 şehirde açık" bilgisi doğru kalır — satırı sessizce
    atmak, kullanıcıya o şehirde ilan yokmuş gibi gösterirdi.
    """
    by_key = {_role_key(w.employer, w.title): w for w in winners}
    out: list[JobSummary] = []
    for j in items:
        w = by_key.get(_role_key(j.employer, j.title))
        if w is None:
            out.append(j)
        elif j.city and j.city != w.city and j.city not in w.other_locations:
            w.other_locations.append(j.city)
    return out


#: "Uzun süredir açık" eşiği. Tazelik eşiğiyle (D-024) aynı sayı: 45 günü
#: aşan bir ilan, elenmese bile kullanıcının bilmesi gereken bir yaştadır.
LONG_OPEN_DAYS = 45


def _is_long_open(posting) -> bool:
    age = age_in_days(posting.posted_at)
    return age is not None and age > LONG_OPEN_DAYS


def _yearly(s) -> float | None:
    """Maaşın **alt sınırının** yıllık karşılığı.

    Alt sınır seçildi: kullanıcı "en az 80.000" dediğinde, aralığı 60–120 bin
    olan bir ilanı eşleşme saymak ona 80 bin garanti edilmiş izlenimi verirdi.
    """
    if s is None:
        return None
    from isuygun_ingest.salary import _yearly_equivalent

    return _yearly_equivalent(s.min_amount, s.period)


def _axis_counts(items: list[JobSummary], field_name: str) -> dict:
    """Bir eksenin değer sayaçları. "Belirtilmemiş" de bir değerdir ve sayılır.

    Gizlenmesi kullanıcıya yanlış bir bütünlük hissi verirdi: 4395 ilanın
    2500'ünde çalışma biçimi yazmıyorsa, bunu görmesi gerekir.
    """
    out: dict[str, int] = {}
    for j in items:
        out[getattr(j, field_name) or "unspecified"] = (
            out.get(getattr(j, field_name) or "unspecified", 0) + 1
        )
    return out


def _currency_counts(items: list[JobSummary]) -> dict:
    """Maaşı okunan ilanların para birimi dağılımı.

    Asgari maaş filtresi ancak tek para birimi içinde anlamlı: kur çevirisi
    yapmadan 100.000 USD ile 100.000 TRY karşılaştırılamaz, çeviri yapmak ise
    D-029'un reddettiği uydurma sayıyı üretir.
    """
    out: dict[str, int] = {}
    for j in items:
        if j.salary_status == "found" and j.salary_currency:
            out[j.salary_currency] = out.get(j.salary_currency, 0) + 1
    return out


def _salary_text(posting) -> str | None:
    from isuygun_ingest.salary import format_tr

    s = getattr(posting, "salary", None)
    return format_tr(s) if s else None


def _lines(items) -> list[ExplanationLineOut]:
    return [
        ExplanationLineOut(text=l.text, evidence=l.evidence, action_label=l.action_label)
        for l in items
    ]


def _summary(posting, result, exp) -> JobSummary:
    return JobSummary(
        job_id=posting.job.job_id,
        title=posting.job.title,
        employer=posting.job.employer,
        city=posting.job.city,
        occupation_id=posting.job.occupation_id,
        source=posting.job.source,
        url=posting.url,
        posted_at=posting.posted_at,
        is_public_sector=posting.job.is_public_sector,
        band=result.band.value if result.band else None,
        band_label=exp.band_label,
        confidence_label=exp.confidence_label,
        listing_only=result.listing_only,
        insufficient_data=result.insufficient_data,
        met_count=len(result.met),
        unmet_count=len(result.unmet),
        unknown_count=len(result.unknown),
        worth_applying=exp.worth_applying,
        worth_applying_rule=exp.worth_applying_rule,
        top_requirements=[
            o.requirement.label for o in result.outcomes
            if o.requirement.kind in ("hard", "required")
            and not o.requirement.is_legal_eligibility
        ][:5],
        matched_requirements=[o.requirement.label for o in result.met][:5],
        regions=sorted(regions.classify(posting.job.city)),
        # Şimdilik **anahtar** yazılır; gösterim adı korpus genelinde
        # tekilleştirilip _canonicalize_cities() içinde yerine konur.
        city_group=regions.city_of(posting.job.city)[0],
        age_days=age_in_days(posting.posted_at),
        refreshed_days=age_in_days(getattr(posting, "refreshed_at", None)),
        long_open=_is_long_open(posting),
        salary_text=_salary_text(posting),
        salary_currency=getattr(getattr(posting, "salary", None), "currency", None),
        salary_min_yearly=_yearly(getattr(posting, "salary", None)),
        salary_status=getattr(posting, "salary_status", "not_stated"),
        work_arrangement=getattr(posting, "work_arrangement", None),
        employment_type=getattr(posting, "employment_type", None),
        experience_level=getattr(posting, "experience_level", None),
        fairness_flags=[
            FairnessFlagOut(category=f.category, note=f.note,
                            evidence=f.evidence, severity=f.severity)
            for f in getattr(posting, "fairness_flags", ())
        ],
    )


# --------------------------------------------------------------------------
# Uçlar
# --------------------------------------------------------------------------


@app.get("/api/health")
def health() -> dict:
    """Sağlık + korpus durumu.

    ``status`` korpusu de yansıtır (D-055): 0 ilanla ayakta duran bir sunucu
    "ok" değildir — canlıda tam olarak bu oldu, ``/api/health`` "ok" derken
    site boştu ve dışarıdan sebebi görünmüyordu.
    """
    n = len(STORE.postings)
    return {
        "status": "ok" if n else "empty_corpus",
        "corpus_size": n,
        "corpus_version": STORE.corpus_version,
        "refresh": STORE.refresh_state,
        "ingest": STORE.ingest_summary,
    }


@app.get("/api/sources", response_model=list[SourceOut])
def sources() -> list[SourceOut]:
    """Kaynak şeffaflığı: hangi kaynak neden kullanılıyor/kullanılmıyor."""
    return [
        SourceOut(
            source_id=r.source_id, name=r.name, access_method=r.access_method,
            scraping_permission=r.scraping_permission, policy_risk=r.policy_risk,
            status=r.status, may_fetch_network=r.may_fetch_network, note=r.note,
            permission_evidence=r.permission_evidence,
            attribution_required=r.attribution_required,
            redistribution_policy=r.redistribution_policy,
        )
        for r in registry.REGISTRY.values()
    ]


@app.get("/api/catalog", response_model=list[CatalogItemOut])
def catalog() -> list[CatalogItemOut]:
    return [
        CatalogItemOut(
            key=i.key, label=i.label, category=i.category,
            category_label=i.category_label, occupation_id=i.occupation_id,
            occupation_label=i.occupation_label, asks_years=i.asks_years,
            needs_verification=i.needs_verification,
        )
        for i in STORE.catalog_items()
    ]


@app.get("/api/profile", response_model=ProfileOut)
def get_profile() -> ProfileOut:
    facts = []
    for f in STORE.profile.facts:
        item = STORE.catalog_item(f.key)
        facts.append(
            FactOut(
                key=f.key,
                label=item.label if item else f.key,
                category=f.category,
                verification=f.verification,
                years=f.years,
                counts_as_present=f.counts_as_present,
            )
        )
    return ProfileOut(
        occupation_ids=list(STORE.profile.occupation_ids),
        facts=facts,
        pending_cv_suggestions=STORE.pending_cv_suggestions,
    )


@app.put("/api/profile/occupations", response_model=ProfileOut)
def set_occupations(body: OccupationsIn) -> ProfileOut:
    STORE.set_occupations(body.occupation_ids)
    return get_profile()


# --------------------------------------------------------------------------
# İsimli profiller (D-045)
# --------------------------------------------------------------------------


class ProfileMetaOut(BaseModel):
    id: str
    name: str
    collar: str | None = None
    attrs: dict = Field(default_factory=dict)
    created_at: str = ""
    is_active: bool = False
    fact_count: int = 0


class ProfileCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    #: white | blue | null
    collar: str | None = None
    #: Onboarding tercihleri: bölge, özel anahtar kelimeler vb.
    attrs: dict = Field(default_factory=dict)
    #: Onboarding'de seçilen katalog alanları — profile doğrudan yazılır.
    fact_keys: list[str] = Field(default_factory=list)


class ProfilePatchIn(BaseModel):
    name: str | None = None
    collar: str | None = None
    attrs: dict | None = None


@app.get("/api/profiles", response_model=list[ProfileMetaOut])
def list_profiles() -> list[ProfileMetaOut]:
    return [ProfileMetaOut(**m) for m in STORE.list_profiles()]


@app.post("/api/profiles", response_model=list[ProfileMetaOut])
def create_profile(body: ProfileCreateIn) -> list[ProfileMetaOut]:
    """Yeni isimli profil oluşturur, etkinleştirir ve seçilen alanları yazar."""
    STORE.create_profile(body.name, collar=body.collar, attrs=body.attrs)
    for key in body.fact_keys:
        item = STORE.catalog_item(key)
        # D-013: yasal uygunluk alanları profile yazılmaz; sessizce atlanır.
        if item is not None and not item.is_legal_eligibility:
            try:
                STORE.set_fact(key)
            except (KeyError, ValueError):
                pass
    return list_profiles()


@app.post("/api/profiles/{profile_id}/activate", response_model=list[ProfileMetaOut])
def activate_profile(profile_id: str) -> list[ProfileMetaOut]:
    try:
        STORE.activate(profile_id)
    except KeyError:
        raise HTTPException(404, "Profil bulunamadı.")
    return list_profiles()


@app.patch("/api/profiles/{profile_id}", response_model=list[ProfileMetaOut])
def patch_profile(profile_id: str, body: ProfilePatchIn) -> list[ProfileMetaOut]:
    try:
        if body.name is not None:
            STORE.rename_profile(profile_id, body.name)
        if body.collar is not None or body.attrs is not None:
            STORE.update_meta(profile_id, collar=body.collar, attrs=body.attrs)
    except KeyError:
        raise HTTPException(404, "Profil bulunamadı.")
    return list_profiles()


@app.delete("/api/profiles/{profile_id}", response_model=list[ProfileMetaOut])
def delete_profile(profile_id: str) -> list[ProfileMetaOut]:
    try:
        STORE.delete_profile(profile_id)
    except KeyError:
        raise HTTPException(404, "Profil bulunamadı.")
    except ValueError as e:
        raise HTTPException(400, str(e))
    return list_profiles()


class UnlockSuggestionOut(BaseModel):
    key: str
    label: str
    category: str
    category_label: str
    asks_years: bool
    needs_verification: bool
    #: Bu alan profile eklenirse değerlendirilebilir hâle gelecek ilan sayısı
    unlocks: int


@app.get("/api/profile/unlock-suggestions", response_model=list[UnlockSuggestionOut])
def unlock_suggestions(limit: int = 12) -> list[UnlockSuggestionOut]:
    """"Neyi eklersem kaç ilan değerlendirilebilir olur?"

    Korpusun büyük bölümü bant alamıyor ve bu **doğru** davranış: kullanıcının
    profilinde karşılaştıracak bilgi yoksa uydurma bir bant üretmek D-019'un
    reddettiği şeydir. Ama kullanıcıya yalnızca "değerlendiremedik" demek,
    elinde çözüm varken onu göstermemek demek.

    Sayı ölçülerek üretilir: her ilan tek tek değerlendirilir ve yalnızca
    *şu anda* bandı olmayan, o alan eklendiğinde ayırt edici bir kanıt
    kazanacak satırlar sayılır. **Yaklaşıktır ve hep hafif yukarıdadır**:
    aynı rol hem değerlendirilen hem değerlendirilemeyen listede temsil
    edilebiliyor. Ölçülen sapma %1–3 (297 iddia → 295 gerçek). Tam kesinlik
    her aday alan için korpusu yeniden değerlendirmeyi gerektirirdi (~9 sn);
    bir yönlendirme paneli için bu bedel orantısız. Arayüz bu yüzden "≈"
    yazar — olmayan bir kesinlik iddia etmez.
    """
    return _unlock_for(STORE.profile, limit)


@app.post("/api/unlock-suggestions", response_model=list[UnlockSuggestionOut])
def unlock_suggestions_stateless(body: ProfilePayload,
                                 limit: int = 12) -> list[UnlockSuggestionOut]:
    """Durumsuz sürüm (D-059): profil gövdede gelir, hiçbir şey saklanmaz.

    Hesap tüm korpusu değerlendirir (~1 sn); aynı profil için tekrar hesaplamak
    boşa CPU olduğundan sonuç küçük bir LRU'da tutulur. Anahtar korpus sürümünü
    de içerir — tazeleme sonrası eski sayılar servis edilmez.
    """
    key = (STORE.corpus_version, _fingerprint_of(_profile_from_payload(body)), limit)
    hit = _UNLOCK_CACHE.get(key)
    if hit is not None:
        _UNLOCK_CACHE.move_to_end(key)
        return hit
    out = _unlock_for(_profile_from_payload(body), limit)
    _UNLOCK_CACHE[key] = out
    while len(_UNLOCK_CACHE) > 4:
        _UNLOCK_CACHE.popitem(last=False)
    return out


_UNLOCK_CACHE: "OrderedDict[tuple, list]" = OrderedDict()


def _unlock_for(profile: CareerProfile, limit: int) -> list[UnlockSuggestionOut]:
    # Sayım **satır** birimindedir, ilan değil: liste aynı işverenin aynı
    # rolünü tek satıra indiriyor (`_group_by_role`). İlan sayarsak "+327"
    # deyip 295 açılır — D-030'da düzeltilen hatanın aynısı: kullanıcının
    # gördüğü sayı, tıklayınca aldığı sayı olmalı.
    roles: dict[str, set[tuple[str, str]]] = {}
    for posting in STORE.postings.values():
        result, _ = _evaluate(posting, profile)
        if result.band is not None or result.listing_only:
            continue        # zaten değerlendirilebiliyor
        role = _role_key(posting.job.employer, posting.job.title)
        for o in result.outcomes:
            req = o.requirement
            if (o.state == "unknown"
                    and o.unknown_reason == "missing_profile_data"
                    and req.category not in GATE_RELEVANT_CATEGORIES
                    and req.category not in NON_DISCRIMINATIVE_CATEGORIES
                    and not req.is_legal_eligibility):
                roles.setdefault(req.key, set()).add(role)

    have = {f.key for f in profile.facts}
    out: list[UnlockSuggestionOut] = []
    for key, n in sorted(((k, len(v)) for k, v in roles.items()),
                         key=lambda kv: -kv[1]):
        if key in have:
            continue
        item = STORE.catalog_item(key)
        # D-013/D-006: yasal uygunluk alanları profile hiç yazılmaz, bu yüzden
        # önerilmezler de — tıklanamayacak bir öneri göstermek olurdu.
        if item is None or item.is_legal_eligibility:
            continue
        out.append(UnlockSuggestionOut(
            key=item.key, label=item.label, category=item.category,
            category_label=item.category_label, asks_years=item.asks_years,
            needs_verification=item.needs_verification, unlocks=n,
        ))
        if len(out) >= limit:
            break
    return out


@app.post("/api/profile/facts", response_model=ProfileOut)
def add_fact(body: FactIn) -> ProfileOut:
    try:
        STORE.set_fact(
            body.key,
            verification="verified" if body.verified else "user_asserted",
            years=body.years,
        )
    except KeyError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    # Onaylanan öneri bekleyenler listesinden düşer.
    STORE.pending_cv_suggestions = [
        s for s in STORE.pending_cv_suggestions if s["key"] != body.key
    ]
    # Etkin profile yazılır. Sabit "local" idi (D-045 öncesi tek profil devri);
    # profiller p-<uuid> olduğundan öneriler var olmayan bir profile gidiyor ve
    # profil değişince/yeniden başlayınca kayboluyordu.
    STORE.store.save_suggestions(STORE.active_id, STORE.pending_cv_suggestions)
    return get_profile()


@app.delete("/api/profile/facts/{key}", response_model=ProfileOut)
def remove_fact(key: str) -> ProfileOut:
    STORE.remove_fact(key)
    return get_profile()


@app.post("/api/profile/facts/{key}/verify", response_model=ProfileOut)
def verify_fact(key: str) -> ProfileOut:
    """Belge doğrulama — MVP'de **simüle edilmiştir**, arayüzde öyle etiketlenir."""
    try:
        STORE.verify_fact(key)
    except KeyError as e:
        raise HTTPException(404, str(e)) from e
    return get_profile()


@app.post("/api/profile/reset", response_model=ProfileOut)
def reset_profile() -> ProfileOut:
    STORE.reset_profile()
    return get_profile()


@app.post("/api/profile/cv")
async def upload_cv(file: UploadFile) -> dict:
    """CV yükler ve alan **önerir**. Profile hiçbir şey yazmaz (T-016)."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Yalnızca PDF kabul ediliyor.")
    data = await file.read()
    if len(data) > MAX_CV_BYTES:
        raise HTTPException(400, "Dosya 10 MB sınırını aşıyor.")
    payload = _cv_payload(data)
    # Classic davranışı: bekleyen öneriler sunucudaki etkin profile yazılır.
    STORE.pending_cv_suggestions = payload["suggestions"]
    STORE.store.save_suggestions(STORE.active_id, STORE.pending_cv_suggestions)
    return payload


@app.post("/api/cv/suggest")
async def cv_suggest(file: UploadFile) -> dict:
    """CV'den alan önerir — **hiçbir şey saklamadan** (D-059).

    Durumsuz sürüm: dosya ayrıştırılır, öneriler döner, sunucuda ne dosya ne
    öneri kalır. Kalıcılık istemcinin işi. Eski ``/api/profile/cv`` ucu
    sunucudaki ORTAK profile yazıyordu — ziyaretçi A'nın CV önerileri classic'e
    bakan herkese görünüyordu.
    """
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Yalnızca PDF kabul ediliyor.")
    data = await file.read()
    if len(data) > MAX_CV_BYTES:
        raise HTTPException(400, "Dosya 10 MB sınırını aşıyor.")
    return _cv_payload(data)


def _cv_payload(data: bytes) -> dict:
    try:
        result = read_cv(data, STORE.catalog)
    except Exception as e:  # bozuk/şifreli PDF
        raise HTTPException(400, f"PDF okunamadı: {e}") from e
    return {
        "page_count": result.page_count,
        "char_count": result.char_count,
        "text_extracted": result.text_extracted,
        "note": result.note,
        "discarded_sensitive": result.discarded_sensitive,
        "suggestions": [
            {
                "key": s.key, "label": s.label, "category": s.category,
                "needs_verification": s.needs_verification,
                "asks_years": s.asks_years,
                "years": s.years, "matched_on": s.matched_on,
            }
            for s in result.suggestions
        ],
        "written_to_profile": False,
    }


class FeedbackIn(BaseModel):
    """Eşleşme geri bildirimi — anonim (D-059).

    Kimlik alınmaz; ``title/employer`` istemciden yalnızca ilan korpustan
    düşmüşse yedek olarak kullanılır.
    """

    job_id: str = Field(..., max_length=200)
    verdict: str = Field(..., pattern="^(up|down)$")
    band: str | None = Field(None, max_length=20)
    reason: str | None = Field(None, max_length=120)
    title: str = Field("", max_length=200)
    employer: str = Field("", max_length=200)


@app.post("/api/feedback", status_code=204)
def post_feedback(body: FeedbackIn) -> None:
    """"Bu eşleşme isabetli miydi?" — kalibrasyonun (T-006b) ham verisi.

    Bizim bandımızla kullanıcının yargısının uyuşmadığı kayıtlar, eşleşme
    motorunun hatasının tam adresidir. Toplanır, hiçbir yerde tek tek
    gösterilmez; analiz çevrimdışıdır.
    """
    posting = STORE.job(body.job_id)
    signals.record_feedback(
        job_id=body.job_id, band=body.band, verdict=body.verdict,
        reason=body.reason,
        title=posting.job.title if posting else body.title,
        employer=posting.job.employer if posting else body.employer,
    )


_APPLY_EVENTS = ("applied", "answered", "interview", "offer", "rejected",
                 "no_answer", "withdrawn")


class ApplyEventIn(BaseModel):
    job_id: str = Field(..., max_length=200)
    event: str
    days_since_apply: int | None = Field(None, ge=0, le=365)
    title: str = Field("", max_length=200)
    employer: str = Field("", max_length=200)


@app.post("/api/apply-events", status_code=204)
def post_apply_event(body: ApplyEventIn) -> None:
    """Başvuru yaşam döngüsü olayı — anonim sayaç (D-059).

    İleride işveren yanıt oranına dönüşür ("N kullanıcı başvurdu, M yanıt
    aldı") ve "uzun süredir açık" tahminini kanıta çevirir. Hacim eşiği
    dolmadan hiçbir yerde gösterilmez; kayıtlar kullanıcıya bağlanamaz.
    """
    if body.event not in _APPLY_EVENTS:
        raise HTTPException(400, f"Bilinmeyen olay: {body.event!r}")
    posting = STORE.job(body.job_id)
    signals.record_apply_event(
        job_id=body.job_id, event=body.event,
        days_since_apply=body.days_since_apply,
        title=posting.job.title if posting else body.title,
        employer=posting.job.employer if posting else body.employer,
    )


@app.post("/api/jobs/evaluate", response_model=JobDetail)
def evaluate_pasted(body: PastedJobIn) -> JobDetail:
    """Yapıştırılan bir ilanı profile karşı değerlendirir.

    Korpustaki ilanlarla **aynı** hattan geçer: aynı sözlük, aynı çıkarım, aynı
    matching, aynı açıklama kuralları. Ayrı bir "yapıştırma modu" yazmak, iki
    kod yolunun zamanla birbirinden sapması demekti.

    Sonuç **saklanmaz**. Kullanıcının getirdiği içerik korpusa karışmaz; bu hem
    veri hijyeni hem de kaynak izni açısından gereklidir — o metnin nereden
    geldiğini ve yeniden yayınlanabilir olup olmadığını biz bilemeyiz.
    """
    from isuygun_ingest.extract import extract_requirements, infer_occupation

    title = body.title.strip() or _first_line(body.text)
    reqs = extract_requirements(title, body.text)
    job = JobPosting(
        job_id="pasted",
        title=title,
        employer=body.employer.strip() or "Belirtilmemiş",
        city=body.city.strip(),
        occupation_id=infer_occupation(title, reqs),
        source="Yapıştırılan ilan",
        requirements=reqs,
    )
    result = match(job, STORE.profile, calibrated_occupation=False)
    exp = build_explanation(result)

    posting = SimpleNamespace(job=job, url=body.url.strip(), posted_at=None,
                              job_text=body.text)
    base = _summary(posting, result, exp)
    return JobDetail(
        **base.model_dump(),
        description=body.text,
        why=list(exp.why),
        met=_lines(exp.met), unmet=_lines(exp.unmet), unknown=_lines(exp.unknown),
        legal_eligibility_notices=list(exp.legal_eligibility_notices),
        verification_notice=exp.verification_notice,
        listing_only_note=exp.listing_only_note,
        insufficient_data_note=exp.insufficient_data_note,
        disclaimer=exp.disclaimer,
    )


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:120]
    return "Başlıksız ilan"


#: Feed önbelleği (D-054). Tek girdilik: anahtar değişince eskisi atılır.
#:
#: **Neden gerekti:** ``/api/feed`` her istekte korpusun tamamını yeniden
#: değerlendiriyordu. Ölçüm (9266 ilan): tek istek **633 ms**, 10 eş zamanlı
#: istek **6,3 saniye** duvar süresi — GIL yüzünden sıraya giriyorlar, yani
#: saniyede ~1,6 istek. Kıyas: ``/api/health`` 1,2 ms.
#:
#: Sonuç ``(korpus sürümü, profil parmak izi)`` çiftinin **saf** fonksiyonudur:
#: aynı korpus + aynı profil her zaman aynı feed'i verir. Bu yüzden önbellek
#: bayat veri riski taşımaz; ikisinden biri değişince anahtar da değişir.
_FEED_CACHE: "OrderedDict[tuple, bytes]" = OrderedDict()
_FEED_CACHE_MAX = 8


def _profile_fingerprint() -> tuple:
    """Eşleşme sonucunu belirleyen profil durumu.

    Bekleyen CV önerileri **dahil değildir**: onaylanana kadar eşleşmeyi
    etkilemezler (D-014), dolayısıyla feed'i geçersizleştirmemeleri gerekir.
    """
    p = STORE.profile
    return (
        STORE.active_id,
        tuple(sorted((f.key, f.verification, f.years) for f in p.facts)),
        tuple(sorted(p.occupation_ids)),
    )


def _fingerprint_of(profile: CareerProfile) -> tuple:
    """Geçici (istemci) profilin önbellek kimliği — kimliksiz, yalnız içerik."""
    return (
        tuple(sorted((f.key, f.verification, f.years or -1.0)
                     for f in profile.facts)),
        tuple(sorted(profile.occupation_ids)),
    )


def _feed_body(cache_key: tuple, profile: CareerProfile) -> bytes:
    """Feed'i hazır JSON bayt olarak üretir/önbellekten verir.

    Önbellek artık çok girdili LRU (D-059): ziyaretçiler ayrı profiller
    gönderdiğinden tek-girdili önbellek her farklı ziyaretçide tam yeniden
    hesap demekti. Gövde ~10 MB olduğundan sınır küçük tutulur (8 girdi);
    sayfalama işi gövdeyi küçülttüğünde artırılabilir. ``response_model``
    doğrulaması bilinçli atlanır — ölçümde isabette bile 173 ms yiyordu.
    """
    hit = _FEED_CACHE.get(cache_key)
    if hit is not None:
        _FEED_CACHE.move_to_end(cache_key)
        return hit
    body = json.dumps(
        jsonable_encoder(_build_feed(profile)), ensure_ascii=False,
    ).encode("utf-8")
    _FEED_CACHE[cache_key] = body
    while len(_FEED_CACHE) > _FEED_CACHE_MAX:
        _FEED_CACHE.popitem(last=False)
    return body


@app.get("/api/feed", response_model=FeedOut)
def feed() -> Response:
    """Eski yüzeyin feed'i — **sunucudaki** global profille (yalnız classic).

    Yeni arayüz :func:`feed_stateless` kullanır; bu uç ``ISUYGUN_CLASSIC``
    kapalıyken 404'tür (D-059) çünkü global profil ziyaretçiler arasında
    paylaşılıyordu.
    """
    key = (STORE.corpus_version, "classic", _profile_fingerprint())
    return Response(content=_feed_body(key, STORE.profile),
                    media_type="application/json")


@app.post("/api/feed", response_model=FeedOut)
def feed_stateless(body: ProfilePayload) -> Response:
    """Feed, istemcinin gönderdiği geçici profille (D-059).

    Profil sunucuya YAZILMAZ; yalnızca bu isteğin değerlendirmesine girer.
    Kalıcı kopya tarayıcıdadır — ziyaretçi izolasyonu tam olarak budur.
    """
    profile = _profile_from_payload(body)
    key = (STORE.corpus_version, "v2", _fingerprint_of(profile))
    return Response(content=_feed_body(key, profile),
                    media_type="application/json")


def _build_feed(profile: CareerProfile) -> FeedOut:
    evaluated: list[tuple[int, JobSummary]] = []
    unevaluated: list[JobSummary] = []

    for posting in STORE.postings.values():
        result, exp = _evaluate(posting, profile)
        s = _summary(posting, result, exp)
        if result.band is None:
            # D-019: bant yok. Bunlar "uymuyor" değil, "bilinmiyor" — ayrı
            # bölümde gösterilir ve bant sırasına sokulmaz (OPEN-22 açık).
            unevaluated.append(s)
        else:
            evaluated.append((_BAND_ORDER[result.band], s))

    evaluated.sort(key=lambda t: (t[0], t[1].title))
    shown_evaluated = _group_by_role([s for _, s in evaluated])
    # Gruplama iki listeye AYRI uygulanırsa aynı rol ikisinde birden çıkabilir
    # (D-055): aynı rolün bir şehirdeki kopyasından şart okunmuş, diğerinden
    # okunamamışsa biri "sana göre"ye biri "veri eksik"e düşer ve kullanıcı
    # aynı ilanı iki kez görür. Ölçümde 8 rol böyleydi. Değerlendirilen taraf
    # kazanır — daha fazla bilgi taşıyan satır odur; diğerinin şehri kaybolmaz,
    # ``other_locations``'a eklenir.
    shown_unevaluated = _absorb_into(
        _group_by_role(unevaluated), shown_evaluated)
    _canonicalize_cities(shown_evaluated, shown_unevaluated)
    # Facet'ler **gösterilen** listeden sayılır. Gruplama öncesinden sayılırsa
    # rozet "1994 ilan" der, kullanıcı tıklar, 1678 ilan görür — sayının
    # kendisi yanlış olmasa da kullanıcıya verilen söz tutulmamış olur.
    every = shown_evaluated + shown_unevaluated
    return FeedOut(
        evaluated=shown_evaluated,
        unevaluated=shown_unevaluated,
        profile_is_empty=not profile.facts,
        profile_is_persistent=STORE.is_persistent,
        profile_backend=STORE.backend,
        ingest=STORE.ingest_summary,
        facets={
            # Birleştirilen konumlar da listelenir: ilan o şehirde gerçekten
            # var, yalnızca gösterimde tek satıra indirilmiş durumda.
            "cities": sorted(
                {j.city for j in every if j.city}
                | {c for j in every for c in j.other_locations if c}
            ),
            "employers": sorted({j.employer for j in every if j.employer}),
            "clusters": sorted({j.occupation_id for j in every if j.occupation_id}),
            # Bölge sayaçları: kullanıcı hangi pazarda kaç ilan olduğunu görebilmeli.
            "salary_counts": {
                k: sum(1 for j in every if j.salary_status == k)
                for k in ("found", "not_stated", "unreadable")
            },
            # Eksen sayaçları. Sabit liste değil korpustan sayılır: bir seçenek
            # sıfır ilan içeriyorsa arayüzde hiç gösterilmez — tıklayınca boş
            # liste veren bir filtre, olmayan bir vaat demektir.
            "arrangements": _axis_counts(every, "work_arrangement"),
            "employment_types": _axis_counts(every, "employment_type"),
            "experience_levels": _axis_counts(every, "experience_level"),
            "currencies": _currency_counts(every),
            "long_open_count": sum(1 for j in every if j.long_open),
            "regions": [
                {"name": r, "count": sum(1 for j in every if r in j.regions)}
                for r in regions.ALL
                if any(r in j.regions for j in every)
            ],
        },
    )


class SearchOut(BaseModel):
    job_ids: list[str]
    #: Sorgunun nasıl anlaşıldığı — kullanıcı operatörü yanlış yazdıysa görsün.
    terms: list[str] = []
    phrases: list[str] = []
    excluded: list[str] = []


@app.get("/api/search", response_model=SearchOut)
def search_jobs(q: str = "") -> SearchOut:
    """İlan **metninde** arama.

    Arayüzün diğer filtreleri istemcide anında çalışır; bu uç yalnızca tam
    metin için var, çünkü açıklamalar toplam 30 MB ve tarayıcıya gönderilemez.
    Dönen kimlikleri istemci kendi filtreleriyle kesiştirir.
    """
    parsed = search.parse(q)
    if parsed.is_empty:
        return SearchOut(job_ids=[])
    ids = [
        job_id for job_id, hay in STORE.search_index.items()
        if search.matches(hay, parsed)
    ]
    return SearchOut(
        job_ids=ids, terms=list(parsed.terms),
        phrases=list(parsed.phrases), excluded=list(parsed.excluded),
    )


@app.post("/api/jobs/{job_id:path}", response_model=JobDetail)
def job_detail_stateless(job_id: str, body: ProfilePayload) -> JobDetail:
    """İlan detayı, istemcinin geçici profiliyle (D-059).

    Defter (met/unmet/unknown) profile bağlıdır; GET sürümü sunucudaki global
    profili kullanıyordu ve durumsuz dünyada başka ziyaretçilerin izini
    taşıyabilirdi.
    """
    return _detail_for(job_id, _profile_from_payload(body))


@app.get("/api/jobs/{job_id:path}", response_model=JobDetail)
def job_detail(job_id: str) -> JobDetail:
    # Classic açıkken global profil (eski davranış). Kapalıyken BOŞ profil:
    # eski ortak profilin kalıntısıyla defter üretmek, o profile yazılmış
    # becerilerin izini herkese göstermek olurdu (D-059).
    profile = STORE.profile if _classic_enabled() else CareerProfile(profile_id="anon")
    return _detail_for(job_id, profile)


def _detail_for(job_id: str, profile: CareerProfile) -> JobDetail:
    posting = STORE.job(job_id)
    if posting is None:
        raise HTTPException(404, "İlan bulunamadı.")
    result, exp = _evaluate(posting, profile)
    base = _summary(posting, result, exp)

    return JobDetail(
        **base.model_dump(),
        description=posting.job_text,
        why=list(exp.why),
        met=_lines(exp.met),
        unmet=_lines(exp.unmet),
        unknown=_lines(exp.unknown),
        legal_eligibility_notices=list(exp.legal_eligibility_notices),
        verification_notice=exp.verification_notice,
        listing_only_note=exp.listing_only_note,
        insufficient_data_note=exp.insufficient_data_note,
        disclaimer=exp.disclaimer,
    )


# --------------------------------------------------------------------------
# Statik arayüz
# --------------------------------------------------------------------------

_WEB = Path(__file__).resolve().parents[4] / "web"
if _WEB.is_dir():
    app.mount("/static", StaticFiles(directory=str(_WEB)), name="static")

    @app.get("/")
    def index() -> FileResponse:
        # Yeni tasarım artık **birincil** (D-046v2). Eski tam-özellikli arayüz
        # `/classic`'te yedek duruyor; kalan özellikler (CV yükle, ilan yapıştır,
        # gelişmiş filtreler, kaynaklar) yeni tasarıma taşınana kadar erişilebilir.
        return FileResponse(str(_WEB / "app.html"))

    @app.get("/app")
    def app_v2() -> FileResponse:
        return FileResponse(str(_WEB / "app.html"))

    @app.get("/classic")
    def classic() -> FileResponse:
        return FileResponse(str(_WEB / "index.html"))
