"""Profil alan kataloğu — paylaşılan sözlükten türetilir.

**Bu dosya bir hatanın düzeltilmesidir.** Önceki sürümde katalog *korpustan*
türetiliyordu: profil editörü yalnızca eldeki 8 sentetik ilanda geçen 18 alanı
tanıyordu. Gerçek bir CV yüklendiğinde hiçbir şey eşleşmedi — çünkü kullanıcının
mesleği o 18 alanın hiçbiri değildi. Sistem bozuk değildi; **eşleşecek bir alan
yoktu.**

Artık katalog ``isuygun_ingest.lexicon``'dan gelir. İlan tarafı da CV tarafı da
aynı sözlüğe eşlendiği için eşleşme anlamlıdır ve profil editörü korpusta o an
hangi ilanlar olduğundan bağımsızdır.

Bu hâlâ tam bir ontoloji değildir (OPEN-23) — sözlük elle yazılmıştır ve
serbest metni anlamaz.
"""

from __future__ import annotations

from dataclasses import dataclass

from isuygun_core.domain import GATE_RELEVANT_CATEGORIES
from isuygun_ingest import lexicon

CATEGORY_LABELS: dict[str, str] = {
    "license": "Belge ve ehliyet",
    "legally_required_certificate": "Zorunlu belge",
    "certificate": "Sertifika",
    "experience": "Deneyim",
    "skill": "Beceri",
    "shift": "Çalışma düzeni",
    "language": "Dil",
    "education": "Eğitim",
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
    occupation_id: str          # lexicon cluster'ı
    occupation_label: str
    asks_years: bool
    needs_verification: bool    # `verified` olmadan `met` üretemez (D-012)
    is_legal_eligibility: bool = False


def build_catalog(_postings=None) -> list[CatalogItem]:
    """Kataloğu sözlükten kurar.

    ``_postings`` artık kullanılmaz; imza, çağıranları kırmamak için korunur.
    Katalog **korpustan bağımsızdır** — bu, düzeltmenin özüdür.
    """
    items = [
        CatalogItem(
            key=t.key,
            label=t.label,
            category=t.category,
            category_label=CATEGORY_LABELS.get(t.category, t.category),
            occupation_id=t.cluster,
            occupation_label=t.cluster,
            asks_years=t.asks_years,
            needs_verification=t.category in GATE_RELEVANT_CATEGORIES,
        )
        for t in lexicon.TERMS
    ]
    order = {c: i for i, c in enumerate(lexicon.clusters())}
    return sorted(items, key=lambda i: (order.get(i.occupation_id, 999),
                                        i.category_label, i.label))


def selectable(catalog: list[CatalogItem]) -> list[CatalogItem]:
    """Kullanıcının profiline ekleyebileceği alanlar.

    Yasal uygunluk şartları (askerlik, yaş, sağlık) **listede yer almaz** —
    profile hiç yazılmaz ve skora girmez (D-013 + D-006).
    """
    return [i for i in catalog if not i.is_legal_eligibility]
