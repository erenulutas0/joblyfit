"""İşveren doğrudan ilan girişi (D-078).

Buradaki testlerin çoğu **kabul etmemeyi** doğruluyor. Sebebi şu: bu panonun
yayımcısı biziz. Üçüncü taraf akışlarında ayrımcı dili *işaretliyoruz* çünkü o
ilanları biz yayımlamıyoruz; burada yayımlarsak "her 28 Türkiye ilanından
1'inde ayrımcı ifade var" diye ölçüm yayımlayan ürün kendi iddiasını çürütür.

İkinci tema: onaylanmamış ilan **hiçbir yerde** görünmemeli. Moderasyon
kuyruğunun tek değeri budur; sızarsa kuyruk tiyatroya döner.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from isuygun_api import employer as emp
from isuygun_api.main import app
from isuygun_api.store import STORE


@pytest.fixture(autouse=True)
def _temiz_db(tmp_path, monkeypatch):
    """Her test kendi veritabanıyla çalışır — sıra bağımlılığı olmasın."""
    monkeypatch.setenv("ISUYGUN_EMPLOYER_DB", str(tmp_path / "emp.db"))
    emp.reset_for_tests()
    yield
    emp.reset_for_tests()


@pytest.fixture()
def client():
    return TestClient(app)


GECERLI = {
    "employer": "Anadolu Metal A.Ş.",
    "contact": "ik@ornek.invalid",
    "title": "Gazaltı Kaynakçı",
    "city": "Kocaeli",
    "description": (
        "Fabrikamızda gazaltı kaynak işlerinde çalışacak takım arkadaşı "
        "arıyoruz. Vardiyalı düzende çalışılacaktır; iş güvenliği "
        "kurallarına uyum beklenmektedir. Servis ve yemek sağlanır."
    ),
    "requirements": [
        {"key": "welding", "kind": "hard"},
        {"key": "highschool", "kind": "required"},
        {"key": "shift_work", "kind": "required"},
        {"key": "quality", "kind": "preferred"},
    ],
    "deadline": "2099-12-31",
    "experience_level": "mid",
}


# --------------------------------------------------------------------------
# Gönderim
# --------------------------------------------------------------------------


def test_gecerli_ilan_kuyruga_girer_ama_yayimlanmaz(client):
    r = client.post("/api/employer/postings", json=GECERLI)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["status"] == "pending"
    # ONAYLANMADAN korpusa girmemeli.
    assert d["id"] not in STORE.postings
    assert emp.to_postings() == []


def test_ayrimci_ifade_yayimlanmaz_ve_kaydedilmez(client):
    """Bloklanır ve KAYDA DA ALINMAZ.

    Kaydetmek, o ilanı bir gün yanlışlıkla onaylanabilir kılar; kuyrukta
    duran ayrımcı bir ilan, tek bir yanlış tıklamayla yayımlanmış ilandır.
    """
    kotu = {**GECERLI, "description": GECERLI["description"] + " Sadece erkek eleman alınacaktır."}
    r = client.post("/api/employer/postings", json=kotu)
    assert r.status_code == 422
    detay = r.json()["detail"]
    # Kullanıcı NEYİ düzelteceğini bilmeli: gerekçe ve kanıt döner.
    assert "dışlayıcı" in detay["reason"]
    assert detay["evidence"]
    assert emp.liste("pending") == []


def test_kapsayici_ifade_engellenmez(client):
    """"kadın ve erkek tüm adaylar" ayrımcılık değil, tersidir (D-075)."""
    iyi = {**GECERLI,
           "description": GECERLI["description"] + " Kadın ve erkek tüm adaylar başvurabilir."}
    assert client.post("/api/employer/postings", json=iyi).status_code == 200


def test_sartsiz_ilan_kabul_edilmez(client):
    """Şartsız ilan, adayın kendini karşılaştıracağı hiçbir şey sunmaz."""
    r = client.post("/api/employer/postings", json={**GECERLI, "requirements": []})
    assert r.status_code == 422
    assert "şart" in r.json()["detail"]["reason"]


def test_cok_kisa_metin_kabul_edilmez(client):
    r = client.post("/api/employer/postings", json={**GECERLI, "description": "Kaynakçı."})
    assert r.status_code == 422
    assert "80 karakter" in r.json()["detail"]["reason"]


def test_gecersiz_sart_turu_reddedilir(client):
    """Bilinmeyen `kind` sessizce 1.0 ağırlığa düşerdi — "hard" yazım hatası
    zorunlu şartı yumuşatırdı."""
    r = client.post("/api/employer/postings",
                    json={**GECERLI, "requirements": [{"key": "welding", "kind": "zorunlu"}]})
    assert r.status_code == 422


def test_gecersiz_tarih_reddedilir(client):
    r = client.post("/api/employer/postings", json={**GECERLI, "deadline": "31.12.2099"})
    assert r.status_code == 422


# --------------------------------------------------------------------------
# Moderasyon kapısı
# --------------------------------------------------------------------------


def test_moderasyon_token_yoksa_uclar_404(client, monkeypatch):
    """Ayarlanmamış dağıtımda moderasyon HİÇ YOK — varsayılan sır bırakmıyoruz."""
    monkeypatch.delenv("ISUYGUN_ADMIN_TOKEN", raising=False)
    assert client.get("/api/employer/queue").status_code == 404
    assert client.post("/api/employer/queue/emp-x/approve").status_code == 404


def test_yanlis_token_403(client, monkeypatch):
    monkeypatch.setenv("ISUYGUN_ADMIN_TOKEN", "dogru-sir")
    r = client.get("/api/employer/queue", headers={"X-Admin-Token": "yanlis"})
    assert r.status_code == 403


def test_onay_ilani_korpusa_sokar(client, monkeypatch):
    monkeypatch.setenv("ISUYGUN_ADMIN_TOKEN", "dogru-sir")
    pid = client.post("/api/employer/postings", json=GECERLI).json()["id"]

    kuyruk = client.get("/api/employer/queue",
                        headers={"X-Admin-Token": "dogru-sir"}).json()
    assert [i["id"] for i in kuyruk["items"]] == [pid]

    r = client.post(f"/api/employer/queue/{pid}/approve",
                    headers={"X-Admin-Token": "dogru-sir"})
    assert r.status_code == 200
    postalar = emp.to_postings()
    assert len(postalar) == 1
    p = postalar[0]
    assert p.job.job_id == pid
    assert p.provenance["source_id"] == "src-direct-employer"
    # ASIL KAZANÇ: yapılandırılmış giriş çok şart demek. Aggregator ortalaması
    # ilan başına ~1,3 şart; kanıt tavanı (D-022) orada bandı "şartlı"da tutuyor.
    assert len(p.job.requirements) == 4
    assert {r.kind for r in p.job.requirements} == {"hard", "required", "preferred"}


def test_red_ilani_korpusa_sokmaz(client, monkeypatch):
    monkeypatch.setenv("ISUYGUN_ADMIN_TOKEN", "dogru-sir")
    pid = client.post("/api/employer/postings", json=GECERLI).json()["id"]
    client.post(f"/api/employer/queue/{pid}/reject",
                headers={"X-Admin-Token": "dogru-sir"})
    assert emp.to_postings() == []


def test_ayni_ilan_iki_kez_onaylanamaz(client, monkeypatch):
    monkeypatch.setenv("ISUYGUN_ADMIN_TOKEN", "dogru-sir")
    pid = client.post("/api/employer/postings", json=GECERLI).json()["id"]
    h = {"X-Admin-Token": "dogru-sir"}
    assert client.post(f"/api/employer/queue/{pid}/approve", headers=h).status_code == 200
    # İkinci çağrı bekleyen kayıt bulamaz: durum makinesi tek yönlü.
    assert client.post(f"/api/employer/queue/{pid}/reject", headers=h).status_code == 404


# --------------------------------------------------------------------------
# Son başvuru tarihi
# --------------------------------------------------------------------------


def test_suresi_gecen_ilan_korpustan_duser(client, monkeypatch):
    """İşverenin yazdığı tarih geçtiyse ilan ölüdür; göstermek zaman çalar."""
    monkeypatch.setenv("ISUYGUN_ADMIN_TOKEN", "dogru-sir")
    pid = client.post("/api/employer/postings",
                      json={**GECERLI, "deadline": "2020-01-01"}).json()["id"]
    client.post(f"/api/employer/queue/{pid}/approve",
                headers={"X-Admin-Token": "dogru-sir"})
    # Onaylı ama süresi geçmiş → korpusta yok.
    assert [i["id"] for i in emp.liste("approved")] == [pid]
    assert emp.to_postings() == []


def test_tarihsiz_ilan_duser_degil(client, monkeypatch):
    monkeypatch.setenv("ISUYGUN_ADMIN_TOKEN", "dogru-sir")
    govde = {**GECERLI}
    govde.pop("deadline")
    pid = client.post("/api/employer/postings", json=govde).json()["id"]
    client.post(f"/api/employer/queue/{pid}/approve",
                headers={"X-Admin-Token": "dogru-sir"})
    assert [p.job.job_id for p in emp.to_postings()] == [pid]


# --------------------------------------------------------------------------
# Hedefli tazeleme
# --------------------------------------------------------------------------


def test_tazeleme_eski_dogrudan_ilanlari_duserir(client, monkeypatch):
    """Reddedilen/süresi geçen ilan BELLEKTEN de düşmeli.

    Yalnızca eklemek yetmez: onayı geri alınan bir ilan aksi halde
    `STORE.postings`te kalır ve listede görünmeye devam eder.
    """
    monkeypatch.setenv("ISUYGUN_ADMIN_TOKEN", "s")
    h = {"X-Admin-Token": "s"}
    pid = client.post("/api/employer/postings", json=GECERLI).json()["id"]
    client.post(f"/api/employer/queue/{pid}/approve", headers=h)
    assert pid in STORE.postings

    # Kaydı doğrudan reddedilmiş yapıp tazele: bellekten düşmeli.
    emp._db().execute("UPDATE employer_postings SET status='rejected' WHERE id=?", (pid,))
    emp._db().commit()
    STORE.reload_direct_employer()
    assert pid not in STORE.postings
    assert pid not in STORE.search_index


def test_tazeleme_diger_ilanlara_dokunmaz(client, monkeypatch):
    """Onay, korpusun geri kalanını yeniden kurmamalı.

    İlk sürüm onay ucunda tam `load()` çağırıyordu: tek satır için 14.400
    ilanlık korpus yeniden kuruluyordu (ölçüm 30 sn → 0,8 sn).
    """
    monkeypatch.setenv("ISUYGUN_ADMIN_TOKEN", "s")
    STORE.load(live=False)
    disardan = {jid for jid, p in STORE.postings.items()
                if (p.provenance or {}).get("source_id") != "src-direct-employer"}
    surum_once = STORE.corpus_version

    pid = client.post("/api/employer/postings", json=GECERLI).json()["id"]
    client.post(f"/api/employer/queue/{pid}/approve", headers={"X-Admin-Token": "s"})

    kalan = {jid for jid, p in STORE.postings.items()
             if (p.provenance or {}).get("source_id") != "src-direct-employer"}
    assert kalan == disardan, "doğrudan olmayan ilanlar değişti — korpus yeniden kurulmuş"
    assert STORE.corpus_version == surum_once + 1, "korpus sürümü tam bir artmalı"
