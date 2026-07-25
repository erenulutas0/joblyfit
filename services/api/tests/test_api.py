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


# ---------------------------------------------------------------------------
# CV → öneri → profil → iş önerisi zinciri (uçtan uca)
# ---------------------------------------------------------------------------


def test_cv_extracts_years_of_experience():
    """CV'deki "8 yil agir vasita tecrubesi" **süre** olarak okunmalı.

    Süre okunmazsa ilan "en az 5 yıl" istediğinde sonuç `unknown/missing_duration`
    olur — kullanıcı sahip olduğu deneyimi kanıtlayamaz (D-026).
    """
    hits = {s.key: s.years for s in suggest_facts(_CV, STORE.catalog)}
    assert hits.get("heavy_driving") == 8, hits


def test_cv_suggestion_accepted_becomes_profile_fact(client, monkeypatch):
    """Zincirin can alıcı halkası: öneri onaylanınca profile geçer ve
    bekleyenlerden düşer."""
    monkeypatch.setattr("isuygun_api.cv.extract_text", lambda d: (_CV, 1))
    body = client.post("/api/profile/cv",
                       files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}).json()
    key = body["suggestions"][0]["key"]

    client.post("/api/profile/facts", json={"key": key})

    profile = client.get("/api/profile").json()
    assert key in {f["key"] for f in profile["facts"]}, "öneri profile geçmedi"
    assert key not in {s["key"] for s in profile["pending_cv_suggestions"]}, \
        "onaylanan öneri bekleyenlerde kaldı"


def test_cv_driven_profile_improves_recommendations(client, monkeypatch):
    """CV'den gelen alanlar kabul edilince değerlendirilebilen ilan sayısı artmalı.

    "CV yükledim ama hiçbir şey değişmedi" şikâyetinin regresyon testi.
    """
    before = len(client.get("/api/feed").json()["evaluated"])

    monkeypatch.setattr("isuygun_api.cv.extract_text", lambda d: (_CV, 1))
    body = client.post("/api/profile/cv",
                       files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}).json()
    for s in body["suggestions"]:
        client.post("/api/profile/facts", json={"key": s["key"]})

    after = len(client.get("/api/feed").json()["evaluated"])
    assert after >= before, "CV kabul edildi ama değerlendirilen ilan sayısı düştü"


def test_experience_filter_axis_is_exposed_and_consistent(client):
    """Kıdem ekseni facet'te sayaçlı gelmeli ve sayaçlar gösterilen listeyle
    tutarlı olmalı (D-030: rozet sayısı = filtre sonucu)."""
    d = client.get("/api/feed").json()
    levels = d["facets"].get("experience_levels")
    assert levels, "deneyim ekseni facet'te yok"

    shown = d["evaluated"] + d["unevaluated"]
    for level, count in levels.items():
        actual = sum(1 for j in shown
                     if (j.get("experience_level") or "unspecified") == level)
        assert actual == count, f"{level}: facet {count} ≠ gerçek {actual}"


def test_years_requirement_reported_with_evidence(client):
    """Yıl şartı karşılanmıyorsa gerekçe **sayıyla** gösterilmeli — kullanıcı
    neyin eksik olduğunu görebilmeli."""
    from isuygun_core import match
    from isuygun_core.domain import (
        CareerProfile, JobPosting, ProfileFact, Requirement,
    )

    profile = CareerProfile(profile_id="t", facts=(
        ProfileFact(key="python", category="skill",
                    verification="user_asserted", years=1),))
    job = JobPosting(
        job_id="j", title="Backend", employer="X", city="İstanbul",
        occupation_id="Yazılım ve veri", source="t",
        requirements=(Requirement(key="python", label="Python", kind="required",
                                  category="skill", min_years=5,
                                  extraction_confidence=0.9),))
    outcome = match(job, profile).outcomes[0]
    assert outcome.state == "unmet"
    assert "5" in outcome.evidence and "1" in outcome.evidence


