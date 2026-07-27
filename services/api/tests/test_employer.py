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
    # D-083: basvuru baglantisi ZORUNLU. Adayin basvuramadigi
    # bir ilan gorunur ama ise yaramaz.
    "apply_url": "https://anadolumetal.example/ilan/kaynakci",
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


# --------------------------------------------------------------------------
# Form sayfası
# --------------------------------------------------------------------------


def test_isveren_formu_servis_edilir(client):
    """`/isveren` UYGULAMA alan adında durur.

    Tanıtım domaininden servis edilseydi form, API ile çapraz-origin olurdu ve
    tek bir form için CORS açmak gereksiz bir yüzey açardı.
    """
    r = client.get("/isveren")
    assert r.status_code == 200
    html = r.text
    # Yol JS'de `API + "/employer/postings"` olarak birleşiyor; tam dize
    # HTML'de yok. İkisini ayrı ayrı ararız.
    assert 'const API = "/api"' in html
    assert '"/employer/postings"' in html, "form gönderim ucuna bağlı değil"
    # Sayfa SEO yüzeyi değil; kök domain o işi yapıyor.
    assert 'content="noindex' in html
    # İşverene baştan söylenen kurallar sayfada YAZILI olmalı — sözlü vaat
    # değil, sayfanın kendisi taahhüt.
    for soz in ("Ücret almıyoruz", "sıralama satmıyoruz",
                "Ayrımcı ifade yayımlamıyoruz", "moderasyon"):
        assert soz.lower() in html.lower(), f"taahhüt sayfada yok: {soz!r}"


def test_formda_bekleyen_secim_gonderirken_absorbe_edilir(client):
    """Açılır listede seçili kalan şart YUTULMAMALI.

    CANLIDA YAŞANDI: işveren listeden şartı seçti, "ekle"ye basmadı, gönderdi
    ve sunucudan "en az bir şart seçmelisin" (422) aldı — oysa seçmişti. Bu,
    onboarding'deki anahtar kelime kutusunda düzelttiğim hatanın (D-070)
    aynısıydı ve formu yazarken tekrarlamışım.

    Burada test edilen sayfanın JS'i: absorbe eden kod formda olduğu için
    varlığını HTML üzerinde doğruluyoruz. Sunucu tarafı zaten şartsız gönderimi
    reddediyor (`test_sartsiz_ilan_kabul_edilmez`); iki koruma birlikte durur.
    """
    html = client.get("/isveren").text
    # Gönderim akışı, bekleyen seçimi eklemeyi ÇAĞIRMALI.
    assert "ekleSecili()" in html, "bekleyen seçim absorbe edilmiyor"
    # Hazır olmadan gönder düğmesi kapalı kalmalı: 422'yi hiç görmemek en iyisi.
    # D-083'te hazırlık koşulu ikiye çıktı (şart + başvuru bağlantısı), bu
    # yüzden dize değişti; DEĞİŞMEYEN şey düğmenin koşula bağlı olması.
    assert '$("#send").disabled = !(sartVar && linkOk)' in html


# ---------------------------------------------------------------------------
# D-083 — moderasyon paneli
# ---------------------------------------------------------------------------
# D-078'de moderasyon UCLARI vardi, ARAYUZU yoktu: onay/red yalnizca elle
# `curl` ile yapilabiliyordu. Bunun bedeli sessizdi ama gercek -- onaylamak
# icin ilan METNINI okumak gerekir, oysa curl cikitisi JSON kacisli tek satir
# ve sartlar `{"key":"excel"}` gibi ANAHTAR olarak geliyordu. Moderator
# pratikte neyi onayladigini gormuyordu.


def test_moderasyon_paneli_servis_edilir(client):
    r = client.get("/moderasyon")
    assert r.status_code == 200
    html = r.text
    # Panel arama motorlarina hic girmemeli: isveren formundan farki "nofollow".
    assert 'content="noindex, nofollow"' in html


def test_moderasyon_paneli_sirri_ICERMEZ(client, monkeypatch):
    """Sayfanin kendisi herkese acik; icinde sir OLMAMALI.

    Yetki kapisi sunucuda (`_require_admin`). Sayfaya token gomulseydi
    "gizli URL" guvenlik sanilir ve sir HTML'de dagitilmis olurdu.
    """
    monkeypatch.setenv("ISUYGUN_ADMIN_TOKEN", "cok-gizli-deger-123")
    html = client.get("/moderasyon").text
    assert "cok-gizli-deger-123" not in html
    # Token istekte BASLIKTA gitmeli, URL'de degil: URL'ler loglanir.
    assert '"X-Admin-Token"' in html
    assert "admin_token=" not in html, "token URL parametresine yazılmış"


def test_moderasyon_paneli_kararin_tek_yonlu_oldugunu_soyler(client):
    """Red geri alinamaz (`WHERE status='pending'`). Bunu SAYFA yazmali.

    Geri alinamaz bir islemi geri alinabilir sanmak, moderatorun yanlis
    tikladiginda ilani kurtaramamasi demek.
    """
    html = client.get("/moderasyon").text
    assert "tekrar bekleyene alınamaz" in html
    # Isverenin iletisim bilgisi panelde gorunur ama YAYIMLANMAZ; ayrimi
    # panelin kendisi soylemeli, yoksa moderator yayimlandigini sanabilir.
    assert "yayımlanmaz" in html


