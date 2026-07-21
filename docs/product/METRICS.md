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
| Profile Completeness (medyan) | Aktif kullanıcıların completeness score medyanı | ≥70% |

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
| Explanation faydası | "Bu açıklama yardımcı oldu mu?" olumlu oranı | ≥70% |
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
| CV parsing field accuracy | Alan bazında doğru çıkarım (kullanıcı düzeltmeleriyle de ölçülür) | ≥85% |
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
| Sensitive attribute leakage testi | Matching feature set'inde yasaklı alan bulunmaması | 0 ihlal (otomatik test) |
| Segment kalite dengesi | Occupation grupları arasında matching kalite metriklerinin sapması | fark izlenir; açıklanamayan büyük sapma incident sayılır ([AI_SYSTEM.md](../architecture/AI_SYSTEM.md) → Bias & Fairness) |

## 3. Scraper Health Metrics

Source başına ve toplam izlenir; alert eşikleri [OBSERVABILITY.md](../quality/OBSERVABILITY.md).

| Metrik | Tanım | İlk hedef |
|---|---|---|
| Crawl success rate | Planlanan crawl'ların başarıyla tamamlanma oranı (source başına) | ≥95% |
| Parser success rate | Fetch edilen sayfalardan başarılı extraction oranı | ≥90% |
| Ingestion freshness lag | İlan source'ta yayınlanma → platformda görünme süresi (medyan) | ≤24 saat (NFR-101) |
| Expired removal lag | Expiration tespiti → feed'den kalkma | ≤24 saat (NFR-102) |
| Duplicate leakage | Feed'de kullanıcıya yansıyan duplicate oranı | ≤1% |
| Data Quality Score (source başına) | Zorunlu alan doluluğu + validation geçme oranı bileşimi ([SOURCE_REGISTRY.md](../architecture/SOURCE_REGISTRY.md)) | ≥0.8 |
| Failure queue yaşı | Failure queue'daki en eski kaydın bekleme süresi | ≤48 saat |
| Rate limit uyumu | Rate limit ihlali sayısı | 0 (compliance metriği, D-002) |
| Manual Review Queue süresi | Kayıt → insan kararı medyan süresi | ≤72 saat |

## 4. Metrik Disiplini

- Her yeni feature, hangi metriği oynatması beklendiği yazılarak yapılır.
- Koruma çiftleri: Feed CTR ↑ hedeflenirken report rate ve not-interested rate
  bozulmamalı; ingestion kapsamı ↑ hedeflenirken Data Quality Score düşmemeli.
- ❓ OPEN: Analitik veri toplama izin modeli (opt-in kapsamı) —
  [PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md) ile
  birlikte kararlaştırılacak.