# ---------------------------------------------------------------------------
# İsimli çoklu profil (D-045)
# ---------------------------------------------------------------------------


def test_create_and_switch_named_profiles(client):
    """"Eren-Computer Engineer" / "Eren-Mavi yaka" senaryosu: iki profil, ayrı
    veri, geçiş yapınca doğru profil etkin olur."""
    client.post("/api/profiles", json={"name": "Eren-Computer Engineer",
                                        "collar": "white", "fact_keys": ["python"]})
    white = client.get("/api/profiles").json()
    active = next(m for m in white if m["is_active"])
    assert active["name"] == "Eren-Computer Engineer"
    assert active["collar"] == "white"
    # aktif profilde python var
    assert any(f["key"] == "python" for f in client.get("/api/profile").json()["facts"])

    client.post("/api/profiles", json={"name": "Eren-Mavi yaka", "collar": "blue"})
    # yeni profil etkin ve BOŞ — önceki profilin verisi sızmamalı
    assert client.get("/api/profile").json()["facts"] == []

    # geri geç: python yine görünür
    white_id = next(m["id"] for m in client.get("/api/profiles").json()
                    if m["name"] == "Eren-Computer Engineer")
    client.post(f"/api/profiles/{white_id}/activate")
    assert any(f["key"] == "python" for f in client.get("/api/profile").json()["facts"])


def test_rename_profile(client):
    client.post("/api/profiles", json={"name": "İlk isim"})
    pid = next(m["id"] for m in client.get("/api/profiles").json() if m["is_active"])
    client.patch(f"/api/profiles/{pid}", json={"name": "Yeni isim"})
    assert any(m["name"] == "Yeni isim" for m in client.get("/api/profiles").json())


def test_cannot_delete_last_profile(client):
    profiles = client.get("/api/profiles").json()
    # tek profile inene kadar sil
    while len(profiles) > 1:
        victim = next(m["id"] for m in profiles if not m["is_active"])
        client.delete(f"/api/profiles/{victim}")
        profiles = client.get("/api/profiles").json()
    last = profiles[0]["id"]
    r = client.delete(f"/api/profiles/{last}")
    assert r.status_code == 400, "son profil silinememeli"


def test_delete_active_profile_switches_to_another(client):
    client.post("/api/profiles", json={"name": "A"})
    client.post("/api/profiles", json={"name": "B"})   # B etkin
    b_id = next(m["id"] for m in client.get("/api/profiles").json() if m["is_active"])
    client.delete(f"/api/profiles/{b_id}")
    # bir profil hâlâ etkin olmalı (kullanıcı boşta kalmamalı)
    assert any(m["is_active"] for m in client.get("/api/profiles").json())


def _upload_cv(client, monkeypatch):
    """CV yükleme ucunu gerçekten çağırır (PDF ayrıştırma sahtelenir)."""
    monkeypatch.setattr("isuygun_api.cv.extract_text", lambda d: (_CV, 1))
    return client.post(
        "/api/profile/cv",
        files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    ).json()


def test_cv_suggestions_survive_profile_switch(client, monkeypatch):
    """Bekleyen CV önerileri **etkin profile** yazılmalı.

    Regresyon: yükleme ucu önerileri sabit ``"local"`` id'sine kaydediyordu
    (D-045 öncesi tek profil devrinden kalma). Profiller ``p-<uuid>`` olduğu için
    öneriler var olmayan bir profile gidiyordu; okuma ise etkin profilden
    yapılıyor. Sonuç: kullanıcı CV'sini yükleyip profil değiştirince bütün
    öneriler kayboluyordu.

    Test **ucun kendisini** çağırır; ``STORE.store.save_suggestions``'ı doğrudan
    çağırmak hatalı satırı hiç çalıştırmaz ve test hatayla birlikte de geçer.
    """
    client.post("/api/profiles", json={"name": "CV sahibi"})
    a_id = next(m["id"] for m in client.get("/api/profiles").json() if m["is_active"])

    body = _upload_cv(client, monkeypatch)
    onerilen = [s["key"] for s in body["suggestions"]]
    assert onerilen, "CV en az bir alan önermeli (testin ön koşulu)"

    client.post("/api/profiles", json={"name": "Baska profil"})   # başka profile geç
    assert client.get("/api/profile").json()["pending_cv_suggestions"] == [], \
        "öneriler profiller arasında sızmamalı"

    client.post(f"/api/profiles/{a_id}/activate")
    back = [s["key"] for s in client.get("/api/profile").json()["pending_cv_suggestions"]]
    assert back == onerilen, "geri dönünce CV önerileri yerinde olmalı"


