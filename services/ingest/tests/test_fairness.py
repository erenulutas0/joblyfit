"""Ayrımcılık/dışlayıcı dil tespiti (D-042).

Testlerin yarısı **yanlış pozitifi** kovalıyor: masum bir ifadeyi ayrımcı diye
işaretlemek hem ilana haksızlık eder hem kullanıcının uyarılara güvenini bozar.
Bu, projenin her yerdeki asimetri ilkesiyle aynı — emin değilsek işaretlemeyiz.
"""

from __future__ import annotations

import pytest

from isuygun_ingest import fairness


def cats(title, desc):
    return {f.category for f in fairness.scan(title, desc)}


# ---------------------------------------------------------------------------
# Yakalanması gerekenler
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("desc", "expected"), [
    ("35 yaş altı adaylar aranıyor.", "age"),
    ("En fazla 40 yaş.", "age"),
    ("25-30 yaş arası.", "age"),
    ("Candidates under 30 years old.", "age"),
    ("Sadece erkek personel alınacaktır.", "gender"),
    ("Bayan eleman aranıyor.", "gender"),
    ("Female candidates only.", "gender"),
    ("Askerliğini yapmış adaylar.", "military"),
    ("Askerlik ile ilişiği olmayan.", "military"),
    ("Evli adaylar tercih edilir.", "marital"),
    ("We need a native English speaker.", "native_speaker"),
    ("Ana dili Türkçe olan.", "native_speaker"),
])
def test_flags_discriminatory_language(desc, expected):
    assert expected in cats("İlan", desc)


def test_multiple_categories_in_one_ad():
    c = cats("Depo", "35 yaş altı, askerliğini yapmış erkek adaylar aranmaktadır.")
    assert {"age", "gender", "military"} <= c


# ---------------------------------------------------------------------------
# Yanlış pozitif tuzakları — asıl önemli kısım
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("desc", [
    "You will manage 50-60 engineers across teams.",   # sayı var, yaş değil
    "5-10 yıl deneyim gereklidir.",                     # yıl, yaş değil
    "Manage a budget of 30-40 million.",
])
def test_numbers_without_age_context_are_not_flagged(desc):
    assert "age" not in cats("Rol", desc)


@pytest.mark.parametrize("desc", [
    "Genç ve dinamik bir ekiple çalışacaksın.",        # betimleyici, şart değil
    "Join our young and dynamic team.",
])
def test_descriptive_youth_is_not_age_requirement(desc):
    assert "age" not in cats("Rol", desc)


@pytest.mark.parametrize("desc", [
    "We actively support women in engineering.",       # kapsayıcı, dışlayıcı değil
    "We value diversity and are an equal opportunity employer.",
    "She will lead a dynamic team.",                   # zamir, şart değil
    "Kadın liderleri destekliyoruz.",
])
def test_inclusive_language_is_not_flagged_as_gender(desc):
    assert "gender" not in cats("Rol", desc)


def test_descriptive_context_suppresses_hard_flag():
    """Şart gibi görünen ifade betimleyici bağlamdaysa düşürülür."""
    # "genç" kelimesi var ama fırsat eşitliği beyanı içinde → işaretlenmez.
    assert not fairness.scan(
        "Rol", "Fırsat eşitliği sağlıyoruz; genç ve dinamik ekibimize katıl.")


# ---------------------------------------------------------------------------
# Çerçeve — hüküm değil, bilgilendirme (T-008)
# ---------------------------------------------------------------------------


def test_flags_inform_never_adjudicate():
    """Not metni 'yasa dışı' demez; 'olabilir' / 'değerlendirilebilir' der ve
    istisna olabileceğini söyler (T-008 çerçevesi)."""
    flags = fairness.scan("Depo", "Sadece erkek eleman aranıyor.")
    note = flags[0].note.lower()
    assert "yasa dışı" not in note and "yasadışı" not in note
    assert "olabilir" in note or "değerlendiril" in note


def test_native_speaker_is_soft():
    """'native speaker' yumuşak işaret: gerçek dil ihtiyacı olabilir, yasak
    değil — kapsayıcılık önerisi olarak sunulur."""
    flags = fairness.scan("Writer", "Native English speaker required.")
    assert flags and flags[0].severity == "soft"


def test_gender_is_hard():
    flags = fairness.scan("Depo", "Sadece bayan personel.")
    assert flags and flags[0].severity == "hard"


def test_evidence_is_present():
    """İddia kanıtsız olmaz: her işaret metinden bir kanıt taşır."""
    for f in fairness.scan("Depo", "35 yaş altı erkek adaylar."):
        assert f.evidence


def test_clean_ad_yields_no_flags():
    assert fairness.scan(
        "Yazılım Mühendisi",
        "Python ve SQL deneyimi. Uzaktan çalışma imkânı. C1 İngilizce.") == []


def test_fairness_in_cache_fingerprint():
    from isuygun_ingest import cache

    assert "fairness.py" in cache._LOGIC_FILES
