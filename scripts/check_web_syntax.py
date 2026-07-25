#!/usr/bin/env python3
"""web/ altındaki TÜM sayfaların inline script'lerini Node ile parse eder.

**Neden ayrı bir kontrol:** Bu projede iki kez, bütün testler geçerken arayüz
tamamen bozuldu. Sebep her seferinde inline script'te bir sözdizimi hatasıydı.
Bu hatanın belirtisi yanıltıcıdır:

* sayfa "Yükleniyor…" ekranında donar,
* tarayıcı konsoluna **hata düşmez** (script hiç çalıştırılmaz),
* API çağrıları 200 döner,

yani sorun backend'de sanılır. Node'un parser'ı bunu bir saniyede yakalar.

**Neden tek sayfa değil:** İlk sürüm yalnızca ``web/index.html``e bakıyordu. Ama
index.html artık ESKİ yüzey (``/classic``); kullanıcının gördüğü sayfa
``web/app.html`` ve o hiç denetlenmiyordu — yani kontrol, korumasız bıraktığı
dosya için "temiz" diyordu. Sayfalar artık taranarak bulunur; yeni bir sayfa
eklendiğinde kapsam kendiliğinden büyür.

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
WEB = ROOT / "web"
SCRIPT_RE = re.compile(r"<script([^>]*)>(.*?)</script>", re.S)
_TYPE_RE = re.compile(r"""\btype\s*=\s*["']?([^"'\s>]+)""", re.I)

#: JavaScript sayılan `type` değerleri. `<script>` etiketi JS dışında VERİ de
#: taşır: `application/ld+json` (arama motoru için yapılandırılmış veri),
#: `text/template` vb. İlk sürüm bunları da Node'a veriyordu ve JSON-LD
#: eklendiğinde "SyntaxError: Unexpected token ':'" diye YANLIŞ POZİTİF
#: üretti — geçerli JSON'u bozuk JS sandı.
_JS_TYPES = {"", "text/javascript", "application/javascript", "module",
             "text/ecmascript", "application/ecmascript"}


def _js_bloklari(kaynak: str) -> list[str]:
    """Yalnızca gerçekten JavaScript olan inline blokları döndürür."""
    out: list[str] = []
    for attrs, gövde in SCRIPT_RE.findall(kaynak):
        if re.search(r"\bsrc\s*=", attrs, re.I):
            continue                      # dış dosya — parse edilecek gövde yok
        m = _TYPE_RE.search(attrs)
        if (m.group(1).lower() if m else "") not in _JS_TYPES:
            continue                      # veri bloğu (ld+json, template…)
        out.append(gövde)
    return out

#: Bu sayfalarda inline script BULUNMASI zorunlu. Regex bir gün sessizce
#: eşleşmeyi bırakırsa kontrol "0 blok denetledim, temiz" demesin.
SCRIPT_BEKLENEN = ("app.html", "index.html")


def _sayfalar() -> list[Path]:
    """web/ altındaki html dosyaları; nokta ile başlayan dizinler atlanır."""
    return sorted(
        p for p in WEB.rglob("*.html")
        if not any(part.startswith(".") for part in p.relative_to(ROOT).parts)
    )


def _parse_hatasi(node: str, kod: str, etiket: str) -> str | None:
    """Tek script bloğunu Node'a verir; hata varsa metnini döndürür."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".js", delete=False, encoding="utf-8"
    ) as f:
        f.write(kod)
        yol = f.name
    try:
        r = subprocess.run([node, "--check", yol], capture_output=True, text=True)
    finally:
        Path(yol).unlink(missing_ok=True)
    if r.returncode == 0:
        return None
    # Node geçici dosya adını basar; okunabilirlik için kaynağa çeviririz.
    return r.stderr.replace(yol, etiket)


def main() -> int:
    if not WEB.is_dir():
        print(f"HATA: {WEB} bulunamadı", file=sys.stderr)
        return 2

    node = shutil.which("node")
    if node is None:
        print("ATLANDI: node bulunamadı; sözdizimi kontrolü yapılamadı", file=sys.stderr)
        return 2

    sayfalar = _sayfalar()
    if not sayfalar:
        print(f"HATA: {WEB} altında html yok — beklenmeyen durum", file=sys.stderr)
        return 1

    hata = 0
    ozet: list[str] = []
    blok_sayisi: dict[str, int] = {}
    for sayfa in sayfalar:
        etiket = sayfa.relative_to(ROOT).as_posix()
        bloklar = _js_bloklari(sayfa.read_text(encoding="utf-8"))
        blok_sayisi[sayfa.name] = len(bloklar)
        for i, kod in enumerate(bloklar, 1):
            mesaj = _parse_hatasi(node, kod, etiket)
            if mesaj:
                hata += 1
                print(f"--- {etiket} script #{i} sözdizimi hatası ---", file=sys.stderr)
                print(mesaj, file=sys.stderr)
        ozet.append(f"  {etiket}: {len(bloklar)} blok")

    # Kapsam kaybını yakala: beklenen sayfada hiç script bulunamadıysa regex
    # bozulmuş ya da sayfa taşınmış olabilir.
    for ad in SCRIPT_BEKLENEN:
        if blok_sayisi.get(ad, 0) == 0:
            print(f"HATA: {ad} içinde inline script bulunamadı — regex mi bozuldu, "
                  f"sayfa mı taşındı?", file=sys.stderr)
            hata += 1

    if hata:
        print(f"\n{hata} sorun bulundu.", file=sys.stderr)
        return 1

    print("web inline script'leri temiz:")
    print("\n".join(ozet))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
