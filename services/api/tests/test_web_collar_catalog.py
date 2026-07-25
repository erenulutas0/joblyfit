"""Arayüzdeki yaka ayrımı ile lexicon grupları arasındaki sessiz uyuşmazlık.

``web/app.html`` beceri matrisini yakaya göre filtreler (``CLUSTERS_BLUE``) ama
bunu lexicon'dan **bağımsız** bir sabit listeyle yapar. İki dosya birbirini
bilmediği için lexicon'a yeni bir grup eklendiğinde arayüz onu sessizce tek bir
yakaya hapsedebilir — hiçbir test kırılmaz, hiçbir hata düşmez.

Canlı persona testinde olan tam buydu: ``Eğitim düzeyi``, ``Çalışma düzeni`` ve
``Dil`` grupları mavi yakaya **hiç** gösterilmiyordu. Kaynakçı ilanı "Tercihen
Meslek Lisesi mezunu" istiyor, kullanıcının bunu beyan edecek yeri yok → şart
kalıcı olarak "bilinmeyen" kalıyor, kanıt oranı tavanı (D-064) devreye giriyor
ve 24 sonucun 24'ü "şartlı eşleşme"de sıkışıyordu. Vardiya ve dilde durum daha
da ters: mavi yakada beyaz yakadan DAHA çok isteniyorlar.

Buradaki iddia grup ADLARINA değil lexicon'un kendi **kategorisine** dayanır:
``LANGUAGE``/``EDUCATION``/``SHIFT`` mesleği değil kişiyi tanımlar, dolayısıyla
iki yakada da sorulmalıdır. Yeni bir eğitim token'ı yeni bir grupla eklenirse
bu test onu da yakalar.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from isuygun_ingest.lexicon import EDUCATION, LANGUAGE, SHIFT, TERMS

#: Kişiye ait çapraz nitelikler — mesleğe göre kısıtlanamaz.
CAPRAZ_KATEGORILER = {EDUCATION, LANGUAGE, SHIFT}

#: Lexicon'da henüz token'ı olmayan ama bilinçli tutulan gruplar. "İnşaat"
#: Türkiye'de büyük bir sektör (sıvacı/kalıpçı/demirci) ve token'lar
#: eklendiğinde kendiliğinden mavi yakaya düşsün diye listede duruyor.
TOKENSIZ_IZINLI = {"İnşaat"}


def _app_html() -> str:
    kok = Path(__file__).resolve().parents[3]
    yol = kok / "web" / "app.html"
    if not yol.is_file():                                   # pragma: no cover
        pytest.skip(f"web/app.html bulunamadı: {yol}")
    return yol.read_text(encoding="utf-8")


def _js_dizi(ad: str, kaynak: str) -> set[str]:
    """``const AD=["a","b"];`` biçimindeki JS dizisini okur."""
    m = re.search(rf"const\s+{ad}\s*=\s*\[(.*?)\]\s*;", kaynak, re.S)
    assert m, f"{ad} web/app.html içinde bulunamadı — yeniden adlandırıldı mı?"
    return set(re.findall(r'"([^"]+)"', m.group(1)))


@pytest.fixture(scope="module")
def kaynak() -> str:
    return _app_html()


@pytest.fixture(scope="module")
def mavi(kaynak: str) -> set[str]:
    return _js_dizi("CLUSTERS_BLUE", kaynak)


@pytest.fixture(scope="module")
def ortak(kaynak: str) -> set[str]:
    return _js_dizi("CLUSTERS_SHARED", kaynak)


def test_capraz_nitelik_gruplari_iki_yakada_da_sorulur(ortak: set[str]) -> None:
    """Eğitim/dil/vardiya grupları CLUSTERS_SHARED'de olmalı.

    Olmazlarsa mavi yaka kullanıcı bu alanları beyan edemez; ilan onları
    isterse şart kalıcı "bilinmeyen" kalır ve band tavana yapışır.
    """
    gerekli = {t.cluster for t in TERMS if t.category in CAPRAZ_KATEGORILER}
    assert gerekli, "lexicon'da hiç eğitim/dil/vardiya token'ı yok — beklenmedik"
    eksik = gerekli - ortak
    assert not eksik, (
        f"Bu gruplar kişiye ait çapraz nitelik ama CLUSTERS_SHARED'de yok: "
        f"{sorted(eksik)}. Mavi yaka kullanıcı bunları beyan edemez."
    )


def test_capraz_gruplar_mesleki_gruplarla_karismaz(
    ortak: set[str], mavi: set[str]
) -> None:
    """Paylaşılan bir grup aynı zamanda "yalnızca mavi" sayılmamalı.

    Karışırsa ``selectableCatalog`` içindeki iki dalın hangisinin kazandığı
    okuyucu için belirsizleşir; niyet tek yerde durmalı.
    """
    cakisma = ortak & mavi
    assert not cakisma, (
        f"Hem CLUSTERS_SHARED hem CLUSTERS_BLUE içinde: {sorted(cakisma)}"
    )


def test_arayuzdeki_grup_adlari_lexiconda_gercekten_var(
    ortak: set[str], mavi: set[str]
) -> None:
    """Grup adları elle yazılmış dizeler — bir harf kayması sessizce token kaybettirir.

    Örnek: "Üretim ve teknik" yerine "Uretim ve teknik" yazılsa mavi yakadan 7
    token birden düşer ve hiçbir şey hata vermez.
    """
    lexicon_gruplari = {t.cluster for t in TERMS}
    bilinmeyen = (ortak | mavi) - lexicon_gruplari - TOKENSIZ_IZINLI
    assert not bilinmeyen, (
        f"web/app.html şu grupları sayıyor ama lexicon'da yok: "
        f"{sorted(bilinmeyen)}. Yazım hatası mı, yoksa TOKENSIZ_IZINLI'ye mi "
        f"eklenmeli?"
    )


def test_tokensiz_izinli_liste_bayatlamaz(mavi: set[str], ortak: set[str]) -> None:
    """İzin verilen tokensiz grup gerçekten tokensiz mi, ve hâlâ sayılıyor mu?

    Token'lar eklendiğinde izin satırı gereksizleşir; kaldırılmazsa gelecekteki
    bir yazım hatasını maskeler.
    """
    lexicon_gruplari = {t.cluster for t in TERMS}
    artik_var = TOKENSIZ_IZINLI & lexicon_gruplari
    assert not artik_var, (
        f"{sorted(artik_var)} artık lexicon'da token'a sahip — TOKENSIZ_IZINLI'den "
        f"çıkarılmalı, yoksa yazım hatalarını gizler."
    )
    olu = TOKENSIZ_IZINLI - (mavi | ortak)
    assert not olu, (
        f"{sorted(olu)} arayüzde hiç sayılmıyor — izin satırı tamamen ölü."
    )
