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

    @property
    def needle_patterns(self) -> tuple[re.Pattern[str], ...]:
        return tuple(_compile(f) for f in self.forms)


def _compile(form: str) -> re.Pattern[str]:
    """Kelime sınırına saygılı desen.

    Düz ``in`` araması kelime içi eşleşiyordu: "geçerli" içindeki "gece" yüzünden
    şoför CV'sine gece vardiyası öneriliyordu.
    """
    f = fold(form)
    # "c++" / "c#" gibi terimlerde sondaki \b işe yaramaz — sembolle biterler.
    tail = r"(?!\w)" if not f[-1].isalnum() else r"\b"
    head = r"(?<!\w)" if not f[0].isalnum() else r"\b"
    return re.compile(head + re.escape(f) + tail)


def T(key, label, category, forms, cluster="genel", asks_years=False) -> Term:
    return Term(key, label, category, tuple(forms), cluster, asks_years)


# --------------------------------------------------------------------------
# Sözlük
# --------------------------------------------------------------------------
# Yüzey biçimleri hem Türkçe hem İngilizce yazılır: ilanlar sıklıkla İngilizce,
# CV'ler sıklıkla Türkçedir. `fold()` her ikisini de aksansızlaştırır.

TERMS: tuple[Term, ...] = (
    # ---- yazılım / veri ----
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
    T("retail", "Perakende / mağaza", EXPERIENCE,
      ["magaza", "perakende", "kasiyer", "retail", "reyon"], "Perakende ve hizmet", True),
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
    T("license_b", "B sınıfı ehliyet", LICENSE, ["b sinifi ehliyet", "b class licence", "binek ehliyet"], "Lojistik ve taşımacılık"),
    T("license_ce", "C+E sınıfı ehliyet", LICENSE,
      ["c+e", "ce sinifi", "agir vasita ehliyet", "tir ehliyet"], "Lojistik ve taşımacılık"),
    T("license_d", "D sınıfı ehliyet", LICENSE, ["d sinifi ehliyet", "otobus ehliyet"], "Lojistik ve taşımacılık"),
    T("src", "SRC mesleki yeterlilik belgesi", LICENSE, ["src", "src1", "src-1", "src2", "src-2"], "Lojistik ve taşımacılık"),
    T("psiko", "Psikoteknik belgesi", CERT, ["psikoteknik"], "Lojistik ve taşımacılık"),
    T("heavy_driving", "Ağır vasıta sürücülüğü", EXPERIENCE,
      ["agir vasita", "tir soforu", "uzun yol", "cekici", "kamyon soforu"], "Lojistik ve taşımacılık", True),
    T("warehouse", "Depo / stok", EXPERIENCE,
      ["depo", "stok", "sevkiyat", "wms", "mal kabul", "istifleme"], "Lojistik ve taşımacılık", True),
    T("forklift", "Forklift operatörlüğü", CERT,
      ["forklift", "istif makinesi", "transpalet"], "Lojistik ve taşımacılık"),
    T("courier", "Kurye / dağıtım", EXPERIENCE,
      ["kurye", "dagitim", "motokurye", "teslimat"], "Lojistik ve taşımacılık", True),
    T("foreign_trade", "Dış ticaret / gümrük", EXPERIENCE,
      ["dis ticaret", "gumruk", "ithalat", "ihracat", "import", "export"], "Lojistik ve taşımacılık", True),

    # ---- üretim / teknik ----
    T("cnc", "CNC / torna", EXPERIENCE, ["cnc", "torna", "freze", "talasli imalat"], "Üretim ve teknik", True),
    T("welding", "Kaynakçılık", EXPERIENCE, ["kaynakci", "kaynak operator", "argon kaynak", "gazalti"], "Üretim ve teknik", True),
    T("electrician", "Elektrik / elektrikçi", EXPERIENCE,
      ["elektrikci", "elektrik teknisyeni", "pano montaj", "electrician"], "Üretim ve teknik", True),
    T("mechanic", "Makine bakım / mekanik", EXPERIENCE,
      ["bakim onarim", "mekanik bakim", "makine bakim", "maintenance technician"], "Üretim ve teknik", True),
    T("production", "Üretim bandı / imalat", EXPERIENCE,
      ["uretim bandi", "imalat", "montaj hatti", "production line", "operator"], "Üretim ve teknik", True),
    T("quality", "Kalite kontrol", EXPERIENCE,
      ["kalite kontrol", "quality control", "iso 9001", "kalite guvence"], "Üretim ve teknik", True),
    T("osgb", "İş güvenliği sertifikası", CERT,
      ["is guvenligi uzmani", "isg", "osgb", "is sagligi"], "Üretim ve teknik"),

    # ---- sağlık ----
    T("nurse_license", "Hemşirelik tescil belgesi", LICENSE,
      ["hemsirelik tescil", "hemsire tescil", "tescil belgesi"], "Sağlık"),
    T("nursing", "Hemşirelik deneyimi", EXPERIENCE, ["hemsire", "hemsirelik", "nurse"], "Sağlık", True),
    T("icu", "Yoğun bakım", EXPERIENCE, ["yogun bakim", "reanimasyon", "intensive care"], "Sağlık", True),
    T("caregiver", "Hasta / yaşlı bakımı", EXPERIENCE,
      ["hasta bakici", "yasli bakim", "refakatci", "caregiver"], "Sağlık", True),
    T("pharmacy", "Eczane / kalfa", EXPERIENCE, ["eczane", "eczaci kalfasi", "pharmacy"], "Sağlık", True),

    # ---- yiyecek / turizm / hizmet ----
    T("cook", "Aşçılık / mutfak", EXPERIENCE,
      ["asci", "ascibasi", "mutfak", "chef", "kitchen", "sef"], "Yiyecek ve turizm", True),
    T("waiter", "Servis / garsonluk", EXPERIENCE,
      ["garson", "servis elemani", "waiter", "barista", "komi"], "Yiyecek ve turizm", True),
    T("housekeeping", "Kat hizmetleri / temizlik", EXPERIENCE,
      ["kat hizmetleri", "temizlik gorevlisi", "housekeeping"], "Yiyecek ve turizm", True),
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
    T("german", "Almanca", LANGUAGE, ["almanca", "german", "deutsch"], "Dil"),
    T("arabic", "Arapça", LANGUAGE, ["arapca", "arabic"], "Dil"),
    T("russian", "Rusça", LANGUAGE, ["rusca", "russian"], "Dil"),

    # ---- eğitim düzeyi ----
    T("bachelor", "Lisans mezuniyeti", EDUCATION,
      ["lisans mezunu", "bachelor", "universite mezunu", "bachelor's degree", "4 yillik"], "Eğitim düzeyi"),
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

    Yıl bilgisi yalnızca eşleşmenin yakınında geçiyorsa alınır; bulunamazsa
    ``None`` bırakılır — tahmin üretilmez.
    """
    low = fold(text)
    hits: list[Hit] = []
    for term in TERMS:
        best: tuple[int, str] | None = None
        for pat, form in zip(term.needle_patterns, term.forms):
            m = pat.search(low)
            if m and (best is None or m.start() < best[0]):
                best = (m.start(), form)
        if best is None:
            continue
        pos, form = best
        years = None
        if want_years and term.asks_years:
            window = low[max(0, pos - 90): pos + 90]
            ym = _YEARS.search(window)
            if ym:
                years = float(ym.group(1))
        hits.append(Hit(term=term, position=pos, matched_form=form, years=years))
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
