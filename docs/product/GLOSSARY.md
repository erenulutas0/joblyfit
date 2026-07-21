# GLOSSARY.md — Terminology Sözlüğü

> **Purpose:** Projedeki bütün dokümanların ve (ileride) kodun kullanacağı terimlerin tek
> tanım kaynağı. Bir terim burada nasıl yazılıyorsa her yerde öyle kullanılır. Yeni terim
> ekleme kuralı: önce buraya tanımını ekle, sonra dokümanlarda kullan.

## Kullanıcı Tarafı

| Terim | Tanım |
|---|---|
| **Career Profile** | Kullanıcının structured profili: education, work experience, skills, certifications, professional licenses, languages, portfolio, preferences ve occupation-specific qualification'ların tamamı. CV'den parse edilebilir veya manuel oluşturulabilir. |
| **CV Parsing** | Yüklenen CV dosyasından Career Profile alanlarının otomatik çıkarılması. Sonuç her zaman kullanıcı doğrulamasından geçer (bkz. Profile Verification). |
| **Profile Verification** | CV parsing çıktısının kullanıcı tarafından kontrol edilip düzeltilmesi adımı. Doğrulanmamış alan matching'de düşük confidence ile işlenir. |
| **Profile Completeness Score** | Career Profile'ın, kullanıcının occupation'ı için gereken alanların ne kadarını doldurduğunu gösteren skor. |
| **Preference** | Kullanıcının iş tercihi: preferred location, salary expectation, work type (remote/hybrid/on-site), shift preference, sector vb. Qualification değildir; eksikliği eleme sebebi olmaz. |
| **Feedback Signal** | Kullanıcının sisteme verdiği açık veya örtük sinyal: saved, not interested, applied, report, dwell/skip. Matching kişiselleştirmesinde kullanılır. |
| **Job Feed** | Kullanıcıya özel, Match Score'a göre sıralanmış ilan listesi. |
| **Digest** | Yeni eşleşen ilanların günlük/haftalık özeti (notification kanalıyla iletilir). |

## İlan ve Ingestion Tarafı

