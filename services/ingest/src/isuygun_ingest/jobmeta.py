"""İlanın çalışma biçimi, istihdam türü ve deneyim seviyesi.

**Neden var:** kullanıcı "uzaktan çalışabileceğim işler" diye arıyor; bunu
serbest metin aramasıyla yapmak zorunda kalması bizim eksiğimiz. Korpusta
ölçüldü: ilanların %33'ü uzaktan, %25'i hibrit işaretine sahip.

**Yanlış pozitif riski burada özellikle yüksek** ve sebebi ironik: bu
kelimeler yazılım ilanlarında *teknik terim* olarak geçiyor.

* ``remote`` → "remote server", "Remote Desktop", "remote debugging"
* ``hybrid`` → "hybrid cloud", "hybrid app", "hybrid search"
* ``contract`` → "smart contract", "contract testing"

Bir yazılım ilanını "uzaktan" diye etiketlemek, kullanıcıyı ofise gitmesi
gereken bir işe uzaktan sanarak başvurttur. Bu yüzden çıplak kelime yetmez;
kalıp aranır ("fully remote", "remote position", "uzaktan çalışma").

**Bilinmiyor gerçek bir durumdur.** İşaret yoksa ``None`` döner ve bu "ofisten"
demek değildir. D-011'in üç durumlu mantığı burada da geçerli: emin olmadığımız
yeri boş bırakırız, varsayılanla doldurmayız.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .pipeline import fold

# ---------------------------------------------------------------------------
# Çalışma biçimi
# ---------------------------------------------------------------------------

#: Konum alanının kendisi "Remote" diyorsa bu en güçlü kanıttır — işveren
#: alanı bunun için doldurmuş, yorum gerekmiyor. Konum dizeleri kısa olduğu
#: için çıplak kelime burada güvenlidir; "Colorado, USA, Remote" da sayılır
#: (önceki hâli yalnızca baştaki "Remote"u yakalıyordu ve bu ilanlar hibrit
#: görünüyordu — şirket "hybrid workplace" yazmıştı ama rol uzaktandı).
_CITY_REMOTE = re.compile(r"\bremote\b|\buzaktan\b|\banywhere\b", re.I)

#: Metinde kalıp aranır, çıplak "remote" değil. "remote server" ile
#: "remote position" arasındaki farkı ancak komşu kelime söyler.
_REMOTE = re.compile(
    r"fully[- ]remote|100%\s*remote|remote[- ]first|remote[- ]friendly|"
    r"work(?:ing)? remotely|work from home|"
    r"remote (?:position|role|job|work|opportunity|team|employee)|"
    r"(?:position|role|job|this) is remote|"
    r"uzaktan calisma|uzaktan calis|evden calis|tamamen uzaktan",
    re.I,
)

_HYBRID = re.compile(
    r"hybrid (?:work|working|model|role|position|schedule|setup|arrangement)|"
    r"(?:work|working) model[^.]{0,20}hybrid|hybrid remote|"
    r"\d\s*(?:-|\+)?\s*days?\s*(?:a|per)?\s*week[^.]{0,30}(?:office|on-?site)|"
    r"(?:office|on-?site)[^.]{0,30}\d\s*days?\s*(?:a|per)\s*week|"
    r"hibrit",
    re.I,
)

#: Şirketin **genel politikasını** sayan cümleler. "fully office-based, fully
#: remote, or hybrid" bu ilanın biçimi değil, şirketin seçenekler listesidir.
#: Böyle bir cümleye bakıp "bu iş uzaktan" demek, kullanıcıyı ofise gitmesi
#: gereken bir işe uzaktan sanarak başvurttur.
_ENUMERATION = re.compile(
    r"(?:office[- ]based|on-?site|remote|hybrid)\s*,\s*"
    r"(?:(?:fully|100%)\s+)?(?:office[- ]based|on-?site|remote|hybrid)|"
    r"(?:office[- ]based|on-?site|remote|hybrid)\s*,?\s+(?:or|and|ya da|veya)\s+"
    r"(?:(?:fully|100%)\s+)?(?:office[- ]based|on-?site|remote|hybrid)",
    re.I,
)


#: Pahalı regex'ten önceki ucuz eleme. Kalıpların hepsi bu kelimelerden en az
#: birini içeriyor; hiçbiri metinde yoksa regex'i hiç çalıştırmaya gerek yok.
#: Korpusun %58'i zaten "belirtilmemiş" — sözlükte de kullanılan iki aşamalı
#: desen (ucuz sonda → pahalı eşleme) burada 30 MB metni taramaktan kurtarıyor.
_PROBES: dict[int, tuple[str, ...]] = {}

#: Cümle sınırı. Politika kontrolü sabit karakter penceresiyle yapılamaz:
#: ilan önce "we support office-based, remote, or hybrid" deyip hemen ardından
#: "this is a fully remote position" diyebiliyor. Sabit pencere ikinci cümleye
#: de değip gerçek beyanı eliyordu — testle yakalandı.
_SENTENCE_END = frozenset(".!?\n;")


def _sentence_around(text: str, start: int, end: int) -> str:
    left = start
    while left > 0 and text[left - 1] not in _SENTENCE_END:
        left -= 1
    right = end
    while right < len(text) and text[right] not in _SENTENCE_END:
        right += 1
    return text[left:right]


def _clean_hit(rx: re.Pattern[str], text: str) -> bool:
    """Kalıbı arar ama seçenek listesi içindeki eşleşmeyi saymaz.

    Tek bir ``search`` yetmez: ilan önce politika cümlesini yazıp sonra kendi
    biçimini söyleyebiliyor. İlk eşleşme elenirse sonrakilere bakılır.
    """
    probe = _PROBES.get(id(rx))
    if probe and not any(p in text for p in probe):
        return False
    for m in rx.finditer(text):
        if _ENUMERATION.search(_sentence_around(text, m.start(), m.end())):
            continue
        return True
    return False


_ONSITE = re.compile(
    r"on-?site (?:position|role|job|work|only)|"
    r"(?:position|role|job|this) is on-?site|fully on-?site|"
    r"in-office (?:position|role|work)|100%\s*on-?site|"
    r"ofisten calis|yerinde calis",
    re.I,
)

# ---------------------------------------------------------------------------
# İstihdam türü
# ---------------------------------------------------------------------------

#: "full_time" bilinçli olarak *çıkarılmaz*. Neredeyse hiçbir ilan yazmıyor
#: çünkü varsayılan; yazmayanı tam zamanlı saymak varsayımdır, kanıt değil.
_PART_TIME = re.compile(r"part[- ]time|yari zamanli|teilzeit|part time", re.I)
_INTERNSHIP = re.compile(
    r"\bintern(?:ship)?\b|stajyer|\bstaj\b|praktikum|werkstudent|"
    r"\btrainee\b|\bco-?op\b", re.I)
_CONTRACT = re.compile(
    r"\bfixed[- ]term\b|\bcontract (?:position|role|basis)\b|"
    r"\bfreelance\b|sozlesmeli|befristet|\btemporary (?:position|role)\b", re.I)

#: "contract" kelimesinin teknik kullanımları — bunlar istihdam türü değildir.
_CONTRACT_FALSE = re.compile(r"smart contract|contract test|contract negoti|"
                             r"contract manage|contract law", re.I)

# ---------------------------------------------------------------------------
# Deneyim seviyesi
# ---------------------------------------------------------------------------

#: Kıdem merdiveni. Yalnızca **başlıktan** okunur — açıklamada "you will work
#: with senior engineers" geçmesi ilanı kıdemli yapmaz; başlık işverenin kendi
#: etiketidir.
#:
#: Basamaklar öncelik sırasıyla denenir, **ilk eşleşen kazanır**. Sıra rastgele
#: değil:
#:
#: * Giriş işaretleri (stajyer/junior) en tepede: iş arayan için belirleyici ve
#:   üst basamaklarla neredeyse hiç birlikte geçmezler ("Junior Staff" nadir,
#:   olduğunda da kullanıcı giriş rolü arıyordur).
#: * ``manager`` merdivende **yok**: "Account Manager" kıdem değil rol türüdür
#:   ve dahil edildiğinde korpusun yarısı "kıdemli" görünüyordu (D-032). Yarıdan
#:   fazlasını seçen bir filtre hiçbir şey seçmiyor demektir.
#: * ``lead`` "Lead Generation Specialist"ten ayrılır — o bir satış rolüdür.
#:
#: Ölçüm (5803 ilan): korpusun **%55'i işaretsiz** kalıyor ("Software Engineer"
#: seviye söylemez). Bu boşluk gizlenmez; "belirtilmemiş" gerçek bir cevaptır
#: (D-011) ve arayüzde kendi sayaçlı grubunda gösterilir.
_LADDER: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    ("intern", re.compile(
        r"\bintern(?:ship)?\b|stajyer|\bstaj\b|praktikum|werkstudent|"
        r"\btrainee\b|\bco-?op\b", re.I)),
    ("junior", re.compile(
        r"\bjunior\b|\bjr\.?\b|\bentry[- ]level\b|\bnew grad(?:uate)?\b|"
        r"yeni mezun|\bgraduate (?:program|scheme|role)\b|\bapprentice\b", re.I)),
    ("executive", re.compile(
        r"\bdirector\b|\bvp\b|\bvice president\b|\bchief\b|\bc[teof]o\b|"
        r"\bhead of\b|genel mudur", re.I)),
    ("architect", re.compile(r"\barchitect\b|\bmimar\b", re.I)),
    ("lead", re.compile(
        r"\bstaff\b|\bprincipal\b|\bdistinguished\b|"
        r"\blead\b(?!\s+(?:generation|gen\b))", re.I)),
    ("senior", re.compile(r"\bsenior\b|\bsr\.?\b|\bsnr\b|kidemli", re.I)),
    ("mid", re.compile(r"\bmid[- ]?level\b|\bintermediate\b|\bii\b", re.I)),
)


@dataclass(frozen=True, slots=True)
class JobMeta:
    #: remote | hybrid | onsite | None(belirtilmemiş)
    work_arrangement: str | None = None
    #: part_time | contract | internship | None(belirtilmemiş)
    employment_type: str | None = None
    #: intern|junior|mid|senior|lead|architect|executive | None(belirtilmemiş)
    experience_level: str | None = None


def _arrangement(title: str, city: str, text: str) -> str | None:
    # Konum alanı en güçlü kanıt: işveren oraya "Remote" yazdıysa yorum yok.
    if _CITY_REMOTE.search(city or ""):
        return "remote"
    # Hibrit önce bakılır: "hybrid" diyen ilan çoğu zaman "remote" kelimesini
    # de kullanır ("2 days remote"), sırayı ters kurarsak hibriti uzaktan
    # sanarız — kullanıcıyı haftada 3 gün ofise gitmesi gereken işe yollar.
    if _clean_hit(_HYBRID, text):
        return "hybrid"
    if _clean_hit(_REMOTE, text):
        return "remote"
    if _clean_hit(_ONSITE, text):
        return "onsite"
    return None


def _employment(title: str, text: str) -> str | None:
    # Staj başlıkta geçiyorsa kesindir; açıklamada "intern" başka şey olabilir
    # ("our interns", "internal").
    if _INTERNSHIP.search(title):
        return "internship"
    if _PART_TIME.search(text):
        return "part_time"
    if _CONTRACT.search(text) and not _CONTRACT_FALSE.search(text):
        return "contract"
    if _INTERNSHIP.search(text):
        return "internship"
    return None


def _experience(title: str) -> str | None:
    for level, pat in _LADDER:
        if pat.search(title):
            return level
    return None


_PROBES[id(_HYBRID)] = ("hybrid", "hibrit", "week")
_PROBES[id(_REMOTE)] = ("remote", "uzaktan", "from home", "evden")
_PROBES[id(_ONSITE)] = ("site", "office", "ofis", "yerinde")

#: Türkçe karakter sondası. Korpusun yalnızca %6'sı Türkçe karakter içeriyor;
#: kalanı için `fold()` yerine `lower()` yeterli ve ~15 kat ucuz.
_TR_CHARS = frozenset("çğıöşüÇĞİÖŞÜ")


def _cheap_fold(text: str) -> str:
    return fold(text) if _TR_CHARS.intersection(text) else text.lower()


#: Kaynağın kendi çalışma-biçimi alanı (Lever/Ashby ``workplaceType``).
#: Bu bir *beyan*dır, bizim tahminimiz değil — metinden regex'le çıkarmaya
#: göre her zaman üstündür ve önce ona bakılır.
_SOURCE_ARRANGEMENT = {
    "remote": "remote", "hybrid": "hybrid",
    "onsite": "onsite", "on-site": "onsite", "on_site": "onsite",
}


def detect(*, title: str, city: str, description: str,
           source_arrangement: str = "") -> JobMeta:
    """İlanın üç ekseni. Kanıt yoksa ``None`` — "belirtilmemiş" bir cevaptır."""
    declared = _SOURCE_ARRANGEMENT.get((source_arrangement or "").strip().lower())
    folded_title = _cheap_fold(title or "")
    # Açıklamanın tamamı taranır ama katlanmış hâli üzerinden: "UZAKTAN
    # ÇALIŞMA" ile "uzaktan çalışma" aynı ilandır.
    folded_text = _cheap_fold(f"{title or ''} {description or ''}")
    return JobMeta(
        work_arrangement=declared or _arrangement(folded_title, city or "", folded_text),
        employment_type=_employment(folded_title, folded_text),
        experience_level=_experience(folded_title),
    )
