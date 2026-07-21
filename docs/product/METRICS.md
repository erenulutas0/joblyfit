# METRICS.md — Product, Matching Quality ve Scraper Health Metrics

> **Purpose:** Ölçülecek metriklerin ve hedef değerlerin tek sahibi. Metriklerin nasıl
> toplanacağı/izleneceği [OBSERVABILITY.md](../quality/OBSERVABILITY.md); test yoluyla
> ölçüm [TEST_STRATEGY.md](../quality/TEST_STRATEGY.md).
>
> Hedef değerler ilk kalibrasyon içindir (Assumption); beta verisiyle revize edilir.
> Hiçbir metrik tek başına optimize edilmez — koruma metrikleriyle birlikte okunur.

## 1. Product Metrics

### Aktivasyon
| Metrik | Tanım | İlk hedef |
|---|---|---|
| Onboarding completion rate | Kayıt başlayan → profil + preferences tamamlayan | ≥60% |
| CV'siz onboarding süresi | Manuel profil akışının medyan süresi | ≤5 dk (NFR-502) |
| Gate-relevant alan doğrulama oranı | Onboarding'de gate alanını teyit eden kullanıcı oranı (D-012) | ≥80% |

### Değer / Engagement
| Metrik | Tanım | İlk hedef |
|---|---|---|
| Feed CTR | Feed'de gösterilen ilanlardan detaya geçiş | ≥15% |
| Apply-intent rate | Detay görüntüleyenlerden source'a başvuruya gidenler | ≥8% |
| Save rate | Gösterilen ilanlardan kaydedilenler | izleme (hedefsiz başlar) |
| Weekly return rate | Haftalık geri dönen aktif iş arayan oranı | ≥40% |
| Digest engagement | Digest'ten platforma dönüş | ≥10% |
| Meslek çeşitliliği | Aktif kullanıcılarda white-collar dışı segment payı | ≥%40 (ürün tezi koruması) |

### Güven
| Metrik | Tanım | İlk hedef |
|---|---|---|
| Report rate | Gösterilen ilan başına incorrect/expired raporu | ≤0.5% |
| Explanation faydası | MVP'de periyodik **insan değerlendirmesi** (rubrik); kullanıcıya soru sorma etkileşimi V1 — ölçüm tanımı §4 | ≥70% |
| Deletion/export SLA uyumu | Talep → tamamlanma süresi hedef içinde | 100% |

## 2. Matching Quality Metrics

Ölçüm iki kaynaktan: **golden set** (offline, T-006) ve **kullanıcı davranışı** (online).

### Offline (golden set)
| Metrik | Tanım | İlk hedef |
|---|---|---|
| Hard requirement precision | "Hard requirement eksik" işaretlemelerinin doğruluğu | ≥95% |
| Hard requirement recall | Gerçek hard requirement eksiklerinin yakalanma oranı | ≥90% |
| Ranking kalitesi (nDCG@10) | Golden set beklenen sıralamasına uyum | ≥0.75 |
| Requirement extraction F1 | İlandan Required/Preferred qualification çıkarma kalitesi | ≥0.80 |
| CV parsing field accuracy | Alan bazında doğru çıkarım. **Birincil ölçüm: offline etiketli CV korpusu** (T-006b); kullanıcı düzeltmeleri yalnızca yön gösterici ikincil sinyal | ≥85% |
| Occupation mapping accuracy | İlan/profil → doğru Occupation | ≥90% |

