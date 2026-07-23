"""Ingestion invariant'ları.

Kapsanan audit bulguları:

* **SCR-01 / ARC-04** — işveren kimliği çözümlenmezse duplicate anahtarı çalışmaz.
* **SCR-02** — tek blocking anahtarı, agency'nin gizlediği kopyaları
  *hiç karşılaştırmadan* kaçırır.
* **D-002 / D-018** — izinsiz kaynağa ağ erişimi kod düzeyinde engellenir.
"""

from __future__ import annotations

import pytest

from isuygun_ingest import registry
from isuygun_ingest.pipeline import (
    CONTENT_SIMILARITY_THRESHOLD,
    RawPosting,
    cluster,
    content_similarity,
    normalize,
    normalize_employer,
    normalize_title,
    pick_canonical,
    run_fixture_ingest,
)

V = "test-0.0.0"


def _raw(**kw) -> RawPosting:
    base = dict(
        source_id="src-fixture-001",
        source_posting_ref="ref",
        url="https://example.invalid/x",
        title="Başlık",
        employer="İşveren",
        city="Bursa",
        occupation_id="Muhasebe ve finans",
        description="metin",
    )
    base.update(kw)
    return RawPosting(**base)


# --------------------------------------------------------------------------
# D-002 / D-018 — izin kapısı
# --------------------------------------------------------------------------


@pytest.mark.parametrize("source_id", ["src-tr-001", "src-tr-006", "src-tr-008"])
def test_conditional_source_cannot_fetch(source_id):
    """İzni `conditional` olan kaynak ağa çıkamaz — uyarı değil, exception."""
    with pytest.raises(registry.PermissionError_):
        registry.assert_fetchable(source_id)


@pytest.mark.parametrize("source_id", ["src-tr-014", "src-tr-015"])
def test_rejected_source_cannot_fetch(source_id):
    with pytest.raises(registry.PermissionError_):
        registry.assert_fetchable(source_id)


def test_unregistered_source_rejected():
    """Registry'de olmayan kaynaktan ingestion yapılamaz (FR-202)."""
    with pytest.raises(KeyError):
        registry.assert_fetchable("src-tr-999")


def test_allowed_sources_must_carry_evidence():
    """D-020 denetimi: izin iddiası **kanıtsız** yazılamaz.

    D-018'in "hiçbir kaynağa crawl yok" kuralının yerini bu aldı. Bir kaynağı
    `allowed` yapmak serbest değil; gerekçesi kayıtta durmak zorunda.
    """
    offenders = registry.allowed_without_evidence()
    assert offenders == [], [r.source_id for r in offenders]
    assert registry.audit()["kanitsiz_allowed"] == 0


def test_rejected_sources_stay_rejected():
    """D-020 gate'i açtı diye LinkedIn/Indeed açılmadı."""
    for sid in ("src-tr-014", "src-tr-015"):
        assert registry.get(sid).scraping_permission == "rejected"
        assert not registry.get(sid).may_fetch_network


def test_every_board_points_at_an_allowed_source():
    """Çekilen her pano, izinli bir kayda bağlı olmalı."""
    for source_id, _platform, slug, _employer in registry.BOARDS:
        rec = registry.assert_fetchable(source_id)
        assert rec.scraping_permission == "allowed", slug


def test_permission_error_names_the_gate():
    """Hata mesajı bypass yolu değil, izin yolunu göstermeli."""
    with pytest.raises(registry.PermissionError_) as e:
        registry.assert_fetchable("src-tr-001")
    msg = str(e.value)
    assert "OPEN-19" in msg or "OPEN-09" in msg
    assert "D-002" in msg


# --------------------------------------------------------------------------
# SCR-01 — işveren kimliği çözümleme
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a,b",
    [
        ("Kuzey Hat Lojistik A.Ş.", "KUZEY HAT LOJİSTİK ANONİM ŞİRKETİ"),
        ("Bereket Gıda Ltd. Şti.", "Bereket Gıda Limited Şirketi"),
        ("Delta Teknik Malzeme", "  Delta   Teknik Malzeme  "),
    ],
)
def test_employer_variants_normalize_equal(a, b):
    """Yazım farkı duplicate anahtarını bozmamalı (SCR-01)."""
    assert normalize_employer(a) == normalize_employer(b)


def test_distinct_employers_stay_distinct():
    assert normalize_employer("Aksu Tekstil A.Ş.") != normalize_employer("Aksu Gıda A.Ş.")


