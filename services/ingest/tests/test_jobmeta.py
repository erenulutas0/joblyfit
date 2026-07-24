"""Çalışma biçimi / istihdam türü / deneyim seviyesi testleri.

Buradaki testlerin çoğu gerçek korpusta **yakalanmış** yanlış pozitiflerden
geliyor. Her biri bir kullanıcı zararına karşılık gelir: ilanı "uzaktan" diye
etiketlemek, ofise gitmesi gereken bir işe uzaktan sanarak başvurtturur.
"""

from __future__ import annotations

import pytest

from isuygun_ingest import jobmeta


def detect(title="Engineer", city="Berlin", description=""):
    return jobmeta.detect(title=title, city=city, description=description)


# ---------------------------------------------------------------------------
# Çalışma biçimi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("desc", [
    "This is a fully remote position.",
    "We are a remote-first company and this role is remote.",
    "You will work remotely from anywhere in the EU.",
    "100% remote opportunity.",
    "Bu pozisyon tamamen uzaktan çalışma şeklindedir.",
])
def test_detects_remote(desc):
    assert detect(description=desc).work_arrangement == "remote"


@pytest.mark.parametrize("city", ["Remote", "Remote, USA", "Colorado, USA, Remote",
                                  "Anywhere", "İstanbul (Uzaktan)"])
def test_city_field_is_strongest_evidence(city):
    """Konum alanına "Remote" yazan işveren yorumu bize bırakmamıştır.

    "Colorado, USA, Remote" vakası gerçek korpustan: yalnızca baştaki "Remote"
    aranınca bu ilanlar kaçıyor ve şirketin "hybrid workplace" cümlesi
    yüzünden **hibrit** görünüyorlardı.
    """
    assert detect(city=city).work_arrangement == "remote"


@pytest.mark.parametrize("desc", [
    "Hybrid work model: 3 days a week in the office.",
    "This is a hybrid role based in Amsterdam.",
    "You will be expected to be in office 4 days per week.",
    "Hibrit çalışma modeli uygulanmaktadır.",
])
def test_detects_hybrid(desc):
    assert detect(description=desc).work_arrangement == "hybrid"


def test_hybrid_wins_over_remote():
    """Hibrit ilanlar "remote" kelimesini de kullanır.

    Sıra ters kurulursa haftada 3 gün ofise gitmesi gereken bir iş "uzaktan"
    görünür — kullanıcı taşınma kararı bile verebilir.
    """
    desc = "Hybrid work model with 2 days remote and 3 days in the office."
    assert detect(description=desc).work_arrangement == "hybrid"


@pytest.mark.parametrize("desc", [
    # Teknik terim olarak "remote" — yazılım ilanlarının her yerinde geçer.
    "You will debug remote servers and manage Remote Desktop sessions.",
    "Experience with remote procedure calls (RPC) is required.",
    "Build hybrid cloud infrastructure across AWS and GCP.",
    "Our hybrid search combines vector and keyword retrieval.",
])
def test_technical_usage_is_not_a_work_arrangement(desc):
    assert detect(description=desc).work_arrangement is None


@pytest.mark.parametrize("desc", [
    "We support all working styles, including fully office-based, fully remote, or hybrid.",
    "The number of hybrid, office-based, and remote workers will vary from team to team.",
])
def test_company_policy_sentences_are_not_this_role(desc):
    """Şirketin seçenek listesi, bu ilanın biçimi değildir.

    Gerçek korpusta yakalandı: iki ilan yalnızca bu cümle yüzünden "uzaktan"
    etiketlenmişti.
    """
    assert detect(description=desc).work_arrangement is None


def test_policy_sentence_does_not_hide_a_real_statement():
    """Politika cümlesi elenir ama ilanın kendi beyanı elenmez."""
    desc = ("We support fully office-based, fully remote, or hybrid styles. "
            "For this particular opening: this is a fully remote position.")
    assert detect(description=desc).work_arrangement == "remote"


def test_unspecified_is_not_onsite():
    """İşaret yoksa ``None``. Bu "ofisten çalışılacak" demek değildir.

    Varsayılana düşmek, ilanın söylemediği bir şeyi söylemiş gibi göstermek
    olurdu (D-011'in aynı mantığı).
    """
    assert detect(description="Join our team and build great products.").work_arrangement is None


# ---------------------------------------------------------------------------
# İstihdam türü
# ---------------------------------------------------------------------------


def test_detects_employment_types():
    assert detect(description="This is a part-time role.").employment_type == "part_time"
    assert detect(title="Software Engineering Intern").employment_type == "internship"
    assert detect(description="Fixed-term contract for 12 months.").employment_type == "contract"


