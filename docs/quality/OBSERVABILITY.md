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

| Alert | Koşul (öneri) | Runbook |
|---|---|---|
| Source down | Bir source'ta art arda 3 crawl başarısız | RB-1 |
| Parser kırıldı | Parser success rate < %70 (tek crawl) veya şema-değişim tespiti | RB-1 |
| Rate limit ihlali | Sayaç > 0 | RB-2 (compliance — anında) |
| Freshness bozuldu | Ingestion lag hedefin 2 katını aştı | RB-1 |
| Failure queue yaşlandı | En eski kayıt > 48 saat | RB-3 |
| Duplicate anomalisi | Yeni cluster oranında ani sapma | RB-4 |
| Matching drift | Skor/confidence dağılımında ani kayma veya golden-set canary düşüşü | RB-5 |
| Bildirim taşması | Kullanıcı başına gönderim limitine takılma oranında sıçrama | RB-6 |
| Data rights SLA | Deletion/export talebi SLA eşiğine yaklaşıyor | RB-7 |
| Güvenlik | Vault erişim anomalisi, yetkisiz erişim denemeleri | RB-8 (incident) |

Eşikler ilk kalibrasyondur; beta verisiyle ayarlanır.

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
