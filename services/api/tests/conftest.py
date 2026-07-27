"""Testler kalıcı veritabanlarına **yazmaz** ve onlardan **okumaz**.

Aksi halde bir test koşusu geliştiricinin gerçek profilini siler ve testler
birbirinin durumunu görür. Ortam değişkeni import'tan önce ayarlanmalı.
"""

import os
import tempfile

os.environ.setdefault("ISUYGUN_DB", ":memory:")
# Eski (sunucu-profilli) yüzey testleri: uçlar D-059'la üretimde kapandı;
# testler davranışlarını hâlâ doğrular, bu yüzden bayrak burada açılır.
os.environ.setdefault("ISUYGUN_CLASSIC", "1")

# İŞVEREN KUYRUĞU DA İZOLE (D-083). Bu eksikti ve gerçek bir yanlış sonuç
# üretti: `test_employer.py` kendi tmp veritabanını kuruyordu ama DİĞER test
# dosyaları geliştiricinin `.data/employer.db`sini okuyordu. Yerelde elle
# onayladığım bir test ilanı `test_smoke.py`nin başvuru bağlantısı
# değişmezini düşürdü — testin kırılması DOĞRUYDU (o ilanın bağlantısı
# yoktu), ama kırılma sebebi makinemdeki veriydi, kodda değil.
#
# Testin geliştiricinin diskindeki duruma bağlı olması, aynı commit'in bir
# makinede geçip diğerinde kalması demektir.
_emp = os.path.join(tempfile.mkdtemp(prefix="joblyfit-test-emp-"), "employer.db")
os.environ.setdefault("ISUYGUN_EMPLOYER_DB", _emp)
