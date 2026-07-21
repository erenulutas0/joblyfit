#!/usr/bin/env python3
"""web/index.html içindeki inline script'i Node ile sözdizimi kontrolünden geçirir.

**Neden ayrı bir kontrol:** Bu projede iki kez, bütün testler geçerken arayüz
tamamen bozuldu. Sebep her seferinde inline script'te bir sözdizimi hatasıydı.
Bu hatanın belirtisi yanıltıcıdır:

* sayfa "Yükleniyor…" ekranında donar,
* tarayıcı konsoluna **hata düşmez** (script hiç çalıştırılmaz),
* API çağrıları 200 döner,

yani sorun backend'de sanılır. Node'un parser'ı bunu bir saniyede yakalar.

Kullanım:  python scripts/check_web_syntax.py
Çıkış kodu: 0 temiz, 1 sözdizimi hatası, 2 çalıştırılamadı.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "web" / "index.html"
SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S)


def main() -> int:
    if not PAGE.is_file():
        print(f"HATA: {PAGE} bulunamadı", file=sys.stderr)
        return 2

    node = shutil.which("node")
    if node is None:
        print("ATLANDI: node bulunamadı; sözdizimi kontrolü yapılamadı", file=sys.stderr)
        return 2

    blocks = SCRIPT_RE.findall(PAGE.read_text(encoding="utf-8"))
    if not blocks:
        print("HATA: index.html içinde inline script yok — beklenmeyen durum",
              file=sys.stderr)
        return 1

    failed = 0
    for i, code in enumerate(blocks, 1):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".js", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            path = f.name
        try:
            r = subprocess.run([node, "--check", path], capture_output=True, text=True)
        finally:
            Path(path).unlink(missing_ok=True)

        if r.returncode != 0:
            failed += 1
            print(f"--- script #{i} sözdizimi hatası ---", file=sys.stderr)
            # Node geçici dosya adını basar; okunabilirlik için kaynağa çeviririz.
            print(r.stderr.replace(path, "web/index.html"), file=sys.stderr)

    if failed:
        print(f"\n{failed} script bloğu parse edilemedi.", file=sys.stderr)
        return 1

    print(f"web/index.html: {len(blocks)} script bloğu temiz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
