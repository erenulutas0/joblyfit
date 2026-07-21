# REQUIREMENTS.md — Functional ve Non-Functional Requirements

> **Purpose:** Sistem gereksinimlerinin sahibi. Scope ataması (hangi requirement hangi
> sürümde) [PRD.md](PRD.md); davranışın *nasıl* sağlanacağı architecture dokümanlarında.
> Format: her requirement test edilebilir bir cümledir. `MUST` = zorunlu, `SHOULD` =
> güçlü beklenti, `MAY` = opsiyonel.
>
> **MoSCoW ↔ Scope kuralı (PRD ile ortak):** MVP feature'ına karşılık gelen her FR
> **MUST** olmalıdır. Bir FR `SHOULD` ise dayandığı feature MVP'de olamaz. Her FR'nin
> scope katmanı aşağıda `[MVP]` / `[V1]` / `[Future]` etiketiyle gösterilir; çelişkide
> [PRD.md](PRD.md) otoritedir.

## Functional Requirements

### FR-0xx — Hesap Yaşam Döngüsü

- **FR-001 `[MVP]`:** Kullanıcı hesap oluşturabilmeli ve giriş yapabilmeli (MUST).
- **FR-002 `[MVP]`:** Kullanıcı hesabını deaktive edebilmeli; deaktif hesap matching'e
  girmemeli ve hiçbir bildirim almamalı (MUST).
- **FR-003 `[V1]`:** Kullanıcı hesabına erişimini kurtarabilmeli (SHOULD).

### FR-1xx — Profile

- **FR-101 `[MVP]`:** Kullanıcı CV dosyası yükleyebilmeli ve sistem bundan Career Profile
  alanlarını çıkarmalı (MUST). Desteklenen format ve dil kapsamı
  [AI_SYSTEM.md](../architecture/AI_SYSTEM.md) §1.1'deki kapsama matrisinde tanımlıdır;
  MVP kapsamı **PDF + Türkçe, OCR'sız**. Kapsam dışı dosya reddedilir ve kullanıcı manuel
  profil yoluna (FR-102) yönlendirilir.
- **FR-102 `[MVP]`:** Kullanıcı CV olmadan, occupation'a özgü soru setiyle manuel Career
  Profile oluşturabilmeli (MUST).
- **FR-103 `[MVP]`:** Parse edilen her alan kullanıcıya gösterilmeli; kullanıcı onaylayana
  veya düzeltene kadar alan `unverified` statüsünde kalmalı (MUST). Manuel girilen alanlar
  da aynı statü modelini kullanır: kullanıcının kendi girdiği alan `user_asserted`
  sayılır; gate-relevant alanlar için FR-107 geçerlidir.
- **FR-104 `[MVP]`:** Career Profile şu alan gruplarını desteklemeli: education, work
  experience, skills, certifications, professional licenses, languages, portfolio,
  preferred location, salary expectation, work type, shift preference ve
  occupation-specific qualifications (MUST).
- **FR-105 `[V1]`:** Sistem Profile Completeness Score hesaplayıp eksik alanları occupation
  bağlamında önermeli (SHOULD). *MVP'den V1'e taşındı (D-008); MVP'de eksik bilgi
  kullanıcıya `unknown` requirement açıklamasıyla bildirilir (FR-411).*
- **FR-106 `[MVP]`:** Kullanıcı preferences'ını (location, salary, work type, shift)
  istediği an değiştirebilmeli; değişiklik feed'e yansımalı (MUST).
- **FR-107 `[MVP]`:** **Gate-relevant alanlar** — professional license, driving license ve
  kategorisi, work permit, yasal zorunlu sertifika, country-specific professional
  authorization ve diğer regulated eligibility belgeleri — kullanıcı tarafından
  doğrulanmadan hiçbir hard requirement'ı `met` saymamalı; doğrulanmamış hali
  `unknown / verification required` üretmeli (MUST — D-012). Bu alanlar için doğrulama
  onboarding'de zorunlu adımdır; diğer alanlar atlanabilir.

