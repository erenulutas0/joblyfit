# DECISIONS.md — Karar Kaydı

> **Purpose:** Projede alınan kararların kaydı. Her kayıt **Decision / Reason /
> Alternatives / Consequence** alanlarını içerir. Faz 0 kararları bu dosyada tam kayıt
> olarak tutulur; implementation fazından itibaren büyük mimari kararlar ayrıca birer ADR
> olarak [docs/adr/](docs/adr/README.md) altına yazılır ve buraya özet satırı eklenir.
> Karar olmayan varsayımlar burada değil, ilgili dokümanda "Assumption" olarak durur
> (ana liste: [PRD.md](docs/product/PRD.md) → Assumptions).

Status değerleri: `Confirmed` (kullanıcı onaylı) · `Proposed` (agent önerisi, onay bekliyor) · `Superseded`

---

## D-001 — Technology stack seçimi ertelendi

- **Status:** Confirmed (kullanıcının açık talebi)
- **Date:** 2026-07-20
- **Decision:** Faz 0 boyunca programming language, framework, database, cloud provider
  seçilmez; bütün tasarım technology-independent yazılır.
- **Reason:** Ürün ve mimari netleşmeden yapılacak stack seçimi tasarımı kısıtlar;
  kullanıcı da bunu açıkça istedi.
- **Alternatives:** Baştan stack seçmek (hız kazandırır ama erken bağımlılık yaratır).
- **Consequence:** Dokümanlar kavramsal kalır; implementation başlamadan önce stack
  ADR'si yazılmak zorundadır (bkz. [TASKS.md](TASKS.md) → T-012).

## D-002 — Compliance-first ingestion, bypass yasağı

- **Status:** Confirmed (kullanıcının açık talebi)
- **Date:** 2026-07-20
- **Decision:** Login wall, CAPTCHA veya bot-detection bypass mekanizması hiçbir koşulda
  tasarlanmaz/yazılmaz. Her source için robots kuralları, Terms of Service, rate limit ve
  permission durumu [Source Registry](docs/architecture/SOURCE_REGISTRY.md) üzerinden
  takip edilir; uygun olmayan source ingest edilmez.
- **Reason:** Hukuki ve etik risk; ayrıca platformun sürdürülebilirliği source
  ilişkilerinin bozulmamasına bağlı.
- **Alternatives:** "Gri bölge" agresif scraping (kısa vadede daha çok ilan, uzun vadede
  hukuki risk ve IP ban); yalnızca API/feed kullanmak (kapsama çok daralır).
- **Consequence:** Bazı büyük platformlar kapsam dışı kalabilir; kapsama açığı
  compliant kaynak çeşitliliğiyle kapatılır. Kapsam riski:
  [RISK_REGISTER.md](docs/security/RISK_REGISTER.md) → R-01.

## D-003 — Hybrid Matching mimarisi

- **Status:** Confirmed
- **Date:** 2026-07-20
- **Decision:** Matching yalnızca semantic similarity ile yapılmaz. Pipeline: (1) hard
  requirement eleme/işaretleme, (2) faktör-bazlı structured scoring, (3) semantic
  similarity katkısı, (4) preference ve feedback ayarı. Detay:
  [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md).
- **Reason:** Salt embedding benzerliği license/shift/location gibi kesin şartları
  yakalayamaz ve açıklanamaz; salt keyword ise meslek çeşitliliğini kaldıramaz.
- **Alternatives:** Pure semantic (açıklanamaz, hard constraint körlüğü); pure
  rule-based (bakım maliyeti yüksek, esneklik düşük); end-to-end learned ranking
  (soğuk başlangıçta veri yok, bias riski yüksek).
- **Consequence:** Occupation Taxonomy ve structured extraction kalitesine bağımlılık
  artar; buna karşılık explainability doğal olarak üretilebilir.

## D-004 — Occupation Taxonomy mevcut bir standarttan türetilir

