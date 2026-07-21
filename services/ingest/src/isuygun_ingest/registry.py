"""Source Registry — dış dünyayla tek temas kapısı.

Bu modül D-002 ve D-018'in **kod düzeyindeki zorlayıcısıdır**:

* Registry'de kayıtlı olmayan source'tan ingestion yapılamaz (FR-202).
* ``scraping_permission`` ``allowed`` değilse ağ erişimi **başlatılamaz** —
  bu bir uyarı değil, exception'dır.
* D-018 gereği MVP'de yalnızca ``fixture`` access_method çalıştırılabilir;
  gerçek kaynağa bağlanmak OPEN-09/OPEN-19 kapanmadan mümkün değildir.

Kayıtların kanıtı ve gerekçesi:
``docs/architecture/SOURCE_REGISTRY.md`` §5 ve
``docs/research/TURKEY_SOURCE_LANDSCAPE.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

ScrapingPermission = Literal["allowed", "conditional", "rejected", "unknown"]
AccessMethod = Literal["api", "feed", "structured_data", "html", "fixture", "unknown"]
SourceStatus = Literal[
    "candidate", "under_review", "rejected",
    "active_limited", "active", "degraded", "suspended",
]


class PermissionError_(RuntimeError):
    """İzin durumu ağ erişimine elvermiyor."""


@dataclass(frozen=True, slots=True)
class SourceRecord:
    source_id: str
    name: str
    source_type: str
    base_url: str | None
    access_method: AccessMethod
    scraping_permission: ScrapingPermission
    policy_risk: Literal["low", "medium", "high", "unknown"]
    status: SourceStatus
    note: str = ""
    # Fixture modunda okunacak yerel dizin (D-018)
    fixture_dir: str | None = None
    # `allowed` işaretlemenin dayanağı. İzin iddiası kanıtsız yazılamaz (D-020);
    # `audit()` bunu denetler.
    permission_evidence: str = ""

    @property
    def may_fetch_network(self) -> bool:
        """Ağ erişimi yalnızca açıkça izinli VE aktif kayıtlarda mümkündür."""
        return (
            self.scraping_permission == "allowed"
            and self.status in ("active", "active_limited")
        )


# T-003 çıktısı. Hiçbiri `allowed` DEĞİL — bu kasıtlıdır (bkz. TURKEY_SOURCE_LANDSCAPE §13).
REGISTRY: dict[str, SourceRecord] = {
    r.source_id: r
    for r in [
        SourceRecord(
            source_id="src-tr-001", name="İşin Olsun", source_type="job_board",
            base_url="https://isinolsun.com", access_method="feed",
            scraping_permission="conditional", policy_risk="high",
            status="under_review",
            note="Wave 1 adayı. robots izinli; üyelik sözleşmesi §4.12 reuse kısıtı "
                 "→ yazılı izin gerekiyor (OPEN-19).",
        ),
        SourceRecord(
            source_id="src-tr-006", name="İŞKUR e-Şube", source_type="government_portal",
            base_url="https://esube.iskur.gov.tr", access_method="html",
            scraping_permission="conditional", policy_risk="medium",
            status="under_review",
            note="Wave 2 adayı. robots izinli; reuse lisansı yok.",
        ),
        SourceRecord(
            source_id="src-tr-008", name="Kamu İlan (SBB)", source_type="government_portal",
            base_url="https://kamuilan.sbb.gov.tr", access_method="html",
            scraping_permission="conditional", policy_risk="low",
            status="candidate",
            note="Wave 2 adayı. D-015 listing-only; hacim düşük.",
        ),
        SourceRecord(
            source_id="src-tr-014", name="Indeed Türkiye", source_type="job_board",
            base_url="https://tr.indeed.com", access_method="html",
            scraping_permission="rejected", policy_risk="high", status="rejected",
            note="robots ilan yollarını açıkça disallow ediyor (AI bot'ları dahil).",
        ),
        SourceRecord(
            source_id="src-tr-015", name="LinkedIn", source_type="job_board",
            base_url="https://www.linkedin.com", access_method="html",
            scraping_permission="rejected", policy_risk="high", status="rejected",
            note="robots.txt başında otomatik erişim açıkça yasak + login wall.",
        ),
        # D-018: geliştirme ve test için tek çalıştırılabilir kaynak.
        SourceRecord(
            source_id="src-fixture-001", name="Fixture Korpusu (geliştirme)",
            source_type="fixture", base_url=None, access_method="fixture",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            fixture_dir="fixtures/isinolsun_like",
            note="Sentetik ilanlar. Gerçek kaynak DEĞİLDİR; şema ve pipeline "
                 "doğrulaması için kullanılır (D-018).",
        ),
        # ------------------------------------------------------------------
        # D-020 — ATS public job board API'leri.
        # Bunlar şirketlerin kendi kariyer sayfalarını kurmaları için yayınladığı
        # kimlik doğrulaması istemeyen public uçlardır. İzin kanıtı `permission_evidence`
        # alanındadır; robots.txt kayıtları 2026-07-21'de doğrulanmıştır.
        # ------------------------------------------------------------------
        SourceRecord(
            source_id="src-ats-lever", name="Lever public job board API",
            source_type="ats_api", base_url="https://api.lever.co", access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "api.lever.co/robots.txt → 'User-agent: * / Allow: / / Crawl-delay: 1' "
                "(doğrulandı 2026-07-21). Uç kimlik doğrulaması istemez ve yanıt, "
                "ilanın kendi sayfasına giden hostedUrl taşır."
            ),
            note="Crawl-delay: 1 uygulanıyor. Yalnızca kayıtlı board slug'ları çekilir.",
        ),
        SourceRecord(
            source_id="src-ats-greenhouse", name="Greenhouse job board API",
            source_type="ats_api", base_url="https://boards-api.greenhouse.io",
            access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "boards-api.greenhouse.io/robots.txt → yalnızca '/embed/' disallow; "
                "'/v1/boards/' serbest (doğrulandı 2026-07-21). Resmî doküman uçların "
                "amacını 'build careers pages with a unique look and feel' diye tanımlar: "
                "developers.greenhouse.io/job-board.html"
            ),
        ),
        SourceRecord(
            source_id="src-ats-recruitee", name="Recruitee public offers API",
            source_type="ats_api", base_url="https://*.recruitee.com", access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "<firma>.recruitee.com/robots.txt → yalnızca '/v/' disallow; "
                "'/api/offers/' serbest (doğrulandı 2026-07-21)."
            ),
        ),
    ]
}

# D-020 — çekilmesine izin verilen şirket panoları.
#
# Kapsam bilinçli olarak **dar**: her slug elle doğrulanmıştır. Otomatik keşif
# yoktur; listede olmayan bir şirket çekilmez. Bu, kaynak listesinin sessizce
# büyümesini engeller.
BOARDS: tuple[tuple[str, str, str, str], ...] = (
    # (source_id,        platform,     slug,         işveren adı)
    ("src-ats-lever",      "lever",      "trendyol",   "Trendyol"),
    ("src-ats-lever",      "lever",      "dreamgames", "Dream Games"),
    ("src-ats-lever",      "lever",      "iyzico",     "iyzico"),
    ("src-ats-lever",      "lever",      "commencis",  "Commencis"),
    ("src-ats-lever",      "lever",      "ciceksepeti","Çiçeksepeti"),
    ("src-ats-recruitee",  "recruitee",  "macellan",   "Macellan"),
)


def get(source_id: str) -> SourceRecord:
    if source_id not in REGISTRY:
        raise KeyError(
            f"Kayıtsız source: {source_id!r}. Registry'de olmayan kaynaktan "
            "ingestion yapılamaz (FR-202)."
        )
    return REGISTRY[source_id]


def assert_fetchable(source_id: str) -> SourceRecord:
    """Ağ erişimi başlatmadan önce çağrılır. İzin yoksa **exception atar**.

    Bu fonksiyon D-002'nin kod düzeyindeki bekçisidir. Bypass edilmesi
    gereken bir engel değil, mimarinin bir parçasıdır.
    """
    rec = get(source_id)
    if rec.access_method == "fixture":
        return rec
    if not rec.may_fetch_network:
        raise PermissionError_(
            f"{rec.name} ({rec.source_id}) için ağ erişimi başlatılamaz.\n"
            f"  scraping_permission = {rec.scraping_permission}\n"
            f"  status              = {rec.status}\n"
            f"  gerekçe             = {rec.note}\n"
            "Bu kaynağa bağlanmak için önce yazılı izin (OPEN-19) veya "
            "T-008 Conditional rubriği (OPEN-09) gerekir. "
            "Bypass edilmez — D-002."
        )
    return rec


def allowed_without_evidence() -> list[SourceRecord]:
    """`allowed` işaretli ama gerekçesi yazılmamış kayıtlar. **Boş olmalı.**

    D-018'in "hiçbir kaynağa crawl yok" maddesi D-020 ile izinli API kanalları
    için revize edildi. Kuralın yerini alan yeni denetim budur: izin iddiası
    kanıtsız yazılamaz. Bu liste boş değilse birisi bir kaynağı gerekçesiz
    açmış demektir.
    """
    return [
        r for r in REGISTRY.values()
        if r.scraping_permission == "allowed"
        and r.access_method != "fixture"
        and not r.permission_evidence.strip()
    ]


def audit() -> dict[str, int]:
    """Registry sağlık denetimi (D-020)."""
    return {
        "toplam": len(REGISTRY),
        "allowed": sum(1 for r in REGISTRY.values() if r.scraping_permission == "allowed"),
        "kanitsiz_allowed": len(allowed_without_evidence()),  # 0 olmalı
        "conditional": sum(1 for r in REGISTRY.values() if r.scraping_permission == "conditional"),
        "rejected": sum(1 for r in REGISTRY.values() if r.scraping_permission == "rejected"),
        "board_sayisi": len(BOARDS),
    }
