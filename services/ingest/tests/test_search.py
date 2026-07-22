"""İlan metni araması ve operatörleri."""

from __future__ import annotations

from isuygun_ingest import search


def test_parses_plain_terms():
    q = search.parse("muhasebe uzmanı")
    assert q.terms == ("muhasebe", "uzmani")   # katlanmış
    assert not q.phrases and not q.excluded


def test_parses_phrase():
    q = search.parse('"ön muhasebe" istanbul')
    assert q.phrases == ("on muhasebe",)
    assert q.terms == ("istanbul",)


def test_parses_exclusion():
    q = search.parse("mühendis -stajyer -satış")
    assert q.terms == ("muhendis",)
    assert q.excluded == ("stajyer", "satis")


def test_empty_query_is_empty():
    assert search.parse("").is_empty
    assert search.parse("   ").is_empty


def test_all_terms_must_match():
    hay = "senior python developer at acme"
    assert search.matches(hay, search.parse("python developer"))
    assert not search.matches(hay, search.parse("python rust"))


def test_phrase_must_be_contiguous():
    hay = "we need a data engineer and a product analyst"
    assert search.matches(hay, search.parse('"data engineer"'))
    assert not search.matches(hay, search.parse('"engineer data"'))


def test_exclusion_removes_match():
    hay = "junior python developer internship"
    assert search.matches(hay, search.parse("python"))
    assert not search.matches(hay, search.parse("python -internship"))


def test_exclusion_beats_inclusion():
    """Dışlama, dahil etmeyi ezer. Kullanıcı "-stajyer" yazdıysa niyeti nettir."""
    hay = "stajyer python developer"
    assert not search.matches(hay, search.parse("stajyer -stajyer"))


def test_turkish_folding_both_ways():
    """Türkçe yazan kullanıcı aksansız da arayabilir, aksanlı da."""
    hay = search.fold("Yazılım Mühendisi — İstanbul")
    for q in ("yazilim", "yazılım", "muhendis", "mühendis", "istanbul", "İstanbul"):
        assert search.matches(hay, search.parse(q)), q


def test_haystack_includes_description():
    """Asıl sebep bu: "forklift" sözlükte yok ama ilan metninde geçiyor."""
    from isuygun_ingest.pipeline import RawPosting, normalize

    p = normalize(RawPosting(
        source_id="src-fixture-001", source_posting_ref="r",
        url="https://example.invalid/x", title="Depo Görevlisi",
        employer="Acme", city="İzmir",
        description="Forklift operatörü belgesi olan adaylar tercih edilir.",
    ), adapter_version="test")
    hay = search.haystack(p)
    assert search.matches(hay, search.parse("forklift"))
    assert search.matches(hay, search.parse("depo"))
    assert not search.matches(hay, search.parse("kaynakçı"))


def test_long_descriptions_are_capped():
    """İlanların kuyruğu hukuki metin; oraya kadar aramak alakasız eşleşme
    üretir ve her istekte bedeli ödenir."""
    from isuygun_ingest.pipeline import RawPosting, normalize

    filler = "lorem ipsum " * 2000
    p = normalize(RawPosting(
        source_id="src-fixture-001", source_posting_ref="r",
        url="https://example.invalid/x", title="Engineer", employer="Acme",
        city="Berlin", description=filler + " NEEDLEWORD",
    ), adapter_version="test")
    assert not search.matches(search.haystack(p), search.parse("needleword"))