def test_turkish_letters_are_not_split_into_pieces():
    """Regresyon: NFKD "ş"yi harf+çengele ayırıp kelime sınırını bozuyordu.

    Bu test geçmiyorsa duplicate anahtarı sessizce çalışmaz hale gelir.
    """
    assert normalize_employer("Şişli Yapı A.Ş.") == "sisli yapi"
    assert " s " not in f" {normalize_employer('Anonim İnşaat Şirketi')} "


@pytest.mark.parametrize("variant", ["Bereket Gıda", "BEREKET GIDA", "Bereket Gida"])
def test_turkish_dotless_i_variants_match(variant):
    """Kaynaklar aynı ismi üç farklı şekilde yazıyor; üçü de eşleşmeli."""
    assert normalize_employer(variant) == "bereket gida"


def test_legal_form_is_only_stripped_from_the_end():
    """Ortadaki kelime hukuki forma benzese bile silinmemeli."""
    assert "ticaret" in normalize_employer("Ticaret Lisesi Vakfı İktisadi İşletmesi")


def test_title_parenthetical_is_kept():
    """Parantez içi **atılmaz** — atıldığında farklı işler birleşiyordu.

    "Software Engineer" ile "Software Engineer (New Grad)" aynı anahtara düşüp
    Geçit A tarafından tek ilana indirgeniyordu. Yanlış birleştirme gerçek bir
    ilanı kullanıcıdan tamamen gizler; kaçırılan birleştirme yalnızca iki kez
    gösterir. Asimetri bu yönde karar verdirir.
    """
    assert normalize_title("Software Engineer (New Grad)") != normalize_title(
        "Software Engineer"
    )


# --------------------------------------------------------------------------
# SCR-02 — agency kopyası, tek anahtarla yakalanamaz
# --------------------------------------------------------------------------

_TEXT = (
    "Tekstil sektöründe genel muhasebe süreçlerini yürütecek uzman. "
    "Mizan, beyanname, cari mutabakat."
)


def test_gate_a_alone_would_miss_the_agency_copy():
    """Kanıt testi: A geçidi bu çifti aynı bloğa bile sokmaz."""
    orig = normalize(_raw(source_posting_ref="o", title="Muhasebe Uzmanı",
                          employer="Aksu Tekstil A.Ş.", description=_TEXT), adapter_version=V)
    copy = normalize(_raw(source_posting_ref="c", title="Finans ve Muhasebe Uzmanı Aranıyor",
                          employer="Firma adı gizli", description=_TEXT), adapter_version=V)

    assert orig.blocking_key_a != copy.blocking_key_a, "A geçidi bu sınıfı kaçırır"
    assert orig.blocking_key_b == copy.blocking_key_b, "B geçidi aynı bloğa sokmalı"


def test_agency_copy_is_merged():
    orig = normalize(_raw(source_posting_ref="o", title="Muhasebe Uzmanı",
                          employer="Aksu Tekstil A.Ş.", description=_TEXT), adapter_version=V)
    copy = normalize(_raw(source_posting_ref="c", title="Finans ve Muhasebe Uzmanı Aranıyor",
                          employer="Firma adı gizli", description=_TEXT), adapter_version=V)

    clusters, _ = cluster([orig, copy])
    assert len(clusters) == 1, "İşveren gizlenmiş kopya ayrı ilan sayılıyor (SCR-02)"


def test_reworded_copy_is_still_merged():
    """Eşik, birebir olmayan kopyayı da yakalamalı — hash tek başına yetmez."""
    a = normalize(_raw(source_posting_ref="a", description=_TEXT), adapter_version=V)
    b = normalize(
        _raw(source_posting_ref="b", employer="Başka Firma",
             description=_TEXT + " Deneyim şarttır."),
        adapter_version=V,
    )
    assert content_similarity(a, b) >= CONTENT_SIMILARITY_THRESHOLD
    clusters, _ = cluster([a, b])
    assert len(clusters) == 1


def test_different_jobs_in_same_block_are_not_merged():
    """Aynı şehir + meslek, farklı ilan → birleşmemeli (false merge koruması)."""
    a = normalize(_raw(source_posting_ref="a", description=_TEXT), adapter_version=V)
    b = normalize(
        _raw(source_posting_ref="b", employer="Başka Firma",
             description="Bordro ve özlük işleri takibi, SGK bildirimleri, "
                         "işe giriş çıkış evrakı hazırlama."),
        adapter_version=V,
    )
    clusters, _ = cluster([a, b])
    assert len(clusters) == 2


