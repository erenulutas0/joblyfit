# REQUIREMENTS.md — Functional ve Non-Functional Requirements

> **Purpose:** Sistem gereksinimlerinin sahibi. Scope ataması (hangi requirement hangi
> sürümde) [PRD.md](PRD.md); davranışın *nasıl* sağlanacağı architecture dokümanlarında.
> Format: her requirement test edilebilir bir cümledir. `MUST` = zorunlu, `SHOULD` =
> güçlü beklenti, `MAY` = opsiyonel.

## Functional Requirements

### FR-1xx — Profile

- **FR-101:** Kullanıcı CV dosyası yükleyebilmeli (yaygın belge formatları); sistem
  bundan Career Profile alanlarını çıkarmalı (MUST).
- **FR-102:** Kullanıcı CV olmadan, occupation'a özgü soru setiyle manuel Career Profile
  oluşturabilmeli (MUST).
- **FR-103:** Parse edilen her alan kullanıcıya gösterilmeli; kullanıcı onaylayana veya
  düzeltene kadar alan "unverified" statüsünde kalmalı (MUST).
- **FR-104:** Career Profile şu alan gruplarını desteklemeli: education, work experience,
  skills, certifications, professional licenses, languages, portfolio, preferred
  location, salary expectation, work type, shift preference ve occupation-specific
  qualifications (MUST).
- **FR-105:** Sistem Profile Completeness Score hesaplayıp eksik alanları occupation
  bağlamında önermeli (SHOULD).
- **FR-106:** Kullanıcı preferences'ını (location, salary, work type, shift) istediği an
  değiştirebilmeli; değişiklik feed'e yansımalı (MUST).

### FR-2xx — Ingestion

- **FR-201:** Sistem birden çok Job Source türünden (job board, company career page,
  ATS page, recruitment agency, government portal, university portal, sector-specific)
  ilan toplayabilmeli (MUST).
- **FR-202:** Her source, Source Registry'de bir Source Record ile tanımlı olmalı;
  registry'de kayıtsız source'tan ingestion yapılmamalı (MUST).
- **FR-203:** Ingestion yalnızca API'ye bağımlı olmamalı; feed ve compliant scraping da
  desteklenmeli. Hiçbir adapter tek bir platformun/HTML yapısının varlığına sistemik
  bağımlılık yaratmamalı (MUST).
- **FR-204:** Sistem robots kurallarına, source Terms'e ve tanımlı rate limit'lere uymalı;
  login wall/CAPTCHA/bot-detection bypass **yapmamalı** (MUST — D-002).
- **FR-205:** Toplanan ilanlar tek bir normalize şemaya (Job Posting) dönüştürülmeli (MUST).
- **FR-206:** Aynı gerçek ilanın farklı source kopyaları tespit edilip bir Canonical Job
  Posting altında birleştirilmeli (MUST).
- **FR-207:** Expired ilanlar tespit edilip kullanıcıya açık yüzeylerden kaldırılmalı (MUST).
- **FR-208:** Her Job Posting, provenance bilgisiyle (source, URL, fetch zamanı,
  parser version) saklanmalı (MUST).
- **FR-209:** Her Job Posting için Freshness Score hesaplanmalı ve kullanıcıya ilan
  yaşı/güncelliği gösterilmeli (MUST).
- **FR-210:** Bir source'un arızası diğer source'ların ingestion'ını durdurmamalı
  (Source Isolation) (MUST).
- **FR-211:** Otomatik işlenemeyen kayıtlar ve kullanıcı raporları Manual Review
  Queue'ya düşmeli (SHOULD).

### FR-3xx — Taxonomy & Understanding

- **FR-301:** Sistem merkezi bir Occupation Taxonomy barındırmalı; her Career Profile ve
  Job Posting en az bir Occupation'a map edilmeli (map edilemeyenler işaretlenmeli) (MUST).
