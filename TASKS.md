# TASKS.md — Task Listesi

> **Purpose:** Küçük, doğrulanabilir ve sıralı task'lar. Her task **Objective /
> Dependency / Acceptance Criteria / Status** alanlarını taşır. "Done" işaretlemeden önce
> [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) şartları da sağlanmalıdır.
> Roadmap seviyesindeki büyük resim için [ROADMAP.md](docs/product/ROADMAP.md).

## Status Semantiği

| Status | Anlamı |
|---|---|
| `Todo` | Henüz başlanmadı. **Dependency'si tamamlanmamış task da Todo'dur** — sıra Dependency alanından okunur, statüde tekrarlanmaz. |
| `In Progress` | Üzerinde aktif çalışılıyor (aynı anda birden fazla olmamalı). |
| `Blocked` | **Yalnızca dış/harici engel** için: kullanıcı kararı, üçüncü taraf yanıtı, hukuki görüş beklemesi. Task içi dependency `Blocked` sayılmaz. |
| `Done` | Acceptance criteria + DEFINITION_OF_DONE karşılandı. |

## Arşiv Kuralı

Bir faz veya milestone kapandığında o fazın `Done` task'ları bu dosyadan
`archive/TASKS-<faz>.md` dosyasına taşınır; aktif dosyada yalnızca güncel ve gelecek faz
kalır. Özet satırları [PROGRESS.md](PROGRESS.md) içinde zaten durduğu için bilgi kaybı
olmaz. Bu kural, dosyanın Faz 2 bölünmesinden sonra yönetilemez hale gelmesini önler.

---

## Faz 1 — Doğrulama & Hazırlık

> ROADMAP ile aynı faz numaralandırması kullanılır: Faz 0 = documentation (tamamlandı),
> Faz 1 = doğrulama & hazırlık, Faz 2 = MVP build, Faz 3 = private beta, Faz 4 = V1.

### 1a — Karar Doğrulama ve Kapsam

#### T-001 — Open question'ların kullanıcı ile kapatılması
- **Objective:** [CONTEXT.md](CONTEXT.md) → Open Question Index'teki **M1-blocker**
  işaretli soruların cevaplanması (OPEN-01…OPEN-06, OPEN-09).
- **Dependency:** —
- **Acceptance Criteria:** M1-blocker sorularının tamamı ya cevaplandı ya da gerekçesiyle
  `pre-build`'e düşürüldü; cevaplananlar sahibi dosyada `❓ OPEN` işaretinden çıkarıldı ve
  index'te `Kapandı (D-0XX)` olarak işaretlendi; karar gerektirenler DECISIONS.md'ye eklendi.
- **Status:** In Progress *(K-1…K-10 kararlarıyla önemli bölümü kapandı: D-008…D-017)*

#### T-002 — Documentation setinin kullanıcı review'u
- **Objective:** Kullanıcının doküman setini gözden geçirip düzeltme/onay vermesi.
- **Dependency:** —
- **Acceptance Criteria:** Review notları alındı; itiraz edilen bölümler revize edildi;
  `Proposed` durumundaki kararlar `Confirmed` veya revize edildi.
- **Status:** Done *(2026-07-21 audit + K-1…K-10 onayları; D-003/D-004/D-007 statüleri
  netleştirildi)*

#### T-003 — Türkiye source landscape araştırması
- **Objective:** Türkiye'de MVP cluster'larını (Logistics & Operations, Office &
  Commercial, Healthcare) taşıyan 10-15 aday job source'un belirlenmesi ve her biri için
  [SOURCE_REGISTRY.md](docs/architecture/SOURCE_REGISTRY.md) template'i ile ön kayıt.
- **Dependency:** T-001
- **Acceptance Criteria:** ≥10 source record dolduruldu; her source için scraping
  permission / policy risk değerlendirmesi yazıldı; **her MVP cluster'ı için asgari ilan
  hacmi doğrulandı**; MVP için 2-3 source önerildi; her aday için tahmini onboarding
  eforu ve aylık bakım eforu yazıldı.