### FR-2xx — Ingestion

- **FR-201 `[MVP]`:** Sistem birden çok Job Source türünden (job board, company career page,
  ATS page, recruitment agency, government portal, university portal, sector-specific)
  ilan toplayabilmeli (MUST).
- **FR-202 `[MVP]`:** Her source, Source Registry'de bir Source Record ile tanımlı olmalı;
  registry'de kayıtsız source'tan ingestion yapılmamalı (MUST).
- **FR-203 `[MVP]`:** Ingestion yalnızca API'ye bağımlı olmamalı; feed ve compliant scraping da
  desteklenmeli. Hiçbir adapter tek bir platformun/HTML yapısının varlığına sistemik
  bağımlılık yaratmamalı (MUST).
- **FR-204 `[MVP]`:** Sistem robots kurallarına, source Terms'e ve tanımlı rate limit'lere uymalı;
  login wall/CAPTCHA/bot-detection bypass **yapmamalı** (MUST — D-002).
- **FR-205 `[MVP]`:** Toplanan ilanlar tek bir normalize şemaya (Job Posting) dönüştürülmeli (MUST).
- **FR-206 `[MVP]`:** Aynı gerçek ilanın farklı source kopyaları tespit edilip bir Canonical Job
  Posting altında birleştirilmeli (MUST).
- **FR-207 `[MVP]`:** Expired ilanlar tespit edilip kullanıcıya açık yüzeylerden kaldırılmalı (MUST).
- **FR-208 `[MVP]`:** Her Job Posting, provenance bilgisiyle (source, URL, fetch zamanı,
  parser version) saklanmalı (MUST).
- **FR-209 `[MVP]`:** Her Job Posting için Freshness Score hesaplanmalı ve kullanıcıya ilan
  yaşı/güncelliği gösterilmeli (MUST).
- **FR-210 `[MVP]`:** Bir source'un arızası diğer source'ların ingestion'ını durdurmamalı
  (Source Isolation) (MUST).
- **FR-211 `[MVP]`:** Manual Review Queue **minimal modda** çalışmalı: yalnızca
  [SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md) §5.2'deki altı tetikleyici
  kuyruğa girmeli; kapasite aşımında tanımlı otomatik davranış (source suspend / occupation
  limited support / recommendation'dan çıkarma) devreye girmeli (MUST — D-014).
  Diğer kayıtlar kuyruğa **girmez**, otomatik davranışa bağlanır.

### FR-3xx — Taxonomy & Understanding

- **FR-301 `[MVP]`:** Sistem merkezi bir Occupation Taxonomy barındırmalı; her Career
  Profile ve Job Posting en az bir Occupation'a map edilmeli. Map edilemeyenler `unmapped`
  işaretiyle **limited tier** davranışı almalı — listelenir, otomatik recommendation
  üretilmez (MUST — D-008, D-014).
- **FR-302 `[MVP]`:** Taxonomy, occupation-specific qualification template'lerini (Occupation
  Profile) desteklemeli (MUST).
- **FR-303 `[MVP]`:** İlan metninden Required ve Preferred Qualification'lar ayrıştırılarak
  çıkarılmalı; belirsiz durumlar confidence ile işaretlenmeli ve `hard` sınıflaması yüksek
  confidence şartına bağlı olmalı (MUST).
- **FR-304 `[MVP]`:** Taxonomy'ye yeni occupation ve qualification eklenebilmeli (tanımlı süreçle:
  [OCCUPATION_TAXONOMY.md](../architecture/OCCUPATION_TAXONOMY.md)) (MUST).

### FR-4xx — Matching & Explanation

- **FR-401 `[MVP]`:** Matching, [MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md)
  faktör tablosunda **MVP olarak işaretli** faktörleri ayrı ayrı değerlendiren hybrid
  yaklaşım kullanmalı; yalnızca semantic similarity'ye dayanmamalı (MUST — D-003, D-017).
  Semantic katkı yalnızca sınırlı reranking sinyalidir (üst sınır ve kısıtlar: D-017).
