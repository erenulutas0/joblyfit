"""Golden set **sadakat** denetimi (D-062).

Donmuş anlık kopya, canlı korpustaki aynı ilanla **aynı bandı** üretmeli.
Üretmiyorsa golden set gerçek hattı ölçmüyor demektir ve bütün rapor değersizdir.

Bu denetim bir kez gerçek bir hatayı yakaladı: ilk sürüm ``extraction_confidence``
ve ``is_legal_eligibility`` alanlarını dondurmuyordu; varsayılana (1.0 / False)
düşen 3 vakada bant ``good`` yerine ``strong`` çıkıyor ve ölçüm aracı kendi
uydurduğu bir gerçekliği ölçüyordu.

Ağa çıkar (canlı korpusu ister) — bu yüzden test paketinde değil, elle
çalıştırılan bir denetimdir::

    python golden/verify_fidelity.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval as ge  # noqa: E402  (golden/eval.py)

from isuygun_core import match                        # noqa: E402
from isuygun_ingest.pipeline import run_live_ingest   # noqa: E402


def main() -> int:
    data = json.loads(ge.SET_PATH.read_text(encoding="utf-8"))
    cat = ge._catalog()
    profiles = {n: ge._profile(n, s, cat) for n, s in data["personas"].items()}

    res = run_live_ingest(include_fixtures=False)
    live = {p.job.job_id: p for p in res["canonical_postings"].values()}

    sapma, eksik = 0, 0
    for case in data["vakalar"]:
        prof = profiles[case["persona"]]
        frozen = match(ge._job(case["ilan"]), prof, calibrated_occupation=False)
        fb = frozen.band.value if frozen.band else None

        post = live.get(case["ilan"]["job_id"])
        if post is None:
            # İlan korpustan düşmüş olabilir (45 gün tazelik, D-024) — bu bir
            # hata değil, donmuş kopyanın var olma sebebi.
            eksik += 1
            continue
        real = match(post.job, prof, calibrated_occupation=False)
        rb = real.band.value if real.band else None
        if fb != rb:
            sapma += 1
            print(f"SAPMA {case['id']}: donmus={fb} canli={rb} — "
                  f"{case['ilan']['title'][:52]}")

    n = len(data["vakalar"])
    print(f"\n{n} vaka | canlı korpusta bulunan: {n - eksik} | "
          f"düşmüş: {eksik} | SAPMA: {sapma}")
    if sapma:
        print("HATA: golden set gerçek hattı yansıtmıyor — rapor geçersiz.")
        return 1
    print("Sadakat tam: donmuş kopyalar canlı hattın bandını birebir üretiyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
