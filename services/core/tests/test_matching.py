

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


# ---------------------------------------------------------------------------
# D-064 — zorunlu şart bilinmiyor + kanıt oranı tavanları
# ---------------------------------------------------------------------------


def _job_with(reqs, level=None):
    from isuygun_core.domain import JobPosting

    return JobPosting(
        job_id="j", title="Rol", employer="X", city="İstanbul",
        occupation_id="Yazılım ve veri", source="t", experience_level=level,
        requirements=tuple(reqs),
    )


def _req(key, kind="required", category="skill", **kw):
    from isuygun_core.domain import Requirement

    return Requirement(key=key, label=key, kind=kind, category=category, **kw)


def test_unknown_hard_requirement_blocks_strong():
    """Profilde karşılığı olmayan **zorunlu** şart varsa "güçlü" denmez.

    Ölçülen hata (D-063 sonrası kalan): "Yüksek lisans zorunlu" / "Almanca
    zorunlu" şartları profilde hiç yokken ilan "güçlü eşleşme" görünüyordu —
    `unknown` skoru düşürmediği için (D-011, doğru kural) skor 1.0 çıkıyordu.
    """
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    job = _job_with([_req("python"), _req("sql"), _req("german", kind="hard")])
    r = match(job, _profile(years=5, n=2), calibrated_occupation=True)
    assert r.band == MatchBand.CONDITIONAL, f"{r.band} geldi"
    assert r.requirement_gap_note and "german" in r.requirement_gap_note
    assert "eler demiyoruz" in r.requirement_gap_note


def test_low_confidence_extraction_does_not_cap():
    """Bilinmeyenin sebebi BİZİM çıkarımımızsa tavan uygulanmaz (FS-4).

    Ayrım kritik: ilanı güvenle okuyamadığımız için kullanıcının bandını
    düşürmek, olmayan bir şartı ona yüklemek olurdu. Tavan yalnızca eksiklik
    PROFİLDEN kaynaklandığında iner.
    """
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    # Kapsama YÜKSEK tutulur (5 karşılanan şart) ki bu test yalnızca
    # zorunlu-şart tavanını sınasın — kanıt oranı tavanı (D-064) karışmasın.
    job = _job_with([_req(k) for k in ("python", "sql", "docker_k8s", "cicd", "cloud")]
                    + [_req("german", kind="hard", extraction_confidence=0.2)])
    r = match(job, _profile(years=5, n=5), calibrated_occupation=True)
    assert r.requirement_gap_note is None
    assert r.band == MatchBand.STRONG, f"{r.band} geldi"


def test_legal_eligibility_hard_gap_does_not_cap():
    """Yasal uygunluk şartı skora girmez (D-013), tavana da girmez."""
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    job = _job_with([_req(k) for k in ("python", "sql", "docker_k8s", "cicd", "cloud")]
                    + [_req("legal_military", kind="hard", category="military",
                            is_legal_eligibility=True)])
    r = match(job, _profile(years=5, n=5), calibrated_occupation=True)
    assert r.requirement_gap_note is None
    assert r.band == MatchBand.STRONG


def test_coverage_cap_limits_claim_when_most_requirements_unassessed():
    """İlanın söylediklerinin çoğunu okuyamadıysak "güçlü" diyemeyiz.

    12 şartlı ilanda 3'ünü değerlendirip tam uyum iddia etmek, ilanın üçte
    ikisi hakkında hiçbir şey bilmeden konuşmaktır. Eşikler ölçümle seçildi:
    <%35 → şartlı, <%60 → iyi (bkz. golden/README).
    """
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    # 3 karşılanan + 9 profilde olmayan = kapsama 3/12 = %25
    reqs = [_req(k) for k in ("python", "sql", "docker_k8s")]
    reqs += [_req(f"yok{i}") for i in range(9)]
    r = match(_job_with(reqs), _profile(years=5, n=3), calibrated_occupation=True)
    assert r.band == MatchBand.CONDITIONAL, f"{r.band} geldi"


def test_high_coverage_still_allows_strong():
    """Kapsama yüksekse tavan uygulanmaz — tavan ceza değil."""
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    reqs = [_req(k) for k in ("python", "sql", "docker_k8s", "cicd")]
    r = match(_job_with(reqs), _profile(years=5, n=4), calibrated_occupation=True)
    assert r.band == MatchBand.STRONG


