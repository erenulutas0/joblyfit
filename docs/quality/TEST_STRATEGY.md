# TEST_STRATEGY.md — Test Stratejisi

> **Purpose:** Kalite doğrulama yaklaşımının sahibi. Technology-independent yazılmıştır;
> araç seçimi stack ADR'siyle (D-001) yapılır. Hedef metrikler
> [METRICS.md](../product/METRICS.md); "Done" şartlarıyla bağ
> [DEFINITION_OF_DONE.md](../../DEFINITION_OF_DONE.md).

## 1. İlkeler

1. **Riskin olduğu yere test:** en yüksek riskli alanlar extraction kalitesi, matching
   doğruluğu, dedupe/expiration ve privacy sınırları — test yatırımı buraya yoğunlaşır.
2. **Gerçek veri yerine temsilî veri:** testlerde gerçek kullanıcı verisi kullanılmaz;
   sentetik Career Profile'lar ve fixture ilanlar kullanılır (persona seti
   [USER_PERSONAS.md](../product/USER_PERSONAS.md) temel alınabilir).
3. **Regression kapıları:** parser/extractor/engine/taxonomy versiyon değişimleri golden
   set regression'ından geçmeden yayınlanmaz.

## 2. Test Katmanları

| Katman | Kapsam | Not |
|---|---|---|
| Unit | Normalizer kuralları, skor fonksiyonları, freshness/dedupe mantığı | Hızlı, her değişiklikte |
| Contract | [API_CONTRACTS.md](../architecture/API_CONTRACTS.md) garantileri: her contract'ın garantisi en az bir testle bağlanır | Örn. "expired posting feed cevabına girmez" |
| Fixture-based parser testleri | Her Source Adapter için kaydedilmiş gerçek sayfa örnekleri (fixtures) → beklenen alan çıktıları | Canlıya bağımlı olmayan, tekrarlanabilir; yapı değişince fixture güncellenir ve fark incelenir |
| Integration / pipeline | Fetch(simüle) → parse → normalize → dedupe → store zincirinin uçtan uca doğrulanması | Source isolation davranışı dahil (bir adapter hata verirken diğerleri sürer) |
| E2E (kullanıcı akışları) | [USER_FLOWS.md](../product/USER_FLOWS.md) Flow 1-8'in kritik yolları | Onboarding, feed+explanation, feedback, data rights |
| Non-functional | Yük (feed gecikmesi, pipeline throughput), güvenlik taramaları | NFR referanslı |

## 3. Matching Quality Tests (özel katman)

- **Golden set** (T-006): insan-etiketli profil×ilan çiftleri; beklenen hard-requirement
  kararları ve sıralama tercihleri. Meslek çeşitliliği şartı: white-collar dışı
  senaryolar setin en az %50'si (B-7 önlemi).
- **Ölçülen:** hard requirement precision/recall, nDCG@10, extraction F1, occupation
  mapping accuracy (hedefler METRICS.md'de).
- **Regression kuralı:** yeni engine/extractor versiyonu, önceki versiyona göre koruma
  metriklerinde anlamlı gerileme yaratıyorsa yayınlanmaz.
- **Explanation doğrulaması:** örneklem explanation'lar için "evidence'sız iddia var mı"
  kontrolü (otomatik: her iddianın evidence referansı olmalı; + periyodik insan değerlendirmesi).

## 4. Fairness & Privacy Tests (zorunlu, otomatik)

- **Sensitive attribute leakage testi:** matching feature set'inde yasaklı alanların
  bulunmadığının otomatik doğrulanması (0 tolerans; D-006, NFR-403).
- **Proxy denetimi:** yeni faktör eklenirken proxy dikkat listesi kontrolü
  ([MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md) → faktör ekleme süreci adım 3).
- **Segment karşılaştırması:** golden set sonuçlarının occupation grupları arasında
  raporlanması; açıklanamayan sapma yayın engeli ([AI_SYSTEM.md](../architecture/AI_SYSTEM.md) → fairness rutini).
- **Data lifecycle testleri:** deletion akışının bütün veri sınıflarını kapsadığının
  doğrulanması; export kapsam testi.

## 5. Compliance Tests

- Rate limit uyum testi: adapter'ların konfigüre limiti aşamadığının doğrulanması.
- robots kural testi: disallow edilen path'lere istek üretilmediğinin doğrulanması.
- Registry zorunluluğu: kayıtsız source'la pipeline'ın çalışmayı reddettiği testi (FR-202).

## 6. Test Verisi Yönetimi

- Fixture'lar ve sentetik profiller versiyonlanır (repo içinde).
- Fixture'larda gerçek kişi bilgisi bulunmaz (ilan fixture'larındaki İK iletişim
  bilgileri maskelenmiş olmalı).
- Golden set etiketleme kılavuzu tek kaynaktır; etiketler arası tutarlılık örneklemle
  denetlenir.

## 7. MVP-Required Alt Küme

❓ OPEN (T-011): Yukarıdaki katmanlardan MVP için zorunlu minimum işaretlenecek.
Öneri: Unit + fixture parser testleri + leakage testi + golden set (küçük) + kritik
E2E (Flow 1, 3, 7) MVP zorunlusu; yük testleri V1'e ertelenebilir.