@pytest.mark.parametrize("desc", [
    "You will develop smart contract auditing tools.",
    "Experience with contract testing (Pact) required.",
])
def test_technical_contract_is_not_employment_type(desc):
    assert detect(description=desc).employment_type is None


def test_full_time_is_never_claimed():
    """Tam zamanlı **çıkarılmaz**: neredeyse hiçbir ilan yazmıyor çünkü
    varsayılan, ve yazmayanı tam zamanlı saymak kanıt değil varsayımdır."""
    m = detect(description="This is a full-time permanent position.")
    assert m.employment_type != "full_time"


# ---------------------------------------------------------------------------
# Deneyim seviyesi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("title", "level"), [
    ("Software Engineering Intern", "intern"),
    ("Stajyer Mühendis", "intern"),
    ("Junior Developer", "junior"),
    ("New Graduate Engineer", "junior"),
    ("Entry-Level Analyst", "junior"),
    ("Software Engineer II", "mid"),
    ("Mid-Level Designer", "mid"),
    ("Senior Software Engineer", "senior"),
    ("Sr. Data Analyst", "senior"),
    ("Kıdemli Yazılım Geliştirici", "senior"),
    ("Staff Engineer", "lead"),
    ("Principal Scientist", "lead"),
    ("Engineering Lead", "lead"),
    ("Solutions Architect", "architect"),
    ("Head of Marketing", "executive"),
    ("Director of Sales", "executive"),
    ("VP of Engineering", "executive"),
])
def test_detects_ladder_level(title, level):
    assert detect(title=title).experience_level == level


@pytest.mark.parametrize("title", ["Account Manager", "Product Manager",
                                   "Engineering Manager", "Customer Success Manager"])
def test_manager_is_not_a_seniority_signal(title):
    """"Manager" bir rol türüdür, kıdem değil.

    Dahil edildiğinde korpusun yarısı "kıdemli" görünüyordu. Yarıdan fazlasını
    seçen bir filtre hiçbir şey seçmiyor demektir (D-032).
    """
    assert detect(title=title).experience_level is None


def test_lead_generation_is_not_seniority():
    """"Lead Generation Specialist" bir satış rolüdür, lider pozisyonu değil."""
    assert detect(title="Lead Generation Specialist").experience_level is None
    assert detect(title="Engineering Lead").experience_level == "lead"


def test_entry_beats_higher_rungs_in_title():
    """Giriş işaretleri üst basamakları ezer: kullanıcı "Junior Staff X"e
    baktığında giriş rolü arıyordur, merdivenin tepesini değil."""
    assert detect(title="Junior Staff Accountant").experience_level == "junior"


def test_highest_rung_wins_among_high_levels():
    """Üst basamaklar arasında en yüksek olan kazanır."""
    assert detect(title="Senior Director").experience_level == "executive"
    assert detect(title="Senior Staff Engineer").experience_level == "lead"
    assert detect(title="Senior Solutions Architect").experience_level == "architect"


def test_seniority_read_from_title_only():
    """Açıklamada "kıdemli mühendislerle çalışacaksın" geçmesi ilanı kıdemli
    yapmaz — başlık işverenin kendi etiketidir.

    Not (D-052): açıklamadaki *çıplak kelimeler* hâlâ sayılmaz. Yalnızca
    sayılı ve çıpalı deneyim şartı ("en az 3 yıl deneyim") basamak türetir —
    bkz. :func:`test_years_in_description_derive_level`.
    """
    m = detect(title="Software Engineer",
               description="You will work closely with senior and principal engineers.")
    assert m.experience_level is None


# --- D-052: Türkçe esnaf merdiveni ----------------------------------------

@pytest.mark.parametrize("title,level", [
    ("Çırak Aranıyor", "intern"),
    ("Oto Elektrik Çırağı", "intern"),
    ("Kalfa Kaynakçı", "mid"),
    ("Pastane Ustası", "senior"),
    ("Pprc Tesisat Ustası", "senior"),
    ("Usta Makine Ressamı", "senior"),
    ("Şantiye Şefi", "lead"),
    ("Teknik Şef", "lead"),
    ("Enjeksiyon Vardiya Amiri", "lead"),
    ("Vasıfsız Eleman", "junior"),
])
def test_turkish_trades_ladder(title, level):
    """çırak → kalfa → usta Türkiye'nin esnaf merdivenidir ve mavi yakanın
    intern/mid/senior karşılığıdır. Ölçüm: bunlar eklenmeden Türkçe başlıkların
    yalnızca %3'ü işaretliydi (İngilizce %39)."""
    assert detect(title=title).experience_level == level


