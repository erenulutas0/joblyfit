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

# Katalog etiketinin kendisi yetmediğinde kullanılan eş anlamlılar.
_SYNONYMS: dict[str, tuple[str, ...]] = {
    "license_ce": ("c+e", "ce sınıfı", "tır", "çekici", "ağır vasıta ehliyet"),
    "license_b": ("b sınıfı", "b ehliyet", "binek"),
    "license_d": ("d sınıfı", "otobüs ehliyet"),
    "src1": ("src", "src1", "src-1", "mesleki yeterlilik"),
    "psiko": ("psikoteknik",),
    "forklift": ("forklift", "istif makinesi", "transpalet"),
    "nurse_license": ("hemşirelik tescil", "tescil belgesi", "diploma tescil"),
    "acc_software": ("logo", "mikro", "netsis", "eta", "muhasebe programı", "luca"),
    "efatura": ("e-fatura", "e fatura", "e-defter", "e arşiv"),
    "smmm": ("smmm", "mali müşavir", "serbest muhasebeci"),
    "shift_ok": ("vardiya",),
    "night_shift": ("gece vardiya", "nöbet"),
    "exp_heavy": ("ağır vasıta", "tır şoför", "uzun yol"),
    "exp_wh": ("depo", "stok", "sevkiyat", "wms"),
    "exp_icu": ("yoğun bakım", "reanimasyon"),
    "exp_acc": ("muhasebe", "mizan", "beyanname", "cari"),
    "exp_sales": ("saha satış", "bayi", "müşteri portföy"),
}

_YEAR_NEAR = re.compile(r"(\d{1,2})\s*(?:\+)?\s*yil", re.I)

# Etiketten türetilen kelimeler tek başına kanıt sayılamaz: "belgesi", "ehliyet"
# gibi terimler neredeyse her CV'de geçer ve alakasız öneri üretir. Bunlar
# olmadan bir şoför CV'sine "Hemşirelik tescil belgesi" önerilebiliyordu.
_TOO_GENERIC: frozenset[str] = frozenset({
    "belge", "belgesi", "belgeler", "ehliyet", "ehliyeti", "sinif", "sinifi",
    "deneyim", "deneyimi", "tecrube", "sertifika", "sertifikasi", "kullanim",
    "kullanimi", "uygunluk", "uygunlugu", "sistem", "sistemi", "mesleki",
    "yeterlilik", "operator", "gorevlisi", "calisabilme", "program", "programi",
    "tescil", "ruhsat", "ruhsati", "vasita", "sahibi", "bilgisi",
})


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


def _needles(item: CatalogItem) -> tuple[str, ...]:
    """Bu alanın CV'de aranacak ipuçları.

    Etiketten türeyen kelimeler ``_TOO_GENERIC`` süzgecinden geçer; ayırt edici
    olmayan bir kelime tek başına öneri üretemez.
    """
    label_tokens = tuple(
        w for w in re.split(r"\W+", fold(item.label))
        if len(w) > 3 and w not in _TOO_GENERIC
    )
    return tuple(fold(s) for s in _SYNONYMS.get(item.key, ())) + label_tokens


def _find(needle: str, text: str) -> int:
    """Kelime sınırına saygılı arama; bulunursa konum, yoksa -1.

    Düz ``in`` kullanmak kelime içi eşleşme üretiyordu: "geçerli" kelimesinin
    içindeki "gece" yüzünden şoför CV'sine "Gece vardiyası" öneriliyordu.
    """
    m = re.search(rf"\b{re.escape(needle)}\b", text)
    return m.start() if m else -1


def suggest_facts(text: str, catalog: list[CatalogItem]) -> list[Suggestion]:
    """CV metninden profil alanı **önerir**. Hiçbir şeyi profile yazmaz."""
    # CV'ler Türkçe karakter kullanmadan da yazılıyor ("Agir vasita"). Her iki
    # tarafı da katlamadan bu CV'ler hiç eşleşmiyordu.
    low = fold(text)
    out: list[Suggestion] = []

    for item in catalog:
        if item.is_legal_eligibility:
            continue  # D-013 — bu alanlar hiç önerilmez
        hit, idx = None, -1
        for n in _needles(item):
            if not n:
                continue
            pos = _find(n, low)
            if pos >= 0:
                hit, idx = n, pos
                break
        if hit is None:
            continue

        years: float | None = None
        if item.asks_years:
            # Eşleşmenin yakınındaki "N yıl" ifadesini arar. Bulamazsa boş bırakır —
            # tahmin üretmez; kullanıcı kendisi girer.
            window = low[max(0, idx - 120): idx + 120]
            m = _YEAR_NEAR.search(window)
            if m:
                years = float(m.group(1))

        out.append(
            Suggestion(
                key=item.key,
                label=item.label,
                category=item.category,
                needs_verification=item.needs_verification,
                asks_years=item.asks_years,
                years=years,
                matched_on=hit,
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
