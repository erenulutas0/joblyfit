# GLOSSARY.md — Terminology Sözlüğü

> **Purpose:** Projedeki bütün dokümanların ve (ileride) kodun kullanacağı terimlerin tek
> tanım kaynağı. Bir terim burada nasıl yazılıyorsa her yerde öyle kullanılır. Yeni terim
> ekleme kuralı: önce buraya tanımını ekle, sonra dokümanlarda kullan.

## Kullanıcı Tarafı

| Terim | Tanım |
|---|---|
| **Career Profile** | Kullanıcının structured profili: education, work experience, skills, certifications, professional licenses, languages, portfolio, preferences ve occupation-specific qualification'ların tamamı. CV'den parse edilebilir veya manuel oluşturulabilir. |
| **CV Parsing** | Yüklenen CV dosyasından Career Profile alanlarının otomatik çıkarılması. Sonuç her zaman kullanıcı doğrulamasından geçer (bkz. Profile Verification). |
| **Profile Verification** | Profil alanının kullanıcı tarafından kontrol edilip onaylanması. Doğrulanmamış alan düşük confidence ile işlenir; **gate-relevant alanlarda doğrulama zorunludur** ve olmadan hard requirement `met` sayılmaz (D-012). |
| **Profile Completeness Score** | Career Profile'ın, kullanıcının occupation'ı için gereken alanların ne kadarını doldurduğunu gösteren skor. *V1 kapsamındadır (F-19); MVP'de eksik bilgi `unknown` requirement açıklamasıyla bildirilir.* |
| **Preference** | Kullanıcının iş **tercihi**: preferred location, salary expectation, work type, shift preference, sector vb. Qualification değildir; uyumsuzluğu sıralamayı düşürür, eleme üretmez. **Capability constraint'ten farklıdır** ("gece çalışamam" bir yapabilirlik kısıtıdır ve gate olabilir — [MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md) §1.2). |
| **Feedback Signal** | Kullanıcının sisteme verdiği açık veya örtük sinyal: saved, not interested, applied, report, dwell/skip. Matching kişiselleştirmesinde kullanılır. |
| **Job Feed** | Kullanıcıya özel sıralı ilan listesi. Sıralama tabanı Match Score'dur; üzerine freshness ve kişiselleştirme re-ranking'i uygulanır ([MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md) §4.1). |
| **Digest** | Yeni eşleşen ilanların özeti. **MVP'de sabit haftalık e-posta + opt-out**; frekans/kanal seçimi V1'dedir (D-016). |

## İlan ve Ingestion Tarafı

