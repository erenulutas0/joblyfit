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
        occupation_id="account",
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