def test_accepting_suggestion_persists_to_active_profile(client, monkeypatch):
    """Öneri onaylanınca kalan liste etkin profile yazılmalı — sabit id'ye değil."""
    client.post("/api/profiles", json={"name": "Onaylayan"})
    a_id = next(m["id"] for m in client.get("/api/profiles").json() if m["is_active"])

    onerilen = [s["key"] for s in _upload_cv(client, monkeypatch)["suggestions"]]
    assert len(onerilen) >= 2, "bu test en az iki öneri gerektirir"
    client.post("/api/profile/facts", json={"key": onerilen[0]})   # birini onayla

    # Profil değiştir-geri dön: kalan öneriler diskten doğru okunmalı.
    client.post("/api/profiles", json={"name": "Gecici"})
    client.post(f"/api/profiles/{a_id}/activate")
    left = [s["key"] for s in client.get("/api/profile").json()["pending_cv_suggestions"]]
    assert left == onerilen[1:], "onaylanan düşmeli, kalanlar durmalı"


# ---------------------------------------------------------------------------
# Feed önbelleği (D-054)
# ---------------------------------------------------------------------------


def test_feed_cache_invalidates_when_profile_changes(client):
    """Önbellek profil değişikliğini kaçırmamalı.

    Feed `(korpus sürümü, profil parmak izi)`'nin saf fonksiyonudur; beceri
    eklemek eşleşmeyi değiştirir, dolayısıyla önbellek düşmelidir. Düşmezse
    kullanıcı beceri ekler ama feed'i hiç değişmez — sessiz ve en can sıkıcı
    hata sınıfı.
    """
    # Beklenen değerler MUTLAK: "değişti mi" karşılaştırması bayat önbellekle
    # de tutabiliyor (iki taraf da aynı eski cevabı okur) ve test boşuna geçer.
    bos = client.get("/api/feed").json()
    assert bos["profile_is_empty"] is True
    assert bos["evaluated"] == [], "boş profilde hiçbir ilan bantlanamaz"

    _add(client, "heavy_driving", years=6)
    dolu = client.get("/api/feed").json()
    assert dolu["profile_is_empty"] is False, "önbellek boş profili döndürüyor"
    assert dolu["evaluated"], "beceri eklendi ama hiçbir ilan değerlendirilmedi"
    assert any("Şoför" in j["title"] for j in dolu["evaluated"])

    client.delete("/api/profile/facts/heavy_driving")
    geri = client.get("/api/feed").json()
    assert geri["evaluated"] == [], "beceri silinince bantlar kalkmalı"
    assert geri["profile_is_empty"] is True


def test_feed_cache_invalidates_on_profile_switch(client):
    """Profil değişince feed O profile ait olmalı — öncekinin kopyası değil."""
    client.post("/api/profiles", json={"name": "Dolu"})
    dolu_id = next(m["id"] for m in client.get("/api/profiles").json() if m["is_active"])
    _add(client, "heavy_driving", years=6)
    dolu = client.get("/api/feed").json()
    assert dolu["evaluated"], "dolu profilde bantlanmış ilan olmalı"
    dolu_n = len(dolu["evaluated"])

    client.post("/api/profiles", json={"name": "Bos"})     # boş profil etkin
    bos = client.get("/api/feed").json()
    # Mutlak beklenti: boş profilde bant ÜRETİLEMEZ. "Dolu"nun önbelleği
    # dönerse burada dolu liste görürüz.
    assert bos["evaluated"] == [], "profil değişti ama önceki profilin feed'i geldi"
    assert bos["profile_is_empty"] is True

    client.post(f"/api/profiles/{dolu_id}/activate")
    geri = client.get("/api/feed").json()
    assert len(geri["evaluated"]) == dolu_n, "geri dönünce dolu profilin feed'i gelmeli"
    assert geri["profile_is_empty"] is False


