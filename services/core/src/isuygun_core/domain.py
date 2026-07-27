"""Domain tipleri — tek doğruluk kaynağı.

Bu modülün asıl işi, audit'in iki CRITICAL bulgusunu **temsil edilemez** kılmak:

* MAT-01 — "profilde bilgi yok" ile "şart karşılanmıyor" aynı şey değildir.
  Bu yüzden hiçbir yerde `bool` ile şart durumu tutulmaz; ``RequirementState``
  üç varyantlıdır ve ``unknown`` kendi gerekçesini taşımak zorundadır.

* AIX-01 — doğrulanmamış bir gate-relevant belge (ehliyet, lisans, çalışma izni)
  hard requirement'ı ``met`` yapamaz. Bu bir runtime kontrolü değil;
  :func:`evaluate_requirement` fonksiyonunun garantisidir.

İlgili kararlar: D-011, D-012, D-005, D-013, D-015, D-017.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Sequence

# --------------------------------------------------------------------------
# Durum tipleri
# --------------------------------------------------------------------------

RequirementState = Literal["met", "unmet", "unknown"]
"""Bir şartın değerlendirme sonucu (D-011). `bool` KULLANILMAZ."""

UnknownReason = Literal[
    "missing_profile_data",       # profilde bu alan hiç yok
    "missing_duration",           # alan var ama kaç yıllık olduğu bilinmiyor
    "unverified_gate_field",      # alan var ama doğrulanmamış (D-012)
    "low_confidence_extraction",  # ilandan güvenle çıkarılamadı (FS-4)
]

VerificationState = Literal["unverified", "user_asserted", "verified"]
"""Profil alanının doğrulama durumu. Gate alanları için yalnızca `verified` yeter."""

RequirementKind = Literal["hard", "required", "preferred"]

# Gate-relevant alanlar: `verified` olmadan hiçbir hard requirement `met` olamaz (D-012).
GATE_RELEVANT_CATEGORIES: frozenset[str] = frozenset(
    {"license", "work_authorization", "legally_required_certificate"}
)

# Ayırt edici olmayan şartlar: mesleğe özgü bilgi taşımazlar.
#
# "İngilizce" ve "lisans mezuniyeti" hemen her beyaz yaka ilanında geçer.
# Bir ilandan yalnızca bunlar çıkarılabildiyse, kullanıcının ikisini de
# karşılıyor olması onun o işe uyduğunu **göstermez**. Gerçek veriyle ilk
# koşuda bir yazılımcı profiline "Legal Professionals — Labor Law" ilanı
# "Güçlü eşleşme" çıkmıştı; sebebi tam olarak buydu.
NON_DISCRIMINATIVE_CATEGORIES: frozenset[str] = frozenset(
    {"language", "education", "shift"}
)

# Kategori yetmiyor: bazı TEK TOKEN'lar da ayırt edici değil (D-081).
#
# Ölçüm (51 + 15 personalık canlı test): "Excel / ofis programları" kategorisi
# `skill` olduğu için ayırt edici sayılıyordu, ama pratikte "lisans mezuniyeti"
# gibi davranıyor — herkeste var, her ofis ilanı istiyor. Sonucu şuydu:
#
#   İnşaat mühendisi → ilk 10 sonucun **6'sı** yalnızca Excel'den eşleşti
#                      ("Finans Uzmanı", "Muhasebe Elemanı"), 4'ü mesleğinden
#   Veri analisti    → ilk 10'un **8'i** Excel; SQL yalnızca 2, Analitik 2
#
# Kategoriyi komple ayırt edici olmaktan çıkarmak yanlış olurdu (Python da
# `skill`). Bu yüzden istisna TOKEN düzeyinde ve açık liste hâlinde: yeni bir
# "herkeste var" token'ı eklenirse fark edilmeden girmesin.
NON_DISCRIMINATIVE_KEYS: frozenset[str] = frozenset({"excel"})


class MatchBand(str, Enum):
    """Kullanıcıya gösterilen eşleşme bandı.

    Yüzde YOKTUR (D-005) — Match Score hiçbir yerde sayısal olarak sunulmaz.
    """

    STRONG = "strong"       # Güçlü eşleşme
    GOOD = "good"           # İyi eşleşme
    CONDITIONAL = "cond"    # Şartlı eşleşme
    WEAK = "weak"           # Zayıf eşleşme


class Confidence(str, Enum):
    """Skordan ayrı bir boyut: girdi kalitesine duyulan güven."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# --------------------------------------------------------------------------
