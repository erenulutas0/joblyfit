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

**Ingestion → Matching : posting olayları**
- Olaylar: `posting_created`, `posting_updated` (content değişti), `posting_expired`.
- Garanti: expired olayı yayıldıktan sonra o canonical feed hesaplarına girmez (NFR-102).

## C-2. Taxonomy Servisi

**Taxonomy → (Extraction, Matching, UI) : kavram sorguları**
- Yetenekler: title/metin → occupation adayları (+confidence); qualification arama/çözme;
  Occupation Profile getirme; transition komşuları; çok dilli label.
- Garanti: cevaplar taxonomy versiyon kimliği taşır; `deprecated` kavramlar yönlendirme
  ile döner (kırık referans olmaz).

## C-3. Understanding

**CV Parser → Profile Store : profil taslağı**
- Girdi: CV dosyası (güvenlik kontrolünden geçmiş). Çıktı: CareerProfile taslak alanları
  (her biri value+confidence+source_span) + vault'a ayrılmış sensitive kayıtlar.
- Garanti: hiçbir alan `verified` olarak dönmez (yalnızca kullanıcı eylemi verified
  yapar, FR-103); sensitive alanlar profil taslağında bulunmaz (D-006).

**Requirement Extractor → Job Posting Store : requirement seti**
- Girdi: normalize ilan metni + structured data. Çıktı: requirements[]
  (kind: hard/required/preferred, kavram bağlantısı, confidence).
- Garanti: hard sınıflaması yüksek confidence şartına bağlıdır
  ([AI_SYSTEM.md](AI_SYSTEM.md) → asimetrik hata politikası).

## C-4. Matching

**Matching Engine → Feed Builder : skorlanmış eşleşmeler**
- Girdi: profile_id (+ tetik: profil değişti / yeni posting'ler). Çıktı: MatchResult
  listesi (factor_scores + hard_requirement_status + confidence + engine_version).
- Garanti: her MatchResult explanation üretilebilir kanıt taşır (D-005); sensitive
  attribute girdisi yoktur (leakage testiyle doğrulanır, D-006).

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
- Yetenek grupları: auth/hesap; profil CRUD + verification; preferences; feed (sayfalı,
  explanation'lı); arama/filtre; feedback (save/not interested/applied/report);
  application tracking; bildirim ayarları; data rights (export/deletion).
- Garantiler: feed cevabında her ilan kartı source + freshness taşır (FR-601); expired
  ilan feed/arama cevabına girmez; export makine-okunur formattadır (FR-602); deletion
  akışı [PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md)
  SLA'sına bağlıdır.

**Feed Builder → Notification & Digest : eşleşme bildirimleri**
- Girdi: eşik üstü yeni MatchResult'lar. Çıktı: kullanıcı tercihine göre paketlenmiş
  bildirim/digest.
- Garanti: kullanıcı başına rate limit; duplicate tek gösterim; expired digest'e girmez;
  opt-out anında geçerli.

## C-6. Admin & Manual Review

**Herhangi bir alt sistem → Manual Review Queue : inceleme talebi**
- Girdi: kayıt referansı + neden (policy değerlendirme / kalite eşik altı / unmapped
  occupation / kullanıcı raporu / şüpheli içerik). Çıktı: insan kararı olayları
  (approve/reject/fix) ilgili sisteme geri akar.
- Garanti: karar audit-log'ludur (kim, ne zaman, neden).

## Contract Evrimi Kuralları

1. Contract değişikliği önce bu dosyada tanımlanır, sonra implement edilir.
2. Geriye dönük uyumsuz değişiklik versiyonlanır; tüketiciler geçiş süresi alır.
3. Her contract'ın garantileri test edilebilir olmalı
   ([TEST_STRATEGY.md](../quality/TEST_STRATEGY.md) → contract testleri).
