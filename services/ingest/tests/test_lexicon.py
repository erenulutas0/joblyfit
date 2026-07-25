"""Sözlük bütünlüğü.

Sözlük, ilan tarafı ile CV tarafının **ortak dilidir**. Buradaki bir bozulma
sessizdir: yinelenen anahtar bir terimi gölgeler, çok kısa bir yüzey biçimi
alakasız metinlerle eşleşir, tanınmayan bir kategori gate mantığını atlar.
Hiçbiri hata vermez; yalnızca kullanıcı yanlış eşleşme görür.
"""

from __future__ import annotations

import collections

import pytest

from isuygun_core.domain import GATE_RELEVANT_CATEGORIES, NON_DISCRIMINATIVE_CATEGORIES
from isuygun_ingest import lexicon as L

_KNOWN_CATEGORIES = {
    L.SKILL, L.LICENSE, L.CERT, L.EXPERIENCE, L.LANGUAGE, L.EDUCATION, L.SHIFT,
}


def test_term_keys_are_unique():
    """Yinelenen anahtar, ikinci terimi `BY_KEY`'de görünmez yapar."""
    dupes = [k for k, n in collections.Counter(t.key for t in L.TERMS).items() if n > 1]
    assert dupes == [], dupes


def test_by_key_covers_every_term():
    assert len(L.BY_KEY) == len(L.TERMS)


def test_no_surface_form_belongs_to_two_terms():
    """Aynı biçim iki terime aitse hangisinin kazandığı sıraya bağlı kalır."""
    counts = collections.Counter(L.fold(f) for t in L.TERMS for f in t.forms)
    shared = [f for f, n in counts.items() if n > 1]
    assert shared == [], shared


def test_categories_are_known():
    """Tanınmayan kategori, gate ve ayırt edicilik mantığını sessizce atlar."""
    unknown = {t.category for t in L.TERMS} - _KNOWN_CATEGORIES
    assert unknown == set(), unknown


def test_gate_categories_are_represented():
    """En az bir gate alanı olmalı; yoksa D-012 hiç devreye girmez."""
    assert {t.category for t in L.TERMS} & GATE_RELEVANT_CATEGORIES


def test_non_discriminative_categories_exist_in_lexicon():
    """D-021 bu kategorilere dayanıyor; sözlükte karşılıkları olmalı."""
    assert {t.category for t in L.TERMS} & NON_DISCRIMINATIVE_CATEGORIES


def test_surface_forms_are_long_enough():
    """Çok kısa biçimler rastgele metinle eşleşir.

    İki karakterlik biçimler yalnızca ayırt edici teknoloji kısaltmaları için
    kabul edilir; liste açıkça yazılır ki yenisi fark edilmeden eklenmesin.
    """
    allowed_short = {"js", "ts", "c#", "go", "qa", "bi", "ui"}
    too_short = {
        L.fold(f) for t in L.TERMS for f in t.forms
        if len(L.fold(f)) <= 2 and L.fold(f) not in allowed_short
    }
    assert too_short == set(), too_short


def test_labels_are_turkish_facing_and_unique():
    """Etiketler kullanıcıya gösteriliyor; tekrar eden etiket kafa karıştırır."""
    dupes = [l for l, n in collections.Counter(t.label for t in L.TERMS).items() if n > 1]
    assert dupes == [], dupes


def test_every_term_has_at_least_one_form():
    empty = [t.key for t in L.TERMS if not t.forms]
    assert empty == [], empty


def test_clusters_are_stable_labels():
    """Küme adları arayüzde filtre olarak görünüyor; boş olamaz."""
    assert all(t.cluster.strip() for t in L.TERMS)
    assert len(L.clusters()) >= 5


# --------------------------------------------------------------------------
# Tarama davranışı
# --------------------------------------------------------------------------


