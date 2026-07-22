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


@pytest.mark.parametrize("title", [
    "Senior Software Engineer", "Sr. Data Analyst", "Staff Engineer",
    "Principal Scientist", "Head of Marketing", "Director of Sales",
    "Kıdemli Yazılım Geliştirici",
])
def test_detects_senior(title):
    assert detect(title=title).experience_level == "senior"


@pytest.mark.parametrize("title", [
    "Junior Developer", "Software Engineering Intern", "New Graduate Engineer",
    "Entry-Level Analyst", "Stajyer Mühendis",
])
def test_detects_entry(title):
    assert detect(title=title).experience_level == "entry"


@pytest.mark.parametrize("title", ["Account Manager", "Product Manager",
                                   "Engineering Manager", "Customer Success Manager"])
def test_manager_is_not_a_seniority_signal(title):
    """"Manager" bir rol türüdür, kıdem değil.

    Dahil edildiğinde korpusun %54'ü "kıdemli" görünüyordu. Yarıdan fazlasını
    seçen bir filtre hiçbir şey seçmiyor demektir.
    """
    assert detect(title=title).experience_level != "senior"


def test_lead_generation_is_not_seniority():
    """"Lead Generation Specialist" bir satış rolüdür, lider pozisyonu değil."""
    assert detect(title="Lead Generation Specialist").experience_level != "senior"
    assert detect(title="Engineering Lead").experience_level == "senior"


def test_entry_wins_over_senior_in_title():
    assert detect(title="Junior Staff Accountant").experience_level == "entry"


def test_seniority_read_from_title_only():
    """Açıklamada "kıdemli mühendislerle çalışacaksın" geçmesi ilanı kıdemli
    yapmaz — başlık işverenin kendi etiketidir."""
    m = detect(title="Software Engineer",
               description="You will work closely with senior and principal engineers.")
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
