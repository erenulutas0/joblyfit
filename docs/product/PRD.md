# PRD.md — Product Requirements Document (Scope)

> **Purpose:** Ürün scope'unun tek sahibi: Assumptions, MVP / V1 / Future scope ve
> explicitly excluded features. Vision ve capability tanımları [PRODUCT.md](PRODUCT.md);
> detaylı requirement'lar [REQUIREMENTS.md](REQUIREMENTS.md); zaman planı
> [ROADMAP.md](ROADMAP.md).

## Assumptions

> Aşağıdakiler **doğrulanmamış varsayımlardır**, gerçek bilgi değildir. Her biri
> doğrulanana kadar tasarım bunlara dayanır; yanlışlanan assumption ilgili dokümanlarda
> revizyon gerektirir.

| # | Assumption | Etkisi | Doğrulama yolu |
|---|---|---|---|
| ~~A-1~~ | ~~Ürün tek bir launch pazarında başlayacak; pazar henüz seçilmedi.~~ | — | **Kapandı: D-009 — Türkiye seçildi (2026-07-21).** Core architecture market-neutral kalır. |
| A-2 | Hedef kitlenin önemli bölümü mobile-first; blue-collar segmentte masaüstü erişimi sınırlı. | UX önceliği, kısa akışlar | Saha görüşmeleri (**T-022**) |
| A-3 | Türkiye'de yeterli sayıda compliant (API'li, feed'li veya scraping'e izinli) job source mevcut. | Ingestion kapsamı | Source landscape (T-003) + **coverage validation (T-021)** |
| A-4 | Kullanıcılar CV'lerinin parse edilmesine, sonucu doğrulayabildikleri sürece olumlu yaklaşır. | Onboarding tasarımı | **CV-vs-manuel tercih validation (T-026)** |
| A-5 | Business model MVP'de gelir hedeflemez; iş arayana ücretsizdir. Gelir modeli (V1+ için employer-side veya premium) sonra kararlaştırılır. | Feature önceliği, employer tarafının excluded olması | ❓ OPEN-16 — kullanıcı kararı |
| A-6 | ESCO veya O*NET benzeri açık taxonomy, Türkiye'nin meslekleri için yeterli çekirdek sağlar; lokal meslekler extension ile eklenebilir. | Taxonomy stratejisi (D-004) | Taxonomy pilot (T-004, T-005) + **mini golden dataset (T-025)** |
| A-7 | İlan metinlerinden requirement extraction, AI destekli yöntemlerle kullanılabilir doğrulukta yapılabilir; hata payı confidence + explanation ile yönetilebilir. | Matching kalitesi | Golden set ölçümü (T-006) + **inter-annotator agreement (T-025)** |
| A-8 | Application tracking MVP'de kullanıcı beyanına dayanır (platform dışında yapılan başvurunun otomatik takibi mümkün değildir). | Feature tasarımı | — (yapısal kısıt) |
| A-9 | Explainable Match Score kullanıcı güvenini ve karar netliğini **artırır**; hatalı bir explanation güveni tümden bozmaz. | D-005'in değer gerekçesi; explanation UI yatırımı | **Wizard-of-Oz explanation validation (T-023)** |
| A-10 | Kullanıcılar mevcut platformlar dururken bu ürünü tercih eder (switching nedeni gerçektir). | Ürünün var olma gerekçesi; konumlandırma | **User interview + problem validation (T-022)** |
| A-11 | Recommendation kalitesi haftalık geri dönüş üretir (retention motorudur). | Retention hedefleri, digest tasarımı | **Concierge recommendation validation (T-024)** |
| A-12 | Kullanıcılar ranking'i etkileyecek hacimde feedback verir. | F-11/F-17, MF-19, M5 kriteri | T-024 içinde ölçülür |
| A-13 | Haftalık e-posta digest, hedef segmentte (mobile-first blue-collar) yeterli re-engagement üretir. | D-016 notification kararı | **Notification channel validation (T-027)** |

