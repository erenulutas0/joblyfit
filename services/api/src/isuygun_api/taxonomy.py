"""Profil alan kataloğu — korpustan türetilir.

Matching, şart anahtarı (``Requirement.key``) ile profil alanı (``ProfileFact.key``)
eşitliğine dayanır. Bu, gerçek bir sistemde bir **ontoloji** işidir (ESCO benzeri):
serbest metin "TIR şoförlüğü" ile ilandaki "C+E sınıfı ehliyet" bir eşleme
katmanından geçmelidir.

MVP'de böyle bir ontoloji **yoktur**. Bunun yerine katalog doğrudan korpustaki
şartlardan türetilir; böylece profil editörü ile ilanlar arasında sessiz bir
kayma oluşamaz. Bu kasıtlı bir sadeleştirmedir ve gerçek kaynağa geçilmeden
önce ontolojiyle değiştirilmelidir (bkz. OPEN-23).
"""

from __future__ import annotations

from dataclasses import dataclass

from isuygun_core.domain import GATE_RELEVANT_CATEGORIES, Requirement

OCCUPATION_LABELS: dict[str, str] = {
    "driver": "Şoförlük ve taşımacılık",
    "warehouse": "Depo ve lojistik",
    "nurse": "Sağlık",
    "account": "Muhasebe ve finans",
    "sales": "Satış",
}

CATEGORY_LABELS: dict[str, str] = {
    "license": "Belge ve ehliyet",
    "legally_required_certificate": "Zorunlu belge",
    "certificate": "Sertifika",
    "experience": "Deneyim",
    "skill": "Beceri",
    "shift": "Çalışma düzeni",
    "work_authorization": "Çalışma izni",
    "other": "Diğer",
}


@dataclass(frozen=True, slots=True)
class CatalogItem:
    """Profil editöründe kullanıcıya gösterilen tek alan."""

    key: str
    label: str
    category: str
    category_label: str
    occupation_id: str
    occupation_label: str
    #: Süre soruluyor mu (ilan en az X yıl istiyorsa)
    asks_years: bool
    #: `verified` olmadan `met` üretemeyen alan (D-012)
    needs_verification: bool
    #: D-013 — yasal uygunluk şartı; profile hiç yazılmaz
    is_legal_eligibility: bool


def build_catalog(postings) -> list[CatalogItem]:
    """İlan korpusundaki şartlardan profil kataloğunu türetir."""
    seen: dict[str, CatalogItem] = {}
    for p in postings:
        occ = p.job.occupation_id
        for req in p.job.requirements:
            if req.key in seen:
                continue
            seen[req.key] = CatalogItem(
                key=req.key,
                label=req.label,
                category=req.category,
                category_label=CATEGORY_LABELS.get(req.category, req.category),
                occupation_id=occ,
                occupation_label=OCCUPATION_LABELS.get(occ, occ),
                asks_years=req.min_years is not None,
                needs_verification=req.category in GATE_RELEVANT_CATEGORIES,
                is_legal_eligibility=req.is_legal_eligibility,
            )
    return sorted(seen.values(), key=lambda i: (i.occupation_label, i.category_label, i.label))


def selectable(catalog: list[CatalogItem]) -> list[CatalogItem]:
    """Kullanıcının profiline ekleyebileceği alanlar.

    Yasal uygunluk şartları (askerlik, yaş, sağlık) **listede yer almaz** —
    bunlar profile hiç yazılmaz ve skora girmez (D-013 + D-006).
    """
    return [i for i in catalog if not i.is_legal_eligibility]
