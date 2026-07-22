"""İlan önbelleği — ham **ve** işlenmiş kayıtlar.

Önbellek iki ayrı maliyeti önler ve ikisinin ömrü farklıdır:

* **Çekim** (~250 sn): 151 pano + 4 API, ``Crawl-delay`` uygulanarak. Ham
  kayıtlar bunun için saklanır.
* **Çıkarım** (~35 sn): 5810 ilanın sözlük taraması. İşlenmiş kayıtlar bunun
  için saklanır.

**Tehlikeli olan ikincisidir.** Sözlüğe bir terim eklendiğinde önbellekteki
işlenmiş kayıtlar eski mantığı taşımaya devam eder; geliştirici değişikliğinin
hiçbir etkisini göremez ve sebebini kodda arar. Bu yüzden çıkarım mantığının
**parmak izi** önbellekle birlikte yazılır: `lexicon.py` veya `extract.py`
değiştiğinde işlenmiş kayıtlar geçersiz sayılır ve ham kayıtlardan yeniden
üretilir — yeniden çekim yapılmadan.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from isuygun_core.domain import JobPosting, Requirement

from .pipeline import NormalizedPosting, RawPosting
from .fairness import FairnessFlag
from .salary import Salary

#: Parmak izine giren dosyalar — çıkarım sonucunu belirleyen her şey.
_LOGIC_FILES = ("lexicon.py", "extract.py", "salary.py", "jobmeta.py",
                "fairness.py")

#: **Çekim** mantığını belirleyen dosyalar. Ayrı bir parmak izi gerekir çünkü
#: bunlar değiştiğinde ham kayıtların kendisi geçersizleşir; yeniden normalize
#: etmek yetmez, yeniden **çekmek** gerekir.
#:
#: Bu ayrım pahalı bir dersle eklendi: Greenhouse adapter'ı ilanın yaşını
#: `updated_at`ten okuyordu (her düzenlemede yenilenen tarih) ve ilanlar
#: gerçekte olduğundan medyan 60 gün daha taze görünüyordu. Adapter düzeltildi
#: ama önbellekteki ham kayıtlar eski tarihi taşımaya devam edecekti —
#: düzeltmenin hiçbir etkisi görünmezdi.
_FETCH_FILES = ("adapters/ats.py", "adapters/public_apis.py")


def _hash_files(names: tuple[str, ...]) -> str:
    here = Path(__file__).parent
    h = hashlib.sha256()
    for name in names:
        h.update((here / name).read_bytes())
    return h.hexdigest()[:16]


def _source_config_marker() -> str:
    """Çekilecek kaynak kümesini **runtime config** ile değiştiren durumlar.

    Adaptör dosyaları değişmese de, bir anahtarın eklenmesi çekilecek kaynak
    kümesini büyütür: Jooble anahtarsızken atlanıyor, anahtar gelince çekiliyor.
    Bunu parmak izine katmazsak kullanıcı anahtarı ekler, önbellek "taze"
    görünür ve Jooble hiç çekilmez — D-028/D-036'nın önlediği sessiz bayatlık,
    bir katman daha aşağıda.
    """
    import os

    return "j1" if os.environ.get("ISUYGUN_JOOBLE_KEY", "").strip() else "j0"


def fetch_fingerprint() -> str:
    """Çekim mantığının + kaynak konfigürasyonunun kimliği.

    Değişirse ham kayıtlar geçersizdir: ya adaptör değişti (farklı alan okunuyor
    olabilir) ya da çekilecek kaynak kümesi değişti (yeni anahtar).
    """
    return f"{_hash_files(_FETCH_FILES)}:{_source_config_marker()}"


def extraction_fingerprint() -> str:
    """Çıkarım mantığının kimliği.

    Kaynak dosyaların içeriğinden üretilir. Elle artırılan bir sürüm numarası
    yerine bu tercih edildi: sürümü artırmayı unutmak, sessiz bayat önbellek
    demektir ve o hatanın belirtisi ("değişikliğim işe yaramıyor") kodda
    aranır, önbellekte değil.
    """
    return _hash_files(_LOGIC_FILES)


# --------------------------------------------------------------------------
# Serileştirme
# --------------------------------------------------------------------------


def _posting_to_dict(p: NormalizedPosting) -> dict:
    return {
        "job": {**asdict(p.job),
                "requirements": [asdict(r) for r in p.job.requirements]},
        "employer_key": p.employer_key,
        "title_key": p.title_key,
        "city_key": p.city_key,
        "content_fingerprint": p.content_fingerprint,
        "job_text": p.job_text,
        "url": p.url,
        "posted_at": p.posted_at,
        "refreshed_at": p.refreshed_at,
        "fetched_at": p.fetched_at,
        "provenance": p.provenance,
        "salary": asdict(p.salary) if p.salary else None,
        "salary_status": p.salary_status,
        "work_arrangement": p.work_arrangement,
        "employment_type": p.employment_type,
        "experience_level": p.experience_level,
        "fairness_flags": [asdict(f) for f in p.fairness_flags],
    }


def _posting_from_dict(d: dict) -> NormalizedPosting:
    job = d["job"]
    return NormalizedPosting(
        job=JobPosting(
            job_id=job["job_id"], title=job["title"], employer=job["employer"],
            city=job["city"], occupation_id=job["occupation_id"], source=job["source"],
            requirements=tuple(Requirement(**r) for r in job["requirements"]),
            is_public_sector=job["is_public_sector"],
        ),
        employer_key=d["employer_key"], title_key=d["title_key"],
        city_key=d["city_key"], content_fingerprint=d["content_fingerprint"],
        job_text=d["job_text"], url=d["url"], posted_at=d["posted_at"],
        refreshed_at=d.get("refreshed_at"),
        fetched_at=d["fetched_at"], provenance=d["provenance"],
        salary=Salary(**d["salary"]) if d.get("salary") else None,
        salary_status=d.get("salary_status", "not_stated"),
        work_arrangement=d.get("work_arrangement"),
        employment_type=d.get("employment_type"),
        experience_level=d.get("experience_level"),
        fairness_flags=tuple(FairnessFlag(**f) for f in d.get("fairness_flags", [])),
    )


# --------------------------------------------------------------------------
# Okuma / yazma
# --------------------------------------------------------------------------


def read(path: Path, max_age_hours: float) -> dict | None:
    """Önbelleği okur.

    Döner: ``{"raws": [...], "postings": [...] | None, "meta": {...}}`` ya da
    ``None`` (yok / süresi dolmuş / bozuk).

    ``postings`` yalnızca çıkarım parmak izi tutuyorsa doldurulur. Tutmuyorsa
    ham kayıtlar döner ve çağıran taraf yeniden normalize eder — yeniden
    **çekim** yapmadan.
    """
    if not path.is_file():
        return None
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
        fetched_at = datetime.fromisoformat(blob["fetched_at"])
    except Exception:
        return None   # bozuk önbellek sessizce yok sayılır, hata değildir

    if (datetime.now() - fetched_at).total_seconds() > max_age_hours * 3600:
        return None

    # Çekim mantığı değiştiyse ham kayıtlar da geçersizdir: adapter artık
    # farklı bir alan okuyor olabilir ve eski kayıtlarda o alan yok.
    if blob.get("fetch_fingerprint") != fetch_fingerprint():
        return None

    fresh_logic = blob.get("extraction_fingerprint") == extraction_fingerprint()
    try:
        raws = [RawPosting(**r) for r in blob["raws"]]
        postings = (
            [_posting_from_dict(p) for p in blob.get("postings", [])]
            if fresh_logic and blob.get("postings") else None
        )
    except Exception:
        return None

    return {"raws": raws, "postings": postings, "meta": blob.get("meta", {})}


def write(path: Path, *, raws: list[RawPosting],
          postings: list[NormalizedPosting], meta: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now().isoformat(),
        "extraction_fingerprint": extraction_fingerprint(),
        "fetch_fingerprint": fetch_fingerprint(),
        "meta": meta,
        "raws": [asdict(r) for r in raws],
        "postings": [_posting_to_dict(p) for p in postings],
    }
    # Önce geçici dosyaya yaz: yazım yarıda kalırsa mevcut önbellek bozulmasın.
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
