"""API sözleşmesi ve kullanıcıya görünen invariant'lar.

Buradaki testler iş kuralını tekrar doğrulamaz (o core'un işi); API katmanının
kuralları **taşıyıp taşımadığını** doğrular. Bir kural HTTP sınırında kaybolursa
core testleri geçmeye devam eder ama kullanıcı yanlış şey görür.
"""

from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient

from isuygun_api.cv import suggest_facts
from isuygun_api.main import app
from isuygun_api.store import STORE


@pytest.fixture(scope="module", autouse=True)
def _offline_corpus():
    """Testler **ağa çıkmaz**.

    Canlı ingest gerçek ATS uçlarına gider ve ``Crawl-delay: 1`` uygular;
    testlerde bunu yapmak hem yavaş hem de dış servise gereksiz yük olurdu.
    Ayrıca test sonucunun uzak bir sunucunun o anki içeriğine bağlı olması
    testi kırılgan yapar.
    """
    STORE.load(live=False)
    yield


@pytest.fixture()
def client():
    # lifespan'i tetiklemeden: korpus zaten yüklendi.
    c = TestClient(app)
    STORE.reset_profile()
    yield c
    STORE.reset_profile()


def _add(c, key, **kw):
    r = c.post("/api/profile/facts", json={"key": key, **kw})
    assert r.status_code == 200, r.text
    return r.json()


# --------------------------------------------------------------------------
# Feed — D-019'un HTTP sınırındaki karşılığı
# --------------------------------------------------------------------------


def test_empty_profile_produces_no_bands(client):
    """Boş profilde hiçbir ilan bantlanmaz — hiçbiri "zayıf" da denmez."""
    f = client.get("/api/feed").json()
    assert f["profile_is_empty"] is True
    assert f["evaluated"] == []
    assert len(f["unevaluated"]) > 0
    assert all(j["band"] is None for j in f["unevaluated"])


def test_unevaluated_never_labelled_weak(client):
    """Değerlendirilemeyen ilan zayıf eşleşme etiketi TAŞIYAMAZ."""
    f = client.get("/api/feed").json()
    for j in f["unevaluated"]:
        assert j["band_label"] is None
        assert j["worth_applying_rule"] in ("insufficient_data", "listing_only")


def test_profile_moves_job_into_evaluated(client):
    _add(client, "heavy_driving", years=6)
    f = client.get("/api/feed").json()
    titles = [j["title"] for j in f["evaluated"]]
    assert any("Şoför" in t for t in titles)


def test_no_percentage_in_any_payload(client):
    """D-005: hiçbir uçtan yüzde veya sayısal skor sızmamalı."""
    _add(client, "heavy_driving", years=6)
    feed = client.get("/api/feed").json()
    blob = str(feed)
    for j in feed["evaluated"] + feed["unevaluated"]:
        blob += str(client.get(f"/api/jobs/{j['job_id']}").json())
    assert "%" not in blob
    # skor alanı API'de hiç yer almamalı
    assert "score" not in blob.lower()


# --------------------------------------------------------------------------
# D-012 — doğrulama kapısı HTTP üzerinden atlanamaz
# --------------------------------------------------------------------------


def test_asserted_licence_does_not_count(client):
    """Beyan edilen ehliyet "karşılanıyor" sayılmaz."""
    p = _add(client, "license_ce")
    fact = next(f for f in p["facts"] if f["key"] == "license_ce")
    assert fact["verification"] == "user_asserted"
    assert fact["counts_as_present"] is False


def test_verified_flag_on_create_is_honoured(client):
    p = _add(client, "license_ce", verified=True)
    fact = next(f for f in p["facts"] if f["key"] == "license_ce")
    assert fact["counts_as_present"] is True


def test_verification_endpoint_promotes_fact(client):
    _add(client, "license_ce")
    p = client.post("/api/profile/facts/license_ce/verify").json()
    fact = next(f for f in p["facts"] if f["key"] == "license_ce")
    assert fact["verification"] == "verified"


def test_unverified_gate_forces_conditional_band(client):
    """Belge doğrulanmadan bant güçlü olamaz; detayda uyarı görünür."""
    _add(client, "heavy_driving", years=6)
    _add(client, "src", verified=True)
    _add(client, "psiko", verified=True)
    _add(client, "license_ce")  # kasten doğrulanmamış

    job = next(j for j in client.get("/api/feed").json()["evaluated"]
               if "Şoför" in j["title"])
    assert job["band"] == "cond"

    d = client.get(f"/api/jobs/{job['job_id']}").json()
    assert d["verification_notice"] is not None
    assert any(l["action_label"] == "Belgeyi doğrula" for l in d["unknown"])


def test_verifying_everything_reaches_strong(client):
    for k in ("heavy_driving",):
        _add(client, k, years=6)
    for k in ("src", "psiko", "license_ce"):
        _add(client, k, verified=True)
    job = next(j for j in client.get("/api/feed").json()["evaluated"]
               if "Şoför" in j["title"])
    assert job["band"] == "strong"