- **FR-402 `[MVP]`:** Her requirement değerlendirmesi **üç durumlu** olmalı: `met`,
  `unmet`, `unknown` (MUST — D-011). Hard Requirement `unmet` ise ilan ya elenir ya da
  "karşılanmayan hard requirement" etiketiyle açıkça işaretlenir; hiçbir zaman sessizce
  yüksek skor almaz. **Profilde bilgi bulunmaması `unmet` değil `unknown` üretir**;
  `unknown` hard requirement eleme sebebi değildir, açıklama sebebidir (FR-411).
- **FR-403 `[MVP]`:** Sensitive attribute'lar Match Score hesabına girmemeli (MUST —
  D-006). Health information MVP matching pipeline'ına hiç alınmaz (D-013).
- **FR-404 `[MVP]`:** Her recommendation bir Match Explanation içermeli: uygunluk
  gerekçesi, karşılanan requirements, **karşılanmayan requirements**, **değerlendirilemeyen
  (`unknown`) requirements**, başvurmaya değerlik değerlendirmesi, Match Confidence,
  freshness ve source (MUST — D-005).
  *MVP-minimum içerik budur.* CV iyileştirme önerileri ve eksik qualification'ı giderme
  yol gösterimi F-20 kapsamındadır `[V1]`.
- **FR-405 `[MVP]`:** Match Score kullanıcıya kesinlik/garanti ifade etmeyen bir çerçeveyle
  sunulmalı; işe alınma olasılığı olarak sunulmamalı (MUST).
- **FR-406 `[MVP]`:** Kullanıcı feedback'i (saved, not interested, applied) sıralamayı
  etkilemeli; "not interested" benzer önerileri azaltmalı (MUST — etki mekanizması MVP'de
  kural bazlı). Raporlanan (`reported`) ilan feed'den düşer; benzerlerine etkisi V1
  konusudur.
- **FR-407 `[V1]`:** Sistem transferable skill'ler üzerinden yakın occupation ve Career
  Transition önerileri sunabilmeli (SHOULD).
- **FR-408 `[MVP]`:** Regulated profession'da kullanıcının gerekli Professional License'ı
  yoksa **veya doğrulanmamışsa**, bu ilanlara yönlendirme yapılırken durum açıkça
  belirtilmeli; "uygun" izlenimi verilmemeli (MUST — D-012). Doğrulanmamış license
  `met` sayılamaz.
- **FR-409 `[V1]`:** Kullanıcı matching faktör önceliklerini ayarlayabilmeli (SHOULD,
  F-18). Gate faktörleri kullanıcı tarafından etkisizleştirilemez.
- **FR-410 `[MVP]`:** Public sector ilanları **listing-only / guidance mode**'da
  sunulmalı: listelenir, normalize edilir, temel eligibility/filter sinyalleri gösterilir
  ve orijinal source'a yönlendirilir; **genel Match Score veya "uygunsun" sonucu
  üretilmez** (MUST — D-015).
- **FR-411 `[MVP]`:** Bir requirement `unknown` ise explanation kullanıcıya (a) profilinde
  hangi bilginin eksik olduğunu, (b) bu bilgiyi ekleyerek recommendation'ın nasıl
  netleşeceğini ve (c) neden kesin değerlendirme yapılamadığını açıklamalı (MUST — D-011).
- **FR-412 `[MVP]`:** Bir ilanda age, health, military status veya benzeri özel bir şart
  tespit edilirse sistem kullanıcıyı otomatik olarak uygun/uygunsuz ilan etmemeli;
  şartı bilgilendirme olarak göstermeli ve kullanıcıyı **orijinal ilanı kontrol etmeye**
  yönlendirmeli. Şartın legal/policy durumu belirsizse kayıt Manual Review'a düşmeli.
  Bu değerlendirme için sensitive user data toplanmamalı (MUST — D-013).

