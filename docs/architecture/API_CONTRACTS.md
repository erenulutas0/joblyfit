# API_CONTRACTS.md — Bileşenler Arası Kavramsal Contract'lar

> **Purpose:** Alt sistemler arasındaki sözleşmelerin **kavramsal** tanımı: kim kime ne
> sağlar, hangi garanti ile. Protokol/format (REST/GraphQL/queue şeması vb.) stack
> kararından (D-001) sonra somutlaşır; buradaki contract'lar o tasarımın girdisidir.
> Bileşen sorumlulukları: [ARCHITECTURE.md](ARCHITECTURE.md). Veri şekilleri:
> [DATA_MODEL.md](DATA_MODEL.md).

## Gösterim

Her contract: **Sağlayıcı → Tüketici : Yetenek** — girdi/çıktı özeti + garantiler.
Çıktı şekilleri DATA_MODEL.md entity'lerine referanstır (tekrar tanımlanmaz).

## C-1. Ingestion → Core Data

**Ingestion Pipeline → Job Posting Store : normalize posting yayınlama**
- Girdi yok (pipeline üretir); çıktı: JobPosting (provenance + quality + confidence dolu).
- Garanti: registry'de kayıtlı olmayan source'tan kayıt üretilmez (FR-202); her kayıt
  canonical'a bağlanmış veya yeni canonical açılmıştır.

**Ingestion → Matching : posting ve canonical olayları**
- Olaylar: `posting_created`, `posting_updated` (content değişti), `posting_expired`,
  `canonical_merged {surviving_id, absorbed_id}`, `canonical_split`,
  `source_suspended {source_id, immediate_deindex: bool}`.
- Garantiler: expired olayı yayıldıktan sonra o canonical feed hesaplarına girmez
  (NFR-102). `canonical_merged` sonrası absorbed canonical'a bağlı feedback, application
  ve saved kayıtları **hayatta kalan canonical'a taşınır**; kullanıcıya dönük referanslar
  kaybolmaz. `source_suspended` + `immediate_deindex` alındığında o source'un posting'leri
  aynı anda feed/arama/digest dışına alınır (FS-13).
- **C-4 ile hizalama:** bu olayların **tamamı** MatchResult invalidation tetikleyicisidir;
  tetik listesi tek yerde tanımlıdır:
  [MATCHING_ENGINE.md](MATCHING_ENGINE.md) §2.3.

## C-2. Taxonomy Servisi

**Taxonomy → (Extraction, Matching, UI) : kavram sorguları**
- Yetenekler: title/metin → occupation adayları (+confidence); qualification arama/çözme;
  Occupation Profile getirme; transition komşuları; label'lar (MVP: Türkçe + core standardın dili; çok dilli genişleme F-22/V1).
- Garanti: cevaplar taxonomy versiyon kimliği taşır; `deprecated` kavramlar yönlendirme
  ile döner (kırık referans olmaz).

## C-3. Understanding

**CV Parser → Profile Store : profil taslağı**
- Girdi: CV dosyası (güvenlik kontrolünden geçmiş). Çıktı: CareerProfile taslak alanları
  (her biri value+confidence+source_span) + discard edilen sensitive alanların meta-kaydı.
- Garantiler: hiçbir alan `verified` olarak dönmez (FR-103); sensitive alanlar profil
  taslağında bulunmaz **ve hiçbir yerde kalıcılaştırılmaz** (D-006); gate-relevant alanlar
  `unverified` döner ve doğrulanana kadar hard requirement'ı `met` yapamaz (D-012).

**Requirement Extractor → Job Posting Store : requirement seti**
- Girdi: normalize ilan metni + structured data. Çıktı: requirements[]
  (kind, kavram bağlantısı, min_years?/level?/jurisdiction?, is_legal_eligibility?,
  source_span, confidence).
- Garanti: hard sınıflaması yüksek confidence şartına bağlıdır
  ([AI_SYSTEM.md](AI_SYSTEM.md) → asimetrik hata politikası).

## C-4. Matching

