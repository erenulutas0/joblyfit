"""Matching engine v0 — üç durumlu değerlendirme + bant/confidence üretimi.

Uygulanan kararlar:

* **D-011** — `unknown` skoru düşürmez; skordan çıkarılır ve confidence'ı düşürür.
  "Bilmiyoruz" bir ceza değildir.
* **D-012** — doğrulanmamış gate alanı `met` üretemez (domain katmanında garanti).
* **D-005** — çıktı yüzde değil ``MatchBand``; ayrıca ``Confidence`` ayrı boyut.
* **D-015** — public sector ilanı için skor **hiç üretilmez**.
* **D-017** — semantic katkı üst sınırı ``SEMANTIC_MAX_CONTRIBUTION`` (~%10) ve
  low-confidence extraction'da devre dışı.
"""

from __future__ import annotations

from dataclasses import dataclass

from .domain import (
    NON_DISCRIMINATIVE_CATEGORIES,
    CareerProfile,
    Confidence,
    JobPosting,
    MatchBand,
    RequirementOutcome,
    evaluate_requirement,
    partition,
)

# D-017: calibration target. Kesin/evrensel değer değildir; golden set ölçümüyle
# (T-006b) yeniden değerlendirilir.
SEMANTIC_MAX_CONTRIBUTION = 0.10

# Şart türlerinin skora ağırlığı. Başlangıç kalibrasyonu — T-006b ile ayarlanacak.
KIND_WEIGHT = {"hard": 3.0, "required": 2.0, "preferred": 1.0}


@dataclass(frozen=True, slots=True)
class MatchResult:
    job: JobPosting
    outcomes: tuple[RequirementOutcome, ...]
    band: MatchBand | None          # public sector'de veya veri yetmezse None
    confidence: Confidence | None
    listing_only: bool = False
    # Hiçbir şart değerlendirilemedi → bant üretilmez (D-011).
    insufficient_data: bool = False
    semantic_contribution: float = 0.0
    #: Kıdem tavanı uygulandıysa gerekçesi (D-063). Kullanıcıya gösterilir:
    #: bandın neden yükselmediğini söylemeyen bir tavan, sessiz bir cezadır.
    seniority_note: str | None = None
    #: Zorunlu şart bilinmediği için tavan uygulandıysa gerekçesi (D-064).
    requirement_gap_note: str | None = None
    #: Kanıt oranı tavanı uygulandıysa gerekçesi (D-064). Tavanların yükünü
    #: bu taşıyor; açıklaması olmadan sessiz bir ceza olurdu.
    coverage_note: str | None = None

    @property
    def met(self) -> list[RequirementOutcome]:
        return partition(self.outcomes)[0]

    @property
    def unmet(self) -> list[RequirementOutcome]:
        return partition(self.outcomes)[1]

    @property
    def unknown(self) -> list[RequirementOutcome]:
        return partition(self.outcomes)[2]

    @property
    def blocking_unmet(self) -> list[RequirementOutcome]:
        """Karşılanmayan **hard** şartlar — kullanıcıya açıkça gösterilir (FR-402)."""
        return [o for o in self.unmet if o.requirement.kind == "hard"]

    @property
    def needs_verification(self) -> list[RequirementOutcome]:
        """Doğrulama beklediği için değerlendirilemeyen şartlar (D-012)."""
        return [o for o in self.unknown if o.unknown_reason == "unverified_gate_field"]


def _structured_score(outcomes: tuple[RequirementOutcome, ...]) -> tuple[float, float]:
    """(skor, değerlendirilebilen ağırlık oranı) döndürür.

    `unknown` olan şart paydaya **girmez** — cezalandırılmaz, yalnızca
    değerlendirilen kütleyi küçültür ve bu confidence'a yansır (D-011).
    """
    earned = 0.0
    assessable = 0.0
    total = 0.0

    for o in outcomes:
        w = KIND_WEIGHT.get(o.requirement.kind, 1.0)
        total += w
        if o.state == "unknown":
            continue
        assessable += w
        if o.state == "met":
            earned += w

    if assessable == 0:
        return 0.0, 0.0
    coverage = assessable / total if total else 0.0
    return earned / assessable, coverage


