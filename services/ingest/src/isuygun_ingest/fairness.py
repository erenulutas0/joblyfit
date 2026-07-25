"""İlan metninde ayrımcı/dışlayıcı dil tespiti.

**Neden var:** launch pazarı Türkiye (D-009) ve Türkiye ilan piyasasında yaşa,
cinsiyete, askerlik durumuna dayalı dışlayıcı ifadeler yaygın — İş Kanunu md.5
ve 6701 sayılı TİHEK Kanunu bunları yasaklıyor ve yaptırım gerçek (TİHEK 2025'te
milyonlarca TL ceza kesti). Bu ilanları kullanıcıya **işaretlemeden** göstermek,
platformun adalet duruşuna (D-005) aykırı olurdu.

**Tasarım kuralı — hüküm vermeyiz, bilgilendiririz (T-008):** Bu modül bir ilanı
"yasa dışı" ilan **etmez**. Bir ifadeyi işaretler, hangi kategoride olduğunu
söyler ve kullanıcıya haklarını hatırlatır. Bazı şartlar yasal olabilir (ör.
belirli rollerde cinsiyet, ISKUR üzerinden pozitif ayrımcılık); ayrımı kullanıcı
ve gerekirse TİHEK yapar, biz değil.

**Yanlış pozitif burada özellikle zararlı:** masum bir ifadeyi "ayrımcı" diye
işaretlemek hem ilana haksızlık eder hem kullanıcının uyarılara güvenini aşındırır.
İki tuzak ölçülerek elendi:

* Betimleyici ("genç ve dinamik bir ekip") ≠ şart ("35 yaş altı"). Yalnızca
  **şart bağlamı** işaretlenir.
* Sayı içeren her ifade yaş değildir: "50-60 mühendis yönetmek", "5-10 yıl
  deneyim". Yaş yalnızca yaş **kelimesi** yakınında işaretlenir.

**Dormant olabilir, sorun değil:** doğrudan şirket ATS'leri (mevcut korpus)
EEO-uyumlu; işaret çıkmaz. İşaretler Türkiye/aggregator verisi geldiğinde
görünür — modül o gün için hazırdır.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Kategoriler ve kalıplar
# ---------------------------------------------------------------------------

#: Yaş sınırı. Yalnızca yaş **kelimesi** ile birlikte gelen sayılar; çıplak
#: sayı aralıkları ("50-60 kişi", "5-10 yıl") ELENMELİ.
_AGE = re.compile(
    r"\b\d{2}\s*yaş(?:ını)?\s*(?:altı|üstü|geçmemiş|geçmeyen|altında|üstünde)\b|"
    r"(?:en\s*fazla|en\s*çok|maksimum|maks\.?)\s*\d{2}\s*yaş\b|"
    r"\b\d{2}\s*[-–]\s*\d{2}\s*yaş(?:\s*(?:arası|aralığında))?\b|"
    r"\bunder\s*(?:2[0-9]|3[0-9]|40)\s*years?\s*(?:old|of\s*age)\b|"
    r"\b(?:max(?:imum)?|no\s*older\s*than)\s*\d{2}\s*years?\s*(?:old|of\s*age)\b|"
    r"\baged?\s*\d{2}\s*(?:to|[-–])\s*\d{2}\b",
    re.I,
)

#: Cinsiyet dışlaması. Kapsayıcı ifadeler (DEI, "kadın mühendisler",
#: EEO beyanları) DEĞİL — yalnızca **dışlayıcı** şart.
#: Cinsiyet kelimesinin niteleyebileceği KİŞİ adları. İlk sürüm yalnızca
#: {eleman, personel, aday, çalışan} tanıyordu ve cinsiyet kelimesinin hemen
#: ardından gelmesini istiyordu. Türkçe iş başlıkları araya rolü sokar, bu
#: yüzden en açık vakalar kaçıyordu — canlı korpusta ölçüldü:
#:   "Kadın satış personeli"              → bayrak YOK
#:   "Almanca konuşan kadın satış elemanı" → bayrak YOK
#:   "Kadın kasiyer"                       → bayrak YOK
_KISI = (
    r"(?:eleman|personel|aday|adaylar|çalışan|işçi|kasiyer|garson|şoför|sürücü"
    r"|görevli|sorumlu|danışman|temsilci|operatör|usta|kalfa|çırak|teknisyen"
    r"|tekniker|sekreter|asistan|hemşire|öğretmen|satıcı|tezgahtar|kurye"
    r"|bakıcı|aşçı|komi|resepsiyonist|müdür|uzman|stajyer)"
)
_GENDER = re.compile(
    r"(?:sadece|yalnızca|tercihen)\s*(?:erkek|kadın|bay|bayan)\b|"
    # Cinsiyet + en fazla 2 araya giren kelime + kişi adı:
    # "kadın satış personeli", "erkek depo görevlisi", "bayan ön muhasebe elemanı".
    # Sınır 2 kelime KASITLI: "kadın giyim mağazası için satış personeli"
    # ifadesinde "personel" 5. kelimededir ve eşleşmez — orada "kadın" ürünü
    # niteliyor, adayı değil.
    r"\b(?:erkek|kadın|bay|bayan)\s+(?:\w+\s+){0,2}" + _KISI + r"\w*\b|"
    r"\b(?:male|female)\s*(?:candidates?\s*)?only\b|"
    r"\b(?:men|women)\s*only\b|"
    r"\bmust\s*be\s*(?:male|female)\b",
    re.I,
)

#: ÜÇÜNCÜ KİŞİ adları: cinsiyet kelimesi bunlardan birini niteliyorsa adayı
#: değil HİZMET VERİLEN kişiyi tanımlıyordur. Ölçümde yakalandı: "Yatağa Bağımlı
#: Yaşlı **Erkek Hastamıza** Hemşire Arıyoruz" ayrımcı olarak işaretlenmişti —
#: oysa cümle adayın cinsiyetini kısıtlamıyor, hastanın cinsiyetini söylüyor.
#: Bakım işlerinde bu kalıp yaygındır ve yanlış suçlama, uyarının kendisini
#: değersizleştirir.
_UCUNCU_KISI = re.compile(
    r"\b(?:erkek|kadın|bay|bayan)\s+"
    r"(?:hasta|hastamız|hastaya|hastamıza|müşteri|müşterimiz|müşterilerimiz"
    r"|misafir|konuk|çocuk|bebek|öğrenci|kursiyer|yolcu|danışan|sakin|üye"
    r"|kullanıcı|yaşlı|bireyler?|katılımcı)\w*",
    re.I,
)

#: KAPSAYICI ifadeler — bunlar ayrımcılık DEĞİL, tersi. "kadın ve erkek
#: adaylar" genişletilmiş desene takılırdı ("ve"+"erkek" iki araya giren
#: kelime) ve kapsayıcı bir işvereni ayrımcılıkla işaretlemek, aracın
#: güvenilirliğini bitirir.
_KAPSAYICI = re.compile(
    r"\b(?:kadın|bayan)\s*(?:[-/]|ve|veya|,|ya\s*da)\s*(?:erkek|bay)\b|"
    r"\b(?:erkek|bay)\s*(?:[-/]|ve|veya|,|ya\s*da)\s*(?:kadın|bayan)\b|"
    r"fark\s*gözet(?:meksizin|meden)|ayrım\s*yap(?:ılmaksızın|maksızın|madan)|"
    r"cinsiyet\s*(?:ayrımı|farkı|ayrımcılığı)|"
    r"\ball\s*genders?\b|\bregardless\s*of\s*gender\b",
    re.I,
)

#: Askerlik durumu şartı (Türkiye'ye özgü, İş Kanunu md.5 kapsamında).
_MILITARY = re.compile(
    r"askerli(?:k|ği?ni?)\s*(?:yap(?:mış|tığını)|tamamla(?:mış|dığını)|"
    r"bitir(?:miş|diğini)|ile\s*ilişiği\s*(?:olmayan|bulunmayan))|"
    r"askerlikle?\s*ilişiği\s*(?:olmayan|bulunmayan)|"
    r"muaf\s*(?:olan|olması)\s*.{0,10}asker",
    re.I,
)

#: Medeni/ailevi durum.
_MARITAL = re.compile(
    r"\b(?:evli|bekar)\s*(?:olması|adaylar?|tercih\s*edilir|olan)\b|"
    r"\bçocuk\s*sahibi\s*ol(?:mayan|maması)\b|"
    r"\bmarried\s*(?:candidates?\s*)?(?:preferred|only)\b|"
    r"\bsingle\s*(?:candidates?\s*)?(?:preferred|only)\b",
    re.I,
)

#: "Ana dili" / uyruk-proxy. Bu daha **yumuşak** bir işarettir: gerçek bir dil
#: ihtiyacı olabilir ama "native speaker" şartı çoğu yerde uyruk ayrımcılığı
#: proxy'si sayılır. Yasak değil, kapsayıcılık **önerisi** olarak sunulur.
_NATIVE = re.compile(
    r"\bnative\s*(?:english|german|french|turkish)?\s*speaker\b|"
    r"\bmother\s*tongue\s*(?:english|german|turkish)\b|"
    r"\bana\s*dili\s*(?:ingilizce|türkçe|almanca)\b",
    re.I,
)

#: Betimleyici bağlam — kültür/ekip anlatan, şart olmayan ifadeler. Yakınında
#: bunlardan biri varsa işaret **düşürülür** (yanlış pozitif önleme).
_DESCRIPTIVE = re.compile(
    r"\b(?:genç\s*ve\s*dinamik|dinamik\s*bir\s*ekip|young\s*and\s*dynamic|"
    r"dynamic\s*team|ekip\s*ruhu|team\s*spirit|kültürümüz|our\s*culture|"
    r"we\s*value\s*diversity|fırsat\s*eşitliği|equal\s*opportunity)\b",
    re.I,
)


@dataclass(frozen=True, slots=True)
class FairnessFlag:
    #: age | gender | military | marital | native_speaker
    category: str
    #: Kullanıcıya gösterilecek kısa açıklama — hüküm değil, bilgilendirme.
    note: str
    #: Metinde neye dayandığı (kanıt). İddia kanıtsız olmaz.
    evidence: str
    #: hard = açık dışlama · soft = kapsayıcılık önerisi
    severity: str = "hard"


_CATEGORY_NOTES = {
    "age": ("Yaş sınırı belirtiliyor olabilir. İş Kanunu md.5 yaşa dayalı "
            "ayrımcılığı yasaklar; bazı istisnalar olabilir."),
    "gender": ("Cinsiyete dayalı dışlayıcı bir ifade olabilir. İş Kanunu md.5 "
               "kapsamında değerlendirilebilir; belirli roller için yasal "
               "istisnalar bulunabilir."),
    "military": ("Askerlik durumu şartı olabilir. Bu, dolaylı olarak cinsiyet "
                 "ayrımcılığı doğurabilir (İş Kanunu md.5)."),
    "marital": ("Medeni/ailevi duruma dayalı bir tercih olabilir; İş Kanunu "
                "md.5 kapsamında değerlendirilebilir."),
    "native_speaker": ("'Ana dili' şartı yerine dil seviyesi (ör. C1/C2) istemek "
                       "daha kapsayıcıdır ve uyruk ayrımcılığı algısını önler."),
}

_CHECKS: tuple[tuple[str, "re.Pattern[str]", str], ...] = (
    ("age", _AGE, "hard"),
    ("gender", _GENDER, "hard"),
    ("military", _MILITARY, "hard"),
    ("marital", _MARITAL, "hard"),
    ("native_speaker", _NATIVE, "soft"),
)

#: İşaretin çevresine bakılan pencere (karakter) — betimleyici bağlam kontrolü için.
_WINDOW = 60


def scan(title: str, description: str) -> list[FairnessFlag]:
    """İlanda ayrımcı/dışlayıcı dil işaretlerini döndürür. Yoksa boş liste.

    Hiçbir şeye "yasa dışı" demez; işaretler ve bilgilendirir. Her kategori en
    fazla bir kez işaretlenir — aynı uyarıyı tekrarlamak kullanıcıyı yormaktan
    başka işe yaramaz.
    """
    text = f"{title or ''}\n{description or ''}"
    flags: list[FairnessFlag] = []
    for category, pat, severity in _CHECKS:
        m = pat.search(text)
        if not m:
            continue
        # Betimleyici bağlam (kültür/DEI) yakınındaysa şart değildir → atla.
        window = text[max(0, m.start() - _WINDOW): m.end() + _WINDOW]
        if severity == "hard" and _DESCRIPTIVE.search(window):
            continue
        # Cinsiyet için ayrıca KAPSAYICI ifade kontrolü: "kadın ve erkek
        # adaylar" ayrımcılık değil, tersidir. Kapsayıcı bir işvereni
        # ayrımcılıkla işaretlemek, uyarının kendisini değersizleştirir.
        if category == "gender" and _KAPSAYICI.search(window):
            continue
        # Cinsiyet kelimesi ADAYI değil hizmet verilen kişiyi niteliyorsa
        # (erkek hasta, kadın müşteri) bu bir kısıtlama beyanı değildir.
        # Eşleşmenin BAŞINDAN bakılır: pencere geniş tutulursa aynı ilandaki
        # gerçek bir kısıtlama da yanlışlıkla affedilirdi.
        if category == "gender" and _UCUNCU_KISI.match(text, m.start()):
            continue
        flags.append(FairnessFlag(
            category=category,
            note=_CATEGORY_NOTES[category],
            evidence=m.group(0).strip()[:80],
            severity=severity,
        ))
    return flags