**Matching Engine → Feed & Search Service : skorlanmış ve sıralanmış eşleşmeler**
- Girdi: profile_id + invalidation tetikleyicileri (tam liste:
  [MATCHING_ENGINE.md](MATCHING_ENGINE.md) §2.3 — C-1'deki bütün olaylar dahil).
  Çıktı: sıralanmış MatchResult listesi (factor_scores + üç durumlu
  hard_requirement_status + confidence + engine_version + taxonomy_version +
  ranking_inputs).
- Garantiler: **nihai sıralama burada üretilir** (freshness ve kişiselleştirme
  re-ranking'i dahil); Feed & Search Service sıralamayı uygular, üretmez. Her MatchResult
  explanation üretilebilir kanıt taşır (D-005). Sensitive attribute girdisi yoktur
  (iki katmanlı leakage testiyle doğrulanır, D-006). Public sector canonical'ları için
  Match Score üretilmez (D-015).

**Explanation Generator → Application API : açıklama**
- Girdi: MatchResult. Çıktı: MatchExplanation (kullanıcı dilinde).
- Garanti: yalnızca evidence'taki iddialar; skoru değiştirmez.

**Feedback Processor → Matching Engine : kişiselleştirme sinyalleri**
- Girdi: FeedbackSignal akışı. Çıktı: kullanıcı düzeyi ayar parametreleri + (anonim)
  kalibrasyon adayları.
- Garanti: bir kullanıcının feedback'i başka kullanıcıya birebir sinyal olmaz;
  sistem düzeyi değişiklik insan onaysız yayına girmez
  ([MATCHING_ENGINE.md](MATCHING_ENGINE.md) → Feedback Loop).

## C-5. Application API (kullanıcıya dönük yüzey)

**Application API → istemciler : ürün işlemleri**
- Yetenek grupları: auth/hesap (FR-001…003); profil CRUD + verification; preferences;
  feed (sayfalı, explanation'lı); **arama/filtre — iş mantığı Feed & Search Service'e
  delege edilir**; feedback (save/not interested/applied/report); application tracking;
  bildirim opt-out; data rights (export/deletion).
- Garantiler: feed cevabında her ilan kartı source + freshness taşır (FR-601) — çok üyeli
  cluster'da bu bilgi `display_source`'tan (temsilci üye) türer; expired ilan feed/arama
  cevabına girmez; export makine-okunur formattadır ve envanterdeki bütün kullanıcıya
  bağlı sınıfları kapsar (FR-602); deletion akışı bir `DataRightsRequest` kaydıyla
  izlenir ve tanımlanacak SLA'ya bağlıdır (❓ OPEN-05).
- **Search cevabı:** arama sonuçlarında Match Score bandı gösterilir, tam Match
  Explanation gösterilmez (detaya girildiğinde açılır). Public sector sonuçları
  listing-only rozetiyle döner (FR-410).

**Feed & Search Service → Notification & Digest : eşleşme bildirimleri**
- Girdi: hafta boyunca biriken eşik üstü yeni MatchResult'lar. Çıktı: **sabit haftalık**
  e-posta digest (D-016).
- Garantiler: kullanıcı başına rate limit; duplicate tek gösterim (merge geçmişi dikkate
  alınır); expired ve düşük confidence eşleşmeler digest'e girmez; opt-out anında geçerli.
  MVP'de frekans/kanal seçimi yoktur.

## C-6. Admin & Manual Review

**Tanımlı alt sistemler → Manual Review Queue : inceleme talebi (minimal mod, D-014)**
- Girdi: kayıt referansı + `reason_code`. **Kapalı liste** — yalnızca şu altı neden:
  `source_permission`, `low_confidence_extraction` (gate-relevant), `regulated_ambiguity`,
  `sensitive_requirement`, `coverage_anomaly`, `removal_request`. Tetikleyicilerin tek
  sahibi [SCRAPING_SYSTEM.md](SCRAPING_SYSTEM.md) §5.2'dir; başka bir neden eklemek
  D-014'ü değiştirmek demektir (kullanıcı onayı gerekir).
- Çıktı: insan kararı olayları (approve/reject/fix) ilgili sisteme geri akar.
- Garantiler: karar audit-log'ludur (kim, ne zaman, neden). Compliance öncelikli kalemler
  quality kalemleri için bekletilmez. Kapasite aşımında §5.2'deki üç davranış
  (suspend / limited support / recommendation'dan çıkarma) devreye girer — kuyruk sessizce
  büyümez.

## Contract Evrimi Kuralları

1. Contract değişikliği önce bu dosyada tanımlanır, sonra implement edilir.
2. Geriye dönük uyumsuz değişiklik versiyonlanır; tüketiciler geçiş süresi alır.
3. Her contract'ın garantileri test edilebilir olmalı
   ([TEST_STRATEGY.md](../quality/TEST_STRATEGY.md) → contract testleri).