# D-022 — bant tavanı: iddianın gücü, kanıtın miktarını aşamaz.
#
# Bir ilandan yalnızca tek bir mesleğe özgü şart değerlendirilebildiyse ve o da
# karşılanıyorsa skor 1.0 çıkar ve "Güçlü eşleşme" denir. Gerçek veride bunun
# sonucu şuydu: bir yazılımcı profiline **"Majors Account Executive"** ilanı
# güçlü eşleşme olarak gösterildi — ilan metninde "bulut" geçtiği için.
#
# Bu bir ceza değil **tavan**dır: bandı skorun verdiğinden aşağı çekmez, yalnızca
# tek veri noktasına dayanan fazla iddialı etiketi engeller. Kaç şartın
# *bilinmediği* bandı etkilemez (D-011 korunur); belirleyici olan kaç şartın
# gerçekten *değerlendirilebildiğidir*.
_EVIDENCE_CAP: tuple[tuple[int, MatchBand], ...] = (
    (1, MatchBand.CONDITIONAL),   # tek şart değerlendirildi → en fazla "şartlı"
    (2, MatchBand.GOOD),          # iki şart → en fazla "iyi"
)

_BAND_RANK = {MatchBand.WEAK: 0, MatchBand.CONDITIONAL: 1,
              MatchBand.GOOD: 2, MatchBand.STRONG: 3}


def _cap_for(discriminative_assessed: int) -> MatchBand | None:
    for threshold, cap in _EVIDENCE_CAP:
        if discriminative_assessed <= threshold:
            return cap
    return None


# D-063 — kıdem tavanı: iddianın gücü, **doğrulanmış kıdemi** aşamaz.
#
# D-022'nin aynı mantığı, başka bir eksende. Ölçüm (golden set, 14.504 ilanlık
# korpus): ilanın kıdem basamağı eşleşmeye HİÇ girmiyordu ve yeni mezun profili
# (yıl beyanı yok) üst düzey rollerin %16,8'ine strong/good alıyordu — 9 yıllık
# kıdemlinin oranı %26,2. İki sayının yakınlığı kanıttı: fark yalnızca beceri
# sayısından geliyordu, kıdemden değil. 49 ilanda yeni mezuna Staff/Senior rolü
# için "güçlü eşleşme" deniyordu — ürünün önlemek için var olduğu yanlış umut.
#
# Eşikler **teamül**dür, ölçülmüş değil; bu yüzden sert eleme yapmazlar.
_SENIORITY_MIN_YEARS: dict[str, float] = {
    "mid": 2.0, "senior": 5.0, "lead": 7.0, "architect": 8.0, "executive": 10.0,
}

#: Kıdem açığı bandı en fazla buraya çeker. **WEAK değil**: adayın
#: reddedileceğini iddia etmiyoruz (D-019) — yalnızca "güçlü/iyi" diyecek
#: dayanağımız yok. Kullanıcı ilanı görmeye devam eder, gerekçeyi okur.
_SENIORITY_CAP = MatchBand.CONDITIONAL


# D-064 — iki tavan daha; ikisi de aynı ilkenin başka yüzü:
# "iddianın gücü, elimizdeki kanıtı aşamaz."
#
# (1) ZORUNLU ŞART BİLİNMİYORSA "güçlü" denmez. D-012 bunu yalnızca *belge*
#     alanları için yapıyordu (doğrulanmamış gate → şartlı). Ölçümde aynı
#     boşluğun başka türü çıktı: "Yüksek lisans **zorunlu**" ve "Almanca
#     **zorunlu**" şartları profilde hiç karşılığı yokken ilan "güçlü eşleşme"
#     görünüyordu — `unknown` skoru düşürmediği için (D-011, doğru kural) skor
#     1.0 çıkıyordu.
#
#     **Sebep ayrımı kritik:** yalnızca bilinmeyenin kaynağı PROFİL olduğunda
#     tavan uygulanır. `low_confidence_extraction` (ilanı biz güvenle
#     okuyamadık) tavana girmez — kendi çıkarım zaafımız için kullanıcının
#     bandını düşürmek, olmayan bir şartı ona yüklemek olurdu (FS-4).
_PROFILE_GAP_REASONS = frozenset({"missing_profile_data", "missing_duration"})
_HARD_UNKNOWN_CAP = MatchBand.CONDITIONAL

