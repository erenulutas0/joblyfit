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

---

## D-023 — Kayıt gerektirmeyen public iş ilanı API'leri eklendi

- **Status:** Confirmed (2026-07-21 kullanıcı onayı: "hesap gerektirmeyenlerle devam et")
- **Date:** 2026-07-21
- **Decision:** Dört kaynak eklendi: **Arbeitsagentur** (Almanya İş Ajansı — mavi
  yaka kapsamı için ana kaynak), **Arbeitnow** (DE/AB), **The Muse** (ABD),
  **Himalayas** (uzaktan). Dördü de kimlik doğrulaması istemeyen, yayıncının kendi
  belgelediği JSON uçlarıdır.
- **Reason:** ATS panoları teknoloji/kurumsal ağırlıklıydı; ürünün "her meslek
  dalı" iddiası karşılanmıyordu. Arbeitsagentur bu boşluğu doğrudan kapatıyor —
  depo, şoför, kaynakçı, aşçı, bakım gibi meslekler.
- **Alternatives:** JobTechDev (İsveç açık verisi) — **eklenmedi**, sözlük İsveççe
  konuşmuyor, eklense ilanlar eşleşmezdi. Adzuna/USAJOBS/Reed — ücretsiz ama kayıt
  gerektiriyor, kullanıcı "hesap gerektirmeyenler" dedi. RemoteOK/Jobicy/Remotive —
  sert atıf veya çok düşük istek limiti; Remotive'in ToS'u kullanıcı hesabı ardında
  ilan göstermeyi kısıtlıyor ve ürün modeliyle çelişiyor.
- **Consequence:** Kaynaklar artık **aynı şartlarla gelmiyor**. Registry kayıt
  başına `attribution_required`, `min_poll_hours` ve `redistribution_policy`
  taşıyor (OPEN-25 kapandı). Arbeitsagentur liste ucu **açıklama metni vermez**;
  şart çıkarımı başlık + meslek adıyla sınırlıdır ve bu sınır kayıtta yazılıdır.
  Sözlüğe Almanca mavi yaka yüzey biçimleri eklendi (Lagerhelfer, Staplerschein,
  Berufskraftfahrer, Schweisser, Pflegehelfer…).
- **Denetlenebilirlik:** `test_api_sources_are_registered_with_policy`,
  `test_attribution_required_sources_are_marked`, `test_every_api_source_has_a_fetcher`.

---

## D-024 — Süresi geçmiş ilan gösterilmez; tarihi bilinmeyen elenmez

- **Status:** Confirmed (2026-07-21 kullanıcı isteği: "geçmiş işler çıkmasın")
- **Date:** 2026-07-21
- **Decision:** Yayın tarihi `MAX_AGE_DAYS`'ten (varsayılan 45) eski olan ilan
  ingest'te **düşürülür**. Yayın tarihi **bilinmeyen** ilan düşürülmez; "tarih
  bilinmiyor" olarak işaretlenir ve tarihe göre sıralamada sona konur.
  Arayüzde "Son 7 / 14 / 30 gün" filtresi ve ilan yaşı göstergesi vardır.
- **Reason:** Kullanıcıyı kapanmış bir ilana yönlendirmek, ona hiç ilan
  göstermemekten daha kötüdür — güveni doğrudan kırar. Kaynakların çoğu kapanan
  ilanı listeden düşürür ama hepsi düşürmez ve düşürme gecikir.
- **Alternatives:** Tarihi bilinmeyen ilanı da elemek (**reddedildi** — D-011'in
  aynı mantığı: "bilmiyoruz", "kötü" demek değildir; bazı kaynaklar tarih hiç
  vermiyor ve bu ilanları atmak kullanıcıdan gerçek fırsat gizlerdi). İlanın hâlâ
  açık olup olmadığını kaynağa tek tek sormak (ertelendi — istek maliyeti yüksek,
  `min_poll_hours` şartlarını zorlar).
- **Consequence:** Eleme **sessiz değildir**: `stale_dropped` ingest raporunda ve
  arayüzde görünür. Himalayas `expiryDate` verdiği için orada süresi geçmiş
  ilanlar çekim anında ayıklanır.
- **Denetlenebilirlik:** `test_stale_posting_is_dropped`,
  `test_posting_without_date_is_not_dropped`, `test_unparseable_date_is_unknown_not_old`.

---

## D-025 — LinkedIn üçüncü kez reddedildi; yerine "ilan yapıştır" akışı

