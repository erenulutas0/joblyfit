"""İlan önbelleği — özellikle **geçersizleştirme**.

Önbelleğin tehlikeli tarafı hız değil, bayatlıktır. Sözlüğe bir terim eklenip
önbellekteki işlenmiş kayıtlar eski mantığı taşımaya devam ederse, geliştirici
değişikliğinin hiçbir etkisini göremez ve sebebini **kodda arar**. Bu testler o
sessiz hatayı imkânsız kılar.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from isuygun_ingest import cache
from isuygun_ingest.pipeline import LIVE_ADAPTER_VERSION, RawPosting, normalize


def _raw(ref="r1"):
    return RawPosting(
        source_id="src-fixture-001", source_posting_ref=ref,
        url="https://example.invalid/x", title="Senior Python Developer",
        employer="Acme", city="İstanbul, Türkiye",
        description="Requirements\n- 5 years Python\n- Docker and Kubernetes",
    )


@pytest.fixture()
def written(tmp_path):
    path = tmp_path / "c.json"
    raws = [_raw("a"), _raw("b")]
    postings = [normalize(r, adapter_version=LIVE_ADAPTER_VERSION) for r in raws]
    cache.write(path, raws=raws, postings=postings, meta={"boards": [], "errors": []})
    return path, raws, postings


def test_round_trip_preserves_everything(written):
    path, raws, postings = written
    got = cache.read(path, max_age_hours=6)

    assert got is not None
    assert len(got["raws"]) == len(raws)
    assert got["postings"] is not None, "işlenmiş kayıtlar okunamadı"

    a, b = postings[0], got["postings"][0]
    assert a.job.job_id == b.job.job_id
    assert a.job.title == b.job.title
    assert a.job.city == b.job.city
    assert a.url == b.url and a.posted_at == b.posted_at
    assert a.provenance == b.provenance
    assert [(r.key, r.kind, r.min_years, r.extraction_confidence)
            for r in a.job.requirements] == \
           [(r.key, r.kind, r.min_years, r.extraction_confidence)
            for r in b.job.requirements], "şartlar kayıpsız dönmedi"


def test_turkish_characters_survive(written):
    path, _, _ = written
    assert cache.read(path, 6)["postings"][0].job.city == "İstanbul, Türkiye"


def test_changed_extraction_logic_invalidates_processed_records(written):
    """**Asıl korunan hata bu.**

    Çıkarım mantığı değişince işlenmiş kayıtlar geçersiz sayılmalı — ama ham
    kayıtlar korunmalı ki yeniden **çekim** gerekmesin.
    """
    path, _, _ = written
    blob = json.loads(path.read_text(encoding="utf-8"))
    blob["extraction_fingerprint"] = "baska-bir-mantik"
    path.write_text(json.dumps(blob, ensure_ascii=False), encoding="utf-8")

    got = cache.read(path, 6)
    assert got is not None, "ham kayıtlar da atıldı — gereksiz yeniden çekim"
    assert got["postings"] is None, "eski mantıkla üretilmiş kayıtlar kullanıldı"
    assert len(got["raws"]) == 2


def test_fingerprint_changes_when_logic_changes(tmp_path, monkeypatch):
    """Parmak izi kaynak dosyalardan üretilir; içerik değişince değişmeli."""
    before = cache.extraction_fingerprint()

    real = cache.Path.read_bytes

    def fake(self):
        data = real(self)
        return data + b"\n# degisiklik\n" if self.name == "lexicon.py" else data

    monkeypatch.setattr(cache.Path, "read_bytes", fake)
    assert cache.extraction_fingerprint() != before


def test_expired_cache_is_ignored(written):
    path, _, _ = written
    blob = json.loads(path.read_text(encoding="utf-8"))
    blob["fetched_at"] = (datetime.now() - timedelta(hours=48)).isoformat()
    path.write_text(json.dumps(blob, ensure_ascii=False), encoding="utf-8")
    assert cache.read(path, max_age_hours=6) is None


def test_corrupt_cache_is_ignored_not_raised(tmp_path):
    """Bozuk önbellek uygulamayı düşürmemeli; yok sayılır."""
    path = tmp_path / "c.json"
    path.write_text("bu JSON degil {{{", encoding="utf-8")
    assert cache.read(path, 6) is None


def test_missing_cache_returns_none(tmp_path):
    assert cache.read(tmp_path / "yok.json", 6) is None


def test_partial_write_does_not_destroy_existing_cache(written, monkeypatch):
    """Yazım yarıda kalırsa eski önbellek bozulmamalı.

    Doğrudan hedefe yazsaydık, çöken bir yazım hem yeni hem eski veriyi
    kaybettirirdi — ve sonucu 250 saniyelik gereksiz bir yeniden çekim olurdu.
    """
    path, raws, postings = written
    original = path.read_bytes()

    def boom(self, *a, **k):
        raise OSError("disk doldu")

    monkeypatch.setattr(cache.Path, "write_text", boom)
    with pytest.raises(OSError):
        cache.write(path, raws=raws, postings=postings, meta={})

    assert path.read_bytes() == original, "eski önbellek bozuldu"
    assert cache.read(path, 6) is not None


# ---------------------------------------------------------------------------
# Çekim parmak izi (D-035)
# ---------------------------------------------------------------------------


def test_changed_fetch_logic_invalidates_raw_records(tmp_path, monkeypatch):
    """Adapter değişince ham kayıtlar da geçersiz olmalı.

    D-028 yalnızca **çıkarım** mantığını koruyordu. Greenhouse adapter'ı
    ilanın yaşını yanlış alandan okuyordu; düzeltildiğinde önbellekteki ham
    kayıtlar eski tarihi taşımaya devam edecekti ve düzeltmenin hiçbir etkisi
    görünmeyecekti — tam olarak parmak izi mekanizmasının önlediği hata, bir
    katman aşağıda.
    """
    from isuygun_ingest import cache
    from isuygun_ingest.pipeline import RawPosting

    path = tmp_path / "c.json"
    raw = RawPosting(source_id="src-fixture-001", source_posting_ref="r",
                     url="https://e.invalid/x", title="T", employer="E", city="C")
    cache.write(path, raws=[raw], postings=[], meta={})
    assert cache.read(path, 24) is not None

    monkeypatch.setattr(cache, "fetch_fingerprint", lambda: "degisti")
    assert cache.read(path, 24) is None, "çekim mantığı değişti, ham kayıt geçersiz olmalı"


def test_fetch_and_extraction_fingerprints_are_independent(tmp_path, monkeypatch):
    """Çıkarım değişimi yeniden **çekim** gerektirmemeli — ham kayıt korunur."""
    from isuygun_ingest import cache
    from isuygun_ingest.pipeline import RawPosting

    path = tmp_path / "c.json"
    raw = RawPosting(source_id="src-fixture-001", source_posting_ref="r",
                     url="https://e.invalid/x", title="T", employer="E", city="C")
    cache.write(path, raws=[raw], postings=[], meta={})

    monkeypatch.setattr(cache, "extraction_fingerprint", lambda: "degisti")
    got = cache.read(path, 24)
    assert got is not None, "çıkarım değişimi ham kaydı düşürmemeli"
    assert got["raws"], "ham kayıtlar korunmalı"
    assert got["postings"] is None, "işlenmiş kayıtlar geçersiz olmalı"


def test_new_board_invalidates_raw_cache(tmp_path, monkeypatch):
    """Pano listesi değişince ham önbellek geçersiz olmalı (D-043).

    Yeni bir şirket panosu eklendiğinde parmak izi değişmezse önbellek "taze"
    görünür ve yeni pano hiç çekilmez — geliştirici panoyu ekler, ilanları
    göremez. D-036'nın aynı sınıfı, üçüncü tekrarı.
    """
    from isuygun_ingest import cache

    assert "registry.py" in cache._FETCH_FILES