> **Not (A-9…A-13):** Bu beş varsayım 2026-07-21 audit'inde eksik tespit edildi (talep
> tarafı boşluğu). D-010 uyarınca hepsi M1 validation gate'ine bağlanmıştır; eşik
> değerleri **calibration target**'tır, kesin bilimsel eşik değildir.

## Scope Katmanları

Tanım: **MVP** = core loop'un uçtan uca, dar kapsamda çalıştığı ilk sürüm. **V1** = halka
açık, güvenle büyütülebilir sürüm. **Future** = yön olarak benimsenmiş ama planlanmamış.
Feature numaraları, ana feature listesine (bu bölümdeki F-kodları) referanstır.

### MVP Scope

**Karar: D-008 — "Three Cluster Thesis Probe".** Hedef: **Türkiye pazarında (D-009),
2-3 compliant source ve 3 cluster / ~6 first-class occupation** üzerinde
"profil → ingestion → matching → explainable feed → feedback" döngüsünü kanıtlamak.

#### MVP Occupation Kapsamı

| Cluster | First-class occupation'lar | Neden bu cluster |
|---|---|---|
| Logistics & Operations | Driver, Warehouse Worker | Blue-collar tezi; license kategorisi + lokasyon + vardiya |
| Office & Commercial | Accountant, Sales Representative | White-collar; certification + sektör deneyimi + yazılım |
| Healthcare | Nurse, Health Technician | Regulated profession; license gate + department + shift |

**"First-class" ne demek:** yalnızca bu altı occupation, occupation-specific taxonomy,
qualification template, kalibre edilmiş matching ağırlıkları ve golden dataset desteği
alır. **Platform vision universal kalır** — diğer occupation'lar yasaklı değildir;
generic matching ile çalışır, ancak düşük Match Confidence ve açık **coverage
limitation** açıklaması gösterilir
([OCCUPATION_TAXONOMY.md](../architecture/OCCUPATION_TAXONOMY.md) → Support Tiers).

#### MVP Feature Listesi

| # | Feature | MoSCoW | Karşılığı | Not |
|---|---|---|---|---|
| F-01 | User onboarding | Must | FR-101…106 | Kısa, mobile-uyumlu; occupation seçimi dahil |
| F-02 | CV upload and parsing | Must | FR-101 | **Tek format (PDF) + tek dil (TR); OCR yok** — kapsam matrisi [AI_SYSTEM.md](../architecture/AI_SYSTEM.md) §1.1 |
| F-03 | Manual career profile editor | Must | FR-102 | CV'siz kullanıcılar için eşdeğer yol |
| F-04 | Profile verification and correction | Must | FR-103, FR-107 | Gate-relevant alanlarda **doğrulama zorunlu** (D-012) |
| F-05 | Profession and occupation selection | Must | FR-104, FR-301 | Taxonomy'den seçim + serbest metin fallback |
| F-06 | Career preference configuration | Must | FR-106 | Location, salary, work type, shift |
| F-07 | Personalized job feed | Must | FR-501 | Match Score + Match Explanation ile |
| F-08 | Search and basic filters | Must | FR-502 | **Keyword + location'a indirgendi**; sahibi Feed & Search Service |
| F-09 | Explainable job recommendations | Must | FR-404, FR-405 | D-005 gereği MVP'nin çekirdeği; `unknown` durumu dahil (D-011) |
| F-10 | Saved jobs | Must | FR-503 | |
| F-11 | Not interested feedback | Must | FR-503, FR-406 | Sıralamaya etki eder |
| F-12 | Applied jobs tracking | Must | FR-503 | Kullanıcı beyanlı (A-8) |
| F-14 | Weekly job digest | Must | FR-505 | **Sabit haftalık e-posta + opt-out** (D-016) — frekans/kanal seçimi yok |
| F-16 | Duplicate and expired job handling | Must | FR-206, FR-207 | Ingestion tarafında zorunlu |
| F-23 | User data export and deletion | Must | FR-602, FR-603 | Yasal gereklilik, ertelenemez |
| F-24 | Source transparency | Must | FR-601 | İlanda source + freshness gösterimi |
| F-25 | Report incorrect or expired job | Should | FR-506 | Basit rapor formu → minimal MRQ (D-014) |
| F-26 | Public sector listing-only mode | Must | FR-410 | **Yeni** — Match Score üretilmez, kaynağa yönlendirilir (D-015) |