- **Status:** Confirmed (2026-07-21) — D-020'nin kapsamını daraltmaz, netleştirir
- **Date:** 2026-07-21
- **Decision:** LinkedIn'den ilan çekilmez. Yerine kullanıcının **kendi getirdiği**
  ilan metnini değerlendiren bir uç eklendi (`POST /api/jobs/evaluate`). Sunucu
  hiçbir adrese istek atmaz; metni kullanıcı yapıştırır. Sonuç **saklanmaz** ve
  korpusa eklenmez.
- **Reason:** Kullanıcı üç kez LinkedIn istedi. Üçüncüsünde cevabı değiştirebilecek
  tek şey doğrulandı — LinkedIn'in bir iş panosuna partner yolu açıp açmadığı.
  Microsoft Learn dokümanı (2026-06-03 güncellemesi) iki şeyi netleştiriyor:
  *"We are currently not accepting new partnerships for LinkedIn's Job Posting API"*
  ve API'nin yönü — *"to **post jobs directly to LinkedIn** on behalf of customers"*.
  Okuma/arama API'si yok; aggregator'ların ilan içeri alabileceği bir program yok.

  Ama kullanıcının asıl ihtiyacı LinkedIn değil **kapsam**dı. Ekranındaki bir ilanı
  kendi eylemiyle sisteme taşıması scraping değildir ve bu ihtiyacı karşılar.
- **Alternatives:** Tarayıcı eklentisi ile kullanıcının oturumundan okumak
  (ertelendi — LinkedIn'in kullanıcı sözleşmesi oturum içinden otomatik veri
  çıkarımını da kısıtlıyor; ayrı bir hukuki değerlendirme gerektirir, T-008).
  Üçüncü taraf scraper API'leri (reddedildi — ihlali devralmak olurdu).
- **Consequence:** Yapıştırılan ilan korpustakiyle **aynı** hattan geçer: aynı
  sözlük, aynı çıkarım, aynı matching, aynı açıklama kuralları. Ayrı bir
  "yapıştırma modu" yazmak iki kod yolunun zamanla sapması demekti.
- **Denetlenebilirlik:** `test_pasted_job_is_not_added_to_the_corpus`,
  `test_pasted_job_keeps_url_without_fetching_it`,
  `test_pasted_job_respects_verification_gate`.
- **Ek not (aynı gün, dördüncü talep):** Kullanıcı "Reddit'ten araştır, en sağlıklı
  scrape mekanizmasını kuralım" dedi. Bu araştırma **yapılmadı**: o mecradaki
  cevaplar tek bir kategoridir — konut proxy'leri, `undetected-chromedriver`,
  oturum çerezi çıkarma, ya da bunu devralan üçüncü taraf scraper servisleri.
  Hepsi bot tespitinden kaçınma tekniğidir; derlemek de uygulamak kadar sorunlu
  olurdu. Ayrıca mühendislik olarak da kötü bir temel: kaynak sizinle aktif
  mücadele ederken kurulan çeker sürekli kırılır.

  **Bu kararı değiştirecek tek şey:** LinkedIn'in okuma/arama API'si açması veya
  Job Posting partner programını yeniden açması. İkisi de takip edilebilir;
  kendiliğinden yeniden araştırma yapılmaz.

---

## D-026 — "Beceri var ama süresi yok" ayrı bir bilinmeyendir

- **Status:** Confirmed (2026-07-21) — gerçek kullanımda ortaya çıktı
- **Date:** 2026-07-21
- **Decision:** ``UnknownReason`` dördüncü bir varyant kazandı:
  ``missing_duration``. Profilde beceri **kayıtlı** ama ilanın istediği süre
  bilgisi yoksa bu durum ``missing_profile_data``'dan ayrılır; kullanıcıya
  "profilinde yok" değil "kaç yıllık olduğu yazmıyor" denir ve eylem
  "Süreyi ekle" olur.
- **Reason:** Yapıştırma akışı ilk denendiğinde sistem **"Python bilgisi
  profilinde yok"** dedi — oysa profilde Python vardı; ilan 5+ yıl istiyordu ve
  bilinmeyen yalnızca süreydi. Kullanıcıya sahip olduğu bir beceriyi yokmuş gibi
  göstermek, `unknown` durumunun taşıdığı bilgiyi kaybetmektir; bu D-011'in
  varlık sebebine aykırıdır.
- **Alternatives:** Süresi bilinmeyen beceriyi `met` saymak (reddedildi — ilan
  açıkça süre istiyor, bunu görmezden gelmek uydurma bir eşleşme üretir).
  Mesajı serbest metinle yamamak (reddedildi — gerekçe tipte taşınmazsa arayüz
  ve API farklı şey söyler).
