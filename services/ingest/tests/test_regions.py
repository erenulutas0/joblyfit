"""Bölge sınıflandırma testleri.

Buradaki vakaların çoğu **gerçek ilan konumlarından** alınmıştır ve her biri
bir kez yanlış sınıflandırılmıştır. Şehir adları ülkeler arasında tekrar ettiği
için bu modül sessizce yanlış çalışmaya elverişlidir: kullanıcı "Avrupa" filtresi
seçer, ABD ilanı görür ve nedenini anlamaz.
"""

from __future__ import annotations

import pytest

from isuygun_ingest import regions as R


@pytest.mark.parametrize("loc,expected", [
    ("Istanbul / Maslak", {R.TR}),
    ("İstanbul, Türkiye", {R.TR}),
    ("Kocaeli", {R.TR}),
    ("Berlin, Berlin, Germany", {R.EU}),
    ("Paris, France", {R.EU}),
    ("London", {R.EU}),
    ("Warszawa, Masovian Voivodeship, Poland", {R.EU}),
    ("New York, NY, United States", {R.US}),
    ("San Francisco", {R.US}),
    ("Austin, TX", {R.US}),
    ("Tokyo, Japan", {R.OTHER}),
    ("Toronto, Ontario, Canada", {R.OTHER}),
    ("Sao Paulo, Brazil", {R.OTHER}),
    ("", {R.OTHER}),
    ("N/A", {R.OTHER}),
])
def test_basic_classification(loc, expected):
    assert R.classify(loc) == expected


# --------------------------------------------------------------------------
# Bir kez yanlış çıkmış vakalar — regresyon koruması
# --------------------------------------------------------------------------


def test_country_beats_city_name():
    """"Vienna, VA, United States" hem ABD hem Avrupa sayılıyordu.

    Şehir adları ülkeler arasında tekrar eder (Vienna: Avusturya ve Virginia).
    Ülke adı varsa şehir tahminine hiç bakılmaz.
    """
    assert R.classify("Vienna, VA, United States") == {R.US}
    assert R.classify("Vienna, Austria") == {R.EU}


def test_us_state_code_is_recognised():
    """"Reading, PA" Avrupa sayılıyordu — Reading aynı zamanda bir İngiliz şehri."""
    assert R.classify("Reading, PA") == {R.US}
    assert R.classify("Cambridge, MA") == {R.US}


def test_ambiguous_state_codes_are_not_used():
    """IN/OR/OK/ME gibi kodlar normal kelimedir; kullanılmamalı.

    "Portland, OR" doğru sonucu **şehir adından** almalı, kısaltmadan değil;
    böylece "Berlin, Germany or Remote" gibi metinler ABD sanılmaz.
    """
    assert R.US not in R.classify("Berlin, Germany or Remote")
    assert R.US not in R.classify("Madrid, Spain in office")


def test_america_substring_does_not_imply_us():
    """"South America" ABD sayılıyordu — "america" hecesi eşleşiyordu."""
    assert R.classify("South America") == {R.OTHER}
    assert R.classify("Latin America") == {R.OTHER}


def test_us_and_uk_only_match_as_whole_words():
    """"us" hecesi belarus/russia içinde, "uk" hecesi ukraine içinde geçiyor."""
    assert R.US not in R.classify("Belarus")
    assert R.US not in R.classify("Russia")
    assert R.EU not in R.classify("Ukraine")
    assert R.classify("Remote — US only") == {R.US, R.REMOTE}


def test_remote_is_orthogonal_to_geography():
    """Uzaktan çalışma bir coğrafya değildir; coğrafyayla birlikte işaretlenir."""
    assert R.classify("Remote (UK)") == {R.EU, R.REMOTE}
    assert R.classify("Cardiff, London or Remote (UK)") == {R.EU, R.REMOTE}
    assert R.classify("Remote") == {R.REMOTE}


def test_primary_prefers_geography_over_remote():
    assert R.primary("Remote (UK)") == R.EU
    assert R.primary("Remote") == R.REMOTE
    assert R.primary("Tokyo, Japan") == R.OTHER


def test_unknown_location_is_other_not_a_guess():
    """Tanınmayan konuma uydurma bölge atanmaz."""
    assert R.classify("Atlantis") == {R.OTHER}
    assert R.classify("???") == {R.OTHER}


def test_all_regions_are_reachable():
    """`ALL` listesindeki her bölge gerçekten üretilebilmeli."""
    produced = set()
    for loc in ("Istanbul", "Berlin, Germany", "Austin, TX", "Remote", "Tokyo, Japan"):
        produced |= R.classify(loc)
    assert produced == set(R.ALL)


def test_classify_result_is_isolated_per_caller():
    """Önbellek (D-054) paylaşılan bir küme döndürmemeli.

    `classify` sonuçları lru_cache'te tutulur. Aynı küme nesnesi çağıranlara
    verilirse, bir yerde yapılan `add`/`discard` bütün ilanların bölgesini
    sessizce değiştirir — 1502 ilan "İstanbul" dizesini paylaşıyor.
    """
    a = R.classify("Istanbul")
    b = R.classify("Istanbul")
    assert a == b
    assert a is not b, "her çağıran kendi kümesini almalı"

    a.add("UYDURMA")
    assert "UYDURMA" not in R.classify("Istanbul"), "mutasyon önbelleğe sızmamalı"


def test_classify_cache_does_not_change_results():
    """Önbellek bir optimizasyondur; sonucu değiştirmemeli.

    Aynı girdiler önbellek dolu ve boşken aynı sonucu vermeli.
    """
    ornekler = ["Istanbul", "Berlin, Germany", "Austin, TX", "Remote",
                "Tokyo, Japan", "", "   ", "Vienna, VA, United States",
                "Cardiff, London or Remote (UK)", "İzmir / Bornova"]
    once = {loc: R.classify(loc) for loc in ornekler}
    R._classify_cached.cache_clear()
    sonra = {loc: R.classify(loc) for loc in ornekler}
    assert once == sonra