# Profil tarafı
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProfileFact:
    """Kullanıcı profilindeki tek bir doğrulanabilir bilgi."""

    key: str
    category: str
    value: str | None = None
    verification: VerificationState = "unverified"
    years: float | None = None

    @property
    def is_gate_relevant(self) -> bool:
        return self.category in GATE_RELEVANT_CATEGORIES

    @property
    def counts_as_present(self) -> bool:
        """Gate alanı yalnızca `verified` ise "var" sayılır (D-012).

        Gate olmayan alanlarda kullanıcı beyanı yeterlidir.
        """
        if self.is_gate_relevant:
            return self.verification == "verified"
        return self.verification in ("user_asserted", "verified")


@dataclass(frozen=True, slots=True)
class CareerProfile:
    profile_id: str
    occupation_ids: tuple[str, ...] = ()
    facts: tuple[ProfileFact, ...] = ()
    #: Toplam çalışma yılı — beceri başına yıldan AYRI bir beyandır.
    #:
    #: Kıdem tavanı (D-063) "bu kişi senior bir rol için yeterli deneyime sahip
    #: mi" sorusunu soruyor ve bunun doğru sinyali toplam kariyer yılıdır. Önce
    #: yalnızca beceri başına yılın en yükseği kullanılıyordu; `_evidenced_years`
    #: bunu "vekil bir ölçü" olarak açıkça belgeliyordu. Daha kötüsü: arayüz
    #: hiçbir yerde yıl SORMUYORDU, dolayısıyla tavan neredeyse her profilde
    #: bağlıyordu. Ölçüm: 9 yıl beyan edilince 33 sonuçtan 3'ü "şartlı"nın
    #: üstüne çıkıyor; beyan yokken 0'ı çıkıyordu.
    #:
    #: ``None`` = beyan yok. Bu "sıfır yıl" DEĞİLDİR (D-011).
    total_years: float | None = None

    def find(self, key: str) -> ProfileFact | None:
        for f in self.facts:
            if f.key == key:
                return f
        return None


# --------------------------------------------------------------------------
# İlan tarafı
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Requirement:
    """İlandan çıkarılmış tek şart."""

    key: str
    label: str
    kind: RequirementKind
    category: str
    min_years: float | None = None
    # İlandan ne kadar güvenle çıkarıldı (0..1). Düşükse hard eleme yapılmaz (FS-4).
    extraction_confidence: float = 1.0
    # age / health / military gibi yasal-uygunluk şartı (D-013).
    # Skora GİRMEZ; kullanıcıya bilgilendirme olarak gösterilir.
    is_legal_eligibility: bool = False
    source_span: str | None = None

    @property
    def requires_verification(self) -> bool:
        return self.category in GATE_RELEVANT_CATEGORIES


@dataclass(frozen=True, slots=True)
class JobPosting:
    job_id: str
    title: str
    employer: str
    city: str
    occupation_id: str
    source: str
    requirements: tuple[Requirement, ...] = ()
    is_public_sector: bool = False
    #: İşverenin başlıkta beyan ettiği kıdem basamağı (D-063):
    #: intern|junior|mid|senior|lead|architect|executive | None(belirtilmemiş).
    #:
    #: Çıkarımı ingest yapar (``jobmeta``); burada durur çünkü **eşleşmeyi
    #: etkiler**: "Senior" bir rol, ilan metninde yazmasa da örtük bir kıdem
    #: şartıdır. Alan eklenmeden önce eşleşme bunu hiç görmüyordu ve yeni mezun
    #: profiline Staff/Senior rolleri için "güçlü eşleşme" deniyordu (D-062
    #: ölçümü: 49 ilan).
    experience_level: str | None = None


# --------------------------------------------------------------------------
# Değerlendirme sonucu
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RequirementOutcome:
    """Tek bir şartın değerlendirilmiş hali.

    `state == "unknown"` ise `unknown_reason` **zorunludur** — bu, MAT-01'in
    "neden bilinmiyor" bilgisini kaybetmemesini garanti eder.
    """

    requirement: Requirement
    state: RequirementState
    unknown_reason: UnknownReason | None = None
    evidence: str = ""

    def __post_init__(self) -> None:
        if self.state == "unknown" and self.unknown_reason is None:
            raise ValueError(
                f"unknown durumu gerekçesiz olamaz: {self.requirement.key!r}"
            )
        if self.state != "unknown" and self.unknown_reason is not None:
            raise ValueError(
                f"unknown olmayan duruma gerekçe verilemez: {self.requirement.key!r}"
            )

    @property
    def missing_field_hint(self) -> str | None:
        """Kullanıcıya "şunu ekle" demek için kullanılan alan adı."""
        if self.state != "unknown":
            return None
        return self.requirement.label


