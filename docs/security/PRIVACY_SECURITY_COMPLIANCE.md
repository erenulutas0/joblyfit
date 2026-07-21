# PRIVACY_SECURITY_COMPLIANCE.md

> **Purpose:** Privacy ve data lifecycle, security boundaries ve compliance/source policy
> risklerinin sahibi. Riskler olasılık/etki boyutuyla [RISK_REGISTER.md](RISK_REGISTER.md)
> içinde izlenir. Fairness politikası matching tarafındadır
> ([MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md) → Fairness Constraints).
>
> ⚠️ Bu doküman hukuki görüş değildir; hedef pazar seçildikten sonra uzman doğrulaması
> zorunludur (T-008).

## 1. Privacy İlkeleri

1. **Minimization — "sakla" değil "hiç toplama":** yalnızca eşleştirme ve ürün işlevi için
   gereken veri toplanır. Amacı ve hukuki dayanağı yazılamayan veri **saklanmaz**.
   D-006 listesindeki sensitive alanlar (photo, religion, ethnicity, marital status,
   health information, union membership, gender, full birth date) CV'den kendiliğinden
   gelse bile structured profile'a aktarılmadan **discard edilir**; yalnızca "tespit
   edildi ve atıldı" meta-kaydı tutulur ([AI_SYSTEM.md](../architecture/AI_SYSTEM.md) §1.2).
   **Sensitive Data Vault varsayılan saklama alanı değildir** — tanımlı purpose + consent
   olmadan kullanılamaz ve MVP'de aktif değildir.
2. **Şeffaflık:** kullanıcı hangi verinin ne için kullanıldığını görebilir; Match
   Explanation bunun ürün içi yüzüdür.
3. **Kontrol:** export ve deletion birinci sınıf özelliktir (F-23, FR-602/603); rıza
   kayıtları (consent_records) tutulur.
4. **Amaç sınırı:** Career Profile verisi yalnızca kullanıcıya hizmet için kullanılır;
   üçüncü tarafa satış/aktarım yok ([PRD.md](../product/PRD.md) → Excluded).

## 2. Veri Envanteri ve Data Lifecycle

> **Statü uyarısı:** Aşağıdaki retention değerlerinin **tamamı öneridir**, karar değildir.
> Hepsi ❓ OPEN-04…OPEN-08 olarak [CONTEXT.md](../../CONTEXT.md) index'inde izlenir ve
> T-008 (hukuki doğrulama) acceptance criteria'sında karara çevrilir. Diğer dokümanlar
> bu değerlere **kesin referans veremez**; "tanımlanacak SLA" ifadesi kullanılır.