def test_feed_cache_invalidates_on_corpus_refresh(client):
    """Arka planda korpus tazelenince önbellek düşmeli.

    Düşmezse kullanıcı saatlerce kapanmış ilanları görür — tazelemenin tamamı
    boşa gider.
    """
    from isuygun_api.store import STORE

    client.get("/api/feed")
    orig = dict(STORE.postings)
    try:
        STORE.corpus_version += 1          # tazeleme taklidi
        STORE.postings = dict(list(STORE.postings.items())[:5])
        tazelenmis = client.get("/api/feed").json()
        assert len(tazelenmis["evaluated"]) + len(tazelenmis["unevaluated"]) <= 5, \
            "korpus küçüldü ama feed eski listeyi verdi (önbellek düşmemiş)"
    finally:
        # Korpus GERİ yüklenir: küçülmüş korpus modül-kapsamlı fixture'da
        # kalıyor ve sıradaki testler 5 ilanla koşuyordu (sıraya bağlı kirlilik).
        STORE.postings = orig
        STORE.corpus_version += 1


def test_pending_cv_suggestions_do_not_invalidate_feed(client, monkeypatch):
    """Bekleyen öneri eşleşmeyi etkilemez (D-014), feed'i geçersizleştirmemeli.

    Etkilerse her CV yüklemesi bütün korpusun yeniden değerlendirilmesini
    tetikler — hem gereksiz hem yavaş.
    """
    from isuygun_api.main import _FEED_CACHE

    client.get("/api/feed")
    anahtarlar = set(_FEED_CACHE.keys())
    assert anahtarlar, "feed önbelleğe alınmalı"

    monkeypatch.setattr("isuygun_api.cv.extract_text", lambda d: (_CV, 1))
    client.post("/api/profile/cv",
                files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")})
    client.get("/api/feed")
    assert set(_FEED_CACHE.keys()) == anahtarlar, \
        "bekleyen öneri önbelleği düşürmemeli (onaylanmadan eşleşmeyi etkilemez)"


def test_feed_response_matches_declared_schema(client):
    """Gövde elle serileştiriliyor (response_model doğrulaması atlanıyor).

    Bu bir performans kararı ama şemadan sapma riski taşır: FastAPI artık
    alanları doğrulamıyor. Sözleşme testle korunur — OpenAPI'den TS tipi
    üretiliyor (ADR-001), sessiz sapma istemcide kırılır.
    """
    from isuygun_api.main import FeedOut

    r = client.get("/api/feed")
    assert r.headers["content-type"].startswith("application/json")
    FeedOut.model_validate(r.json())   # şemaya uymuyorsa burada patlar


# ---------------------------------------------------------------------------
# D-055 — aynı rol iki bölümde birden görünmemeli
# ---------------------------------------------------------------------------


def test_role_never_appears_in_both_sections(client):
    """Bir rol hem "değerlendirilen" hem "veri eksik" listesinde olamaz.

    Gruplama iki listeye ayrı uygulanıyordu: aynı rolün bir şehirdeki
    kopyasından şart okunmuş, diğerinden okunamamışsa satır ikiye bölünüyor ve
    kullanıcı aynı ilanı iki kez görüyordu (canlı korpusta 8 rol böyleydi).
    """
    _add(client, "heavy_driving", years=6)
    f = client.get("/api/feed").json()

    def rol(j):
        return (j["employer"].casefold(), j["title"].casefold())

    ev = {rol(j) for j in f["evaluated"]}
    un = {rol(j) for j in f["unevaluated"]}
    ortak = ev & un
    assert not ortak, f"aynı rol iki bölümde birden: {sorted(ortak)[:3]}"


def test_no_duplicate_rows_within_a_section(client):
    """Tek bir bölümde aynı rol iki satır olamaz — gruplama bunun için var."""
    _add(client, "heavy_driving", years=6)
    f = client.get("/api/feed").json()
    for ad in ("evaluated", "unevaluated"):
        goruldu = set()
        for j in f[ad]:
            k = (j["employer"].casefold(), j["title"].casefold())
            assert k not in goruldu, f"{ad}: '{j['title']}' iki kez listelendi"
            goruldu.add(k)


def test_absorbed_row_keeps_its_city(client):
    """Düşürülen satırın şehri kaybolmamalı.

    Satırı sessizce atmak, o şehirde ilan yokmuş gibi gösterirdi; şehir
    kazanan satırın `other_locations`'ına taşınır.
    """
    from isuygun_api.main import JobSummary, _absorb_into

    ortak = dict(job_id="x", occupation_id="o", source="s", url="u",
                 is_public_sector=False)
    kazanan = JobSummary(employer="ACME", title="Şoför", city="Ankara", **ortak)
    duşen = JobSummary(employer="acme", title="şoför", city="İzmir", **ortak)

    kalan = _absorb_into([duşen], [kazanan])
    assert kalan == [], "rol zaten kazanan listede, satır düşmeli"
    assert "İzmir" in kazanan.other_locations, "şehir kaybolmamalı"


# ---------------------------------------------------------------------------
# D-059 — durumsuz uçlar: ziyaretçi izolasyonu
# ---------------------------------------------------------------------------


def test_stateless_feed_isolates_visitors(client):
    """İki ziyaretçi farklı profil gönderir; ikisi de KENDİ sonucunu alır ve
    sunucudaki global profil değişmez.

    Canlıda doğrulanan gizlilik açığının regresyon testi: eskiden feed global
    STORE.profile ile hesaplanıyordu ve B ziyaretçisi A'nın becerileriyle
    hesaplanmış eşleşmeler görüyordu.
    """
    surucu = {"profile": {"facts": [
        {"key": "heavy_driving", "years": 6},
        {"key": "src", "verified": True},
        {"key": "psiko", "verified": True},
        {"key": "license_ce", "verified": True}]}}
    a = client.post("/api/feed", json=surucu).json()
    b = client.post("/api/feed", json={"profile": {"facts": []}}).json()

    assert a["profile_is_empty"] is False
    assert any("Şoför" in j["title"] for j in a["evaluated"]), \
        "şoför profili şoför ilanını bantlamalı"
    assert b["profile_is_empty"] is True
    assert b["evaluated"] == [] and b["evaluated_total"] == 0, \
        "boş profilli ziyaretçi A'nın bantlarını GÖRMEMELİ"
    # sunucu tarafında hiçbir şey birikmedi
    assert STORE.profile.facts == (), "geçici profil global profile sızmamalı"

    # A tekrar gelir (önbellekten): kendi sonucu değişmemiş olmalı
    a2 = client.post("/api/feed", json=surucu).json()
    assert a2["evaluated_total"] == a["evaluated_total"]


def test_stateless_feed_drops_legal_keys(client):
    """HTTP sınırından gelen ``legal_*`` alanları profile giremez (D-013)."""
    r = client.post("/api/feed", json={
        "profile": {"facts": [{"key": "legal_military"}]}}).json()
    assert r["profile_is_empty"] is True, \
        "yasal uygunluk alanı geçici profilde bile fact sayılmamalı"


def test_stateless_detail_ledger_follows_payload(client):
    """POST detay defteri, gönderilen profile göre hesaplanmalı."""
    feed = client.post("/api/feed", json={
        "profile": {"facts": [{"key": "heavy_driving", "years": 6}]}}).json()
    job = next(j for j in feed["evaluated"] if "Şoför" in j["title"])

    with_profile = client.post(f"/api/jobs/{job['job_id']}", json={
        "facts": [{"key": "heavy_driving", "years": 6}]}).json()
    assert with_profile["met"], "sürüş deneyimi met satırı üretmeli"

    empty = client.post(f"/api/jobs/{job['job_id']}", json={"facts": []}).json()
    assert empty["met"] == [], "boş profilde met satırı olmamalı"


def test_cv_suggest_is_stateless(client, monkeypatch):
    """/api/cv/suggest öneri döner ama sunucuda İZ BIRAKMAZ.

    Eski uç ortak profile yazıyordu: A'nın CV önerileri classic'e bakan
    herkese görünüyordu.
    """
    monkeypatch.setattr("isuygun_api.cv.extract_text", lambda d: (_CV, 1))
    before = list(STORE.pending_cv_suggestions)
    body = client.post("/api/cv/suggest",
                       files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4"),
                                       "application/pdf")}).json()
    assert body["suggestions"], "öneri üretmeli"
    assert body["written_to_profile"] is False
    assert STORE.pending_cv_suggestions == before, \
        "durumsuz uç sunucudaki bekleyen önerilere dokunmamalı"