- **Consequence:** Arayüzde dördüncü bir eylem etiketi var: "Süreyi ekle".
- **Denetlenebilirlik:** `test_missing_duration_is_not_reported_as_missing_skill`,
  `test_absent_skill_still_says_missing`.

---

## D-027 — Profil kalıcılığı SQLite ile; PostgreSQL hedef olarak duruyor

- **Status:** Confirmed (2026-07-21) — **ADR-001'i değiştirmez**, sırasını değiştirdi.
  **Aynı gün tamamlandı:** Docker açılınca PostgreSQL uygulaması yazıldı ve
  gerçek veritabanına karşı sınandı. SQLite artık düşme zincirinin ikinci
  halkası olarak duruyor.
- **Date:** 2026-07-21
- **Decision:** Kullanıcı profili artık kalıcı. Depolama bir **arayüz** ardına
  alındı (`storage.ProfileStore`); bugünkü uygulaması SQLite. PostgreSQL
  uygulaması yazıldığında değişecek tek yer `open_store`'dur — API ve arayüz
  katmanı hiç dokunulmaz.
- **Reason:** ADR-001 PostgreSQL diyor ve bu karar geçerli. Ama bu makinede
  **Docker daemon çalışmıyor**; PostgreSQL kodu yazılsa koşturulup sınanamazdı.
  Çalıştığı görülmemiş altyapı kodu teslim etmek, çalışan bir şey teslim etmek
  değildir. SQLite bugün doğrulanabiliyor ve kullanıcının gerçek şikâyetini
  (her yeniden başlatmada profilin kaybolması) çözüyor.
- **Alternatives:** PostgreSQL'i doğrulamadan yazmak (reddedildi — yukarıdaki
  gerekçe). Kalıcılığı ertelemek (reddedildi — sorun her oturumda tekrarlıyordu).