| Veri sınıfı | Örnek | Hassasiyet | Retention (öneri) | Silme davranışı |
|---|---|---|---|---|
| Hesap verisi | e-posta, auth kimliği | Orta | Hesap ömrü | Deletion'da kalıcı silinir |
| Career Profile | education, skills, licenses… | Yüksek (PII) | Hesap ömrü | Kalıcı silinir |
| **İletişim bilgisi (CV'den)** | telefon, adres | Yüksek (PII) | **Toplanmaz** — hesap e-postası zaten var; adres yalnızca `location_ref`'e indirgenerek işlenir, ham hali saklanmaz | — (saklanmadığı için silinecek kayıt yok) |
| CV dosyası (orijinal) | yüklenen belge | Yüksek (PII) | Parse + doğrulama sonrası kısa süre (öneri: 90 gün, ❓ OPEN-04) | Süre sonunda otomatik; deletion'da anında |
| Sensitive Data Vault | *(MVP'de kullanılmıyor)* | Çok yüksek | Yalnızca tanımlı purpose + consent varsa; aksi halde **hiç saklanmaz** (D-006) | Anında |
| Feedback Signals | saved, not interested… | Orta (davranışsal) | Hesap ömrü; sistem kalibrasyonu için **yalnızca agrega** kopya | Kişisel bağlantı silinir; agrega istatistik kalabilir (§2.1) |
| Application kayıtları | başvuru durumu | Orta | Hesap ömrü | Kalıcı silinir |
| **MatchResult / MatchExplanation** | skor, faktör evidence'ları, kullanıcıya özel açıklama | Yüksek (türetilmiş PII) | Hesap ömrü; stale kayıtlar yeniden hesaplamada üzerine yazılır | **Kalıcı silinir** — profil silinince türetilmiş veri de silinir |
| **Analytics / product event'leri** | feed görüntüleme, tıklama | Orta (davranışsal) | ❓ OPEN-01 izin modeline bağlı; öneri: kısa | Kişisel bağlantı silinir |
| **Manual Review kayıtları** | rapor metni, karar notu | Orta (serbest metin PII içerebilir) | Karar + denetim süresi (öneri: 12 ay, ❓ OPEN-08) | Kullanıcıya bağlı alanlar silinir; karar kaydı anonimleştirilir |
| **DataRightsRequest** | export/deletion talep kaydı | Orta | Yükümlülük kanıtı olarak asgari süre (T-008) | Silinmez; **kişisel içerik taşımaz**, yalnızca talep kanıtıdır |
| Job Posting verisi | ilan içeriği | Karma* | Aktif + arşiv (expired: öneri 12 ay, ❓ OPEN-07) | — |
| Loglar/telemetri | erişim, hata | Değişken | Kısa (öneri: 30-90 gün, ❓ OPEN-08) | Rotasyonla |
| **Backup kopyaları** | yukarıdakilerin yedeği | Kaynağıyla aynı | Rotasyon süresi ❓ OPEN-08 | Deletion sonrası rotasyon süresi içinde temizlenir; süre kullanıcıya bildirilir |

\* **Karma sınıf:** ilan içeriği kişisel veri değildir, **ancak içine gömülü üçüncü kişi
PII'si** (İK çalışanının adı/telefonu) bulunabilir. Gösterimde asgari tutulur. Platform
kullanıcısı olmayan kişiler için ayrı bir **kaldırma talep kanalı** bulunur (F-25 yalnızca
platform kullanıcılarına açıktır). ❓ OPEN-06: gösterim sınırı ve maskeleme politikası
T-008 kapsamında.

### 2.1 Anonimleştirme standardı

Deletion sonrası kalmasına izin verilen "anonim kalibrasyon verisi" için kurallar:

- Yalnızca **agrega/istatistik** düzeyinde tutulur — kayıt bazlı "anonim" feedback
  tutulmaz (niş occupation'larda tek kişiye indirgenebilir).
- Serbest metin alanları (not-interested nedeni, rapor metni) agrega kopyaya **girmez**.
- Düşük hacimli segmentlerde **küçük-n bastırma** uygulanır.
- Deletion testine "anonim kopyada kullanıcıya bağlanabilir kayıt kalmadı" doğrulaması
  eklenir ([TEST_STRATEGY.md](../quality/TEST_STRATEGY.md) §4).

Nihai standart T-008 girdisidir.

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

Genel: at-rest & in-transit encryption (NFR-402 — **backup kopyaları dahil**), secrets
yönetimi, ortam ayrımı (prod verisi test ortamına kopyalanmaz; test için sentetik
profiller — [TEST_STRATEGY.md](../quality/TEST_STRATEGY.md)).

**"PII sızmaz" ilkesinin kapsamı:** [OBSERVABILITY.md](../quality/OBSERVABILITY.md)'deki
"PII loglanmaz" kuralı yalnızca logları kapsar. Aynı ilke üç yerde daha geçerlidir:
- **Analytics:** event'ler ID referanslıdır; profil alan değerleri veya serbest metin
  event payload'una girmez.
- **Backup:** yedekler kaynağıyla aynı hassasiyet sınıfındadır; şifrelenir, erişimi
  audit-log'lanır ve deletion sonrası rotasyon süresi içinde temizlenir.
- **Manual Review:** kuyruk kayıtlarında yalnızca kararı vermek için gereken alan tutulur;
  karar sonrası kullanıcıya bağlı alanlar anonimleştirilir.

**Yaş sınırı:** ❓ OPEN-11 — minimum kullanıcı yaşı ve reşit olmayan kullanıcı politikası
T-008'de karara bağlanır. Tasarım kısıtı şimdiden geçerlidir: yaş bilgisi gerekiyorsa
**tam doğum tarihi saklanmaz**; hesap düzeyinde türetilmiş bir uygunluk işareti kullanılır
ve bu işaret matching veri yoluna girmez.

## 4. Compliance ve Source Policy Riskleri

### 4.1 Veri koruma rejimleri

**Launch pazarı Türkiye'dir (D-009)**, dolayısıyla birincil rejim KVKK'dır. Ancak
compliance **country-specific bir extension katmanı** olarak tasarlanır: ikinci bir pazar
eklendiğinde (ör. AB/GDPR) core veri modeli ve akışlar değişmez; yalnızca bu katmandaki
kurallar — hukuki dayanak, retention süreleri, rıza metinleri, veri hakları süreleri,
ihlal bildirimi yükümlülükleri — eklenir. TR'ye özgü bir kuralı core varsayımı haline
getirmek D-009 ihlalidir.

Tasarım rejimden bağımsız olarak şunları varsayar: hukuki dayanak kaydı, rıza yönetimi,
veri hakları (erişim/export/silme/düzeltme), ihlal bildirimi süreci, işleme envanteri.
**Otomatik öneri sistemleri** için ek yükümlülük olabilir (öneri mantığının
açıklanabilirliği — D-005 bunu zaten ürün ilkesi yapar).

> Bu bölüm **hukuki görüş değildir** ve hiçbir ifadesi confirmed legal fact olarak
> okunmamalıdır. Yükümlülüklerin kapsamı ve uygulanışı T-008'de uzman doğrulamasından
> geçmeden kesinleşmez.

### 4.2 Source policy (özet — operasyonel çerçeve [SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md) §4)

| Risk | Açıklama | Duruş |
|---|---|---|
| ToS ihlali iddiası | Bir source otomatik erişimi yasaklıyor olabilir | `Rejected/Conditional` sınıflaması; insan onaysız crawl yok (D-002) |
| Telif/yeniden yayın | İlan metninin platformda gösterimi içerik hakları sorusu doğurur | Kullanıcıya özet + zorunlu alanlar + **orijinal source'a link ve atıf**; tam metin yeniden yayını yapılmaz; ❓ OPEN-06: gösterim sınırı (T-008) |
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