def test_stateless_unlock_excludes_submitted_facts(client):
    """POST unlock, gövdede zaten olan alanı önermemeli."""
    base = client.post("/api/unlock-suggestions", json={"facts": []}).json()
    assert base, "boş profile en az bir öneri çıkmalı"
    top = base[0]["key"]
    with_top = client.post("/api/unlock-suggestions",
                           json={"facts": [{"key": top}]}).json()
    assert all(s["key"] != top for s in with_top), \
        "profilde olan alan yeniden önerilmemeli"


def test_signal_endpoints_record_anonymously(client):
    """Geri bildirim + başvuru olayı 204 döner ve sayaç artar."""
    from isuygun_api import signals

    before = signals.counts()
    feed = client.post("/api/feed", json={"profile": {"facts": []}}).json()
    job = feed["unevaluated"][0]

    r1 = client.post("/api/feedback", json={
        "job_id": job["job_id"], "verdict": "down", "band": "strong",
        "reason": "meslek uymuyor"})
    assert r1.status_code == 204
    r2 = client.post("/api/apply-events", json={
        "job_id": job["job_id"], "event": "applied"})
    assert r2.status_code == 204
    r3 = client.post("/api/apply-events", json={
        "job_id": job["job_id"], "event": "hacked"})
    assert r3.status_code == 400, "bilinmeyen olay reddedilmeli"

    after = signals.counts()
    assert after["match_feedback"] == before["match_feedback"] + 1
    assert after["apply_events"] == before["apply_events"] + 1


