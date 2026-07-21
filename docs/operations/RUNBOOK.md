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

## RB-1 — Source down / parser kırıldı / yield çöktü / freshness bozuldu

1. Registry'de source'un health durumunu ve son crawl loglarını incele. Aynı source'un
   eşzamanlı alert'leri tek olaydır — hepsini birlikte değerlendir.
2. Sınıflandır: geçici ağ hatası mı (retry/backoff zaten deniyor), yapı değişimi mi
   (parser success düşük **veya yield çöküşü** — ikincisi sessizdir, parser "başarılı"
   görünür), **erişim/policy değişimi mi** (access-change tespiti, 4xx, robots değişimi)?
3. Yapı değişimi → source'u `Degraded` işaretle; adapter fixture'larını yeni yapıyla
   güncelleme işi aç; bu sırada eski veri expiration akışında normal yaşar.
4. **Erişim/policy değişimi → RB-2'ye geç.** Bypass **hiçbir koşulda denenmez** (D-002):
   yeniden deneme, oturum taşıma, alternatif erişim yolu arama yasaktır.
5. Yalnızca yield çöktüyse: listing yapısını elle kontrol et; pagination deseni değişmiş
   olabilir. Adapter düzeltilene kadar source `Degraded` kalır.
6. Kapanış: health yeşile döndüğünde `Active`; olay notu Registry'ye.

## RB-1b — Acil içerik kaldırma / source emergency takedown (FS-13)

Hukuki kaldırma talebi veya toplu scam tespitinde TTL beklemek yeterli değildir.

1. Talebi ve kapsamını kaydet (kim, ne, hangi gerekçe) — Manual Review `removal_request`.
2. Source'u `Suspended` + **`immediate de-index`** bayrağıyla işaretle: o source'un bütün
   posting'leri anında feed, arama ve digest dışına alınır.
3. Canonical cluster'ları yeniden değerlendir — başka source'tan üyesi olan canonical'lar
   yaşamaya devam eder.
4. Arşiv ve provenance **korunur**; kalıcı silme ayrı bir karardır (hukuki talebin kapsamı
   neyse ona göre).
5. `source_suspended` olayının yayıldığını ve MatchResult invalidation'ının tetiklendiğini
   doğrula.
6. Talep sahibine sonucu bildir; olayı PROGRESS ve gerekiyorsa RISK_REGISTER'a işle.

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

## RB-5 — Matching drift / feed bayatlaması / unmapped artışı

1. Neyin değiştiğini bul: engine/extractor/taxonomy versiyonu mu, ingestion kompozisyonu
   mu (yeni source ağırlığı), kullanıcı kompozisyonu mu?
2. Versiyon kaynaklıysa → **rollback** (aşağıdaki ön şartlar sağlanmış olmalı), golden set
   farkını incele.
3. **Feed bayatladıysa (FS-5):** yeniden hesaplama kuyruğunun derinliğini ve son başarılı
   hesaplama yaşını kontrol et. Graceful degradation gereği son geçerli feed servis
   edilmeye devam eder — kullanıcıya tazelik bilgisi gösterildiğini doğrula. Kuyruk
   tıkalıysa önceliklendir: aktif kullanıcılar önce.
4. **Unmapped oranı arttıysa:** yeni bir source mu geldi, taxonomy mi değişti? Geçici
   çözüm: etkilenen ilanlar limited tier'da kalır (kullanıcıya yanlış öneri gitmez).
5. Fairness segment raporunda sapma varsa yayını blokla
   ([AI_SYSTEM.md](../architecture/AI_SYSTEM.md) → fairness rutini).

### RB-5 rollback ön şartları (tatbikatla doğrulanır)

Rollback bir *yetenektir*, `engine_version` alanının varlığı değil. Şunlar sağlanmadan
RB-5 uygulanamaz:

1. **Son N engine/taxonomy versiyonu çalıştırılabilir tutulur** (yalnızca kayıt değil).
2. Rollback sonrası etkilenen MatchResult'lar **yeniden hesaplanır** (invalidation
   tetikleyicisi: engine_version/taxonomy_version değişimi) ve kullanıcıya feed tazelik
   bilgisi yansır.
3. Rollback **golden set ile doğrulanır** — eski versiyonun beklenen metrikleri ürettiği
   teyit edilir.
4. Taxonomy rollback'inde ek adım: geri alınan mapping'lerle `unmapped`'e düşen ilanlar
   limited tier'a alınır, silinmez.
5. Bu prosedür **en az bir kez tatbikatla** doğrulanmadan "hazır" sayılmaz
   ([DEFINITION_OF_DONE.md](../../DEFINITION_OF_DONE.md)).

## RB-10 — CV parsing arızası (FS-6)

1. Parsing failure rate'i ve hata sınıfını incele (format reddi mi, servis arızası mı?).
2. **Manuel profil yolu (F-03) her zaman açık kalmalı** — onboarding'in kapanmadığını
   doğrula; CV yolu geçici olarak devre dışı bırakılabilir.
3. Başarısız dosyalar yeniden işleme kuyruğuna alınır; kullanıcıya "CV'ni sonra tekrar
   deneyebilirsin, şimdilik birkaç soruyla devam et" mesajı gösterilir.
4. Harici bir servis kullanılıyorsa sözleşme/kota durumunu kontrol et.

## RB-11 — API hata oranı / availability

1. Hata sınıfını ve etkilenen yüzeyi belirle (feed mi, profil mi, arama mı?).
2. Bağımlılık kaynaklıysa (veri katmanı, arama indeksi) ilgili bileşeni izole et;
   feed son hesaplanan haliyle servis edilmeye devam etmeli (NFR-301).
3. Kullanıcıya dönük bozulmada durum bilgisi göster; sessiz hata bırakma.
4. Olayı kaydet; tekrar ediyorsa kök neden analizi aç.

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
