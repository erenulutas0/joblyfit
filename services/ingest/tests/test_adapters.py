"""Adapter sözleşmesi — dış JSON şekli değişirse burada kırılır.

Adapter'lar bizim kontrolümüzde olmayan veriyi okur. Bir kaynak alan adını
değiştirdiğinde kod **çökmeyebilir**: boş başlık, boş URL veya boş tarih üretip
sessizce devam eder. Kullanıcı tarafındaki sonucu ise ağırdır — "İlana git"
düğmesi hiçbir yere gitmez.

Bu yüzden testler ağa çıkmaz; her kaynağın gerçek yanıt **şeklini** taklit eden
sabit örnekler üzerinden parse mantığını doğrular. Ağ testi ayrı bir iştir ve
CI'da koşturulmaz (dış servise yük + kırılganlık).
"""

from __future__ import annotations

import json
import pytest

from isuygun_ingest.adapters import ats, public_apis

# --------------------------------------------------------------------------
# Örnek yanıtlar — gerçek uçlardan alınan şekiller (içerik kısaltılmış)
# --------------------------------------------------------------------------

LEVER = [{
    "id": "abc-123",
    "text": "Senior Backend Engineer",
    "hostedUrl": "https://jobs.lever.co/acme/abc-123",
    "applyUrl": "https://jobs.lever.co/acme/abc-123/apply",
    "categories": {"location": "Istanbul / Maslak", "team": "Eng"},
    "workplaceType": "hybrid",
    "createdAt": 1784635200000,   # 2026-07-21 UTC
    "descriptionPlain": "Acme hakkinda genel tanitim metni.",
    "lists": [
        {"text": "Requirements", "content": "<ul><li>5 years Python</li></ul>"},
        {"text": "What We Offer", "content": "<ul><li>Health insurance</li></ul>"},
    ],
}]

GREENHOUSE = {"jobs": [{
    "id": 4567,
    "title": "Data Engineer",
    "absolute_url": "https://boards.greenhouse.io/acme/jobs/4567",
    "location": {"name": "Berlin, Germany"},
    "updated_at": "2026-07-15T10:00:00-04:00",
    "content": "&lt;p&gt;We need &lt;strong&gt;SQL&lt;/strong&gt; skills&lt;/p&gt;",
}]}

ASHBY = {"jobs": [{
    "id": "ash-9",
    "title": "ML Engineer",
    "jobUrl": "https://jobs.ashbyhq.com/acme/ash-9",
    "location": "Remote (US)",
    "workplaceType": "Remote",
    "publishedAt": "2026-07-18T08:00:00.000Z",
    "descriptionHtml": "<p>PyTorch experience required</p>",
}]}

RECRUITEE = {"offers": [{
    "id": 77,
    "title": "Depo Görevlisi",
    "careers_url": "https://acme.recruitee.com/o/depo-gorevlisi",
    "city": "İstanbul", "country": "Türkiye",
    "published_at": "2026-07-20 09:00:00 UTC",
    "description": "<p>Forklift belgesi tercih sebebidir</p>",
}]}

ARBEITSAGENTUR = {"stellenangebote": [{
    "refnr": "10000-1234567890-S",
    "titel": "Lagerhelfer (m/w/d)",
    "beruf": "Lagerhelfer/in",
    "arbeitgeber": "Muster Logistik GmbH",
    "arbeitsort": {"ort": "Bremen", "region": "Bremen"},
    "aktuelleVeroeffentlichungsdatum": "2026-07-21T00:00:00.000+00:00",
    "externeUrl": "https://example.invalid/stelle/1234",
}]}

ARBEITNOW = {"data": [{
    "slug": "senior-dev-berlin-123",
    "title": "Senior Developer (m/f/d)",
    "company_name": "Muster GmbH",
    "location": "Berlin",
    "remote": True,
    "created_at": 1784635200,   # 2026-07-21 UTC
    "url": "https://www.arbeitnow.com/jobs/companies/muster/senior-dev-123",
    "description": "<p>Docker und Kubernetes</p>",
}]}

THEMUSE = {"results": [{
    "id": 999,
    "name": "Product Manager",
    "company": {"name": "Acme Inc"},
    "locations": [{"name": "New York, NY"}, {"name": "Remote"}],
    "publication_date": "2026-07-10T12:00:00Z",
    "contents": "<p>Roadmap ownership</p>",
    "refs": {"landing_page": "https://www.themuse.com/jobs/acme/product-manager"},
}]}