def test_different_city_never_merges():
    a = normalize(_raw(source_posting_ref="a", city="Bursa", description=_TEXT), adapter_version=V)
    b = normalize(_raw(source_posting_ref="b", city="İzmir", description=_TEXT), adapter_version=V)
    clusters, _ = cluster([a, b])
    assert len(clusters) == 2


def test_canonical_prefers_named_employer():
    """Kullanıcıya işvereni yazan sürüm gösterilir (FR-206)."""
    orig = normalize(_raw(source_posting_ref="o", employer="Aksu Tekstil A.Ş.",
                          description=_TEXT, posted_at="2026-07-19"), adapter_version=V)
    copy = normalize(_raw(source_posting_ref="c", employer="Firma adı gizli",
                          description=_TEXT, posted_at="2026-07-20"), adapter_version=V)

    assert pick_canonical([copy, orig]).job.employer == "Aksu Tekstil A.Ş."


# --------------------------------------------------------------------------
# Uçtan uca fixture koşusu
# --------------------------------------------------------------------------


def test_fixture_ingest_runs_end_to_end():
    r = run_fixture_ingest()

    assert r["fetched"] == 8
    assert r["normalized"] == 8
    assert r["duplicates_merged"] == 1, "Agency kopyası tekilleştirilmedi"
    assert r["canonical"] == 7
    assert r["oversized_blocks"] == []


def test_provenance_is_recorded_on_every_posting():
    """Her kayıt hangi kaynaktan, hangi adapter sürümüyle geldiğini taşımalı."""
    for p in run_fixture_ingest()["postings"]:
        assert p.provenance["source_id"] == "src-fixture-001"
        assert p.provenance["adapter_version"]
        assert p.provenance["source_posting_ref"]
        assert p.url


def test_public_sector_flag_survives_ingestion():
    """D-015 bayrağı pipeline boyunca korunmalı, yoksa kamu ilanı skorlanır."""
    postings = run_fixture_ingest()["postings"]
    public = [p for p in postings if p.job.is_public_sector]
    assert len(public) == 1
    assert public[0].job.title == "Sözleşmeli Şoför Alımı"


# --------------------------------------------------------------------------
# D-024 — tazelik
# --------------------------------------------------------------------------

from datetime import date, timedelta

from isuygun_ingest.pipeline import age_in_days, is_fresh


def test_age_in_days_counts_from_publication():
    today = date(2026, 7, 21)
    assert age_in_days("2026-07-21", today=today) == 0
    assert age_in_days("2026-07-01", today=today) == 20
    assert age_in_days("2026-07-01T09:30:00Z", today=today) == 20


def test_unparseable_date_is_unknown_not_old():
    assert age_in_days(None) is None
    assert age_in_days("bilinmiyor") is None


def test_stale_posting_is_dropped():
    p = normalize(_raw(source_posting_ref="old"), adapter_version=V)
    p.posted_at = (date.today() - timedelta(days=200)).isoformat()
    assert not is_fresh(p), "200 günlük ilan gösterilmemeli"


def test_fresh_posting_is_kept():
    p = normalize(_raw(source_posting_ref="new"), adapter_version=V)
    p.posted_at = (date.today() - timedelta(days=3)).isoformat()
    assert is_fresh(p)


def test_posting_without_date_is_not_dropped():
    """Tarihi bilinmeyen ilan **elenmez**.

    "Bilmiyoruz", "eski" demek değildir — D-011'in aynı mantığı. Kaynakların bir
    kısmı yayın tarihi vermiyor; onları atmak kullanıcıdan gerçek ilan gizlerdi.
    """
    p = normalize(_raw(source_posting_ref="nodate"), adapter_version=V)
    p.posted_at = None
    assert is_fresh(p)


# --------------------------------------------------------------------------
# D-023 — public API kaynakları
# --------------------------------------------------------------------------


def test_api_sources_are_registered_with_policy():
    """Her API kaynağı kendi kullanım şartlarını **taşımak zorunda**."""
    srcs = registry.api_sources()
    assert srcs, "kayıtlı API kaynağı yok"
    for r in srcs:
        assert r.permission_evidence.strip(), r.source_id
        assert r.min_poll_hours > 0, r.source_id
        assert r.redistribution_policy, r.source_id


def test_attribution_required_sources_are_marked():
    """Atıf isteyen kaynaklar işaretli olmalı; arayüz buna göre davranır."""
    by_id = {r.source_id: r for r in registry.api_sources()}
    for sid in ("src-api-themuse", "src-api-arbeitnow", "src-api-himalayas"):
        assert by_id[sid].attribution_required is True, sid