@pytest.mark.parametrize("title", [
    "Mustafa Bey Market Elemanı",   # "usta" Mustafa'nın içinde — kelime başı değil
    "Sefer Planlama Uzmanı",        # "sef" sefer'in içinde
    "Amiral Gemisi Mağaza Elemanı", # "amir" amiral'in içinde
])
def test_turkish_stems_do_not_bleed_into_other_words(title):
    """Gövde eşlemesi sonek yakalamalı ama kelime içine sızmamalı.

    Bunlar gerçek tuzaklar: ``\\busta\\w*`` yazılsa "Mustafa" kıdemli olurdu,
    ``\\bsef\\w*`` yazılsa "Sefer Planlama" amirlik sayılırdı.
    """
    assert detect(title=title).experience_level is None


@pytest.mark.parametrize("title", [
    "Mesul Müdür", "Teknik Müdür",      # müdür = rol türü (D-032 gerekçesi)
    "Yönetici Asistanı",                # asistan; üst düzey değil
    "Uzman Öğretici",                   # "uzman" her unvana eklenir
    "E-Ticaretten Sorumlu Müdür",
    "Deneyimli Aşçı",                   # deneyimli ama HANGİ basamak belirsiz
    "Tecrübeli Satış Personeli",
])
def test_turkish_role_words_are_not_seniority(title):
    """Ölçülüp **reddedilen** kelimeler. Hepsi korpusta sık geçiyor ama kıdem
    ayırt etmiyor; basamağa yazmak uydurma kesinlik olurdu (D-011).

    "deneyimli" gerçek bir sinyaldir — ama 2 yıl da 20 yıl da olabilir. Sayı
    verildiğinde yıl kuralı devreye girer, verilmediğinde "belirtilmemiş" kalır.
    """
    assert detect(title=title).experience_level is None


# --- D-052: açıklamadaki deneyim yılından türetme --------------------------

@pytest.mark.parametrize("desc,level", [
    ("En az 3 yıl deneyim aranmaktadır.", "mid"),
    ("3 years of experience required", "mid"),
    ("Minimum 5 yıl tecrübe şarttır.", "senior"),
    ("8+ years experience", "senior"),
    ("1 yıl deneyimli adaylar", "junior"),
    ("0-1 yıl deneyim", "junior"),
])
def test_years_in_description_derive_level(desc, level):
    """Başlık sessizse açıklamadaki sayılı deneyim şartı basamak verir.
    Ölçüm: bu kural tüm korpusta 1261 ilanı daha işaretledi."""
    assert detect(title="Personel Alınacaktır", description=desc).experience_level == level


def test_title_beats_years_in_description():
    """Başlık işverenin kendi etiketidir; açıklamadaki yıla göre üstündür."""
    m = detect(title="Stajyer Mühendis",
               description="En az 5 yıl deneyim gereklidir.")
    assert m.experience_level == "intern"


@pytest.mark.parametrize("desc", [
    "1958 yılında kurulan firmamız sektörde güven vermektedir.",
    "58 yıllık deneyimimizle hizmetinizdeyiz.",
    "40 yıllık tecrübemizle Türkiye'nin lideriyiz.",
])
def test_company_own_experience_is_not_a_requirement(desc):
    """En sinsi yanlış pozitif: şirketin kendi tecrübesi.

    Çıpa ("deneyim" kelimesi) bunu elemiyor çünkü cümlede gerçekten geçiyor —
    eleyen şey 15 yıl üst sınırıdır. Sınır olmadan "58 yıllık deneyimimizle"
    ilanı kıdemli gösteriyordu (ölçümde 14 ilan).
    """
    assert detect(title="Personel", description=desc).experience_level is None


def test_years_needs_anchor_word():
    """Çıpasız sayı sayılmaz: "2 yıl sonra taşınacağız" kıdem şartı değildir."""
    m = detect(title="Personel",
               description="Ofisimiz 2 yıl sonra yeni binaya taşınacaktır.")
    assert m.experience_level is None


def test_jobmeta_is_in_cache_fingerprint():
    from isuygun_ingest import cache

    assert "jobmeta.py" in cache._LOGIC_FILES


def test_pipeline_attaches_axes():
    from isuygun_ingest.pipeline import RawPosting, normalize

    p = normalize(RawPosting(
        source_id="src-fixture-001", source_posting_ref="ref",
        url="https://example.invalid/x", title="Senior Backend Engineer",
        employer="Acme", city="Remote, Germany",
        description="This is a fully remote position.",
    ), adapter_version="test")
    assert p.work_arrangement == "remote"
    assert p.experience_level == "senior"