**MVP'den çıkarılanlar (audit sonrası):** F-19 (Profile completeness score) → V1'e taşındı;
detaylı gerekçe aşağıda "MVP'den V1'e Taşınanlar".

#### MVP'den V1'e Taşınanlar (D-008 daraltması)

| # | Feature | Neden ertelendi |
|---|---|---|
| F-19 | Profile completeness score | Formülü ve hesap sahibi tanımsızdı, FR-105 zaten SHOULD; `unknown` durumu (D-011) kullanıcıya eksik bilgiyi zaten söylüyor — completeness'in MVP'deki işlevini kısmen üstleniyor |

> **MoSCoW ↔ Scope kuralı:** Bir feature MVP listesinde ise karşılığı olan FR'ler
> **Must** olmak zorundadır; Should seviyesindeki bir FR'ye dayanan feature MVP'de
> yer alamaz. Tek istisna F-25 (Should): raporlama akışı MVP'de basit formla karşılanır,
> tam MRQ ürünleşmesi V1'dedir. Bu kural [REQUIREMENTS.md](REQUIREMENTS.md) ile birlikte
> denetlenir.

### V1 Scope

| # | Feature | Not |
|---|---|---|
| F-08+ | Advanced filters | Sektör, seniority, salary aralığı, shift, license kategorisi |
| F-13 | Application status tracking | Kullanıcı beyanlı durum akışı (applied → interview → offer → rejected) |
| F-15 | Notification kişiselleştirme | Frekans **ve** kanal seçenekleri, push/SMS, anlık bildirim, eşik ayarı — **MVP'de hiçbiri yok** (D-016) |
| F-17 | User feedback learning | Feedback'in ranking'e sistematik, ölçülen etkisi (MVP'de basit kural, V1'de öğrenen katman) |
| F-18 | Match preference controls | Kullanıcının faktör ağırlıklarını ayarlaması ("lokasyon benim için kritik") |
| F-19 | Profile completeness score | MVP'den taşındı (D-008); formül ve hesap sahibi V1'de tanımlanır |
| F-20 | Missing qualification recommendations | Eksik certification/license için yol gösterme |
| F-21 | Career transition support | Transferable skill tabanlı yakın meslek önerisi; regulated profession uyarılarıyla |
| F-22 | Multi-language job and CV support | Çok dilli CV/ilan; ikinci pazar açılımıyla birlikte |
| F-26+ | Public sector tam desteği | Sınav puanı/kadro mekaniğinin modellenmesi (OPEN-15); MVP'de listing-only (D-015) |
| — | Semantic katkının genişletilmesi | MVP'de ≤~%10 reranking (D-017); üst sınır golden set ölçümüyle yeniden değerlendirilir |
| — | Source seti genişletme | 15-25 source; source onboarding süreci olgunlaştırılır |
| — | Occupation kapsamı genişletme | 6 → 50+ occupation profile; cluster bazlı büyüme |

### Future Scope

- Employer/recruiter tarafı (ilan verme, aday arama) — A-5 kararına bağlı.
- Kariyer danışmanı / kurum arayüzleri (İŞKUR benzeri kurumlar, üniversite kariyer
  merkezleri).
- Skill gelişim içerik/eğitim sağlayıcılarıyla entegrasyon (missing qualification →
  kurs önerisi).
- Otomatik başvuru desteği (kullanıcı onaylı, platform dışı formlara — compliance
  değerlendirmesiyle).
