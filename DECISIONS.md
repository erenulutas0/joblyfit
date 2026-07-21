# DECISIONS.md — Karar Kaydı

> **Purpose:** Projede alınan kararların kaydı. Her kayıt **Decision / Reason /
> Alternatives / Consequence** alanlarını içerir. Bir kararın ayrıca ADR olarak
> yazılıp yazılmayacağının kuralı **burada değil**, tek sahibi olan
> [docs/adr/README.md](docs/adr/README.md) dosyasındadır; ADR yazıldığında buraya yalnızca
> özet satırı ve ADR linki eklenir.
> Karar olmayan varsayımlar burada değil, ilgili dokümanda "Assumption" olarak durur
> (ana liste: [PRD.md](docs/product/PRD.md) → Assumptions).

Status değerleri: `Confirmed` (kullanıcı onaylı) · `Proposed` (agent önerisi, onay bekliyor) · `Superseded`

**Confirmed kuralı:** Bir karar yalnızca kullanıcı onayıyla `Confirmed` olur ve onayın
kaynağı parantez içinde belirtilir (ör. "kullanıcının açık talebi", "2026-07-21 onayı").
Kaynağı yazılamayan karar `Proposed` kalır.

---

## D-001 — Technology stack seçimi ertelendi

- **Status:** **Kapandı (2026-07-21)** — stack seçildi: [ADR-001](docs/adr/ADR-001-technology-stack.md)
- **Date:** 2026-07-20 · *kapandı: 2026-07-21*
- **Decision:** Faz 0 boyunca programming language, framework, database, cloud provider
  seçilmez; bütün tasarım technology-independent yazılır.
- **Kapanış:** Seçilen stack — veri/işleme katmanı **Python** (ingestion, extraction,
  matching, FastAPI), arayüz **TypeScript/Next.js**, veri **PostgreSQL + pgvector**,
  çalışma ortamı **Docker Compose**. Gerekçe, alternatifler ve şema kayması riskinin
  nasıl kapatıldığı: [ADR-001](docs/adr/ADR-001-technology-stack.md).
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

- **Status:** Confirmed (product direction, 2026-07-21 onayı) — **kapsam sınırı aşağıda**
- **Date:** 2026-07-20 · *statü açıklığa kavuşturuldu: 2026-07-21*
- **Decision:** Matching yalnızca semantic similarity ile yapılmaz. Pipeline: (1) hard
  requirement eleme/işaretleme, (2) faktör-bazlı structured scoring, (3) semantic
  similarity katkısı, (4) preference ve feedback ayarı. Detay:
  [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md).
- **Onaylanan ile onaylanmayanın sınırı:** Onaylanan şey **hybrid yaklaşımın product
  direction olarak benimsenmesidir**. Faktörlerin tam listesi, grup atamaları ve
  ağırlıkları onaylanmış değildir; bunlar calibration konusudur ve golden set ölçümüyle
  (T-006/T-006b) belirlenir. MVP faktör alt kümesi ve semantic katkının üst sınırı ayrı
  bir kararla sabitlenmiştir (D-017).
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
  extension süreci gerekir. ❓ OPEN-02: ESCO mu O*NET mi (bkz. [CONTEXT.md](CONTEXT.md)
  → Open Question Index). Pazar artık belli olduğu için (D-009) seçim T-004'te
  yapılabilir; seçimden bağımsız olarak Türkçe label üretimi ve TR'ye özgü
  license/qualification'lar **her iki standartta da** extension işi olarak kalır —
  bu bağımlılık [OCCUPATION_TAXONOMY.md](docs/architecture/OCCUPATION_TAXONOMY.md) §2'de
  matris olarak yazılmıştır.

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

- **Status:** Confirmed (kullanıcının açık talebi) · *2026-07-21'de "sakla" → "hiç sakla­ma"
  yönünde güçlendirildi*
- **Date:** 2026-07-20 · *güncellendi: 2026-07-21*
- **Decision:** Age, gender, photo, ethnicity, religion, marital status ve işle doğrudan
  ilgisi olmayan diğer sensitive attribute'lar Match Score hesabına girmez; CV'den
  parse edilseler bile matching feature set'ine taşınmaz. Tam politika:
  [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md) → Fairness Constraints ve
  [AI_SYSTEM.md](docs/architecture/AI_SYSTEM.md) → Bias & Fairness.
