"""Golden set korkuluğu (D-062).

Rapor tek başına çürür: kimse çalıştırmazsa aşırı iddia sessizce artar. Bu test
ölçümü **CI'ya bağlar** — eşiği aşan bir değişiklik kırmızıya düşer.

Eşik bilinçli olarak *bugünün gerçeği* (0,486) üzerine konmuştur, hedef değil.
Hedef sıfıra yakındır; eşik her iyileştirmede AŞAĞI çekilmelidir. Yukarı
çekilmesi ancak golden set büyüdüğünde ve gerekçesi yazıldığında meşrudur.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_EVAL = Path(__file__).resolve().parents[3] / "golden" / "eval.py"

#: Ölçülen zemin (2026-07-25, 37 vaka).
#:   D-062 (kıdem körlüğü varken) : 18/37 = %48,6
#:   D-063 (kıdem tavanı sonrası) :  8/37 = %21,6  <-- şimdiki
#: Kalan 8 vaka kıdemden değil: zorunlu şartın bilinmemesi (2), meslek kayması
#: (2) ve çekirdek becerinin doğrulanmamış olması (4). Sıradaki iyileştirmeler
#: bunları hedefler ve eşik yine aşağı çekilir.
ASIRI_IDDIA_ESIGI = 0.22


@pytest.fixture(scope="module")
def rapor():
    if not _EVAL.is_file():
        pytest.skip("golden/eval.py yok")
    spec = importlib.util.spec_from_file_location("golden_eval", _EVAL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run()


def test_golden_set_yuklenebilir(rapor):
    """Set okunabilmeli ve boş olmamalı — sessizce 0 vakaya düşmek, testin
    yeşil kalıp hiçbir şey ölçmemesi demekti."""
    assert rapor["vaka"] >= 30, f"golden set küçülmüş: {rapor['vaka']} vaka"


def test_asiri_iddia_esigi_asilmiyor(rapor):
    """**Birincil korkuluk.** Aşırı iddia = savunulamayacak kadar yüksek bant.

    Bu ürünün kardinal günahı: kullanıcı "güçlü eşleşme" görüp başvurur, boşa
    umutlanır. D-005 ve D-019'un varlık sebebi tam olarak budur.
    """
    oran = rapor["asiri_iddia_orani"]
    assert oran <= ASIRI_IDDIA_ESIGI, (
        f"aşırı iddia oranı yükseldi: %{100*oran:.1f} > "
        f"%{100*ASIRI_IDDIA_ESIGI:.1f} eşiği. "
        f"Eşleşme kuralları savunulamayan bant üretmeye başladı."
    )


def test_alakasiz_ilana_bant_verilmiyor(rapor):
    """Mesleği hiç uymayan ilana bant verilmemeli — şoföre 'risk yöneticiliği'
    için eşleşme derecesi göstermek anlamsızdır (D-019)."""
    assert rapor["alakasiza_bant"] == 0, (
        f"{rapor['alakasiza_bant']} alakasız ilana bant verildi"
    )