- Maaş içgörüleri ve pazar analitiği.
- Sesli/asistan tabanlı iş arama deneyimi.

### Explicitly Excluded (bilinçli olarak yapılmayacaklar)

| Excluded | Neden |
|---|---|
| Login wall / CAPTCHA / bot-detection bypass eden her tür ingestion | D-002; hukuki ve etik sınır |
| İzinsiz kaynaklardan scraping | D-002 |
| Sensitive attribute'ların matching'de kullanılması | D-006 |
| Kullanıcı adına habersiz/otomatik başvuru gönderimi | Güven ve hukuki risk; Future'daki otomasyon bile açık onay şartına bağlı |
| CV'deki bilgilerin işverene/üçüncü tarafa kullanıcı onayı olmadan satılması/aktarılması | [PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md) |
| "İşe alım garantisi" veya kesinlik iddiası taşıyan skor sunumu | D-005; Match Score her zaman tahmin olarak sunulur |
| Kendi ATS'imizi yazmak (başvurular platform dışında, ilan sahibinin kanalında yapılır) | MVP/V1 odağı discovery & matching |
| Freelance gig marketplace mekaniği (escrow, milestone ödemeleri) | Freelance *ilanları* kapsam içi, marketplace altyapısı değil |
| Sensitive user data toplayarak otomatik eligibility scoring (yaş/sağlık/askerlik şartı için) | D-013; şart gösterilir ve kaynağa yönlendirilir, hesaplanmaz |
| Amacı tanımlanmamış sensitive alanların saklanması (photo, religion, ethnicity, marital status, health, union membership, gender, full birth date) | D-006 güçlendirmesi; parse anında discard |
| Public sector ilanları için Match Score / "uygunsun" sonucu üretmek | D-015; sınav puanı ve mevzuat modellenmeden yapılamaz |

## Feature → Requirement → User Flow Traceability

> Audit bulgusu: F↔FR↔Flow izlenebilirliği yoktu (REQUIREMENTS tüm dosyada yalnızca iki
> feature ID'sine atıf yapıyordu). Aşağıdaki matris MVP feature'ları içindir; V1/Future
> feature'ları için karşılıklar ilgili sürüm planlanırken doldurulur.

| Feature | Requirements | User Flow |
|---|---|---|
| F-01 Onboarding | FR-101…FR-106 | Flow 1, Flow 2 |
| F-02 CV upload & parsing | FR-101 | Flow 1 |
| F-03 Manual profile | FR-102 | Flow 2 |
| F-04 Verification | FR-103, FR-107 | Flow 1, Flow 2 |
| F-05 Occupation selection | FR-104, FR-301 | Flow 1, Flow 2 |
| F-06 Preferences | FR-106 | Flow 1 |
| F-07 Job feed | FR-501 | Flow 3 |
| F-08 Search & filters | FR-502 | **Flow 9** (yeni) |
| F-09 Explainable recommendations | FR-404, FR-405, FR-411 | Flow 3 |
| F-10 Saved jobs | FR-503 | Flow 3 |
| F-11 Not interested | FR-503, FR-406 | Flow 3 |
| F-12 Applied tracking | FR-503 | Flow 3, Flow 5 |
| F-14 Weekly digest | FR-505 | Flow 4 |
| F-16 Duplicate/expired | FR-206, FR-207 | — (arka plan; kullanıcıya Flow 3'te yansır) |
| F-23 Export & deletion | FR-602, FR-603 | Flow 7 |
| F-24 Source transparency | FR-601 | Flow 3 |
| F-25 Report job | FR-506 | Flow 8 |
| F-26 Public sector mode | FR-410 | Flow 3 (ayrı gösterim modu) |

## Feature Alanlarının Sahipleri

Detaylı davranış tanımları [REQUIREMENTS.md](REQUIREMENTS.md) içindedir; akışlar
[USER_FLOWS.md](USER_FLOWS.md), matching davranışı
[MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md), ingestion davranışı
[SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md) dosyasındadır.
