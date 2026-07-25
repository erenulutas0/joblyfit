"""Paylaşılan beceri/şart sözlüğü — ilan tarafı ile profil tarafının ortak dili.

**Bu modülün varlık sebebi bir hatadır.** Önceki tasarımda ilan şartları ilandan,
profil alanları da aynı ilanlardan türetiliyordu; ikisi aynı korpustan geldiği için
"çalışıyor" görünüyordu. Gerçek bir CV yüklendiğinde hiçbir şey eşleşmedi — çünkü
katalog yalnızca 8 sentetik ilandaki 18 alanı tanıyordu ve kullanıcının mesleği
onların hiçbiri değildi.

Doğru çözüm, iki tarafın da **aynı sözlüğe** bağlanmasıdır: ilan metni de, CV metni
de buradaki terimlere eşlenir. Eşleşme ancak o zaman anlamlıdır.

Bu tam bir ontoloji **değildir** (OPEN-23). ESCO/O*NET gibi bir taksonomiye
geçilene kadarki asgari çalışan sürümdür. Kapsamı bilinçli olarak geniş tutulur —
sistem yalnız white-collar için tasarlanmaz (PRODUCT.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .pipeline import fold

# --------------------------------------------------------------------------
# Kategoriler
# --------------------------------------------------------------------------
# license / work_authorization / legally_required_certificate → gate alanı (D-012)

SKILL = "skill"
LICENSE = "license"
CERT = "certificate"
EXPERIENCE = "experience"
LANGUAGE = "language"
EDUCATION = "education"
SHIFT = "shift"


@dataclass(frozen=True, slots=True)
class Term:
    key: str
    label: str                       # kullanıcıya gösterilen Türkçe etiket
    category: str
    forms: tuple[str, ...]           # metinde aranacak yüzey biçimleri
    cluster: str = "genel"           # meslek kümesi (arayüzde gruplama)
    asks_years: bool = False         # süre sorulur mu


# TÜRKÇE EK TOLERANSI — ölçülmüş bir kök nedenin düzeltmesi.
#
# Desenler sonda `\b` istiyordu ve Türkçe eklemeli bir dil olduğu için bu her eki
# bloke ediyordu. Ölçüm (5.930 TR ilanı): ilanların **%44'ünden hiç şart
# okunamıyordu**. Örnekler — solda tutan, sağda TUTMAYAN:
#   "Öğretmen aranıyor" ✓ | "Matematik Öğretmen**i**" ✗
#   "Temizlik Görevlisi" ✓ | "Temizlik Görevli**leri**" ✗
#   "Mağaza sorumlusu"  ✓ | "**Mağazada** çalışacak"  ✗
#   "Aşçı aranıyor"     ✓ | "Aşçı**sı** aranıyor"     ✗
#
# Sondaki sınırı tamamen KALDIRMAK çözüm değil: "import" → "important",
# "java" → "javascript", "komi" → "komisyon" eşleşirdi. Bu yüzden yalnızca
# GERÇEK Türkçe eklerine izin verilir. Liste folded (ASCII) hâlde yazılır çünkü
# `fold()` ı→i, ş→s, ğ→g, ü→u, ö→o, ç→c dönüşümünü zaten yapmıştır.
_TR_EK = (
    r"(?:l[ae]r|l[iu]k|l[iu]g[iu]|c[iu]l[iu]k|c[iu]l[iu]g[iu]"
    # -lama/-leme: fiilden isim ("bordrolama", "depolama", "stoklama").
    r"|l[ae]m[ae]"
    r"|s[iu]z|l[iu]|c[iu]|[csz][iu]|n[iu]n|y[ae]|d[ae]n|t[ae]n|d[ae]|t[ae]|[iuea])"
)
#: En fazla üç ek zinciri: "gorev-li-ler-den" gibi biçimler için yeter.
_TR_EK_ZINCIR = _TR_EK + r"{0,3}"
#: Ek toleransı yalnızca bu uzunluktan itibaren uygulanır. 3 harfli biçimler
#: Türkçe ÖZEL ADLARA çarpıyor: "sem"+"a" = Sema, "sap"+"a" = Sapa,
#: "sef"+"a" = Sefa. Bu biçimler ("git", "sap", "seo", "sef", "sem"…) katı
#: kalır; zaten kısa oldukları için ek almadan da geçiyorlar.
_EK_MIN_UZUNLUK = 4


#: Kelimenin SONUNDAKİ tek eki yakalar — gövde üretmek için.
_EK_SON = re.compile(_TR_EK + r"$")


def _govdeler(word: str) -> tuple[str, ...]:
    """Kelime + Türkçe ekleri soyulmuş gövdeleri (en fazla 3 ek).

    Tek kelimelik biçimler regex'le değil **sözlük aramasıyla** eşleşiyor
    (100+ deseni 30 MB metne karşı çalıştırmak pahalı olurdu). Sözlük tam
    eşitlik arar, dolayısıyla "ogretmeni" → "ogretmen" bulunamıyordu. Çözüm
    ters yönden: metindeki kelimeden gövde üretip sözlüğe bakılır — kelime
    başına birkaç sözlük araması, regex yok.

    Yanlış gövde üretmek zararsızdır: sözlükte yoksa eşleşme olmaz. Gövdenin
    ``_EK_MIN_UZUNLUK``tan kısa olması ENGELLENİR — "sema" → "sem" olurdu ve
    Sema bir özel ad, SEM ise pazarlama terimi.
    """
    out = [word]
    govde = word
    for _ in range(3):
        m = _EK_SON.search(govde)
        if not m or m.start() < _EK_MIN_UZUNLUK:
            break
        govde = govde[: m.start()]
        out.append(govde)
    return tuple(out)


def T(key, label, category, forms, cluster="genel", asks_years=False) -> Term:
    return Term(key, label, category, tuple(forms), cluster, asks_years)


# --------------------------------------------------------------------------
# Sözlük
# --------------------------------------------------------------------------
# Yüzey biçimleri hem Türkçe hem İngilizce yazılır: ilanlar sıklıkla İngilizce,
# CV'ler sıklıkla Türkçedir. `fold()` her ikisini de aksansızlaştırır.

TERMS: tuple[Term, ...] = (
    # ---- yazılım / veri ----
    T("software_dev", "Yazılım geliştirme", EXPERIENCE,
      ["yazilim gelistirici", "yazilim muhendisi", "software developer",
       "software engineer", "softwareentwickler", "entwickler", "programmierer",
       "backend developer", "frontend developer", "fullstack"], "Yazılım ve veri", True),
    T("python", "Python", SKILL, ["python"], "Yazılım ve veri", True),
    T("javascript", "JavaScript", SKILL, ["javascript", "js", "es6"], "Yazılım ve veri", True),
    T("typescript", "TypeScript", SKILL, ["typescript", "ts"], "Yazılım ve veri", True),
    T("java", "Java", SKILL, ["java"], "Yazılım ve veri", True),
    T("csharp", "C#/.NET", SKILL, ["c#", "csharp", ".net", "dotnet", "asp.net"], "Yazılım ve veri", True),
    T("cpp", "C/C++", SKILL, ["c++", "cpp"], "Yazılım ve veri", True),
    T("go", "Go", SKILL, ["golang"], "Yazılım ve veri", True),
    T("php", "PHP", SKILL, ["php", "laravel", "symfony"], "Yazılım ve veri", True),
    T("ruby", "Ruby", SKILL, ["ruby", "rails"], "Yazılım ve veri", True),
    T("swift_kotlin", "Mobil (Swift/Kotlin)", SKILL,
      ["swift", "kotlin", "android developer", "ios developer", "mobil uygulama"], "Yazılım ve veri", True),
    T("react", "React", SKILL, ["react", "reactjs", "react.js", "next.js", "nextjs"], "Yazılım ve veri", True),
    T("vue_angular", "Vue / Angular", SKILL, ["vue", "vuejs", "angular"], "Yazılım ve veri", True),
    T("node", "Node.js", SKILL, ["node.js", "nodejs", "express.js"], "Yazılım ve veri", True),
    T("sql", "SQL / veritabanı", SKILL,
      ["sql", "postgresql", "postgres", "mysql", "mssql", "oracle db", "veritabani"], "Yazılım ve veri", True),
    T("nosql", "NoSQL", SKILL, ["mongodb", "redis", "elasticsearch", "cassandra", "dynamodb"], "Yazılım ve veri"),
    T("docker_k8s", "Docker / Kubernetes", SKILL, ["docker", "kubernetes", "k8s", "container"], "Yazılım ve veri"),
    T("cloud", "Bulut (AWS/Azure/GCP)", SKILL,
      ["aws", "azure", "gcp", "google cloud", "amazon web services", "bulut"], "Yazılım ve veri", True),
    T("cicd", "CI/CD ve DevOps", SKILL,
      ["ci/cd", "jenkins", "gitlab ci", "github actions", "terraform", "devops"], "Yazılım ve veri"),
    T("git", "Git / versiyon kontrol", SKILL, ["git", "github", "gitlab", "bitbucket"], "Yazılım ve veri"),
    T("ml", "Makine öğrenmesi / AI", SKILL,
      ["machine learning", "makine ogrenmesi", "deep learning", "tensorflow", "pytorch",
       "yapay zeka", "llm", "nlp", "veri bilimi", "data science"], "Yazılım ve veri", True),
    T("data_eng", "Veri mühendisliği", SKILL,
      ["etl", "airflow", "spark", "hadoop", "data warehouse", "dbt", "veri ambari"], "Yazılım ve veri", True),
    T("analytics", "Analitik / BI", SKILL,
      ["power bi", "tableau", "looker", "google analytics", "veri analizi", "data analysis"], "Yazılım ve veri"),
    T("qa", "Test / QA", SKILL,
      ["selenium", "cypress", "test otomasyon", "qa engineer", "yazilim testi"], "Yazılım ve veri", True),
    T("security", "Siber güvenlik", SKILL,
      ["siber guvenlik", "cyber security", "penetration test", "sizma testi", "soc analyst"], "Yazılım ve veri", True),

    # ---- tasarım / ürün / pazarlama ----
    T("ui_ux", "UI/UX tasarım", SKILL,
      ["ui/ux", "ux design", "kullanici deneyimi", "arayuz tasarim", "figma", "sketch"], "Tasarım ve ürün", True),
    T("graphic", "Grafik tasarım", SKILL,
      ["grafik tasarim", "photoshop", "illustrator", "indesign", "adobe"], "Tasarım ve ürün", True),
    T("product", "Ürün yönetimi", SKILL,
      ["product manager", "urun yoneticisi", "product owner", "urun yonetimi", "roadmap"], "Tasarım ve ürün", True),
    T("agile", "Agile / Scrum", SKILL, ["agile", "scrum", "kanban", "jira"], "Tasarım ve ürün"),
    T("digital_marketing", "Dijital pazarlama", SKILL,
      ["dijital pazarlama", "digital marketing", "google ads", "meta ads", "performance marketing",
       "seo", "sem", "sosyal medya yonetimi"], "Pazarlama ve satış", True),
    T("content", "İçerik üretimi", SKILL,
      ["icerik uretimi", "content marketing", "copywriting", "metin yazarligi"], "Pazarlama ve satış"),
    T("crm", "CRM kullanımı", SKILL, ["crm", "salesforce", "hubspot"], "Pazarlama ve satış"),

    # ---- satış / müşteri ----
    T("field_sales", "Saha satış", EXPERIENCE,
      ["saha satis", "field sales", "bayi ziyaret", "musteri portfoy"], "Pazarlama ve satış", True),
    T("b2b_sales", "B2B satış", EXPERIENCE,
      ["b2b satis", "b2b sales", "kurumsal satis", "key account"], "Pazarlama ve satış", True),
    # GENEL SATIŞ — ölçümde en büyük tek boşluk. Okunamayan TR ilanlarında
    # "satis" 352, "danismani" 187 kez geçiyordu ama sözlükte yalnızca *saha* ve
    # *B2B* satış vardı: "Satış Danışmanı" başlıklı bir ilan HİÇBİR token
    # tutmuyordu. Biçimler eksiz gövde: ek toleransı "danismanı",
    # "temsilcisi", "elemanları" çekimlerini yakalar.
    T("sales", "Satış / mağaza danışmanlığı", EXPERIENCE,
      ["satis danisman", "satis temsilcisi", "satis temsilci", "satis eleman",
       "satis personel", "satis sorumlu", "satis uzman", "sales representative",
       "sales consultant", "musteri danisman"], "Pazarlama ve satış", True),
    T("retail", "Perakende / mağaza", EXPERIENCE,
      ["magaza", "perakende", "kasiyer", "retail", "reyon",
       "verkaufer", "verkäufer", "einzelhandel", "kassierer"], "Perakende ve hizmet", True),
    T("call_center", "Çağrı merkezi / müşteri hizmetleri", EXPERIENCE,
      ["cagri merkezi", "call center", "musteri hizmetleri", "customer support",
       "customer service"], "Perakende ve hizmet", True),

    # ---- muhasebe / finans / idari ----
    T("accounting", "Muhasebe", EXPERIENCE,
      ["muhasebe", "accounting", "mizan", "beyanname", "cari hesap", "mutabakat"], "Muhasebe ve finans", True),
    T("acc_software", "Muhasebe programı", SKILL,
      ["logo", "mikro", "netsis", "luca", "eta", "nebim", "sap"], "Muhasebe ve finans"),
    T("efatura", "E-fatura / e-defter", SKILL, ["e-fatura", "e fatura", "e-defter", "e-arsiv"], "Muhasebe ve finans"),
    T("smmm", "SMMM ruhsatı", LICENSE, ["smmm", "mali musavir", "serbest muhasebeci"], "Muhasebe ve finans"),
    T("payroll", "Bordro ve özlük", EXPERIENCE,
      ["bordro", "ozluk", "payroll", "sgk bildirim", "ise giris cikis"], "İnsan kaynakları", True),
    T("hr", "İnsan kaynakları", EXPERIENCE,
      ["insan kaynaklari", "human resources", "ise alim", "recruitment", "talent acquisition"], "İnsan kaynakları", True),
    T("office_admin", "Ofis / idari işler", EXPERIENCE,
      ["idari isler", "ofis yoneticisi", "executive assistant", "yonetici asistani",
       "sekreter", "office manager"], "İnsan kaynakları", True),
    T("excel", "Excel / ofis programları", SKILL,
      ["excel", "ms office", "microsoft office", "spreadsheet"], "İnsan kaynakları"),

    # ---- lojistik / sürücü / depo ----
    T("license_b", "B sınıfı ehliyet", LICENSE, ["b sinifi ehliyet", "b class licence",
      "binek ehliyet", "fuhrerschein klasse b", "driving licence"], "Lojistik ve taşımacılık"),
    T("license_ce", "C+E sınıfı ehliyet", LICENSE,
      ["c+e", "ce sinifi", "agir vasita ehliyet", "tir ehliyet"], "Lojistik ve taşımacılık"),
    T("license_d", "D sınıfı ehliyet", LICENSE, ["d sinifi ehliyet", "otobus ehliyet"], "Lojistik ve taşımacılık"),
    T("src", "SRC mesleki yeterlilik belgesi", LICENSE, ["src", "src1", "src-1", "src2", "src-2"], "Lojistik ve taşımacılık"),
    T("psiko", "Psikoteknik belgesi", CERT, ["psikoteknik"], "Lojistik ve taşımacılık"),
    T("heavy_driving", "Ağır vasıta sürücülüğü", EXPERIENCE,
      ["agir vasita", "tir soforu", "uzun yol", "cekici", "kamyon soforu",
       "berufskraftfahrer", "kraftfahrer", "lkw fahrer", "truck driver"], "Lojistik ve taşımacılık", True),
    T("warehouse", "Depo / stok", EXPERIENCE,
      ["depo", "stok", "sevkiyat", "wms", "mal kabul", "istifleme",
       "lagerhelfer", "lagerist", "lagerarbeit", "kommissionierer", "warehouse"], "Lojistik ve taşımacılık", True),
    T("forklift", "Forklift operatörlüğü", CERT,
      ["forklift", "istif makinesi", "transpalet", "staplerschein", "gabelstapler"], "Lojistik ve taşımacılık"),
    T("courier", "Kurye / dağıtım", EXPERIENCE,
      ["kurye", "dagitim", "motokurye", "teslimat",
       "zusteller", "auslieferungsfahrer", "kurierfahrer"], "Lojistik ve taşımacılık", True),
    T("foreign_trade", "Dış ticaret / gümrük", EXPERIENCE,
      ["dis ticaret", "gumruk", "ithalat", "ihracat", "import", "export"], "Lojistik ve taşımacılık", True),

    # ---- üretim / teknik ----
    T("cnc", "CNC / torna", EXPERIENCE, ["cnc", "torna", "freze", "talasli imalat"], "Üretim ve teknik", True),
    T("welding", "Kaynakçılık", EXPERIENCE, ["kaynakci", "kaynak operator", "argon kaynak",
      "gazalti", "schweisser", "schweißer", "welder", "mig mag"], "Üretim ve teknik", True),
    T("electrician", "Elektrik / elektrikçi", EXPERIENCE,
      ["elektrikci", "elektrik teknisyeni", "pano montaj", "electrician",
       "elektroniker", "elektriker", "elektrofachkraft"], "Üretim ve teknik", True),
    T("mechanic", "Makine bakım / mekanik", EXPERIENCE,
      ["bakim onarim", "mekanik bakim", "makine bakim", "maintenance technician"], "Üretim ve teknik", True),
    T("production", "Üretim bandı / imalat", EXPERIENCE,
      ["uretim bandi", "imalat", "montaj hatti", "production line", "operator",
       "produktionshelfer", "produktionsmitarbeiter", "fertigung", "montage"], "Üretim ve teknik", True),
    T("quality", "Kalite kontrol", EXPERIENCE,
      ["kalite kontrol", "quality control", "iso 9001", "kalite guvence"], "Üretim ve teknik", True),
    # İSG İKİ AYRI ŞEY ve tek token'da birleşikti. Sonuç canlı persona
    # testinde ölçüldü: kaynakçı profilinin 24 sonucunun 11'i (%46) "İş
    # Güvenliği Uzmanı" ilanıydı — kullanıcının giremeyeceği, ayrı bakanlık
    # sınavı ve teknik diploma isteyen ruhsatlı bir meslek.
    #
    # 17.858 ilan üzerinde ölçüm: eski token 174 ilanda tutuyordu, bunun
    # **128'i (%74)** yalnızca "is sagligi" biçiminden geliyordu. Yani
    # "İş sağlığı ve güvenliği kurallarına uymak" KALIP METNİ. Eşleşenler
    # arasında Aşçı, Garson, Temizlik Görevlisi, Forklift Operatörü vardı.
    #
    # Şu biçimler bu yüzden KASITLI olarak dışarıda:
    #   * "is sagligi" → alanın adı, bir nitelik değil; neredeyse her mavi
    #     yaka ilanının kalıp metninde geçiyor
    #   * çıplak "isg" → "İSG kurallarına uygun çalışmak" kalıbı (24 ilan)
    #   * "osgb" → İŞVEREN türü (Ortak Sağlık Güvenlik Birimi), çalışanın
    #     niteliği değil. Kaybı yok: OSGB ilanları zaten "iş güvenliği uzmanı"
    #     arıyor ve aşağıdaki token onları tutuyor.
    #
    # Anahtar `osgb` olarak KALDI. Yeniden adlandırmak semantik olarak daha
    # doğru olurdu ama katalogda bulunmayan anahtar API sınırında sessizce
    # atlanıyor (main.py `_profile_from_payload`) — yani bu chip'i işaretlemiş
    # her kullanıcının beyanı kaybolurdu. "İş güvenliği sertifikası" işaretleyen
    # kişi zaten eğitim sertifikasını kastediyordu; niyeti korumak, iç isim
    # güzelliğinden önemli.
    # ÖLÇÜM NOTU: bu token bugünkü korpusta (17.858 ilan) **0** ilanla eşleşiyor
    # ve bu bir darlık hatası DEĞİL. 6331 sayılı kanunda temel İSG eğitimini
    # işveren vermek zorunda, dolayısıyla adaydan istemiyor. Chip listede
    # kalıyor: kullanıcı beyan edebilsin ve İŞKUR gibi kaynaklar eklendiğinde
    # (orada daha sık isteniyor) kendiliğinden çalışsın. Sıfır eşleşen bir chip
    # zarar vermez; aşırı geniş bir chip 128 yanlış eşleşme veriyordu.
    T("osgb", "İş güvenliği eğitim sertifikası", CERT,
      ["is guvenligi sertifikasi", "is guvenligi belgesi", "is guvenligi egitimi",
       "isg sertifikasi", "isg belgesi", "isg egitimi"], "Üretim ve teknik"),
    # Ruhsatlı MESLEK: bakanlık sınavı + A/B/C sınıf belgesi + teknik diploma.
    # LICENSE olduğu için doğrulanmadan "karşılanıyor" sayılmaz (D-012).
    T("isg_specialist", "İş güvenliği uzmanlığı belgesi (A/B/C)", LICENSE,
      ["is guvenligi uzmani", "isg uzmani", "is guvenligi uzmanligi",
       "is sagligi ve guvenligi uzmani", "a sinifi is guvenligi",
       "b sinifi is guvenligi", "c sinifi is guvenligi"], "Üretim ve teknik"),

    # ---- sağlık ----
    T("nurse_license", "Hemşirelik tescil belgesi", LICENSE,
      ["hemsirelik tescil", "hemsire tescil", "tescil belgesi"], "Sağlık"),
    T("nursing", "Hemşirelik deneyimi", EXPERIENCE, ["hemsire", "hemsirelik", "nurse"], "Sağlık", True),
    T("icu", "Yoğun bakım", EXPERIENCE, ["yogun bakim", "reanimasyon", "intensive care"], "Sağlık", True),
    T("caregiver", "Hasta / yaşlı bakımı", EXPERIENCE,
      ["hasta bakici", "yasli bakim", "refakatci", "caregiver",
       "pflegehelfer", "pflegekraft", "altenpflege", "pflegefachkraft"], "Sağlık", True),
    T("pharmacy", "Eczane / kalfa", EXPERIENCE, ["eczane", "eczaci kalfasi", "pharmacy"], "Sağlık", True),

    # ---- yiyecek / turizm / hizmet ----
    T("cook", "Aşçılık / mutfak", EXPERIENCE,
      ["asci", "ascibasi", "mutfak", "chef", "kitchen", "sef",
       "koch", "küchenhilfe", "kuechenhilfe", "beikoch"], "Yiyecek ve turizm", True),
    T("waiter", "Servis / garsonluk", EXPERIENCE,
      ["garson", "servis elemani", "waiter", "barista", "komi",
       "servicekraft", "kellner", "bedienung"], "Yiyecek ve turizm", True),
    T("housekeeping", "Kat hizmetleri / temizlik", EXPERIENCE,
      # Biçimler EKSİZ gövde olarak yazılır: "temizlik gorevli" ek toleransıyla
      # "gorevlisi" ve "gorevlileri"nin ikisini de yakalar. Tam çekimli
      # ("gorevlisi") yazılırsa yalnızca o tek çekim tutar — ölçümde
      # "Temizlik Görevlileri" ilanları bu yüzden okunamıyordu.
      ["kat hizmetleri", "temizlik gorevli", "temizlik personel", "housekeeping",
       "reinigungskraft", "gebäudereiniger", "gebaeudereiniger"], "Yiyecek ve turizm", True),
    T("front_desk", "Ön büro / resepsiyon", EXPERIENCE,
      ["on buro", "resepsiyon", "front desk", "receptionist"], "Yiyecek ve turizm", True),
    T("food_safety", "Hijyen belgesi", CERT, ["hijyen belgesi", "haccp", "food safety"], "Yiyecek ve turizm"),

    # ---- eğitim ----
    T("teaching", "Öğretmenlik / eğitmenlik", EXPERIENCE,
      ["ogretmen", "egitmen", "teacher", "instructor", "ogretim gorevlisi"], "Eğitim", True),

    # ---- güvenlik ----
    T("security_guard", "Özel güvenlik görevlisi", LICENSE,
      ["ozel guvenlik", "guvenlik gorevlisi", "silahsiz guvenlik", "silahli guvenlik"], "Güvenlik"),

    # ---- diller ----
    T("english", "İngilizce", LANGUAGE,
      ["ingilizce", "english", "fluent in english", "ileri seviye ingilizce"], "Dil"),
    T("german", "Almanca", LANGUAGE, ["almanca", "german", "deutsch", "deutschkenntnisse"], "Dil"),
    T("arabic", "Arapça", LANGUAGE, ["arapca", "arabic"], "Dil"),
    T("russian", "Rusça", LANGUAGE, ["rusca", "russian"], "Dil"),

    # ---- eğitim düzeyi ----
    T("bachelor", "Lisans mezuniyeti", EDUCATION,
      # "üniversitelerin ilgili bölümlerinden mezun" Türkiye ilanlarının en
       # yaygın diploma ifadesi (okunamayan ilanlarda "bolumlerinden" 124,
       # "universitelerin" 181 kez) ve hiçbir biçim onu tutmuyordu.
      ["lisans mezunu", "bachelor", "universite mezunu", "bachelor's degree", "4 yillik",
       "bolumlerinden mezun", "bolumunden mezun", "fakulte mezunu",
       "lisans egitimi", "lisans duzeyinde"], "Eğitim düzeyi"),
    T("highschool", "Lise mezuniyeti", EDUCATION,
      ["lise mezunu", "high school", "meslek lisesi"], "Eğitim düzeyi"),
    T("masters", "Yüksek lisans", EDUCATION, ["yuksek lisans", "master's", "msc", "mba"], "Eğitim düzeyi"),

    # ---- çalışma düzeni ----
    T("shift_work", "Vardiyalı çalışma", SHIFT, ["vardiya", "shift work", "vardiyali"], "Çalışma düzeni"),
    T("night_shift", "Gece vardiyası", SHIFT, ["gece vardiyasi", "night shift", "nobet"], "Çalışma düzeni"),
    T("travel", "Seyahat engeli olmaması", SHIFT,
      ["seyahat engeli", "seyahat edebilecek", "willing to travel"], "Çalışma düzeni"),
)

BY_KEY: dict[str, Term] = {t.key: t for t in TERMS}


# --------------------------------------------------------------------------
# Tarama motoru
# --------------------------------------------------------------------------
#
# Naif yaklaşım — her terim için ayrı regex — ilan başına ~360 arama demekti ve
# desenler her çağrıda yeniden derleniyordu; 2445 ilanlık korpusta tek başına
# ~60 saniye tutuyordu. Tek büyük alternasyona derlemek de yetmedi: Python'un
# `re` motoru trie kurmaz, metnin **her konumunda** bütün alternatifleri sırayla
# dener.
#
# Çözüm iki aşamalı. Metin bir kez kelimelere ayrılır; tek kelimelik biçimler
# (çoğunluk: "python", "forklift", "docker") doğrudan sözlük araması olur.
# Çok kelimeli veya simge içeren biçimler ("makine ogrenmesi", "c++", "e-fatura")
# için önce **ucuz bir ön-eleme** yapılır: biçimin ilk kelimesi metinde hiç
# geçmiyorsa regex hiç çalıştırılmaz.

_WORD = re.compile(r"[a-z0-9]+")


def _probe(folded_form: str) -> str | None:
    """Biçimin ucuz ön-eleme anahtarı: ilk alfanümerik kelime."""
    m = _WORD.search(folded_form)
    return m.group(0) if m else None


def _form_pattern(folded: str) -> re.Pattern[str]:
    """Çok kelimeli biçimin deseni — sonda Türkçe ek zincirine izin verir.

    "gazalti kaynak" biçimi "gazaltı kaynakçısı" metnini de bulmalı.
    """
    head = r"\b" if folded[0].isalnum() else r"(?<!\w)"
    if not folded[-1].isalnum():
        return re.compile(head + re.escape(folded) + r"(?!\w)")
    tail = (_TR_EK_ZINCIR if len(folded) >= _EK_MIN_UZUNLUK else "") + r"\b"
    return re.compile(head + re.escape(folded) + tail)


#: tek kelimelik biçim → terim (doğrudan sözlük araması)
_SIMPLE: dict[str, Term] = {}
#: (probe, derlenmiş desen, biçim, terim) — yalnızca probe tutarsa çalıştırılır
_COMPLEX: list[tuple[str | None, re.Pattern[str], str, Term]] = []

for _t in TERMS:
    for _raw in _t.forms:
        _f = fold(_raw)
        if _WORD.fullmatch(_f):
            _SIMPLE.setdefault(_f, _t)
        else:
            _COMPLEX.append((_probe(_f), _form_pattern(_f), _f, _t))

# Yasal uygunluk şartları (D-013): tespit edilir, **skora girmez**, profile yazılmaz.
LEGAL_ELIGIBILITY_PATTERNS: dict[str, re.Pattern[str]] = {
    "military": re.compile(r"\baskerli\w*|\bmilitary service\b"),
    "age_limit": re.compile(r"\b\d{2}\s*ya[sş]\w*\s*(alti|ustu|arasi)|\bage\s+\d{2}\b"),
    "health": re.compile(r"\bsaglik raporu\b|\bsaglik durumu\b|\bengel\w*\s*durum"),
}

_YEARS = re.compile(r"(?:en az\s*)?(\d{1,2})\s*(?:\+)?\s*(?:yil|yillik|years?|yrs?)")


@dataclass(frozen=True, slots=True)
class Hit:
    term: Term
    position: int
    matched_form: str
    years: float | None = None


def scan(text: str, *, want_years: bool = True) -> list[Hit]:
    """Metni sözlüğe karşı tarar. İlan metni ve CV metni **aynı** fonksiyondan geçer.

    Metin bir kez taranır; her terim için **ilk** eşleşme tutulur. Yıl bilgisi
    yalnızca eşleşmenin yakınında geçiyorsa alınır; bulunamazsa ``None``
    bırakılır — tahmin üretilmez.
    """
    low = fold(text)
    first: dict[str, tuple[int, str]] = {}

    # 1) Metni bir kez kelimelere ayır; her kelimenin ilk konumunu tut.
    where: dict[str, int] = {}
    for m in _WORD.finditer(low):
        where.setdefault(m.group(0), m.start())

    # 2) Tek kelimelik biçimler: sözlük araması, regex yok.
    for word, pos in where.items():
        # Kelimenin kendisi ve ek soyulmuş gövdeleri denenir (bkz. _govdeler):
        # "ogretmeni" → "ogretmen". Sözlük tam eşitlik aradığı için eklemeli
        # her biçim eşleşmeden kaçıyordu.
        term = None
        for g in _govdeler(word):
            term = _SIMPLE.get(g)
            if term is not None:
                break
        if term is not None:
            prev = first.get(term.key)
            if prev is None or pos < prev[0]:
                first[term.key] = (pos, word)

    # 3) Çok kelimeli / simgeli biçimler: yalnızca ön-eleme tutarsa regex.
    for probe, pattern, form, term in _COMPLEX:
        if probe is not None and probe not in where:
            continue
        m = pattern.search(low)
        if m is None:
            continue
        prev = first.get(term.key)
        if prev is None or m.start() < prev[0]:
            first[term.key] = (m.start(), form)

    hits: list[Hit] = []
    for key, (pos, form) in first.items():
        term = BY_KEY[key]
        years = None
        if want_years and term.asks_years:
            window = low[max(0, pos - 90): pos + 90]
            ym = _YEARS.search(window)
            if ym:
                years = float(ym.group(1))
        hits.append(Hit(term=term, position=pos, matched_form=form, years=years))

    # Sonuç sırası TERMS sırasını izler; çağıranlar deterministik çıktı bekler.
    order = {t.key: i for i, t in enumerate(TERMS)}
    hits.sort(key=lambda h: order[h.term.key])
    return hits


def find_legal_eligibility(text: str) -> list[str]:
    """Yasal uygunluk şartlarını tespit eder (D-013). Skora **girmez**."""
    low = fold(text)
    return sorted(k for k, pat in LEGAL_ELIGIBILITY_PATTERNS.items() if pat.search(low))


def clusters() -> list[str]:
    seen: list[str] = []
    for t in TERMS:
        if t.cluster not in seen:
            seen.append(t.cluster)
    return seen