### Online (davranışsal)
| Metrik | Tanım | İlk hedef |
|---|---|---|
| Top-10 apply-intent | İlk 10 öneriden başvuru niyeti üretme oranı | izleme → beta'da hedef |
| Not-interested rate (top-10) | İlk 10 öneride "not interested" oranı | ≤20% |
| "Meslek dışı" şikayeti | Not-interested nedenleri içinde "alakasız meslek" payı | ≤10% |
| Feedback etkisi | Not interested sonrası benzer ilan gösteriminde azalma | ölçülüyor olmalı (V1'de hedef) |

### Fairness koruma metrikleri
| Metrik | Tanım | Hedef |
|---|---|---|
| Leakage — yapısal katman | Matching'e giren alanların allowlist'e uygunluğu | **0 ihlal** (otomatik test) |
| Leakage — içerik katmanı | Sensitive tohumlu sentetik profillerle probe: serbest metin/semantic kanaldan sızma | ölçülen recall; hedef ilk kalibrasyonda konur (0 iddiası yapılmaz) |
| Segment kalite dengesi | **Cluster** düzeyinde matching kalite metriklerinin sapması (occupation başına örneklem çok küçük) | fark izlenir; açıklanamayan büyük sapma incident sayılır ([AI_SYSTEM.md](../architecture/AI_SYSTEM.md) → Bias & Fairness) |

## 3. Scraper Health Metrics

Source başına ve toplam izlenir; alert eşikleri [OBSERVABILITY.md](../quality/OBSERVABILITY.md).

| Metrik | Tanım | İlk hedef |
|---|---|---|
| **Market coverage** | Bağımsız derlenen gerçek açık pozisyon örnekleminin (cluster başına 50-70 ilan) yüzde kaçına compliant source'lardan erişilebiliyor. **Ölçüm:** T-021 protokolü, periyodik tekrar | ≥%60 (calibration target) |
| **Postings discovered per crawl** | Source başına keşfedilen yeni ilan sayısı; hareketli medyandan sapma sessiz kapsam çöküşünü yakalar (FS-11) | anomali izlenir |
| **Listing yield** | Listing'de görülen ilan ÷ başarıyla çıkarılan kayıt (kayıt düzeyi) | ≥90% |
| Crawl success rate | Planlanan crawl'ların başarıyla tamamlanma oranı (source başına) | ≥95% |
| Parser success rate | Fetch edilen sayfalardan başarılı extraction oranı | ≥90% |
| Ingestion freshness lag | İlan source'ta yayınlanma → platformda görünme süresi (medyan) | ≤24 saat (NFR-101) |
| Expired removal lag | Expiration tespiti → feed'den kalkma | ≤24 saat (NFR-102) |
| Duplicate leakage | Feed'de kullanıcıya yansıyan duplicate oranı | ≤1% |
| Data Quality Score (source başına) | Formül ve eşikler §4'te (bu dosya sahibi) | ≥0.8 (hedef) · <0.6 Degraded · <0.5 Suspended |
| Failure queue yaşı | Failure queue'daki en eski kaydın bekleme süresi | ≤48 saat |
| Rate limit uyumu | Rate limit ihlali sayısı | 0 (compliance metriği, D-002) |
| Manual Review Queue derinliği | Açık kayıt sayısı ve en eski kaydın bekleme süresi. **SLA hedefi yoktur** (D-014: ~2 saat/hafta kapasite); kapasite aşımında tanımlı otomatik davranış devreye girer | eşik: kapasiteyi aşan birikme |

## 4. Ölçüm Tanımları

Hedef değer taşıyan her metriğin operasyonel tanımı olmalıdır. Aşağıdakiler audit'te
tanımsız bulunanlardır:

| Metrik | Operasyonel tanım |
|---|---|
| **Impression** (CTR ve report rate paydası) | Kullanıcı ekranında en az 1 saniye görünen ilan kartı. Feed'de yüklenip hiç görünmeyen kartlar sayılmaz. |
| **Aktif iş arayan** (weekly return paydası) | Son 30 günde en az bir feed/arama etkileşimi olan kullanıcı. **"Başarılı churn" ayrı sayılır:** hesabını "işi buldum" gerekçesiyle kapatan kullanıcı retention hesabından çıkarılır, ayrı bir outcome sayacına eklenir. |
| **Data Quality Score** | Formülün tek sahibi bu dosyadır: `0.5 × zorunlu alan doluluk oranı + 0.3 × validation geçme oranı + 0.2 × field accuracy` (field accuracy: kullanıcı "yanlış bilgi" raporları ve örneklem denetiminden). Source Registry yalnızca değeri **tutar**, tanımlamaz. |
| **Source askıya alma eşiği** | Data Quality Score < 0.6 → otomatik `Degraded`; < 0.5 → otomatik `Suspended` + Manual Review. (Hedef değer ≥0.8 ile karıştırılmamalıdır: hedef başarı çizgisi, eşik müdahale çizgisidir.) |
| **Freshness Score** | Girdiler ve ölçek: `posted_at` bilinen ilanlarda yayın yaşı, bilinmeyenlerde ilk görülme yaşı; `last_verified_at` tazeliği; source'un tipik güncelleme temposu. 0-1 aralığına normalize edilir. Yeni source'ta (tempo bilinmiyor) nötr 0.5 kabul edilir. Digest'e girme eşiği: ≥0.4. |
| **Ingestion freshness lag** | Yalnızca `posted_at` bilinen kayıtlar üzerinden hesaplanır; **kapsam oranı (posted_at bilinen kayıt yüzdesi) ayrıca raporlanır** — aksi halde ölçüm posted_at yayınlayan source'lar lehine yanlıdır. |
| **Duplicate leakage** | Haftalık örneklem denetimi: feed gösterimlerinden rastgele seçilen N ilan çifti elle kontrol edilir. Payda: denetlenen çift sayısı. Kılık değiştirmiş agency kopyaları **hedefe dahildir**; Aşama 3'ün bilinçli "ayrı göster" kararları ayrı sayılır ve leakage sayılmaz. Ters yöndeki hata (false-merge) aynı denetimde ayrı sayılır. |
| **Explanation faydası** | MVP'de kullanıcıya soru sorulmaz (feature yok). Ölçüm **periyodik insan değerlendirmesiyle** yapılır: örneklem explanation'lar rubrik üzerinden puanlanır. Kullanıcıya sorulan "yardımcı oldu mu?" etkileşimi V1'dedir. |
| **Meslek çeşitliliği** | Payda: MVP occupation setine (6 first-class) map edilmiş aktif kullanıcılar. Sınıflama: cluster bazlı — Logistics & Operations + Healthcare teknisyen rolleri "white-collar dışı", Office & Commercial "white-collar". Generic tier kullanıcıları ayrı raporlanır, bu orana katılmaz. |
| **`unknown` oranı** | Bir MatchResult'taki `unknown` requirement sayısı ÷ toplam değerlendirilen requirement. Profil seyrekliğinin feed kalitesine etkisini izler (D-011). Hedef konulmaz; segment bazlı izlenir. |

## 5. Hedef Revizyon Kuralı

Buradaki bütün hedefler **calibration target**'tır (dosya başındaki nota bakınız) ve
şu kurala tabidir:

1. İlk golden set / ilk gerçek ölçüm **baseline** sayılır.
2. Bir hedefin değiştirilmesi [DECISIONS.md](../../DECISIONS.md) kaydı gerektirir;
   sessizce düşürülemez.
3. T-017 ve M3 kapıları "hedefe ulaşıldı **veya** gerekçeli revize hedefe ulaşıldı"
   şeklinde okunur — kalibrasyonsuz bir sayı tek başına build'i bloklamaz.

## 6. Metrik Disiplini

- Her yeni feature, hangi metriği oynatması beklendiği yazılarak yapılır.
- Koruma çiftleri: Feed CTR ↑ hedeflenirken report rate ve not-interested rate
  bozulmamalı; ingestion kapsamı ↑ hedeflenirken Data Quality Score düşmemeli;
  `unknown` oranı ↓ hedeflenirken kullanıcıdan istenen bilgi miktarı (onboarding süresi)
  bozulmamalı.
- ❓ OPEN-01: Analitik veri toplama izin modeli (opt-in kapsamı) — T-008'de karara
  bağlanır. **Bağımlılık:** bu karar verilmeden §1'deki online metriklerin
  instrumentation'ı tasarlanamaz; izin modeli iki sınıfı ayırmalıdır — ürün işlevi için
  zorunlu sinyaller (feedback, kişiselleştirme) ve analitik/ölçüm event'leri.