- **2026-07-21 güçlendirmesi (data minimization):** Açık bir product veya legal amacı
  olmayan şu alanlar **hiç saklanmaz**: photo, religion, ethnicity, marital status,
  health information, union membership, gender, full birth date. CV parsing sırasında
  tespit edilirlerse structured Career Profile'a **aktarılmadan discard edilir**;
  yalnızca "tespit edildi ve atıldı" meta-kaydı tutulur. **Sensitive Data Vault varsayılan
  saklama alanı değildir**; yalnızca açıkça tanımlanmış legal/product purpose ve consent
  bulunması halinde kullanılabilecek bir extension olarak kalır.
- **Reason:** Ayrımcılık riski, yasal zorunluluklar ve etik ilke. Güçlendirme gerekçesi
  (audit PRV-01): vault'un varlık amacı hiçbir dokümanda gerekçelendirilmemişti; amacı
  yazılamayan veriyi şifreli saklamak minimization ilkesiyle çelişir ve gereksiz sızıntı
  yüzeyi yaratır.
- **Alternatives:** Yok — bu bir kısıt, optimizasyon konusu değil. (Güçlendirme için
  değerlendirilen alternatif: vault'ta saklamaya devam etmek — reddedildi.)
- **Consequence:** CV parsing katmanı sensitive alanları matching'e giden veri yolundan
  izole etmekle kalmaz, listedekileri hiç kalıcılaştırmaz. Free-text alanlar üzerinden
  içerik-seviyesi sızıntı riski ayrıca ele alınır
  ([AI_SYSTEM.md](docs/architecture/AI_SYSTEM.md),
  [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md),
  [TEST_STRATEGY.md](docs/quality/TEST_STRATEGY.md)). Yaş doğrulaması gerekiyorsa tam
  doğum tarihi yerine hesap düzeyinde "18+ mı" gibi türetilmiş bir işaret kullanılır.

## D-007 — MVP tek pazar + sınırlı source seti ile başlar

- **Status:** Confirmed (2026-07-21 onayı) — somutlaştırılması: D-008 (occupation kapsamı)
  ve D-009 (pazar)
- **Date:** 2026-07-20 · *onaylandı: 2026-07-21*
- **Decision:** MVP tek bir launch pazarına ve 3-5 doğrulanmış compliant job source'a
  odaklanır; core loop (profil → ingestion → matching → explainable feed → feedback)
  uçtan uca çalışır. Scope detayı: [PRD.md](docs/product/PRD.md).
- **Reason:** Çok pazarlı/çok kaynaklı başlangıç, taxonomy ve compliance yükünü MVP'de
  taşınamaz hale getirir; matching kalitesi dar kapsamda ölçülüp iyileştirilebilir.
- **Alternatives:** Geniş kapsamlı başlangıç (kapsama iyi görünür ama kalite ve
  compliance kontrol edilemez).
- **Consequence:** İlk kullanıcı kitlesi coğrafi olarak sınırlı olur. Pazar D-009 ile,
  occupation kapsamı D-008 ile kapatılmıştır; source sayısı 2-3 olarak daraltılmıştır
  (D-008).

---

# 2026-07-21 Onaylı Kararlar (D-008 … D-017)

> Bu bölümdeki kararlar kullanıcının 2026-07-21 tarihli açık onayıyla alınmıştır ve
> [audit raporunun](PROGRESS.md) bulgularına verilen yanıtlardır.

## D-008 — MVP kapsamı: üç cluster, ~6 first-class occupation

- **Status:** Confirmed (2026-07-21 onayı)
- **Date:** 2026-07-21
- **Decision:** MVP, audit'in "Alternative 2 — Three Cluster Thesis Probe" seçeneğiyle
  yürür: üç occupation cluster'ında toplam ~6 first-class occupation ve 2-3 compliant
  source. Cluster'lar: **Logistics & Operations** (Driver, Warehouse Worker),
  **Office & Commercial** (Accountant, Sales Representative), **Healthcare** (Nurse,
  Health Technician). Kapsam detayı: [PRD.md](docs/product/PRD.md) → MVP Scope.
- **Reason:** 8-10 occupation, belirtilen kapasiteyle (tek küçük ekip) hiçbir dikeyde
  "birinci sınıf" kaliteye ulaşamaz; üç cluster ise ürünün meslek-genişliği tezini
  (1 regulated + 1 blue-collar + 1 white-collar) kontrollü biçimde test eder.
- **Alternatives:** Tek cluster (en hızlı öğrenme, genişlik tezi ertelenir); 6-8
  occupation'lı budanmış PRD (vizyona en sadık, tek geliştirici için riskli); mevcut
  8-10'luk kapsam (taşınamaz).
- **Consequence:** Platform vision **universal kalır**. Bu altı occupation yalnızca
  occupation-specific taxonomy, qualification template, kalibre edilmiş matching ve
  golden dataset desteği alır. Diğer occupation'lar yasak değildir: generic matching ile
  çalışır, ancak düşük Match Confidence ve açık **coverage limitation** açıklaması
  gösterilir ([OCCUPATION_TAXONOMY.md](docs/architecture/OCCUPATION_TAXONOMY.md) → Support
  Tiers).

## D-009 — Initial launch market: Türkiye

- **Status:** Confirmed (2026-07-21 onayı)
- **Date:** 2026-07-21
- **Decision:** İlk launch pazarı Türkiye'dir. **Ancak core architecture market-neutral
  ve extensible kalır.** TR'ye özgü her şey — job source'lar, legal requirement'lar,
  professional license'lar, qualification denkliği, dil, lokasyon yapısı, public sector
  davranışı, retention/compliance kararları — country-specific **extension veya policy
  katmanında** modellenir; core model varsayımı haline getirilmez.
- **Reason:** Pazar kararı verilmeden taxonomy standardı, compliance doğrulaması ve source
  araştırması ilerleyemiyordu; dokümanların örnekleri de fiilen TR'yi işaret ediyordu
  (audit PS-03). Karar açıkça kayda geçerek "assumption ≠ decision" ilkesi onarılır.
- **Alternatives:** Pazarı açık tutup dokümanları pazar-nötr yazmak (kararı geciktirir,
  T-004/T-008 bloke kalır).
- **Consequence:** T-004 (taxonomy standardı) ve T-008 (hukuki doğrulama) gecikmesiz
  başlayabilir. Karşılığında her dokümanda "bu TR'ye özgüdür / bu core'dur" ayrımının
  görünür tutulması zorunludur; ihlali architecture review bulgusu sayılır. A-1
  assumption'ı kapanmıştır.

## D-010 — Implementation öncesi validation gate zorunludur

- **Status:** Confirmed (2026-07-21 onayı)
- **Date:** 2026-07-21
- **Decision:** MVP build başlamadan önce hem demand-side hem supply-side validation
  yapılır. Faz 1'e yedi validation çalışması eklenir (source coverage, user interview,
  wizard-of-oz explanation, concierge recommendation, mini golden dataset +
  inter-annotator, CV-vs-manuel tercih, notification kanal tercihi — bkz.
  [TASKS.md](TASKS.md) T-021…T-027). **M1 milestone'u yalnızca documentation
  completion ile kapanmaz**; validation sonuçlarına dayalı açık bir
  **go / revise / stop** kararı gerektirir.
