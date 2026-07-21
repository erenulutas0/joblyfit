# RUNBOOK.md — Operasyonel Senaryolar ve Müdahale Adımları

> **Purpose:** Alert'lere ve bilinen arıza senaryolarına müdahale prosedürleri. Alert
> tanımları [OBSERVABILITY.md](../quality/OBSERVABILITY.md); senaryoların mimari arka
> planı [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) → Failure Scenarios.
> Stack seçilmediği için adımlar kavramsaldır; implementation sırasında komut/panel
> referanslarıyla somutlaştırılır (DEFINITION_OF_DONE → observability şartı).

## Genel İlkeler

1. Önce **etkiyi sınırla** (karantina/kill-switch), sonra kök nedeni araştır.
2. Source ile ilgili her müdahale Source Registry üzerinden yapılır ve kayda geçer.
3. Compliance sınıfı olaylar (RB-2, RB-8) ertelenemez ve kapatma gerekçesi yazılmadan
   kapanmaz.

## RB-1 — Source down / parser kırıldı / freshness bozuldu

1. Registry'de source'un health durumunu ve son crawl loglarını incele.
2. Sınıflandır: geçici ağ hatası mı (retry/backoff zaten deniyor), yapı değişimi mi
   (parser success düşük + şema-değişim sinyali), erişim engeli mi (4xx/robots değişimi)?
3. Yapı değişimi → source'u `Degraded` işaretle; adapter fixture'larını yeni yapıyla
   güncelleme işi aç; bu sırada eski veri expiration akışında normal yaşar.
4. Erişim engeli / policy sinyali → crawl'ı durdur, source'u `Suspended` yap,
   policy yeniden değerlendirme başlat (bypass denenmez — D-002).
5. Kapanış: health yeşile döndüğünde `Active`; olay notu Registry'ye.

## RB-2 — Rate limit ihlali (compliance)

1. İlgili adapter'ın crawl'ını **derhal durdur**.
2. İhlalin kaynağını bul (konfigürasyon hatası mı, kod hatası mı, kaynak limitinin
   değişmesi mi); kayıtla.
3. Düzeltme + test ([TEST_STRATEGY.md](../quality/TEST_STRATEGY.md) → compliance testleri)
   olmadan crawl açılmaz.
4. Olay [BUGS.md](../../BUGS.md) kaydı + gerekiyorsa Source Record'a not.

## RB-3 — Failure queue yaşlanması

1. Kuyruktaki hata sınıflarını grupla (hangi source, hangi aşama).
2. Tek source yoğunluğu → RB-1'e geç. Yaygın dağılım → pipeline kapasite/kaynak sorunu;
   işleme hızını ve kuyruk tüketicilerini incele.
3. Çözülemeyen kayıtları Manual Review'a taşı; kuyruğu sessizce boşaltma (veri kaybı).

## RB-4 — Duplicate anomalisi

1. Son merge kararlarının örneklemini incele (merge log).
2. Yanlış birleştirme (farklı ilanlar tek olmuş) → ilgili cluster'ları geri al
   (merge log üzerinden), eşiği/blocking anahtarını gözden geçir.
3. Yanlış ayrık (aynı ilan çoklu görünüyor) → duplicate leakage metriğini doğrula,
   eşik ayarı işi aç.
4. Değişiklik golden set + fixture regression'dan geçmeden yayınlanmaz.

## RB-5 — Matching drift / kalite düşüşü

1. Neyin değiştiğini bul: engine/extractor/taxonomy versiyonu mu, ingestion kompozisyonu
   mu (yeni source ağırlığı), kullanıcı kompozisyonu mu?
2. Versiyon kaynaklıysa → önceki versiyona dön (engine_version'lı MatchResult'lar
   karşılaştırma sağlar), golden set farkını incele.
3. Fairness segment raporunda sapma varsa yayını blokla ([AI_SYSTEM.md](../architecture/AI_SYSTEM.md) → fairness rutini).

## RB-6 — Bildirim taşması

1. Bildirim gönderimini kill-switch ile durdur (digest kuyruğu bekletilir, silinmez).
2. Nedeni bul: eşik hatası mı, duplicate patlaması mı (RB-4 ile bağlantılı), bug mı?
3. Etkilenen kullanıcı kitlesini belirle; gerekiyorsa özür/açıklama bildirimi tek sefer.
4. Düzeltme sonrası kademeli açılış.

## RB-7 — Data rights SLA riski

1. Bekleyen export/deletion taleplerini listele; takılma noktasını bul (hangi veri
   sınıfı/akış).
2. Deletion akışı kısmen çalıştıysa: hangi sınıflar silindi kaydını doğrula; kalanları
   manuel tamamla; kullanıcıya durum bildir.
3. SLA aşılırsa: [PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md)
   uyarınca kayıt + kök neden + süreç düzeltmesi.

## RB-8 — Güvenlik olayı (vault erişim anomalisi / yetkisiz erişim / veri ihlali şüphesi)

1. [PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md) →
   Incident Response çerçevesini başlat.
2. Erişimi kapat (kimlik bilgisi iptali, sınır sıkılaştırma); kanıtları koru (loglar).
3. Kapsamı belirle: hangi veri sınıfları, hangi kullanıcılar, hangi zaman aralığı.
4. Yasal bildirim gereksinimlerini değerlendir (pazar rejimine göre süreler).
5. Postmortem → önlemler bu runbook'a ve RISK_REGISTER'a işlenir.

## RB-9 — Dolandırıcılık ilanı bildirimi yoğunlaşması

1. Raporlanan ilanları ve ortak source'larını incele.
2. Doğrulanan scam ilanları `suspicious` → yayından kaldır; benzer desenli kayıtları tara.
3. Source Data Quality Score güncellenir; eşik altına düşen source askıya alınır (FS-8).
4. Etkilenen kullanıcılara (ilana başvuranlar) bilgilendirme değerlendirilir.
