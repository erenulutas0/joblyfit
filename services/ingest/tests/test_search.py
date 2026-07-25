"""İlan metni araması ve operatörleri."""

from __future__ import annotations

from isuygun_ingest import search


def _doc(blob: str, title: str = "") -> search.Doc:
    """Test torbasi. `blob` zaten katlanmis varsayilir (testler oyle yaziyor)."""
    return search.Doc(blob=blob, title=title or blob)


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
    assert search.matches(_doc(hay), search.parse("python developer"))
    assert not search.matches(_doc(hay), search.parse("python rust"))


def test_phrase_must_be_contiguous():
    hay = "we need a data engineer and a product analyst"
    assert search.matches(_doc(hay), search.parse('"data engineer"'))
    assert not search.matches(_doc(hay), search.parse('"engineer data"'))


def test_exclusion_removes_match():
    hay = "junior python developer internship"
    assert search.matches(_doc(hay), search.parse("python"))
    assert not search.matches(_doc(hay), search.parse("python -internship"))


def test_exclusion_beats_inclusion():
    """Dışlama, dahil etmeyi ezer. Kullanıcı "-stajyer" yazdıysa niyeti nettir."""
    hay = "stajyer python developer"
    assert not search.matches(_doc(hay), search.parse("stajyer -stajyer"))


def test_turkish_folding_both_ways():
    """Türkçe yazan kullanıcı aksansız da arayabilir, aksanlı da."""
    hay = search.fold("Yazılım Mühendisi — İstanbul")
    for q in ("yazilim", "yazılım", "muhendis", "mühendis", "istanbul", "İstanbul"):
        assert search.matches(_doc(hay), search.parse(q)), q


def test_haystack_includes_description():
    """Asıl sebep bu: "forklift" sözlükte yok ama ilan metninde geçiyor."""
    from isuygun_ingest.pipeline import RawPosting, normalize

    p = normalize(RawPosting(
        source_id="src-fixture-001", source_posting_ref="r",
        url="https://example.invalid/x", title="Depo Görevlisi",
        employer="Acme", city="İzmir",
        description="Forklift operatörü belgesi olan adaylar tercih edilir.",
    ), adapter_version="test")
    hay = search.haystack(p)          # zaten Doc — _doc ile sarılmaz
    assert search.matches(hay, search.parse("forklift"))
    assert search.matches(hay, search.parse("depo"))
    assert not search.matches(hay, search.parse("kaynakçı"))
    # Başlıkta "depo" var, "forklift" yok: sıralama ikisini ayırt etmeli.
    assert search.title_matches(hay, search.parse("depo"))
    assert not search.title_matches(hay, search.parse("forklift"))


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


# ---------------------------------------------------------------------------
# Kelime sınırı + Türkçe ek toleransı (canlı persona testinden)
# ---------------------------------------------------------------------------
# Ölçümler (4.211 TR ilanı):
#   "kaynakçılık"      -> 0 sonuç   (uygulamanın KENDİ chip etiketi!)
#   "insan kaynakları" -> 259 sonuç, ilk 100'ünün HİÇBİRİNİN başlığında yok
#   "yazılım"          -> 129 sonuç, yalnızca 11'i başlıkta


def test_query_with_turkish_suffix_finds_the_stem():
    """Uygulamanın kendi kelimesini yazan kullanıcı sonuç almalı.

    Chip "Kaynakçılık" diyor, ilanlar "Kaynakçı" yazıyor. Eşleştirme motoru
    eklemeli yapıyı çözüyordu, arama kutusu çözmüyordu.
    """
    hay = _doc(search.fold("Gazaltı Kaynakçı aranıyor"))
    assert search.matches(hay, search.parse("kaynakçı"))
    assert search.matches(hay, search.parse("kaynakçılık")), \
        "ek soyulmadı — kullanıcı uygulamanın kendi kelimesiyle 0 sonuç alır"


def test_suffix_stripping_does_not_reach_dangerous_stems():
    """"kaynakçılık" -> "kaynakçı" olur, "kaynak" OLMAZ.

    Türkçe'de "kaynak" hem *welding* hem *resource*: gövde oraya kadar
    kısaltılırsa her kaynakçı araması "İnsan Kaynakları" ilanlarını getirir.
    """
    ik = _doc(search.fold("İnsan Kaynakları Yöneticisi"))
    assert not search.matches(ik, search.parse("kaynakçılık"))
    assert not search.matches(ik, search.parse("kaynakçı"))


