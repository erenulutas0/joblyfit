# PRIVACY_SECURITY_COMPLIANCE.md

> **Purpose:** Privacy ve data lifecycle, security boundaries ve compliance/source policy
> risklerinin sahibi. Riskler olasılık/etki boyutuyla [RISK_REGISTER.md](RISK_REGISTER.md)
> içinde izlenir. Fairness politikası matching tarafındadır
> ([MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md) → Fairness Constraints).
>
> ⚠️ Bu doküman hukuki görüş değildir; hedef pazar seçildikten sonra uzman doğrulaması
> zorunludur (T-008).

## 1. Privacy İlkeleri

1. **Minimization:** yalnızca eşleştirme ve ürün işlevi için gereken veri toplanır.
   Sensitive attribute'lar toplanmaya çalışılmaz; CV'den kendiliğinden gelirse vault'a
   izole edilir (D-006) ve matching'de kullanılmaz.
2. **Şeffaflık:** kullanıcı hangi verinin ne için kullanıldığını görebilir; Match
   Explanation bunun ürün içi yüzüdür.
3. **Kontrol:** export ve deletion birinci sınıf özelliktir (F-23, FR-602/603); rıza
   kayıtları (consent_records) tutulur.
4. **Amaç sınırı:** Career Profile verisi yalnızca kullanıcıya hizmet için kullanılır;
   üçüncü tarafa satış/aktarım yok ([PRD.md](../product/PRD.md) → Excluded).

## 2. Veri Envanteri ve Data Lifecycle

| Veri sınıfı | Örnek | Hassasiyet | Retention (öneri) | Silme davranışı |
|---|---|---|---|---|
| Hesap verisi | e-posta, auth kimliği | Orta | Hesap ömrü | Deletion'da kalıcı silinir |
| Career Profile | education, skills, licenses… | Yüksek (PII) | Hesap ömrü | Kalıcı silinir |
| CV dosyası (orijinal) | yüklenen belge | Yüksek (PII) | Parse + doğrulama sonrası kısa süre (öneri: 90 gün, ❓ OPEN) | Süre sonunda otomatik; deletion'da anında |
| Sensitive Data Vault | doğum tarihi, fotoğraf vb. | Çok yüksek | Mümkün olan en kısa (öneri: kullanıcı görünürlüğü için tutulmayacaksa parse sonrası silinir, ❓ OPEN) | Anında |
| Feedback Signals | saved, not interested… | Orta (davranışsal) | Hesap ömrü; sistem kalibrasyonu için anonimleştirilmiş kopya | Kişisel bağlantı silinir; anonim istatistik kalabilir |
| Application kayıtları | başvuru durumu | Orta | Hesap ömrü | Kalıcı silinir |
| Job Posting verisi | ilan içeriği | Kişisel değil* | Aktif + arşiv (expired: öneri 12 ay, ❓ OPEN) | — |
| Loglar/telemetri | erişim, hata | Değişken | Kısa (öneri: 30-90 gün) | Rotasyonla |

\* İlan metni istisnası: ilan içinde kişi bilgisi (İK çalışanının adı/telefonu) olabilir;
gösterimde makul, talep gelirse kaldırılır.

**Deletion akışı:** talep → kimlik doğrulama → geri alma penceresi (öneri: 7 gün,
❓ OPEN) → tüm kişisel veri sınıflarının kalıcı silinmesi → tamamlanma bildirimi.
SLA (öneri): talepten itibaren ≤30 gün. Yedeklerdeki kopyalar yedek rotasyon süresi
içinde temizlenir; bu süre kullanıcıya bildirilir.

**Export:** makine-okunur format; kapsam: profil, preferences, feedback, applications,
saved jobs, consent kayıtları.

## 3. Security Boundaries

[ARCHITECTURE.md](../architecture/ARCHITECTURE.md) → Boundaries'in güvenlik detayı:

| Sınır | Tehdit | Kontroller |
|---|---|---|
| Dış içerik (source'lardan gelen) | Zararlı/aldatıcı içerik, injection, scam ilan | İçerik sanitization; ilan içeriği hiçbir yerde kod/komut olarak işlenmez; scam tespiti + report akışı (FS-8) |
| CV dosyaları | Zararlı dosya, aşırı boyut, gizli içerik | Format allowlist, boyut limiti, içerik tarama, izole işleme ortamı |
| Kullanıcı girdileri | Injection, kötüye kullanım | Girdi doğrulama; feedback spam koruması (rate limit, anomali) |
| Sensitive Data Vault | İçeriden erişim, sızıntı | Ayrı saklama + encryption; erişim yalnızca kullanıcı self-service ve data-rights akışları; erişim audit-log |
| Matching veri yolu | Sensitive leakage | Vault'tan matching'e akış yok (NFR-403); otomatik leakage testi |
| Admin/Manual Review | Yetki aşımı | Role-based erişim, least privilege, karar audit-log (C-6) |
| Dış AI servisleri (kullanılırsa) | Veri sızıntısı | ❓ OPEN (T-009): izinli veri sınıfları, sözleşme şartları, bölge kısıtı |

Genel: at-rest & in-transit encryption (NFR-402), secrets yönetimi, ortam ayrımı
(prod verisi test ortamına kopyalanmaz; test için sentetik profiller —
[TEST_STRATEGY.md](../quality/TEST_STRATEGY.md)).

## 4. Compliance ve Source Policy Riskleri

### 4.1 Veri koruma rejimleri

Hedef pazara göre (❓ OPEN, A-1): GDPR (AB), KVKK (TR) veya muadili. Tasarım şimdiden
şunları varsayar: hukuki dayanak kaydı, rıza yönetimi, veri hakları (erişim/export/
silme/düzeltme), ihlal bildirimi süreci, işleme envanteri. **Otomatik öneri sistemleri**
için ek yükümlülük olabilir (öneri mantığının açıklanabilirliği — D-005 bunu zaten
ürün ilkesi yapar).

### 4.2 Source policy (özet — operasyonel çerçeve [SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md) §4)

| Risk | Açıklama | Duruş |
|---|---|---|
| ToS ihlali iddiası | Bir source otomatik erişimi yasaklıyor olabilir | `Rejected/Conditional` sınıflaması; insan onaysız crawl yok (D-002) |
| Telif/yeniden yayın | İlan metninin platformda gösterimi içerik hakları sorusu doğurur | Kullanıcıya özet + zorunlu alanlar + **orijinal source'a link ve atıf**; tam metin yeniden yayını yapılmaz; ❓ OPEN: gösterim sınırı (T-008) |
| İlan içindeki kişisel veri | İK iletişim bilgileri vb. | Minimum gösterim; kaldırma talebi süreci |
| Kaynak yük etkisi | Crawl'ın kaynak siteye maliyeti | Muhafazakâr rate limit, cache, gece dengeleme (nazik komşuluk) |
| Policy değişimi | Source sonradan kural değiştirebilir | `reevaluation_due` ile periyodik yeniden değerlendirme; Suspended akışı |

### 4.3 Ürün tarafı compliance

- İstihdamda ayrımcılık hukuku: sensitive attribute yasağı (D-006) ve ayrımcı ilan
  işleme (B-4) bununla hizalıdır.
- Regulated profession yönlendirme dürüstlüğü (FR-408) — yanlış yönlendirme hem etik
  hem potansiyel hukuki risk.
- Pazarlama/bildirim izinleri: digest ve bildirimler açık izinle, kolay opt-out.

## 5. Incident Response (çerçeve)

1. Tespit (alert/rapor) → sınıflandırma (veri ihlali mi, servis mi, içerik mi).
2. Veri ihlalinde: kapsam belirleme, erişim kapatma, kanıt koruma, yasal bildirim
   süreleri (pazara göre), kullanıcı bilgilendirmesi.
3. Kayıt + postmortem → [RUNBOOK.md](../operations/RUNBOOK.md) senaryolarına işlenir.
