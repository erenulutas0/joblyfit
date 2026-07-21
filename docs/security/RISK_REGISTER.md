# RISK_REGISTER.md — Risk Register

> **Purpose:** Proje ve ürün risklerinin tek kayıt yeri. Her risk: olasılık (L/M/H),
> etki (L/M/H), önlem (mitigation), sahip ve durum. Teknik failure senaryoları
> [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) → Failure Scenarios; bias riskleri
> [AI_SYSTEM.md](../architecture/AI_SYSTEM.md) → Bias & Fairness (buraya yalnızca
> yönetim görünümüyle özetlenir, detay orada).

Durum: `Open` · `Mitigating` · `Accepted` · `Closed`. Sahip: şimdilik "Product Owner"
(tek karar verici kullanıcı) veya "Eng" (implementasyon sorumlusu).

> **Gözden geçirme notu (2026-07-21):** Register, 12 reviewer'lı documentation audit'inin
> bulgularıyla karşılaştırıldı. R-15 ve R-16'nın durumu güncellendi; audit'in ortaya
> çıkardığı dört yeni risk (R-17…R-20) eklendi. Audit'in teknik bulguları (üç durumlu
> requirement, gate doğrulama, employer resolution vb.) risk olarak değil, doğrudan
> tasarım düzeltmesi olarak işlendi — bu yüzden burada karşılıkları yoktur.

## Stratejik / Ürün Riskleri

| ID | Risk | L | E | Mitigation | Sahip | Durum |
|---|---|---|---|---|---|---|
| R-01 | **Kapsama açığı:** compliant-only ingestion (D-002) nedeniyle büyük platformlar dışarıda kalır; kullanıcı "ilanlar eksik" algısıyla ayrılır | H | H | Kaynak çeşitliliği (gov/univ/ATS/company pages); resmi API/feed anlaşmaları önceliği; coverage raporu ile açık takibi; beklenti yönetimi (source transparency) | Product Owner | Open |
| R-02 | **Soğuk başlangıç:** az kullanıcı ↔ değerin kanıtlanamaması | M | H | MVP tek pazar/dar segment odağı (D-007); digest ile düşük-frekans kullanıcıyı tutma | Product Owner | Open |
| R-03 | **Business model belirsizliği** (A-5): gelir yolu seçilmeden büyüme maliyeti | M | M | V1 öncesi model kararı; excluded listesinin koruduğu güven bozulmadan gelir tasarımı | Product Owner | Open |
| R-04 | **Meslek genişliği tezi tutmaz:** blue-collar segment dijital kanalda beklenen ilgiyi göstermez | M | H | Beta'da meslek çeşitliliği metriği (METRICS.md); persona bazlı kullanıcı testi; gerekirse segment odağı revizyonu | Product Owner | Open |

## Hukuki / Compliance Riskleri

| ID | Risk | L | E | Mitigation | Sahip | Durum |
|---|---|---|---|---|---|---|
| R-05 | **Source ToS/telif ihtilafı** | M | H | D-002 çerçevesi; Conditional için insan onayı; gösterimde özet+atıf; hukuki doğrulama (T-008) | Product Owner | Open |
| R-06 | **Veri koruma ihlali yaptırımı** (GDPR/KVKK) | L | H | Privacy-by-design (PRIVACY_SECURITY_COMPLIANCE.md); veri envanteri; T-008 doğrulaması | Eng | Open |
| R-07 | **Ayrımcılık iddiası:** matching'in bir gruba sistematik dezavantaj ürettiği iddiası | L | H | D-006 + leakage testi + segment denge izleme; explainability kanıt sağlar | Eng | Open |
| R-08 | **Regulated profession yanlış yönlendirmesi** kullanıcı zararı doğurur | M | H | FR-408 kuralları; regulated occupation'larda license gate; explanation dürüstlüğü | Eng | Open |

## Teknik Riskler

