# OBSERVABILITY.md — Logging, Metrics, Alerting

> **Purpose:** Sistemin gözlemlenebilirlik tasarımının sahibi: ne loglanır, hangi
> metrikler toplanır, hangi koşullar alert üretir. Metrik tanımları ve hedef değerler
> [METRICS.md](../product/METRICS.md) (tekrar edilmez; burada toplama/izleme boyutu).
> Alert'lere müdahale prosedürleri [RUNBOOK.md](../operations/RUNBOOK.md).

## 1. İlkeler

1. **Sağlık üçlüsü:** her alt sistem için (a) çalışıyor mu (uptime/lag), (b) doğru mu
   (quality skorları), (c) uyumlu mu (compliance sayaçları) izlenir.
2. **PII loglanmaz:** loglarda CV içeriği, profil alan değerleri, sensitive veri
   bulunmaz; kayıtlar ID referanslıdır. Hata ayıklama için içerik gerekiyorsa maskeli
   örnekleme + kısa retention ([PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md) → veri envanteri).
3. **Provenance = izlenebilirlik:** bir ilanın feed'e nasıl geldiği (source → crawl →
   parse → dedupe → match) ID zinciriyle geriye doğru izlenebilir olmalı.

## 2. İzleme Alanları

### Ingestion / Scraper Health
- Source başına: crawl success, parser success, fetch hata sınıfları (4xx/5xx/timeout),
  lag'ler, failure queue derinliği/yaşı, rate-limit uyum sayacı.
- Pipeline geneli: aşama başına throughput ve kuyruk derinlikleri; Manual Review Queue
  boyutu ve bekleme süresi.
- Kaynak: Scraper Health Monitor ([SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md));
  değerler Source Registry'nin health alanlarına da yazılır.

### Data Quality
- Validation geçme oranları, zorunlu alan doluluk dağılımı, duplicate leakage örneklem
  sonucu, expired removal lag, source başına Data Quality Score değişimi.

### Matching & AI
- Skor dağılımları (drift takibi), confidence dağılımı, unmapped occupation oranı,
  extraction confidence dağılımı, engine/parser versiyon etiketli karşılaştırma,
  fairness segment raporu üretim durumu.

### Ürün
- Feed gecikmesi, API hata oranları, bildirim gönderim/başarı, digest hacmi,
  product metrics event akışı (izin modeliyle uyumlu — ❓ OPEN, METRICS.md §4).

## 3. Alert Koşulları (başlangıç seti)

Anomali tabanlı eşikler "ani sapma" gibi ölçülemez ifadelerle bırakılmaz; hepsi bir
baseline ve pencere ile tanımlanır. Değerler ilk kalibrasyondur (Assumption) ve gerçek
veriyle ayarlanır.

| Alert | Koşul | Aciliyet | Runbook |
|---|---|---|---|
| Source down | Son 24 saatte hiç başarılı crawl yok *(crawl frekansından bağımsız olsun diye süre bazlı)* | günlük | RB-1 |
| Parser kırıldı | Parser success rate < %70 (tek crawl) | günlük | RB-1 |
| Parser sessiz bozulma | Parser success 7 gün üst üste < %90 (hedef altı ama alert eşiği üstü bant) | günlük | RB-1 |
| **Yield çöküşü (FS-11)** | Source'un keşfettiği ilan sayısı, 7 günlük hareketli medyanın **%50'sinin altına** düştü | günlük | RB-1 |
| **Access-change tespiti (FS-12)** | Fetch yanıtında login/CAPTCHA/erişim engeli imzası | **acil** | RB-1 → RB-2 |
| Rate limit ihlali | Sayaç > 0 | **acil** | RB-2 (compliance) |
| Freshness bozuldu | Ingestion lag hedefin 2 katını aştı | günlük | RB-1 |
| **Source otomatik askıya alındı** | Data Quality Score eşiği aşıldı ve sistem `Suspended` yaptı | günlük (bilgilendirme) | RB-1 |
| Failure queue yaşlandı | En eski kayıt > 48 saat | günlük | RB-3 |
| Duplicate anomalisi | Yeni cluster oranı, 7 günlük hareketli medyandan ±%40 saptı | günlük | RB-4 |
| Matching drift | Skor/confidence dağılımının medyanı 7 günlük baseline'dan ±%20 saptı **veya** golden-set canary'de koruma metriği baseline'ın X puan altına düştü | günlük | RB-5 |
| **Feed bayatladı (FS-5)** | Son başarılı feed hesaplama yaşı > 24 saat, veya yeniden hesaplama kuyruğu büyümeye devam ediyor | **acil** | RB-5 |
| **CV parsing arızası (FS-6)** | Parsing failure rate > %30 (son 1 saat) | günlük | RB-10 |
| **API hata oranı / availability** | 5xx oranı > %2 (5 dk) veya sağlık kontrolü başarısız | **acil** | RB-11 |
| Bildirim taşması | Kullanıcı başına gönderim limitine takılma oranı, haftalık baseline'ın 3 katı | **acil** | RB-6 |
| **Rapor oranı sıçraması** | Report rate, 7 günlük baseline'ın 3 katı (scam dalgası sinyali) | günlük | RB-9 |
| **Unmapped oranı** | Yeni ilanlarda unmapped occupation oranı > %25 (24 saat) | günlük | RB-5 |
| **Policy reevaluation gecikti** | Bir source'un `reevaluation_due` tarihi geçti | günlük | RB-1 |
| Data rights SLA | Deletion/export talebi SLA eşiğinin %75'ine ulaştı | günlük | RB-7 |
| Güvenlik | Yetkisiz erişim denemeleri, vault erişimi (MVP'de olmamalı) | **acil** | RB-8 (incident) |

**Aciliyet modeli (tek kişilik ekip gerçeğiyle):** `acil` = hedef tepki ≤4 saat;
`günlük` = ≤1 iş günü. Bu değerler Assumption'dır. Formal on-call beklenmez; ulaşılamama
durumunda `acil` sınıfı alert'lerin tetiklediği otomatik davranış (crawl durdurma,
bildirim kill-switch) insan müdahalesi olmadan da koruma sağlar.

**Alert korelasyonu:** Aynı source'un eşzamanlı alert'leri (source down + parser kırıldı +
freshness bozuldu) tek olay altında gruplanır; üçü de RB-1'e gider ve tek bildirim üretir.

**Golden-set canary:** Matching drift alert'inin dayanağı olan canary, golden set'in sabit
bir alt kümesinin **planlı aralıklarla (günlük) güncel engine ile çalıştırılmasıdır.**
Bu, TEST_STRATEGY'deki versiyon-değişimi regression kapısından ayrı bir operasyonel
görevdir ve MVP-required alt kümesinde değerlendirilir (T-011).

## 4. Dashboards (asgari)

1. **Scraper Health:** source tablosu (health, quality, lag) + pipeline kuyrukları.
2. **Matching Quality:** golden set trendleri + online davranış metrikleri + fairness raporu.
3. **Ürün:** aktivasyon/engagement/güven metrikleri ([METRICS.md](../product/METRICS.md)).
4. **Compliance:** rate-limit sayaçları, policy yeniden değerlendirme takvimi, data
   rights SLA durumu.

## 5. MVP-Required Alt Küme

❓ OPEN (T-011): kesinleşecek. Öneri: Scraper Health alarmlarının tamamı + rate limit
sayacı + API hata izleme + deletion SLA takibi MVP zorunlusu; drift ve fairness
dashboard'ları ilk sürümde basit rapor olarak başlayabilir.
