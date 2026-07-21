"""İlan metninden şart çıkarımı.

Çıkarım, CV tarafıyla **aynı sözlüğü** (:mod:`lexicon`) kullanır. Bu bir tercih
değil zorunluluktur: iki taraf farklı kelime dağarcığı kullanırsa eşleşme
matematiksel olarak mümkün olsa bile anlamsız olur — nitekim önceki sürümde
gerçek bir CV yüklendiğinde hiçbir şey eşleşmiyordu.

Güven derecelendirmesi (FS-4 / D-011): terim ilanın "aranan nitelikler" benzeri
bir bölümünde geçiyorsa daha yüksek güvenle, yalnızca gövdede geçiyorsa daha
düşük güvenle işaretlenir. Düşük güvenli şart **hard eleme yapamaz** —
``evaluate_requirement`` onu ``unknown`` üretmeye zorlar.
"""

from __future__ import annotations

import re

from isuygun_core.domain import Requirement

from . import lexicon
from .pipeline import fold

# "Aranan nitelikler" başlığından sonrası zorunluluk sinyali taşır.
_REQ_SECTION = re.compile(
    r"(aranan nitelik|genel nitelik|nitelikler|gereksinim|qualification|requirement|"
    r"what you.{0,10}ll need|who you are|we.{0,5}re looking for|beklenen|aday(?:lar)?(?:da|dan) beklen)",
    re.I,
)
_NICE_SECTION = re.compile(
    r"(tercih (?:sebebi|edilen)|nice to have|bonus|plus if|artı olarak|avantaj)", re.I
)
# Yan haklar bölümü şart DEĞİLDİR. "What We Offer" altında geçen "İngilizce" veya
# "eğitim" gibi terimleri şart saymak, ilanın istemediği bir şeyi istiyormuş gibi
# göstermek olurdu.
_BENEFIT_SECTION = re.compile(
    r"(what we offer|we offer|benefits|perks|yan haklar|sunduklarimiz|"
    r"neler sunuyoruz|why join|our culture)", re.I
)

#: Başlıkta geçen terimler için kullanılan sözde bölüm.
_TITLE_SECTION = "title"

# Zorunluluk vurgusu taşıyan kalıplar.
_MUST = re.compile(r"\b(zorunlu|sart(?:tir)?|gerekli|must have|required|mandatory)\b", re.I)


def _section_of(text_folded: str, position: int) -> str:
    """Terimin hangi bölümde geçtiğini kestirir.

    Döner: ``required`` | ``preferred`` | ``benefits`` | ``body``.
    En son açılan bölüm başlığı kazanır.
    """
    head = text_folded[:position]
    marks = {
        "required": _last(head, _REQ_SECTION),
        "preferred": _last(head, _NICE_SECTION),
        "benefits": _last(head, _BENEFIT_SECTION),
    }
    best = max(marks.items(), key=lambda kv: kv[1])
    return best[0] if best[1] >= 0 else "body"


def _last(s: str, pat: re.Pattern[str]) -> int:
    pos = -1
    for m in pat.finditer(s):
        pos = m.start()
    return pos


def _kind_and_confidence(term, section: str, near_text: str) -> tuple[str, float]:
    """Şartın türünü ve çıkarım güvenini belirler.

    Gate alanları (ehliyet, lisans) ilanda geçtiğinde ``hard`` sayılır — ama
    yalnızca yüksek güvenle çıkarıldıysa. Düşük güven hard elemeye dönüşemez.
    """
    gate = term.category in ("license", "work_authorization", "legally_required_certificate")

    if section == _TITLE_SECTION:
        # Başlıktaki terim işin tanımıdır; "tercih edilir" değildir.
        return ("hard" if gate else "required"), 0.9
    if section == "preferred":
        return "preferred", 0.8
    if section == "required":
        if gate or _MUST.search(near_text):
            return "hard", 0.9
        return "required", 0.85
    # Yalnızca gövdede geçiyor: ilan onu şart olarak saymamış olabilir.
    return ("required" if gate else "preferred"), 0.45