def test_caps_never_produce_weak():
    """Hiçbir tavan "zayıf" üretmez: eleme iddiası D-019'a aykırıdır.

    Zayıf yalnızca gerçekten karşılanmayan şarttan (unmet) gelir.
    """
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    senaryolar = [
        _job_with([_req("python"), _req("sql"), _req("german", kind="hard")],
                  level="executive"),
        _job_with([_req("python")] + [_req(f"yok{i}") for i in range(11)]),
    ]
    for job in senaryolar:
        r = match(job, _profile(years=None, n=2), calibrated_occupation=True)
        assert r.band != MatchBand.WEAK, f"tavan zayıf üretti: {job.title}"


# ---------------------------------------------------------------------------
# D-022 — kanıt MİKTARI tavanının gerekçesi (canlı persona testinden)
# ---------------------------------------------------------------------------
# Canlı testte kaynakçı profili "Gaz Altı Kaynakçı" ilanının İKİ şartını da
# karşılıyordu, bilinmeyen tek satır yoktu — yine de "şartlı eşleşme · güven
# düşük" yazıyordu ve ekranda gerekçe YOKTU. Diğer üç tavanın notu vardı; en sık
# bağlayan bu tavanın notu hiç yazılmamıştı. Sessiz tavan, açıklaması olmayan
# bir cezadır.


def _thin_job(n_disc=1):
    """`n_disc` adet AYIRT EDİCİ şart içeren "ince" ilan.

    Gerçek karşılığı: nitelikleri iki satırla yazan mavi yaka ilanları.
    """
    from isuygun_core.domain import JobPosting, Requirement

    keys = ["python", "sql", "docker_k8s"][:n_disc]
    return JobPosting(
        job_id="j", title="Kaynakçı", employer="X", city="İstanbul",
        occupation_id="Üretim ve teknik", source="t",
        requirements=tuple(
            Requirement(key=k, label=k, kind="required", category="skill")
            for k in keys
        ),
    )


def test_evidence_cap_explains_itself():
    """Tek ayırt edici şart okunabildiyse tavan uygulanır VE gerekçesi yazılır."""
    from isuygun_core import match
    from isuygun_core.domain import MatchBand

    r = match(_thin_job(1), _profile(years=8), calibrated_occupation=True)
    assert r.band == MatchBand.CONDITIONAL, f"kanıt tavanı uygulanmadı: {r.band}"
    assert not r.unmet and not r.unknown, "kurgu bozuk: eksik/bilinmeyen olmamalı"
    assert r.evidence_note, "en sık bağlayan tavanın gerekçesi ekranda olmalı"
    assert "1 şart" in r.evidence_note


def test_evidence_note_blames_the_posting_not_the_user():
    """Cümle yükü doğru tarafa koymalı: eksik olan ilan metni, kullanıcı değil.

    Kullanıcı okunabilen her şartı karşılıyor. Bunu "sende eksik var" diye
    sunmak, karşıladığı şartı görmezden gelmek olur.
    """
    from isuygun_core import match

    r = match(_thin_job(1), _profile(years=8), calibrated_occupation=True)
    assert "eksik olan sen değil" in r.evidence_note


def test_evidence_note_absent_when_cap_did_not_bite():
    """Yeterli kanıt varken tavandan söz etmek yanıltıcı olur."""
    from isuygun_core import match

    r = match(_skill_job("mid", n=4), _profile(years=8), calibrated_occupation=True)
    assert r.evidence_note is None, \
        f"tavan bağlamadığı hâlde not üretildi: {r.evidence_note}"


def test_worth_applying_does_not_claim_missing_points_when_nothing_is_missing():
    """"aşağıdaki noktalar eksik görünüyor" — eksik hiçbir şey yokken YANLIŞTI.

    Defterde tek bir eksik/bilinmeyen satır yokken bu cümle yazılıyordu;
    kullanıcı ekranda göremediği bir eksiği arıyordu.
    """
    from isuygun_core import match
    from isuygun_core.explanation import build_explanation

    r = match(_thin_job(1), _profile(years=8), calibrated_occupation=True)
    exp = build_explanation(r)
    assert not r.unmet and not r.unknown
    assert "eksik görünüyor" not in exp.worth_applying, \
        f"eksik yokken eksiklik iddia ediliyor: {exp.worth_applying!r}"
    assert exp.worth_applying_rule == "met_all_thin_posting"
    # Gerekçe kaybolmasın: not açıklamada da taşınmalı.
    assert exp.evidence_note and "1 şart" in exp.evidence_note