def test_terms_match_at_word_start_only():
    """Düz substring araması kelime ORTASINA tutuyordu: "SAP" -> "hesaplama"."""
    hay = _doc(search.fold("Ön muhasebe ve hesaplama işleri"))
    assert not search.matches(hay, search.parse("sap")), \
        "kelime ortası eşleşmesi: 'sap' 'hesaplama' içinde bulundu"
    assert search.matches(hay, search.parse("muhasebe"))
    # Sonda sınır YOK — Türkçe eklemeli, "muhasebe" "muhasebeci"yi de bulmalı.
    assert search.matches(_doc(search.fold("Muhasebeci aranıyor")),
                          search.parse("muhasebe"))


def test_exclusion_also_respects_word_start():
    """"-sap" yazan kullanıcı "hesaplama" geçen ilanları kaybetmemeli."""
    hay = _doc(search.fold("Ön muhasebe, hesaplama bilgisi"))
    assert search.matches(hay, search.parse("muhasebe -sap"))


def test_title_hit_is_distinguishable_from_body_hit():
    """Sıralamanın dayanağı: aradığın şeyin KENDİSİ mi, ondan söz eden ilan mı."""
    q = search.parse("kaynakçı")
    baslikta = search.Doc(blob=search.fold("Kaynakçı aranıyor. Fabrikada..."),
                          title=search.fold("Kaynakçı"))
    govdede = search.Doc(
        blob=search.fold("Garson aranıyor. Kaynakçı ekibiyle çalışılacak."),
        title=search.fold("Garson"))
    assert search.matches(baslikta, q) and search.matches(govdede, q)
    assert search.title_matches(baslikta, q)
    assert not search.title_matches(govdede, q)


def test_title_match_ignores_exclusion():
    """Dışlama tüm metinde bir kez uygulandı; başlık kontrolü sıralama içindir.

    `title_matches` dışlamaya bakarsa, gövdesinde dışlanan kelime geçen bir
    ilan başlık isabetini kaybeder ve alakasızların arkasına düşer.
    """
    d = search.Doc(blob=search.fold("Kaynakçı aranıyor. Stajyer alınmaz."),
                   title=search.fold("Kaynakçı"))
    assert search.title_matches(d, search.parse("kaynakçı -stajyer"))


def test_cheap_prefilter_is_a_prefix_of_every_variant():
    """Ön süzgecin GÜVENLİ olmasının koşulu: en kısa gövde diğerlerinin ön eki.

    `_Term.hits` metinde `needle` yoksa regex'i hiç çalıştırmadan reddeder. Bu
    ancak needle bütün varyantların ön ekiyse doğrudur; değilse arama sessizce
    ilan kaybetmeye başlar — ve hiçbir test kırılmaz.

    Ölçüm neden zorunlu kıldı: yalnızca regex 17.858 ilanda sorgu başına
    1470–1714 ms sürüyordu, düz `in` ise 30–49 ms. Ön süzgeç 36–55 ms'e indirdi.
    """
    for term in ("kaynakcilik", "muhasebe", "belgeleri", "temizlikci",
                 "isciligi", "sap", "c++"):
        t = search._pattern(term)
        for varyant in search._stems(term):
            assert varyant.startswith(t.needle), (
                f"{term!r}: needle {t.needle!r} varyant {varyant!r} icin on ek "
                f"degil — ucuz reddetme ilan kaybettirir"
            )


def test_prefilter_does_not_change_results():
    """Ön süzgeç yalnızca hız içindir; sonuç kümesi regex'in kendisiyle aynı olmalı."""
    metinler = [
        "gazalti kaynakci aranıyor",
        "insan kaynaklari yoneticisi",
        "on muhasebe ve hesaplama",
        "sap danismani",
        "kaynakcilik egitimi verilir",
    ]
    for q in ("kaynakci", "kaynakcilik", "sap", "muhasebe", "kaynak"):
        parsed = search.parse(q)
        for m in metinler:
            hizli = search.matches(_doc(m), parsed)
            # Ön süzgeci atlayan referans: yalnızca regex.
            yavas = all(t.rx.search(m) for t in parsed.term_res)
            assert hizli == yavas, f"{q!r} / {m!r}: on suzgec sonucu degistirdi"