# (2) KANIT ORANI tavanı. D-022 değerlendirilen şartın **sayısına** bakar;
#     bu, ilanın söylediklerinin ne kadarını okuyabildiğimize (**orana**)
#     bakar. 12 şartlı bir ilanda 4'ünü değerlendirip "güçlü" demek, ilanın
#     üçte ikisi hakkında hiçbir şey bilmeden tam uyum iddia etmektir.
#     Eşikler ölçümle seçildi (bkz. golden/README).
_COVERAGE_CAP: tuple[tuple[float, MatchBand], ...] = (
    (0.35, MatchBand.CONDITIONAL),   # şartların <%35'i değerlendirildi
    (0.60, MatchBand.GOOD),          # <%60 → en fazla "iyi"
)


def _hard_unknown_cap(outcomes: tuple[RequirementOutcome, ...]
                      ) -> tuple[MatchBand | None, str | None]:
    """Profil eksikliği yüzünden değerlendirilemeyen **zorunlu** şart var mı?"""
    eksik = [
        o for o in outcomes
        if o.state == "unknown"
        and o.requirement.kind == "hard"
        and not o.requirement.is_legal_eligibility     # D-013: skora girmez
        and o.unknown_reason in _PROFILE_GAP_REASONS
    ]
    if not eksik:
        return None, None
    adlar = ", ".join(o.requirement.label for o in eksik[:3])
    return _HARD_UNKNOWN_CAP, (
        f"İlan şu şartı **zorunlu** tutuyor ve profilinde karşılığı yok: "
        f"{adlar}. Bu seni **eler demiyoruz** — ama zorunlu bir şart "
        f"doğrulanmadan güçlü eşleşme diyemeyiz."
    )


def _coverage_cap(coverage: float) -> MatchBand | None:
    for esik, cap in _COVERAGE_CAP:
        if coverage < esik:
            return cap
    return None


def _coverage_note(outcomes: tuple[RequirementOutcome, ...]) -> str:
    """Kanıt oranı tavanının gerekçesi — **sayıyla**.

    Ölçüm bu notu zorunlu kıldı: tavanların yükünü kanıt oranı taşıyor (bir
    profilde 976 bantlı ilanın 852'si) ve açıklaması olmadığında kullanıcı
    bandın neden yükselmediğini hiçbir yerden öğrenemiyordu — tam olarak
    kaçınmak istediğimiz sessiz tavan.
    """
    toplam = len(outcomes)
    okunan = sum(1 for o in outcomes if o.state != "unknown")
    return (
        f"İlanın **{toplam} şartından {okunan} tanesini** profilinle "
        f"karşılaştırabildik; kalanı hakkında bilgimiz yok. Bu yüzden güçlü "
        f"eşleşme demiyoruz — **uymadığın anlamına gelmez**, profiline alan "
        f"ekledikçe bu oran yükselir."
    )


def _evidenced_years(profile: CareerProfile) -> float | None:
    """Profilin beyan ettiği **en yüksek** deneyim yılı.

    Vekil bir ölçüdür: profil "toplam kaç yıl çalıştın" diye sormuyor, alan
    başına yıl tutuyor. En yükseğini almak kullanıcının lehinedir — kıdemi
    olduğundan düşük göstermek, tavanı haksız yere indirirdi.

    ``None`` = hiç yıl beyanı yok. Bu "sıfır yıl" DEĞİLDİR (D-011); doğrulanamaz
    demektir ve tavan da bu yüzden iner.
    """
    years = [f.years for f in profile.facts if f.years is not None]
    return max(years) if years else None