def test_legacy_surface_gated_when_classic_off(client, monkeypatch):
    """ISUYGUN_CLASSIC kapalıyken eski profil uçları 404; durumsuzlar açık."""
    monkeypatch.delenv("ISUYGUN_CLASSIC", raising=False)
    try:
        assert client.get("/api/profile").status_code == 404
        assert client.get("/api/profiles").status_code == 404
        assert client.get("/api/feed").status_code == 404
        assert client.get("/classic").status_code == 404
        # durumsuz yüzey çalışmaya devam eder
        assert client.post("/api/feed", json={"profile": {"facts": []}}).status_code == 200
        # D-061: yapıştırma ucu artık kapıda DEĞİL — durumsuz hâle geldiği için
        # classic kapalıyken de çalışması gerekiyor (özellik kaybı düzeltmesi).
        assert client.post("/api/jobs/evaluate",
                           json={"text": "x" * 50}).status_code == 200
        assert client.get("/api/sources").status_code == 200
        assert client.get("/api/health").status_code == 200
        assert client.get("/").status_code == 200
    finally:
        monkeypatch.setenv("ISUYGUN_CLASSIC", "1")


# ---------------------------------------------------------------------------
# D-060 — sunucu taraflı sayfalama + filtreler
# ---------------------------------------------------------------------------


