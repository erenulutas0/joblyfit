

def test_job_with_no_requirements_gets_no_band():
    """Şart çıkarılamayan ilan bant ALMAZ (D-019 regresyonu).

    Koşulun başındaki `outcomes and ...` yüzünden boş şart listesi kontrolün
    dışında kalıyor, skorlamaya düşüyor ve ilan "zayıf eşleşme" etiketi
    alıyordu. Gerçek korpusta 472 ilan böyle yanlış etiketlenmişti:
    kullanıcıya "uymuyorsun" deniyordu, doğrusu "okuyamadık"tı.
    """
    from isuygun_core import match
    from isuygun_core.domain import CareerProfile, JobPosting

    job = JobPosting(
        job_id="j", title="Spring Boot Development Camp", employer="X",
        city="İstanbul", occupation_id="genel", source="t", requirements=(),
    )
    result = match(job, CareerProfile(profile_id="p"))
    assert result.band is None, "şartsız ilan bant almamalı"
    assert result.insufficient_data is True


# ---------------------------------------------------------------------------
# D-063 — kıdem tavanı
# ---------------------------------------------------------------------------


def _skill_job(level, n=4, title="Rol"):
    """`n` adet karşılanabilir beceri şartı olan ilan (skor yükselsin diye)."""
    from isuygun_core.domain import JobPosting, Requirement

    keys = ["python", "sql", "docker_k8s", "cicd", "cloud", "git"][:n]
    return JobPosting(
        job_id="j", title=title, employer="X", city="İstanbul",
        occupation_id="Yazılım ve veri", source="t",
        experience_level=level,
        requirements=tuple(
            Requirement(key=k, label=k, kind="required", category="skill")
            for k in keys
        ),
    )


def _profile(years=None, n=6):
    from isuygun_core.domain import CareerProfile, ProfileFact

    keys = ["python", "sql", "docker_k8s", "cicd", "cloud", "git"][:n]
    return CareerProfile(profile_id="p", facts=tuple(
        ProfileFact(key=k, category="skill", verification="user_asserted",
                    years=years)
        for k in keys
    ))


def test_seniority_cap_blocks_strong_when_years_unstated():
    """Yıl beyanı olmayan profile üst düzey rol için "güçlü" DENMEZ.

    Ölçülen hata (D-062): yeni mezun profili — becerileri tutuyor ama hiç yıl
    beyanı yok — Staff/Senior rollerinin %16,8'ine strong/good alıyordu; 49
    ilanda "GÜÇLÜ EŞLEŞME" diyordu. Ürünün önlemek için var olduğu yanlış umut.
    """
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    r = match(_skill_job("senior"), _profile(years=None),
              calibrated_occupation=True)
    assert r.band == MatchBand.CONDITIONAL, \
        f"kıdem doğrulanamazken bant {r.band} olmamalı"
    assert r.seniority_note, "tavanın gerekçesi kullanıcıya söylenmeli"
    assert "yıl bilgisi yok" in r.seniority_note


def test_seniority_cap_lifts_when_years_sufficient():
    """Kıdem yetiyorsa tavan UYGULANMAZ — ceza değil, tavan."""
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    r = match(_skill_job("senior"), _profile(years=8),
              calibrated_occupation=True)
    assert r.band == MatchBand.STRONG, f"8 yıl senior için yeterli, {r.band} geldi"
    assert r.seniority_note is None


def test_seniority_cap_does_not_claim_rejection():
    """Kıdem açığı "zayıf" ÜRETMEZ: adayın eleneceğini iddia etmiyoruz (D-019).

    Tavan en fazla "şartlı"ya çeker ve gerekçesinde bunu açıkça söyler.
    """
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    r = match(_skill_job("executive"), _profile(years=1),
              calibrated_occupation=True)
    assert r.band == MatchBand.CONDITIONAL
    assert r.band != MatchBand.WEAK
    assert "eler demiyoruz" in (r.seniority_note or "")


def test_no_seniority_label_means_no_cap():
    """Kıdem belirtilmemişse tavan yok — "belirtilmemiş" ceza değildir (D-011)."""
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    r = match(_skill_job(None), _profile(years=None), calibrated_occupation=True)
    assert r.band == MatchBand.STRONG
    assert r.seniority_note is None


def test_entry_level_roles_are_not_capped():
    """Giriş düzeyi rollerde tavan yok: fazla niteliklilik aşırı iddia değildir."""
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    for lvl in ("intern", "junior"):
        r = match(_skill_job(lvl), _profile(years=None), calibrated_occupation=True)
        assert r.band == MatchBand.STRONG, f"{lvl} rolü tavana takılmamalı"


def test_lowest_cap_wins_over_evidence_cap():
    """Kanıt tavanı (D-022) ile kıdem tavanı bağımsızdır; en DÜŞÜĞÜ uygulanır.

    Tek şart değerlendirilen bir ilan D-022 gereği en fazla "şartlı"dır; kıdem
    tavanı bunu gevşetemez.
    """
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    r = match(_skill_job("senior", n=1), _profile(years=9), calibrated_occupation=True)
    assert r.band == MatchBand.CONDITIONAL, "kanıt tavanı gevşetilmemeli"


def test_seniority_note_absent_when_cap_did_not_bite():
    """Skor zaten "şartlı" veriyorsa kıdemden söz etmek yanıltıcı olur."""
    from isuygun_core import match
    from isuygun_core.domain import CareerProfile

    # Hiç eşleşen beceri yok → skor düşük; bant kıdem yüzünden değil skordan.
    r = match(_skill_job("senior"), CareerProfile(profile_id="bos"),
              calibrated_occupation=True)
    assert r.seniority_note is None