def test_scan_respects_word_boundaries():
    """Regresyon: "geçerli" içindeki "gece" gece vardiyası önerdiriyordu."""
    keys = {h.term.key for h in L.scan("Psikoteknik belgesi geçerli")}
    assert "night_shift" not in keys


def test_scan_folds_turkish_and_german():
    """Aynı terim üç dilde de bulunmalı; kaynaklar karışık dilde."""
    assert "warehouse" in {h.term.key for h in L.scan("Depo görevlisi aranıyor")}
    assert "warehouse" in {h.term.key for h in L.scan("Lagerhelfer gesucht")}
    assert "warehouse" in {h.term.key for h in L.scan("Warehouse associate")}


def test_scan_reports_first_position_only():
    """Bir terim birden çok geçse de tek kayıt üretir; konum ilk geçiştir."""
    hits = [h for h in L.scan("Python. Sonra yine Python.") if h.term.key == "python"]
    assert len(hits) == 1
    assert hits[0].position == 0


def test_scan_reads_years_only_near_the_match():
    """Uzaktaki bir sayı yıl bilgisi sanılmamalı."""
    near = L.scan("5 yıl Python deneyimi")
    assert next(h for h in near if h.term.key == "python").years == 5
    far = L.scan("Python bilgisi. " + "dolgu " * 60 + "12 yıl sektör tecrübesi")
    assert next(h for h in far if h.term.key == "python").years is None


def test_scan_is_deterministic():
    text = "Python, Docker, İngilizce, lisans mezunu"
    assert [h.term.key for h in L.scan(text)] == [h.term.key for h in L.scan(text)]


def test_legal_eligibility_detected_but_separate():
    """D-013: askerlik şartı tespit edilir ama normal terim olarak dönmez."""
    assert "military" in L.find_legal_eligibility("Askerliğini tamamlamış olmak")
    assert not any(h.term.key.startswith("legal") for h in L.scan("askerliğini tamamlamış"))


# --------------------------------------------------------------------------
# İSG: sertifika ≠ uzmanlık (canlı persona testinden çıkan düzeltme)
# --------------------------------------------------------------------------
# Tek token'ken kaynakçı profilinin 24 sonucunun 11'i "İş Güvenliği Uzmanı"
# ilanıydı. 17.858 ilanlık ölçümde token 174 ilanda tutuyordu ve 128'i sırf
# "iş sağlığı ve güvenliği kurallarına uymak" kalıp metninden geliyordu.

#: Türkiye ilanlarında neredeyse standart olan güvenlik kalıp metinleri.
#: Bunlar bir NİTELİK beyan etmez; hiçbir İSG token'ını tetiklememeli.
ISG_KALIP_METINLERI = (
    "İş sağlığı ve güvenliği kurallarına uymak",
    "İSG kurallarına uygun çalışmak",
    "İş sağlığı ve güvenliği talimatlarına riayet etmek",
    "Şirketin iş sağlığı ve güvenliği politikalarına uyum",
)


@pytest.mark.parametrize("metin", ISG_KALIP_METINLERI)
def test_isg_kalip_metni_hicbir_isg_tokenini_tetiklemez(metin):
    """Kalıp metin nitelik değildir — Aşçı/Garson ilanlarını İSG'ye bağlıyordu."""
    anahtarlar = {h.term.key for h in L.scan(metin)}
    assert "osgb" not in anahtarlar, f"eğitim sertifikası kalıp metne takıldı: {metin!r}"
    assert "isg_specialist" not in anahtarlar, f"uzmanlık kalıp metne takıldı: {metin!r}"


@pytest.mark.parametrize("metin", [
    "İş Güvenliği Uzmanı aranıyor",
    "C sınıfı iş güvenliği uzmanı",
    "İSG uzmanı olarak görevlendirilmek üzere",
    "İş sağlığı ve güvenliği uzmanı (B sınıfı)",
])
def test_uzmanlik_ilanlari_uzmanlik_belgesine_baglanir(metin):
    anahtarlar = {h.term.key for h in L.scan(metin)}
    assert "isg_specialist" in anahtarlar, f"uzmanlık ilanı tanınmadı: {metin!r}"
    # Ruhsatlı meslek, çalışanın temel eğitim sertifikasıyla KARIŞMAMALI.
    assert "osgb" not in anahtarlar


