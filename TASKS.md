# TASKS.md — Task Listesi

> **Purpose:** Küçük, doğrulanabilir ve sıralı task'lar. Her task **Objective /
> Dependency / Acceptance Criteria / Status** alanlarını taşır. "Done" işaretlemeden önce
> [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) şartları da sağlanmalıdır.
> Roadmap seviyesindeki büyük resim için [ROADMAP.md](docs/product/ROADMAP.md).

Status değerleri: `Todo` · `In Progress` · `Blocked` · `Done`

---

## Faz 0 — Design Doğrulama (kod yok)

### T-001 — Open question'ların kullanıcı ile kapatılması
- **Objective:** [CONTEXT.md](CONTEXT.md) → Açık Konular listesindeki 5 kritik sorunun
  cevaplanması (hedef pazar, başlangıç source adayları, business model, taxonomy
  standardı, stack karar tarihi).
- **Dependency:** —
- **Acceptance Criteria:** 5 sorunun cevabı ilgili dokümanlara işlendi; cevaplananlar
  `❓ OPEN` işaretinden çıkarıldı; kararlaşanlar DECISIONS.md'ye eklendi.
- **Status:** Todo

### T-002 — Documentation setinin kullanıcı review'u
- **Objective:** Kullanıcının bütün dokümanları gözden geçirip düzeltme/onay vermesi.
- **Dependency:** —
- **Acceptance Criteria:** Review notları alındı; itiraz edilen bölümler revize edildi;
  `Proposed` durumundaki kararlar (D-004, D-007) `Confirmed` veya revize edildi.
- **Status:** Todo

### T-003 — Launch pazarı için source landscape araştırması
- **Objective:** Seçilen pazarda 10-15 aday job source'un belirlenmesi ve her biri için
  [SOURCE_REGISTRY.md](docs/architecture/SOURCE_REGISTRY.md) template'i ile ön kayıt
  (access method, API availability, policy risk dahil) oluşturulması.
- **Dependency:** T-001
- **Acceptance Criteria:** ≥10 source record dolduruldu; her source için scraping
  permission / policy risk değerlendirmesi yazıldı; MVP için 3-5 source önerildi.
- **Status:** Todo

### T-004 — Taxonomy standardı seçimi (ESCO vs O*NET)
- **Objective:** Hedef pazara göre taxonomy çekirdeğinin seçilmesi ve D-004'ün
  kapatılması.
- **Dependency:** T-001
- **Acceptance Criteria:** Karşılaştırma özeti yazıldı; karar DECISIONS.md'de
  `Confirmed`; [OCCUPATION_TAXONOMY.md](docs/architecture/OCCUPATION_TAXONOMY.md)
  seçilen standarda göre güncellendi.
- **Status:** Todo

### T-005 — MVP occupation seti ve qualification template'leri
- **Objective:** MVP'de birinci sınıf desteklenecek 8-10 mesleğin seçilmesi ve her biri
  için Occupation Profile (qualification template) taslağının yazılması.
- **Dependency:** T-004
- **Acceptance Criteria:** 8-10 Occupation Profile, OCCUPATION_TAXONOMY.md'deki şablonla
  dolduruldu; en az 3'ü white-collar dışı (ör. Nurse, Driver, Technician); regulated
  olanlarda license alanı işaretli.
- **Status:** Todo

### T-006 — Matching golden set'inin tasarlanması
- **Objective:** Matching kalitesini ölçmek için insan-etiketli test seti tasarımı:
  ~50 sentetik Career Profile × ~200 Job Posting üzerinde beklenen match kararları.
- **Dependency:** T-005
- **Acceptance Criteria:** Golden set formatı ve etiketleme kılavuzu yazıldı
  ([TEST_STRATEGY.md](docs/quality/TEST_STRATEGY.md) ile tutarlı); ilk 10 örnek üretildi.
- **Status:** Todo

### T-007 — Wireframe seviyesinde core flow taslakları
- **Objective:** Onboarding, profil oluşturma, job feed ve explanation ekranlarının
  düşük-fidelity taslakları (platform teknolojisi seçilmeden, mobile + web düşünülerek).
- **Dependency:** T-002
- **Acceptance Criteria:** [USER_FLOWS.md](docs/product/USER_FLOWS.md) akışlarındaki her
  adım için ekran taslağı var; explanation ekranı D-005 gereklerini karşılıyor.
- **Status:** Todo

## Faz 1 — Teknik Hazırlık

### T-008 — Compliance çerçevesinin hukuki doğrulaması
- **Objective:** Seçilen pazar için scraping, veri koruma (ör. GDPR/KVKK) ve otomatik
  öneri sistemleri yükümlülüklerinin uzman görüşüyle doğrulanması.
- **Dependency:** T-001
- **Acceptance Criteria:** [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md)
  hukuki görüşle güncellendi; engelleyici bulgular RISK_REGISTER.md'ye işlendi.
- **Status:** Todo

### T-009 — CV parsing yaklaşımı için önerilerin karşılaştırılması
- **Objective:** CV parsing için yaklaşım seçeneklerinin (LLM-based extraction, mevcut
  parser servisleri, hybrid) kalite/maliyet/privacy ekseninde değerlendirilmesi.