### FR-5xx — Engagement

- **FR-501 `[MVP]`:** Kullanıcı, Feed & Search Service tarafından üretilen sıralı kişisel
  Job Feed'i görmeli (MUST). Sıralama tabanı Match Score'dur; freshness sıralamaya
  Match Score sonrası bir re-ranking etkeni olarak katılır
  ([MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md) → Final Ranking).
- **FR-502 `[MVP]`:** Keyword + location ile arama/filtreleme yapılabilmeli (MUST).
  Arama sorumluluğunun sahibi **Feed & Search Service**'tir
  ([ARCHITECTURE.md](../architecture/ARCHITECTURE.md)). Arama sonuçlarında Match Score
  bandı gösterilir, tam Match Explanation gösterilmez (detaya girildiğinde açılır).
  Advanced filters (sektör, seniority, salary, shift, license) `[V1]` (SHOULD).
- **FR-503 `[MVP]`:** Kullanıcı ilan kaydedebilmeli, "not interested" diyebilmeli,
  "applied" işaretleyebilmeli (MUST).
- **FR-504 `[V1]`:** Uygulama durumu takibi (applied → interview → offer → sonuç)
  yapılabilmeli (SHOULD).
- **FR-505 `[MVP]`:** Yeni eşleşen ilanlar için **sabit haftalık e-posta digest**
  sunulmalı ve kullanıcı tek dokunuşla opt-out edebilmeli (MUST — D-016).
  MVP'de anlık bildirim, frekans seçimi, kanal seçimi ve eşik ayarı **yoktur**; bunlar
  F-15 kapsamında `[V1]`'dedir.
- **FR-506 `[MVP]`:** Kullanıcı hatalı/expired ilanı raporlayabilmeli; sonuç kendisine
  bildirilmeli (MUST). MVP'de rapor basit bir formla alınır ve minimal Manual Review
  akışına düşer (D-014).

### FR-6xx — Trust & Data Rights

- **FR-601 `[MVP]`:** Her ilanın orijinal source'u ve ilan yaşı kullanıcıya görünmeli;
  başvuru orijinal source'a yönlendirilmeli (MUST).
- **FR-602 `[MVP]`:** Kullanıcı bütün verisini makine-okunur formatta export edebilmeli
  (MUST). Export kapsamı
  [PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md) → veri
  envanterindeki bütün kullanıcıya bağlı sınıfları içerir.
- **FR-603 `[MVP]`:** Kullanıcı hesabını ve verisini sildirebilmeli; silme, tanımlanacak
  SLA içinde ve envanterdeki bütün kullanıcıya bağlı sınıfları kapsayacak şekilde kalıcı
  olmalı (MUST). ❓ OPEN-05: SLA ve geri alma penceresi değerleri hukuki doğrulamayla
  (T-008) kesinleşecek; o zamana kadar dokümanlardaki değerler **öneridir**.
- **FR-604 `[V1]`:** Çok dilli ilan ve CV desteği sağlanmalı (SHOULD, F-22). MVP dil
  politikası: hedef dil Türkçe; hedef dil dışı ilanlar ingest edilip dil işaretlenir ancak
  requirement extraction yapılmaz ve first-class matching'e girmez.

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
- **NFR-504:** Arayüz erişilebilirlik standartlarını (ör. WCAG düzeyi — ❓ OPEN-14: hedef
  düzey) gözetmeli.

### NFR-6xx — Observability & İşletim

- **NFR-601:** Scraper health, data quality ve matching quality metrikleri sürekli
  toplanmalı ([OBSERVABILITY.md](../quality/OBSERVABILITY.md)).
- **NFR-602:** Kritik arıza senaryoları ([ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
  → Failure Scenarios) alert'lere ve [RUNBOOK.md](../operations/RUNBOOK.md) prosedürlerine bağlı olmalı.
