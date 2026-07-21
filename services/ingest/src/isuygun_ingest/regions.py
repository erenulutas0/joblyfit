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
    """
    s = fold(location or "")
    if not s.strip():
        return {OTHER}

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

    return out or {OTHER}


def _tokens(folded: str) -> list[str]:
    return re.findall(r"[a-z]+", folded)


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
