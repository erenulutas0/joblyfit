"""Uygulama durumu.

İki tür veri var ve ikisi **farklı yerlerde** tutulur:

* **Kullanıcı profili** kalıcıdır (:mod:`storage`) — süreç kapansa da kalır.
* **İlan korpusu** bellektedir ve dış kaynaktan gelir; tazeliği vardır ve
  ``.cache/`` altında ayrı yönetilir (D-024). Kalıcı kılınması anlamsız olurdu:
  ilan kapanır, veritabanındaki kopya yaşamaya devam eder.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path

from isuygun_core.domain import CareerProfile, ProfileFact, VerificationState


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
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
    #: job_id -> aranabilir ilan (bkz. search.haystack). Başlık ayrı alanda
    #: tutulur; arama sonuçlarında başlıkta geçenler öne alınır.
    search_index: dict[str, search.Doc] = field(default_factory=dict)
    profile: CareerProfile = field(default_factory=lambda: CareerProfile(profile_id=PROFILE_ID))
    #: CV'den önerilen ama kullanıcı onayından geçmemiş alanlar (T-016)
    pending_cv_suggestions: list[dict] = field(default_factory=list)
    #: Şu an etkin profil (D-045). Kullanıcı isimli profiller arasında geçer;
    #: bütün profil işlemleri bu id üzerinde çalışır.
    active_id: str = PROFILE_ID
    ingest_summary: dict = field(default_factory=dict)
    #: Korpus her yüklendiğinde artar. Feed önbelleği (D-054) buna bakar: arka
    #: planda tazeleme olduğunda önbellek kendiliğinden geçersizleşir, yoksa
    #: kullanıcı saatlerce eski ilan listesini görürdü.
    corpus_version: int = 0
    #: Arka plan tazelemesinin durumu (D-055): running | ok | failed | idle.
    #: `/api/health` bunu yayınlar — tazeleme sessizce ölürse korpus boş kalıyor
    #: ve dışarıdan bakan biri sebebini göremiyordu.
    refresh_state: dict = field(
        default_factory=lambda: {"status": "idle", "error": None})
    store: ProfileStore = field(
        default_factory=lambda: open_store(
            _db_path(), os.environ.get("ISUYGUN_DSN") or None
        )
    )

    def __post_init__(self) -> None:
        # Geriye dönük uyum: daha önce tek profil ("local") vardı. Meta boşsa
        # ama o profilde veri varsa, onu "Varsayılan" adıyla meta'ya taşı ki
        # eski kullanıcı verisi kaybolmasın.
        metas = self.store.list_profiles()
        if not metas:
            existing = self.store.load(PROFILE_ID)
            if existing.facts or existing.occupation_ids:
                self.store.save_meta({
                    "id": PROFILE_ID, "name": "Varsayılan", "collar": None,
                    "attrs": {}, "created_at": _now(),
                })
                metas = self.store.list_profiles()
        self.active_id = metas[0]["id"] if metas else PROFILE_ID
        self._load_active()

    def _load_active(self) -> None:
        self.profile = self.store.load(self.active_id)
        self.pending_cv_suggestions = self.store.load_suggestions(self.active_id)

    @property
    def is_persistent(self) -> bool:
        return not isinstance(self.store, MemoryProfileStore)

    @property
    def backend(self) -> str:
        """Hangi depo kullanılıyor: postgres | sqlite | memory."""
        return type(self.store).__name__.replace("ProfileStore", "").lower()

    def _persist(self) -> None:
        self.store.save(self.profile)
        self.store.save_suggestions(self.active_id, self.pending_cv_suggestions)

    # -- isimli profiller (D-045) ------------------------------------------

    def list_profiles(self) -> list[dict]:
        metas = self.store.list_profiles()
        for m in metas:
            m["is_active"] = m["id"] == self.active_id
            m["fact_count"] = len(self.store.load(m["id"]).facts)
        return metas

    def create_profile(self, name: str, *, collar: str | None = None,
                       attrs: dict | None = None, activate: bool = True) -> str:
        """Yeni isimli profil oluşturur ve id'sini döner."""
        pid = f"p-{uuid.uuid4().hex[:12]}"
        self.store.save(CareerProfile(profile_id=pid))
        self.store.save_meta({
            "id": pid, "name": name.strip() or "Profil", "collar": collar,
            "attrs": attrs or {}, "created_at": _now(),
        })
        if activate:
            self.active_id = pid
            self._load_active()
        return pid

    def activate(self, profile_id: str) -> None:
        if profile_id not in {m["id"] for m in self.store.list_profiles()}:
            raise KeyError(f"Profil yok: {profile_id!r}")
        self.active_id = profile_id
        self._load_active()

    def rename_profile(self, profile_id: str, name: str) -> None:
        metas = {m["id"]: m for m in self.store.list_profiles()}
        if profile_id not in metas:
            raise KeyError(f"Profil yok: {profile_id!r}")
        m = metas[profile_id]
        m["name"] = name.strip() or m["name"]
        self.store.save_meta(m)

    def update_meta(self, profile_id: str, *, collar: str | None = None,
                    attrs: dict | None = None) -> None:
        metas = {m["id"]: m for m in self.store.list_profiles()}
        if profile_id not in metas:
            raise KeyError(f"Profil yok: {profile_id!r}")
        m = metas[profile_id]
        if collar is not None:
            m["collar"] = collar
        if attrs is not None:
            m["attrs"] = {**m.get("attrs", {}), **attrs}
        self.store.save_meta(m)

    def delete_profile(self, profile_id: str) -> None:
        """Profili siler. Son profili silmek yasak — sistemde en az bir profil
        kalmalı, yoksa kullanıcı hiçbir yere yazamaz."""
        metas = self.store.list_profiles()
        if profile_id not in {m["id"] for m in metas}:
            raise KeyError(f"Profil yok: {profile_id!r}")
        if len(metas) <= 1:
            raise ValueError("Son profil silinemez.")
        self.store.delete_profile(profile_id)
        if self.active_id == profile_id:
            self.active_id = next(m["id"] for m in metas if m["id"] != profile_id)
            self._load_active()

    # -- ilanlar -----------------------------------------------------------

    def load(self, *, live: bool = True, include_fixtures: bool = True,
             stale_ok: bool = False) -> None:
        """İlanları ingest edip belleğe alır.

        ``live=True`` iken Registry'de izinli ATS panolarından **gerçek** ilanlar
        çekilir (D-020). Ağ hatası ingest'i düşürmez; ``errors`` alanına yazılır
        ve arayüzde görünür — sessizce boş liste göstermek, kaynağın kapandığını
        gizlerdi.

        ``stale_ok=True`` **ağa çıkmaz**: ne varsa (eski cache) onu yükler. Açılışta
        siteyi anında ayağa kaldırmak için kullanılır; tazeleme :meth:`refresh` ile
        arka planda yapılır (D-047).
        """
        if live:
            try:
                result = run_live_ingest(include_fixtures=include_fixtures,
                                         stale_ok=stale_ok)
            except Exception as e:  # ağ tamamen kapalıysa fixture'a düş
                try:
                    result = run_fixture_ingest()
                except Exception:
                    # Üretim imajında fixture yok; o zaman boş korpusla aç.
                    # Site ayakta kalır, bir sonraki tazeleme gerçek veriyi getirir.
                    result = {"canonical_postings": {}, "source": "boş",
                              "fetched": 0, "canonical": 0, "duplicates_merged": 0}
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
        self.corpus_version += 1
        self.ingest_summary = {
            "source": result["source"],
            "fetched": result["fetched"],
            "canonical": result["canonical"],
            "duplicates_merged": result["duplicates_merged"],
            "stale_dropped": result.get("stale_dropped", 0),
            "max_age_days": result.get("max_age_days", 45),
            "truncated": result.get("truncated", 0),
            "from_cache": result.get("from_cache", False),
            "stale_logic": result.get("stale_logic", False),
            "skipped_sources": result.get("skipped_sources", {}),
            "boards": result.get("boards", []),
            "errors": result.get("errors", []),
        }

    def refresh(self) -> None:
        """Korpusu **ağa çıkarak** tazeler (arka planda çağrılır, D-047).

        Açılışta `load(stale_ok=True)` siteyi eski cache'le anında ayağa kaldırır;
        bu metod sonra gerçek çekimi yapar ve sonucu yerine koyar. Hata olursa
        eski korpus yerinde kalır — site asla veriyi kaybetmez.
        """
        self.load(live=True, stale_ok=False, include_fixtures=False)

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
        """Etkin profilin **içeriğini** temizler (profili silmez)."""
        self.profile = CareerProfile(profile_id=self.active_id)
        self.pending_cv_suggestions = []
        self._persist()


STORE = Store()
