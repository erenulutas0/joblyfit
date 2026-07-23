-- İşe Uygun — profil şeması (D-027 / ADR-001)
--
-- Yalnızca **kullanıcı profili** burada tutulur. İlan korpusu bilinçli olarak
-- veritabanına yazılmaz: ilanlar dış kaynaktan gelir ve tazelikleri vardır
-- (D-024). Veritabanındaki bir kopya, kapanmış bir ilanı yaşatmaya devam eder
-- ve kullanıcıyı ölü bir bağlantıya yönlendirir.

-- Semantic reranking (T-006b) henüz yazılmadı; uzantı ADR-001 öngördüğü için
-- şimdiden açılıyor, çünkü sonradan eklemek imaj değişikliği gerektiriyor.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS profile (
    profile_id      TEXT PRIMARY KEY,
    occupation_ids  TEXT[] NOT NULL DEFAULT '{}',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- İsimli profillerin üst verisi (D-045). Matching'e GİRMEZ; onboarding
-- tercihleri ve gösterim içindir. `attrs` esnek JSON (bölge, özel kelimeler).
CREATE TABLE IF NOT EXISTS profile_meta (
    profile_id  TEXT PRIMARY KEY REFERENCES profile(profile_id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    collar      TEXT CHECK (collar IN ('white', 'blue') OR collar IS NULL),
    attrs       JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- `verification` bir CHECK ile sınırlanır.
--
-- Bu satır D-012'nin veritabanı düzeyindeki karşılığıdır: uygulama katmanı
-- tanınmayan bir değeri zaten `unverified`'a düşürüyor, ama veritabanına
-- doğrudan yazan bir yol (migration, elle müdahale, ileride bir admin aracı)
-- o kontrolü atlar. İki katman da tutmalı.
CREATE TABLE IF NOT EXISTS profile_fact (
    profile_id   TEXT NOT NULL REFERENCES profile(profile_id) ON DELETE CASCADE,
    key          TEXT NOT NULL,
    category     TEXT NOT NULL,
    verification TEXT NOT NULL
                 CHECK (verification IN ('unverified', 'user_asserted', 'verified')),
    years        DOUBLE PRECISION CHECK (years IS NULL OR years >= 0),
    PRIMARY KEY (profile_id, key)
);

-- CV'den gelen ama kullanıcı onayından geçmemiş öneriler.
-- Profil tablosundan AYRI durur: bunlar profil verisi değildir ve matching'e
-- giremez (T-016). Aynı tabloya konsaydı bir JOIN hatası onları profile
-- karıştırabilirdi.
CREATE TABLE IF NOT EXISTS cv_suggestion (
    profile_id  TEXT NOT NULL,
    key         TEXT NOT NULL,
    payload     JSONB NOT NULL,
    PRIMARY KEY (profile_id, key)
);

CREATE INDEX IF NOT EXISTS profile_fact_profile_idx ON profile_fact (profile_id);
CREATE INDEX IF NOT EXISTS cv_suggestion_profile_idx ON cv_suggestion (profile_id);
