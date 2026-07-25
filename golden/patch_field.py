"""Donmuş golden set'e YENİ bir ilan alanı ekler — **job_id ile eşleyerek**.

Neden ayrı bir araç: golden set'i yeniden örneklemek TEHLİKELİDİR. Örnekleme
sistemin ürettiği banda göre tabakalıdır; eşleştirici değişince örnek kayar ve
elle konmuş etiketler **başka ilanlara yapışır**. Bu gerçekten oldu (D-063):
kıdem tavanı eklendikten sonra yeniden örneklemede 5 vakanın etiketi yanlış
ilana bağlandı ve ölçüm geçersiz bir sonuç (%21,6) üretti.

Kural: **golden set bir kez donar; sonraki eklemeler job_id üzerinden yapılır.**

    python golden/patch_field.py experience_level
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _p in ("services/core/src", "services/ingest/src", "services/api/src"):
    sys.path.insert(0, str(_ROOT / _p))

from isuygun_ingest.pipeline import run_live_ingest   # noqa: E402

SET = Path(__file__).with_name("set.json")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    field = sys.argv[1]
    data = json.loads(SET.read_text(encoding="utf-8"))

    res = run_live_ingest(include_fixtures=False)
    live = {p.job.job_id: p for p in res["canonical_postings"].values()}

    doldu = eksik = 0
    for case in data["vakalar"]:
        jid = case["ilan"]["job_id"]
        post = live.get(jid)
        if post is None:
            eksik += 1
            case["ilan"].setdefault(field, None)
            continue
        # Alan hem NormalizedPosting'de hem job'da olabilir; job önce gelir.
        val = getattr(post.job, field, None)
        if val is None:
            val = getattr(post, field, None)
        case["ilan"][field] = val
        if val is not None:
            doldu += 1

    SET.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"{field}: {doldu} vakada dolduruldu, {eksik} ilan korpusta yok "
          f"({len(data['vakalar'])} vaka)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
