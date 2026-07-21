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

- **Golden set** (T-006 tasarım, T-006b üretim): insan-etiketli profil×ilan çiftleri.
  Etiketleme kılavuzu **üç durumu ayırt eder** (`met` / `unmet` / `unknown`) ve
  gate-relevant alanların doğrulanmamış halini `unknown` olarak etiketler (D-011, D-012).
  Meslek çeşitliliği: MVP'nin altı occupation'ı doğal olarak yarıdan fazlası white-collar
  dışı bir dağılım verir (Driver, Warehouse Worker, Nurse, Health Technician) — ayrı bir
  kota kuralına gerek kalmaz.
- **Ölçülen:** hard requirement precision/recall, nDCG@10, extraction F1, occupation
  mapping accuracy, CV parsing field accuracy (hedefler ve ölçüm tanımları METRICS.md'de).
- **Zorunlu senaryolar (fixture olarak):**
  - Seyrek profil: yalnızca occupation + 2-3 alan dolu → beklenen çıktı `unknown`
    ağırlıklı, `unmet` değil.
  - Doğrulanmamış gate alanı: profilde license var ama `unverified` → beklenen `unknown`.
  - **Agency kopyası:** aynı ilan, değiştirilmiş başlık + gizlenmiş işveren → dedupe
    yakalamalı (SCR-02).
  - Legal eligibility şartı içeren ilan → skora girmemeli, uyarı üretmeli (D-013).
  - Public sector ilanı → Match Score üretilmemeli (D-015).
- **Regression kuralı:** yeni engine/extractor versiyonu, önceki versiyona göre koruma
  metriklerinde anlamlı gerileme yaratıyorsa yayınlanmaz. "Anlamlı"nın operasyonel
  tanımı: ilk ölçüm baseline sayılır; koruma metriğinde **mutlak X puan üstü düşüş**
  yayını bloklar (X, ilk kalibrasyonda belirlenir ve METRICS hedef revizyon kuralına
  tabidir). Segment karşılaştırması MVP'de **cluster düzeyinde** raporlanır (tek tek
  occupation değil) ve örneklem sınırı raporda açıkça not edilir.
- **Semantic üst sınır invariant testi:** structured evidence'ı zayıf bir eşleşmenin
  yalnızca semantic katkıyla yüksek skora çıkamadığı doğrulanır; semantic katkının toplam
  skordaki payının ~%10 sınırını aşmadığı ölçülür (D-017).
- **Explanation doğrulaması:** her iddianın `evidence_refs[]` taşıdığının otomatik
  kontrolü + periyodik insan değerlendirmesi. **Kapsam notu:** otomatik kontrol şablonlu
  üretim için geçerlidir; serbest üretken metin kullanılacaksa doğrulama yöntemi
  (yapılandırılmış claim listesi + insan örneklem denetimi) T-009 ADR'sinde tanımlanmadan
  üretken yol açılmaz.

## 4. Fairness & Privacy Tests (zorunlu, otomatik)

Leakage testi **iki katmanlıdır**; tek katmanlı bir test yanlış güvence verir.

- **Katman 1 — yapısal (0 tolerans):** matching'e giren her contract/entity alanının açık
  bir **allowlist**'e karşı doğrulanması. Denylist değil allowlist: yeni eklenen bir alan
  varsayılan olarak yasaktır ve testi kırar. D-006/NFR-403'ün otomatik güvencesi budur.
- **Katman 2 — içerik (ölçülen kalite):** serbest metin alanları (`headline`,
  `work_experience.description`, free-text skill'ler) ve semantic kanal için **sensitive
  tohumlu sentetik profillerle** probe testi: içine bilerek yerleştirilmiş sensitive
  öğelerin profile taslağına ve oradan matching'e sızmadığı doğrulanır. Burada hedef
  "0 ihlal" değil, **ölçülen ve izlenen bir recall metriğidir** — tespit bir AI görevidir
  ve %100 garanti edilemez (B-10).
- **Discard doğrulaması:** D-006 listesindeki alanların hiçbir entity'de
  kalıcılaşmadığının testi (yalnızca "tespit edildi ve atıldı" meta-kaydı bulunmalı).
- **Gate koruması testi:** `unverified` bir professional license'ın hiçbir koşulda hard
  requirement'ı `met` yapmadığının doğrulanması (D-012) — bu, audit'in iki CRITICAL
  bulgusundan birinin regression koruması.
- **Üç durum testi:** profilde bulunmayan bir qualification'ın `unmet` değil `unknown`
  ürettiğinin doğrulanması (D-011) — diğer CRITICAL bulgunun koruması.
- **Proxy denetimi:** yeni faktör eklenirken proxy dikkat listesi kontrolü
  ([MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md) → faktör ekleme süreci adım 3).
- **Segment karşılaştırması:** golden set sonuçlarının **cluster düzeyinde** raporlanması;
  açıklanamayan sapma yayın engeli ([AI_SYSTEM.md](../architecture/AI_SYSTEM.md) →
  fairness rutini).
- **Data lifecycle testleri:** deletion akışının **veri envanterindeki her sınıfı**
  kapsadığının doğrulanması (envanter ile test kapsamı birebir eşlenir — envanterde
  olmayan sınıf testin de dışında kalır); export kapsam testi; anonim kopyada kullanıcıya
  bağlanabilir kayıt kalmadığının doğrulanması.

## 5. Compliance Tests

- Rate limit uyum testi: adapter'ların konfigüre limiti aşamadığının doğrulanması.
- robots kural testi: disallow edilen path'lere istek üretilmediğinin doğrulanması.
- Registry zorunluluğu: kayıtsız source'la pipeline'ın çalışmayı reddettiği testi (FR-202).
- **Bypass yasağı doğrulaması (D-002'nin çekirdek kuralı):** bu yasağın yalnızca yazılı
  ilke olarak kalmaması için üç mekanizma:
  1. *Access-change testi:* login/auth yönlendirmesi, CAPTCHA sayfası veya erişim engeli
     imzası döndüren bir fixture karşısında Fetcher'ın **crawl'ı durdurduğu ve source'u
     `Suspended` yaptığı** doğrulanır — yeniden deneme, oturum taşıma veya alternatif yol
     denemesi olmadığı test edilir (FS-12).
  2. *Kod review kapısı:* kimlik doğrulama taşıma, CAPTCHA çözme, bot-detection kaçınma
     veya paywall aşma amaçlı hiçbir kod eklenemez —
     [DEFINITION_OF_DONE.md](../../DEFINITION_OF_DONE.md) security maddesinde açık şart.
  3. *Metrik:* `Rate limit uyumu = 0 ihlal` yanında **`access-change tespit sayısı`**
     izlenir; tespit edilen her vaka Manual Review'da sonuçlandırılır.

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
