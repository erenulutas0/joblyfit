"""Match Explanation üretimi (D-005).

Kurallar:

* Her iddia bir ``RequirementOutcome``'a dayanır — evidence'sız cümle üretilmez.
* ``worth_applying`` serbest yorumla değil, **kural tablosuyla** üretilir
  (MATCHING_ENGINE §4). Hiçbir durumda mutlak "başvurma" denmez.
* Match Score hiçbir yerde yüzde olarak sunulmaz; bant + "bu bir tahmindir"
  çerçevesi zorunludur.
* ``unknown`` satırları "eksiğin var" diye değil, "şunu eklersen netleşir" diye
  yazılır (D-011).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .domain import MatchBand, RequirementOutcome
from .matching import MatchResult

BAND_LABEL: dict[MatchBand, str] = {
    MatchBand.STRONG: "Güçlü eşleşme",
    MatchBand.GOOD: "İyi eşleşme",
    MatchBand.CONDITIONAL: "Şartlı eşleşme",
    MatchBand.WEAK: "Zayıf eşleşme",
}

DISCLAIMER = (
    "Eşleşme derecesi bir tahmindir; işe alınacağın anlamına gelmez ve işverenin "
    "kararını yansıtmaz. Şartların tamamını ilanın kendi sayfasından kontrol et."
)

LISTING_ONLY_NOTE = (
    "Bu bir kamu ilanı. Sınav puanı, kadro ve mevzuat şartları tam olarak "
    "modellenmediği için uygunluk değerlendirmesi yapılmaz. Şartların tamamı "
    "resmî ilan metnindedir."
)

INSUFFICIENT_DATA_NOTE = (
    "Bu ilanı profilindeki bilgiyle değerlendiremedik — şartların hiçbiri için "
    "karşılaştıracak kayıt yok. Bu, ilanın sana uymadığı anlamına gelmez."
)


@dataclass(frozen=True, slots=True)
class ExplanationLine:
    text: str
    evidence: str
    action_label: str | None = None   # "Profilime ekle" / "Belgeyi doğrula"
    action_field: str | None = None


@dataclass(frozen=True, slots=True)
class MatchExplanation:
    band_label: str | None
    confidence_label: str | None
    why: tuple[str, ...] = ()
    met: tuple[ExplanationLine, ...] = ()
    unmet: tuple[ExplanationLine, ...] = ()
    unknown: tuple[ExplanationLine, ...] = ()
    legal_eligibility_notices: tuple[str, ...] = ()
    verification_notice: str | None = None
    worth_applying: str = ""
    worth_applying_rule: str = ""
    disclaimer: str = DISCLAIMER
    listing_only_note: str | None = None
    insufficient_data_note: str | None = None


CONF_LABEL = {"high": "Yüksek", "medium": "Orta", "low": "Düşük"}


def _line(o: RequirementOutcome) -> ExplanationLine:
    action_label = None
    if o.state == "unknown":
        action_label = {
            "unverified_gate_field": "Belgeyi doğrula",
            "missing_duration": "Süreyi ekle",
        }.get(o.unknown_reason, "Profilime ekle")
    return ExplanationLine(
        text=o.requirement.label,
        evidence=o.evidence,
        action_label=action_label,
        action_field=o.missing_field_hint,
    )


def _worth_applying(result: MatchResult) -> tuple[str, str]:
    """MATCHING_ENGINE §4 kural tablosu. Mutlak 'başvurma' asla üretilmez."""
    if result.blocking_unmet:
        names = ", ".join(o.requirement.label for o in result.blocking_unmet)
        return (
            f"Bu ilan {names} şartını istiyor ve profilinde karşılanmıyor. "
            "Yine de başvurmak senin kararın.",
            "hard_unmet",
        )
    if result.needs_verification:
        names = ", ".join(o.requirement.label for o in result.needs_verification)
        return (
            f"Önce {names} bilgisini doğrula — bu ilan için zorunlu. "
            "Doğrulayınca değerlendirme kesinleşir.",
            "hard_unknown_verify",
        )
    if result.insufficient_data:
        return (
            "Bu ilan için henüz bir değerlendirme yapamıyoruz. Aşağıdaki "
            "bilgileri profiline eklersen ilanın sana uyup uymadığını gösterebiliriz.",
            "insufficient_data",
        )
    strong_side = result.band in (MatchBand.STRONG, MatchBand.GOOD)

    if result.unknown:
        first_out = result.unknown[0]
        first = first_out.requirement.label
        n = len(result.unknown)
        rest = f" (ve {n - 1} şart daha)" if n > 1 else ""

        # "Bilmiyoruz"un üç ayrı sebebi var ve üçü kullanıcıya farklı şey
        # söyler. Hepsini "profilinde yok" diye özetlemek, sahip olduğu bir
        # beceriyi yokmuş gibi göstermeye kadar gidiyordu.
        if first_out.unknown_reason == "missing_duration":
            return (
                f"{first} profilinde var ama kaç yıllık olduğu yazmıyor{rest}. "
                "Süreyi eklersen bu ilana uyup uymadığın netleşir.",
                "unknown_duration",
            )
        if strong_side:
            # Bandı olumlu olan bir ilana "değerlendirme eksik kaldı" diye
            # başlamak, kullanıcının kazandığı zemini gizler. Önce ne
            # bildiğimizi söyleriz, sonra neyi bilmediğimizi.
            return (
                f"Kontrol edebildiğimiz şartları karşılıyorsun. {first} bilgisi"
                f"{rest} profilinde yok — eklersen değerlendirme netleşir.",
                "partial_unknown",
            )
        return (
            f"Değerlendirme eksik kaldı: {first} bilgisi{rest} profilinde yok. "
            "Eklersen bu ilanın sana uyup uymadığı netleşir.",
            "hard_unknown_missing",
        )
    if result.band == MatchBand.STRONG:
        return ("Aradıkları şartların tamamını karşılıyor görünüyorsun.", "strong")
    return ("Başvurulabilir; aşağıdaki noktalar eksik görünüyor.", "partial")


def build_explanation(result: MatchResult) -> MatchExplanation:
    """MatchResult'tan kullanıcıya gösterilecek açıklamayı üretir."""
    if result.listing_only:
        return MatchExplanation(
            band_label=None,
            confidence_label=None,
            listing_only_note=LISTING_ONLY_NOTE,
            worth_applying="Şartları resmî kaynaktan kontrol et.",
            worth_applying_rule="listing_only",
            disclaimer=DISCLAIMER,
        )

    met, unmet, unknown = result.met, result.unmet, result.unknown

    legal = tuple(
        f"Bu ilan «{o.requirement.label}» şartı içeriyor. Bu şart değerlendirmeye "
        "katılmaz; ilanın kendi sayfasından kontrol et."
        for o in result.outcomes
        if o.requirement.is_legal_eligibility
    )

    # `why` yalnızca gerçekten karşılanmış şartlardan üretilir. Karşılanan şart
    # yoksa cümle de yoktur: "mesleğin örtüşüyor" gibi kanıtsız bir iddia
    # üretmek, açıklama katmanının kendi kuralını çiğnerdi (D-005).
    why = [f"{o.requirement.label}: {o.evidence}" for o in met[:3]]

    verification_notice = None
    if result.needs_verification:
        verification_notice = (
            "Bu ilanda zorunlu bir belge var ve profilinde doğrulanmadı. "
            "Doğrulamadan bu şartı «karşılanıyor» olarak göstermiyoruz."
        )

    text, rule = _worth_applying(result)

    return MatchExplanation(
        band_label=BAND_LABEL.get(result.band) if result.band else None,
        confidence_label=CONF_LABEL.get(result.confidence.value) if result.confidence else None,
        why=tuple(why),
        met=tuple(_line(o) for o in met),
        unmet=tuple(_line(o) for o in unmet),
        unknown=tuple(_line(o) for o in unknown),
        legal_eligibility_notices=legal,
        verification_notice=verification_notice,
        worth_applying=text,
        worth_applying_rule=rule,
        insufficient_data_note=INSUFFICIENT_DATA_NOTE if result.insufficient_data else None,
    )