- **FR-302:** Taxonomy, occupation-specific qualification template'lerini (Occupation
  Profile) desteklemeli (MUST).
- **FR-303:** İlan metninden Required ve Preferred Qualification'lar ayrıştırılarak
  çıkarılmalı; belirsiz durumlar confidence ile işaretlenmeli (MUST).
- **FR-304:** Taxonomy'ye yeni occupation ve qualification eklenebilmeli (tanımlı süreçle:
  [OCCUPATION_TAXONOMY.md](../architecture/OCCUPATION_TAXONOMY.md)) (MUST).

### FR-4xx — Matching & Explanation

- **FR-401:** Matching, [MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md) içinde
  listelenen faktörleri **ayrı ayrı** değerlendiren hybrid yaklaşım kullanmalı; yalnızca
  semantic similarity'ye dayanmamalı (MUST — D-003).
- **FR-402:** Hard Requirement karşılanmıyorsa ilan ya elenir ya da "eksik hard
  requirement" etiketiyle açıkça işaretlenir; hiçbir zaman sessizce yüksek skor almaz (MUST).
- **FR-403:** Sensitive attribute'lar Match Score hesabına girmemeli (MUST — D-006).
- **FR-404:** Her recommendation bir Match Explanation içermeli: uygunluk gerekçesi,
  karşılanan requirements, eksik requirements, başvurmaya değerlik değerlendirmesi,
  CV iyileştirme önerileri, eksik qualification/certification bilgisi, Match Confidence,
  freshness ve source (MUST — D-005).
- **FR-405:** Match Score kullanıcıya kesinlik/garanti ifade etmeyen bir çerçeveyle
  sunulmalı (MUST).
- **FR-406:** Kullanıcı feedback'i (saved, not interested, applied, report) sıralamayı
  etkilemeli; "not interested" benzer önerileri azaltmalı (MUST — etki mekanizması MVP'de
  kural bazlı olabilir).
- **FR-407:** Sistem transferable skill'ler üzerinden yakın occupation ve Career
  Transition önerileri sunabilmeli (SHOULD — V1).
- **FR-408:** Regulated profession'da kullanıcının gerekli Professional License'ı yoksa
  bu ilanlara yönlendirme yapılırken eksik açıkça belirtilmeli; "uygun" izlenimi
  verilmemeli (MUST).
- **FR-409:** Kullanıcı matching faktör önceliklerini ayarlayabilmeli (SHOULD — V1, F-18).

### FR-5xx — Engagement

- **FR-501:** Kullanıcı Match Score'a göre sıralı, kişisel Job Feed görmeli (MUST).
- **FR-502:** Keyword + location + work type ile arama/filtreleme yapılabilmeli (MUST);
  advanced filters (sektör, seniority, salary, shift, license) V1'de (SHOULD).
- **FR-503:** Kullanıcı ilan kaydedebilmeli, "not interested" diyebilmeli, "applied"
  işaretleyebilmeli (MUST).
- **FR-504:** Uygulama durumu takibi (applied → interview → offer → sonuç) yapılabilmeli
  (SHOULD — V1).
- **FR-505:** Yeni eşleşen ilanlar için bildirim ve günlük/haftalık digest sunulmalı;
  kullanıcı frekans seçebilmeli ve opt-out edebilmeli (MUST).
- **FR-506:** Kullanıcı hatalı/expired ilanı raporlayabilmeli; sonuç kendisine
  bildirilmeli (MUST).

### FR-6xx — Trust & Data Rights

- **FR-601:** Her ilanın orijinal source'u ve ilan yaşı kullanıcıya görünmeli; başvuru
  orijinal source'a yönlendirilmeli (MUST).
- **FR-602:** Kullanıcı bütün verisini makine-okunur formatta export edebilmeli (MUST).
- **FR-603:** Kullanıcı hesabını ve verisini sildirebilmeli; silme tanımlı SLA içinde
  kalıcı olmalı ([PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md)) (MUST).
