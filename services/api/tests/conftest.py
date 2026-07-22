"""Testler kalıcı profil veritabanına **yazmaz**.

Aksi halde bir test koşusu geliştiricinin gerçek profilini siler ve testler
birbirinin durumunu görür. Ortam değişkeni import'tan önce ayarlanmalı.
"""

import os

os.environ.setdefault("ISUYGUN_DB", ":memory:")