def test_feed_pagination_pages_do_not_overlap(client):
    """Sayfalar kesişmez, toplamlar sabittir, taşan offset boş döner."""
    p1 = client.post("/api/feed", json={
        "profile": {"facts": []}, "limit": 5}).json()
    assert len(p1["unevaluated"]) == 5
    assert p1["unevaluated_total"] > 5

    p2 = client.post("/api/feed", json={
        "profile": {"facts": []}, "limit": 5, "offset_unevaluated": 5}).json()
    ids1 = {j["job_id"] for j in p1["unevaluated"]}
    ids2 = {j["job_id"] for j in p2["unevaluated"]}
    assert not ids1 & ids2, "ardışık sayfalar aynı ilanı içermemeli"
    assert p2["unevaluated_total"] == p1["unevaluated_total"], \
        "toplam, sayfadan bağımsız olmalı"

    beyond = client.post("/api/feed", json={
        "profile": {"facts": []}, "limit": 5,
        "offset_unevaluated": p1["unevaluated_total"] + 50}).json()
    assert beyond["unevaluated"] == []
    assert beyond["unevaluated_total"] == p1["unevaluated_total"]


def test_feed_filters_apply_server_side(client):
    """Bölge + kıdem + arama sunucuda süzülmeli; sayfa yalnız eşleşeni taşır."""
    r = client.post("/api/feed", json={
        "profile": {"facts": []},
        "filters": {"region": "Türkiye"}}).json()
    assert r["unevaluated_total"] > 0
    assert all("Türkiye" in j["regions"] for j in r["unevaluated"])

    q = client.post("/api/feed", json={
        "profile": {"facts": []},
        "filters": {"q": "sofor"}}).json()      # katlamalı arama: ş'siz yazım
    assert q["unevaluated_total"] > 0
    got = {j["title"] for j in q["unevaluated"]}
    assert any("Şoför" in t or "şoför" in t.lower() for t in got), \
        f"katlamalı arama şoför ilanlarını bulmalı, gelen: {got}"


def test_feed_facets_are_relative_and_sum_correctly(client):
    """Filtre yokken eksen sayaçlarının toplamı, gösterilen satır toplamına
    eşit olmalı (her satır tam bir eksende sayılır)."""
    r = client.post("/api/feed", json={"profile": {"facts": []}}).json()
    shown = r["evaluated_total"] + r["unevaluated_total"]
    for axis in ("experience_levels", "arrangements", "employment_types"):
        assert sum(r["facets"][axis].values()) == shown, axis

    bd = r["unevaluated_breakdown"]
    assert bd["unreadable"] + bd["missing_data"] + bd["listing_only"] \
        == r["unevaluated_total"]


def test_feed_facets_follow_other_filters(client):
    """D-057 kuralı sunucuda: bir eksen seçilince DİĞER eksenlerin sayıları
    o seçime göre daralmalı; rozet tıklanınca gelen sayı tutmalı."""
    all_r = client.post("/api/feed", json={"profile": {"facts": []}}).json()
    tr = client.post("/api/feed", json={
        "profile": {"facts": []},
        "filters": {"region": "Türkiye"}}).json()
    # Türkiye seçiliyken kıdem sayaçları, bölgesiz sayaçlardan büyük olamaz
    for k, v in tr["facets"]["experience_levels"].items():
        assert v <= all_r["facets"]["experience_levels"].get(k, 0) or v == 0

    # rozet sözü: Türkiye + bir kıdem seçeneği → o sayıda satır dönmeli
    lvl, n = next(iter(tr["facets"]["experience_levels"].items()))
    combo = client.post("/api/feed", json={
        "profile": {"facts": []},
        "filters": {"region": "Türkiye", "level": lvl}}).json()
    assert combo["evaluated_total"] + combo["unevaluated_total"] == n, \
        f"rozet {lvl}={n} dedi, gelen {combo['evaluated_total']+combo['unevaluated_total']}"