# --------------------------------------------------------------------------
# D-013 / D-015 / D-006
# --------------------------------------------------------------------------


def test_legal_eligibility_not_in_catalog(client):
    """Askerlik gibi şartlar profil kataloğunda YER ALMAZ."""
    keys = [i["key"] for i in client.get("/api/catalog").json()]
    assert not any(k.startswith("legal_") for k in keys)


def test_legal_eligibility_cannot_be_written(client):
    r = client.post("/api/profile/facts", json={"key": "legal_military"})
    assert r.status_code in (400, 404)


def test_legal_eligibility_shown_as_notice(client):
    """Skora girmez ama kullanıcıya bilgi olarak gösterilir."""
    feed = client.get("/api/feed").json()
    job = next(j for j in feed["evaluated"] + feed["unevaluated"]
               if "Saha Satış" in j["title"])
    d = client.get(f"/api/jobs/{job['job_id']}").json()
    assert d["legal_eligibility_notices"]
    assert "değerlendirmeye katılmaz" in d["legal_eligibility_notices"][0]


def test_public_sector_is_listing_only(client):
    feed = client.get("/api/feed").json()
    job = next(j for j in feed["unevaluated"] if j["is_public_sector"])
    assert job["band"] is None and job["listing_only"] is True
    d = client.get(f"/api/jobs/{job['job_id']}").json()
    assert d["listing_only_note"] is not None


# --------------------------------------------------------------------------
# CV — öneri kayıt değildir + sensitive imhası
# --------------------------------------------------------------------------

_CV = """
MEHMET Y. - Ozgecmis
Dogum tarihi: 12.05.1988
Medeni hal: Evli
Kuzey Nakliyat - Agir vasita soforu, 8 yil agir vasita tecrubesi.
C+E sinifi ehliyet. SRC-1 mesleki yeterlilik belgesi. Psikoteknik belgesi - gecerli.
"""


def test_cv_suggestions_are_not_written_to_profile(client, monkeypatch):
    monkeypatch.setattr("isuygun_api.cv.extract_text", lambda d: (_CV, 1))
    r = client.post("/api/profile/cv",
                    files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")})
    body = r.json()
    assert body["written_to_profile"] is False
    assert body["suggestions"]
    assert client.get("/api/profile").json()["facts"] == []


def test_cv_discards_sensitive_fields(client, monkeypatch):
    monkeypatch.setattr("isuygun_api.cv.extract_text", lambda d: (_CV, 1))
    body = client.post("/api/profile/cv",
                       files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}).json()
    assert "dogum_tarihi" in body["discarded_sensitive"]
    assert "medeni_hal" in body["discarded_sensitive"]
    # İçerik DEĞİL, yalnızca alan adı raporlanır.
    assert "1988" not in str(body)
    assert "Evli" not in str(body)


def test_cv_rejects_non_pdf(client):
    r = client.post("/api/profile/cv",
                    files={"file": ("cv.docx", io.BytesIO(b"x"), "application/msword")})
    assert r.status_code == 400


def test_cv_does_not_suggest_unrelated_professions():
    """Şoför CV'sine hemşirelik lisansı önerilmemeli.

    "belgesi" gibi genel kelimeler tek başına kanıt sayılınca tam bu oluyordu.
    """
    labels = [s.label for s in suggest_facts(_CV, STORE.catalog)]
    assert not any("Hemşire" in l for l in labels), labels
    assert any("C+E" in l for l in labels)


def test_cv_matching_survives_missing_turkish_characters():
    """CV'ler "Agir vasita" diye de yazılıyor; katlama olmadan hiç eşleşmiyordu."""
    keys = [s.key for s in suggest_facts(_CV, STORE.catalog)]
    assert "heavy_driving" in keys


def test_cv_does_not_match_inside_words():
    """Regresyon: "gecerli" içindeki "gece" gece vardiyası önerdiriyordu."""
    keys = [s.key for s in suggest_facts(_CV, STORE.catalog)]
    assert "night_shift" not in keys


# --------------------------------------------------------------------------
# Kaynak şeffaflığı
# --------------------------------------------------------------------------


def test_open_sources_are_only_permitted_apis(client):
    """D-020: ağ erişimi açık olan her kaynak izinli bir API olmalı.

    Gate açıldı ama sınırsız açılmadı: yalnızca `api` erişim yöntemli, izni
    `allowed` kayıtlar çekilebilir. Bir gün buraya `html` erişimli bir kayıt
    sızarsa bu test düşer.
    """
    rows = client.get("/api/sources").json()
    for s in rows:
        if not s["may_fetch_network"]:
            continue
        assert s["scraping_permission"] == "allowed", s["source_id"]
        assert s["access_method"] in ("api", "feed", "fixture"), s["source_id"]


def test_rejected_platforms_remain_closed(client):
    """LinkedIn ve Indeed kapalı kalmalı — gate açılışı onları kapsamadı."""
    rows = {s["name"]: s for s in client.get("/api/sources").json()}
    for name in ("LinkedIn", "Indeed Türkiye"):
        assert rows[name]["may_fetch_network"] is False
        assert rows[name]["scraping_permission"] == "rejected"