HIMALAYAS = {"jobs": [{
    "guid": "https://himalayas.app/jobs/acme-designer",
    "title": "Product Designer",
    "companyName": "Acme",
    "locationRestrictions": ["United States", "Canada"],
    "pubDate": "2026-07-19T00:00:00.000Z",
    "expiryDate": "2099-01-01T00:00:00.000Z",
    "description": "<p>Figma required</p>",
    "excerpt": "Design role",
}]}


@pytest.fixture()
def stub(monkeypatch):
    """Ağ katmanını sabit yanıtla değiştirir; hiçbir istek gitmez."""
    def make(payload):
        def _fake(url, headers=None):
            return payload
        monkeypatch.setattr(public_apis, "_get", _fake)
        monkeypatch.setattr(ats, "fetch_json", lambda url: payload)
    return make


# --------------------------------------------------------------------------
# Her adapter için aynı sözleşme
# --------------------------------------------------------------------------


def _assert_contract(posting, *, source_id):
    """Her adapter'ın üretmek **zorunda** olduğu asgari alanlar."""
    assert posting.source_id == source_id
    assert posting.source_posting_ref, "kaynak referansı boş — provenance kırılır"
    assert posting.url.startswith("http"), (
        f"URL kullanılabilir değil: {posting.url!r} — 'İlana git' hiçbir yere gitmez"
    )
    assert posting.title.strip(), "başlık boş"
    assert posting.employer.strip(), "işveren boş"


def test_lever_contract(stub):
    stub(LEVER)
    board = ats.Board(source_id="src-ats-lever", platform="lever",
                      slug="acme", employer="Acme")
    items, truncated = ats.fetch_board(board)
    assert len(items) == 1 and truncated == 0
    p = items[0]
    _assert_contract(p, source_id="src-ats-lever")
    assert p.city == "Istanbul / Maslak"
    assert p.posted_at == "2026-07-21"
    # `lists` kullanılmalı; yalnızca şirket tanıtımı alınırsa dedupe bozulur.
    assert "Requirements" in p.description
    assert "5 years Python" in p.description
    assert "Acme hakkinda" not in p.description


def test_greenhouse_contract(stub):
    stub(GREENHOUSE)
    board = ats.Board(source_id="src-ats-greenhouse", platform="greenhouse",
                      slug="acme", employer="Acme")
    items, _ = ats.fetch_board(board)
    p = items[0]
    _assert_contract(p, source_id="src-ats-greenhouse")
    assert p.city == "Berlin, Germany"
    assert p.posted_at == "2026-07-15"
    # HTML entity'leri çözülmeli, etiketler atılmalı
    assert "SQL" in p.description and "<strong>" not in p.description


def test_ashby_contract(stub):
    stub(ASHBY)
    board = ats.Board(source_id="src-ats-ashby", platform="ashby",
                      slug="acme", employer="Acme")
    items, _ = ats.fetch_board(board)
    p = items[0]
    _assert_contract(p, source_id="src-ats-ashby")
    assert p.posted_at == "2026-07-18"
    assert "PyTorch" in p.description


def test_recruitee_contract(stub):
    stub(RECRUITEE)
    board = ats.Board(source_id="src-ats-recruitee", platform="recruitee",
                      slug="acme", employer="Acme")
    items, _ = ats.fetch_board(board)
    p = items[0]
    _assert_contract(p, source_id="src-ats-recruitee")
    assert "İstanbul" in p.city and "Türkiye" in p.city


def test_arbeitsagentur_contract(stub, monkeypatch):
    stub(ARBEITSAGENTUR)
    monkeypatch.setattr(public_apis, "BA_QUERIES", ("Lagerhelfer",))
    items = public_apis.fetch_arbeitsagentur("src-api-arbeitsagentur")
    p = items[0]
    _assert_contract(p, source_id="src-api-arbeitsagentur")
    assert p.posted_at == "2026-07-21"
    assert "Bremen" in p.city


def test_arbeitsagentur_falls_back_to_jobdetail_url(stub, monkeypatch):
    """externeUrl yoksa ilan yine de açılabilir bir adrese bağlanmalı."""
    payload = json.loads(json.dumps(ARBEITSAGENTUR))
    del payload["stellenangebote"][0]["externeUrl"]
    stub(payload)
    monkeypatch.setattr(public_apis, "BA_QUERIES", ("Lagerhelfer",))
    p = public_apis.fetch_arbeitsagentur("src-api-arbeitsagentur")[0]
    assert p.url.startswith("https://www.arbeitsagentur.de/jobsuche/jobdetail/")