| Terim | Tanım |
|---|---|
| **Job Source** | İlan alınan herhangi bir kaynak: job board, company career page, ATS-powered career page, recruitment agency page, government portal, university career portal, sector-specific source. |
| **Source Registry** | Bütün Job Source'ların kayıt, policy, health ve quality bilgilerini tutan merkezi katalog. |
| **Source Record** | Source Registry'deki tek bir source'un kaydı (şablon: [SOURCE_REGISTRY.md](../architecture/SOURCE_REGISTRY.md)). |
| **Source Adapter** | Belirli bir source'tan veri almayı bilen, source'a özgü mantığı izole eden bileşen. Adapter çökerse yalnızca kendi source'u etkilenir (Source Isolation). |
| **Ingestion Pipeline** | Fetch → parse → extract → normalize → dedupe → validate → store zincirinin tamamı. |
| **Raw Job Document** | Source'tan alınmış, henüz işlenmemiş ham içerik (HTML/JSON/feed). |
| **Job Posting** | Normalize edilmiş, platform şemasına oturtulmuş tek iş ilanı kaydı. |
| **Canonical Job Posting** | Duplicate Detection sonrası, aynı gerçek ilanı temsil eden kayıtların bağlandığı tekil temsilci kayıt. Kullanıcı feed'inde bu gösterilir. |
| **Duplicate Cluster** | Aynı gerçek ilana ait Job Posting'lerin kümesi; bir Canonical Job Posting'e bağlıdır. |
| **Provenance** | Bir Job Posting'in nereden, ne zaman, hangi adapter/parser versiyonuyla alındığının kaydı. |
| **Freshness Score** | İlanın güncellik değerlendirmesi (yayın tarihi, son doğrulama zamanı, source'un güncelleme davranışı üzerinden). |
| **Expired Posting** | Yayından kalktığı tespit edilen veya ömrünü doldurduğu değerlendirilen ilan; feed'den çıkarılır ama provenance ile arşivlenir. |
| **Crawl** | Bir source'un planlı olarak taranması (Crawl Scheduler tarafından tetiklenir). |
| **Source Isolation** | Bir source'un arızasının/politika değişikliğinin diğer source'ları ve sistemin geri kalanını etkilememesi ilkesi. |
| **Manual Review Queue** | Otomatik işlenemeyen veya kullanıcı tarafından raporlanan kayıtların insan incelemesine düştüğü kuyruk. |

## Taxonomy ve Matching Tarafı

| Terim | Tanım |
|---|---|
| **Occupation Taxonomy** | Meslekleri, aralarındaki ilişkileri ve her mesleğin qualification yapısını tanımlayan merkezi model. |
| **Occupation** | Taxonomy'deki tek meslek düğümü (ör. Registered Nurse, Heavy Vehicle Driver). |
| **Occupation Profile** | Bir Occupation'ın qualification template'i: hangi qualification türleri zorunlu/tipik/tercihen beklenir. |
| **Qualification** | İş için değerlendirilebilir nitelik: skill, education, certification, professional license, language, portfolio, experience vb. |
| **Hard Requirement** | Karşılanmadığında başvurunun gerçekçi olmadığı şart (ör. zorunlu professional license, yasal çalışma izni, ilan dilinde asgari yeterlilik). Eksikliği gizlenmez, açıkça gösterilir. |
| **Required Qualification** | İlanın açıkça zorunlu tuttuğu qualification. |
| **Preferred Qualification** | İlanın "tercih sebebi" saydığı qualification. |
| **Professional License** | Devlet/meslek kuruluşunca verilen, regulated profession'da çalışma yetkisi (ör. hemşirelik lisansı, ehliyet kategorisi). Certification'dan farklıdır. |
| **Certification** | Kurum/kuruluş sertifikası (ör. CPA, AWS certification, kaynakçılık sertifikası). Yasal zorunluluk olmayabilir. |
| **Regulated Profession** | Yasal olarak license/yetki belgesi şartı bulunan meslek. Bu alanlarda eksik license kullanıcıya açıkça bildirilir. |
| **Matching Engine** | Career Profile ile Job Posting'leri karşılaştırıp skor, sıralama ve explanation üreten sistem. |
| **Matching Factor** | Matching'de ayrı değerlendirilen tek boyut (ör. skill compatibility, location, shift availability). Tam liste: [MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md). |
| **Match Score** | Bir Job Posting'in kullanıcıya uygunluğunun toplam skoru. **Tahmindir; kesinlik veya işe alım garantisi değildir** ve kullanıcıya da böyle sunulur. |
| **Match Confidence** | Skorun dayandığı verinin kalitesine/eksiksizliğine göre sistemin kendi tahminine güveni. Score'dan ayrı bir boyuttur. |
| **Match Explanation** | Önerinin gerekçesi: neden uygun, hangi requirement'lar karşılanıyor/eksik, başvurmaya değer mi, CV'de ne iyileştirilebilir. |
| **Career Transition** | Kullanıcının mevcut occupation'ından, transferable skill'ler üzerinden gerçekçi biçimde geçebileceği yakın occupation önerisi. |
| **Transferable Skill** | Birden çok occupation'da geçerli qualification (ör. müşteri iletişimi, ekip yönetimi, forklift kullanımı). |
| **Sensitive Attribute** | Matching'de kullanılması yasak kişisel özellik: age, gender, photo, ethnicity, religion, marital status ve işle doğrudan ilgili olmayan benzerleri (politika: [MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md) → Fairness Constraints). |

## Süreç Terimleri

| Terim | Tanım |
|---|---|
| **Assumption** | Doğrulanmamış, açıkça işaretlenmiş varsayım (ana liste: [PRD.md](PRD.md)). Confirmed decision değildir. |
| **Decision** | [DECISIONS.md](../../DECISIONS.md) veya ADR ile kayıt altına alınmış karar. |
| **Open Question** | `❓ OPEN:` işaretiyle gösterilen, cevabı beklenen soru. |
| **ADR** | Architecture Decision Record ([docs/adr/README.md](../adr/README.md)). |
| **MVP / V1 / Future** | Scope katmanları; tanımları [PRD.md](PRD.md) dosyasındadır. |
