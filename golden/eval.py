"""Eşleşme kalitesi değerlendirmesi (T-006b / D-062).

**Neden var:** bu ürünün iddiası "en iyi eşleşmeyi bulmak" değil, **yanlış umut
vermemek**. O yüzden birincil ölçü isabet değil, **aşırı iddia (overclaim)**
oranıdır: savunulamayacak kadar yüksek bant verdiğimiz vaka sayısı.

``_CALIBRATED`` bugüne kadar boş kaldı çünkü hiçbir ölçüm yoktu; bu dosya o
boşluğu kapatır ve değeri **sayıya** bağlar.

Çalıştırma::

    python golden/eval.py            # rapor
    python golden/eval.py --json     # makine okunur

Ölçüler:

* **aşırı iddia**: üretilen bant, elle etiketlenen "en yüksek savunulabilir
  bant"tan yüksek. Ürünün kardinal günahı — kullanıcı başvurur, boşa umutlanır.
* **eksik iddia**: üretilen bant savunulabilirden düşük (fırsat kaybı; aşırı
  iddiadan daha az zararlı ama körlük göstergesi).
* **alakasıza bant**: meslek hiç uymayan ilana bant verilmiş.
* **tam isabet / komşu isabet**: bilgi amaçlı ikincil ölçüler.

**Sınırlar — dürüstçe:** 37 vaka küçük bir kümedir ve etiketler proje
geliştiricisi tarafından konmuştur; gerçek kullanıcı yargısının yerini tutmaz.
Amaç mutlak bir kalite notu değil, **regresyon zemini**: bir değişiklik aşırı
iddiayı artırıyorsa burada görünür. Gerçek kullanıcı geri bildirimi
(``/api/feedback`` → signals.db) biriktikçe bu küme onunla değiştirilmeli.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _p in ("services/core/src", "services/ingest/src", "services/api/src"):
    sys.path.insert(0, str(_ROOT / _p))

from isuygun_core import match                                    # noqa: E402
from isuygun_core.domain import (                                 # noqa: E402
    CareerProfile,
    JobPosting,
    ProfileFact,
    Requirement,
)
from isuygun_api.taxonomy import build_catalog, selectable        # noqa: E402

#: Bant sırası — karşılaştırma ordinaldir (D-005: yüzde yok, sıra var).
#: ``None`` = "bantlanamaz" ve en altta durur.
_ORDER = {None: 0, "weak": 1, "cond": 2, "good": 3, "strong": 4}

SET_PATH = Path(__file__).with_name("set.json")


def _catalog() -> dict:
    return {i.key: i for i in selectable(build_catalog())}


def _profile(name: str, spec: dict, cat: dict) -> CareerProfile:
    facts = []
    for f in spec["facts"]:
        item = cat.get(f["key"])
        if item is None:      # katalog değişmiş: sessiz atlamak yanlış olurdu
            raise SystemExit(f"golden: katalogda olmayan anahtar {f['key']!r} "
                             f"(persona {name}) — set güncellenmeli")
        facts.append(ProfileFact(
            key=f["key"], category=item.category,
            verification="verified" if f.get("verified") else "user_asserted",
            years=f.get("years"),
        ))
    return CareerProfile(profile_id=name, facts=tuple(facts))


def _job(d: dict) -> JobPosting:
    return JobPosting(
        job_id=d["job_id"], title=d["title"], employer=d["employer"],
        city=d["city"], occupation_id=d["occupation_id"],
        source="golden", is_public_sector=False,
        # `extraction_confidence` ve `is_legal_eligibility` MUTLAKA taşınır:
        # ilki düşük güvenli çıkarımın hard eleme yapmasını engeller (FS-4),
        # ikincisi şartı skordan çıkarır (D-013). Varsayılana bırakıldığında
        # golden set gerçek hattan sapıyordu (3 vakada bant farklı çıktı) —
        # yani ölçüm aracının kendisi yanlış ölçüyordu.
        requirements=tuple(
            Requirement(
                key=q["key"], label=q["label"], kind=q["kind"],
                category=q["category"], min_years=q.get("min_years"),
                extraction_confidence=q.get("extraction_confidence", 1.0),
                is_legal_eligibility=q.get("is_legal_eligibility", False),
                source_span=q.get("source_span"),
            )
            for q in d["requirements"]
        ),
    )


def run() -> dict:
    data = json.loads(SET_PATH.read_text(encoding="utf-8"))
    cat = _catalog()
    profiles = {n: _profile(n, s, cat) for n, s in data["personas"].items()}

    rows, tally = [], {"asiri": 0, "eksik": 0, "tam": 0, "komsu": 0,
                       "alakasiza_bant": 0}
    for case in data["vakalar"]:
        prof = profiles[case["persona"]]
        result = match(_job(case["ilan"]), prof, calibrated_occupation=False)
        got = result.band.value if result.band else None
        want = case["etiket"]["en_yuksek_savunulabilir_bant"]
        d = _ORDER[got] - _ORDER[want]

        if d > 0:
            tally["asiri"] += 1
        elif d < 0:
            tally["eksik"] += 1
        if d == 0:
            tally["tam"] += 1
        if abs(d) <= 1:
            tally["komsu"] += 1
        if not case["etiket"]["ilgili"] and got is not None:
            tally["alakasiza_bant"] += 1

        rows.append({"id": case["id"], "baslik": case["ilan"]["title"],
                     "uretilen": got, "savunulabilir": want, "fark": d,
                     "gerekce": case["etiket"]["gerekce"]})

    n = len(rows)
    return {
        "vaka": n,
        "asiri_iddia": tally["asiri"],
        "asiri_iddia_orani": round(tally["asiri"] / n, 4) if n else 0.0,
        "eksik_iddia": tally["eksik"],
        "tam_isabet_orani": round(tally["tam"] / n, 4) if n else 0.0,
        "komsu_isabet_orani": round(tally["komsu"] / n, 4) if n else 0.0,
        "alakasiza_bant": tally["alakasiza_bant"],
        "satirlar": rows,
    }


def main() -> None:
    r = run()
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return
    print(f"golden set: {r['vaka']} vaka\n")
    print(f"  AŞIRI İDDİA        : {r['asiri_iddia']:3}  "
          f"(%{100*r['asiri_iddia_orani']:.1f})   <-- birincil ölçü")
    print(f"  alakasıza bant     : {r['alakasiza_bant']:3}")
    print(f"  eksik iddia        : {r['eksik_iddia']:3}")
    print(f"  tam isabet         : %{100*r['tam_isabet_orani']:.1f}")
    print(f"  komşu isabet (±1)  : %{100*r['komsu_isabet_orani']:.1f}")
    asiri = [s for s in r["satirlar"] if s["fark"] > 0]
    if asiri:
        print(f"\n  aşırı iddia veren vakalar:")
        for s in asiri:
            print(f"    ! {s['uretilen']:>6} (olmalı: {str(s['savunulabilir']):>6}) "
                  f"{s['baslik'][:52]}")
            print(f"        {s['gerekce']}")


if __name__ == "__main__":
    main()
