"""Uygulama durumu.

İki tür veri var ve ikisi **farklı yerlerde** tutulur:

* **Kullanıcı profili** kalıcıdır (:mod:`storage`) — süreç kapansa da kalır.
* **İlan korpusu** bellektedir ve dış kaynaktan gelir; tazeliği vardır ve
  ``.cache/`` altında ayrı yönetilir (D-024). Kalıcı kılınması anlamsız olurdu:
  ilan kapanır, veritabanındaki kopya yaşamaya devam eder.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path

from isuygun_core.domain import CareerProfile, ProfileFact, VerificationState
from isuygun_ingest import search
from isuygun_ingest.pipeline import (
    NormalizedPosting,
    run_fixture_ingest,
    run_live_ingest,
)

from .storage import MemoryProfileStore, ProfileStore, open_store
from .taxonomy import CatalogItem, build_catalog, selectable

PROFILE_ID = "local"

#: Profil veritabanı. Öncelik `ISUYGUN_DSN` (PostgreSQL — ADR-001 hedefi);
#: yoksa SQLite dosyası. `ISUYGUN_DB=:memory:` kalıcılığı tamamen kapatır
#: (testler bunu kullanır).
def _db_path() -> Path | None:
    raw = os.environ.get("ISUYGUN_DB", "")
    if raw == ":memory:":
        return None
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[4] / ".data" / "profile.db"


@dataclass
class Store:
    postings: dict[str, NormalizedPosting] = field(default_factory=dict)
    catalog: list[CatalogItem] = field(default_factory=list)
    #: job_id -> aranabilir metin torbası (bkz. search.haystack)
    search_index: dict[str, str] = field(default_factory=dict)
    profile: CareerProfile = field(default_factory=lambda: CareerProfile(profile_id=PROFILE_ID))
    #: CV'den önerilen ama kullanıcı onayından geçmemiş alanlar (T-016)
    pending_cv_suggestions: list[dict] = field(default_factory=list)
    ingest_summary: dict = field(default_factory=dict)
    store: ProfileStore = field(
        default_factory=lambda: open_store(
            _db_path(), os.environ.get("ISUYGUN_DSN") or None
        )
    )

    def __post_init__(self) -> None:
        self.profile = self.store.load(PROFILE_ID)
        self.pending_cv_suggestions = self.store.load_suggestions(PROFILE_ID)

    @property
    def is_persistent(self) -> bool:
        return not isinstance(self.store, MemoryProfileStore)

    @property
    def backend(self) -> str:
        """Hangi depo kullanılıyor: postgres | sqlite | memory."""
        return type(self.store).__name__.replace("ProfileStore", "").lower()

    def _persist(self) -> None:
        self.store.save(self.profile)
        self.store.save_suggestions(PROFILE_ID, self.pending_cv_suggestions)

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
        # Arama torbaları bir kez kurulur. Her istekte 30 MB metni yeniden
        # katlamak, arama kutusuna her harf yazıldığında bunu tekrarlamak
        # demekti.
        self.search_index = {
            job_id: search.haystack(p) for job_id, p in self.postings.items()
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
        self._persist()

    def remove_fact(self, key: str) -> None:
        self.profile = replace(
            self.profile, facts=tuple(f for f in self.profile.facts if f.key != key)
        )
        self._persist()

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
        self._persist()

    def set_occupations(self, occupation_ids: list[str]) -> None:
        self.profile = replace(self.profile, occupation_ids=tuple(occupation_ids))
        self._persist()

    def reset_profile(self) -> None:
        self.profile = CareerProfile(profile_id=PROFILE_ID)
        self.pending_cv_suggestions = []
        self._persist()


STORE = Store()