| Terim | Tanım |
|---|---|
| **Job Source** | İlan alınan herhangi bir kaynak: job board, company career page, ATS-powered career page, recruitment agency page, government portal, university career portal, sector-specific source. |
| **Source Registry** | Bütün Job Source'ların kayıt, policy, health ve quality bilgilerini tutan merkezi katalog. |
| **Source Record** | Source Registry'deki tek bir source'un kaydı (şablon: [SOURCE_REGISTRY.md](../architecture/SOURCE_REGISTRY.md)). |
| **Source Adapter** | Belirli bir source'tan veri almayı bilen, source'a özgü mantığı izole eden bileşen. Adapter çökerse yalnızca kendi source'u etkilenir (Source Isolation). |
| **Ingestion Pipeline** | Fetch → parse → **normalize → extract** → dedupe → validate → store zincirinin tamamı. Requirement extraction ayrı bir alt sistem değil, normalize adımının parçasıdır; store'a iki fazlı yazma uygulanır ([ARCHITECTURE.md](../architecture/ARCHITECTURE.md) → Akış A). |
| **Raw Job Document** | Source'tan alınmış, henüz işlenmemiş ham içerik (HTML/JSON/feed). |
| **Job Posting** | Normalize edilmiş, platform şemasına oturtulmuş tek iş ilanı kaydı. |
| **Canonical Job Posting** | Duplicate Detection sonrası, aynı gerçek ilanı temsil eden kayıtların bağlandığı tekil temsilci kayıt. Kullanıcı feed'inde bu gösterilir. |
| **Duplicate Cluster** | Aynı gerçek ilana ait Job Posting'lerin kümesi; bir Canonical Job Posting'e bağlıdır. |
| **Provenance** | Bir Job Posting'in nereden, ne zaman, hangi adapter/parser versiyonuyla alındığının kaydı. |
| **Freshness Score** | İlanın güncellik değerlendirmesi (yayın tarihi, son doğrulama zamanı, source'un güncelleme davranışı üzerinden). |
| **Expired Posting** | Yayından kalktığı tespit edilen veya ömrünü doldurduğu değerlendirilen ilan; feed'den çıkarılır ama provenance ile arşivlenir. |
| **Crawl** | Bir source'un planlı olarak taranması (Crawl Scheduler tarafından tetiklenir). |
| **Source Isolation** | Bir source'un arızasının/politika değişikliğinin diğer source'ları ve sistemin geri kalanını etkilememesi ilkesi. |
| **Manual Review Queue** | İnsan kararı gerektiren kayıtların kuyruğu. **MVP'de minimal mod**: yalnızca altı tanımlı tetikleyici, ~2 saat/hafta kapasite, SLA hedefi yok ([SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md) §5.2, D-014). |

## Taxonomy ve Matching Tarafı

| Terim | Tanım |
|---|---|
| **Occupation Taxonomy** | Meslekleri, aralarındaki ilişkileri ve her mesleğin qualification yapısını tanımlayan merkezi model. |
| **Occupation** | Taxonomy'deki tek meslek düğümü (ör. Registered Nurse, Heavy Vehicle Driver). |
| **Occupation Profile** | Bir Occupation'ın qualification template'i: hangi qualification türleri zorunlu/tipik/tercihen beklenir. |
| **Qualification** | İş için değerlendirilebilir nitelik: skill, education, certification, professional license, language, portfolio, experience vb. |
| **Hard Requirement** | Karşılanmadığında başvurunun gerçekçi olmadığı şart (ör. zorunlu professional license, yasal çalışma izni). Üç durumlu değerlendirilir (bkz. Requirement State); `unmet` gizlenmez, `unknown` eleme sebebi değildir. İki kaynağı vardır: ilan extraction'ı ve regulated occupation kuralı ([OCCUPATION_TAXONOMY.md](../architecture/OCCUPATION_TAXONOMY.md) §3). |
| **Required Qualification** | İlanın açıkça zorunlu tuttuğu qualification. |
| **Preferred Qualification** | İlanın "tercih sebebi" saydığı qualification. |
| **Professional License** | Devlet/meslek kuruluşunca verilen, regulated profession'da çalışma yetkisi (ör. hemşirelik lisansı, ehliyet kategorisi). Certification'dan farklıdır. |
| **Certification** | Kurum/kuruluş sertifikası (ör. CPA, AWS certification, kaynakçılık sertifikası). Yasal zorunluluk olmayabilir. |
| **Regulated Profession** | Yasal olarak license/yetki belgesi şartı bulunan meslek. Regulation **jurisdiction ve bağlam bağımlıdır** (aynı meslek bir pazarda/bağlamda regulated olabilir, başkasında olmayabilir). Eksik **veya doğrulanmamış** license kullanıcıya açıkça bildirilir. |
| **Matching Engine** | Career Profile ile Job Posting'leri karşılaştırıp skor, sıralama ve explanation üreten sistem. |
| **Matching Factor** | Matching'de ayrı değerlendirilen tek boyut. Tam liste ve **MVP/V1 sınıflandırması**: [MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md) §2. MVP'de ~8 structured faktör + sınırlı semantic reranking (D-017). |
| **Match Score** | Bir Job Posting'in kullanıcıya uygunluğunun toplam skoru. **Tahmindir; kesinlik veya işe alım garantisi değildir** ve kullanıcıya da böyle sunulur. |
| **Match Confidence** | Skorun dayandığı verinin kalitesine/eksiksizliğine göre sistemin kendi tahminine güveni. Score'dan ayrı bir boyuttur. |
| **Match Explanation** | Önerinin gerekçesi: neden uygun; karşılanan, karşılanmayan ve **değerlendirilemeyen (`unknown`)** requirement'lar; başvurmaya değer mi. Her iddia evidence taşır. CV iyileştirme önerileri V1'dedir (F-20). |
| **Career Transition** | Kullanıcının mevcut occupation'ından, transferable skill'ler üzerinden gerçekçi biçimde geçebileceği yakın occupation önerisi. |
| **Transferable Skill** | Birden çok occupation'da geçerli qualification (ör. müşteri iletişimi, ekip yönetimi, forklift kullanımı). |
| **Sensitive Attribute** | Matching'de kullanılması yasak **ve** çoğu hiç saklanmayan kişisel özellik: age/full birth date, gender, photo, ethnicity, religion, marital status, health information, union membership (politika: [MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md) → Fairness Constraints; saklama: D-006). |
| **Legal Eligibility Requirement** | İlan tarafındaki yasal/policy şartı (ör. yaş sınırı, askerlik durumu, zorunlu sağlık belgesi). Sensitive Attribute'tan **farklıdır**: Match Score'a girmez, kullanıcıya bilgilendirme olarak gösterilir ve kaynağa yönlendirilir (D-013). |
| **Requirement State** | Bir requirement'ın değerlendirme sonucu: `met` (karşılanıyor), `unmet` (karşılanmıyor), `unknown` (değerlendirilemedi — profilde veri yok veya gate-relevant alan doğrulanmamış). Profilde bilgi olmaması `unmet` değil `unknown`'dır (D-011). |
| **Verification State** | Bir profil alanının doğrulama durumu: `unverified` (parse edildi, onaylanmadı), `user_asserted` (kullanıcı beyan etti/onayladı), `verified` (gate-relevant alan için gereken teyit tamamlandı). |
| **Gate-relevant Field** | `verified` olmadan hiçbir hard requirement'ı `met` yapamayan alan: professional license (ehliyet kategorisi dahil), work authorization, yasal zorunlu sertifika, country-specific professional authorization (D-012). |
| **Support Tier** | Bir occupation'ın MVP'deki destek derinliği: `first-class` (template + kalibre ağırlık + golden set), `generic` (jenerik ağırlık + coverage limitation açıklaması), `limited` (listelenir, otomatik öneri yok), `listing-only` (public sector; Match Score üretilmez). Tanım: [OCCUPATION_TAXONOMY.md](../architecture/OCCUPATION_TAXONOMY.md) §2.5. |
| **Coverage Limitation** | First-class olmayan bir occupation'ın kullanıcısına gösterilen, eşleştirmenin genel değerlendirmeye dayandığını sade dille açıklayan not (D-008). |
| **Employer** | Normalize edilmiş işveren kimliği: canonical ad + alias'lar + ATS domain eşlemeleri. Duplicate blocking, cluster temsilci seçimi ve "işverenimden gizle" bu çözünürlüğe bağımlıdır ([DATA_MODEL.md](../architecture/DATA_MODEL.md) → Employer). |
| **Sector / Industry** | İşin ait olduğu ekonomik faaliyet alanı (ör. perakende, sağlık, lojistik). Occupation'dan farklıdır: occupation *ne iş yaptığını*, sector *hangi alanda yaptığını* söyler. Normalize sektör sözlüğünün sahibi Normalizer'dır ([SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md) §3). |
| **Seniority** | Aynı occupation içindeki deneyim/rol düzeyi. **Ayrı occupation node'u açılmaz**; ilan tarafında `min_years`/`level`, kullanıcı tarafında iş geçmişi süresinden türetilir ([OCCUPATION_TAXONOMY.md](../architecture/OCCUPATION_TAXONOMY.md) §3). |
| **Golden Set** | Matching kalitesini offline ölçmek için insan-etiketli profil×ilan test seti; dört etiket katmanı içerir (match/sıralama, requirement, occupation, CV alanı). Kalite kapılarının dayanağıdır ([TEST_STRATEGY.md](../quality/TEST_STRATEGY.md) §3). |
| **Evidence** | Bir iddianın dayandığı kaynak referansı: ilan metnindeki kısa alıntı (`source_span`), profil alanı veya structured data alanı. Explanation'daki her iddia en az bir evidence taşımak zorundadır (D-005). |
| **Sensitive Data Vault** | Tanımlı `purpose` ve `consent_ref` bulunan sensitive alanlar için ayrılmış, matching veri yoluna kapalı saklama alanı. **Varsayılan saklama yeri değildir ve MVP'de kullanılmaz** (D-006). |
| **Data Quality Score** | Source başına kalite bileşimi (zorunlu alan doluluğu + validation geçme oranı + field accuracy). Formülün sahibi [METRICS.md](METRICS.md) → Ölçüm Tanımları; Source Registry yalnızca değeri tutar. |
| **Repost** | Expire olduktan sonra yeniden yayınlanan ilan. Yeni cluster açar ama `repost_of` ile eski cluster'a bağlanır. |
| **Crawl Scheduler** | Source Registry'deki aktif source'lar için crawl planını üreten bileşen (frekans, öncelik, yük dağılımı). |

## Süreç Terimleri

| Terim | Tanım |
|---|---|
| **Assumption** | Doğrulanmamış, açıkça işaretlenmiş varsayım (ana liste: [PRD.md](PRD.md)). Confirmed decision değildir. |
| **Decision** | [DECISIONS.md](../../DECISIONS.md) veya ADR ile kayıt altına alınmış karar. |
| **Open Question** | `❓ OPEN-NN:` işaretiyle gösterilen, cevabı beklenen soru. Bütün açık soruların envanteri [CONTEXT.md](../../CONTEXT.md) → Open Question Index'tedir; sahibi dosyada işaret, envanterde satır bulunur. |
| **ADR** | Architecture Decision Record ([docs/adr/README.md](../adr/README.md)). |
| **MVP / V1 / Future** | Scope katmanları; tanımları [PRD.md](PRD.md) dosyasındadır. |