- **Reason:** Risk register'ın en yüksek riskleri talep tarafındaydı (R-01 H/H, R-04 M/H)
  ama ilk gerçek kullanıcı teması MVP build sonrasına bırakılmıştı; bu deneyler kod
  yazmadan yapılabilir (audit PS-01).
- **Alternatives:** Doğrulamayı beta'ya bırakmak (aylarca emek doğrulanmamış varsayıma
  yatırılır).
- **Consequence:** Faz 1 uzar; karşılığında build'e girilen varsayımlar kanıtlanmış olur.
  **Eşik değerleri calibration target'tır** — bilimsel kesinlik iddiası taşımaz ve ilk
  gerçek veriyle yeniden değerlendirilir ([METRICS.md](docs/product/METRICS.md)).

## D-011 — Üç durumlu requirement değerlendirmesi (met / unmet / unknown)

- **Status:** Confirmed (2026-07-21 onayı)
- **Date:** 2026-07-21
- **Decision:** Her requirement değerlendirmesi üç durumludur: `met`, `unmet`, `unknown`.
  **Profilde bir qualification bilgisinin bulunmaması, kullanıcının o qualification'a
  sahip olmadığı anlamına gelmez** — `unknown` üretir. Unknown durumunda kullanıcıya
  (a) profilinde hangi bilginin eksik olduğu, (b) bilgiyi ekleyerek recommendation'ın
  nasıl netleşeceği, (c) neden kesin değerlendirme yapılamadığı açıklanır.