def test_arbeitnow_contract(stub):
    stub(ARBEITNOW)
    items = public_apis.fetch_arbeitnow("src-api-arbeitnow", pages=1)
    p = items[0]
    _assert_contract(p, source_id="src-api-arbeitnow")
    assert p.posted_at == "2026-07-21"
    assert p.arrangement == "Uzaktan"


def test_themuse_contract(stub):
    stub(THEMUSE)
    p = public_apis.fetch_themuse("src-api-themuse", pages=1)[0]
    _assert_contract(p, source_id="src-api-themuse")
    assert p.city == "New York, NY"
    assert p.posted_at == "2026-07-10"


def test_himalayas_contract(stub):
    stub(HIMALAYAS)
    p = public_apis.fetch_himalayas("src-api-himalayas", pages=1)[0]
    _assert_contract(p, source_id="src-api-himalayas")
    assert p.arrangement == "Uzaktan"
    assert "United States" in p.city


def test_himalayas_drops_expired_postings(stub):
    """Kaynak süresinin geçtiğini söylüyorsa ilan hiç alınmaz (D-024)."""
    payload = json.loads(json.dumps(HIMALAYAS))
    payload["jobs"][0]["expiryDate"] = "2020-01-01T00:00:00.000Z"
    stub(payload)
    assert public_apis.fetch_himalayas("src-api-himalayas", pages=1) == []


# --------------------------------------------------------------------------
# Bozuk / eksik veri karşısında davranış
# --------------------------------------------------------------------------


def test_missing_fields_do_not_crash(stub):
    """Alanlar eksikse adapter çökmemeli — kayıt üretmeli ya da atlamalı."""
    stub({"jobs": [{"id": 1}]})
    board = ats.Board(source_id="src-ats-greenhouse", platform="greenhouse",
                      slug="acme", employer="Acme")
    items, _ = ats.fetch_board(board)
    assert len(items) == 1
    assert items[0].title == "" and items[0].url == ""


def test_unexpected_shape_raises_rather_than_silently_empty(stub):
    """Lever liste bekler; sözlük gelirse **sessizce boş dönmemeli**.

    Sessiz boş dönüş, kaynağın kapandığını gizler. Hata yükselir ve ingest
    raporunda `errors` altında görünür.
    """
    stub({"unexpected": True})
    board = ats.Board(source_id="src-ats-lever", platform="lever",
                      slug="acme", employer="Acme")
    with pytest.raises(ats.FetchError):
        ats.fetch_board(board)


def test_unknown_platform_is_an_error():
    board = ats.Board(source_id="src-ats-lever", platform="myspace",
                      slug="acme", employer="Acme")
    with pytest.raises(ats.FetchError):
        ats.fetch_board(board)


def test_per_board_cap_keeps_newest(stub):
    """Sınır uygulanırken **en yeniler** tutulmalı, rastgele değil."""
    payload = {"jobs": [
        {"id": i, "title": f"Job {i}", "absolute_url": f"https://x.invalid/{i}",
         "location": {"name": "Berlin, Germany"},
         "updated_at": f"2026-0{1 + i % 7}-10T00:00:00Z", "content": "text"}
        for i in range(10)
    ]}
    stub(payload)
    board = ats.Board(source_id="src-ats-greenhouse", platform="greenhouse",
                      slug="acme", employer="Acme")
    items, truncated = ats.fetch_board(board, limit=3)
    assert len(items) == 3 and truncated == 7
    assert [p.posted_at for p in items] == sorted(
        [p.posted_at for p in items], reverse=True
    )


# --------------------------------------------------------------------------
# HTML → metin
# --------------------------------------------------------------------------


def test_html_to_text_strips_tags_and_scripts():
    html = "<div><script>alert(1)</script><p>Merhaba</p><li>Madde</li></div>"
    out = ats.html_to_text(html)
    assert "alert" not in out
    assert "Merhaba" in out and "Madde" in out
    assert "<" not in out


def test_date_parser_handles_source_formats():
    assert public_apis._date("2026-07-21T00:00:00.000+00:00") == "2026-07-21"
    assert public_apis._date("2026-07-21 09:00:00 UTC") == "2026-07-21"
    assert public_apis._date("2026-07-21") == "2026-07-21"
    assert public_apis._date(None) is None
    assert public_apis._date("bilinmiyor") is None