def test_moderasyon_paneli_kullanici_metnini_kacirmadan_basar(client):
    """Ilan metni KULLANICI GIRDISI: `innerHTML` ile basmak XSS kanalidir.

    Hem de tam yetkili operatorun sekmesinde -- panelden calinacak sey
    moderasyon anahtarinin kendisi olurdu.
    """
    html = client.get("/moderasyon").text
    assert "textContent" in html
    # Ilan alanlarini basan yol `innerHTML` KULLANMAMALI.
    assert "innerHTML" not in html, "kullanıcı metni innerHTML ile basılıyor"


def test_moderasyon_paneli_403_ile_404u_ayirir(client):
    """"Yanlis anahtar" ile "moderasyon kapali" ayri sorunlar, ayri cozumler.

    Ikisine de "islem basarisiz" demek, operatoru `.env.prod`a mi baksin
    yoksa anahtari mi duzeltsin bilmeden birakir.
    """
    html = client.get("/moderasyon").text
    assert "Anahtar geçersiz" in html
    assert "ISUYGUN_ADMIN_TOKEN ayarlı değil" in html


def test_moderasyon_paneli_anahtari_kalici_saklamaz(client):
    """Anahtar sessionStorage'da: localStorage paylasilan makinede kalirdi."""
    html = client.get("/moderasyon").text
    assert "sessionStorage" in html
    # KULLANIMI arar, kelimeyi degil: ilk yazdigim hali yorumdaki
    # "localStorage kalici olurdu" cumlesine takiliyordu.
    for cagri in ("localStorage.setItem", "localStorage.getItem"):
        assert cagri not in html, f"moderasyon anahtarı kalıcı depoya yazılıyor: {cagri}"


def test_basvuru_baglantisi_zorunlu(client):
    """Baglantisiz ilan kabul edilmez (D-083).

    ESKIDEN ISTEGE BAGLIYDI ve sonucu su oldu: `to_postings` bos URL yaziyor,
    arayuz `href=""` basiyordu -- "ilana git" dugmesi sayfayi yeniden
    yukluyordu. Aday ilani goruyor ama BASVURAMIYOR. `contact` alanini
    yayimlamayacagimiza soz verdigimiz icin baska yol da kalmiyordu.
    """
    govde = dict(GECERLI); govde.pop("apply_url")
    r = client.post("/api/employer/postings", json=govde)
    assert r.status_code == 422
    assert "zorunlu" in r.json()["detail"]["reason"]


def test_mailto_kabul_edilir(client):
    """Web sitesi olmayan kucuk isveren de ilan verebilmeli.

    Zorunlulugu sadece `https://` ile sinirlamak, bu ozelligin var oldugu
    isveren kitlesini disarida birakirdi.
    """
    govde = dict(GECERLI, apply_url="mailto:ik@anadolumetal.example")
    assert client.post("/api/employer/postings", json=govde).status_code == 200


def test_bozuk_baglanti_reddedilir(client):
    for bozuk in ("anadolumetal.example", "javascript:alert(1)", "ftp://a.b/c",
                  "mailto:duz-metin"):
        govde = dict(GECERLI, apply_url=bozuk)
        r = client.post("/api/employer/postings", json=govde)
        assert r.status_code == 422, f"kabul edilmemeliydi: {bozuk!r}"


def test_onayli_ilan_calisan_baglantiyla_gelir(client, monkeypatch):
    """Ucdan uca: gonderim -> onay -> korpus -> akista KULLANILABILIR baglanti.

    `test_every_feed_item_has_a_usable_apply_link` bu acigi yakalayan testti;
    burada isveren yolunda ozel olarak tekrar dogruluyoruz.
    """
    monkeypatch.setenv("ISUYGUN_ADMIN_TOKEN", "t")
    pid = client.post("/api/employer/postings", json=GECERLI).json()["id"]
    client.post(f"/api/employer/queue/{pid}/approve", headers={"X-Admin-Token": "t"})
    akis = client.get("/api/feed").json()
    bizim = [j for j in akis["evaluated"] + akis["unevaluated"] if j["job_id"] == pid]
    assert bizim, "onaylanan ilan akışta yok"
    assert bizim[0]["url"].startswith("http")


def test_formda_baglanti_yazilinca_gonder_acilir(client):
    """Sayfa, baglanti yazildiginda hazirligi YENIDEN hesaplamali.

    Ilk yazdigim halde `cizReq` yalnizca sart secimi degisince cagriliyordu;
    gecerli bir URL girmek dugmeyi acmiyordu. Duzeltmeye calistigim hatanin
    ta kendisi -- bu yuzden bagi testle sabitliyorum.
    """
    html = client.get("/isveren").text
    assert '$("#apply_url").addEventListener("input", cizReq)' in html


def test_arayuz_bos_baglantida_olu_dugme_basmaz(client):
    """`href=""` sayfayi yeniden yukler -- kullanici tiklar, hicbir sey olmaz.

    Yeni gonderimlerde baglanti artik zorunlu (yukaridaki testler), ama bu dal
    ESKI kayitlar icin savunma: onaylanmis, baglantisiz bir ilan hala
    veritabaninda durabilir.

    Sablonun kendisi test ediliyor cunku app.html'in JS'i modul kapsaminda ve
    disaridan cagrilamiyor. Ucdan uca yol `test_onayli_ilan_calisan_
    baglantiyla_gelir`de dogrulaniyor.
    """
    html = client.get("/").text
    assert "${j.url?`<div class=\"apply\">" in html, \
        "başvuru düğmesi boş URL'ye karşı korunmuyor"
    assert "Bu ilanda başvuru bağlantısı yok" in html, \
        "URL yoksa kullanıcıya sebebi söylenmiyor"
