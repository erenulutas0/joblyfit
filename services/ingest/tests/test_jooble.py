"""Jooble toplayıcı adaptörü (D-038).

Canlı API'ye çıkılmaz; yanıt mock'lanır. Testlerin çoğu iki şeyi güvenceye
alır: (1) anahtar yokken temiz ve **bilgilendirici** atlama, (2) Jooble'ın
alan adlarının bizim modele doğru eşlenmesi — özellikle tarih, çünkü Jooble
``updated`` verir (son görülme) ama ilk yayın vermez ve bunu yaş sanmak
D-035'te düzeltilen hatayı geri getirirdi.
"""

from __future__ import annotations

import pytest

from isuygun_ingest.adapters import public_apis as pa


_SAMPLE = {
    "jobs": [
        {
            "id": "111", "title": "Muhasebe Uzmanı",
            "company": "Örnek A.Ş.", "location": "İstanbul",
            "salary": "35000 - 50000 TL", "type": "Tam zamanlı",
            "snippet": "Ön muhasebe deneyimi aranmaktadır. Excel bilgisi şart.",
            "link": "https://kariyer.example/ilan/111", "source": "kariyer.net",
            "updated": "2026-07-18T09:00:00.0000000",
        },
        {
            "id": "222", "title": "Depo Görevlisi",
            "company": "", "location": "Kocaeli, Gebze",
            "salary": "", "type": "",
            "snippet": "Forklift belgesi olan adaylar tercih edilir.",
            "link": "https://secretcv.example/ilan/222", "source": "secretcv",
            "updated": "2026-07-20T00:00:00.0000000",
        },
    ]
}


def _mock_post(monkeypatch, payload):
    calls = []

    def fake(url, body):
        calls.append((url, body))
        # İkinci sayfa boş döner ki sayfalama dursun.
        if body.get("page", 1) > 1:
            return {"jobs": []}
        return payload

    monkeypatch.setattr(pa, "_post_json", fake)
    return calls


# ---------------------------------------------------------------------------
# Anahtar yönetimi
# ---------------------------------------------------------------------------


def test_missing_key_skips_with_helpful_message(monkeypatch):
    """Anahtar yoksa çökme değil, kullanıcıya ne yapacağını söyleyen hata.

    Sessizce boş dönmek, kaynağın kapandığını gizlemekle aynı olurdu; bu hata
    ingest raporunda görünür ve anahtarın nereden alınacağını yazar.
    """
    monkeypatch.delenv("ISUYGUN_JOOBLE_KEY", raising=False)
    with pytest.raises(pa.FetchError) as e:
        pa.fetch_jooble("src-api-jooble")
    assert "ISUYGUN_JOOBLE_KEY" in str(e.value)
    assert "jooble.org/api/about" in str(e.value)


def test_missing_key_does_not_crash_ingest(monkeypatch):
    """_fetch_api_sources hatayı yakalar; Jooble'sız ingest yine tamamlanır."""
    monkeypatch.delenv("ISUYGUN_JOOBLE_KEY", raising=False)
    from isuygun_ingest.registry import assert_fetchable

    # Kaynak izinli ve çekilebilir olmalı (kayıt doğru) ama anahtarsız atlanır.
    rec = assert_fetchable("src-api-jooble")
    assert rec.may_fetch_network


def test_key_is_placed_in_url(monkeypatch):
    monkeypatch.setenv("ISUYGUN_JOOBLE_KEY", "SECRET123")
    calls = _mock_post(monkeypatch, _SAMPLE)
    pa.fetch_jooble("src-api-jooble", queries=("test",), pages=1)
    assert calls and calls[0][0].endswith("/SECRET123")


# ---------------------------------------------------------------------------
# Alan eşlemesi
# ---------------------------------------------------------------------------


def test_maps_fields_to_rawposting(monkeypatch):
    monkeypatch.setenv("ISUYGUN_JOOBLE_KEY", "k")
    _mock_post(monkeypatch, _SAMPLE)
    out = pa.fetch_jooble("src-api-jooble", queries=("muhasebe",), pages=1)

    by_ref = {r.source_posting_ref: r for r in out}
    a = by_ref["111"]
    assert a.title == "Muhasebe Uzmanı"
    assert a.employer == "Örnek A.Ş."
    assert a.city == "İstanbul"
    assert a.url == "https://kariyer.example/ilan/111"   # kaynağa yönlendirme
    assert a.source_id == "src-api-jooble"


def test_updated_maps_to_refreshed_not_age(monkeypatch):
    """Jooble `updated`'ı yaş sanmak, D-035'teki hayalet-ilan hatasını geri
    getirirdi. İlk yayın bilinmiyor → posted_at None (elenmez), tazelik
    refreshed_at'ten ölçülür."""
    monkeypatch.setenv("ISUYGUN_JOOBLE_KEY", "k")
    _mock_post(monkeypatch, _SAMPLE)
    r = pa.fetch_jooble("src-api-jooble", queries=("x",), pages=1)[0]
    assert r.posted_at is None
    assert r.refreshed_at == "2026-07-18"


def test_empty_company_becomes_placeholder(monkeypatch):
    monkeypatch.setenv("ISUYGUN_JOOBLE_KEY", "k")
    _mock_post(monkeypatch, _SAMPLE)
    out = pa.fetch_jooble("src-api-jooble", queries=("x",), pages=1)
    depo = next(r for r in out if r.source_posting_ref == "222")
    assert depo.employer == "Belirtilmemiş"