def _seniority_cap(job_level: str | None,
                   profile: CareerProfile) -> tuple[MatchBand | None, str | None]:
    """Kıdem açığı için bant tavanı ve gerekçesi.

    Yalnızca **üst basamaklar** tavan uygular. `intern`/`junior` rollerde
    tersine bir uyumsuzluk (fazla niteliklilik) olabilir ama o aşırı iddia
    değildir — kapsam dışı bırakıldı, uydurma bir ceza eklemek istemedik.
    """
    need = _SENIORITY_MIN_YEARS.get(job_level or "")
    if need is None:
        return None, None            # kıdem belirtilmemiş → tavan yok (D-011)
    have = _evidenced_years(profile)
    if have is None:
        return _SENIORITY_CAP, (
            f"İlan {job_level} düzeyinde bir rol; bu genellikle {need:.0f}+ yıl "
            f"deneyim ister. Profilinde **yıl bilgisi yok**, bu yüzden kıdem "
            f"şartını doğrulayamıyoruz — eşleşme şartlı sayılır."
        )
    if have < need:
        return _SENIORITY_CAP, (
            f"İlan {job_level} düzeyinde bir rol ({need:.0f}+ yıl beklenir); "
            f"profilinde beyan edilen en yüksek deneyim {have:.0f} yıl. "
            f"Bu seni **eler demiyoruz** — yalnızca güçlü eşleşme diyecek "
            f"dayanağımız yok."
        )
    return None, None


def _band(
    score: float,
    has_blocking_unmet: bool,
    has_pending_verification: bool,
    discriminative_assessed: int,
    seniority_cap: MatchBand | None = None,
    extra_caps: tuple[MatchBand | None, ...] = (),
) -> MatchBand:
    if has_blocking_unmet:
        # Hard şart karşılanmıyorsa hiçbir koşulda "güçlü" denmez (FR-402).
        return MatchBand.WEAK
    if has_pending_verification:
        # Zorunlu belge doğrulanmadan eşleşme kesinleşmez (D-012).
        return MatchBand.CONDITIONAL

    if score >= 0.85:
        band = MatchBand.STRONG
    elif score >= 0.6:
        band = MatchBand.GOOD
    elif score >= 0.35:
        band = MatchBand.CONDITIONAL
    else:
        band = MatchBand.WEAK

    # Tavanların **en düşüğü** uygulanır: kanıt miktarı (D-022), kıdem (D-063),
    # zorunlu-şart ve kanıt oranı (D-064) bağımsız kısıtlardır; biri diğerini
    # gevşetemez.
    for cap in (_cap_for(discriminative_assessed), seniority_cap, *extra_caps):
        if cap is not None and _BAND_RANK[band] > _BAND_RANK[cap]:
            band = cap
    return band


def _confidence(coverage: float, unknown_count: int, calibrated_occupation: bool) -> Confidence:
    """Girdi kalitesinden türetilir; skordan bağımsızdır (D-005).

    Düşüren etkenler: değerlendirilemeyen şart oranı, occupation'ın kalibre
    edilmemiş olması (D-008 generic tier).
    """
    if not calibrated_occupation:
        return Confidence.LOW
    if coverage >= 0.8 and unknown_count == 0:
        return Confidence.HIGH
    if coverage >= 0.5:
        return Confidence.MEDIUM
    return Confidence.LOW