- **Consequence:** `.data/profile.db` dosyası oluşur (git'te değil).
  **İlan korpusu kalıcı kılınmadı** ve bu bilinçli: ilanlar dış kaynaktan gelir,
  tazelikleri vardır (D-024) ve veritabanındaki kopya kapanmış bir ilanı
  yaşatmaya devam ederdi. Korpus `.cache/` altında ayrı yönetiliyor.
  Açılış süresi hâlâ ~35 sn — bu extraction maliyeti, kalıcılıkla ilgisiz.
- **Uygulama sırası (D-027b):** `open_store` → PostgreSQL → SQLite → bellek.
  `docker-compose.yml` (pgvector/pg16, port 5435 — 5432 ve 5433 doluydu) ve
  `db/001_init.sql`. Şemada `verification` bir **CHECK** ile sınırlandı: uygulama
  katmanı tanınmayan değeri zaten düşürüyor ama veritabanına doğrudan yazan bir
  yol (migration, elle müdahale) o kontrolü atlar; iki katman da tutmalı.
  pgvector uzantısı şimdiden açıldı — semantic reranking (T-006b) henüz yok ama
  imajı sonradan değiştirmek veri taşımayı gerektirir.
- **Denetlenebilirlik:** `services/api/tests/test_storage.py`. PostgreSQL testleri
  `ISUYGUN_TEST_DSN` verilmezse atlanır — sahte bir veritabanına karşı test etmek
  asıl riski (SQL lehçesi, dizi tipleri, CHECK, işlem sınırları) hiç sınamazdı.
  `test_pg_and_sqlite_agree` iki uygulamanın aynı girdide aynı sonucu verdiğini
  doğrular: sessiz bir semantik farkı, veritabanı değiştirildiğinde kullanıcının
  profilinin sessizce değişmesi demektir. Ayrıca
  `test_tampered_verification_does_not_pass_the_gate`: veritabanından gelen
  tanınmayan doğrulama değeri **en güvenli** duruma düşer. Sessizce `verified`
  kabul etmek, D-012'nin bütün gate mantığını veritabanı üzerinden atlatılabilir
  yapardı.

---

## D-028 — Önbellek işlenmiş kayıtları da tutar; çıkarım parmak iziyle geçersizleşir

- **Status:** Confirmed (2026-07-21)
- **Date:** 2026-07-21
- **Decision:** `.cache/ats_postings.json` artık **hem ham hem işlenmiş** kayıt
  tutar ve yanında **çıkarım mantığının parmak izini** taşır (`lexicon.py` +
  `extract.py` içeriğinin hash'i). Parmak izi tutmuyorsa işlenmiş kayıtlar
  atılır, ham kayıtlar korunur.
- **Reason:** Açılışın 35 saniyesinin **tamamı** extraction'dı — 5810 ilanın
  sözlük taraması her açılışta baştan yapılıyordu. Ölçüm: ham önbellekle 35 sn,
  işlenmiş önbellekle **1.2 sn**.
- **Asıl mesele hız değil, geçersizleştirme.** Sözlüğe bir terim eklendiğinde
  önbellekteki işlenmiş kayıtlar eski mantığı taşımaya devam etseydi,
  geliştirici değişikliğinin hiçbir etkisini göremezdi. O hatanın belirtisi
  ("değişikliğim işe yaramıyor") insanı **kodda** arattırır, önbellekte değil —
  saatler kaybettirebilecek bir sessiz hata.
- **Alternatives:** Elle artırılan sürüm numarası (reddedildi — artırmayı
  unutmak tam da yukarıdaki sessiz hatayı üretir). Yalnızca işlenmiş kayıtları
  tutmak (reddedildi — mantık değiştiğinde yeniden **çekim** gerekirdi: 195 sn
  yerine 43 sn).
- **Consequence:** Önbellek ~70 MB (ham + işlenmiş). Disk ucuz, 150 saniye
  değil. Yazım geçici dosya üzerinden yapılır: yarıda kalan bir yazım eski
  önbelleği de kaybettirseydi sonuç gereksiz bir tam çekim olurdu.
  Ölçülen: soğuk 195 sn · sıcak **1.2 sn** · mantık değişmiş 43 sn.
- **Denetlenebilirlik:** `services/ingest/tests/test_cache.py`, özellikle
  `test_changed_extraction_logic_invalidates_processed_records` ve
  `test_partial_write_does_not_destroy_existing_cache`.

---

## D-029 — Maaş üç durumlu gösterilir; kur dönüştürmesi yapılmaz

- **Date:** 2026-07-22
- **Status:** Accepted
- **Context:** Saha çalışması, maaşın gizlenmesini muadillerin en somut ve en
  çok şikâyet edilen eksiği olarak gösterdi. Türkiye'de ağırlığı ayrıca var:
  Kariyer.net'te maaş **filtresi bile yok**. Rakiplerin burada yapısal bir
  çıkar çatışması var — ilan verenden ücret alıyorlar, ilan veren maaşı
  yazmak istemiyor. Bizim böyle bir bağımlılığımız yok.
- **Decision:** İlan metninden maaş çıkarılır ve üç durumdan biri gösterilir:
  `found` (yazıyor), `not_stated` (ilan yazmamış), `unreadable` (rakam var,
  güvenle okunamadı). Filtre yalnızca `found` üzerinden çalışır.
- **Reason (üç durum):** "Yazmamış" ile "okuyamadım" farklı taraflara ait
  kusurlardır. İkisini birleştirmek, maaşını dürüstçe yazan bir ilanı
  yazmamış gibi göstermek olurdu — tam da ödüllendirmek istediğimiz davranışı
  cezalandırırdık. Bu, D-011'in üç durumlu şart değerlendirmesiyle aynı ilke.
- **Reason (dönüştürme yok):** Kaynaktaki para birimi olduğu gibi gösterilir.
  Kur çevirisi yapsaydık, hangi güne ait kurla hesaplandığı belirsiz bir sayı
  üretirdik; yanlış kurla gösterilen maaş maaş değildir.
- **Yanlış pozitif asimetrisi:** Maaşı bulamamak kullanıcıya "belirtilmemiş"
  gösterir — ilanın kusuru, zararsız. Yanlış bulmak **var olmayan bir sayı**
  gösterir ve kullanıcı ona güvenerek başvurur. Bu yüzden yakınında maaş
  bağlamı (±90 karakter) olmayan sayı kabul edilmez ve makul aralık dışına
  çıkan değer elenir. Testlerin çoğu doğru pozitifi değil, yanlış pozitifi
  kovalar.
- **Ölçüm (5808 ilanlık gerçek korpus):** %37 bulundu · %16 para var ama
  okunamadı · %46 hiç maaş yok.
- **Consequence:** `salary.py` çıkarım mantığıdır, bu yüzden önbellek parmak
  izine (`cache._LOGIC_FILES`) eklendi; eklenmeseydi önbellekteki ilanlar
  sessizce maaşsız kalırdı.
- **Denetlenebilirlik:** `services/ingest/tests/test_salary.py`.

---

## D-030 — Facet sayaçları gösterilen listeden sayılır; liste artımlı basılır

- **Date:** 2026-07-22
- **Status:** Accepted
- **Context:** Maaş rozeti eklenince ortaya çıktı: rozet "1994 ilan" diyordu,
  kullanıcı tıklayınca 1678 ilan görüyordu. Facet'ler `_group_by_role`
  **öncesinden**, liste ise sonrasından sayılıyordu. Aynı sapma şehir, işveren
  ve bölge sayaçlarında da vardı.
- **Decision (a):** Facet'ler gösterilen listeden sayılır. Şehir facet'i
  birleştirilen konumları da içerir ve şehir filtresi `other_locations`'a da
  bakar — aksi halde o şehirdeki gerçek ilan kaybolurdu.
- **Decision (b):** Liste 60'ar ilan basılır, kalan sayı açıkça yazılır
  ("1309 ilan daha var"). Filtre değişince pencere başa döner.
- **Reason:** Sayının kendisi yanlış değildi ama kullanıcıya verilen söz
  tutulmuyordu. Gördüğü sayı, tıklayınca aldığı sayı olmalı.
- **Ölçüm:** 4395 kart tek turda basılırken 105.470 DOM düğümü üretiliyor ve
  sayfa donuyordu; artımlı gösterimle **5.241** düğüm.
- **Kırpma sessiz değildir:** Gizlenen ilan sayısı yazılır. Sessizce kırpmak
  kullanıcıya "hepsi bu" demek olurdu.

---

## D-031 — Tam metin araması sunucuda; operatörlerle daraltılabilir

- **Date:** 2026-07-22
- **Status:** Accepted
- **Context:** Arama yalnızca başlık, işveren, şehir ve şart önizlemesine
  bakıyordu. Sözlükte olmayan ama ilan metninde geçen terimler ("forklift",
  "SAP", "kaynakçı") hiç bulunamıyordu — kullanıcı aradığı işin **var**
  olduğunu bilmeden "sonuç yok" görüyordu. Ölçüldü: "forklift" 0 sonuç
  veriyordu, gerçekte 13 ilan var.
- **Decision:** Tam metin araması sunucuda yapılır; `/api/search` yalnızca
  eşleşen ilan kimliklerini döner. Diğer filtreler istemcide anında çalışmaya
  devam eder ve bu kümeyle kesiştirilir.
- **Reason:** Açıklamalar toplam **30 MB**. Tarayıcıya göndermek anlamsız;
  sunucuda tam korpus taraması **19 ms** sürüyor. Buna karşılık şehir/bant/
  bölge filtreleri istemcide kalmalı — her tuş vuruşunda ağa çıkmak, hâlihazırda
  anında olan bir şeyi yavaşlatırdı.
- **Operatörler:** `"tam öbek"`, `-dışla`, çoklu kelime (VE mantığı). Dışlama
  özellikle işe yarıyor: "engineer -senior" 2771 sonucu 1418'e indiriyor.
  Sorgunun **nasıl anlaşıldığı** kullanıcıya geri gösterilir — operatörü yanlış
  yazdığında sessizce başka bir arama yapılmış olmasın.
- **Consequence:** Arama torbaları açılışta bir kez kurulur; her istekte 30 MB
  metni yeniden katlamak, arama kutusuna her harf yazıldığında bunu tekrarlamak
  demekti. İlan metni 8000 karakterde kesilir: kuyruk genelde hukuki metin ve
  eşit fırsat beyanıdır, oradan gelen eşleşme alakasızdır.
- **Yarış koşulu:** İstemci `searchSeq` ile geç dönen eski yanıtı yok sayar;
  yoksa hızlı yazarken liste sorguyla alakasız görünebilirdi.

---

## D-032 — Üç yeni eksen: çalışma biçimi, deneyim, istihdam türü

- **Date:** 2026-07-22
- **Status:** Accepted
- **Context:** Kullanıcı "uzaktan çalışabileceğim işler" diye arıyordu ve bunu
  serbest metinle yapmak zorundaydı. Ölçüm: korpusun %27'si uzaktan, %13'ü
  hibrit işareti taşıyor — filtre olmayı fazlasıyla hak eden bir eksen.
- **Decision:** `work_arrangement` (remote/hybrid/onsite), `experience_level`
  (senior/entry), `employment_type` (part_time/contract/internship) çıkarılır.
  Üçü de `None` olabilir ve **bu "belirtilmemiş" demektir, varsayılan değil**.
- **Reason (bilinmiyor ≠ varsayılan):** İşaret yoksa "ofisten" demek, ilanın
  söylemediği bir şeyi söylemiş gibi göstermek olurdu (D-011'in aynı mantığı).
  "Belirtilmemiş" arayüzde kendi seçeneği olarak sayaçlı gösterilir; gizlenmesi
  kullanıcıya yanlış bir bütünlük hissi verirdi.
- **Reason (tam zamanlı çıkarılmaz):** Neredeyse hiçbir ilan yazmıyor çünkü
  varsayılan. Yazmayanı tam zamanlı saymak kanıt değil varsayımdır.
- **Yanlış pozitifler — hepsi gerçek korpusta yakalandı:**
  1. `remote`/`hybrid`/`contract` yazılım ilanlarında **teknik terim**:
     "remote server", "hybrid cloud", "smart contract". Çıplak kelime yetmez,
     kalıp aranır.
  2. Şirketin **politika cümlesi** ("fully office-based, fully remote, or
     hybrid") o ilanın biçimi sanılıyordu. Seçenek listesi içindeki eşleşme
     sayılmaz — ama kontrol **cümle** düzeyinde yapılır: sabit karakter
     penceresi, hemen ardından gelen gerçek beyanı da eliyordu (testle
     yakalandı).
  3. Hibrit önce bakılır: hibrit ilanlar "remote" kelimesini de kullanır
     ("2 days remote"). Ters sıra, haftada 3 gün ofise gitmesi gereken bir işi
     "uzaktan" gösterirdi — kullanıcı taşınma kararı bile verebilir.
  4. `manager` kıdem işareti **değil**: "Account Manager" rol türüdür. Dahil
     edilince korpusun %54'ü "kıdemli" görünüyordu; yarıdan fazlasını seçen
     filtre hiçbir şey seçmiyor demektir. Düzeltilince %38.
  5. `lead` "Lead Generation Specialist"ten ayrılır — o bir satış rolüdür.
- **Performans:** Ucuz alt dize sondası (sözlükteki iki aşamalı desenin aynısı)
  ve Türkçe karakter sondası ile 13.4 sn → **9.4 sn**, sonuçlar birebir aynı.
- **Consequence:** `jobmeta.py` çıkarım mantığıdır, önbellek parmak izine
  eklendi (D-028).

---

## D-033 — Asgari maaş filtresi tek para birimi içinde; kayıtlı aramalar

- **Date:** 2026-07-22
- **Status:** Accepted
- **Decision (a):** Asgari maaş eşiği ancak bir para birimi seçildiğinde
  etkinleşir. Eşik ilanın **alt sınırına** uygulanır.
- **Reason:** Kur çevirisi yapmadan 100.000 USD ile 100.000 TRY
  karşılaştırılamaz; çeviri yapmak D-029'un reddettiği uydurma sayıyı üretir.
  Alt sınır seçildi çünkü "en az 80.000" diyen kullanıcıya aralığı 60–120 bin
  olan ilanı göstermek, ona 80 bin garanti edilmiş izlenimi verirdi.
- **Decision (b):** Kullanıcı kurduğu aramayı adıyla kaydedip tek tıkla geri
  getirebilir. Ad, filtrelerden otomatik önerilir ("uzaktan · kıdemli").
- **Neden `localStorage`:** Bunlar kariyer verisi değil arayüz tercihi; profil
  veritabanına tablo eklemek orantısız olurdu. Eski kayıtlarda bulunmayan
  alanlar geri yüklenirken varsayılana düşer — yoksa yeni bir filtre
  eklendiğinde eski kayıtlar `undefined` yazardı.

---

## D-034 — "Neyi eklersem kaç ilan açılır": ölçülmüş profil önerileri

- **Date:** 2026-07-22
- **Status:** Accepted
- **Context:** Ölçüldü: ilanların **%68'i** (3026/4395) bant alamıyor. İnceleme
  bunun bir hata **olmadığını** gösterdi — değerlendirilemeyen 3026 ilanın
  hepsinde şart çıkarılmış durumda; bant yokluğu D-019/D-021/D-022'nin doğru
  çalışmasından geliyor:
  - "Legal Professionals — Labor Law" → tek şart "İngilizce" (ayırt edici
    değil, D-021) → bant yok.
  - "Trendyol Express Dağıtım Merkezi" → Excel, Kurye, Vardiya → profilde yok
    → hepsi `unknown` → değerlendirilecek kanıt yok.
- **Asıl eksik mantıkta değil, yönlendirmede:** Kullanıcıya 3026 ilanlık bir
  yığın gösterip "değerlendiremedik" demek, elimizde çözüm varken onu
  göstermemek. Hangi alanın kaç ilanı açacağı **hesaplanabilir**.
- **Decision:** `/api/profile/unlock-suggestions` her aday alan için, o alan
  eklendiğinde bant alabilecek satır sayısını ölçer; arayüz bunları sayaçlı
  gösterir ve tek tıkla profile ekletir.
- **Sayım birimi satırdır, ilan değil:** İlan sayınca "+327" diyip 295 açıldı
  (%10 abartı) — D-030'da düzeltilen hatanın aynısı. Liste aynı işverenin aynı
  rolünü tek satıra indirdiği için sayım da satır üzerinden yapılır. Düzeltme
  sonrası sapma **%1–3** (297 iddia → 295 gerçek).
- **Kalan sapma dürüstçe etiketlenir:** Aynı rol hem değerlendirilen hem
  değerlendirilemeyen listede temsil edilebiliyor. Tam kesinlik her aday alan
  için korpusu yeniden değerlendirmeyi gerektirir (~9 sn); bir yönlendirme
  paneli için orantısız. Arayüz "≈+300" yazar — olmayan bir kesinlik iddia
  etmez.
- **Gruplama kuralı tek yerde (`_role_key`):** Gösterim birleştirmesi ve sayım
  aynı fonksiyonu kullanır. İki yerde ayrı yazılsaydı biri değişince diğeri
  sessizce sapardı ve sonuç yine yanlış sayı olurdu.
- **D-013/D-006 korunur:** Yasal uygunluk alanları profile yazılamadığı için
  önerilmez de — tıklanamayacak bir öneri göstermek olurdu. Test bunu her
  önerinin gerçekten eklenebildiğini deneyerek doğrular.
- **Denetlenebilirlik:** `test_adding_a_suggested_field_actually_unlocks_listings`
  iddianın kendisini test eder: "+N" dedikten sonra değerlendirilemeyen sayısı
  gerçekten düşmeli, iddia gerçekleşenden düşük olmamalı ve sapma %15'i
  geçmemeli.

---

## D-035 — İlanın **yaşı** ile **canlılığı** ayrı şeylerdir

- **Date:** 2026-07-22
- **Status:** Accepted
- **Nasıl bulundu:** Kullanıcı, tekrar tespiti için gereken geçmişi
  biriktirmek üzere bilgisayarı sürekli açık tutamayacağını söyledi. Bunun
  üzerine "geçmiş biriktirmeden bugün elde edilebilecek bir sinyal var mı"
  diye bakıldı — ve veri en baştan beri oradaydı.
- **Bulunan hata:** Greenhouse adapter'ı `posted_at` alanını **`updated_at`**
  değerinden dolduruyordu. `updated_at` ilan her düzenlendiğinde yenilenir;
  `first_published` ise gerçek yayın tarihidir ve API onu da veriyor.
- **Ölçüm (12 Greenhouse panosu, 1980 ilan):**
  - İki tarihin farklı olduğu ilan: **%79**
  - Gizlenen gün, medyan: **60**; en uç örnek: **1920 gün** (5+ yıl)
  - 45 günlük tazelik eşiğini aşan ama "taze" görünen: **%45**
- **Neden ciddi:** Kullanıcının açık isteği "geçmiş işler çıkmasın"dı (D-024).
  Korpusun çoğunluğu Greenhouse olduğu için bu söz tutulmuyordu. Dahası
  araştırmanın en sık şikâyeti olan **hayalet ilan**ı ifşa etmek yerine
  büyütüyorduk: 96 gündür açık bir ilana "5 gün önce" diyorduk.
- **Decision:** İki kavram ayrılır ve ikisi de saklanır.
  - `posted_at` = gerçek ilk yayın. **Yaş** bundan hesaplanır ve kullanıcıya
    gösterilir ("96 gündür açık").
  - `refreshed_at` = kaynağın son güncellemesi. **Eleme** bundan yapılır.
- **Neden eleme yaşa bağlanmadı:** Yaşa bağlansaydı, açık olduğunu
  *bildiğimiz* ilanların %45'i gizlenirdi — ATS onları hâlâ listeliyor, yani
  başvurulabilirler. Kullanıcıya yardım değil, fırsat saklamak olurdu. Doğru
  davranış: göstermek ama yaşını **açıkça** söylemek. Karar kullanıcının,
  bilgi bizim sorumluluğumuz.
- **Arayüz:** 45 günü aşan ilanlarda "N gündür açık" rozeti ve isteğe bağlı
  "uzun süredir açıkları gizle" filtresi. Rozet, son güncelleme tarihini de
  ipucu olarak taşır.
- **Yan bulgu:** Lever ve Ashby'nin `workplaceType` alanı adapter tarafından
  yakalanıyor ama **hiç kullanılmıyordu**; jobmeta regex'le tahmin ediyordu.
  Kaynağın kendi beyanı artık önceliklidir — tahmin yalnızca beyan yokken
  devreye girer.
- **Lever tuzağı:** Lever tarihleri milisaniye epoch verir, ISO dize değil;
  `updatedAt` de `createdAt` gibi dönüştürülmelidir.

---

## D-036 — Çekim mantığının ayrı parmak izi

- **Date:** 2026-07-22
- **Status:** Accepted
- **Context:** D-028 önbelleği **çıkarım** mantığı değiştiğinde geçersiz
  kılıyordu. Ama D-035'te değişen şey adapter'dı — yani **çekim** mantığı.
  Ham kayıtlar önbellekte eski (yanlış) tarihle duruyordu ve düzeltmenin
  hiçbir etkisi görünmeyecekti: tam olarak D-028'in önlemek için yazıldığı
  sessiz bayatlık, bir katman aşağıda.
- **Decision:** `fetch_fingerprint()` — `adapters/` dosyalarının hash'i.
  Değişirse **ham** kayıtlar geçersizdir ve yeniden çekim yapılır.
- **İki parmak izi bağımsızdır ve olması gereken budur:** çıkarım değişimi
  yeniden çekim gerektirmez (43 sn), çekim değişimi gerektirir (~195 sn).
  Tek parmak iziyle her sözlük değişikliği 151 panoyu yeniden çekerdi.
- **Denetlenebilirlik:** `test_changed_fetch_logic_invalidates_raw_records`
  ve `test_fetch_and_extraction_fingerprints_are_independent`.

---

## D-037 — Kıdem: ikili senior/entry yerine 7 basamaklı merdiven

- **Date:** 2026-07-22
- **Status:** Accepted
- **Context:** Kullanıcı "stajyer, jr, mid, senior, architect" tarzı bir yapı
  istedi. Mevcut sistem yalnızca senior/entry ayırıyordu.
- **Ölçüm (5803 başlık, öncelik çözümlü):** intern %1, junior %0.5, mid %1,
  senior %21, lead %11, architect %1, executive %6, **belirtilmemiş %55**.
- **Decision:** `experience_level` yedi basamak döner: `intern`, `junior`,
  `mid`, `senior`, `lead`, `architect`, `executive`. Yalnızca başlıktan,
  öncelik sırasıyla (ilk eşleşen kazanır).
- **"mid" pozitif olarak çıkarılamaz:** Korpusun %55'i işaretsiz. "Software
  Engineer" seviye söylemez. Bu %55'i "mid" saymak, projenin her yerde
  kaçındığı fazla iddiadır (D-011). `mid` yalnızca **açık** işaretle
  ("mid-level", "II", "intermediate") atanır; kalan çoğunluk kendi sayaçlı
  "belirtilmemiş" grubunda kalır.
- **Öncelik sırası neden böyle:**
  - Giriş işaretleri (stajyer/junior) en tepede: iş arayan için belirleyici ve
    üst basamaklarla neredeyse hiç birlikte geçmezler. "Junior Staff Accountant"
    → junior (kullanıcı giriş rolü arıyor).
  - Üst basamaklar arasında en yüksek kazanır: "Senior Director" → executive,
    "Senior Staff Engineer" → lead, "Senior Solutions Architect" → architect.
  - `manager` merdivende **yok** (D-032 dersi): rol türüdür, dahil edilince
    korpusun yarısı "kıdemli" görünüyordu.
  - `lead` "Lead Generation Specialist"ten ayrılır (satış rolü).
- **Kaynağın beyanı öncelikli:** Lever/Ashby `workplaceType` alanı çalışma
  biçimi için zaten kullanılıyordu (D-035); kıdem başlıktan okunur çünkü ATS'ler
  seviye için yapısal alan vermiyor.
- **Arayüz:** Filtre çubuğunda 7 basamak + belirtilmemiş, her biri sayaçlı.
  Kartlarda kıdem rozeti (belirtilmemiş gösterilmez — yer kaplar, bilgi
  taşımaz). İş tanımının tam metni zaten detay görünümünde yapılandırılmış
  gösteriliyordu (başlık→alt başlık, madde listesi).