- **Status:** **Done** *(2026-07-21)*
- **Sonuç:** 15 aday incelendi, kanıtlar
  [TURKEY_SOURCE_LANDSCAPE.md](docs/research/TURKEY_SOURCE_LANDSCAPE.md) içinde; registry
  kayıtları [SOURCE_REGISTRY.md](docs/architecture/SOURCE_REGISTRY.md) §5'te.
  **Tavsiye: CONDITIONAL GO.** Wave 1 = isinolsun.com (conditional), Wave 2 = İŞKUR
  e-Şube + Kamu İlan (SBB). Hiçbir kaynak koşulsuz `allowed` değil; crawl başlatılması
  ya yazılı izne ya da T-008'in OPEN-09 rubriğine bağlı.
  **Acceptance sapması:** "cluster başına asgari ilan hacmi doğrulandı" kriteri
  **niceliksel olarak karşılanamadı** — hacim tahminleri niteliksel kaldı; nicel ölçüm
  T-021'in örneklem denetimine devredildi (plan: araştırma dosyası §9). Bu sapma
  bilinçlidir ve T-021 acceptance'ında kapanır.

#### T-004 — Taxonomy standardı seçimi (ESCO vs O*NET)
- **Objective:** Türkiye pazarına göre taxonomy çekirdeğinin seçilmesi ve D-004'ün
  kapatılması (OPEN-02).
- **Dependency:** T-001
- **Acceptance Criteria:** Karşılaştırma özeti yazıldı ve
  [OCCUPATION_TAXONOMY.md](docs/architecture/OCCUPATION_TAXONOMY.md) §2.1'deki
  **özellik→standart bağımlılık matrisi** dolduruldu (hangi özellik için ne kadar
  platform işi çıkıyor); karar DECISIONS.md'de `Confirmed`.
- **Status:** Todo