def evaluate_requirement(
    req: Requirement, profile: CareerProfile
) -> RequirementOutcome:
    """Tek şartı üç durumlu değerlendirir.

    Garantiler:

    * Profilde ilgili bilgi yoksa sonuç **asla** ``unmet`` olmaz → ``unknown``
      (``missing_profile_data``). Bu MAT-01'in doğrudan karşılığıdır.
    * Gate-relevant bir şart, karşılığı olan profil alanı ``verified`` değilse
      ``met`` **olamaz** → ``unknown`` (``unverified_gate_field``). AIX-01.
    * İlandan düşük güvenle çıkarılmış şart hard elemeye dönüşmez → ``unknown``
      (``low_confidence_extraction``). FS-4.
    * Yasal-uygunluk şartı (``is_legal_eligibility``) hiçbir zaman ``unmet``
      üretmez; skora girmez, yalnızca bilgilendirilir. D-013.
    """
    if req.extraction_confidence < 0.5:
        return RequirementOutcome(
            requirement=req,
            state="unknown",
            unknown_reason="low_confidence_extraction",
            evidence="İlan metninden bu şart net olarak çıkarılamadı.",
        )

    if req.is_legal_eligibility:
        # D-013: değerlendirilmez, kullanıcı kaynağa yönlendirilir.
        return RequirementOutcome(
            requirement=req,
            state="unknown",
            unknown_reason="missing_profile_data",
            evidence=(
                "Bu şart ilanda yer alıyor ancak sistem tarafından değerlendirilmez. "
                "Şartı ilanın kendi sayfasından kontrol et."
            ),
        )

    fact = profile.find(req.key)

    if fact is None:
        return RequirementOutcome(
            requirement=req,
            state="unknown",
            unknown_reason="missing_profile_data",
            evidence="Profilinde bu bilgiye dair kayıt yok.",
        )

    if req.requires_verification and fact.verification != "verified":
        return RequirementOutcome(
            requirement=req,
            state="unknown",
            unknown_reason="unverified_gate_field",
            evidence=(
                "Profilinde kayıtlı ama doğrulanmadı. Bu ilan için doğrulama gerekiyor."
            ),
        )

    if not fact.counts_as_present:
        return RequirementOutcome(
            requirement=req,
            state="unknown",
            unknown_reason="missing_profile_data",
            evidence="Profilinde bu bilgi onaylanmamış durumda.",
        )

    if req.min_years is not None:
        if fact.years is None:
            # Beceri profilde VAR; bilinmeyen yalnızca süresi. Bunu
            # "profilinde yok" diye raporlamak kullanıcıya sahip olduğu şeyi
            # yokmuş gibi göstermek olurdu.
            return RequirementOutcome(
                requirement=req,
                state="unknown",
                unknown_reason="missing_duration",
                evidence=(
                    f"Profilinde kayıtlı ama kaç yıl olduğu yazmıyor; "
                    f"ilan en az {req.min_years:g} yıl istiyor."
                ),
            )
        if fact.years < req.min_years:
            return RequirementOutcome(
                requirement=req,
                state="unmet",
                evidence=(
                    f"İlan en az {req.min_years:g} yıl bekliyor; "
                    f"profilinde {fact.years:g} yıl görünüyor."
                ),
            )
        return RequirementOutcome(
            requirement=req,
            state="met",
            evidence=f"Profilinde {fact.years:g} yıl görünüyor.",
        )

    return RequirementOutcome(
        requirement=req,
        state="met",
        evidence=(
            "Profilinde doğrulanmış olarak kayıtlı."
            if fact.verification == "verified"
            else "Profilinde kayıtlı."
        ),
    )


def partition(
    outcomes: Sequence[RequirementOutcome],
) -> tuple[list[RequirementOutcome], list[RequirementOutcome], list[RequirementOutcome]]:
    """Sonuçları met / unmet / unknown olarak üçe ayırır (arayüzdeki defter)."""
    met = [o for o in outcomes if o.state == "met"]
    unmet = [o for o in outcomes if o.state == "unmet"]
    unknown = [o for o in outcomes if o.state == "unknown"]
    return met, unmet, unknown