def test_every_api_source_has_a_fetcher():
    from isuygun_ingest.adapters.public_apis import FETCHERS

    for r in registry.api_sources():
        assert r.source_id in FETCHERS, r.source_id


# ---------------------------------------------------------------------------
# Yaş vs canlılık ayrımı (D-035)
# ---------------------------------------------------------------------------


def _posting(posted_at, refreshed_at):
    from isuygun_ingest.pipeline import RawPosting, normalize

    return normalize(RawPosting(
        source_id="src-fixture-001", source_posting_ref="r",
        url="https://e.invalid/x", title="Engineer", employer="Acme",
        city="Berlin", description="Some role.",
        posted_at=posted_at, refreshed_at=refreshed_at,
    ), adapter_version="test")


def test_old_posting_kept_alive_by_refresh_is_not_dropped():
    """96 gündür açık ama dün güncellenmiş ilan **elenmez**.

    ATS onu hâlâ listeliyor, yani açık. Elemek, açık olduğunu bildiğimiz bir
    fırsatı gizlemek olurdu.
    """
    from datetime import date, timedelta
    from isuygun_ingest.pipeline import is_fresh

    today = date.today()
    p = _posting(str(today - timedelta(days=96)), str(today - timedelta(days=1)))
    assert is_fresh(p)


def test_true_age_is_reported_not_the_refresh_date():
    """Yaş gerçek yayın tarihinden okunur — asıl düzeltilen hata buydu."""
    from datetime import date, timedelta
    from isuygun_ingest.pipeline import days_open

    today = date.today()
    p = _posting(str(today - timedelta(days=96)), str(today - timedelta(days=1)))
    assert days_open(p) == 96, "yaş güncelleme tarihinden okunuyor — ilan taze görünür"


def test_abandoned_posting_is_dropped():
    """Uzun süredir dokunulmamış ilan elenir: canlılık sinyali yok."""
    from datetime import date, timedelta
    from isuygun_ingest.pipeline import is_fresh

    today = date.today()
    p = _posting(str(today - timedelta(days=200)), str(today - timedelta(days=180)))
    assert not is_fresh(p)


def test_unknown_dates_still_survive():
    """D-024 korunur: tarihi bilinmeyen ilan elenmez."""
    from isuygun_ingest.pipeline import is_fresh

    assert is_fresh(_posting(None, None))


# ---------------------------------------------------------------------------
# Bölüm başlığı tespiti (D-044)
# ---------------------------------------------------------------------------


def test_benefit_word_mid_sentence_does_not_kill_requirements():
    """"benefits" cümle içinde geçince sonraki şartlar atılmamalı.

    Gerçek korpustan: "ability to use consultative, benefits based selling…"
    Bu bir satış tekniği, yan haklar bölümü değil. Desen çıplak kelimeyi
    yakalayınca o noktadan **sonraki her şey** eleniyordu ve tek bir kelime
    bütün ilanı sakatlıyordu (624 ilan şartsız kalmıştı).
    """
    from isuygun_ingest.extract import extract_requirements

    reqs = extract_requirements(
        "Account Executive",
        "## Responsibilities\n"
        "Use consultative, benefits based selling with partners.\n"
        "Experience with Salesforce is required.",
    )
    assert any(r.key == "crm" for r in reqs), [r.key for r in reqs]


def test_real_benefit_heading_still_excludes_requirements():
    """Gerçek yan-haklar **başlığı** altındakiler şart sayılmamalı — bu koruma
    kaybedilmemeli (ilanın istemediği şeyi istiyormuş gibi göstermek)."""
    from isuygun_ingest.extract import extract_requirements

    reqs = extract_requirements(
        "Developer",
        "## Requirements\nPython experience needed.\n\n"
        "## What We Offer\nEnglish courses and Excel training.",
    )
    keys = {r.key for r in reqs}
    assert "python" in keys
    assert "english" not in keys and "excel" not in keys, keys


def test_section_markers_require_heading_position():
    """Bölüm işaretleri satır başında (opsiyonel #/-/* ile) aranır."""
    from isuygun_ingest.extract import _BENEFIT_SECTION

    assert _BENEFIT_SECTION.search("## What We Offer\nfoo")
    assert _BENEFIT_SECTION.search("- Benefits\nfoo")
    assert not _BENEFIT_SECTION.search("we use benefits based selling daily")
