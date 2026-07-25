"""Sözlük bütünlüğü.

Sözlük, ilan tarafı ile CV tarafının **ortak dilidir**. Buradaki bir bozulma
sessizdir: yinelenen anahtar bir terimi gölgeler, çok kısa bir yüzey biçimi
alakasız metinlerle eşleşir, tanınmayan bir kategori gate mantığını atlar.
Hiçbiri hata vermez; yalnızca kullanıcı yanlış eşleşme görür.
"""

from __future__ import annotations

import collections

import pytest

from isuygun_core.domain import GATE_RELEVANT_CATEGORIES, NON_DISCRIMINATIVE_CATEGORIES
from isuygun_ingest import lexicon as L

_KNOWN_CATEGORIES = {
    L.SKILL, L.LICENSE, L.CERT, L.EXPERIENCE, L.LANGUAGE, L.EDUCATION, L.SHIFT,
}


def test_term_keys_are_unique():
    """Yinelenen anahtar, ikinci terimi `BY_KEY`'de görünmez yapar."""
    dupes = [k for k, n in collections.Counter(t.key for t in L.TERMS).items() if n > 1]
    assert dupes == [], dupes


def test_by_key_covers_every_term():
    assert len(L.BY_KEY) == len(L.TERMS)


def test_no_surface_form_belongs_to_two_terms():
    """Aynı biçim iki terime aitse hangisinin kazandığı sıraya bağlı kalır."""
    counts = collections.Counter(L.fold(f) for t in L.TERMS for f in t.forms)
    shared = [f for f, n in counts.items() if n > 1]
    assert shared == [], shared


def test_categories_are_known():
    """Tanınmayan kategori, gate ve ayırt edicilik mantığını sessizce atlar."""
    unknown = {t.category for t in L.TERMS} - _KNOWN_CATEGORIES
    assert unknown == set(), unknown


def test_gate_categories_are_represented():
    """En az bir gate alanı olmalı; yoksa D-012 hiç devreye girmez."""
    assert {t.category for t in L.TERMS} & GATE_RELEVANT_CATEGORIES


def test_non_discriminative_categories_exist_in_lexicon():
    """D-021 bu kategorilere dayanıyor; sözlükte karşılıkları olmalı."""
    assert {t.category for t in L.TERMS} & NON_DISCRIMINATIVE_CATEGORIES


def test_surface_forms_are_long_enough():
    """Çok kısa biçimler rastgele metinle eşleşir.

    İki karakterlik biçimler yalnızca ayırt edici teknoloji kısaltmaları için
    kabul edilir; liste açıkça yazılır ki yenisi fark edilmeden eklenmesin.
    """
    allowed_short = {"js", "ts", "c#", "go", "qa", "bi", "ui"}
    too_short = {
        L.fold(f) for t in L.TERMS for f in t.forms
        if len(L.fold(f)) <= 2 and L.fold(f) not in allowed_short
    }
    assert too_short == set(), too_short


def test_labels_are_turkish_facing_and_unique():
    """Etiketler kullanıcıya gösteriliyor; tekrar eden etiket kafa karıştırır."""
    dupes = [l for l, n in collections.Counter(t.label for t in L.TERMS).items() if n > 1]
    assert dupes == [], dupes


def test_every_term_has_at_least_one_form():
    empty = [t.key for t in L.TERMS if not t.forms]
    assert empty == [], empty


def test_clusters_are_stable_labels():
    """Küme adları arayüzde filtre olarak görünüyor; boş olamaz."""
    assert all(t.cluster.strip() for t in L.TERMS)
    assert len(L.clusters()) >= 5


# --------------------------------------------------------------------------
# Tarama davranışı
# --------------------------------------------------------------------------


def test_scan_respects_word_boundaries():
    """Regresyon: "geçerli" içindeki "gece" gece vardiyası önerdiriyordu."""
    keys = {h.term.key for h in L.scan("Psikoteknik belgesi geçerli")}
    assert "night_shift" not in keys


def test_scan_folds_turkish_and_german():
    """Aynı terim üç dilde de bulunmalı; kaynaklar karışık dilde."""
    assert "warehouse" in {h.term.key for h in L.scan("Depo görevlisi aranıyor")}
    assert "warehouse" in {h.term.key for h in L.scan("Lagerhelfer gesucht")}
    assert "warehouse" in {h.term.key for h in L.scan("Warehouse associate")}


def test_scan_reports_first_position_only():
    """Bir terim birden çok geçse de tek kayıt üretir; konum ilk geçiştir."""
    hits = [h for h in L.scan("Python. Sonra yine Python.") if h.term.key == "python"]
    assert len(hits) == 1
    assert hits[0].position == 0


