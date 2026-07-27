"""İlan metninde arama.

**Neden sunucuda:** korpustaki açıklamalar toplam 30 MB. Arayüzün diğer
filtreleri istemcide anında çalışıyor ve öyle kalmalı, ama tam metin araması
için 30 MB'ı tarayıcıya göndermek anlamsız. Sunucu ilan kimliklerini döner
(birkaç yüz KB), istemci kendi filtrelerini onun üzerine uygular.

**Neden gerekli:** arama şimdiye kadar yalnızca başlık, işveren, şehir ve şart
önizlemesine bakıyordu. "forklift", "SAP", "kaynakçı" gibi sözlükte olmayan
ama ilan metninde geçen terimler hiç bulunamıyordu — kullanıcı aradığı işin
var olduğunu bilmeden "sonuç yok" görüyordu.

**Operatörler:** iş arayanlar aramayı daraltmak ister; bu yüzden sadece
kelime yığını değil, üç operatör desteklenir:

* ``muhasebe uzman``  → ikisi de geçmeli (VE mantığı)
* ``"ön muhasebe"``   → tam öbek
* ``-stajyer``        → bu kelime geçmemeli

Dışlama özellikle işe yarıyor: "mühendis -satış" ya da "-stajyer" tek
başına yüzlerce alakasız ilanı eler.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .pipeline import fold

#: Aramada taranan metnin üst sınırı (karakter). İlanların kuyruğu genelde
#: hukuki metin ve eşit fırsat beyanı; oraya kadar aramak hem yavaş hem de
#: alakasız eşleşme üretir.
_MAX_SCAN = 8000


#: Sorgu terimini KISALTMAK için izin verilen Türkçe son ekler (katlanmış hâlde).
#:
#: Ölçüm bunu zorunlu kıldı: kullanıcı uygulamanın KENDİ chip etiketini
#: ("Kaynakçılık") arama kutusuna yazdığında **0 sonuç** alıyordu, çünkü ilanlar
#: "Kaynakçı" yazıyor. Eşleştirme motoru eklemeli yapıyı çözüyordu, arama kutusu
#: çözmüyordu — iki kod yolu Türkçe'yi farklı işliyordu.
#:
#: Liste bilinçli olarak KISA. Her eki soymak "kaynak" gibi çok kısa gövdeler
#: üretir ve Türkçe'de "kaynak" hem *welding* hem *resource* demek: o zaman
#: "insan kaynakları" her kaynakçı aramasına karışır (ölçüldü: "kaynak" 363
#: sonuç veriyor ve çoğu İnsan Kaynakları).
#: DİKKAT: "cilik"/"ciligi" bilinçli olarak YOK. Testim yazarken onları da
#: koymuştum ve test kırıldı: "kaynakcilik"ten "cilik" soyulunca **"kaynak"**
#: kalıyor ve "insan kaynaklari"na tutuyor — kaçınmak istediğimiz şeyin ta
#: kendisi. Yalnızca "lik" soyunca "kaynakci" kalır, istenen budur.
#:
#: D-087 — LİSTE GENİŞLETİLDİ. Canlı ölçüm (4.089 TR ilanı, 31 sorgu) bu
#: kısalığın bedelini gösterdi:
#:
#:     "muhasebe"  347 sonuç   |  "muhasebeci"   6 sonuç
#:     "satis"     833 sonuç   |  "satisci"      0 sonuç
#:     "muhendis"  162 sonuç   |  "muhendisler"  4 sonuç
#:
#: Türk kullanıcı mesleğini "muhasebeci" diye yazar, "muhasebe" diye değil.
#: Bu, D-074'te SÖZLÜK tarafında çözdüğüm eklemeli-dil probleminin arama
#: kutusundaki aynasıydı: iki kod yolu Türkçe'yi hâlâ farklı işliyordu.
#:
#: Sıra ÖNEMLİ: uzun ekler önce denenir, yoksa "ligi" varken "i" soyulur.
#: Fold sonrası ç→c, ı→i, ü→u olduğu için "-çı/-ci/-cı/-çi" hepsi "ci"dir.
_STRIPPABLE: tuple[str, ...] = (
    "ligi", "lugu", "lik", "luk", "leri", "lari", "ler", "lar",
    "cilik", "ciligi",
    "den", "dan", "ten", "tan", "nin", "nun",
    "ci", "cu", "si", "su", "ye", "ya", "de", "da", "te", "ta",
    "i", "u", "e", "a",
)
#: Ek soyulduktan sonra gövde bundan kısa kalırsa soyma yapılmaz.
_MIN_STEM = 4


def _stems(term: str) -> tuple[str, ...]:
    """Terim + (varsa) tek ek soyulmuş hâli. En fazla BİR ek soyulur."""
    for suf in _STRIPPABLE:
        if term.endswith(suf) and len(term) - len(suf) >= _MIN_STEM:
            return (term, term[: -len(suf)])
    return (term,)


@dataclass(frozen=True, slots=True)
class _Term:
    """Tek arama terimi: ucuz ön süzgeç + kesin desen.

    **Neden iki aşama (ölçüldü, 17.858 ilan):** yalnızca regex kullanmak
    sorgu başına 1470–1714 ms sürüyordu; eski düz ``in`` araması 30–49 ms.
    35 kat fark, arama kutusuna her harf yazılışında ödenirdi.

    ``needle`` en KISA gövdedir ve bütün varyantların ön ekidir; metinde hiç
    geçmiyorsa hiçbir varyant da geçemez, dolayısıyla regex'i çalıştırmadan
    reddetmek **güvenlidir**. Bu haliyle maliyet 36–55 ms: doğruluk eski
    hızla birlikte.
    """
    needle: str
    rx: re.Pattern[str]
    #: Yalnızca KULLANICININ YAZDIĞI biçim — gövde varyantı olmadan.
    #:
    #: Ayrım gerekli çünkü gövdeye inmek bazen anlam değiştirir: "kaynakci"nin
    #: gövdesi "kaynak" ve Türkçe'de "kaynak" hem *welding* hem *resource*
    #: demek — "insan kaynaklari" ilanları kaynakçı aramasına karışıyor.
    #:
    #: Eşleşmeyi ATMAK yanlış olurdu (kullanıcı hiç sonuç görmemektense
    #: sıralaması kötü sonuç görsün), ama tam eşleşmelerle aynı yere koymak da
    #: yanlış. Bu yüzden gevşetilmiş eşleşmeler İŞARETLENİR ve listede sona
    #: alınır (D-087).
    rx_exact: re.Pattern[str] | None = None

    def hits(self, text: str) -> bool:
        return self.needle in text and self.rx.search(text) is not None

    def hits_exact(self, text: str) -> bool:
        rx = self.rx_exact if self.rx_exact is not None else self.rx
        return rx.search(text) is not None


def _pattern(term: str) -> _Term:
    """Terimi KELİME BAŞINDAN eşleyen desen + ucuz ön süzgeci.

    Önceki sürüm düz ``term in hay`` yapıyordu ve kelime ortasına da tutuyordu:
    "SAP" araması "he**sap**lama" geçen her ilanı getiriyordu ("ön muhasebe"
    ölçümde 305 sonuçtan 153'e indi — aradaki 152 kelime-ortası gürültüydü).
    Kelime başı sınırı bunu keser; sonda sınır YOKTUR çünkü Türkçe eklemeli —
    "kaynakci" terimi "kaynakcisi" ve "kaynakcilar"ı da bulmalı.
    """
    govdeler = _stems(term)
    alt = "|".join(re.escape(s) for s in govdeler)
    return _Term(needle=min(govdeler, key=len),
                 rx=re.compile(r"(?<!\w)(?:" + alt + r")"),
                 rx_exact=re.compile(r"(?<!\w)" + re.escape(term)))


@dataclass(frozen=True, slots=True)
class Query:
    terms: tuple[str, ...]      # hepsi geçmeli
    phrases: tuple[str, ...]    # tam öbek olarak geçmeli
    excluded: tuple[str, ...]   # hiçbiri geçmemeli
    #: Derlenmiş terimler — sorgu başına BİR kez kurulur, 14.500 ilan için
    #: yeniden derlenmez.
    term_res: tuple["_Term", ...] = ()
    excl_res: tuple["_Term", ...] = ()
    #: Terimlerin BİTİŞİK yazılmış hâli (D-087).
    #:
    #: Ölçüm: "satın alma" 29 ilan, "satınalma" 11 ilan — İKİ AYRIK KÜME.
    #: Aynı işi arayan iki kullanıcı, yalnızca boşluk yüzünden birbirinin
    #: ilanlarını hiç görmüyordu. Türkçe'de bu yazım ikiliği çok yaygın
    #: (satınalma, önmuhasebe, işgücü…).
    joined_re: "_Term | None" = None

    def __post_init__(self) -> None:
        # Elle kurulan Query'ler de desenlerini alsın: aksi halde `terms` dolu
        # ama `term_res` boş bir nesne sessizce "her şey eşleşir" davranırdı.
        if self.terms and not self.term_res:
            object.__setattr__(self, "term_res",
                               tuple(_pattern(t) for t in self.terms))
        if self.excluded and not self.excl_res:
            object.__setattr__(self, "excl_res",
                               tuple(_pattern(t) for t in self.excluded))
        # Bitişik biçim yalnızca 2-3 terimde kurulur: daha uzun sorgularda
        # birleşim gerçek bir kelime olmaz ve boşuna tarama olurdu.
        if 2 <= len(self.terms) <= 3 and self.joined_re is None:
            object.__setattr__(self, "joined_re", _pattern("".join(self.terms)))

    @property
    def is_empty(self) -> bool:
        return not (self.terms or self.phrases or self.excluded)


_PHRASE = re.compile(r'"([^"]+)"')


def parse(raw: str) -> Query:
    """Arama dizesini operatörlerine ayırır."""
    if not raw:
        return Query((), (), ())

    text = fold(raw)
    phrases = tuple(p.strip() for p in _PHRASE.findall(text) if p.strip())
    text = _PHRASE.sub(" ", text)

    terms: list[str] = []
    excluded: list[str] = []
    for word in text.split():
        if word.startswith("-") and len(word) > 1:
            excluded.append(word[1:])
        elif word:
            terms.append(word)
    return Query(tuple(terms), phrases, tuple(excluded))


@dataclass(frozen=True, slots=True)
class Doc:
    """Bir ilanın aranabilir hâli.

    Başlık AYRI tutulur çünkü ölçüm sıralamayı zorunlu kıldı: "yazılım" araması
    129 ilan getiriyor ama yalnızca **11'inin başlığında** "yazılım" geçiyor;
    kalan 118'i açıklama metninden eşleşiyor ve sıralama olmadığı için ilk
    sayfayı onlar dolduruyordu. "insan kaynakları"nda oran 34/100.

    Açıklamadan eşleşenleri ATMAK yanlış olur — başlığı "Uzman" olup metninde
    muhasebe arayan gerçek ilanlar var — ama başlıkta geçenler önce gelmeli.
    """
    #: Başlık + işveren + şehir + küme + ilan metni, katlanmış.
    blob: str
    #: Yalnızca başlık, katlanmış. Sıralama için; ~60 karakter, bellek maliyeti
    #: ihmal edilebilir.
    title: str


def haystack(posting) -> Doc:
    """Bir ilanın aranabilir hâlini kurar.

    Başlık ve işveren torbaya da girer: bir terim yalnızca açıklamada geçtiğinde
    de başlıkta geçtiğinde de eşleşme sayılmalı. Ayrıca başlık kendi alanında
    ikinci kez tutulur — bu sıralama içindir, eşleşme için değil.
    """
    job = posting.job
    parts = (
        job.title, job.employer, job.city, job.occupation_id,
        (posting.job_text or "")[:_MAX_SCAN],
    )
    return Doc(blob=fold(" ".join(p for p in parts if p)),
               title=fold(job.title or ""))


def _hits(text: str, q: Query, *, check_excluded: bool, exact: bool = False) -> bool:
    if check_excluded and any(t.hits(text) for t in q.excl_res):
        return False
    if not all(p in text for p in q.phrases):
        return False
    vur = (lambda t: t.hits_exact(text)) if exact else (lambda t: t.hits(text))
    if all(vur(t) for t in q.term_res):
        return True
    # Bitişik yazım: "satın alma" arayan "Satınalma Sorumlusu"nu da görmeli.
    return q.joined_re is not None and vur(q.joined_re)


def exact_matches(doc: Doc, q: Query) -> bool:
    """Kullanıcının YAZDIĞI biçim geçiyor mu — gövdeye inmeden.

    Sıralama için: gevşetilmiş (gövde) eşleşmeler listenin sonuna alınır.
    Bkz. :class:`_Term.rx_exact`.
    """
    return _hits(doc.blob, q, check_excluded=True, exact=True)


def matches(doc: Doc, q: Query) -> bool:
    """İlanın sorguyu karşılayıp karşılamadığı.

    Dışlama **önce** bakılır: eleme, dahil etmeden ucuzdur ve kullanıcı
    "-stajyer" yazdıysa niyeti nettir.
    """
    return _hits(doc.blob, q, check_excluded=True)


def title_matches(doc: Doc, q: Query) -> bool:
    """Sorgu ilanın BAŞLIĞINDA geçiyor mu — sıralama için.

    Dışlamaya bakılmaz: dışlama zaten :func:`matches` içinde tüm metin üzerinde
    uygulandı. Burada yalnızca "bu ilan aradığın şeyin kendisi mi, yoksa
    metninde ondan söz eden bir ilan mı" sorusu var.
    """
    return _hits(doc.title, q, check_excluded=False)
