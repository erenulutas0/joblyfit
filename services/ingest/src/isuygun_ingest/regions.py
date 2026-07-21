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

from .pipeline import fold

TR = "Türkiye"
EU = "Avrupa"
US = "ABD"
REMOTE = "Uzaktan"
OTHER = "Diğer"

ALL = (TR, EU, US, REMOTE, OTHER)

_TR = (
    "turkiye", "turkey", "istanbul", "ankara", "izmir", "bursa", "antalya",
    "kocaeli", "adana", "konya", "gaziantep", "eskisehir", "kayseri", "samsun",
    "denizli", "mersin", "sakarya", "tekirdag", "trabzon", "maslak", "atasehir",
)

_EU = (
    # ülkeler / bölgeler
    "united kingdom", "germany", "france", "spain", "italy", "netherlands",
    "ireland", "poland", "portugal", "sweden", "denmark", "norway", "finland",
    "switzerland", "belgium", "austria", "czech", "czechia", "hungary", "greece",
    "romania", "bulgaria", "croatia", "slovenia", "slovakia", "estonia",
    "latvia", "lithuania", "luxembourg", "cyprus", "malta", "iceland",
    "england", "scotland", "wales", "europe", "emea", "deutschland",
    # şehirler
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

_US = (
    "united states", "usa", "u.s.", "u.s.a", "america",
    "san francisco", "new york", "nyc", "brooklyn", "seattle", "austin",
    "boston", "chicago", "los angeles", "denver", "atlanta", "miami", "dallas",
    "houston", "portland", "san diego", "san jose", "palo alto", "mountain view",
    "sunnyvale", "cupertino", "menlo park", "washington", "philadelphia",
    "phoenix", "minneapolis", "detroit", "nashville", "charlotte", "raleigh",
    "durham", "salt lake", "las vegas", "san antonio", "columbus", "pittsburgh",
    "kansas city", "st. louis", "orlando", "tampa", "sacramento", "bellevue",
    "redmond", "boulder", "ann arbor", "madison", "irvine", "santa monica",
    "aurora, il", "california", "texas", "florida", "colorado", "illinois",
    "massachusetts", "washington, dc", "new jersey", "virginia", "georgia, us",
)

_REMOTE = ("remote", "anywhere", "distributed", "work from home", "wfh", "hybrid/remote")

# "US" tek başına bir konum olarak geçiyor ama "us" hecesi başka kelimelerin
# içinde de var (russia, belarus, austin…). Yalnızca tam kelime kabul edilir.
_US_TOKENS = {"us", "usa"}


def classify(location: str) -> set[str]:
    """Konum metnini bölge kümesine çevirir.

    Bir ilan birden fazla bölgeye ait olabilir: "Cardiff, London or Remote (UK)"
    hem :data:`EU` hem :data:`REMOTE`'tur. Hiçbiri tutmuyorsa :data:`OTHER`.
    """
    s = fold(location or "")
    if not s.strip():
        return {OTHER}

    out: set[str] = set()
    if any(m in s for m in _TR):
        out.add(TR)
    if any(m in s for m in _EU):
        out.add(EU)
    if any(m in s for m in _US) or (_US_TOKENS & set(_tokens(s))):
        out.add(US)
    if any(m in s for m in _REMOTE):
        out.add(REMOTE)

    return out or {OTHER}


def _tokens(folded: str) -> list[str]:
    import re

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