- **Status:** Proposed (standart seçimi open question)
- **Date:** 2026-07-20
- **Decision:** Taxonomy sıfırdan icat edilmez; ESCO veya O*NET gibi açık bir occupation
  standardı çekirdek alınır, üzerine platformun qualification-template extension katmanı
  eklenir. Detay: [OCCUPATION_TAXONOMY.md](docs/architecture/OCCUPATION_TAXONOMY.md).
- **Reason:** Binlerce mesleği ve aralarındaki geçiş ilişkilerini sıfırdan modellemek
  yıllar alır; açık standartlar çok dillidir ve career transition için ilişki verisi içerir.
- **Alternatives:** Sıfırdan taxonomy (tam kontrol, sürdürülemez maliyet); taxonomy'siz
  serbest metin (matching kalitesi düşer).
- **Consequence:** Standardın güncelleme döngüsüne bağımlılık; lokal meslekler için
  extension süreci gerekir. ❓ OPEN: ESCO mu O*NET mi — hedef pazara göre seçilecek
  (bkz. [CONTEXT.md](CONTEXT.md) → Açık Konular).

## D-005 — Explainability zorunlu, Match Score garanti değil

- **Status:** Confirmed (kullanıcının açık talebi)
- **Date:** 2026-07-20
- **Decision:** Her recommendation, karşılanan/eksik requirement'ları, gerekçeyi ve
  confidence'ı içeren bir Match Explanation ile sunulur. Match Score kullanıcıya her
  zaman "tahmindir, garanti değildir" çerçevesiyle gösterilir.
- **Reason:** Kullanıcı güveni ve yanlış yönlendirme riskinin (özellikle regulated
  profession'larda) azaltılması.
- **Alternatives:** Yalnızca yüzde göstermek (basit ama güven ve fayda düşük).
- **Consequence:** Matching pipeline'ının her faktörü explanation üretecek şekilde
  structured olmalı; UI'da explanation birinci sınıf alan olur.

## D-006 — Sensitive attribute'lar matching'de kullanılmaz

- **Status:** Confirmed (kullanıcının açık talebi)
- **Date:** 2026-07-20
- **Decision:** Age, gender, photo, ethnicity, religion, marital status ve işle doğrudan
  ilgisi olmayan diğer sensitive attribute'lar Match Score hesabına girmez; CV'den
  parse edilseler bile matching feature set'ine taşınmaz. Tam politika:
  [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md) → Fairness Constraints ve
  [AI_SYSTEM.md](docs/architecture/AI_SYSTEM.md) → Bias & Fairness.
- **Reason:** Ayrımcılık riski, yasal zorunluluklar ve etik ilke.
- **Alternatives:** Yok — bu bir kısıt, optimizasyon konusu değil.
- **Consequence:** CV parsing katmanında sensitive alanlar ayrıştırılıp matching'e giden
  veri yolundan izole edilir; proxy-feature sızıntısı için fairness testi gerekir.

## D-007 — MVP tek pazar + sınırlı source seti ile başlar

- **Status:** Proposed
- **Date:** 2026-07-20
- **Decision:** MVP tek bir launch pazarına ve 3-5 doğrulanmış compliant job source'a
  odaklanır; core loop (profil → ingestion → matching → explainable feed → feedback)
  uçtan uca çalışır. Scope detayı: [PRD.md](docs/product/PRD.md).
- **Reason:** Çok pazarlı/çok kaynaklı başlangıç, taxonomy ve compliance yükünü MVP'de
  taşınamaz hale getirir; matching kalitesi dar kapsamda ölçülüp iyileştirilebilir.
- **Alternatives:** Geniş kapsamlı başlangıç (kapsama iyi görünür ama kalite ve
  compliance kontrol edilemez).
- **Consequence:** İlk kullanıcı kitlesi coğrafi olarak sınırlı olur; pazar seçimi
  open question (❓ CONTEXT.md → Açık Konular #1, #2).