def match(
    job: JobPosting,
    profile: CareerProfile,
    *,
    semantic_similarity: float = 0.0,
    calibrated_occupation: bool = True,
) -> MatchResult:
    """Bir ilanı bir profile karşı değerlendirir.

    ``semantic_similarity`` 0..1 aralığında bir yeniden sıralama sinyalidir;
    katkısı ``SEMANTIC_MAX_CONTRIBUTION`` ile sınırlıdır ve **hard gate kararı
    veremez** (D-017).
    """
    outcomes = tuple(evaluate_requirement(r, profile) for r in job.requirements)

    if job.is_public_sector:
        # D-015: listing-only / guidance mode — skor ve bant üretilmez.
        return MatchResult(
            job=job,
            outcomes=outcomes,
            band=None,
            confidence=None,
            listing_only=True,
        )

    base, coverage = _structured_score(outcomes)

    # Değerlendirilebilen şartların hiçbiri mesleğe özgü değilse, elde bir
    # eşleşme iddiası kuracak kanıt yoktur. "İngilizce biliyorsun" bir hukuk
    # ilanı için uyum kanıtı değildir.
    discriminative_assessed = sum(
        1 for o in outcomes
        if o.state != "unknown"
        and o.requirement.category not in NON_DISCRIMINATIVE_CATEGORIES
        and not o.requirement.is_legal_eligibility
    )

    if not outcomes or coverage == 0.0 or discriminative_assessed == 0:
        # Üç durum da aynı sonuca çıkar: elimizde bant kuracak kanıt yok.
        #
        # (0) İlandan **hiç şart çıkarılamadı**. Bu, bilgisizliğin en uç hali
        #     ve bir zamanlar kontrolün DIŞINDA kalıyordu (`outcomes and ...`):
        #     boş liste skorlamaya düşüyor, skor 0 çıkıyor ve ilan "zayıf
        #     eşleşme" etiketi alıyordu. Gerçek korpusta **472 ilan** böyle
        #     yanlış etiketlenmişti — kullanıcıya "sen uymuyorsun" deniyordu,
        #     oysa doğrusu "bu ilanı okuyamadık"tı. D-019'un önlemek için
        #     yazıldığı hatanın ta kendisi.
        #
        # (a) Hiçbir şart değerlendirilemedi. Skor 0 çıkar ve bu "zayıf
        #     eşleşme"ye dönerdi — oysa sistemin söylediği "uymuyorsun" değil,
        #     "bilmiyorum"dur. Bu ikisini bant düzeyinde de ayırmak D-011'in
        #     gereğidir; aksi halde `unknown` arka kapıdan `unmet` gibi
        #     cezalandırılmış olur.
        # (b) Değerlendirilenlerin hepsi ayırt edici olmayan şartlar. Bunlara
        #     dayanıp "güçlü eşleşme" demek uydurma bir iddia olurdu.
        return MatchResult(
            job=job,
            outcomes=outcomes,
            band=None,
            confidence=None,
            insufficient_data=True,
        )

    # Semantic katkı: structured evidence'ı ezemez, sınırlı ve low-confidence'ta kapalı.
    sem = 0.0
    if coverage > 0 and semantic_similarity > 0:
        sem = min(max(semantic_similarity, 0.0), 1.0) * SEMANTIC_MAX_CONTRIBUTION
    score = min(1.0, base * (1 - SEMANTIC_MAX_CONTRIBUTION) + sem)

    unknown_count = sum(1 for o in outcomes if o.state == "unknown")
    has_blocking = any(o.state == "unmet" and o.requirement.kind == "hard" for o in outcomes)
    pending_verify = any(
        o.state == "unknown" and o.unknown_reason == "unverified_gate_field"
        for o in outcomes
    )

    sen_cap, sen_note = _seniority_cap(job.experience_level, profile)
    hard_cap, hard_note = _hard_unknown_cap(outcomes)
    cov_cap = _coverage_cap(coverage)
    band = _band(score, has_blocking, pending_verify, discriminative_assessed,
                 seniority_cap=sen_cap, extra_caps=(hard_cap, cov_cap))

    # Notlar yalnızca tavan GERÇEKTEN bandı düşürdüyse anlamlıdır: skor zaten
    # "şartlı" veriyorsa tavandan söz etmek yanıltıcı olurdu.
    def _if_bit(cap, note):
        return note if (cap is not None and band == cap) else None

    return MatchResult(
        job=job,
        outcomes=outcomes,
        band=band,
        confidence=_confidence(coverage, unknown_count, calibrated_occupation),
        semantic_contribution=sem,
        seniority_note=_if_bit(sen_cap, sen_note),
        requirement_gap_note=_if_bit(hard_cap, hard_note),
        coverage_note=_if_bit(cov_cap, _coverage_note(outcomes)),
    )