def test_openapi_schema_is_generated(client):
    """TS tipleri bundan üretiliyor; şema bozulursa arayüz sessizce sapar."""
    schema = client.get("/openapi.json").json()
    assert "FeedOut" in schema["components"]["schemas"]
    assert "/api/feed" in schema["paths"]


# ---------------------------------------------------------------------------
# Arama ucu (D-031)
# ---------------------------------------------------------------------------


def test_search_returns_job_ids(client):
    r = client.get("/api/search", params={"q": "engineer"})
    assert r.status_code == 200
    assert isinstance(r.json()["job_ids"], list)


def test_empty_search_returns_nothing_not_everything(client):
    """Boş sorgu **hiçbir şey** döner, her şeyi değil.

    Her şeyi dönseydi arayüz "arama aktif" sanıp tüm listeyi filtre sonucu
    gibi gösterirdi; sorgu kutusu boşken arama hiç uygulanmamalı.
    """
    assert client.get("/api/search", params={"q": ""}).json()["job_ids"] == []
    assert client.get("/api/search", params={"q": "   "}).json()["job_ids"] == []


def test_search_reports_how_query_was_understood(client):
    """Operatörün nasıl anlaşıldığı geri bildirilir — kullanıcı yanlış
    yazdığında sessizce farklı bir arama yapılmış olmasın."""
    d = client.get("/api/search", params={"q": '"data engineer" -stajyer python'}).json()
    assert d["phrases"] == ["data engineer"]
    assert d["excluded"] == ["stajyer"]
    assert d["terms"] == ["python"]


def test_search_exclusion_narrows_results(client):
    wide = client.get("/api/search", params={"q": "engineer"}).json()["job_ids"]
    narrow = client.get("/api/search", params={"q": "engineer -senior"}).json()["job_ids"]
    assert set(narrow) <= set(wide)


def test_feed_exposes_new_axes(client):
    d = client.get("/api/feed").json()
    for key in ("arrangements", "experience_levels", "employment_types", "currencies"):
        assert key in d["facets"], key
    every = d["evaluated"] + d["unevaluated"]
    if every:
        j = every[0]
        for key in ("work_arrangement", "employment_type", "experience_level",
                    "salary_currency", "salary_min_yearly"):
            assert key in j, key


# ---------------------------------------------------------------------------
# Profil açma önerileri (D-034)
# ---------------------------------------------------------------------------


def test_unlock_suggestions_are_actionable(client):
    """Öneriler tıklanabilir olmalı: profile yazılamayan bir alanı önermek,
    kullanıcıya yapamayacağı bir eylem göstermek olurdu."""
    for s in client.get("/api/profile/unlock-suggestions").json():
        r = client.post("/api/profile/facts", json={"key": s["key"]})
        assert r.status_code == 200, s["key"]


def test_unlock_suggestions_exclude_what_profile_already_has(client):
    first = client.get("/api/profile/unlock-suggestions").json()
    if not first:
        pytest.skip("korpusta öneri üretecek şart yok")
    client.post("/api/profile/facts", json={"key": first[0]["key"]})
    after = {s["key"] for s in client.get("/api/profile/unlock-suggestions").json()}
    assert first[0]["key"] not in after


def test_unlock_suggestions_are_ranked(client):
    got = [s["unlocks"] for s in client.get("/api/profile/unlock-suggestions").json()]
    assert got == sorted(got, reverse=True)


def test_adding_a_suggested_field_actually_unlocks_listings(client):
    """İddianın kendisi test edilir: "+N" dedikten sonra gerçekten
    değerlendirilemeyen sayısı düşmeli.

    Sapmaya izin verilir (aynı rol iki listede temsil edilebiliyor) ama
    **yön** ve **büyüklük mertebesi** tutmalı — bunlar tutmazsa sayı
    kullanıcıyı yanlış yönlendiriyor demektir.
    """
    suggestions = client.get("/api/profile/unlock-suggestions").json()
    if not suggestions or suggestions[0]["unlocks"] < 5:
        pytest.skip("anlamlı ölçüm için yeterli korpus yok")
    target = suggestions[0]

    before = len(client.get("/api/feed").json()["unevaluated"])
    client.post("/api/profile/facts", json={"key": target["key"]})
    after = len(client.get("/api/feed").json()["unevaluated"])

    actual = before - after
    assert actual > 0, "öneri hiçbir ilanı açmadı"
    assert actual <= target["unlocks"], "iddia gerçekleşenden düşük olamaz"
    assert actual >= target["unlocks"] * 0.85, (
        f"iddia {target['unlocks']}, gerçekleşen {actual} — sapma çok büyük"
    )


def test_role_key_shared_between_grouping_and_counting():
    """Gruplama ve sayım aynı kuralı kullanmalı; iki yerde ayrı yazılsaydı
    biri değişince diğeri sessizce sapardı."""
    from isuygun_api.main import _role_key

    assert _role_key("ACME A.Ş.", "Yazılım Uzmanı") == _role_key("acme a.ş.", "yazılım uzmanı")
