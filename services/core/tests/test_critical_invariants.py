"""Audit'in iki CRITICAL bulgusunun regression koruması.

Bu testler geçmiyorsa MAT-01 veya AIX-01 geri gelmiş demektir.
TEST_STRATEGY §4 → "Üç durum testi" ve "Gate koruması testi".
"""

from __future__ import annotations

import pytest

from isuygun_core.domain import (
    CareerProfile,
    JobPosting,
    ProfileFact,
    Requirement,
    RequirementOutcome,
    evaluate_requirement,
)
from isuygun_core.explanation import build_explanation
from isuygun_core.matching import SEMANTIC_MAX_CONTRIBUTION, match


# --------------------------------------------------------------------------
# MAT-01 — "profilde bilgi yok" asla "karşılanmıyor" demek değildir
# --------------------------------------------------------------------------


def test_missing_profile_data_yields_unknown_not_unmet():
    req = Requirement(key="forklift", label="Forklift belgesi", kind="required", category="certificate")
    empty = CareerProfile(profile_id="p1")

    out = evaluate_requirement(req, empty)

    assert out.state == "unknown", "Profilde bilgi yoksa sonuç unmet OLAMAZ (MAT-01)"
    assert out.unknown_reason == "missing_profile_data"


def test_unknown_requires_a_reason():
    """`unknown` gerekçesiz üretilemez — bilgi kaybını yapısal olarak engeller."""
    req = Requirement(key="x", label="X", kind="required", category="skill")
    with pytest.raises(ValueError):
        RequirementOutcome(requirement=req, state="unknown")


def test_non_unknown_cannot_carry_reason():
    req = Requirement(key="x", label="X", kind="required", category="skill")
    with pytest.raises(ValueError):
        RequirementOutcome(requirement=req, state="met", unknown_reason="missing_profile_data")


def test_unknown_does_not_lower_score_like_unmet():
    """Aynı ilan: bir profilde şart `unknown`, diğerinde `unmet`.

    `unknown` olan profil, `unmet` olandan daha kötü bir bant ALMAMALIDIR.
    """
    reqs = (
        Requirement(key="exp", label="3 yıl deneyim", kind="required", category="experience", min_years=3),
        Requirement(key="skill_a", label="Depo sistemi", kind="required", category="skill"),
    )
    job = JobPosting(
        job_id="j", title="Depo Görevlisi", employer="X", city="İzmit",
        occupation_id="warehouse", source="fixture", requirements=reqs,
    )

    # A: skill bilgisi profilde YOK → unknown
    prof_unknown = CareerProfile(
        profile_id="a",
        facts=(ProfileFact(key="exp", category="experience", verification="user_asserted", years=5),),
    )
    # B: skill var ama deneyim yetersiz → unmet
    prof_unmet = CareerProfile(
        profile_id="b",
        facts=(
            ProfileFact(key="exp", category="experience", verification="user_asserted", years=1),
            ProfileFact(key="skill_a", category="skill", verification="user_asserted"),
        ),
    )

    r_unknown = match(job, prof_unknown)
    r_unmet = match(job, prof_unmet)

    assert r_unknown.unknown and not r_unknown.unmet
    assert r_unmet.unmet

    # unknown'lı profil skordan ceza almadığı için bandı daha iyi olmalı
    order = ["weak", "cond", "good", "strong"]
    assert order.index(r_unknown.band.value) >= order.index(r_unmet.band.value), (
        "unknown, unmet gibi cezalandırılıyor — D-011 ihlali"
    )


def test_all_unknown_produces_no_band_at_all():
    """Hiçbir şart değerlendirilemediyse "Zayıf eşleşme" DENMEZ.

    Skor 0 çıkıp zayıf banda düşerse, `unknown` arka kapıdan `unmet` gibi
    cezalandırılmış olur — D-011'in bant düzeyindeki ihlali. Şoför profiline
    hemşire ilanı "sana uymuyor" diye gösterilemez; sistem "bilmiyorum" der.
    """
    reqs = tuple(
        Requirement(key=f"nurse_{i}", label=f"Şart {i}", kind="required", category="skill")
        for i in range(3)
    )
    job = JobPosting(job_id="j", title="Hemşire", employer="E", city="Konya",
                     occupation_id="nurse", source="fixture", requirements=reqs)
    driver = CareerProfile(
        profile_id="p",
        facts=(ProfileFact(key="license_ce", category="license", verification="verified"),),
    )

    r = match(job, driver)

    assert r.insufficient_data
    assert r.band is None, "Değerlendirilemeyen ilan için bant üretilemez"
    assert r.confidence is None

    exp = build_explanation(r)
    assert exp.band_label is None
    assert exp.insufficient_data_note is not None
    assert exp.worth_applying_rule == "insufficient_data"
    assert "uymadığı anlamına gelmez" in exp.insufficient_data_note


