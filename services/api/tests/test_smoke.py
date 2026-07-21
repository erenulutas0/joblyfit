"""Uygulama duman testi — "açılıyor mu, her uç cevap veriyor mu".

Diğer test dosyaları tek tek kuralları doğruluyor; bu dosya **uygulamanın
bütününün ayakta olduğunu** doğruluyor. Bir uç 500 dönmeye başladığında kural
testleri geçmeye devam eder ama uygulama kullanılamaz olur.

Ağa çıkmaz: korpus fixture'dan yüklenir.
"""

from __future__ import annotations

import urllib.parse

import pytest
from fastapi.testclient import TestClient

from isuygun_api.main import app
from isuygun_api.store import STORE


@pytest.fixture(scope="module", autouse=True)
def _corpus():
    STORE.load(live=False)
    yield


@pytest.fixture()
def client():
    c = TestClient(app)
    STORE.reset_profile()
    yield c
    STORE.reset_profile()


@pytest.mark.parametrize("path", [
    "/api/health", "/api/sources", "/api/catalog", "/api/profile", "/api/feed",
    "/openapi.json", "/",
])
def test_endpoint_responds(client, path):
    r = client.get(path)
    assert r.status_code == 200, f"{path} → {r.status_code}"


def test_index_page_is_served(client):
    """Arayüz statik dosyası servis ediliyor olmalı."""
    body = client.get("/").text
    assert "<title>İşe Uygun</title>" in body
    assert "<script>" in body


def test_every_feed_item_can_be_opened(client):
    """Feed'deki her ilanın detayı açılabilmeli.

    İlan kimlikleri kaynak referansından üretiliyor ve bazıları eğik çizgi,
    nokta veya Unicode içeriyor. Detay yolu bunları taşıyamazsa kullanıcı
    listede gördüğü ilana tıklayınca hata alır.
    """
    feed = client.get("/api/feed").json()
    items = feed["evaluated"] + feed["unevaluated"]
    assert items, "korpus boş"
    for j in items:
        r = client.get("/api/jobs/" + urllib.parse.quote(j["job_id"], safe=""))
        assert r.status_code == 200, f"{j['job_id']} → {r.status_code}"


def test_every_feed_item_has_a_usable_apply_link(client):
    """Ürünün asıl eylemi budur: kullanıcıyı ilanın kendi sayfasına götürmek.

    Boş veya bozuk URL, "İlana git" düğmesini sessizce ölü hale getirir.
    """
    feed = client.get("/api/feed").json()
    for j in feed["evaluated"] + feed["unevaluated"]:
        assert j["url"].startswith("http"), f"{j['title']}: {j['url']!r}"


def test_missing_job_returns_404(client):
    assert client.get("/api/jobs/olmayan-ilan").status_code == 404


def test_unknown_fact_key_is_rejected(client):
    r = client.post("/api/profile/facts", json={"key": "uydurma-alan"})
    assert r.status_code == 404


def test_profile_lifecycle(client):
    """Ekle → doğrula → kaldır → sıfırla akışı uçtan uca çalışmalı."""
    p = client.post("/api/profile/facts", json={"key": "python"}).json()
    assert any(f["key"] == "python" for f in p["facts"])

    p = client.post("/api/profile/facts/python/verify").json()
    assert next(f for f in p["facts"] if f["key"] == "python")["verification"] == "verified"

    p = client.delete("/api/profile/facts/python").json()
    assert not any(f["key"] == "python" for f in p["facts"])

    client.post("/api/profile/facts", json={"key": "docker_k8s"})
    assert client.post("/api/profile/reset").json()["facts"] == []


def test_occupations_round_trip(client):
    r = client.put("/api/profile/occupations",
                   json={"occupation_ids": ["Yazılım ve veri", "Sağlık"]})
    assert r.status_code == 200
    assert set(r.json()["occupation_ids"]) == {"Yazılım ve veri", "Sağlık"}


def test_facets_are_present_and_non_empty(client):
    """Arayüzdeki filtreler bu alanlardan besleniyor; boşsa filtre çubuğu ölür."""
    f = client.get("/api/feed").json()["facets"]
    for key in ("cities", "employers", "clusters", "regions"):
        assert f.get(key), f"facet boş: {key}"
    assert all({"name", "count"} <= set(r) for r in f["regions"])


def test_ingest_summary_reports_what_was_dropped(client):
    """Eleme sessiz olmamalı: kullanıcı neyin gösterilmediğini görebilmeli."""
    i = client.get("/api/feed").json()["ingest"]
    for key in ("fetched", "canonical", "duplicates_merged", "stale_dropped"):
        assert key in i, f"ingest özetinde eksik: {key}"


def test_openapi_documents_every_route(client):
    """TS tipleri buradan üretiliyor; bir uç şemada yoksa arayüz onu göremez."""
    schema = client.get("/openapi.json").json()
    for path in ("/api/feed", "/api/catalog", "/api/profile", "/api/sources",
                 "/api/profile/cv", "/api/jobs/{job_id}"):
        assert path in schema["paths"], f"OpenAPI'de yok: {path}"


def test_source_policy_is_exposed(client):
    """Atıf zorunluluğu arayüze ulaşmalı — kaynak şartı gizlenemez (D-023)."""
    rows = client.get("/api/sources").json()
    open_sources = [s for s in rows if s["may_fetch_network"]]
    assert open_sources
    for s in open_sources:
        assert "attribution_required" in s
        assert "redistribution_policy" in s