# ---------------------------------------------------------------------------
# D-061 — ilan yapıştır durumsuz + kaynak şeffaflığı
# ---------------------------------------------------------------------------

_PASTE = ("Agir vasita soforu araniyor. C+E sinifi ehliyet ve SRC belgesi "
          "sarttir. En az 5 yil agir vasita deneyimi gereklidir. Istanbul "
          "merkezli calisma, vardiyali sistem.")


def test_pasted_job_uses_payload_profile(client):
    """Yapıştırılan ilan, GÖVDEDE gelen profile göre değerlendirilir (D-061).

    Sunucudaki global profil kullanılmaz — /classic üretimde kapalı olduğu için
    bu uç durumsuz hâle geldi; profilsiz istekte de kimsenin izini taşımamalı.
    """
    bos = client.post("/api/jobs/evaluate", json={
        "text": _PASTE, "profile": {"facts": []}}).json()
    assert bos["met"] == [], "boş profilde karşılanan şart olmamalı"

    dolu = client.post("/api/jobs/evaluate", json={
        "text": _PASTE,
        "profile": {"facts": [{"key": "heavy_driving", "years": 6},
                              {"key": "license_ce", "verified": True},
                              {"key": "src", "verified": True}]}}).json()
    assert dolu["met"], "sürücü profili şart karşılamalı"
    assert dolu["band"] is not None
    # Sunucuda iz kalmadı
    assert STORE.profile.facts == ()


def test_pasted_job_is_not_added_to_corpus(client):
    """Yapıştırılan metin korpusa karışmaz (veri hijyeni + kaynak izni)."""
    before = len(STORE.postings)
    client.post("/api/jobs/evaluate", json={
        "text": _PASTE, "profile": {"facts": []}})
    assert len(STORE.postings) == before
    assert "pasted" not in STORE.postings


def test_pasted_job_endpoint_open_without_classic(client, monkeypatch):
    """Yapıştırma ucu classic kapalıyken de ÇALIŞIR.

    Regresyon: D-059'da /classic kapatılınca bu uç da kapıya takılmıştı ve
    "ilan yapıştır" özelliği kullanıcıdan tamamen koptu.
    """
    monkeypatch.delenv("ISUYGUN_CLASSIC", raising=False)
    try:
        r = client.post("/api/jobs/evaluate", json={
            "text": _PASTE, "profile": {"facts": [{"key": "heavy_driving", "years": 6}]}})
        assert r.status_code == 200, r.text
        assert r.json()["met"], "profil gövdeden gelmeli"
        # profil verilmezse: global profilin izi SIZMAMALI
        STORE.set_fact("heavy_driving", years=9)
        try:
            anon = client.post("/api/jobs/evaluate", json={"text": _PASTE}).json()
            assert anon["met"] == [], \
                "classic kapalıyken profilsiz istek global profili kullanmamalı"
        finally:
            STORE.reset_profile()
    finally:
        monkeypatch.setenv("ISUYGUN_CLASSIC", "1")


def test_sources_endpoint_exposes_permission_evidence(client):
    """Kaynak şeffaflığı: her kayıt izin/risk/durum taşımalı, reddedilenler
    görünür olmalı (LinkedIn/Indeed iddiası denetlenebilsin)."""
    src = client.get("/api/sources").json()
    assert src, "kaynak listesi boş olamaz"
    for s in src:
        assert s["scraping_permission"] in ("allowed", "conditional", "rejected", "unknown")
        assert "may_fetch_network" in s
    red = [s for s in src if s["scraping_permission"] == "rejected"]
    adlar = " ".join(s["name"] for s in red).lower()
    assert "linkedin" in adlar and "indeed" in adlar, \
        "reddedilen kaynaklar listede açıkça görünmeli"
    assert all(not s["may_fetch_network"] for s in red), \
        "reddedilen kaynak için ağ çekimi ASLA açık olmamalı"