def test_scan_reads_years_only_near_the_match():
    """Uzaktaki bir sayı yıl bilgisi sanılmamalı."""
    near = L.scan("5 yıl Python deneyimi")
    assert next(h for h in near if h.term.key == "python").years == 5
    far = L.scan("Python bilgisi. " + "dolgu " * 60 + "12 yıl sektör tecrübesi")
    assert next(h for h in far if h.term.key == "python").years is None


def test_scan_is_deterministic():
    text = "Python, Docker, İngilizce, lisans mezunu"
    assert [h.term.key for h in L.scan(text)] == [h.term.key for h in L.scan(text)]


def test_legal_eligibility_detected_but_separate():
    """D-013: askerlik şartı tespit edilir ama normal terim olarak dönmez."""
    assert "military" in L.find_legal_eligibility("Askerliğini tamamlamış olmak")
    assert not any(h.term.key.startswith("legal") for h in L.scan("askerliğini tamamlamış"))


# --------------------------------------------------------------------------
# İSG: sertifika ≠ uzmanlık (canlı persona testinden çıkan düzeltme)
# --------------------------------------------------------------------------
# Tek token'ken kaynakçı profilinin 24 sonucunun 11'i "İş Güvenliği Uzmanı"
# ilanıydı. 17.858 ilanlık ölçümde token 174 ilanda tutuyordu ve 128'i sırf
# "iş sağlığı ve güvenliği kurallarına uymak" kalıp metninden geliyordu.

#: Türkiye ilanlarında neredeyse standart olan güvenlik kalıp metinleri.
#: Bunlar bir NİTELİK beyan etmez; hiçbir İSG token'ını tetiklememeli.
ISG_KALIP_METINLERI = (
    "İş sağlığı ve güvenliği kurallarına uymak",
    "İSG kurallarına uygun çalışmak",
    "İş sağlığı ve güvenliği talimatlarına riayet etmek",
    "Şirketin iş sağlığı ve güvenliği politikalarına uyum",
)


@pytest.mark.parametrize("metin", ISG_KALIP_METINLERI)
def test_isg_kalip_metni_hicbir_isg_tokenini_tetiklemez(metin):
    """Kalıp metin nitelik değildir — Aşçı/Garson ilanlarını İSG'ye bağlıyordu."""
    anahtarlar = {h.term.key for h in L.scan(metin)}
    assert "osgb" not in anahtarlar, f"eğitim sertifikası kalıp metne takıldı: {metin!r}"
    assert "isg_specialist" not in anahtarlar, f"uzmanlık kalıp metne takıldı: {metin!r}"


@pytest.mark.parametrize("metin", [
    "İş Güvenliği Uzmanı aranıyor",
    "C sınıfı iş güvenliği uzmanı",
    "İSG uzmanı olarak görevlendirilmek üzere",
    "İş sağlığı ve güvenliği uzmanı (B sınıfı)",
])
def test_uzmanlik_ilanlari_uzmanlik_belgesine_baglanir(metin):
    anahtarlar = {h.term.key for h in L.scan(metin)}
    assert "isg_specialist" in anahtarlar, f"uzmanlık ilanı tanınmadı: {metin!r}"
    # Ruhsatlı meslek, çalışanın temel eğitim sertifikasıyla KARIŞMAMALI.
    assert "osgb" not in anahtarlar


@pytest.mark.parametrize("metin", [
    "İş güvenliği sertifikası olan adaylar",
    "İSG eğitimi almış olmak",
    "İş güvenliği belgesi tercih edilir",
])
def test_egitim_sertifikasi_ayri_tokene_baglanir(metin):
    anahtarlar = {h.term.key for h in L.scan(metin)}
    assert "osgb" in anahtarlar, f"eğitim sertifikası tanınmadı: {metin!r}"
    assert "isg_specialist" not in anahtarlar, \
        "temel sertifika, ruhsatlı uzmanlık sanılıyor — kullanıcıyı giremeyeceği " \
        "mesleğe yönlendirir"


def test_osgb_isveren_turu_nitelik_sayilmaz():
    """OSGB bir işveren türü (Ortak Sağlık Güvenlik Birimi), çalışan niteliği değil."""
    anahtarlar = {h.term.key for h in L.scan("Bir OSGB firmasında görevlendirilmek üzere")}
    assert "osgb" not in anahtarlar
    assert "isg_specialist" not in anahtarlar


def test_uzmanlik_belgesi_dogrulama_kapisina_tabidir():
    """Ruhsatlı meslek: doğrulanmadan "karşılanıyor" sayılamaz (D-012)."""
    uzman = next(t for t in L.TERMS if t.key == "isg_specialist")
    egitim = next(t for t in L.TERMS if t.key == "osgb")
    assert uzman.category in GATE_RELEVANT_CATEGORIES
    # Temel eğitim sertifikası yasal kapı DEĞİL — kaynakçı olmanın önkoşulu değil.
    assert egitim.category not in GATE_RELEVANT_CATEGORIES
