"""Uygulama durumu — şimdilik bellekte.

**Bu kalıcı depolama DEĞİLDİR.** Stack kararı PostgreSQL'dir (ADR-001); bu modül
onun yerine geçen geçici bir katmandır ve süreç kapanınca veri kaybolur. Amacı,
şema ve API sözleşmesini kalıcılık kurulmadan önce çalışır halde doğrulamaktır.

Kalıcılığa geçerken değişecek tek yer burasıdır: API katmanı ``Store``
arayüzünü kullanır, doğrudan dict'e dokunmaz.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from isuygun_core.domain import CareerProfile, ProfileFact, VerificationState
from isuygun_ingest.pipeline import (
    NormalizedPosting,
    run_fixture_ingest,
    run_live_ingest,
)

from .taxonomy import CatalogItem, build_catalog, selectable


@dataclass
class Store:
    postings: dict[str, NormalizedPosting] = field(default_factory=dict)
    catalog: list[CatalogItem] = field(default_factory=list)
    profile: CareerProfile = field(default_factory=lambda: CareerProfile(profile_id="local"))
    #: CV'den önerilen ama kullanıcı onayından geçmemiş alanlar (T-016)
    pending_cv_suggestions: list[dict] = field(default_factory=list)
    ingest_summary: dict = field(default_factory=dict)

    # -- ilanlar -----------------------------------------------------------

    def load(self, *, live: bool = True, include_fixtures: bool = True) -> None:
        """İlanları ingest edip belleğe alır.

        ``live=True`` iken Registry'de izinli ATS panolarından **gerçek** ilanlar
        çekilir (D-020). Ağ hatası ingest'i düşürmez; ``errors`` alanına yazılır
        ve arayüzde görünür — sessizce boş liste göstermek, kaynağın kapandığını
        gizlerdi.
        """
        if live:
            try:
                result = run_live_ingest(include_fixtures=include_fixtures)
            except Exception as e:  # ağ tamamen kapalıysa fixture'a düş
                result = run_fixture_ingest()
                result = {**result, "errors": [{"board": "canlı ingest", "error": str(e)}],
                          "boards": [], "stale_dropped": 0}
        else:
            result = run_fixture_ingest()
            result = {**result, "errors": [], "boards": [], "stale_dropped": 0}

        self.postings = {
            p.job.job_id: p for p in result["canonical_postings"].values()
        }
        self.catalog = build_catalog()
        self.ingest_summary = {
            "source": result["source"],
            "fetched": result["fetched"],
            "canonical": result["canonical"],
            "duplicates_merged": result["duplicates_merged"],
            "stale_dropped": result.get("stale_dropped", 0),
            "max_age_days": result.get("max_age_days", 45),
            "truncated": result.get("truncated", 0),
            "from_cache": result.get("from_cache", False),
            "boards": result.get("boards", []),
            "errors": result.get("errors", []),
        }

    def job(self, job_id: str) -> NormalizedPosting | None:
        return self.postings.get(job_id)

    def catalog_items(self) -> list[CatalogItem]:
        return selectable(self.catalog)

    def catalog_item(self, key: str) -> CatalogItem | None:
        return next((i for i in self.catalog if i.key == key), None)

    # -- profil ------------------------------------------------------------

    def set_fact(
        self,
        key: str,
        *,
        verification: VerificationState = "user_asserted",
        years: float | None = None,
    ) -> None:
        item = self.catalog_item(key)
        if item is None:
            raise KeyError(f"Katalogda olmayan alan: {key!r}")
        if item.is_legal_eligibility:
            # D-013 + D-006: bu alanlar profile hiç yazılmaz.
            raise ValueError(
                f"{item.label!r} yasal uygunluk şartıdır; profile kaydedilmez."
            )
        facts = tuple(f for f in self.profile.facts if f.key != key)
        facts += (
            ProfileFact(
                key=key,
                category=item.category,
                verification=verification,
                years=years,
            ),
        )
        self.profile = replace(self.profile, facts=facts)

    def remove_fact(self, key: str) -> None:
        self.profile = replace(
            self.profile, facts=tuple(f for f in self.profile.facts if f.key != key)
        )

    def verify_fact(self, key: str) -> None:
        """Belgeyi 'doğrulanmış' yapar.

        Gerçek sistemde burada bir **belge doğrulama akışı** olur (yükleme,
        kontrol, gerekirse manuel inceleme). MVP'de bu adım simüle edilir ve
        arayüzde açıkça öyle etiketlenir — doğrulanmış gibi gösterilen sahte bir
        durum üretmek D-012'yi anlamsız kılardı.
        """
        fact = self.profile.find(key)
        if fact is None:
            raise KeyError(f"Profilde olmayan alan: {key!r}")
        facts = tuple(
            replace(f, verification="verified") if f.key == key else f
            for f in self.profile.facts
        )
        self.profile = replace(self.profile, facts=facts)

    def set_occupations(self, occupation_ids: list[str]) -> None:
        self.profile = replace(self.profile, occupation_ids=tuple(occupation_ids))

    def reset_profile(self) -> None:
        self.profile = CareerProfile(profile_id="local")
        self.pending_cv_suggestions = []


STORE = Store()