- **Reason:** Audit CRITICAL bulgusu MAT-01: ikili model, ≤5 dakikada kurulan seyrek
  profillerde (öncelikli blue-collar segment) sistematik yanlış "eksik" üretiyordu.
- **Alternatives:** İkili model + confidence ile yumuşatma (skalar confidence, "eksik"
  iddiasının kendisini değiştirmez — audit'te çürütüldü).
- **Consequence:** [DATA_MODEL.md](docs/architecture/DATA_MODEL.md),
  [DOMAIN_MODEL.md](docs/architecture/DOMAIN_MODEL.md) invariant'ları,
  [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md),
  [USER_FLOWS.md](docs/product/USER_FLOWS.md) ve
  [REQUIREMENTS.md](docs/product/REQUIREMENTS.md) tutarlı biçimde güncellenmiştir. Golden
  set etiketleme kılavuzu üç durumu ayırt etmek zorundadır.

## D-012 — Gate-relevant alanlar verified olmadan "met" sayılmaz

- **Status:** Confirmed (2026-07-21 onayı)
- **Date:** 2026-07-21
- **Decision:** Şu alanlar **verified** değilse hard requirement'ı `met` sayamaz:
  professional license; driving license ve kategorisi; work permit; yasal zorunlu
  sertifika; country-specific professional authorization; diğer regulated eligibility
  belgeleri. Unverified gate-relevant veri `met` de `unmet` de değildir —
  **`unknown` / verification required** durumundadır.
- **Reason:** Audit CRITICAL bulgusu AIX-01: yanlış parse edilmiş bir lisans,
  doğrulanmadan regulated ilanlarda "karşılanıyor" gösterilebiliyordu; invariant #8
  yalnızca "license yok" durumunu kapsıyordu.
- **Alternatives:** Bütün alanlarda doğrulamayı zorunlu kılmak (onboarding sürtünmesi
  gereksiz yere artar); mevcut hali korumak (FR-408 ve R-08 ihlali).
- **Consequence:** Onboarding'de yalnızca gate-relevant alanlar için doğrulama zorunlu
  adımdır; diğer alanlar atlanabilir kalır. DOMAIN_MODEL invariant #8 genişletilmiş,
  DATA_MODEL'e `verification_state` eklenmiştir.

## D-013 — Legal Eligibility Requirement ≠ Sensitive Attribute

- **Status:** Confirmed (2026-07-21 onayı)
- **Date:** 2026-07-21
- **Decision:** İlan tarafındaki "yasal/policy şartı" ile kullanıcı tarafındaki "sensitive
  attribute" ayrı kavramlardır. **Health information MVP matching pipeline'ına alınmaz ve
  Match Score'da kullanılmaz.** Bir ilanda age, health, military status veya benzeri özel
  şart bulunursa: kullanıcı otomatik olarak uygun/uygunsuz ilan edilmez; şartın
  legal/policy durumu belirsizse Manual Review veya warning davranışı kullanılır;
  kullanıcı **orijinal ilanı kontrol etmeye yönlendirilir**; sensitive user data
  toplanarak otomatik eligibility scoring yapılmaz.
- **Reason:** Audit'te iki reviewer aynı cümleye zıt reçete yazmıştı (XP-02 istisnayı
  çerçevelemek, PRV-02 kaldırmak). Bu karar ikisini uzlaştırır: sensitive veri akmaz
  (PRV-02'nin mimari temizliği korunur) ama kullanıcı şartı görür ve yanlış umuda
  düşmez (XP-02'nin ürün dürüstlüğü korunur).
- **Alternatives:** Şartı tamamen görmezden gelmek (kullanıcı başvuruda elenir); otomatik
  eligibility hesaplamak (sensitive veri toplamayı gerektirir — reddedildi).
- **Consequence:** MATCHING_ENGINE'deki koşullu "sağlık durumu" istisnası kaldırılmış,
  yerine warning/Manual Review davranışı tanımlanmıştır. **Hangi şartın hangi pazarda
  yasal olduğu hukuki görüş gerektirir (T-008); bu dokümanlarda kesin hukuki gerçek
  olarak yazılmaz.**

## D-014 — Manual Review Queue minimal modda çalışır

- **Status:** Confirmed (2026-07-21 onayı)
- **Date:** 2026-07-21
- **Decision:** MVP'de MRQ yalnızca altı durum için kullanılır: source permission
  uncertainty; critical low-confidence extraction; regulated requirement ambiguity;
  potansiyel ayrımcı/hukuken hassas requirement; anlamlı source coverage/yield anomalisi;
  veri kaldırma veya source suspension talebi. **İnsan operasyon kapasitesi haftada en
  fazla ~2 saat kabul edilir.** SLA'lı, çok katmanlı, büyük operasyon sistemi tasarlanmaz.
  Kapasite aşılırsa: source geçici suspend edilebilir, ilgili occupation limited support'a
  alınabilir, problemli extraction otomatik recommendation'dan çıkarılabilir.
- **Reason:** Audit'te MRQ'ya 6-7 akış besleniyordu, hacim tahmini ve sahibi yoktu; iki
  reviewer grubu zıt reçete veriyordu (küçült / birinci sınıf alt sisteme çevir).
  Kapasitenin sayı olarak verilmesi bu çelişkiyi çözer.
- **Alternatives:** Tam MRQ altyapısı (şema + öncelik + alert + dashboard) — MVP'ye
  görünmeyen bir alt sistem ekler.
- **Consequence:** Unmapped occupation ve possible-duplicate akışları MRQ'dan çıkarılmış,
  otomatik/batch davranışa bağlanmıştır. ≤72 saat SLA hedefi kaldırılmıştır.

## D-015 — Public sector: listing-only / guidance mode

- **Status:** Confirmed (2026-07-21 onayı)
- **Date:** 2026-07-21
- **Decision:** Public sector ilanları MVP'de listelenebilir, normalize edilebilir, temel
  eligibility/filter sinyalleri gösterebilir ve orijinal source'a yönlendirebilir. **Ancak
  sınav puanı, mevzuat ve özel prosedürler tam modellenmeden genel Match Score veya
  "uygunsun" sonucu üretilmez.** Bu mod "listing-only / guidance mode" olarak adlandırılır.
- **Reason:** Audit XP-01: public sector hedef grup ilan edilmişti ama merkezi sınav
  puanı/kadro mekaniği ne modellenmiş ne de dürüstçe dışlanmıştı; lisans için engellenen
  yanlış umut, sınav puanı için serbest kalıyordu.
- **Alternatives:** Sınav puanını qualification olarak modellemek (MVP'ye ciddi yeni
  modelleme işi ekler); tamamen Excluded'a almak (hedef grubu kaybettirir).
- **Consequence:** Public sector ilanları için ayrı bir gösterim modu gerekir; Match Score
  yerine "resmi şartları kaynaktan kontrol et" yönlendirmesi yapılır.

## D-016 — MVP notification: sabit haftalık e-posta digest

- **Status:** Confirmed (2026-07-21 onayı)
- **Date:** 2026-07-21
- **Decision:** MVP notification davranışı: **sabit haftalık e-posta digest + opt-out.**
  Instant notification yok, frequency selection yok, channel selection yok, push/SMS yok.
  Kanal etkinliği validation sırasında ölçülür (T-027).
- **Reason:** Audit'te frekans seçimi dört dokümanda çelişkiliydi (F-15 V1 diyor, FR-505
  MUST diyor, T-019 ve Flow 4 MVP davranışı anlatıyor). Sabitleme çelişkiyi kapatır ve
  MVP yükünü azaltır.
- **Alternatives:** Frekans seçimini MVP'de tutmak (küçük ama gereksiz yük); push/SMS
  eklemek (yeni teknik yüzey + yeni kimlik yolu).
- **Consequence:** PRD, REQUIREMENTS, USER_FLOWS, TASKS ve ROADMAP hizalanmıştır.
  **Bilinen risk:** hedef segmentin (mobile-first blue-collar) e-postayı en az kullanan
  segment olması — bu yüzden T-027 kanal validation'ı M1 kapsamındadır ve sonucu
  MVP kanal kararını yeniden açabilir.

## D-017 — MVP matching factor seti ve semantic katkı sınırı

- **Status:** Confirmed (2026-07-21 onayı)
- **Date:** 2026-07-21
- **Decision:** MVP matching ~8 structured factor ile sınırlıdır: occupation
  compatibility; hard qualification compatibility; skills; experience; education; license
  & certification; location & work arrangement; shift & salary preferences. Faktör
  tablosuna MVP/V1 sınıflandırması eklenir. **Semantic similarity MVP'de yalnızca sınırlı
  reranking sinyalidir:** toplam skora katkısı en fazla ~%10; hard gate kararı veremez;
  structured evidence'ın yerine geçemez; low-confidence extraction'da devre dışı kalır;
  tek başına explanation kaynağı olamaz.
- **Reason:** T-017 acceptance'ı var olmayan bir "MVP faktör seti"ne atıf yapıyordu;
  FR-401 literal okunduğunda 19 faktörün tamamını zorunlu kılıyordu (audit MVP-03).
  Semantic'in "sınırlı katkısı" ise niceliksiz ve testsizdi (MAT-10).
- **Alternatives:** Semantic'i tamamen V1'e atmak (D-003'ün "hybrid" tanımı MVP'de
  gerçekleşmez); 19 faktörün tamamı (taşınamaz).
- **Consequence:** **%10 değeri bir calibration target'tır, kesin veya evrensel bir değer
  değildir**; golden set ölçümüyle yeniden değerlendirilir. Sınırın testi TEST_STRATEGY'ye
  invariant olarak eklenmiştir.

## D-018 — M1 validation gate kısmen revize edildi

- **Status:** Confirmed (2026-07-21 onayı) — **D-010'u kısmen revize eder**
- **Date:** 2026-07-21
- **Decision:** Implementation, M1 validation gate'inin tamamı kapanmadan başlar; ancak
  gate iki şey için **aynen korunur**:
  1. **Gerçek source'a bağlanmak** — hiçbir kaynağa crawl başlatılmaz (D-002 + T-003
     sonucu: `allowed` kaynak yok; OPEN-09/OPEN-19 açık).
  2. **Gerçek kullanıcı almak** — beta'ya kullanıcı alınmaz; T-021/T-022B/T-023/T-024
     tamamlanmadan gerçek kullanıcı verisi işlenmez.

  Bu ikisi dışındaki her şey (şema, ingestion pipeline, matching engine, explanation,
  arayüz) **fixture/sentetik veriyle** şimdi inşa edilir.
