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


def _band(score: float, has_blocking_unmet: bool, has_pending_verification: bool) -> MatchBand:
    if has_blocking_unmet:
        # Hard şart karşılanmıyorsa hiçbir koşulda "güçlü" denmez (FR-402).
        return MatchBand.WEAK
    if has_pending_verification:
        # Zorunlu belge doğrulanmadan eşleşme kesinleşmez (D-012).
        return MatchBand.CONDITIONAL
    if score >= 0.85:
        return MatchBand.STRONG
    if score >= 0.6:
        return MatchBand.GOOD
    if score >= 0.35:
        return MatchBand.CONDITIONAL
    return MatchBand.WEAK


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

    if coverage == 0.0 and outcomes:
        # Tek bir şart bile değerlendirilemedi. Skor 0 çıkar ve bu "zayıf
        # eşleşme"ye dönerdi — oysa sistemin söylediği "uymuyorsun" değil,
        # "bilmiyorum"dur. Bu ikisini bant düzeyinde de ayırmak D-011'in
        # gereğidir; aksi halde `unknown` arka kapıdan `unmet` gibi
        # cezalandırılmış olur.
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

    return MatchResult(
        job=job,
        outcomes=outcomes,
        band=_band(score, has_blocking, pending_verify),
        confidence=_confidence(coverage, unknown_count, calibrated_occupation),
        semantic_contribution=sem,
    )
