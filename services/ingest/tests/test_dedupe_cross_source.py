"""Kaynaklar arası dedupe (D-039).

Jooble bir toplayıcıdır: aynı ilanı hem şirketin ATS'sinden (doğrudan, tam
açıklama) hem Jooble'dan (snippet) alabiliriz. Bu testler iki şeyi güvenceye
alır: (1) aynı URL'e çözülen kayıtlar birleşir, (2) birleşince en zengin kopya
(doğrudan ATS) kalır, toplayıcı düşer.
"""

from __future__ import annotations

from isuygun_ingest.pipeline import (
    RawPosting,
    _normalize_url,
    _source_tier,
    cluster,
    normalize,
    pick_canonical,
)


def _mk(source_id, ref, url, *, title="Backend Engineer", employer="Acme",
        city="İstanbul", desc="Python ve Django deneyimi aranıyor."):
    return normalize(
        RawPosting(source_id=source_id, source_posting_ref=ref, url=url,
                   title=title, employer=employer, city=city, description=desc),
        adapter_version="test",
    )


# ---------------------------------------------------------------------------
# URL normalizasyonu
# ---------------------------------------------------------------------------


def test_url_normalization_strips_noise():
    a = _normalize_url("https://www.Boards.Greenhouse.io/acme/jobs/123?utm=x#top")
    b = _normalize_url("http://boards.greenhouse.io/acme/jobs/123/")
    assert a == b == "boards.greenhouse.io/acme/jobs/123"


def test_shallow_url_yields_no_key():
    """Tek segmentli sığ yol anahtar üretmez: farklı ilanlar aynı '/jobs'
    sayfasını paylaşabilir, yanlış birleştirme olurdu."""
    assert _normalize_url("https://site.com/jobs") == ""
    assert _normalize_url("https://site.com/") == ""
    assert _normalize_url("") == ""


def test_query_only_ids_do_not_false_merge():
    """Yol aynı, yalnızca query farklıysa — bizim kaynaklarımızda kimlik yolda
    olduğu için bu durum oluşmaz, ama olsa bile sığ-yol kuralı korur."""
    assert _normalize_url("https://x.com/a") == ""   # tek segment → anahtar yok


# ---------------------------------------------------------------------------
# Kaynaklar arası birleştirme
# ---------------------------------------------------------------------------


def test_same_url_merges_across_sources():
    """Toplayıcı kaynağa link veriyorsa ATS kopyasıyla birleşir."""
    url = "https://boards.greenhouse.io/acme/jobs/123"
    ats = _mk("src-ats-greenhouse", "123", url)
    jooble = _mk("src-api-jooble", "999", url, employer="Belirtilmemiş",
                 desc="Python...")
    clusters, _ = cluster([ats, jooble])
    assert len(clusters) == 1, "aynı URL tek kümede olmalı"


def test_different_urls_not_merged_by_url_gate():
    """Farklı URL'ler URL geçidinden birleşmez (içerik geçidi ayrı karar verir)."""
    a = _mk("src-ats-greenhouse", "1", "https://boards.greenhouse.io/acme/jobs/1")
    b = _mk("src-api-jooble", "2", "https://kariyer.net/is-ilani/xyz-777",
            employer="Başka Firma", city="Ankara",
            desc="Tamamen farklı bir rol, muhasebe.")
    clusters, _ = cluster([a, b])
    assert len(clusters) == 2


# ---------------------------------------------------------------------------
# Kaynak katmanı — hangi kopya kalır
# ---------------------------------------------------------------------------


def test_source_tier_order():
    assert _source_tier("src-ats-greenhouse:1") == 0
    assert _source_tier("src-api-arbeitnow:1") == 1
    assert _source_tier("src-api-arbeitsagentur:1") == 2
    assert _source_tier("src-api-jooble:1") == 3


def test_canonical_prefers_direct_ats_over_aggregator():
    """Aynı ilan hem ATS hem Jooble'da: kullanıcıya doğrudan ATS kopyası
    gösterilir — tam açıklama, gerçek işveren, ilk-yayın tarihi onda."""
    url = "https://boards.greenhouse.io/acme/jobs/123"
    ats = _mk("src-ats-greenhouse", "123", url, employer="Acme")
    jooble = _mk("src-api-jooble", "999", url, employer="Belirtilmemiş")
    chosen = pick_canonical([jooble, ats])
    assert chosen is ats
    assert chosen.job.job_id.startswith("src-ats-")


def test_canonical_tier_beats_employer_visibility():
    """Katman önce gelir: Jooble işvereni gösterse bile doğrudan ATS yeğlenir
    (ATS tam açıklama + ilk-yayın tarihi taşır)."""
    url = "https://jobs.lever.co/acme/uuid"
    ats = _mk("src-ats-lever", "uuid", url, employer="Acme")
    jooble = _mk("src-api-jooble", "999", url, employer="Acme A.Ş.")
    assert pick_canonical([jooble, ats]) is ats


# ---------------------------------------------------------------------------
# Config marker — anahtar eklenince önbellek geçersizleşir
# ---------------------------------------------------------------------------


def test_jooble_key_presence_changes_fetch_fingerprint(monkeypatch):
    from isuygun_ingest import cache

    monkeypatch.delenv("ISUYGUN_JOOBLE_KEY", raising=False)
    without = cache.fetch_fingerprint()
    monkeypatch.setenv("ISUYGUN_JOOBLE_KEY", "abc")
    with_key = cache.fetch_fingerprint()
    assert without != with_key, "anahtar eklenince parmak izi değişmeli (re-fetch)"
