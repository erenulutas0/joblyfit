"""İşe Uygun — paylaşılan domain çekirdeği.

Bu paket ingestion, matching ve API servislerinin ortak tip kaynağıdır.
Domain invariant'ları burada tanımlanır; başka katmanda tekrar edilmez.
"""

from .domain import (
    CareerProfile,
    Confidence,
    JobPosting,
    MatchBand,
    ProfileFact,
    Requirement,
    RequirementOutcome,
    RequirementState,
    UnknownReason,
    VerificationState,
    evaluate_requirement,
    partition,
)
from .explanation import MatchExplanation, build_explanation
from .matching import MatchResult, match

__all__ = [
    "CareerProfile", "Confidence", "JobPosting", "MatchBand", "ProfileFact",
    "Requirement", "RequirementOutcome", "RequirementState", "UnknownReason",
    "VerificationState", "evaluate_requirement", "partition",
    "MatchExplanation", "build_explanation", "MatchResult", "match",
]