def test_partial_coverage_still_produces_a_band():
    """Tek bir şart bile değerlendirilebiliyorsa bant üretilir."""
    reqs = (
        Requirement(key="a", label="A", kind="required", category="skill"),
        Requirement(key="b", label="B", kind="required", category="skill"),
    )
    job = JobPosting(job_id="j", title="T", employer="E", city="C",
                     occupation_id="o", source="fixture", requirements=reqs)
    prof = CareerProfile(profile_id="p",
                         facts=(ProfileFact(key="a", category="skill", verification="user_asserted"),))

    r = match(job, prof)
    assert not r.insufficient_data and r.band is not None


def test_no_unevidenced_claims_in_why():
    """`why` yalnızca karşılanmış şartlardan üretilir; kanıtsız cümle yok."""
    reqs = (Requirement(key="x", label="X", kind="required", category="skill"),)
    job = JobPosting(job_id="j", title="T", employer="E", city="C",
                     occupation_id="o", source="fixture", requirements=reqs)

    exp = build_explanation(match(job, CareerProfile(profile_id="p")))
    assert exp.why == (), "Karşılanan şart yokken gerekçe cümlesi üretilmemeli"


def test_explanation_separates_three_states():
    reqs = (
        Requirement(key="have", label="Var olan", kind="required", category="skill"),
        Requirement(key="short", label="Deneyim", kind="required", category="experience", min_years=10),
        Requirement(key="absent", label="Bilinmeyen", kind="required", category="skill"),
    )
    job = JobPosting(job_id="j", title="T", employer="E", city="C",
                     occupation_id="o", source="fixture", requirements=reqs)
    prof = CareerProfile(
        profile_id="p",
        facts=(
            ProfileFact(key="have", category="skill", verification="user_asserted"),
            ProfileFact(key="short", category="experience", verification="user_asserted", years=2),
        ),
    )

    exp = build_explanation(match(job, prof))

    assert len(exp.met) == 1 and len(exp.unmet) == 1 and len(exp.unknown) == 1
    # unknown satırı kullanıcıya eylem sunmalı, suçlamamalı
    assert exp.unknown[0].action_label == "Profilime ekle"


# --------------------------------------------------------------------------
# AIX-01 — doğrulanmamış gate-relevant belge `met` yapamaz
# --------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["unverified", "user_asserted"])
def test_unverified_gate_field_never_met(state):
    req = Requirement(
        key="nurse_license", label="Hemşirelik tescil belgesi",
        kind="hard", category="license",
    )
    prof = CareerProfile(
        profile_id="p",
        facts=(ProfileFact(key="nurse_license", category="license", verification=state),),
    )

    out = evaluate_requirement(req, prof)

    assert out.state != "met", f"'{state}' bir gate alanını met yapamaz (AIX-01)"
    assert out.state == "unknown"
    assert out.unknown_reason == "unverified_gate_field"


def test_verified_gate_field_becomes_met():
    req = Requirement(key="nurse_license", label="Hemşirelik tescil belgesi",
                      kind="hard", category="license")
    prof = CareerProfile(
        profile_id="p",
        facts=(ProfileFact(key="nurse_license", category="license", verification="verified"),),
    )
    assert evaluate_requirement(req, prof).state == "met"


def test_pending_verification_forces_conditional_band():
    """Zorunlu belge doğrulanmadıkça bant asla 'güçlü' olmaz."""
    reqs = (
        Requirement(key="lic", label="Lisans", kind="hard", category="license"),
        Requirement(key="s1", label="Beceri 1", kind="required", category="skill"),
        Requirement(key="s2", label="Beceri 2", kind="required", category="skill"),
    )
    job = JobPosting(job_id="j", title="Hemşire", employer="E", city="Konya",
                     occupation_id="nurse", source="fixture", requirements=reqs)
    prof = CareerProfile(
        profile_id="p",
        facts=(
            ProfileFact(key="lic", category="license", verification="user_asserted"),
            ProfileFact(key="s1", category="skill", verification="user_asserted"),
            ProfileFact(key="s2", category="skill", verification="user_asserted"),
        ),
    )

    r = match(job, prof)
    assert r.band.value == "cond"
    assert r.needs_verification

    exp = build_explanation(r)
    assert exp.verification_notice is not None
    assert exp.worth_applying_rule == "hard_unknown_verify"


