"""İşe Uygun API.

Bu katman iş kuralı **içermez**. Değerlendirme mantığının tamamı
``isuygun_core``'da, ilan toplama mantığının tamamı ``isuygun_ingest``'tedir.
API yalnızca onları HTTP'ye açar — kural burada tekrar edilirse iki yerde
birbirinden sapar.

OpenAPI şeması ``/openapi.json`` adresinden alınır; TypeScript tipleri bundan
üretilir (ADR-001 şema kayması önlemi).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from isuygun_core import build_explanation, match
from isuygun_core.domain import JobPosting, MatchBand
from isuygun_ingest import regions, registry
from isuygun_ingest.pipeline import age_in_days

from .cv import read_cv
from .store import STORE

MAX_CV_BYTES = 10 * 1024 * 1024

@asynccontextmanager
async def lifespan(_: FastAPI):
    STORE.load()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="İşe Uygun API",
    version="0.1.0",
    description=(
        "Fixture veriyle çalışan MVP çekirdeği. Gerçek ilan kaynağına bağlı "
        "DEĞİLDİR (D-018)."
    ),
)


# --------------------------------------------------------------------------
# Şemalar — OpenAPI çıktısının kaynağı
# --------------------------------------------------------------------------


class ExplanationLineOut(BaseModel):
    text: str
    evidence: str
    action_label: str | None = None


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
    #: Aynı rolün diğer konumları. Bunlar **ayrı ilanlardır** (her birinin kendi
    #: URL'i var) ve birleştirilmez; yalnızca listede tek satır olarak gösterilir.
    other_locations: list[str] = []
    #: İlanın yaşı (gün). null = yayın tarihi bilinmiyor (D-024).
    age_days: int | None = None


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


def _evaluate(posting):
    job = posting.job
    result = match(
        job,
        STORE.profile,
        calibrated_occupation=job.occupation_id in _CALIBRATED,
    )
    return result, build_explanation(result)


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
        key = (j.employer.casefold(), j.title.casefold())
        first = seen.get(key)
        if first is None:
            seen[key] = j
            out.append(j)
        elif j.city and j.city not in first.other_locations and j.city != first.city:
            first.other_locations.append(j.city)
    return out


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
        age_days=age_in_days(posting.posted_at),
    )


# --------------------------------------------------------------------------
# Uçlar
# --------------------------------------------------------------------------


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "ingest": STORE.ingest_summary}


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
    try:
        result = read_cv(data, STORE.catalog)
    except Exception as e:  # bozuk/şifreli PDF
        raise HTTPException(400, f"PDF okunamadı: {e}") from e

    STORE.pending_cv_suggestions = [
        {
            "key": s.key, "label": s.label, "category": s.category,
            "needs_verification": s.needs_verification, "asks_years": s.asks_years,
            "years": s.years, "matched_on": s.matched_on,
        }
        for s in result.suggestions
    ]
    return {
        "page_count": result.page_count,
        "char_count": result.char_count,
        "text_extracted": result.text_extracted,
        "note": result.note,
        "discarded_sensitive": result.discarded_sensitive,
        "suggestions": STORE.pending_cv_suggestions,
        "written_to_profile": False,
    }


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


@app.get("/api/feed", response_model=FeedOut)
def feed() -> FeedOut:
    evaluated: list[tuple[int, JobSummary]] = []
    unevaluated: list[JobSummary] = []

    for posting in STORE.postings.values():
        result, exp = _evaluate(posting)
        s = _summary(posting, result, exp)
        if result.band is None:
            # D-019: bant yok. Bunlar "uymuyor" değil, "bilinmiyor" — ayrı
            # bölümde gösterilir ve bant sırasına sokulmaz (OPEN-22 açık).
            unevaluated.append(s)
        else:
            evaluated.append((_BAND_ORDER[result.band], s))

    evaluated.sort(key=lambda t: (t[0], t[1].title))
    every = [s for _, s in evaluated] + unevaluated
    return FeedOut(
        evaluated=_group_by_role([s for _, s in evaluated]),
        unevaluated=_group_by_role(unevaluated),
        profile_is_empty=not STORE.profile.facts,
        ingest=STORE.ingest_summary,
        facets={
            "cities": sorted({j.city for j in every if j.city}),
            "employers": sorted({j.employer for j in every if j.employer}),
            "clusters": sorted({j.occupation_id for j in every if j.occupation_id}),
            # Bölge sayaçları: kullanıcı hangi pazarda kaç ilan olduğunu görebilmeli.
            "regions": [
                {"name": r, "count": sum(1 for j in every if r in j.regions)}
                for r in regions.ALL
                if any(r in j.regions for j in every)
            ],
        },
    )


@app.get("/api/jobs/{job_id:path}", response_model=JobDetail)
def job_detail(job_id: str) -> JobDetail:
    posting = STORE.job(job_id)
    if posting is None:
        raise HTTPException(404, "İlan bulunamadı.")
    result, exp = _evaluate(posting)
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
        return FileResponse(str(_WEB / "index.html"))
