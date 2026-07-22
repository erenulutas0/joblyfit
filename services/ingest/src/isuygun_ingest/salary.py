"""İlan metninden maaş çıkarımı.

**Neden var:** saha araştırması, maaşın gizlenmesini en sık ve en somut
şikâyetlerden biri olarak gösterdi — iş arayanların önemli bir kısmı maaşı
yazmayan ilana hiç başvurmuyor. Türkiye'de ayrıca ağırlığı var: maaşı
belirtilmeyen bir teklifi reddetmek işsizlik ödeneğini kestirebiliyor.

**Tasarım kuralı, projenin geri kalanıyla aynı:** emin olunmayan yerde
uydurulmaz. Üç durum vardır ve üçü farklı şeyler söyler:

* **Bulundu** — metinde açıkça yazıyor, aralık ya da tek değer.
* **Belirtilmemiş** — metin okundu, maaş yok. Bu ilanın *kusuru*dur ve
  kullanıcıya öyle gösterilir (filtrelenebilir).
* **Okunamadı** — para birimi ve sayı var ama güvenle ayrıştırılamadı.
  "Belirtilmemiş" ile karıştırılmaz; ilana haksızlık olurdu.

Yanlış pozitif burada özellikle pahalıdır: "$500 bonus" veya "401(k)" gibi bir
ifadeyi maaş sanmak, kullanıcıya **var olmayan bir sayı** göstermek demektir.
Bu yüzden yakınında maaş bağlamı olmayan sayılar kabul edilmez.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Para birimi işaretleri → ISO kodu
_CURRENCY = {
    "$": "USD", "usd": "USD", "us$": "USD",
    "€": "EUR", "eur": "EUR",
    "£": "GBP", "gbp": "GBP",
    "₺": "TRY", "try": "TRY", "tl": "TRY",
    "chf": "CHF", "sek": "SEK", "dkk": "DKK", "nok": "NOK", "pln": "PLN",
    "c$": "CAD", "cad": "CAD",
}

#: Maaş bağlamı. Bunlardan biri yakında yoksa sayı maaş sayılmaz —
#: "$500 bonus" ya da "$2M funding" gibi ifadeleri elemek için.
_CONTEXT = re.compile(
    r"salary|salaries|compensation|base pay|base salary|pay range|pay rate|"
    r"annual|annually|per year|per hour|hourly|wage|remuneration|"
    r"maas|maaş|ucret|ücret|brut|net ucret|yillik|aylik|saatlik",
    re.I,
)

#: Dönem işaretleri
_HOURLY = re.compile(r"per hour|/\s?h(?:r|our)?\b|hourly|saatlik|stundenlohn", re.I)
_MONTHLY = re.compile(r"per month|/\s?mo(?:nth)?\b|monthly|aylik|aylık|monatlich", re.I)
_YEARLY = re.compile(r"per year|per annum|/\s?y(?:r|ear)?\b|annual|yearly|yillik|yıllık|p\.a\.", re.I)

_SYM = r"\$|€|£|₺"
_CODE = r"USD|EUR|GBP|TRY|TL|CHF|SEK|DKK|NOK|PLN|CAD"
_NUM = r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?"

#: Aralık: iki sayı, arada tire/en-dash/"to"/"–"/"ile"
_RANGE = re.compile(
    rf"(?P<c1>{_SYM})?\s?(?P<n1>{_NUM})\s?(?P<k1>k\b)?\s?(?P<cc1>{_CODE})?"
    rf"\s*(?:-|–|—|to|ile|až)\s*"
    rf"(?P<c2>{_SYM})?\s?(?P<n2>{_NUM})\s?(?P<k2>k\b)?\s?(?P<cc2>{_CODE})?",
    re.I,
)

#: Tek değer
_SINGLE = re.compile(
    rf"(?:(?P<c>{_SYM})\s?(?P<n>{_NUM})\s?(?P<k>k\b)?|"
    rf"(?P<n2>{_NUM})\s?(?P<k2>k\b)?\s?(?P<cc>{_CODE}))",
    re.I,
)

#: Makul maaş aralığı (yıllık karşılığı). Dışına çıkan sayı maaş sayılmaz —
#: "$2,500,000 funding" ya da "$12 lunch stipend" gibi ifadeleri eler.
_PLAUSIBLE_YEARLY = (5_000, 2_000_000)


@dataclass(frozen=True, slots=True)
class Salary:
    currency: str
    min_amount: float
    max_amount: float
    period: str            # yearly | monthly | hourly
    source_span: str       # metinde neye dayandığı — iddia kanıtsız olmaz

    @property
    def is_range(self) -> bool:
        return self.max_amount > self.min_amount


def _to_number(raw: str, k: bool) -> float | None:
    """'120,000' / '120.000' / '120' + k → sayı.

    Binlik ayracı dile göre değişiyor: İngilizce '120,000', Türkçe '120.000'.
    Ayracı yanlış okumak 120 bini 120'ye çevirir, yani sayıyı bin kat yanlış
    gösterir — bu yüzden ondalık olarak yorumlama yalnızca **iki basamaklı**
    kuyrukta yapılır.
    """
    s = raw.strip()
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", s):        # 120,000 / 120.000
        s = re.sub(r"[.,]", "", s)
    elif re.fullmatch(r"\d+[.,]\d{1,2}", s):             # 25.50 → ondalık
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "").replace(".", "")
    try:
        value = float(s)
    except ValueError:
        return None
    return value * 1000 if k else value


def _period(window: str, amount: float, currency: str) -> str:
    """Dönemi metinden okur; yoksa büyüklükten kestirir."""
    if _HOURLY.search(window):
        return "hourly"
    if _MONTHLY.search(window):
        return "monthly"
    if _YEARLY.search(window):
        return "yearly"
    # Metin söylemiyorsa büyüklük kestirimi. TL'de aylık, diğerlerinde yıllık
    # yaygın; küçük rakamlar saatlik.
    if amount < 200:
        return "hourly"
    if currency == "TRY":
        return "monthly"
    return "yearly" if amount >= 10_000 else "monthly"


def _yearly_equivalent(amount: float, period: str) -> float:
    return {"hourly": amount * 2080, "monthly": amount * 12}.get(period, amount)


def _currency_of(*candidates: str | None) -> str | None:
    for c in candidates:
        if c and c.strip().lower() in _CURRENCY:
            return _CURRENCY[c.strip().lower()]
    return None


def extract(text: str) -> Salary | None:
    """Metinden maaş çıkarır. Güvenle okunamıyorsa ``None``.

    ``None`` iki farklı şeyi birden temsil eder ve bu bilinçlidir: çağıran
    taraf metinde para birimi geçip geçmediğine bakarak "belirtilmemiş" ile
    "okunamadı"yı ayırabilir (:func:`mentions_money`).
    """
    if not text:
        return None

    # Elenen aralıkların yeri. Tek-değer taraması bunların **içine girmez**:
    # "$160,000 - $120,000" bozuk bir aralıktır ve bir ucunu alıp "maaş
    # $160.000" demek, okunamayan veriden kesin bir sayı uydurmak olur.
    rejected_spans: list[tuple[int, int]] = []

    for m in _RANGE.finditer(text):
        window = text[max(0, m.start() - 90): m.end() + 90]
        if not _CONTEXT.search(window):
            continue
        rejected_spans.append(m.span())
        currency = _currency_of(m.group("c1"), m.group("c2"),
                                m.group("cc1"), m.group("cc2"))
        if currency is None:
            continue
        lo = _to_number(m.group("n1"), bool(m.group("k1")))
        hi = _to_number(m.group("n2"), bool(m.group("k2")))
        if lo is None or hi is None or hi < lo:
            continue
        period = _period(window, hi, currency)
        if not (_PLAUSIBLE_YEARLY[0] <= _yearly_equivalent(hi, period) <= _PLAUSIBLE_YEARLY[1]):
            continue
        return Salary(currency, lo, hi, period, m.group(0).strip()[:60])

    for m in _SINGLE.finditer(text):
        if any(s <= m.start() < e for s, e in rejected_spans):
            continue          # elenen aralığın ucu tek maaş sayılmaz
        window = text[max(0, m.start() - 90): m.end() + 90]
        if not _CONTEXT.search(window):
            continue
        currency = _currency_of(m.group("c"), m.group("cc"))
        if currency is None:
            continue
        raw = m.group("n") or m.group("n2")
        k = bool(m.group("k") or m.group("k2"))
        amount = _to_number(raw, k)
        if amount is None:
            continue
        period = _period(window, amount, currency)
        if not (_PLAUSIBLE_YEARLY[0] <= _yearly_equivalent(amount, period) <= _PLAUSIBLE_YEARLY[1]):
            continue
        return Salary(currency, amount, amount, period, m.group(0).strip()[:60])

    return None


_MONEY = re.compile(rf"(?:{_SYM})\s?\d|\d\s?(?:{_CODE})\b", re.I)


def mentions_money(text: str) -> bool:
    """Metinde para geçiyor mu?

    "Maaş belirtilmemiş" ile "okuyamadım"ı ayırmak için. İkisini birbirine
    karıştırmak, maaşını yazan bir ilanı yazmamış gibi göstermek olurdu.
    """
    return bool(text) and bool(_MONEY.search(text))


_SYMBOL_OF = {"USD": "$", "EUR": "€", "GBP": "£", "TRY": "₺"}
_PERIOD_TR = {"yearly": "yıllık", "monthly": "aylık", "hourly": "saatlik"}


def format_tr(s: Salary) -> str:
    """Kullanıcıya gösterilecek metin. Dönüştürme yapılmaz — kaynaktaki birim."""
    sym = _SYMBOL_OF.get(s.currency, s.currency + " ")

    def fmt(v: float) -> str:
        return f"{v:,.0f}".replace(",", ".") if v >= 1000 else f"{v:g}"

    body = fmt(s.min_amount) if not s.is_range else f"{fmt(s.min_amount)}–{fmt(s.max_amount)}"
    return f"{sym}{body} {_PERIOD_TR.get(s.period, s.period)}"