@pytest.mark.parametrize("metin", [
    "İş güvenliği sertifikası olan adaylar",
    "İSG eğitimi almış olmak",
    "İş güvenliği belgesi tercih edilir",
])
def test_egitim_sertifikasi_ayri_tokene_baglanir(metin):
    anahtarlar = {h.term.key for h in L.scan(metin)}
    assert "osgb" in anahtarlar, f"eğitim sertifikası tanınmadı: {metin!r}"
    assert "isg_specialist" not in anahtarlar, \
        "temel sertifika, ruhsatlı uzmanlık sanılıyor — kullanıcıyı giremeyeceği " \
        "mesleğe yönlendirir"


def test_osgb_isveren_turu_nitelik_sayilmaz():
    """OSGB bir işveren türü (Ortak Sağlık Güvenlik Birimi), çalışan niteliği değil."""
    anahtarlar = {h.term.key for h in L.scan("Bir OSGB firmasında görevlendirilmek üzere")}
    assert "osgb" not in anahtarlar
    assert "isg_specialist" not in anahtarlar


def test_uzmanlik_belgesi_dogrulama_kapisina_tabidir():
    """Ruhsatlı meslek: doğrulanmadan "karşılanıyor" sayılamaz (D-012)."""
    uzman = next(t for t in L.TERMS if t.key == "isg_specialist")
    egitim = next(t for t in L.TERMS if t.key == "osgb")
    assert uzman.category in GATE_RELEVANT_CATEGORIES
    # Temel eğitim sertifikası yasal kapı DEĞİL — kaynakçı olmanın önkoşulu değil.
    assert egitim.category not in GATE_RELEVANT_CATEGORIES


# ---------------------------------------------------------------------------
# Türkçe ek toleransı — ÇIKARIM tarafının koruması
# ---------------------------------------------------------------------------
# Golden set şartları DONMUŞ hâlde tutar (`golden/set.json` → `ilan.requirements`),
# yani eşleştirme kalibrasyonunu ölçer ama çıkarımı HİÇ sınamaz. Sözlükteki bir
# gerileme oradan sessizce geçer. Buradaki vakalar o boşluğu kapatır.
#
# Kök neden: desenler sonda `\b` istiyordu ve Türkçe eklemeli bir dil.
# Ölçüm (5.930 TR ilanı): hiç şart okunamayan ilan %44 → %24,5.

EKLI_BICIMLER = [
    ("Matematik Öğretmeni aranıyor", "teaching"),
    ("Öğretmenlik deneyimi olan", "teaching"),
    ("Temizlik Görevlileri alınacaktır", "housekeeping"),
    ("Temizlik Personeli aranıyor", "housekeeping"),
    ("Mağazada çalışacak eleman", "retail"),
    ("Aşçısı aranıyor", "cook"),
    ("Garsonlar alınacak", "waiter"),
    ("Hemşireler için ilan", "nursing"),
    ("Kasiyerler alınacak", "retail"),
    ("Vardiyalı çalışma", "shift_work"),
    ("Tornacı aranıyor", "cnc"),
    ("Kuryelik yapabilecek", "courier"),
    ("Depoda görevlendirilmek üzere", "warehouse"),
    ("Bordrolama işlemleri", "payroll"),
    ("Almancası iyi olan", "german"),
    ("İmalatta deneyimli", "production"),
]


@pytest.mark.parametrize("metin,anahtar", EKLI_BICIMLER)
def test_turkce_ekli_bicimler_de_bulunur(metin, anahtar):
    assert anahtar in {h.term.key for h in L.scan(metin)}, \
        f"ek almış biçim okunamadı: {metin!r} → {anahtar}"