- **Reason:** Ürünün nasıl hissettirdiğini görmek ve mimari kararların gerçekten
  uygulanabilir olduğunu kanıtlamak için çalışan bir çekirdek gerekiyordu. Fixture'la
  inşa etmek, doğrulanmamış talep varsayımlarına yatırım yapmadan bunu sağlar.
- **Alternatives:** Tam revizyon (implementation önce, validation sonra — R-20
  gerçekleşirse geri dönüş maliyeti yüksek); gate'i olduğu gibi korumak (en güvenli, en
  yavaş; kullanıcı ilerleme görmek istedi).
- **Consequence:** T-013…T-018 fixture veriyle yürütülebilir hale gelir. **T-014'ün
  gerçek source'a bağlanan kısmı ve T-020'nin gerçek kullanıcı verisi işleyen kısmı
  bloke kalır.** Yazılan kodun bir bölümü, T-021/T-022B sonucu ürünü yanlışlarsa
  değişebilir — bu risk bilinçli kabul edilmiştir (R-20).
- **Denetlenebilirlik:** Bu kararın ihlal edilmediği şununla doğrulanır: Source
  Registry'de `scraping_permission: allowed` kayıt bulunmaması ve ingestion'ın yalnızca
  `fixture` access_method'uyla çalışması.

