"""Bölge sınıflandırma — **politika katmanı**, core değil.

D-009: pazara özgü hiçbir şey core architecture varsayımı yapılmaz. Bu modül
bilinçli olarak ``isuygun_core``'un dışındadır ve matching mantığına girmez;
yalnızca feed'i gruplamak ve filtrelemek için kullanılır.

Sınıflandırma **kesin değildir**. İlan konumları serbest metindir ("London",
"Berlin, Berlin, Germany", "Cardiff, London or Remote (UK)"), bu yüzden bir ilan
birden fazla bölgeye düşebilir ve hiçbirine düşmeyebilir. Eşleşme bulunamazsa
:data:`OTHER` döner — uydurma bir bölge atanmaz.
"""

from __future__ import annotations

import re
from functools import lru_cache

from .pipeline import fold

TR = "Türkiye"
EU = "Avrupa"
US = "ABD"
REMOTE = "Uzaktan"
OTHER = "Diğer"

ALL = (TR, EU, US, REMOTE, OTHER)

# Sinyaller iki güçte tutulur.
#
# **Ülke adı şehir adını ezer.** Şehir adları ülkeler arasında tekrar eder:
# Vienna hem Avusturya'da hem Virginia'da, Reading hem İngiltere'de hem
# Pennsylvania'da vardır. Hepsini eşit ağırlıkta aramak "Vienna, VA, United
# States" ilanını hem ABD hem Avrupa yapıyordu. Bu yüzden önce ülke/bölge
# işaretleri aranır; biri tutarsa şehir tahminlerine hiç bakılmaz.

_TR_COUNTRY = ("turkiye", "turkey")
_TR_CITY = (
    "istanbul", "ankara", "izmir", "bursa", "antalya",
    "kocaeli", "adana", "konya", "gaziantep", "eskisehir", "kayseri", "samsun",
    "denizli", "mersin", "sakarya", "tekirdag", "trabzon", "maslak", "atasehir",
)

_EU_COUNTRY = (
    "united kingdom", "germany", "france", "spain", "italy", "netherlands",
    "ireland", "poland", "portugal", "sweden", "denmark", "norway", "finland",
    "switzerland", "belgium", "austria", "czech", "czechia", "hungary", "greece",
    "romania", "bulgaria", "croatia", "slovenia", "slovakia", "estonia",
    "latvia", "lithuania", "luxembourg", "cyprus", "malta", "iceland",
    "england", "scotland", "wales", "europe", "emea", "deutschland",
)

_EU_CITY = (
    "london", "berlin", "munich", "munchen", "hamburg", "frankfurt", "cologne",
    "koln", "dusseldorf", "stuttgart", "leipzig", "dresden", "magdeburg",
    "amsterdam", "rotterdam", "utrecht", "eindhoven", "the hague", "den haag",
    "paris", "lyon", "marseille", "toulouse", "bordeaux", "lille", "nantes",
    "madrid", "barcelona", "valencia", "sevilla", "bilbao", "malaga",
    "milan", "milano", "rome", "roma", "turin", "torino", "bologna", "naples",
    "dublin", "cork", "lisbon", "lisboa", "porto", "warsaw", "warszawa",
    "krakow", "wroclaw", "gdansk", "poznan", "prague", "praha", "brno",
    "vienna", "wien", "graz", "stockholm", "gothenburg", "malmo",
    "copenhagen", "kobenhavn", "aarhus", "oslo", "bergen", "helsinki", "espoo",
    "zurich", "geneva", "geneve", "basel", "lausanne", "bern",
    "brussels", "bruxelles", "antwerp", "ghent", "budapest", "athens", "athina",
    "thessaloniki", "bucharest", "bucuresti", "cluj", "sofia", "zagreb",
    "ljubljana", "bratislava", "tallinn", "riga", "vilnius", "nicosia",
    "edinburgh", "manchester", "cambridge", "oxford", "cardiff", "glasgow",
    "bristol", "leeds", "birmingham", "belfast", "sheffield", "derby",
    "milton keynes", "reading", "brighton",
)

_US_COUNTRY = ("united states", "usa", "u.s.a", "u.s.")