#: Ek toleransının ASLA üretmemesi gereken eşleşmeler. Sondaki sınırı tamamen
#: kaldırmak bunların hepsini yanlış eşleştirirdi; bu yüzden yalnızca gerçek
#: Türkçe eklerine izin verilir ve 4 harften kısa biçimler katı kalır.
TEHLIKELI_ESLESMELER = [
    ("important to note", "foreign_trade"),   # import + "ant" ek DEĞİL
    ("javascript bilgisi", "java"),           # java + "script"
    ("komisyon oranı yüksek", "waiter"),      # komi + "syon"
    ("gitti ve geldi", "git"),                # git + "ti"
    ("mikrobiyoloji laboratuvarı", "acc_software"),   # mikro + "biyoloji"
    ("sefer sayısı artacak", "cook"),         # sef + "er"
    ("Sema Hanım ile görüşün", "digital_marketing"),  # sem + "a" (özel ad)
    ("sapa bir yerde", "acc_software"),       # sap + "a"
    ("semt pazarı kurulur", "digital_marketing"),
    ("etap etap teslim edilecek", "acc_software"),
]


@pytest.mark.parametrize("metin,olmamali", TEHLIKELI_ESLESMELER)
def test_ek_toleransi_yanlis_eslesme_uretmez(metin, olmamali):
    assert olmamali not in {h.term.key for h in L.scan(metin)}, \
        f"ek toleransı yanlış eşleşme üretti: {metin!r} → {olmamali}"


def test_govde_uretimi_cok_kisa_govde_uretmez():
    """"sema" → "sem" ÜRETİLMEZ: Sema özel ad, SEM pazarlama terimi.

    Kısa gövdeye inmek, ek toleransının en büyük riski. Eşik kalkarsa bu test
    kırılır ve sebebi burada yazılıdır.
    """
    assert "sem" not in L._govdeler("sema")
    assert "sef" not in L._govdeler("sefa")
    # Yeterince uzun gövdeler ÜRETİLİR.
    assert "ogretmen" in L._govdeler("ogretmeni")
    assert "garson" in L._govdeler("garsonlar")


def test_genel_satis_tokeni_var():
    """Ölçümdeki en büyük tek boşluk: "Satış Danışmanı" hiçbir token tutmuyordu.

    Sözlükte yalnızca *saha* ve *B2B* satış vardı; okunamayan TR ilanlarında
    "satis" 352, "danismani" 187 kez geçiyordu.
    """
    for metin in ("Satış Danışmanı", "Satış Temsilcisi aranıyor",
                  "Mağaza Satış Elemanı", "Satış Uzmanı"):
        assert "sales" in {h.term.key for h in L.scan(metin)}, metin


def test_universite_mezuniyeti_yaygin_ifadeyle_de_bulunur():
    """Türkiye ilanlarının en yaygın diploma ifadesi tutmuyordu."""
    for metin in ("Üniversitelerin ilgili bölümlerinden mezun",
                  "İlgili bölümünden mezun olmak",
                  "Fakülte mezunu adaylar"):
        assert "bachelor" in {h.term.key for h in L.scan(metin)}, metin


# ---------------------------------------------------------------------------
# D-076 — eksik meslek aileleri
# ---------------------------------------------------------------------------
# Olcum: test edilen 41 meslekten 38'inde HIC token yoktu. Tam aileler
# eksikti — ev hizmetleri, muhendislik, saglik meslekleri, insaat zanaatlari,
# kuaforluk. "Insaat" kumesi arayuzde tanimliydi ama lexicon'da tek token'i
# yoktu. Okunamayan TR ilani: %24,5 -> %18,2.