---

## D-019 — Değerlendirilemeyen ilan için bant üretilmez

- **Status:** Confirmed (2026-07-21) — **D-011'in uygulanması sırasında ortaya çıktı**
- **Date:** 2026-07-21
- **Decision:** Bir ilanın **hiçbir** şartı değerlendirilemiyorsa (tümü `unknown`),
  Match Band ve Confidence **üretilmez**. Kullanıcıya "Zayıf eşleşme" değil,
  "bu ilanı profilindeki bilgiyle değerlendiremedik" mesajı ve eksik alan listesi
  gösterilir. `MatchResult.insufficient_data` bunu taşır.
- **Reason:** Implementation sırasında uçtan uca koşuda görüldü: şoför profiline
  hemşire ilanı **"Zayıf eşleşme"** olarak çıkıyordu. Nedeni şartların
  karşılanmaması değil, hiç değerlendirilememesiydi — değerlendirilebilir kütle
  sıfır olunca skor 0 çıkıyor ve zayıf banda düşüyordu. Bu, `unknown`'ın arka
  kapıdan `unmet` gibi cezalandırılması, yani **D-011'in bant düzeyindeki
  ihlalidir**. Skor katmanı doğru davranıyordu; kaçak bant katmanındaydı.
- **Alternatives:** Bandı coverage ile tavanlamak (reddedildi — bu da `unknown`'a
  ceza yazar, D-011'e aykırı); olduğu gibi bırakıp yalnızca Confidence'ı düşük
  göstermek (reddedildi — "Zayıf eşleşme" etiketi kullanıcı tarafından
  "sana uymuyor" diye okunur, oysa sistemin bilgisi yok).
- **Consequence:** Arayüzde ilan kartının **dördüncü bir durumu** vardır:
  güçlü / iyi / şartlı / zayıf **ve** "değerlendirilemedi". Feed sıralaması bu
  ilanları bant üzerinden sıralayamaz; ayrı ele alınması gerekir (bkz. OPEN-22).
- **Denetlenebilirlik:** `services/core/tests/test_critical_invariants.py` →
  `test_all_unknown_produces_no_band_at_all`.

---

## D-020 — İzinli ATS API'leri açıldı; LinkedIn/Indeed kapalı kaldı

- **Status:** Confirmed (2026-07-21 kullanıcı onayı) — **D-018'i kısmen revize eder**
- **Date:** 2026-07-21
- **Decision:** Gerçek ilanlar, **izni kaynağın kendi yayınında kanıtlanan** public
  ATS API'lerinden çekilir: Lever, Greenhouse, Recruitee. Bu uçlar şirketlerin
  kendi kariyer sayfalarını kurmaları için yayınladığı, kimlik doğrulaması
  istemeyen public API'lerdir ve yanıt ilanın **kendi sayfasına** giden URL taşır.

  D-018'in "hiçbir kaynağa crawl başlatılmaz" maddesi **yalnızca bu sınıf için**
  kalkar. Kaldıran şey kararsızlık değil, kanıttır: izin, kaynağın kendi
  robots.txt'inde ve dokümantasyonunda yazılıdır.

  D-018'in ikinci maddesi (**beta'ya gerçek kullanıcı alınmaz**) aynen durur.