# --------------------------------------------------------------------------
# D-005 / D-015 / D-013 / D-017
# --------------------------------------------------------------------------


def test_no_percentage_anywhere_in_explanation():
    """Match Score hiçbir yerde yüzde olarak sunulmaz (D-005)."""
    req = Requirement(key="a", label="A", kind="required", category="skill")
    job = JobPosting(job_id="j", title="T", employer="E", city="C",
                     occupation_id="o", source="fixture", requirements=(req,))
    prof = CareerProfile(profile_id="p",
                         facts=(ProfileFact(key="a", category="skill", verification="user_asserted"),))

    exp = build_explanation(match(job, prof))
    blob = " ".join(
        [exp.band_label or "", exp.confidence_label or "", exp.worth_applying, exp.disclaimer]
        + [l.text + l.evidence for l in exp.met + exp.unmet + exp.unknown]
    )
    assert "%" not in blob
    assert "garanti" in exp.disclaimer.lower() or "anlamına gelmez" in exp.disclaimer


def test_public_sector_produces_no_score():
    """D-015: kamu ilanında bant ve confidence üretilmez."""
    job = JobPosting(
        job_id="j7", title="Sözleşmeli Şoför Alımı", employer="Kamu kurumu",
        city="Ankara", occupation_id="driver", source="Kamu İlan",
        is_public_sector=True,
        requirements=(Requirement(key="a", label="A", kind="required", category="skill"),),
    )
    r = match(job, CareerProfile(profile_id="p"))

    assert r.band is None and r.confidence is None and r.listing_only

    exp = build_explanation(r)
    assert exp.band_label is None
    assert exp.listing_only_note is not None
    assert "uygunluk değerlendirmesi yapılmaz" in exp.listing_only_note


def test_legal_eligibility_never_unmet():
    """D-013: yaş/sağlık/askerlik şartı skora girmez, unmet üretmez."""
    req = Requirement(
        key="military", label="Askerlik durumu", kind="hard",
        category="other", is_legal_eligibility=True,
    )
    out = evaluate_requirement(req, CareerProfile(profile_id="p"))
    assert out.state == "unknown"

    job = JobPosting(job_id="j", title="T", employer="E", city="C",
                     occupation_id="o", source="fixture", requirements=(req,))
    exp = build_explanation(match(job, CareerProfile(profile_id="p")))
    assert exp.legal_eligibility_notices
    assert "değerlendirmeye katılmaz" in exp.legal_eligibility_notices[0]


def test_semantic_cannot_override_structured():
    """D-017: semantic katkı structured evidence'ı ezemez."""
    reqs = tuple(
        Requirement(key=f"r{i}", label=f"Şart {i}", kind="required",
                    category="experience", min_years=5)
        for i in range(4)
    )
    job = JobPosting(job_id="j", title="T", employer="E", city="C",
                     occupation_id="o", source="fixture", requirements=reqs)

    # (a) Profil boş: semantic tavanda olsa bile bant HİÇ üretilmez.
    r_empty = match(job, CareerProfile(profile_id="p"), semantic_similarity=1.0)
    assert r_empty.band is None, "Yalnızca semantic ile bant üretilemez"
    assert r_empty.semantic_contribution == 0.0

    # (b) Dört şart da gerçekten karşılanmıyor: semantic bunu telafi edemez.
    prof = CareerProfile(
        profile_id="p",
        facts=tuple(
            ProfileFact(key=f"r{i}", category="experience",
                        verification="user_asserted", years=1)
            for i in range(4)
        ),
    )
    r = match(job, prof, semantic_similarity=1.0)
    assert len(r.unmet) == 4
    assert r.semantic_contribution <= SEMANTIC_MAX_CONTRIBUTION + 1e-9
    assert r.band.value == "weak", "Yalnızca semantic ile zayıf bant yükseltilemez"


def test_uncalibrated_occupation_lowers_confidence():
    """D-008: generic tier occupation'da confidence düşürülür."""
    req = Requirement(key="a", label="A", kind="required", category="skill")
    job = JobPosting(job_id="j", title="T", employer="E", city="C",
                     occupation_id="teacher", source="fixture", requirements=(req,))
    prof = CareerProfile(profile_id="p",
                         facts=(ProfileFact(key="a", category="skill", verification="user_asserted"),))

    assert match(job, prof, calibrated_occupation=True).confidence.value == "high"
    assert match(job, prof, calibrated_occupation=False).confidence.value == "low"