YENI_MESLEKLER = [
    ("Ev Yardımcısı Arıyoruz", "home_help"),
    ("Ev temizliği yapabilecek yardımcı", "home_help"),
    ("Çocuk bakıcısı aranıyor", "child_care"),
    ("Yaşlı bakıcısı aranıyor", "caregiver"),
    ("Üretim Elemanı alınacaktır", "production"),
    ("Üretim Montaj Elemanı", "production"),
    ("Makine Mühendisi", "mech_eng"),
    ("İnşaat Mühendisi", "civil_eng"),
    ("İç Mimar aranıyor", "civil_eng"),
    ("Elektrik Mühendisi", "elec_eng"),
    ("Endüstri Mühendisi", "industrial_eng"),
    ("Şoför aranıyor", "driver"),
    ("Fizyoterapist", "physio"),
    ("Diyetisyen", "dietitian"),
    ("Psikolog", "psychologist"),
    ("Aile Hekimi", "physician"),
    ("Veteriner Hekim", "vet"),
    ("Pazarlama Uzmanı", "marketing"),
    ("Ofis temizliği yapacak personel", "housekeeping"),
    ("Şantiye elemanı", "construction"),
    ("Sıvacı aranıyor", "plaster"),
    ("Kalıpçı", "formwork"),
    ("Demirci", "rebar"),
    ("Boyacı", "painter"),
    ("Marangoz", "carpenter"),
    ("Tesisatçı", "plumber"),
    ("İklimlendirme teknikeri", "hvac"),
    ("Oto Kaporta Ustası", "auto_repair"),
    ("Kuaför aranıyor", "hairdresser"),
    ("Terzi", "tailor"),
    ("Bahçıvan", "gardener"),
    ("Otopark Görevlisi", "valet"),
    ("Barmen", "bartender"),
    ("Pastacı", "pastry"),
    ("Bulaşıkçı", "dishwasher"),
]


@pytest.mark.parametrize("metin,anahtar", YENI_MESLEKLER)
def test_eksik_meslek_aileleri_artik_taniniyor(metin, anahtar):
    assert anahtar in {h.term.key for h in L.scan(metin)}, \
        f"meslek tanınmadı: {metin!r} → {anahtar}"


#: Kapsami genisletirken OLCUMDE yakalanan yanlis eslesmeler. Her biri gercek
#: bir ilanda gorulmustur; daraltma bu yuzden yapildi.
YENI_TOKEN_TEHLIKELERI = [
    # "mimar" ciplak halde yazilimdaki "architect" ile cakisiyordu.
    ("JAVA DEVELOPER — software architect pozisyonu", "civil_eng"),
    # "hekim" ciplak halde meslektas olarak anilmayi da tutuyordu.
    ("Diş Hekimi Asistanı aranıyor", "physician"),
    ("Acil Servis Hemşiresi — hekim ile çalışacak", "physician"),
    # "cocuk gelisimi" akademik bir bolum adi, bakicilik degil.
    ("Anaokulu Öğretmeni — çocuk gelişimi mezunu", "child_care"),
    # Ciplak "veteriner" sirketin SEKTORUNU tutuyordu.
    ("Veteriner ürünleri saha satış temsilcisi", "vet"),
]


@pytest.mark.parametrize("metin,olmamali", YENI_TOKEN_TEHLIKELERI)
def test_yeni_tokenlar_olcumdeki_yanlis_eslesmeleri_tekrarlamaz(metin, olmamali):
    assert olmamali not in {h.term.key for h in L.scan(metin)}, \
        f"daraltma geri alınmış — yanlış eşleşme geri geldi: {metin!r}"


def test_insaat_kumesi_artik_bos_degil():
    """Arayüz bu kümeyi mavi yakada listeliyordu ama lexicon'da tek token yoktu.

    Boş bir küme, kullanıcıya var olmayan bir kapsama sözü verir.
    """
    insaat = [t.key for t in L.TERMS if t.cluster == "İnşaat"]
    assert len(insaat) >= 6, f"inşaat kümesi hâlâ zayıf: {insaat}"