| ID | Risk | L | E | Mitigation | Sahip | Durum |
|---|---|---|---|---|---|---|
| R-09 | **Extraction kalitesi yetersiz** kalır (A-7 yanlışlanır): eşleşmeler güven vermez | M | H | Golden set ile erken ölçüm (T-006); confidence mimarisi; asimetrik hata politikası; structured data önceliği | Eng | Open |
| R-10 | **Parser kırılganlığı:** source'ların yapı değişimleri bakım yükünü boğar | H | M | Structured data > HTML tercihi; adapter izolasyonu; fixture testleri; health alarmları; adapter başına bakım maliyeti takibi | Eng | Open |
| R-11 | **Taxonomy bakım yükü:** extension + alias büyümesi kontrolsüzleşir | M | M | Tanımlı ekleme süreci (OCCUPATION_TAXONOMY.md §6); MVP'de 6 first-class occupation sınırı (D-008); deprecated akışı | Eng | Open |
| R-12 | **Duplicate/expiration hataları** kullanıcı güvenini bozar (çöp feed) | M | H | Katmanlı dedupe + geri alınabilir merge; expiration çoklu sinyal; F-25 raporu; leakage metrikleri | Eng | Open |
| R-13 | **Dolandırıcılık ilanları** platform üzerinden kullanıcıya ulaşır | M | H | Quality validation + scam işaretleri + report akışı + source quality score (FS-8) | Eng | Open |
| R-14 | **Ölçek maliyeti:** crawl+AI işleme maliyeti gelir öncesi büyür | M | M | Adaptif crawl frekansı; change-detection ile gereksiz işleme azaltma; maliyet metriği (stack sonrası) | Eng | Open |

## Süreç Riskleri

| ID | Risk | L | E | Mitigation | Sahip | Durum |
|---|---|---|---|---|---|---|
| R-15 | **Scope sürünmesi:** MVP'ye özellik dolması | H | M | **Gerçekleşti ve müdahale edildi (2026-07-21):** audit MVP'nin taşınamaz büyüklükte olduğunu tespit etti; D-008 ile kapsam 3 cluster / 6 occupation / 2-3 source'a, D-016/D-017 ile notification ve matching daraltıldı. Devam eden mitigation: PRD scope disiplini, excluded listesi, scope değişikliğinin kullanıcı onayına bağlı olması | Product Owner | Mitigating |
| R-16 | **Dokümantasyon-gerçek sapması:** implementation başlayınca dokümanlar güncellenmez | M | M | DEFINITION_OF_DONE'da documentation şartı; CONTEXT.md güncelleme tetiğinin checklist'e bağlanması; session handoff disiplini; git tarihçesi | Eng | Mitigating |
| R-17 | **Harici AI sağlayıcısına veri aktarımı:** CV/profil verisinin üçüncü tarafa gitmesi sızıntı ve uyum riski doğurur | M | H | ❓ OPEN-03 kapanmadan hiçbir gerçek kullanıcı verisi harici servise gönderilmez; T-009 privacy ekseni + T-008 hukuki doğrulaması; izinli veri sınıflarının açıkça tanımlanması | Eng | Open |
| R-18 | **Scraped ilan içindeki üçüncü kişi PII'si:** İK iletişim bilgilerinin işlenmesi ve gösterimi | M | M | Asgari gösterim; platform-dışı kişiler için kaldırma talep kanalı; maskeleme politikası T-008'de değerlendirilir (OPEN-06) | Eng | Open |
| R-19 | **Manual Review kapasite darboğazı:** ~2 saat/hafta kapasite aşılırsa compliance kararları ve scam raporları gecikir | M | H | D-014 minimal mod (kapalı tetikleyici listesi); compliance kalemlerinin quality kalemlerinin önünde olması; kapasite aşımında tanımlı otomatik davranış (suspend / limited support / recommendation'dan çıkarma); kuyruk boyutu ve bekleme süresi izlenir | Product Owner | Open |
| R-20 | **Validation gate sonucu olumsuz çıkarsa:** M1'de "revise" veya "stop" kararı, planlanan takvimi ve yönü değiştirir | M | M | D-010 kararı bu ihtimali baştan kabul eder; her validation task'ında eşik altı için önceden tanımlı karar yazılıdır; eşikler calibration target olduğundan tek bir sapma otomatik "stop" değildir | Product Owner | Open |

## Gözden Geçirme

- Faz geçişlerinde (bkz. [ROADMAP.md](../product/ROADMAP.md) milestone'ları) tüm
  register gözden geçirilir; L/E değerleri ve durumlar güncellenir.
- Yeni risk: sıradaki R-numarası ile eklenir; kapatılan risk silinmez, `Closed` +
  gerekçe alır.