- **FR-604:** Çok dilli ilan ve CV desteği sağlanmalı (SHOULD — V1, F-22).

## Non-Functional Requirements

> Sayısal hedefler stack ve pazar seçiminden bağımsız, ürün beklentisi seviyesinde
> verilmiştir; implementation öncesinde revize edilebilir. ❓ OPEN işaretli değerler
> kullanıcı onayı bekler.

### NFR-1xx — Kalite & Doğruluk

- **NFR-101 (Freshness):** Aktif bir source'taki yeni ilan, source'un crawl frekansı
  içinde (hedef: ≤24 saat) platformda görünmeli.
- **NFR-102 (Expiration):** Expired olduğu tespit edilebilen ilan, tespitten sonra
  ≤24 saat içinde feed'lerden kalkmalı.
- **NFR-103 (Duplicate):** Kullanıcı feed'inde aynı gerçek ilanın birden çok kopyası
  görünmemeli (hedef duplicate leakage: [METRICS.md](METRICS.md)).
- **NFR-104 (Extraction kalitesi):** Requirement extraction ve CV parsing kalitesi golden
  set ile sürekli ölçülmeli; hedefler METRICS.md'de.

### NFR-2xx — Performans & Ölçek

- **NFR-201:** Job Feed ilk yükleme, olağan koşullarda birkaç saniye içinde gelmeli
  (mobile network dahil düşünülür).
- **NFR-202:** Profil değişikliği sonrası feed'in yeniden hesaplanması dakikalar
  mertebesinde tamamlanmalı (real-time şart değil).
- **NFR-203:** Mimari, source sayısının 5'ten yüzlere, ilan hacminin milyonlara
  büyümesine yeniden tasarım gerektirmeden izin vermeli (yatay ölçeklenebilir pipeline).

### NFR-3xx — Güvenilirlik

- **NFR-301:** Tek source arızası (Source Isolation) veya matching alt sisteminin
  arızası, mevcut feed'in sunulmasını engellememeli (son hesaplanan feed servis edilir —
  graceful degradation).
- **NFR-302:** Ingestion pipeline'ı retry + backoff + failure queue ile geçici hataları
  kendisi absorbe etmeli ([SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md)).

### NFR-4xx — Güvenlik & Privacy

- **NFR-401:** PII, [PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md)
  içindeki data lifecycle ve minimization kurallarına göre işlenmeli.
- **NFR-402:** CV dosyaları ve Career Profile verisi at-rest ve in-transit encrypted
  saklanmalı; erişim least-privilege olmalı.
- **NFR-403:** Sensitive attribute izolasyonu (D-006) veri katmanında da uygulanmalı:
  matching'e giden veri yolunda bu alanlar bulunmamalı.

### NFR-5xx — Erişilebilirlik & Kullanılabilirlik

- **NFR-501:** Core flow'lar (onboarding, profil, feed, başvuru işaretleme) mobile
  ekranda eksiksiz tamamlanabilmeli.
- **NFR-502:** CV'siz onboarding ≤5 dakikada tamamlanabilmeli (P2 Hasan kriteri).
- **NFR-503:** Explanation'lar teknik jargonsuz, hedef pazarın dilinde ve sade yazılmalı.
- **NFR-504:** Arayüz erişilebilirlik standartlarını (ör. WCAG düzeyi — ❓ OPEN: hedef
  düzey) gözetmeli.

### NFR-6xx — Observability & İşletim

- **NFR-601:** Scraper health, data quality ve matching quality metrikleri sürekli
  toplanmalı ([OBSERVABILITY.md](../quality/OBSERVABILITY.md)).
- **NFR-602:** Kritik arıza senaryoları ([ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
  → Failure Scenarios) alert'lere ve [RUNBOOK.md](../operations/RUNBOOK.md) prosedürlerine bağlı olmalı.
