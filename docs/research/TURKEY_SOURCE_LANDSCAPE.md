# TURKEY_SOURCE_LANDSCAPE.md — T-003 Araştırma Kanıtları

> **Purpose:** T-003'ün kanıt dosyası. Türkiye launch pazarı (D-009) için job source
> landscape'inin gerçek kaynaklara dayalı araştırması: aday kaynaklar, erişim ve policy
> kanıtları, cluster coverage değerlendirmesi ve MVP source wave önerileri.
> Registry kayıtları [SOURCE_REGISTRY.md](../architecture/SOURCE_REGISTRY.md) §5'te;
> policy çerçevesi [SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md) §4.
>
> **Bu dosya hukuki görüş içermez.** Buradaki hiçbir policy değerlendirmesi confirmed
> legal fact değildir; hepsi T-008 hukuki doğrulamasının girdisidir.

**Araştırma tarihi:** 2026-07-21 · **Yöntem:** yalnızca public erişim (robots.txt,
public ToS/sözleşme sayfaları, public listing sayfaları, sitemap'ler). Hiçbir kaynakta
login, CAPTCHA, paywall veya anti-automation önlemi aşılmamıştır; erişilemeyen kaynaklar
`Unknown` olarak işaretlenmiştir.

---

## 1. Executive Summary

Türkiye job source landscape'i **belirgin biçimde yoğunlaşmış** durumda. Üç MVP cluster'ı
için yapılan taramada, özel sektör ilanlarının pratikte birkaç büyük platformda toplandığı
görülüyor: kariyer.net (ve aynı grubun blue-collar markası isinolsun.com), yenibiris.com,
secretcv.com. Büyük hastane gruplarının (Acıbadem, Medical Park) hemşire ilanları bile
kendi kariyer sayfalarından çok bu platformlarda görünüyor — yani "company career page'ler
üzerinden yeterli coverage" hipotezi Türkiye için **zayıf** görünüyor (§4.2).

Araştırmanın en önemli bulgusu compliance tarafında: **hiçbir aday kaynak
koşulsuz `allowed` değil.** Teknik erişilebilirlik ile izin arasındaki fark burada çok
belirgin:

- **isinolsun.com** robots.txt açısından tamamen izinli (`Allow: /`) ve günlük güncellenen
  sitemap sunuyor — ama platform üyelik sözleşmesi §4.12 verilerin yazılı izin olmadan
  kopyalanmasını/çoğaltılmasını/dağıtılmasını yasaklıyor.
- **kariyer.net** robots.txt ilan sayfalarına izin veriyor ama hizmet sözleşmesi sayfası
  otomatik erişime **403** dönüyor; yani izin durumu doğrulanamıyor.
- **yenibiris.com** robots.txt'in kendisi **403** dönüyor — bu, anti-automation davranışının
  erken bir işareti.
- **tr.indeed.com** ve **linkedin.com** robots.txt'te iş ilanı path'lerini açıkça
  yasaklıyor; LinkedIn ayrıca dosyanın başında otomatik erişimi açık ifadeyle men ediyor.
- **Kamu kaynakları** (esube.iskur.gov.tr, kamuilan.sbb.gov.tr) robots açısından izinli
  ama **hiçbirinde açık bir yeniden kullanım lisansı bulunamadı**.

Bu tablo, [SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md) §4'teki **gri alan
kuralını** doğrudan devreye sokuyor: policy belirsizse source `Conditional` işaretlenir ve
**insan kararı olmadan crawl başlamaz.** Dolayısıyla T-003'ün sonucu bir "hemen başla"
tavsiyesi değil, **Conditional Go**'dur (§14).

İkinci önemli bulgu: **tek source ile core loop doğrulaması teknik olarak mümkün.**
isinolsun.com'un sitemap'i hem Logistics & Operations hem Office & Commercial cluster'ını
taşıyor (örnek: "ön muhasebe görevlisi", "barista", "iç mimar" aynı sitemap'te) — yani
Wave 1 kriteri "en az iki cluster" tek kaynakla karşılanabiliyor.

---

## 2. Source Candidate Karşılaştırma Tablosu

Ölçek: **Low / Medium / High** ordinal; sahte hassasiyet üretilmemiştir. Her skorun
gerekçesi §3'teki kartlarda.

| ID | Source | Tip | Cluster kapsamı | Public erişim | Auth | API/Feed | robots durumu | Permission confidence | Teknik erişim | Adapter karmaşıklığı | Policy riski | Önerilen statü |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| src-tr-001 | isinolsun.com | job_board | Log+Ops, Office | Public | none | Sitemap (XML) | `Allow: /` + sitemap | **Low** (sözleşme §4.12 reuse kısıtı) | High | Low | **Medium-High** | Candidate → UnderReview |
| src-tr-002 | kariyer.net | job_board | 3/3 | Public | none | Sitemap | İlan sayfaları izinli; hesap/CV path'leri disallow | **Unknown** (ToS 403) | High | Medium | **High** | UnderReview |
| src-tr-003 | yenibiris.com | job_board | 3/3 (varsayılan) | Unknown | Unknown | Unknown | **robots.txt 403** | **Unknown** | **Low** (403) | Unknown | **High** | Rejected (MVP) |
| src-tr-004 | secretcv.com | job_board | 3/3 | Public | none | Sitemap | Arama parametreleri (`?k=`,`?s=`,`?p=`) disallow | **Unknown** | Medium | Medium | **Medium-High** | UnderReview |
| src-tr-005 | eleman.net | job_board | Log+Ops ağırlıklı | Public | none | none | **`/is_ilanlari.php`, `?ilan_id=`, `*.html$` disallow** | **Low** (ilan path'leri disallow) | Low | Medium | **High** | Rejected (MVP) |
| src-tr-006 | esube.iskur.gov.tr | government_portal | 3/3 | Public (arama loginsiz) | none (arama) | none | `Allow: /` + 1 popup disallow | **Medium** (robots izinli, reuse lisansı yok) | Medium | **High** (ASP.NET postback) | **Medium** | Candidate → UnderReview |
| src-tr-007 | iskur.gov.tr (kurumsal) | government_portal | Kamu duyuruları | Public | none | Sitemap | **`/is-arama?*` ve `/*?*` disallow**; SEO bot'ları tamamen disallow | **Low** (arama path'leri disallow) | Medium | Medium | **Medium** | Rejected (ilan ingestion için) |
| src-tr-008 | kamuilan.sbb.gov.tr | government_portal | Kamu (3/3 dolaylı) | Public | none | none | robots.txt **yok (404)** | **Medium** (kısıt beyanı yok, izin beyanı da yok) | High | Low | **Low-Medium** | Candidate (listing-only) |
| src-tr-009 | ilan.gov.tr | government_portal | Kamu personel alımı | Unknown | Unknown | Unknown | **Unknown** (TLS sertifika hatası) | **Unknown** | **Unknown** | Unknown | Unknown | Candidate (doğrulama gerekli) |
| src-tr-010 | kariyerkapisi.cbiko.gov.tr | government_portal | Kamu | Unknown | Muhtemel e-Devlet | Unknown | **Unknown** (DNS çözülemedi) | **Unknown** | **Unknown** | Unknown | Unknown | Candidate (doğrulama gerekli) |
| src-tr-011 | kariyermerkezi.bogazici.edu.tr | university_portal | Office (entry-level) | Public | none | none | Drupal robots; **Crawl-delay: 10**; ilan path'leri disallow değil | **Medium** | High | Low | **Low** | Candidate (düşük hacim) |
| src-tr-012 | kpm.metu.edu.tr (ODTÜ KPM) | university_portal | Office (entry-level) | **Restricted** | **login wall** | none | — | **Rejected** (login arkası) | — | — | — | Rejected (D-002) |
| src-tr-013 | ATS-powered career pages (ör. `*.hrpeak.com`) | ats_page | Değişken | Public (tenant'a göre) | none | Tenant'a göre | Örnek: `careers.hrpeak.com` → `Disallow:` (tam izinli) | **Medium** (tenant ToS'una bağlı) | **Değişken** (örnek tenant 403 döndü) | Medium | **Medium** | Candidate (Wave 2+ araştırma) |
| src-tr-014 | tr.indeed.com | job_board (aggregator) | 3/3 | Public | none | Partner API | **`/job/`, `/jobs/`, `/viewjob?`, `/q-`, `/l-` disallow — AI bot'ları dahil** | **Rejected** | — | — | **High** | **Rejected** |
| src-tr-015 | linkedin.com | job_board | 3/3 | Kısmen | login (çoğu) | Partner API | **robots.txt başında otomatik erişim açıkça yasak**; `/jobs*` disallow | **Rejected** | — | — | **High** | **Rejected** |

---

## 3. Source Kartları (kanıt detayı)

> Aşağıdaki alanlar [SOURCE_REGISTRY.md](../architecture/SOURCE_REGISTRY.md) §3
> template'iyle hizalıdır. Doğrulanamayan her alan açıkça `Unknown`'dır.

### src-tr-001 — İşin Olsun (isinolsun.com)

| Alan | Değer |
|---|---|
| Source type | job_board (blue-collar odaklı; Kariyer.net grubu) |
| Covered clusters | **Logistics & Operations**, **Office & Commercial** (Healthcare kısmi) |
| Örnek occupation title'lar | sitemap'te gözlenen: "ön muhasebe görevlisi", "barista", "iç mimar" |
| Geographic coverage | TR geneli (city/town sitemap'leri mevcut) |
| Public access | Public — listing ve detay sayfaları loginsiz |
| Authentication | none |
| Official API | **none** (bulunamadı) |
| RSS/feed | **Sitemap index** — `https://isinolsun.com/sitemap.xml` (23 alt sitemap) |
| Structured data | Doğrulanmadı (`Unknown`) — job detail sayfasında JSON-LD kontrolü yapılmadı |
| robots.txt | `User-agent: * / Allow: / ` + `Sitemap: https://isinolsun.com/sitemap.xml` — **kısıt yok** |
| Terms/policy | Platform Üyelik Sözleşmesi **§4.12**: verilerin "Kariyer.net'in bilgisi veya yazılı onayı dışında herhangi bir şekilde kopyalanması, çoğaltılması ve dağıtılması" yasak. **Kapsam:** hüküm üyeler (Müşteriler/Adaylar) için yazılmış; üye olmayan ziyaretçiye uygulanabilirliği **Unknown** |
| Scraping permission confidence | **Low** — robots izinli ama operatörün veri yeniden kullanımına açık itirazı var |
| Technical accessibility | **High** — sitemap ile keşif, temiz URL, günlük `lastmod` |
| Pagination model | Sitemap tabanlı keşif (listing pagination'a gerek yok) |
| Job detail page | Var — `https://isinolsun.com/is-ilani/{başlık}-{şirket}-{id}` |
| Estimated job volume | `jobdetailsitemap1.xml` + `jobdetailsitemap2.xml`; tek dosyada **1000+ URL gözlendi** (fetch truncate edildi, gerçek sayı daha yüksek) |
| Volume estimation method | Sitemap URL sayımı (kısmi; tam sayım yapılmadı) |
| Posting freshness | **High** — sitemap `lastmod` 2026-07-21T02:10 (araştırma günü) |
| Employer identity quality | **High** — şirket adı URL slug'ında ve ayrıca 13 adet `companylistsitemap` mevcut |
| Salary data | `Unknown` |
| Location data quality | **High** — city/town/position kırılımlı sitemap'ler |
| Requirement detail quality | `Unknown` (detay sayfası incelenmedi) |
| Duplicate/repost riski | **Medium** — aynı grup içindeki kariyer.net ile çapraz yayın olasılığı yüksek |
| Agency-copy riski | **Medium** (`Unknown` — ölçülmedi) |
| Public-sector davranışı | Yok |
| Adapter complexity | **Low** — sitemap + detay sayfası |
| Expected maintenance | **Low-Medium** |
| Policy riski | **Medium-High** — §4.12 nedeniyle |
| Önerilen statü | `Candidate` → **UnderReview** (yazılı izin talebi önerilir) |
| Evidence | [robots.txt](https://isinolsun.com/robots.txt) · [sitemap](https://isinolsun.com/sitemap.xml) · [jobdetailsitemap1](https://isinolsun.com/sitemaps/jobdetailsitemap1.xml) · [Platform Üyelik Sözleşmesi](https://isinolsun.com/sozlesmeler/platform-uyelik-sozlesmesi) |
| Last reviewed | 2026-07-21 |
| Notes / open questions | §4.12'nin üye olmayan otomatik erişime uygulanıp uygulanmadığı **hukuki soru** (T-008). Site genel "kullanım koşulları" sayfası ayrıca aranmalı. |

### src-tr-002 — Kariyer.net

| Alan | Değer |
|---|---|
| Source type | job_board (pazarın en büyüğü) |
| Covered clusters | **3/3** — Healthcare dahil (Acıbadem, Medical Park hemşire ilanları burada görünüyor) |
| Public access | Public (ilan sayfaları) |
| Authentication | none (görüntüleme) |
| Official API | **none** (public API bulunamadı) |
| RSS/feed | `Sitemap: https://www.kariyer.net/sitemapxml` |
| robots.txt | 43 disallow kuralı; **ilan sayfaları disallow değil**; `/ozgecmis/*`, `/hesabim`, `/aday/giris`, `/basvuru-*`, `/filtre/*` disallow. Crawl-delay yok |
| Terms/policy | **Unknown** — `https://www.kariyer.net/veri-politikamiz/hizmet-sozlesmesi` otomatik erişime **HTTP 403** döndü; içerik doğrulanamadı |
| Scraping permission confidence | **Unknown** — robots izin veriyor ama sözleşme okunamadı; **"izin var" varsayılamaz** |
| Technical accessibility | **High** (ilan sayfaları) |
| Estimated job volume | Pazar lideri; ilan hacmi **High** (nicel doğrulama yapılmadı) |
| Employer identity quality | **High** — firma profil sayfaları mevcut (`/firma-profil/...`) |
| Duplicate/repost riski | **High** — diğer platformlarla ve isinolsun ile çapraz yayın |
| Adapter complexity | **Medium** |
| Policy riski | **High** — ToS doğrulanamadı + pazar lideri konumu ihtilaf riskini artırır |
| Önerilen statü | **UnderReview** — T-008 öncesi crawl önerilmez |
| Evidence | [robots.txt](https://www.kariyer.net/robots.txt) · [hizmet sözleşmesi (403)](https://www.kariyer.net/veri-politikamiz/hizmet-sozlesmesi) |
| Last reviewed | 2026-07-21 |

### src-tr-003 — Yenibiriş (yenibiris.com)

| Alan | Değer |
|---|---|
| robots.txt | **HTTP 403 Forbidden** — robots.txt'in kendisi otomatik istemciye kapalı |
| Yorum | Bu, [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) FS-12'de tanımlanan **access-change / anti-automation imzasının** erken bir örneği. robots.txt okunamadığı için crawl kuralları bilinemez |
| Scraping permission confidence | **Unknown** — ve robots okunamadan crawl başlatmak D-002 ile uyumsuz |
| Önerilen statü | **Rejected (MVP)** — bypass denenmez; ileride resmi feed/izin yolu araştırılabilir |
| Evidence | [robots.txt (403)](https://www.yenibiris.com/robots.txt) |
| Last reviewed | 2026-07-21 |

### src-tr-004 — SecretCV (secretcv.com)

| Alan | Değer |
|---|---|
| robots.txt | `User-agent: *` için arama/parametre path'leri disallow (`?k=`, `?s=`, `?p=`, `/hesabim`, `/banner/redirect/*`). **GPTBot ve OAI-SearchBot açıkça `Allow`** |
| Sitemap | `https://www.secretcv.com/sitemap` |
| Yorum | Site, belirli AI crawler'larına açık izin verirken genel arama parametrelerini kapatmış — yani crawler ayrımı yapan bilinçli bir politika var. Bizim user-agent'ımız için geçerli kural `User-agent: *` bloğudur |
| Covered clusters | 3/3 (Acıbadem gibi sağlık grubu firma sayfaları mevcut) |
| Scraping permission confidence | **Unknown** — ToS incelenmedi |
| Adapter complexity | **Medium** — arama parametreleri disallow olduğu için keşif sitemap'e bağımlı |
| Policy riski | **Medium-High** |
| Önerilen statü | **UnderReview** |
| Evidence | [robots.txt](https://www.secretcv.com/robots.txt) |
| Last reviewed | 2026-07-21 |

### src-tr-005 — Eleman.net

| Alan | Değer |
|---|---|
| robots.txt | **`Disallow: /is_ilanlari.php`**, **`Disallow: *?ilan_id=*`**, `Disallow: /*.html$`, `/firmalar.php`, `/basvuru_yap.php`, `/cv_guncelle.php` |
| Yorum | **İlan listeleme ve ilan detayı path'lerinin ikisi de disallow.** Blue-collar coverage'ı cazip olsa da robots kuralları ingestion'ın çekirdeğini kapatıyor |
| Scraping permission confidence | **Low** — robots açıkça ilan path'lerini kapatıyor |
| Önerilen statü | **Rejected (MVP)** — robots'a uyum gereği (FR-204) |
| Evidence | [robots.txt](https://www.eleman.net/robots.txt) |
| Last reviewed | 2026-07-21 |

### src-tr-006 — İŞKUR e-Şube (esube.iskur.gov.tr)

| Alan | Değer |
|---|---|
| Source type | government_portal (özel **ve** kamu işveren açık iş ilanları) |
| Covered clusters | **3/3** — meslek bazlı arama mevcut (`AcikIsMeslek.aspx`) |
| Public access | **Public** — açık iş arama formu loginsiz kullanılabiliyor; kayıt yalnızca kaydedilmiş arama gibi ek özellikler için |
| Authentication | none (arama için) |
| Official API | **none** bulunamadı. `data.gov.tr` üzerinde İŞKUR açık veri seti araması **sonuçsuz** kaldı (`Unknown` — portal doğrudan taranmadı) |
| robots.txt | `User-agent: * / Allow: /` + yalnızca `/Meslek/ViewMeslekDetayPopUp.aspx/` disallow |
| Terms/policy | Sayfada yalnızca **"Türkiye İş Kurumu ©2026"** telif ibaresi görüldü; **yeniden kullanım lisansı bulunamadı** (`Unknown`) |
| Scraping permission confidence | **Medium** — robots izinli, kurum kamu hizmeti sunuyor; ama açık reuse izni yok |
| Technical accessibility | **Medium** |
| Pagination model | **ASP.NET postback (`__doPostBack`)** — GET parametreli sayfalama değil |
| Adapter complexity | **High** — form state/ViewState yönetimi gerekir; bu bir *teknik* maliyettir, bypass değildir |
| Estimated job volume | **High** (nicel doğrulama yapılmadı) |
| Employer identity quality | `Unknown` — İŞKUR ilanlarında işveren adı bazen gizli olabilir (doğrulanmadı) |
| Posting freshness | `Unknown` — ilan tarih aralığı filtresi mevcut, güvenilirliği ölçülmedi |
| Public-sector davranışı | Kamu işveren ilanları da içeriyor → D-015 listing-only kuralı bu alt küme için geçerli |
| Policy riski | **Medium** |
| Önerilen statü | `Candidate` → **UnderReview**; kurumla resmi veri paylaşımı talebi tercih edilen yol (SCRAPING_SYSTEM §4/5) |
| Evidence | [robots.txt](https://esube.iskur.gov.tr/robots.txt) · [Açık İş İlan Ara](https://esube.iskur.gov.tr/Istihdam/AcikIsIlanAra.aspx) · [Meslek bazında](https://esube.iskur.gov.tr/Istihdam/AcikIsMeslek.aspx) |
| Last reviewed | 2026-07-21 |

### src-tr-007 — İŞKUR Kurumsal (iskur.gov.tr)

| Alan | Değer |
|---|---|
| robots.txt | `User-agent: *` için **`Disallow: /is-arama?*`**, **`Disallow: /*?*`** (bütün query-string URL'leri), `/search?*`, `/*?sayfa=*`. Googlebot/Bingbot/YandexBot/DuckDuckBot'a `Allow: /` + Crawl-delay; SemrushBot/AhrefsBot/MJ12bot/DotBot/BLEXBot **tamamen disallow**; `User-agent: *bot*` → Crawl-delay: 5 |
| Yorum | **Aynı kurumun iki host'u iki farklı policy taşıyor.** Kurumsal sitede iş arama path'i açıkça kapalı; e-şube host'unda açık. Bu ayrım Source Registry'de iki ayrı kayıt olarak tutulmalı |
| Scraping permission confidence | **Low** (iş ilanı ingestion'ı için) |
| Önerilen statü | **Rejected (ilan ingestion için)** — duyuru/istatistik sayfaları ayrı değerlendirilebilir |
| Evidence | [robots.txt](https://www.iskur.gov.tr/robots.txt) |
| Last reviewed | 2026-07-21 |

### src-tr-008 — Kamu İlan (kamuilan.sbb.gov.tr)

| Alan | Değer |
|---|---|
| Source type | government_portal — T.C. Cumhurbaşkanlığı Strateji ve Bütçe Başkanlığı |
| Covered clusters | Kamu personel alımı (memur, sözleşmeli, akademik, işçi) — üç cluster'a **dolaylı** dokunur (kamu hastanesi hemşire, kamu şoför/işçi alımları) |
| Public access | **Public**, loginsiz |
| robots.txt | **Yok (HTTP 404)** — kısıt beyanı yok; izin beyanı da yok |
| Terms/policy | Footer: "Her hakkı saklıdır. © 2021" + hukuki uyarı linki (içerik incelenmedi, `Unknown`) |
| Scraping permission confidence | **Medium** — robots kısıtı yok, kamu duyurusu niteliği; ama açık reuse lisansı yok |
| Estimated job volume | **Low** — sayfada "TÜM İLANLAR 81 ilan" görüldü |
| Adapter complexity | **Low** |
| Public-sector davranışı | **Tamamı kamu** → D-015 **listing-only / guidance mode** zorunlu; Match Score üretilmez |
| Policy riski | **Low-Medium** |
| Önerilen statü | `Candidate` — listing-only besleyici olarak uygun, **core loop doğrulaması için uygun değil** (skor üretmiyor) |
| Evidence | [kamuilan.sbb.gov.tr](https://kamuilan.sbb.gov.tr/) · [robots.txt (404)](https://kamuilan.sbb.gov.tr/robots.txt) |
| Last reviewed | 2026-07-21 |

### src-tr-009 — ilan.gov.tr (Basın İlan Kurumu)

| Alan | Değer |
|---|---|
| Source type | government_portal — resmi ilan portalı; "Personel Alımı" kategorisi mevcut |
| Erişim denemesi | `https://www.ilan.gov.tr/robots.txt` ve `https://ilan.gov.tr/robots.txt` → **TLS hatası: "unable to verify the first certificate"** |
| Bütün policy/erişim alanları | **Unknown** — otomatik erişim doğrulanamadı |
| Önerilen statü | `Candidate` — **elle doğrulama gerekli** (sertifika zinciri sorunu ortamsal da olabilir) |
| Evidence | [ilan.gov.tr personel alımı kategorisi](https://www.ilan.gov.tr/ilan/tum-ilanlar/personel-alimi?ats=5) (arama sonucundan; içerik doğrulanmadı) |
| Last reviewed | 2026-07-21 |

### src-tr-010 — Kariyer Kapısı (kariyerkapisi.cbiko.gov.tr)

| Alan | Değer |
|---|---|
| Source type | government_portal — Cumhurbaşkanlığı İnsan Kaynakları Ofisi; kamu işe alım başvuru platformu |
| Erişim denemesi | `kariyerkapisi.cbiko.gov.tr` → **DNS çözülemedi (ENOTFOUND)**; `kariyerkapisi.gov.tr/robots.txt` → **404** |
| Yorum | Platform e-Devlet entegrasyonlu; başvuru akışı büyük olasılıkla kimlik doğrulaması gerektiriyor (**doğrulanmadı**). İlan **listeleme** kısmının public olup olmadığı `Unknown` |
| Önerilen statü | `Candidate` — elle doğrulama gerekli; login arkasındaysa D-015 listing-only bile uygulanamaz |
| Evidence | [kariyerkapisi.cbiko.gov.tr](https://kariyerkapisi.cbiko.gov.tr/) (erişilemedi) · [SSS](https://isealimkariyerkapisi.cbiko.gov.tr/sss) |
| Last reviewed | 2026-07-21 |

### src-tr-011 — Boğaziçi Üniversitesi Kariyer Merkezi

| Alan | Değer |
|---|---|
| Source type | university_portal |
| Covered clusters | Office & Commercial (entry-level/staj ağırlıklı) |
| Public access | **Public** — ilanların herkese açık olduğu belirtiliyor |
| robots.txt | Standart Drupal; **Crawl-delay: 10**; `/admin/`, `/user/*`, `/search/` disallow. **İlan path'leri disallow değil** |
| Scraping permission confidence | **Medium** |
| Estimated job volume | **Low** |
| Adapter complexity | **Low** (Drupal, düzenli yapı) |
| Policy riski | **Low** |
| Önerilen statü | `Candidate` — düşük hacim; MVP cluster'larına katkısı sınırlı |
| Evidence | [robots.txt](https://kariyermerkezi.bogazici.edu.tr/robots.txt) · [İş ve Staj İlanları](https://kariyermerkezi.bogazici.edu.tr/tr/is-ve-staj-ilanlari) |
| Last reviewed | 2026-07-21 |

### src-tr-012 — ODTÜ Kariyer Planlama Merkezi (kpm.metu.edu.tr)

| Alan | Değer |
|---|---|
| Public access | **Restricted** — kaynak kendi ifadesiyle "üye olup **sadece bir ODTÜ'lünün görebileceği** ilanları görebilir" |
| Authentication | **login wall** |
| Önerilen statü | **Rejected** — D-002 gereği login arkasındaki içerik kapsam dışıdır; bypass **önerilmez ve tasarlanmaz** |
| Evidence | [ODTÜ KPM](https://kpm.metu.edu.tr/) |
| Last reviewed | 2026-07-21 |

### src-tr-013 — ATS-powered career page'ler (örnek: `*.hrpeak.com`)

| Alan | Değer |
|---|---|
| Source type | ats_page — çok kiracılı (multi-tenant) ATS altyapısı |
| Gözlem | `careers.hrpeak.com/robots.txt` → `User-agent: * / Disallow:` (**tam izinli**). Ancak örnek bir tenant sayfası (`tss.hrpeak.com/jobs`) → **HTTP 403** |
| Yorum | ATS altyapısı robots açısından açık olsa bile **her tenant kendi erişim davranışını ve ToS'unu taşıyabiliyor.** Bu yüzden "ATS provider onaylandı" denemez; **tenant bazında** değerlendirme gerekir |
| Türkiye'de yaygın ATS'ler | Arama sonuçlarına göre SAP SuccessFactors, Workday, Oracle Taleo, Greenhouse, Lever ve yerel çözümler kullanılıyor (**public job endpoint'leri doğrulanmadı** — `Unknown`) |
| Scraping permission confidence | **Medium** (provider) / **Unknown** (tenant) |
| Adapter complexity | **Medium** — bir ATS için yazılan adapter aynı provider'ın diğer tenant'larına yeniden kullanılabilir (**kaldıraç fırsatı**) |
| Önerilen statü | `Candidate` — Wave 2+ için **en umut verici uzun vadeli yol**; T-003 kapsamında tam envanter çıkarılmadı |
| Evidence | [careers.hrpeak.com/robots.txt](https://careers.hrpeak.com/robots.txt) · [tss.hrpeak.com/jobs (403)](https://tss.hrpeak.com/jobs) |
| Last reviewed | 2026-07-21 |

### src-tr-014 — Indeed Türkiye (tr.indeed.com) — **Rejected**

robots.txt genel user-agent'lar için `/job/`, `/jobs/`, `/viewjob?`, `/q-`, `/l-`
path'lerini **disallow** ediyor; ayrıca `Claude-User` ve `anthropic-ai` dahil AI
crawler'ları için **genişletilmiş disallow listesi** var. İş ilanı ingestion'ı için
robots kurallarına uyum (FR-204) gereği **Rejected**. Bypass önerilmez.
Evidence: [robots.txt](https://tr.indeed.com/robots.txt) · Kontrol: 2026-07-21

### src-tr-015 — LinkedIn — **Rejected**

robots.txt dosyasının başında açık ifade: *"The use of robots or other automated means to
access LinkedIn without the express permission of LinkedIn is strictly prohibited."*
`/jobs?runSearch*`, `/jobs-guest/`, `/api/jobPostings/jobs*` vb. disallow. İçeriğin
önemli bölümü ayrıca login arkasında. **Rejected** (D-002). İzin yolu yalnızca
LinkedIn'in kendi belirttiği başvuru kanalıdır.
Evidence: [robots.txt](https://www.linkedin.com/robots.txt) · Kontrol: 2026-07-21

---

## 4. Özel Araştırma Konuları

### 4.1 İlanlar birkaç büyük platformda mı yoğunlaşıyor? — **Evet (Medium-High güven)**

Pazar taraması kariyer.net'i açık ara lider gösteriyor (25M+ CV, 94.000+ üye firma
iddiası — kaynağın kendi beyanı, bağımsız doğrulanmadı). Blue-collar tarafında
isinolsun.com (aynı grup) ve eleman.net öne çıkıyor. Beyaz yakada yenibiris.com ve
secretcv.com. **Sonuç:** compliant-only strateji (D-002) altında, pazarın en yoğun
kanallarının önemli bölümü ya `Unknown` ya `Rejected` durumunda — bu, R-01 (kapsama
açığı) riskini **doğruluyor**.

### 4.2 Company career page'ler yeterli coverage sağlar mı? — **Muhtemelen hayır (Medium güven)**

Aksi yönde güçlü bir sinyal bulundu: Türkiye'nin en büyük özel hastane gruplarının
(Acıbadem, Medical Park) hemşire ilanları **kendi kariyer sayfalarından çok** kariyer.net,
secretcv ve Indeed üzerinde görünüyor. Yani Türkiye'de company career page, ilanın
*birincil* değil *ikincil* yayın kanalı gibi davranıyor. Bu, "büyük platformları
atlayıp doğrudan şirketlerden toplayalım" stratejisinin Türkiye'de ABD'ye kıyasla çok
daha zayıf olacağını düşündürüyor. **Nicel doğrulama T-021'in işi** (§12).

### 4.3 Türkiye'de ATS provider'lar ve public endpoint'ler — **Kısmen (Low-Medium güven)**

SAP SuccessFactors, Workday, Oracle Taleo, Greenhouse, Lever ve yerel çözümlerin
kullanıldığına dair sinyal var; ancak **public job endpoint envanteri çıkarılmadı**.
Gözlemlenen tek somut örnek (`hrpeak`) provider seviyesinde tam izinli robots, tenant
seviyesinde 403 gösterdi. **ATS yolu Wave 2+ için en umut verici uzun vadeli kaldıraç**
(bir adapter → çok tenant), ama T-003 kapsamında doğrulanamadı → `Unknown`.

### 4.4 Healthcare ilanları nerede yoğunlaşıyor? — büyük job board'lar

Acıbadem ve Medical Park ilanları kariyer.net ve secretcv üzerinde bulundu. İŞKUR e-şube
meslek bazlı arama sunduğu için hemşire/sağlık teknisyeni ilanlarını da taşıyor
(doğrulanmadı, `Unknown`). Kamu sağlık personeli alımları kamuilan.sbb.gov.tr ve
Kariyer Kapısı üzerinden yürüyor → **D-015 listing-only** kapsamına girer.

### 4.5 Driver / warehouse ilanları nerede yoğunlaşıyor? — isinolsun + eleman.net + İŞKUR

isinolsun.com blue-collar odaklı ve robots açısından en erişilebilir kaynak.
eleman.net aynı segmentte güçlü ama **robots ilan path'lerini kapatıyor**. İŞKUR e-şube
bu segmentte yüksek hacimli (kamu ve özel işveren açık işleri).

### 4.6 Accountant / sales ilanları nerede yoğunlaşıyor? — kariyer.net, secretcv, isinolsun

isinolsun sitemap'inde "ön muhasebe görevlisi" gözlendi → **Office & Commercial
cluster'ının isinolsun tarafından da taşındığı doğrulandı.** Bu, Wave 1'in "en az iki
cluster" kriterini tek kaynakla karşılamasını mümkün kılıyor.

### 4.7 İŞKUR ve kamu kaynaklarının erişim/reuse koşulları — **Kısmen açık, lisans yok**

- `esube.iskur.gov.tr`: robots `Allow: /`, arama loginsiz → **teknik erişim açık**.
- `iskur.gov.tr`: `/is-arama?*` ve bütün query-string'ler **disallow** → aynı kurumda
  farklı politika.
- Hiçbirinde **açık veri lisansı veya yeniden kullanım izni bulunamadı**; yalnızca telif
  ibaresi var. `data.gov.tr` üzerinde İŞKUR veri seti araması sonuçsuz kaldı (`Unknown`).
- **Öneri:** kurumla resmi veri paylaşımı/feed talebi — SCRAPING_SYSTEM §4/5'in "tercih
  edilen yol" dediği seçenek.

### 4.8 Kamu ilanları listing-only için kullanılabilir mi? — **Evet**

kamuilan.sbb.gov.tr temiz, public, robots kısıtsız ve tamamen kamu personel alımı içeriyor.
D-015 listing-only / guidance mode için **uygun**. Ancak hacim düşük (görülen: 81 ilan) ve
Match Score üretilmediği için **core loop doğrulamasına katkısı yok**.

### 4.9 Çapraz yayın sıklığı ve dedupe riski — **High (tahmini)**

isinolsun ve kariyer.net aynı grup; hastane gruplarının ilanları birden çok platformda
görüldü. **Nicel ölçüm yapılmadı** — bu, T-021'in ölçmesi gereken kalemlerden biri.
Tasarım tarafında karşılığı hazır: SCRAPING_SYSTEM §6 çoklu blocking geçidi (Geçit A
employer+title+location, Geçit B location+occupation+fingerprint).

### 4.10 Agency ilanlarında işveren gizleme oranı — **Unknown**

Ölçülmedi. isinolsun URL slug'ında şirket adı bulunması olumlu sinyal; ancak agency
ilanlarında bu alanın agency adını mı gerçek işvereni mi taşıdığı **doğrulanmadı**.
T-021 örnekleminde ölçülmeli (§12).

### 4.11 published_at / expiration güvenilirliği — **Kısmen**

isinolsun sitemap'i `lastmod` veriyor ama bu **sitemap güncelleme zamanı**, ilanın yayın
tarihi değil — bütün kayıtlar aynı timestamp'i taşıyor. Gerçek `posted_at` detay
sayfasından çıkarılmalı (`Unknown`). İŞKUR arama formunda ilan tarih aralığı filtresi var.
Bu, METRICS'teki "posted_at bilinmeyen kayıtlar için lag ölçümü" uyarısını **doğruluyor**.

### 4.12 HTML değişikliği ve bakım riski — **Medium**

isinolsun sitemap tabanlı olduğu için keşif katmanı dayanıklı; kırılganlık detay sayfası
parser'ında. İŞKUR e-şube ASP.NET WebForms olduğu için postback/ViewState değişimlerine
karşı **daha kırılgan**. R-10 (parser kırılganlığı, olasılık H) bu araştırmayla doğrulandı.

### 4.13 Login wall / anti-automation'a sonradan geçişi nasıl gözleriz?

Bu araştırma sırasında **canlı iki örnek** görüldü: yenibiris.com robots.txt'e 403,
kariyer.net sözleşme sayfasına 403, hrpeak tenant'ına 403. Tasarımdaki karşılığı hazır:
[SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md) §3 Fetcher **access-change
detection** ve FS-12. Bu araştırma, o mekanizmanın **spekülatif olmadığını** gösteriyor —
davranış Türkiye pazarında yaygın. Ek öneri: Source Record'daki
`access_change_detected_at` alanı ilk crawl'dan itibaren doldurulmalı.

### 4.14 Cluster başına minimum kaç source gerekir? — **tahmini 2-3**

- *Logistics & Operations:* isinolsun tek başına anlamlı hacim veriyor → **1-2**
- *Office & Commercial:* isinolsun + bir beyaz yaka kaynağı → **2**
- *Healthcare:* büyük board'lar + İŞKUR + kamu portalı → **2-3** (en zor cluster)

Bu tahminler **nicel doğrulanmadı**; T-021'in çıktısı bunları düzeltecektir.

### 4.15 Core loop tek source ile doğrulanabilir mi? — **Evet**

isinolsun.com hem Logistics & Operations hem Office & Commercial cluster'ını taşıyor,
sitemap ile keşif sağlıyor ve günlük güncelleniyor. Bu, ROADMAP M2'nin "1 source ile core
loop" hedefini ve T-017'nin düzeltilmiş dependency yapısını **teknik olarak destekliyor**.
Kısıt teknik değil, **policy** tarafında (§4.12 reuse hükmü).

---

## 5. Cluster Bazında Coverage Değerlendirmesi

| Cluster | Erişilebilir aday kaynaklar | Tahmini coverage | Güven | Ana risk |
|---|---|---|---|---|
| **Logistics & Operations** (Driver, Warehouse Worker) | isinolsun (High), İŞKUR e-şube (High), kamuilan (Low) | **Medium-High** | Medium | En iyi iki kaynağın ikisi de policy `Conditional` |
| **Office & Commercial** (Accountant, Sales Rep) | isinolsun (Medium), kariyer.net (High ama Unknown), secretcv (Medium), Boğaziçi (Low) | **Medium** | Low-Medium | Beyaz yakada en zengin kaynaklar `Unknown`/`Rejected` |
| **Healthcare** (Nurse, Health Technician) | kariyer.net (High ama Unknown), secretcv (Medium), İŞKUR (Unknown), kamuilan (listing-only) | **Low-Medium** | Low | **En kırılgan cluster** — özel hastane ilanları ağırlıkla erişimi belirsiz platformlarda |

> **Uyarı:** Bu tablodaki "coverage" değerleri **nicel ölçüme dayanmıyor**; kaynak
> mevcudiyeti ve erişilebilirliğine dayalı niteliksel tahmindir. Gerçek coverage T-021'in
> örneklem denetimiyle ölçülecektir (§12). Healthcare cluster'ının zayıflığı, D-008'in
> cluster seçiminin yeniden değerlendirilmesini gerektirebilir — bu bir **kullanıcı
> kararıdır**.

---

## 6. MVP Source Waves

### Wave 1 — Core Loop Validation (tek source)

**Öneri: `src-tr-001` — isinolsun.com — durum: CONDITIONAL**

*Neden bu:*
- Robots açısından **tam izinli** (`Allow: /`) ve sitemap sunuyor → keşif katmanı dayanıklı.
- **İki MVP cluster'ını birden taşıyor** (Logistics & Operations + Office & Commercial) —
  Wave 1 kriterini karşılayan tek aday.
- Günlük `lastmod`, temiz URL, şirket adı slug'da → employer identity ve freshness için
  iyi başlangıç.
- Adapter karmaşıklığı **Low** → core loop'a odaklanmayı sağlar.

*Neden koşullu:*
- Platform Üyelik Sözleşmesi §4.12 verilerin yazılı izin olmadan çoğaltılmasını yasaklıyor.
  Hükmün üye olmayan otomatik erişime uygulanıp uygulanmadığı **hukuki bir sorudur** ve
  bu doküman onu cevaplamaz.
- **Zorunlu ön adım:** Kariyer.net grubuna **yazılı izin/feed talebi** (SCRAPING_SYSTEM §4
  madde 5: işbirliği tercih edilen yoldur). İzin alınırsa `Allowed`; alınmazsa veya
  cevapsız kalırsa T-008 rubriği (OPEN-09) karar verene kadar **crawl başlatılmaz**.

*Neden diğerleri Wave 1 değil:*
- kariyer.net: ToS doğrulanamadı + pazar lideri → en yüksek policy riski.
- İŞKUR e-şube: policy daha savunulabilir ama **adapter karmaşıklığı High** (postback);
  Wave 1'in amacı matching loop'unu doğrulamak, adapter mühendisliğiyle boğuşmak değil.
- kamuilan.sbb.gov.tr: D-015 gereği **skor üretmiyor** → core loop doğrulanamaz.

### Wave 2 — Coverage and Deduplication (iki ek source)

| Öneri | Neden | Durum |
|---|---|---|
| **`src-tr-006` İŞKUR e-Şube** | 3/3 cluster, yüksek hacim, **farklı işveren havuzu** (isinolsun ile örtüşmesi düşük → gerçek cross-source dedupe testi); Healthcare cluster'ını güçlendirir | CONDITIONAL — resmi veri paylaşımı talebi önerilir |
| **`src-tr-008` kamuilan.sbb.gov.tr** | Kamu segmenti; **D-015 listing-only davranışını gerçek veriyle test etme** imkânı; robots kısıtsız, adapter Low | CONDITIONAL — düşük hacim kabul edilerek |

*Dedupe test değeri:* isinolsun (özel/blue-collar) + İŞKUR (özel+kamu karma) kombinasyonu,
aynı işverenin aynı ilanı iki kanalda yayınlaması senaryosunu üretmeye elverişli — bu tam
olarak T-015'in test etmesi gereken durum.

### Fallback Sources

| Fallback | Ne zaman devreye girer | Not |
|---|---|---|
| **`src-tr-004` secretcv.com** | isinolsun izni alınamazsa beyaz yaka + healthcare ikamesi | Arama parametreleri disallow → keşif sitemap'e bağımlı; ToS incelenmeli |
| **`src-tr-011` Boğaziçi Kariyer Merkezi** | Düşük hacimli ama **policy riski en düşük** aday; acil durumda "en azından bir kaynak" güvencesi | Crawl-delay 10'a uyulmalı; hacim Low |
| **`src-tr-013` ATS tenant'ları** | Orta vadede en ölçeklenebilir yol | Tenant bazlı ToS incelemesi gerekir; T-003'te envanter çıkarılmadı |

### Restricted / Rejected Sources

| Source | Gerekçe | Bypass? |
|---|---|---|
| **tr.indeed.com** | robots.txt iş ilanı path'lerini açıkça disallow (AI crawler'ları dahil) | **Hayır — önerilmez** |
| **linkedin.com** | robots.txt'te açık otomatik erişim yasağı + login wall | **Hayır — önerilmez** |
| **eleman.net** | robots `/is_ilanlari.php` ve `?ilan_id=` disallow → ingestion çekirdeği kapalı | **Hayır — önerilmez** |
| **yenibiris.com** | robots.txt'in kendisi 403; crawl kuralları bilinemiyor | **Hayır — önerilmez** |
| **kpm.metu.edu.tr (ODTÜ)** | İlanlar login arkasında (üyeye özel) | **Hayır — D-002** |
| **iskur.gov.tr (kurumsal host)** | `/is-arama?*` ve `/*?*` disallow | **Hayır** — e-şube host'u ayrı değerlendirilir |

> Bu kaynakların hiçbiri için teknik atlatma yöntemi araştırılmamış, önerilmemiş veya
> tasarlanmamıştır. `Rejected` kayıtlar silinmez; koşullar değişirse (resmi API, yazılı
> izin) `UnderReview`'a döner.

---

## 7. Adapter Feasibility Özetleri (Wave 1 ve Wave 2)

### isinolsun.com (Wave 1)

| Boyut | Değerlendirme |
|---|---|
| Keşif | Sitemap index → `jobdetailsitemap{1,2}.xml`; pagination gerekmez |
| Detay toplama | Temiz URL; her ilan ayrı sayfa |
| Alan çıkarımı | `Unknown` — JSON-LD/structured data varlığı **doğrulanmadı**; adapter geliştirmeden önce kontrol edilmeli |
| Employer identity | Slug'da şirket adı + `companylistsitemap` × 13 → normalize için iyi girdi |
| Kırılganlık | Detay sayfası HTML değişimine duyarlı; keşif katmanı dayanıklı |
| Tahmini onboarding eforu | **Low** (birkaç gün mertebesi — nicel tahmin yapılmadı) |
| Tahmini aylık bakım | **Low-Medium** |

### İŞKUR e-Şube (Wave 2)

| Boyut | Değerlendirme |
|---|---|
| Keşif | `AcikIsMeslek.aspx` meslek bazlı; sitemap yok |
| Pagination | **ASP.NET postback** — form state yönetimi gerekir (teknik maliyet, bypass değil) |
| Alan çıkarımı | `Unknown` |
| Employer identity | `Unknown` — İŞKUR ilanlarında işveren gizliliği olasılığı araştırılmalı |
| Kırılganlık | **High** — WebForms yapısı değişimlerine duyarlı |
| Tahmini onboarding eforu | **High** |
| Tahmini aylık bakım | **Medium-High** |

### kamuilan.sbb.gov.tr (Wave 2)

| Boyut | Değerlendirme |
|---|---|
| Keşif | Tek liste sayfası; tarih grupları |
| Pagination | Var (yapı doğrulanmadı) |
| Alan çıkarımı | `Unknown` — ilanlar çoğunlukla PDF/duyuru metni olabilir (**kontrol edilmeli**) |
| Özel davranış | D-015 listing-only; Match Score üretilmez |
| Tahmini onboarding eforu | **Low** |
| Tahmini aylık bakım | **Low** |

---

## 8. Riskler

### 8.1 Source coverage riskleri

- **R-01 doğrulandı ve keskinleşti:** pazarın en yoğun kanalları `Unknown`/`Rejected`.
  Compliant-only strateji altında gerçek coverage'ın hedefin (≥%60) altında kalma ihtimali
  **gerçek**.
- **Healthcare en kırılgan cluster** — özel hastane ilanları ağırlıkla erişimi belirsiz
  platformlarda. D-008 cluster seçiminin yeniden değerlendirilmesi gerekebilir.
- Wave 1 ve Wave 2 önerilerinin **üçü de `Conditional`** — hiçbiri "hemen başlanabilir"
  değil.

### 8.2 Employer identity ve duplicate detection riskleri

- isinolsun ↔ kariyer.net aynı grup → çapraz yayın olasılığı yüksek; ama kariyer.net
  MVP'de olmadığı için bu duplicate MVP'de görünmeyebilir (**dedupe testini zayıflatır**).
- Agency ilanlarında gerçek işveren gizleme oranı **ölçülmedi** → SCRAPING_SYSTEM §6
  Geçit B'nin (employer'sız blocking) gerçek dünyada ne kadar gerekli olduğu bilinmiyor.
- İŞKUR'da işveren adı gizliliği olasılığı `Unknown` → Employer Identity Resolver'ın
  fallback davranışı bu kaynakta kritik olabilir.

### 8.3 Policy ve permission belirsizlikleri (**hepsi T-008 girdisi**)

| # | Belirsizlik | Etkilediği karar |
|---|---|---|
| P-1 | isinolsun §4.12'nin üye olmayan otomatik erişime uygulanabilirliği | Wave 1'in başlayıp başlayamayacağı |
| P-2 | kariyer.net hizmet sözleşmesinin içeriği (403 nedeniyle okunamadı) | src-tr-002'nin statüsü |
| P-3 | Kamu kaynaklarında (İŞKUR, SBB) yeniden kullanım lisansının bulunmaması | Wave 2'nin statüsü |
| P-4 | İlan metninin ne kadarının gösterilebileceği (telif) | OPEN-06; bütün kaynaklar |
| P-5 | `Conditional` kaynaklar için karar rubriğinin olmaması | OPEN-09; **Wave 1/2'nin tamamı** |

---

## 9. T-021 Source Coverage Validation için Veri Toplama Planı

T-021'in amacı: "bağımsız derlenen gerçek açık pozisyonların yüzde kaçına compliant
source'lardan erişilebiliyor" sorusunu ölçmek. Bu araştırmanın bıraktığı boşlukları
kapatacak plan:

**Örneklem tasarımı**
- Cluster başına **50-70 gerçek açık pozisyon**, toplam ~150-200.
- Occupation dağılımı: her cluster'ın iki occupation'ına eşit ağırlık.
- Coğrafi dağılım: en az 3 il (İstanbul + 2 farklı büyüklükte il) — tek şehir yanlılığını
  önlemek için.
- **Derleme yöntemi (kritik):** örneklem **aday source'lardan derlenmemelidir** — aksi
  halde ölçüm döngüsel olur. Bağımsız derleme yolları: işveren kariyer sayfaları,
  sektörel dernek duyuruları, gazete/ilan portalları, saha gözlemi (T-022 görüşmelerinde
  katılımcılara "son başvurduğun ilanı nereden buldun" sorusu).

**Her örneklem ilanı için kaydedilecek alanlar**
1. Occupation + cluster · 2. İl/ilçe · 3. İşveren (gerçek işveren mi agency mi) ·
4. Nerede bulundu (birincil kanal) · 5. Wave 1 kaynağında bulunabildi mi (evet/hayır) ·
6. Wave 2 kaynaklarında bulunabildi mi · 7. Kaç farklı kanalda görüldü (**çapraz yayın
ölçümü** — §4.9) · 8. İşveren adı gizli mi (**§4.10 ölçümü**) · 9. İlan yayın tarihi
görünüyor mu (**§4.11 ölçümü**) · 10. Hard requirement metinde açık mı (**extraction
zorluğu ön sinyali**)

**Türetilecek metrikler**
- Cluster başına ve toplam **coverage %** → METRICS "Market coverage" (hedef ≥%60,
  calibration target).
- **Çapraz yayın oranı** → dedupe tasarımının gerçek yükü.
- **İşveren gizleme oranı** → Employer Identity Resolver fallback ihtiyacı.
- **posted_at görünürlük oranı** → freshness lag ölçümünün kapsam oranı.

**Eşik altı kalınırsa** (T-021 acceptance'ında tanımlı): source seti genişletme, cluster
değişikliği veya value proposition dilinin coverage'dan kalite/explainability eksenine
kaydırılması — **kullanıcı kararı**.

---

## 10. Assumptions (bu araştırmanın dayandığı varsayımlar)

| # | Assumption | Neden varsayım |
|---|---|---|
| TR-A1 | robots.txt içeriği araştırma anında geçerli ve kalıcı | Kaynaklar politikalarını istedikleri zaman değiştirebilir; `reevaluation_due` bu yüzden var |
| TR-A2 | Fetch sırasında alınan 403'ler kalıcı politika, geçici arıza değil | Ayırt edilemedi; elle doğrulama gerekir |
| TR-A3 | isinolsun sitemap'indeki ilan hacmi gözlemlenenden yüksek | Fetch truncate edildi; tam sayım yapılmadı |
| TR-A4 | Büyük hastane gruplarının ilanlarının board'larda yoğunlaşması genel eğilimi temsil ediyor | Küçük örneklemden çıkarım |
| TR-A5 | ATS provider'ların robots politikası tenant'a devrolmuyor | `hrpeak` örneğinde provider izinli, tenant 403 — bu varsayımı destekliyor ama tek örnek |

## 11. Unknown Bilgiler (araştırmada kapatılamayanlar)

- kariyer.net hizmet sözleşmesinin içeriği (403)
- yenibiris.com'un bütün policy ve yapı bilgileri (403)
- ilan.gov.tr erişimi (TLS sertifika hatası)
- kariyerkapisi.cbiko.gov.tr erişimi (DNS)
- Bütün kaynaklarda **structured data (JSON-LD JobPosting) varlığı** — hiçbiri kontrol
  edilmedi; adapter kararı için önemli
- Salary alanı mevcudiyeti (hiçbir kaynakta doğrulanmadı)
- Gerçek ilan hacimleri (nicel sayım yapılmadı)
- İŞKUR'da işveren adı gizliliği
- Türkiye'deki ATS tenant envanteri
- `data.gov.tr` üzerinde İŞKUR veri seti bulunup bulunmadığı (portal doğrudan taranmadı)

## 12. Open Questions

- **❓ TR-Q1:** isinolsun §4.12 üye olmayan otomatik erişime uygulanır mı? → T-008
- **❓ TR-Q2:** Kariyer.net grubundan yazılı izin/feed talebi yapılacak mı? → **kullanıcı kararı**
- **❓ TR-Q3:** İŞKUR'dan resmi veri paylaşımı talebi yapılacak mı? → **kullanıcı kararı**
- **❓ TR-Q4:** Healthcare cluster'ının coverage zayıflığı D-008 cluster seçimini değiştirir mi? → **kullanıcı kararı** (T-021 sonrası)
- **❓ TR-Q5:** İlan metninin ne kadarı gösterilebilir? → OPEN-06 / T-008
- **❓ TR-Q6:** `Conditional` kaynaklar için karar rubriği ne olacak? → OPEN-09 / T-008

---

## 13. Go / Conditional / No-Go Tavsiyesi

### **CONDITIONAL GO**

**Go tarafı:** Türkiye pazarında MVP'yi besleyecek teknik olarak erişilebilir, yapısal ve
güncel kaynaklar **mevcut**. Wave 1 için tek kaynakla iki cluster'ı kapsayan somut bir
aday (isinolsun.com) ve Wave 2 için tamamlayıcı iki kaynak belirlendi. Core loop'un tek
source ile doğrulanabileceği (ROADMAP M2) **teknik olarak doğrulandı**.

**Conditional tarafı — üç şart:**

1. **Hiçbir kaynak için crawl başlatılmamalıdır** ki bunlardan biri gerçekleşsin:
   (a) ilgili kaynaktan **yazılı izin/feed anlaşması** alınması, **veya**
   (b) T-008'in `Conditional` karar rubriğini (OPEN-09) kapatması.
   Bu, SCRAPING_SYSTEM §4 gri alan kuralının doğrudan uygulanmasıdır.
2. **T-021 çalıştırılmalı** — coverage tahminleri niteliksel; ≥%60 hedefinin
   karşılanabilirliği **ölçülmeden bilinemez.**
3. **Healthcare cluster'ı yeniden değerlendirilmeli** — üç cluster içinde compliant
   erişilebilirliği en zayıf olanı; T-021 sonucuna göre D-008 kullanıcı kararıyla revize
   edilebilir.

**No-Go değil**, çünkü: kaynak yokluğu değil, **izin belirsizliği** söz konusu; ve bu
belirsizliği kapatacak iki yol (izin talebi, hukuki rubrik) zaten planda mevcut.

**Uyarı:** Bu bölüm bir hukuki değerlendirme değildir. "Conditional" ifadesi, projenin
kendi compliance çerçevesinin (D-002 + SCRAPING_SYSTEM §4) uygulanmasının sonucudur.