_US_CITY = (
    "san francisco", "new york", "nyc", "brooklyn", "seattle", "austin",
    "boston", "chicago", "los angeles", "denver", "atlanta", "miami", "dallas",
    "houston", "portland", "san diego", "san jose", "palo alto", "mountain view",
    "sunnyvale", "cupertino", "menlo park", "washington", "philadelphia",
    "phoenix", "minneapolis", "detroit", "nashville", "charlotte", "raleigh",
    "durham", "salt lake", "las vegas", "san antonio", "columbus", "pittsburgh",
    "kansas city", "st. louis", "orlando", "tampa", "sacramento", "bellevue",
    "redmond", "boulder", "ann arbor", "madison", "irvine", "santa monica",
    "aurora, il", "california", "texas", "florida", "colorado", "illinois",
    "massachusetts", "washington, dc", "new jersey", "virginia",
)

_REMOTE = ("remote", "anywhere", "distributed", "work from home", "wfh", "hybrid/remote")

# Kısaltmalar yalnızca **tam kelime** olarak kabul edilir: "us" hecesi
# russia/belarus/austin içinde, "uk" hecesi ukraine içinde geçiyor.
# "america" bilinçli olarak listede YOK — "South America" ilanını ABD yapıyordu.
_US_TOKENS = {"us", "usa"}
_EU_TOKENS = {"uk", "eu"}

# ABD eyalet kısaltmaları — yalnızca virgülden sonra ve **belirsiz olmayanlar**.
# Kasıtlı olarak dışarıda bırakılanlar: IN, OR, OK, ME, HI, DE, ID, LA, MS, MT,
# AL, AR, CA — hepsi İngilizce/Almanca/Türkçe bir kelime ya da ülke kısaltması
# ("CA" Kanada sanılabilir). Kapsamı dar tutmak, yanlış sınıflandırmadan iyidir.
_US_STATE_CODE = re.compile(
    r",\s*(pa|tx|ny|il|ma|wa|ga|nc|sc|va|md|mn|mi|mo|nj|nv|az|co|ct|ut|wi|ks|ky|"
    r"ne|nh|nm|ri|sd|nd|tn|vt|wv|wy|ak|ia|oh|fl)\b"
)


def classify(location: str) -> set[str]:
    """Konum metnini bölge kümesine çevirir.

    Bir ilan birden fazla bölgeye ait olabilir: "Cardiff, London or Remote (UK)"
    hem :data:`EU` hem :data:`REMOTE`'tur. Hiçbiri tutmuyorsa :data:`OTHER`.

    Uzaktan çalışma coğrafyadan bağımsızdır ve her zaman ayrıca işaretlenir.

    Sonuç **önbelleklenir** (D-054): bu saf bir metin→küme dönüşümüdür ve konum
    dizeleri korpusta yoğun tekrar eder ("İstanbul" 1502 ilanda). Ölçümde
    ``/api/feed`` her istekte bunu 10385 kez çağırıyordu ve ``fold`` + regex
    maliyeti gecikmenin büyük kısmıydı.

    Çağırana **kopya** döner: önbellek tek bir küme nesnesi tutar, onu paylaşmak
    bir çağıranın mutasyonunu bütün ilanlara yayardı.
    """
    return set(_classify_cached(location or ""))


@lru_cache(maxsize=8192)
def _classify_cached(location: str) -> frozenset[str]:
    s = fold(location)
    if not s.strip():
        return frozenset({OTHER})

    words = set(_tokens(s))
    out: set[str] = set()

    # 1) Güçlü sinyal: ülke / bölge adı.
    if any(m in s for m in _TR_COUNTRY):
        out.add(TR)
    if any(m in s for m in _EU_COUNTRY) or (_EU_TOKENS & words):
        out.add(EU)
    if (any(m in s for m in _US_COUNTRY) or (_US_TOKENS & words)
            or _US_STATE_CODE.search(s)):
        out.add(US)

    # 2) Ülke bulunamadıysa şehir adına düşülür. Ülke varken şehre bakmak,
    #    "Vienna, VA, United States" gibi ilanları iki bölgeye birden sokar.
    if not out:
        if any(m in s for m in _TR_CITY):
            out.add(TR)
        if any(m in s for m in _EU_CITY):
            out.add(EU)
        if any(m in s for m in _US_CITY):
            out.add(US)

    if any(m in s for m in _REMOTE):
        out.add(REMOTE)

    return frozenset(out or {OTHER})


def _tokens(folded: str) -> list[str]:
    return re.findall(r"[a-z]+", folded)


# ---------------------------------------------------------------------------
# Şehir grubu (D-056)
# ---------------------------------------------------------------------------

#: Büyükşehir yaka/bölge ekleri. Kaynaklar İstanbul'u üçe bölüyor
#: ("İstanbul", "İstanbul Avrupa", "İstanbul Anadolu") ve bunlar **aynı ildir**.
_SIDE_WORDS = frozenset({"avrupa", "anadolu", "asya", "yakasi", "avrupasi"})

