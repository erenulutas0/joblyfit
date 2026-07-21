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
| A-1 | Ürün tek bir launch pazarında (tek ülke/dil) başlayacak; pazar henüz seçilmedi. | Taxonomy, dil desteği ve compliance önceliği | ❓ OPEN — kullanıcı kararı (T-001) |
| A-2 | Hedef kitlenin önemli bölümü mobile-first; blue-collar segmentte masaüstü erişimi sınırlı. | UX önceliği, kısa akışlar | Pazar araştırması / ilk kullanıcı testleri |
| A-3 | Seçilecek pazarda yeterli sayıda compliant (API'li, feed'li veya scraping'e izinli) job source mevcut. | Ingestion kapsamı | Source landscape araştırması (T-003) |
| A-4 | Kullanıcılar CV'lerinin parse edilmesine, sonucu doğrulayabildikleri sürece olumlu yaklaşır. | Onboarding tasarımı | Kullanıcı testi |
| A-5 | Business model MVP'de gelir hedeflemez; iş arayana ücretsizdir. Gelir modeli (V1+ için employer-side veya premium) sonra kararlaştırılır. | Feature önceliği, employer tarafının excluded olması | ❓ OPEN — kullanıcı kararı |
| A-6 | ESCO veya O*NET benzeri açık taxonomy, hedef pazarın meslekleri için yeterli çekirdek sağlar; lokal meslekler extension ile eklenebilir. | Taxonomy stratejisi (D-004) | Taxonomy pilot çalışması (T-004, T-005) |
| A-7 | İlan metinlerinden requirement extraction, AI destekli yöntemlerle kullanılabilir doğrulukta yapılabilir; hata payı confidence + explanation ile yönetilebilir. | Matching kalitesi | Golden set ölçümü (T-006) |
| A-8 | Application tracking MVP'de kullanıcı beyanına dayanır (platform dışında yapılan başvurunun otomatik takibi mümkün değildir). | Feature tasarımı | — (yapısal kısıt) |

## Scope Katmanları

Tanım: **MVP** = core loop'un uçtan uca, dar kapsamda çalıştığı ilk sürüm. **V1** = halka
açık, güvenle büyütülebilir sürüm. **Future** = yön olarak benimsenmiş ama planlanmamış.
Feature numaraları, ana feature listesine (bu bölümdeki F-kodları) referanstır.

### MVP Scope

Hedef: **tek pazar, 3-5 compliant source, 8-10 birinci sınıf occupation** üzerinde
"profil → ingestion → matching → explainable feed → feedback" döngüsünü kanıtlamak.

| # | Feature | Not |
|---|---|---|
| F-01 | User onboarding | Kısa, mobile-uyumlu; occupation seçimi dahil |
| F-02 | CV upload and parsing | Yaygın formatlar; sonuç her zaman doğrulamaya düşer |
| F-03 | Manual career profile editor | CV'siz kullanıcılar için eşdeğer yol |
| F-04 | Profile verification and correction | Parse edilen her alan onaylanabilir/düzeltilebilir |
| F-05 | Profession and occupation selection | Taxonomy'den seçim + serbest metin fallback |
| F-06 | Career preference configuration | Location, salary, work type, shift |
| F-07 | Personalized job feed | Match Score + Match Explanation ile |
| F-08 | Search and basic filters | Keyword + location + work type; advanced filters V1 |
| F-09 | Explainable job recommendations | D-005 gereği MVP'nin çekirdeği |
| F-10 | Saved jobs | |
| F-11 | Not interested feedback | Sıralamaya etki eder |
| F-12 | Applied jobs tracking | Kullanıcı beyanlı (A-8) |
| F-14 | New matching job notifications + digest | MVP'de tek kanal (e-posta) ve digest odaklı |
| F-16 | Duplicate and expired job handling | Ingestion tarafında zorunlu |
| F-19 | Profile completeness score | |
| F-23 | User data export and deletion | Yasal gereklilik, ertelenemez |
| F-24 | Source transparency | İlanda source + freshness gösterimi |
| F-25 | Report incorrect or expired job | Manual Review Queue'ya düşer |

### V1 Scope

| # | Feature | Not |
|---|---|---|
| F-08+ | Advanced filters | Sektör, seniority, salary aralığı, shift, license kategorisi |
| F-13 | Application status tracking | Kullanıcı beyanlı durum akışı (applied → interview → offer → rejected) |
| F-15 | Digest kişiselleştirme | Frekans/kanal seçenekleri, push notification |
| F-17 | User feedback learning | Feedback'in ranking'e sistematik, ölçülen etkisi (MVP'de basit kural, V1'de öğrenen katman) |
| F-18 | Match preference controls | Kullanıcının faktör ağırlıklarını ayarlaması ("lokasyon benim için kritik") |
| F-20 | Missing qualification recommendations | Eksik certification/license için yol gösterme |
| F-21 | Career transition support | Transferable skill tabanlı yakın meslek önerisi; regulated profession uyarılarıyla |
| F-22 | Multi-language job and CV support | İkinci pazar/dil açılımıyla birlikte |
| — | Source seti genişletme | 15-25 source; source onboarding süreci olgunlaştırılır |
| — | Occupation kapsamı genişletme | 8-10 → 50+ occupation profile |

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

## Feature Alanlarının Sahipleri

Detaylı davranış tanımları [REQUIREMENTS.md](REQUIREMENTS.md) içindedir; akışlar
[USER_FLOWS.md](USER_FLOWS.md), matching davranışı
[MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md), ingestion davranışı
[SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md) dosyasındadır.