- **Reason:** Kullanıcı gerçek ilanları listelemek ve kullanıcıyı ilanın kendi
  sayfasına yönlendirmek istedi. Araştırma, LinkedIn için **hiçbir yasal yol
  olmadığını** gösterdi (okuma API'si yok; Job Posting API ters yönde çalışıyor ve
  yeni partner almıyor; robots.txt `Disallow: /`). Buna karşılık ATS public API'leri
  tam olarak bu kullanım için var: yönlendirilen trafik kaynağın **istediği** şey.
- **Alternatives:** Careerjet / Jooble publisher API'leri (Türkiye kapsamı daha
  geniş, blue-collar dahil — **ertelenmedi, sırada**; publisher kaydını kullanıcı
  yapacak). Aggregator scraper'ları (JSearch, Coresignal) **reddedildi**: kendi
  tanımlarıyla LinkedIn/Indeed'i scrape ediyorlar, o ToS ihlalini devralmak olurdu.
- **Consequence:** Türkiye kapsamı **dar ve tech ağırlıklı** — 5 pano, ~52 ilan.
  Ürünün "her meslek dalı" iddiasını bu kaynak tek başına karşılamaz; Careerjet/
  Jooble veya doğrudan izin (OPEN-19) gerekir. Kapsam sınırı arayüzde gizlenmez.