def test_salary_and_snippet_folded_into_description(monkeypatch):
    """Maaş ve tür ayrı alanlarda gelir; metne katılınca mevcut çıkarıcılar
    (salary.py) onları görebilmeli."""
    monkeypatch.setenv("ISUYGUN_JOOBLE_KEY", "k")
    _mock_post(monkeypatch, _SAMPLE)
    a = next(r for r in pa.fetch_jooble("src-api-jooble", queries=("x",), pages=1)
             if r.source_posting_ref == "111")
    assert "Maaş: 35000 - 50000 TL" in a.description
    assert "Excel" in a.description

    from isuygun_ingest import salary
    s = salary.extract(a.description)
    assert s is not None and s.currency == "TRY"


# ---------------------------------------------------------------------------
# Dedupe
# ---------------------------------------------------------------------------


def test_overlapping_queries_deduped_by_id(monkeypatch):
    """Geniş tohum sorguları aynı ilanı birden çok kez getirir; batch içinde
    id ile tekilleştirilir."""
    monkeypatch.setenv("ISUYGUN_JOOBLE_KEY", "k")
    _mock_post(monkeypatch, _SAMPLE)
    # Üç farklı tohum, hepsi aynı iki ilanı döndürüyor.
    out = pa.fetch_jooble("src-api-jooble",
                          queries=("a", "b", "c"), pages=1)
    assert len(out) == 2
    assert {r.source_posting_ref for r in out} == {"111", "222"}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_registered_and_fetchable():
    from isuygun_ingest import registry

    ids = {r.source_id for r in registry.api_sources()}
    assert "src-api-jooble" in ids
    rec = registry.get("src-api-jooble")
    assert rec.may_fetch_network
    assert rec.permission_evidence   # D-020: kanıtsız 'allowed' olamaz
    assert rec.attribution_required


def test_jooble_in_fetch_fingerprint():
    """public_apis.py çekim parmak izinde olmalı: adaptör değişince ham
    kayıtlar geçersizleşmeli (D-036)."""
    from isuygun_ingest import cache

    assert "adapters/public_apis.py" in cache._FETCH_FILES


# ---------------------------------------------------------------------------
# Ülke sitesi / host uyumu (D-041)
# ---------------------------------------------------------------------------


def test_host_is_configurable(monkeypatch):
    """Host ülke sitesidir ve ayarlanabilir: tr.jooble.org anahtarı Türkiye
    verir, jooble.org vermez."""
    monkeypatch.setenv("ISUYGUN_JOOBLE_KEY", "k")
    monkeypatch.setenv("ISUYGUN_JOOBLE_HOST", "tr.jooble.org")
    calls = _mock_post(monkeypatch, _SAMPLE)
    pa.fetch_jooble("src-api-jooble", queries=("x",), pages=1)
    assert calls[0][0].startswith("https://tr.jooble.org/api/")


def test_default_host_is_turkey_site(monkeypatch):
    monkeypatch.setenv("ISUYGUN_JOOBLE_KEY", "k")
    monkeypatch.delenv("ISUYGUN_JOOBLE_HOST", raising=False)
    calls = _mock_post(monkeypatch, _SAMPLE)
    pa.fetch_jooble("src-api-jooble", queries=("x",), pages=1)
    assert "tr.jooble.org" in calls[0][0]


def test_zero_jobs_is_not_silent(monkeypatch):
    """Sorgular çalışıp 0 ilan dönerse (host/anahtar ülke uyumsuzluğu) sessiz
    dönmek yanıltıcı olurdu — bu tam olarak jooble.org anahtarının Türkiye'de
    yaşadığı durum. Rehber mesajla hata yükseltilir."""
    monkeypatch.setenv("ISUYGUN_JOOBLE_KEY", "k")

    def empty(url, body):
        return {"totalCount": 0, "jobs": []}

    monkeypatch.setattr(pa, "_post_json", empty)
    with pytest.raises(pa.FetchError) as e:
        pa.fetch_jooble("src-api-jooble", queries=("x",), pages=1)
    assert "0 ilan" in str(e.value) and "tr.jooble.org" in str(e.value)


def test_api_key_never_leaks_in_errors(monkeypatch):
    """Anahtar URL'de; hiçbir hata mesajı ham anahtarı taşımamalı — yoksa
    ingest raporuna, arayüze ve önbelleğe sızar."""
    secret = "super-secret-key-123"
    monkeypatch.setenv("ISUYGUN_JOOBLE_KEY", secret)

    def forbidden(url, body):
        raise pa.FetchError(pa._mask_key(f"{url} → HTTP 403"))

    monkeypatch.setattr(pa, "_post_json", forbidden)
    with pytest.raises(pa.FetchError) as e:
        pa.fetch_jooble("src-api-jooble", queries=("x",), pages=1)
    assert secret not in str(e.value), "anahtar hata mesajına sızdı!"
    assert "***" in str(e.value)


def test_mask_key_helper():
    assert pa._mask_key("https://tr.jooble.org/api/abc-123 → HTTP 403") == \
        "https://tr.jooble.org/api/*** → HTTP 403"
    # /api/ olmayan URL'ler dokunulmaz (Arbeitnow gibi meşru yollar korunur).
    assert pa._mask_key("no key here") == "no key here"