#### T-005 — MVP occupation template'leri (6 occupation)
- **Objective:** D-008'in altı first-class occupation'ı için Occupation Profile'ların
  (qualification template + occupation'a özgü soru seti) yazılması.
- **Dependency:** T-003, T-004
- **Acceptance Criteria:** 6 Occupation Profile dolduruldu (§4.1 taslağı esas alınarak);
  regulated olanlar için `OccupationRegulation` kaydı jurisdiction/context ile yazıldı ve
  hukuki dayanağı T-008'e bağlandı; **seçilen source'larda her occupation için asgari ilan
  hacmi doğrulandı** (T-003 çıktısıyla kesişim); her occupation için manuel profil soru
  seti ≤5 dakikada tamamlanabilir uzunlukta.
- **Status:** Todo

#### T-028 — MVP matching factor seti ve semantic sınırının sabitlenmesi
- **Objective:** D-017'nin faktör tablosuna uygulanmış halinin doğrulanması; MVP faktör
  alt kümesinin ve semantic üst sınırının implementation'a hazır hale getirilmesi.
- **Dependency:** T-005
- **Acceptance Criteria:** MATCHING_ENGINE faktör tablosundaki MVP işaretleri altı
  occupation'ın gerçek qualification yapısıyla doğrulandı; her MVP faktörü için girdi
  alanlarının DATA_MODEL'de mevcut olduğu tek tek kontrol edildi; semantic katkının
  ~%10 üst sınırı için ölçüm yöntemi tanımlandı.
- **Status:** Todo

#### T-029 — Public sector listing-only davranışının tanımlanması
- **Objective:** D-015'in ürün davranışının netleştirilmesi: public sector ilanı nasıl
  tespit edilir, nasıl gösterilir, hangi sinyaller verilir.
- **Dependency:** T-003
- **Acceptance Criteria:** `is_public_sector` tespit kuralı yazıldı (source tipi +
  içerik sinyalleri); listing-only kart tasarımı ve yönlendirme metni tanımlandı;
  hiçbir akışta Match Score üretilmediği doğrulandı (FR-410).
- **Status:** Todo

### 1b — Validation Gate (D-010) — M1'in kapanma şartı

> Bu yedi task implementation gerektirmez. Eşik değerleri **calibration target**'tır;
> gerçek veri geldikten sonra yeniden değerlendirilir.

#### T-021 — Source coverage validation
- **Objective:** A-3'ün doğrulanması: Türkiye'de MVP meslekleri için bağımsız derlenen
  gerçek açık pozisyonların ne kadarına compliant source'lardan erişilebiliyor?
- **Dependency:** T-003 ✔
- **Acceptance Criteria:** Cluster başına 50-70 ilanlık örneklem **aday source'lardan
  bağımsız olarak** derlendi (döngüsel ölçümü önlemek için); her ilan "aday source'lardan
  erişilebilir mi" diye işaretlendi; coverage yüzdesi cluster başına raporlandı.
  Aynı örneklemden **çapraz yayın oranı**, **işveren gizleme oranı** ve **`posted_at`
  görünürlük oranı** da ölçüldü (T-003'ün nicel olarak kapatamadığı kalemler).
  **Calibration target: ≥%60.** Eşik altında kalınırsa önceden tanımlı karar uygulanır:
  source seti genişletme, cluster değişikliği veya value proposition dilinin coverage'dan
  kalite/explainability eksenine kaydırılması.
- **Hazır plan:** [TURKEY_SOURCE_LANDSCAPE.md](docs/research/TURKEY_SOURCE_LANDSCAPE.md) §9
  (örneklem tasarımı, kaydedilecek 10 alan, türetilecek metrikler).
- **Status:** **Todo — başlatılmadı.** T-003 tamamlandı (dependency karşılandı) ancak
  kullanıcı önceliği T-022 hazırlığına verdi; T-021 kullanıcı onayı olmadan başlatılmaz.

#### T-022A — User interview hazırlığı (saha materyalleri)
- **Objective:** T-022B'nin saha çalışması için tarafsız görüşme materyallerinin
  hazırlanması: katılımcı kriterleri, kota, script, rıza metni, kanıt kodlama ve sentez
  çerçevesi.
- **Dependency:** T-001
- **Acceptance Criteria:** Üç cluster için recruitment kotası belirlendi ✔;
  leading olmayan interview script hazırlandı ✔; consent ve privacy metni yazıldı ✔;
  yapılandırılmış response template oluşturuldu ✔; evidence coding ve synthesis yöntemi
  tanımlandı ✔; Go/Revise/Stop çerçevesi hazırlandı ✔; **hayali response veya sonuç
  üretilmedi** ✔.
- **Status:** **Done** *(2026-07-21)*
- **Çıktılar:** [USER_INTERVIEW_VALIDATION_PLAN.md](docs/research/USER_INTERVIEW_VALIDATION_PLAN.md)
  (25 bölüm + CSV kod defteri) ·
  [USER_INTERVIEW_RESPONSE_TEMPLATE.csv](docs/research/USER_INTERVIEW_RESPONSE_TEMPLATE.csv)
  (yalnızca başlık satırı; PII alanı yok)

#### T-022B — User interview saha çalışması ve sentez
- **Objective:** A-2, A-10 ve R-04'ün gerçek katılımcılarla doğrulanması: hedef segmentler
  bu problemi yaşıyor mu, mevcut platformlar yerine bunu tercih eder mi, dijital kanalla
  erişilebilir mi?
- **Dependency:** T-022A ✔
- **Acceptance Criteria:** 12-18 görüşme tamamlandı (cluster başına ≥4); cevaplar response
  template'ine işlendi; sentez şablonu (plan §21) dolduruldu — **"bizi yanlışlayan
  bulgular" bölümü dahil**; A-2/A-4/A-10 için değerlendirme yazıldı; Go/Revise/Stop kararı
  gerekçesiyle verildi.
- **Status:** **Pending Fieldwork — Blocked (External Input)**
- **Neden bloke:** Görüşmeleri **kullanıcı yürütür.** Bu task gerçek katılımcı verisi
  olmadan tamamlanamaz; hayali görüşme cevabı veya validation sonucu üretilmez.
- **Not:** Plan §23'teki calibration target'lar başarı/başarısızlık eşiği değildir
  ([METRICS.md](docs/product/METRICS.md) §5 hedef revizyon kuralına tabidir).

#### T-023 — Wizard-of-Oz explanation validation
- **Objective:** A-9'un doğrulanması: explainable Match Score karar netliği ve güven
  üretiyor mu; hatalı bir explanation güveni ne kadar bozuyor?
- **Dependency:** T-005
- **Acceptance Criteria:** 10-15 kullanıcıya, kendi profilleri için **elle hazırlanmış**
  5'er explanation kartı gösterildi (biri kasıtlı hatalı); "kararımı netleştirdi" oranı
  ve hatalı kart sonrası güven etkisi ölçüldü. **Calibration target: ≥%70 fayda; hatalı
  kart sonrası tam terk yok.** `unknown` durumunun anlaşılırlığı ayrıca test edildi.
- **Status:** Todo

#### T-024 — Concierge recommendation validation
- **Objective:** A-11 ve A-12'nin doğrulanması: elle üretilen kaliteli öneriler haftalık
  geri dönüş ve feedback üretiyor mu?
- **Dependency:** T-021
- **Acceptance Criteria:** 10-20 gönüllüye 2-4 hafta boyunca haftalık elle hazırlanmış
  5 eşleşme gönderildi (insan = matching engine); haftalık etkileşim, devam isteği ve
  feedback verme oranı ölçüldü. **Calibration target: ≥%40 haftalık etkileşim, ≥%60 devam
  isteği, ≥%30 feedback.**
- **Status:** Todo

#### T-025 — Mini golden dataset ve inter-annotator agreement
- **Objective:** A-6 ve A-7'nin erken doğrulanması: MVP meslekleri için requirement'lar
  tutarlı biçimde etiketlenebiliyor mu, taxonomy kavramlarına bağlanabiliyor mu?
- **Dependency:** T-004, T-005
- **Acceptance Criteria:** 3 occupation'da 30-50 gerçek ilan **iki bağımsız kişi**
  tarafından etiketlendi; hard/required/preferred ayrımı ve `met/unmet/unknown` kararları
  için etiketleyiciler arası uyum ölçüldü; taxonomy kavram kapsama oranı raporlandı.
  **Calibration target: uyum ≥%75, kavram kapsama ≥%80.** Etiketleme kılavuzu bu turda
  revize edildi.
- **Status:** Todo

#### T-026 — CV upload vs manuel profil tercih validation
- **Objective:** A-4'ün doğrulanması ve F-02 kapsam kararının bilgilendirilmesi.
- **Dependency:** T-001
- **Acceptance Criteria:** 12-15 kişiye tıklanabilir mockup ile "CV yükle" vs "5 soruda
  profil" seçimi sunuldu; tercih oranı ve parse endişeleri raporlandı; PDF-only + Türkçe
  kapsamının (AI_SYSTEM §1.1) gerçek kullanıcı dosyalarıyla uyumu değerlendirildi.
  **Calibration target: ≥%50 CV yolu veya endişelerin doğrulama akışıyla giderilebilmesi.**
- **Status:** Todo

#### T-027 — Notification channel validation
- **Objective:** A-13'ün doğrulanması: haftalık e-posta digest hedef segmentte
  re-engagement üretiyor mu; hangi kanal tercih ediliyor?
- **Dependency:** T-022, T-024
- **Acceptance Criteria:** T-024 concierge gönderimlerinin açılma oranı ölçüldü; T-022
  görüşmelerinde kanal tercihi (e-posta / SMS / WhatsApp / uygulama bildirimi) soruldu.
  **Calibration target: açılma ≥%25 ve e-postanın hedef segmentte ilk iki kanal içinde
  olması.** Sonuç D-016'yı yeniden açabilir — bu durumda kullanıcı kararı gerekir.
- **Status:** Todo

### 1c — Teknik Hazırlık

#### T-008 — Compliance çerçevesinin hukuki doğrulaması
- **Objective:** Türkiye için scraping, veri koruma (KVKK) ve otomatik öneri sistemleri
  yükümlülüklerinin uzman görüşüyle doğrulanması.
- **Dependency:** T-001, T-003
- **Acceptance Criteria:**
  [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md) hukuki
  görüşle güncellendi ve **§2 tablosundaki bütün ❓ OPEN / öneri retention değerleri ile
  deletion SLA'sı `Confirmed` karara çevrildi** (DECISIONS.md kaydıyla; gerekçesi
  yazılamayan değer "hiç saklama"ya düşer); `Conditional` source karar rubriği (OPEN-09)
  tanımlandı; ilan gösterim sınırı (OPEN-06), analitik izin modeli (OPEN-01), minimum yaş
  (OPEN-11) ve harici AI servis izni (OPEN-03) karara bağlandı; D-013 kapsamında hangi
  ilan şartlarının Türkiye'de meşru sayıldığı değerlendirildi; engelleyici bulgular
  RISK_REGISTER'a işlendi.
- **Status:** Todo

#### T-009 — CV parsing yaklaşımının karşılaştırılması
- **Objective:** CV parsing için yaklaşım seçeneklerinin (LLM-based extraction, mevcut
  parser servisleri, hybrid) kalite/maliyet/privacy ekseninde değerlendirilmesi.
- **Dependency:** T-002, T-026
- **Acceptance Criteria:** Karşılaştırma [AI_SYSTEM.md](docs/architecture/AI_SYSTEM.md)'e
  eklendi; PDF+Türkçe kapsamı için yeterlilik değerlendirildi; deterministic/AI görev
  ayrımı (§1.3) yaklaşıma göre somutlaştırıldı; öneri ADR taslağı hazırlandı.
  **Privacy ekseni sonucu ve harici servis izin önerisi T-008 çıktısıyla doğrulanmadan
  ADR `Accepted` olamaz.**
- **Status:** Todo

#### T-030 — Employer identity resolution tasarımı
- **Objective:** Duplicate blocking, cluster temsilci seçimi ve `excluded_employers`
  özelliğinin dayandığı employer çözümlemesinin tasarlanması.
- **Dependency:** T-003
- **Acceptance Criteria:** Employer entity alanları ve alias/ATS domain eşleme yaklaşımı
  netleştirildi; Türkiye'ye özgü legal form varyantları (A.Ş., Ltd. Şti. vb.) için
  normalizasyon kuralı yazıldı; employer çözümlenemediğinde kullanılacak fallback
  blocking anahtarı tanımlandı; agency-kopyası senaryosu (SCR-02) fixture olarak eklendi.
- **Status:** Todo

#### T-031 — Privacy inventory ve data rights akışının tamamlanması
- **Objective:** Veri envanterinin eksiksizleştirilmesi ve deletion/export kapsamının
  envanterle birebir eşlenmesi.
- **Dependency:** T-008
- **Acceptance Criteria:** Envanterdeki her sınıf için retention kararı ve silme davranışı
  `Confirmed`; `DataRightsRequest` akışı veri sınıfı bazında izlenebilir şekilde
  tanımlandı; backup rotasyon süresi kararlaştırıldı; anonimleştirme standardı (§2.1)
  hukuki görüşle doğrulandı; TEST_STRATEGY'deki deletion kapsam testi envanterle eşlendi.
- **Status:** Todo

#### T-006 — Matching golden set tasarımı
- **Objective:** Matching kalitesini ölçmek için insan-etiketli test setinin **tasarımı**:
  format, etiketleme kılavuzu, örnekleme stratejisi.
- **Dependency:** T-005, T-025
- **Acceptance Criteria:** Golden set formatı ve etiketleme kılavuzu yazıldı; kılavuz
  `met / unmet / unknown` üç durumunu ayırt ediyor (D-011) ve gate-relevant alanların
  doğrulanmamış halini `unknown` olarak etiketliyor (D-012); **dört etiket katmanı**
  (pairwise match/sıralama kararları, posting-düzeyi requirement etiketleri, occupation
  etiketleri, CV alan etiketleri) ayrı ayrı tanımlandı; **örnekleme stratejisi** netleşti
  (tam çapraz çarpım değil, occupation-içi aday havuzu) ve nDCG@10'un hesaplanacağı aday
  kümesi tanımlandı.
- **Status:** Todo

#### T-006b — Golden set üretimi ve etiketleme
- **Objective:** Tasarlanan golden set'in fiilen üretilmesi (audit MVP-04: bu iş hiçbir
  task'a atanmamıştı).
- **Dependency:** T-006
- **Acceptance Criteria:** Çekirdek set üretildi: 6 occupation'ı kapsayan, örnekleme
  stratejisine uygun etiketli çift seti + span düzeyinde requirement etiketleri +
  format/segment çeşitliliği taşıyan **etiketli sentetik CV korpusu** (CV parsing accuracy
  ve B-3 segment ölçümü için). Etiketleyici planı gerçekçi: tek kişi çalışıyorsa
  test-retest tutarlılığı + agent-öneri/insan-onay protokolü uygulandı, iki kişi varsa
  inter-annotator agreement raporlandı. Etiketleme eforu (çift başına süre × hacim)
  ölçüldü ve kaydedildi.
- **Status:** Todo

#### T-010 — Data model'in gözden geçirilip dondurulması
- **Objective:** [DATA_MODEL.md](docs/architecture/DATA_MODEL.md) entity'lerinin gerçek
  veriyle doğrulanması.
- **Dependency:** T-003, T-005, T-030
- **Acceptance Criteria:** En az 3 gerçek ilanın ve 3 personanın verisi modele kayıpsız
  map edildi; **üç durumlu requirement değerlendirmesi** (D-011) ve **verification state**
  (D-012) alanları gerçek örneklerle sınandı; `requirements[]` içindeki `min_years`,
  `level`, `jurisdiction` alanlarının gerçek ilan metinlerinden doldurulabildiği
  doğrulandı; gereken model değişiklikleri işlendi.
- **Status:** Todo

#### T-011 — MVP-required test ve observability alt kümesinin işaretlenmesi
- **Objective:** [OBSERVABILITY.md](docs/quality/OBSERVABILITY.md),
  [TEST_STRATEGY.md](docs/quality/TEST_STRATEGY.md), **SCRAPING_SYSTEM ve
  MATCHING_ENGINE** dokümanlarında "MVP-required" minimum alt kümesinin işaretlenmesi
  (OPEN-12, OPEN-13).
- **Dependency:** T-002
- **Acceptance Criteria:** Dört dokümanda da "MVP-required" işaretli net liste var;
  ingestion bileşenlerinden hangilerinin MVP'de basit eşdeğerle karşılanacağı
  (Change Detector, Source Discovery, adaptif frekans, öğrenilen TTL) açıkça yazıldı.
- **Status:** Todo

#### T-007 — Wireframe seviyesinde core flow taslakları
- **Objective:** Onboarding, profil oluşturma, job feed, explanation, arama ve digest
  ekranlarının düşük-fidelity taslakları (mobile + web).
- **Dependency:** T-002
- **Acceptance Criteria:** [USER_FLOWS.md](docs/product/USER_FLOWS.md) Flow 1-9'daki her
  adım için ekran taslağı var; explanation ekranı D-005 ve **`unknown` durumu (FR-411)**
  gereklerini karşılıyor; gate-relevant doğrulama adımı (D-012) akışta görünür;
  coverage limitation ve listing-only gösterimleri taslakta yer alıyor.
- **Status:** Todo

#### T-012 — Technology stack kararı (ADR)
- **Objective:** D-001'in kapatılması (OPEN-17).
- **Dependency:** T-008, T-009, T-010, T-011
- **Acceptance Criteria:** Stack ADR'si docs/adr/ altında yazıldı; DECISIONS.md
  güncellendi; kullanıcı onayı alındı.
- **Status:** **Done (2026-07-21)** — [ADR-001](docs/adr/ADR-001-technology-stack.md);
  D-001 kapandı, OPEN-17 kapandı. Kullanıcı onayı: Python veri + TS arayüz, tek
  container runtime.

---

## Faz 2 — MVP Implementation

> Aşağıdaki task'lar bilinçli olarak kabadır; T-012 kapandıktan sonra alt task'lara
> bölünecektir. **Faz 2'ye giriş şartı D-018 ile revize edildi:** implementation
> fixture veriyle başlar; gerçek source'a bağlanma ve gerçek kullanıcı alma
> M1 gate'ine bağlı kalır.

#### T-013 — Repository iskeleti ve CI kurulumu
- **Objective:** Kod repository yapısı, CI pipeline, lint/test iskeleti.
- **Dependency:** T-011, T-012
- **Acceptance Criteria:** Boş servis iskeletleri CI'da build oluyor; DEFINITION_OF_DONE
  implementation bölümü uygulanabilir durumda.
- **Status:** **In Progress** — `services/core` ve `services/ingest` paketleri kuruldu,
  44 test geçiyor. **Eksik:** CI pipeline, lint yapılandırması, `services/api`, `web/`.

#### T-014 — Source Registry + ilk Source Adapter (1 kaynak)
- **Objective:** Source Registry'nin çalışır hali ve tek bir compliant source için uçtan
  uca ingestion (fetch → parse → normalize → store).
- **Dependency:** T-013
- **Acceptance Criteria:** Seçilen source'tan ilanlar normalize edilmiş şekilde
  depolanıyor; provenance kaydediliyor; rate limit ve robots uyumu loglardan doğrulanabiliyor;
  **access-change detection** (login wall/CAPTCHA imzası) çalışıyor ve tetiklendiğinde
  crawl duruyor.
- **Status:** **In Progress (yalnızca fixture)** — Source Registry çalışıyor
  (`services/ingest/src/isuygun_ingest/registry.py`); izin kapısı kod düzeyinde
  zorlayıcı. Pipeline fetch → normalize → dedupe uçtan uca koşuyor.
  **Bloke kalan kısım:** gerçek source adapter, rate limit, access-change detection —
  bunlar ancak OPEN-19/OPEN-09 kapanınca yazılır (D-018).

#### T-016 — Career Profile + CV upload/parsing (MVP kapsamı)
- **Objective:** Manuel profil editörü + CV upload (PDF/Türkçe) + parsing + kullanıcı
  doğrulama akışı.
- **Dependency:** T-013
- **Acceptance Criteria:** Flow 1 ve Flow 2 uçtan uca çalışıyor; parse sonucu kullanıcı
  onayından geçmeden matching'e girmiyor; **gate-relevant alanlarda doğrulama adımı
  atlanamıyor** (D-012); sensitive alanlar profile'a hiç yazılmıyor (D-006) ve discard
  meta-kaydı üretiliyor.
- **Status:** Todo

#### T-017 — Matching Engine v0 + Explainability
- **Objective:** Üç durumlu hard requirement değerlendirmesi + MVP faktör seti ile
  scoring + Match Explanation üretimi.
- **Dependency:** T-014, T-016, T-006b, T-028
  *(Not: cross-source dedupe (T-015) **dependency değildir** — core loop tek source ile
  doğrulanır; audit MVP-06 düzeltmesi.)*
- **Acceptance Criteria:** Golden set üzerinde hedef metrikler **ölçülüyor ve trend
  raporlanıyor** (mutlak eşik M3 kapısı değil, kalibrasyon çıktısıdır — METRICS hedef
  revizyon kuralı); her önerinin explanation'ı FR-404 ve FR-411 şartlarını sağlıyor;
  `unknown` durumu explanation'da ayrı bölümde görünüyor; iki katmanlı sensitive
  attribute testi geçiyor; semantic katkının üst sınırı invariant testiyle doğrulanıyor.
- **Status:** **In Progress** — `services/core` çalışıyor: üç durumlu değerlendirme,
  bant/confidence üretimi, explanation kural tablosu; 17 invariant testi (semantic üst
  sınırı, sensitive attribute, `unknown` ayrımı dahil). D-019 bu task sırasında ortaya
  çıktı. **Eksik:** golden set ve metrik ölçümü (T-006b'ye bağlı), semantic reranking'in
  gerçek embedding'le çalışması.

#### T-015 — İkinci/üçüncü source + cross-source dedupe ve expiration
- **Objective:** 2-3 source'a çıkılması, cross-source duplicate detection ve expiration
  işleme alınması.
- **Dependency:** T-014, T-030
- **Acceptance Criteria:** Farklı source'lardan gelen aynı ilan tek Canonical Job
  Posting'e bağlanıyor; **agency-kopyası senaryosu (değiştirilmiş başlık + gizli işveren)
  fixture testiyle doğrulanıyor**; expired ilanlar feed'den düşüyor; yield/coverage
  anomali izlemesi çalışıyor.
- **Status:** **Kısmen karşılandı** — agency-kopyası senaryosu fixture testiyle
  doğrulandı (`test_agency_copy_is_merged`, `test_reworded_copy_is_still_merged`;
  fixture `007_orig.json` / `008_agency_copy.json`). **Eksik:** ikinci/üçüncü source
  (izne bağlı, D-018), expiration, yield/coverage anomali izlemesi.

#### T-018 — Personalized Job Feed + arama + feedback
- **Objective:** Feed & Search Service: sıralı feed, keyword+location araması, feedback
  (save / not interested / applied).
- **Dependency:** T-017
- **Acceptance Criteria:** Feed explanation'larla geliyor; arama Flow 9'a uygun çalışıyor;
  "not interested" benzer ilanların sıralamasını düşürüyor; MatchResult invalidation
  tetikleyicileri (§2.3) çalışıyor; public sector ilanları listing-only modda görünüyor.
- **Status:** Todo

#### T-019 — Haftalık digest
- **Objective:** Sabit haftalık e-posta digest + opt-out (D-016).
- **Dependency:** T-018
- **Acceptance Criteria:** Digest yalnızca fresh, duplicate-olmayan ve yeterli confidence'lı
  ilanlar içeriyor; opt-out tek dokunuşla çalışıyor; kullanıcı başına gönderim rate limit'i
  var. *Frekans/kanal seçimi bilinçli olarak yoktur.*
- **Status:** Todo

#### T-020 — MVP kapanış: data rights + source transparency + rapor akışı
- **Objective:** Veri export/deletion, ilan kaynağı gösterimi ve "report incorrect/expired
  job" akışının tamamlanması.
- **Dependency:** T-018, T-031
- **Acceptance Criteria:** Export ve deletion uçtan uca çalışıyor ve envanterdeki bütün
  sınıfları kapsıyor; `DataRightsRequest` kaydı sınıf bazında ilerleme gösteriyor; her
  ilan kartında source ve freshness görünüyor; report akışı Flow 8'e uygun çalışıyor ve
  sonuç kullanıcıya bildiriliyor (FR-506).
- **Status:** Todo