- **Denetlenebilirlik:**
  1. `allowed` işaretli her kayıt `permission_evidence` taşımak zorundadır;
     `registry.allowed_without_evidence()` boş dönmelidir
     (`test_allowed_sources_must_carry_evidence`).
  2. LinkedIn ve Indeed `rejected` kalır (`test_rejected_sources_stay_rejected`).
  3. Ağ erişimi açık her kayıt `access_method` olarak yalnızca `api`/`feed`
     taşıyabilir (`test_open_sources_are_only_permitted_apis`).
  4. Çekilecek panolar `registry.BOARDS` içinde **elle** listelenir; otomatik
     keşif yoktur.

---

## D-021 — Ayırt edici olmayan şartlar tek başına bant üretemez

- **Status:** Confirmed (2026-07-21) — gerçek veriyle ortaya çıktı
- **Date:** 2026-07-21
- **Decision:** Bir ilandan değerlendirilebilen şartların **hepsi** ayırt edici
  olmayan kategorilerdense (`language`, `education`, `shift`), Match Band
  üretilmez; ilan "değerlendirilemedi" olarak gösterilir (D-019 mekanizması).
- **Reason:** Gerçek ATS ilanlarıyla ilk koşuda bir yazılımcı profiline
  **"Legal Professionals — Labor Law"** ilanı *Güçlü eşleşme* çıktı. Sebep: o
  ilandan yalnızca "İngilizce" ve "Lisans mezuniyeti" çıkarılabilmişti ve
  geliştirici ikisine de sahipti → 1/1 → güçlü. Hiçbir mesleki kanıt olmadan
  uyum iddia edilmiş oluyordu. Bu, zayıf extraction'ın sahte güvene dönüşmesidir.
- **Alternatives:** Occupation eşleşmesini skora katmak (reddedildi — meslek
  sınıflandırması kestirimdir, gate kararı veremez); ayırt edici şartlara daha
  yüksek ağırlık vermek (reddedildi — ağırlık, kanıt yokluğunu gizler, yalnızca
  geciktirir).
- **Consequence:** Zayıf çıkarımlı ilanlar bant almaz. Bu, feed'de daha az
  "eşleşme" demektir — **kasıtlıdır**: az ve doğru, çok ve yanlıştan iyidir.
  Extraction iyileştikçe bant alan ilan sayısı kendiliğinden artar.
- **Denetlenebilirlik:** `test_generic_requirements_alone_produce_no_band`.

---

## D-022 — Bant tavanı: iddianın gücü, kanıtın miktarını aşamaz

- **Status:** Confirmed (2026-07-21) — gerçek veriyle ortaya çıktı
- **Date:** 2026-07-21
- **Decision:** Match Band, **değerlendirilebilen ayırt edici şart sayısıyla**
  tavanlanır: 1 şart → en fazla `cond`, 2 şart → en fazla `good`, 3+ → `strong`
  serbest. Bu bir ceza değil **üst sınırdır**; bandı skorun verdiğinden aşağı
  çekmez.
- **Reason:** ~2400 gerçek ilanla koşuda bir yazılımcı profiline **"Majors
  Account Executive, Berlin"** ilanı *Güçlü eşleşme* çıktı. İlan metninde
  "bulut" geçiyordu, geliştiricide de o beceri vardı → 1/1 → skor 1.0 → güçlü.
  Tek tesadüfi kelime örtüşmesi "güçlü eşleşme" iddiasını taşımaz.
- **Alternatives:** Occupation eşleşmesini skora katmak (reddedildi — meslek
  sınıflandırması kestirimdir, gate kararı veremez); ayırt edici şartlara daha
  yüksek ağırlık (reddedildi — kanıt *yokluğunu* gizler, yalnızca geciktirir).
- **Consequence:** Güçlü bant sayısı belirgin şekilde azalır (252 → 207 örnek
  koşuda) ve kalanlar 3+ karşılanan şarta dayanır. **D-011 korunur:** kaç şartın
  *bilinmediği* bandı etkilemez; belirleyici olan kaç şartın gerçekten
  *değerlendirilebildiğidir*.
- **Denetlenebilirlik:** `test_single_requirement_cannot_produce_strong_band`,
  `test_three_requirements_may_reach_strong`, `test_cap_never_lowers_a_weak_band`.
