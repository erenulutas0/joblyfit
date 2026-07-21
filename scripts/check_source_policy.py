#!/usr/bin/env python3
"""Kaynak izni denetimi — ürünün uyum taahhüdünün otomatik kontrolü.

Bu, bir kod kalitesi kontrolü **değildir**. D-002, D-020 ve D-023 kullanıcıya ve
kaynaklara verilmiş taahhütlerdir; bir kaynağı yanlışlıkla açmak sessiz bir ihlal
üretir. Testlerden ayrı bir adım olarak koşar ki "testleri geçici olarak atla"
kararı bu denetimi de atlamasın.

Denetlenen kurallar:

1. İzinli (`allowed`) her gerçek kaynak, izin gerekçesini **kayıtta taşımalı**.
2. LinkedIn ve Indeed `rejected` kalmalı — ikisi için de yasal erişim yolu yok.
3. Ağ erişimi açık her kaynak yalnızca `api` / `feed` yöntemiyle erişilmeli;
   `html` bir kaynağın açılması scraping'e kayma anlamına gelir.
4. Çekilen her pano, izinli bir kayda bağlı olmalı.
5. İzinli her API kaynağının kullanım şartları (atıf, gecikme, yeniden yayın)
   kayıtta yazılı olmalı.

Kullanım:  python scripts/check_source_policy.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "services" / "ingest" / "src"),
    str(ROOT / "services" / "core" / "src"),
]

from isuygun_ingest import registry  # noqa: E402

#: Yasal erişim yolu bulunmayan platformlar. Bu liste **kısalmaz**; bir platform
#: buradan çıkacaksa gerekçesi DECISIONS.md'de yazılı olmalıdır.
MUST_STAY_REJECTED = {"src-tr-014": "Indeed", "src-tr-015": "LinkedIn"}

ALLOWED_ACCESS_METHODS = {"api", "feed", "fixture"}


def main() -> int:
    problems: list[str] = []

    # 1 — kanıtsız izin
    for rec in registry.allowed_without_evidence():
        problems.append(
            f"{rec.source_id} `allowed` işaretli ama `permission_evidence` boş"
        )

    # 2 — kapalı kalması gerekenler
    for sid, name in MUST_STAY_REJECTED.items():
        rec = registry.REGISTRY.get(sid)
        if rec is None:
            problems.append(f"{sid} ({name}) registry'den silinmiş")
            continue
        if rec.scraping_permission != "rejected" or rec.may_fetch_network:
            problems.append(
                f"{sid} ({name}) açılmış — bu platformlar için yasal erişim yolu yok"
            )

    # 3 — açık kaynakların erişim yöntemi
    for rec in registry.REGISTRY.values():
        if rec.may_fetch_network and rec.access_method not in ALLOWED_ACCESS_METHODS:
            problems.append(
                f"{rec.source_id} ağa açık ama access_method={rec.access_method!r} "
                "— yalnızca api/feed kabul edilir"
            )

    # 4 — panolar izinli kayda bağlı mı
    for source_id, platform, slug, _employer in registry.BOARDS:
        try:
            rec = registry.assert_fetchable(source_id)
        except Exception as e:
            problems.append(f"{platform}/{slug} → {source_id}: {e}")
            continue
        if rec.scraping_permission != "allowed":
            problems.append(f"{platform}/{slug} izinli olmayan kayda bağlı")

    # 5 — API kaynaklarının kullanım şartları
    for rec in registry.api_sources():
        if not rec.permission_evidence.strip():
            problems.append(f"{rec.source_id}: izin kanıtı yok")
        if rec.min_poll_hours <= 0:
            problems.append(f"{rec.source_id}: min_poll_hours tanımsız")
        if not rec.redistribution_policy.strip():
            problems.append(f"{rec.source_id}: redistribution_policy yazılmamış")

    if problems:
        print("KAYNAK İZNİ DENETİMİ BAŞARISIZ:\n", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    a = registry.audit()
    print(
        f"Kaynak izni denetimi temiz — {a['toplam']} kayıt, {a['allowed']} izinli, "
        f"{a['rejected']} reddedilmiş, {a['board_sayisi']} pano."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
