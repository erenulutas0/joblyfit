

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