- **Dependency:** T-002
- **Acceptance Criteria:** Karşılaştırma [AI_SYSTEM.md](docs/architecture/AI_SYSTEM.md)'e
  eklendi; öneri ADR taslağı hazırlandı (karar stack ADR'si ile birlikte verilebilir).
- **Status:** Todo

### T-010 — Data model'in gözden geçirilip dondurulması
- **Objective:** [DATA_MODEL.md](docs/architecture/DATA_MODEL.md) entity'lerinin T-003 ve
  T-005 çıktılarıyla doğrulanması (gerçek source alanları ve occupation template'leri
  modele oturuyor mu?).
- **Dependency:** T-003, T-005
- **Acceptance Criteria:** En az 3 gerçek ilanın ve 3 personanın verisi modele kayıpsız
  map edildi; gereken model değişiklikleri işlendi.
- **Status:** Todo

### T-011 — Observability ve test altyapısı gereksinimlerinin netleştirilmesi
- **Objective:** [OBSERVABILITY.md](docs/quality/OBSERVABILITY.md) ve
  [TEST_STRATEGY.md](docs/quality/TEST_STRATEGY.md) dokümanlarının MVP kapsamına göre
  "minimum zorunlu" alt kümesinin işaretlenmesi.
- **Dependency:** T-002
- **Acceptance Criteria:** Her iki dokümanda "MVP-required" işaretli net liste var.
- **Status:** Todo

### T-012 — Technology stack kararı (ADR)
- **Objective:** D-001'in kapatılması: language, framework, database(ler), queue,
  hosting yaklaşımının seçilmesi.
- **Dependency:** T-008, T-009, T-010
- **Acceptance Criteria:** Stack ADR'si docs/adr/ altında yazıldı; DECISIONS.md
  güncellendi; kullanıcı onayı alındı.
- **Status:** Blocked (T-008, T-009, T-010 bekliyor)

## Faz 2 — MVP Implementation (stack kararından sonra detaylandırılacak)

> Aşağıdaki task'lar bilinçli olarak kaba tutulmuştur; T-012 kapandıktan sonra alt
> task'lara bölünecektir.

### T-013 — Repository iskeleti ve CI kurulumu
- **Objective:** Kod repository yapısı, CI pipeline, lint/test iskeleti.
- **Dependency:** T-012
- **Acceptance Criteria:** Boş servis iskeletleri CI'da build oluyor; DEFINITION_OF_DONE
  implementation bölümü uygulanabilir durumda.
- **Status:** Blocked

### T-014 — Source Registry + ilk Source Adapter (1 kaynak)
- **Objective:** Source Registry'nin çalışır hali ve tek bir compliant source için
  uçtan uca ingestion (fetch → parse → normalize → store).
- **Dependency:** T-013
- **Acceptance Criteria:** Seçilen source'tan ilanlar normalize edilmiş şekilde
  depolanıyor; provenance kaydediliyor; rate limit ve robots kurallarına uyum loglardan
  doğrulanabiliyor.
- **Status:** Blocked

### T-015 — Normalizer + Duplicate Detector + Expiration Detector
- **Objective:** İkinci ve üçüncü source eklenip cross-source duplicate detection ve
  expiration işleme alınması.
- **Dependency:** T-014
- **Acceptance Criteria:** 3 source'tan gelen aynı ilan tek Canonical Job Posting'e
  bağlanıyor; expired ilanlar feed'den düşüyor; metrikler
  ([METRICS.md](docs/product/METRICS.md) → Scraper Health) yayınlanıyor.
- **Status:** Blocked

### T-016 — Career Profile + CV upload/parsing (MVP kapsamı)
- **Objective:** Manuel profil editörü + CV upload + parsing + kullanıcı doğrulama akışı.
- **Dependency:** T-013
- **Acceptance Criteria:** [USER_FLOWS.md](docs/product/USER_FLOWS.md) → Flow 1 ve 2
  uçtan uca çalışıyor; parse sonucu kullanıcı onayından geçmeden matching'e girmiyor.
- **Status:** Blocked

### T-017 — Matching Engine v0 + Explainability
- **Objective:** Hard requirement kontrolü + faktör bazlı scoring + Match Explanation
  üretimi (MVP faktör seti: [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md)).
- **Dependency:** T-015, T-016, T-006
- **Acceptance Criteria:** Golden set üzerinde hedef metriklere ulaşıldı
  ([METRICS.md](docs/product/METRICS.md) → Matching Quality); her önerinin explanation'ı
  D-005 şartlarını sağlıyor; sensitive attribute testi geçiyor.
- **Status:** Blocked

### T-018 — Personalized Job Feed + feedback (save / not interested / applied)
- **Objective:** Kullanıcının sıralı feed görmesi, feedback vermesi ve feedback'in
  sıralamaya etkimesi.
- **Dependency:** T-017
- **Acceptance Criteria:** Feed explanation'larla birlikte geliyor; "not interested"
  benzer ilanların sıralamasını düşürüyor; applied/saved listeleri çalışıyor.
- **Status:** Blocked

### T-019 — Notification + digest (MVP: e-posta digest)
- **Objective:** Yeni eşleşen ilanlar için günlük/haftalık digest.
- **Dependency:** T-018
- **Acceptance Criteria:** Kullanıcı frekans seçebiliyor; digest yalnızca fresh ve
  duplicate-olmayan ilanlar içeriyor; opt-out çalışıyor.
- **Status:** Blocked

### T-020 — MVP kapanış: data export/deletion + source transparency + rapor akışı
- **Objective:** Kullanıcı veri export/deletion hakları, ilan kaynağı gösterimi ve
  "report incorrect/expired job" akışının tamamlanması.
- **Dependency:** T-018
- **Acceptance Criteria:** Export ve deletion uçtan uca çalışıyor (deletion SLA:
  [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md));
  her ilan kartında source ve freshness görünüyor; report akışı Manual Review Queue'ya
  düşüyor.
- **Status:** Blocked