def extract_requirements(title: str, description: str) -> tuple[Requirement, ...]:
    """İlan metnini şartlara çevirir.

    Metin ``başlık + açıklama`` olarak birleştirilir; başlıkta geçen terimler
    ayrıca işaretlenir (bkz. :data:`_TITLE_SECTION`).
    """
    text = f"{title}\n{description}"
    folded = fold(text)
    title_len = len(fold(title))
    out: list[Requirement] = []

    for hit in lexicon.scan(text):
        # Başlıkta geçen terim, gövdede geçenden çok daha güvenilirdir: başlık
        # işin ne olduğunu söyler. Bazı kaynaklar (ör. Arbeitsagentur liste ucu)
        # açıklama metni hiç vermiyor; başlığı gövde gibi saymak o ilanların
        # **tamamını** değerlendirilemez yapıyordu — 229 ilan hiç eşleşmiyordu.
        in_title = hit.position < title_len
        section = _TITLE_SECTION if in_title else _section_of(folded, hit.position)
        if section == "benefits":
            continue  # yan hak, şart değil
        near = folded[max(0, hit.position - 120): hit.position + 120]
        kind, conf = _kind_and_confidence(hit.term, section, near)
        out.append(
            Requirement(
                key=hit.term.key,
                label=hit.term.label,
                kind=kind,
                category=hit.term.category,
                min_years=hit.years,
                extraction_confidence=conf,
                source_span=hit.matched_form,
            )
        )

    # D-013 — yasal uygunluk şartları ayrı işaretlenir; skora GİRMEZ.
    for key in lexicon.find_legal_eligibility(text):
        out.append(
            Requirement(
                key=f"legal_{key}",
                label=_LEGAL_LABEL.get(key, key),
                kind="hard",
                category="other",
                extraction_confidence=0.9,
                is_legal_eligibility=True,
            )
        )
    return tuple(out)


_LEGAL_LABEL = {
    "military": "Askerlik durumu",
    "age_limit": "Yaş şartı",
    "health": "Sağlık durumu şartı",
}


# --------------------------------------------------------------------------
# Meslek kümesi tahmini
# --------------------------------------------------------------------------


#: Meslek sinyali taşımayan kümeler — hangi işte olursan ol geçebilirler.
_NEUTRAL_CLUSTERS = ("Dil", "Eğitim düzeyi", "Çalışma düzeni")

#: Başlıktaki terim, gövdedeki terimden çok daha güçlü bir sinyaldir.
#: Bu ağırlık olmadan "Accounting Intern" ilanı, metninde SQL ve Excel geçtiği
#: için "Yazılım ve veri" kümesine düşüyordu.
_TITLE_WEIGHT = 6


def infer_occupation(title: str, requirements: tuple[Requirement, ...]) -> str:
    """İlanın hangi meslek kümesine düştüğünü kestirir.

    Kesin bir sınıflandırma değildir; feed gruplaması ve duplicate blocking için
    kullanılır. Bulunamazsa ``"genel"`` döner — uydurulmuş bir küme atanmaz.
    """
    counts: dict[str, float] = {}

    def add(cluster: str, w: float) -> None:
        if cluster not in _NEUTRAL_CLUSTERS:
            counts[cluster] = counts.get(cluster, 0) + w

    # Başlıkta geçen terimler baskın sinyaldir.
    for hit in lexicon.scan(title, want_years=False):
        add(hit.term.cluster, _TITLE_WEIGHT)

    for r in requirements:
        term = lexicon.BY_KEY.get(r.key)
        if term is None:
            continue
        # Düşük güvenle çıkarılmış (yalnızca gövdede geçen) terim az sayılır.
        w = 2 if r.kind in ("hard", "required") else 1
        if r.extraction_confidence < 0.5:
            w = 0.5
        add(term.cluster, w)

    if not counts:
        return "genel"
    return max(counts.items(), key=lambda kv: kv[1])[0]