#: Şehir yerine geçen ama şehir OLMAYAN değerler. "Türkiye" yazan 137 ilan
#: şehir söylemiyor; onları "İstanbul"la aynı listeye koymak yanlış olurdu.
_NOT_A_CITY = frozenset(
    set(_TR_COUNTRY) | set(_EU_COUNTRY) | set(_US_COUNTRY)
    | {"remote", "uzaktan", "anywhere", "hybrid", "onsite", "global",
       "worldwide", "emea", "europe", "avrupa"}
)


#: Ülke adlarının tek tek kelimeleri ("united kingdom" → united, kingdom).
#: Şehir adının sonuna yapışan ülke ekini atmak için.
_COUNTRY_TOKENS = frozenset(
    w
    for name in (*_TR_COUNTRY, *_EU_COUNTRY, *_US_COUNTRY)
    for w in name.split()
) - {"york", "jersey"}   # "New York" / "New Jersey" şehirdir, ülke eki değil


def city_of(location: str) -> tuple[str, str]:
    """Konumdan **il/şehir** çıkarır: ``(gruplama anahtarı, gösterim adı)``.

    Ham konum dizesiyle filtre yapılamaz: aynı il beş ayrı yazımla geliyor ve
    her biri ayrı bir seçenek gibi görünüyor. Ölçüm (canlı korpus, 4284 TR
    ilanı, 166 farklı dize): İstanbul ``İstanbul`` 938 + ``İstanbul Avrupa``
    538 + ``İstanbul Anadolu`` 403 + ``İstanbul, Kadıköy``… şeklinde
    parçalanmıştı. "İstanbul (938)" yazan bir filtre, ilin gerçek 2000+
    ilanının çoğunu gizlerdi — rozetteki sayının tutmaması bu kod tabanının
    zaten reddettiği şey (bkz. facet sayımı).

    Kural: ilk segment (virgül/eğik çizgi/parantez öncesi) + yaka eki atılır.
    Ülke/uzaktan gibi şehir olmayan değerler ``("", "")`` döner — bunlar
    "belirtilmemiş"tir ve uydurulmaz (D-011).
    """
    raw = (location or "").strip()
    if not raw:
        return "", ""
    # Ayırıcılar: virgül/eğik çizgi/parantez + uzun tire ve **boşluklu** kısa
    # tire. Boşluk şart: "Baden-Württemberg" ve "Saint-Denis" gerçek şehir
    # adlarıdır, bölünmemeli. Uzun tire ayrımı olmadan "Remote — United States"
    # bir şehir grubu gibi listeleniyordu (ölçümde 98 ilan).
    seg = re.split(r"[,/|()–—]|\s-\s", raw)[0].strip()
    if not seg:
        return "", ""

    words = seg.split()
    folded = _classify_fold(seg).split()
    # İlk kelime "remote/uzaktan" ise bu bir şehir değil, çalışma biçimidir.
    # ("Remote US", "Uzaktan Türkiye" → şehir belirtilmemiş.)
    if folded and folded[0] in _NOT_A_CITY:
        return "", ""
    # Sondaki yaka ve ülke eklerini at:
    #   "İstanbul Avrupa"            → "İstanbul"
    #   "München Bayern Deutschland" → "München Bayern"
    # İkincisi Alman iş ajansından geliyor ve **ayırıcı içermiyor**; ülke ekini
    # atmazsak "München" ile ayrı iki şehir grubu olarak listeleniyor.
    while len(folded) > 1 and (folded[-1] in _SIDE_WORDS
                               or folded[-1] in _COUNTRY_TOKENS):
        folded.pop()
        words = words[:len(folded)]

    key = " ".join(folded)
    # Geriye yalnızca ülke kelimeleri kaldıysa bu bir şehir değildir:
    # "United States" → sondaki "states" atılınca "united" kalıyordu ve
    # ekranda "United" diye bir şehir görünüyordu.
    if (not key or key in _NOT_A_CITY
            or all(t in _COUNTRY_TOKENS for t in folded)):
        return "", ""
    return key, " ".join(words[:len(folded)])


def _classify_fold(s: str) -> str:
    return fold(s)


def primary(location: str) -> str:
    """Tek bir bölge etiketi gerektiğinde kullanılır (gruplama için).

    Uzaktan çalışma tek başına bir coğrafya değildir; coğrafi bir işaret varsa
    o tercih edilir.
    """
    r = classify(location)
    for candidate in (TR, EU, US):
        if candidate in r:
            return candidate
    return REMOTE if REMOTE in r else OTHER
