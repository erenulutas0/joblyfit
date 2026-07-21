"""CV okuma — metin çıkarımı, alan **önerisi** ve sensitive alan imhası.

İki kural bu modülün tasarımını belirler:

* **Öneri, kayıt değildir (T-016).** Buradan çıkan hiçbir şey profile yazılmaz;
  kullanıcı tek tek onaylamadan matching'e giremez. Fonksiyon adı bilinçli
  olarak ``suggest_facts``'tir.
* **Sensitive alanlar parse anında imha edilir (D-006).** Fotoğraf, din, etnik
  köken, medeni hal, sağlık, sendika üyeliği, cinsiyet ve tam doğum tarihi
  profile *yazılmaz*; tespit edilirse atılır ve yalnızca sayısal bir imha
  kaydı üretilir — içeriği saklanmaz.

Çıkarım kalitesi bilinçli olarak mütevazıdır: anahtar kelime örtüşmesi kullanılır,
CV'nin anlamı çözülmez. Kullanıcıya "CV'ni okudum ve anladım" izlenimi verilmez.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

from isuygun_ingest import lexicon
from isuygun_ingest.pipeline import fold

from .taxonomy import CatalogItem

# D-006 — profile hiçbir koşulda yazılmayacak alan imzaları.
_SENSITIVE_PATTERNS: dict[str, re.Pattern[str]] = {
    "medeni_hal": re.compile(r"\bmedeni\s*(hal|durum)\w*\b|\bbekar\b|\bevli\b", re.I),
    "din": re.compile(r"\b(din|mezhep|inan[çc])\w*\s*:", re.I),
    "etnik_koken": re.compile(r"\b(etnik|[ıi]rk|milliyet)\w*\s*:", re.I),
    "saglik": re.compile(r"\b(sa[ğg]l[ıi]k\s*durum|engel\s*oran|kronik\s*hastal)\w*", re.I),
    "sendika": re.compile(r"\bsendika\w*\b", re.I),
    "cinsiyet": re.compile(r"\bcinsiyet\w*\s*:|\b(kad[ıi]n|erkek)\s*$", re.I | re.M),
    "dogum_tarihi": re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b"),
    "fotograf": re.compile(r"\b(foto[ğg]raf|vesikal[ıi]k)\b", re.I),
}




@dataclass(frozen=True, slots=True)
class Suggestion:
    key: str
    label: str
    category: str
    needs_verification: bool
    asks_years: bool
    years: float | None
    matched_on: str
    #: Kullanıcı onaylayana kadar profile YAZILMAZ.
    confirmed: bool = False


@dataclass(frozen=True, slots=True)
class CVReadResult:
    char_count: int
    page_count: int
    suggestions: list[Suggestion]
    #: Yalnızca hangi kategorilerin atıldığı — içerik saklanmaz (D-006).
    discarded_sensitive: list[str]
    text_extracted: bool
    note: str


def extract_text(data: bytes) -> tuple[str, int]:
    """PDF'ten düz metin çıkarır. Görüntü tabanlı PDF'te boş dönebilir."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n".join(pages), len(pages)


def _scan_sensitive(text: str) -> list[str]:
    """Sensitive alanları tespit eder; **içeriğini döndürmez**, yalnızca adını."""
    return sorted(name for name, pat in _SENSITIVE_PATTERNS.items() if pat.search(text))


def suggest_facts(text: str, catalog: list[CatalogItem]) -> list[Suggestion]:
    """CV metninden profil alanı **önerir**. Hiçbir şeyi profile yazmaz.

    Tarama, ilan tarafıyla **aynı** fonksiyondan (``lexicon.scan``) geçer.
    Ayrı bir CV sözlüğü tutmak, iki tarafın sessizce birbirinden sapmasına yol
    açardı — nitekim bu modülün önceki sürümünde tam olarak bu olmuştu.
    """
    by_key = {i.key: i for i in catalog}
    out: list[Suggestion] = []
    for hit in lexicon.scan(text):
        item = by_key.get(hit.term.key)
        if item is None or item.is_legal_eligibility:
            continue  # D-013 — yasal uygunluk alanları hiç önerilmez
        out.append(
            Suggestion(
                key=item.key,
                label=item.label,
                category=item.category,
                needs_verification=item.needs_verification,
                asks_years=item.asks_years,
                years=hit.years,
                matched_on=hit.matched_form,
            )
        )
    return out


def read_cv(data: bytes, catalog: list[CatalogItem]) -> CVReadResult:
    text, pages = extract_text(data)
    discarded = _scan_sensitive(text)

    if len(text.strip()) < 40:
        return CVReadResult(
            char_count=len(text),
            page_count=pages,
            suggestions=[],
            discarded_sensitive=discarded,
            text_extracted=False,
            note=(
                "Bu PDF'ten metin çıkarılamadı — büyük olasılıkla taranmış görüntü. "
                "Alanları elle girebilirsin."
            ),
        )

    suggestions = suggest_facts(text, catalog)
    note = (
        f"CV'den {len(suggestions)} alan önerildi. Bunlar **profiline eklenmedi** — "
        "her birini tek tek onaylaman gerekiyor. Öneriler anahtar kelime "
        "eşleşmesine dayanır; CV'nin tamamı anlaşılmış değildir."
    )
    if not suggestions:
        note = (
            "CV okundu ama tanıdık bir alan bulunamadı. Bu, CV'nin zayıf olduğu "
            "anlamına gelmez — sistemin alan kataloğu şimdilik dar. Elle girebilirsin."
        )
    return CVReadResult(
        char_count=len(text),
        page_count=pages,
        suggestions=suggestions,
        discarded_sensitive=discarded,
        text_extracted=True,
        note=note,
    )
