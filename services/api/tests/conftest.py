"""Testler kalıcı profil veritabanına **yazmaz**.

Aksi halde bir test koşusu geliştiricinin gerçek profilini siler ve testler
birbirinin durumunu görür. Ortam değişkeni import'tan önce ayarlanmalı.
"""

import os

os.environ.setdefault("ISUYGUN_DB", ":memory:")
# Eski (sunucu-profilli) yüzey testleri: uçlar D-059'la üretimde kapandı;
# testler davranışlarını hâlâ doğrular, bu yüzden bayrak burada açılır.
os.environ.setdefault("ISUYGUN_CLASSIC", "1")
