# SOURCE_PERMISSION_REQUESTS_TR.md — Resmî İzin Talebi Taslakları (OPEN-19)

> **Purpose:** T-003'ün `conditional` bıraktığı iki öncelikli kaynak için resmî izin /
> işbirliği talebi taslakları. Bu, [SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md)
> §4 madde 5'in "tercih edilen yol" dediği seçenektir ve OPEN-19'un çıktısıdır.
>
> **⚠️ Bu mesajlar GÖNDERİLMEMİŞTİR ve Claude tarafından gönderilmeyecektir.**
> Gönderim kararı ve iletişim kanalının doğrulanması kullanıcıya aittir.
>
> **⚠️ İletişim adresleri doğrulanmamıştır** ve bu dosyada **uydurulmamıştır** — `Unknown`
> bırakılmıştır (§4). Adres doğrulanmadan gönderim yapılmamalıdır.

**Hazırlık tarihi:** 2026-07-21 · **Kaynak değerlendirmeleri:**
[TURKEY_SOURCE_LANDSCAPE.md](TURKEY_SOURCE_LANDSCAPE.md)

---

## 1. Neden bu iki kurum?

| Kaynak | T-003 durumu | Neden izin talebi |
|---|---|---|
| **İşin Olsun / Kariyer.net grubu** (src-tr-001) | `conditional`, `policy_risk: high` | Wave 1 adayı. robots.txt izinli ama üyelik sözleşmesi §4.12 veri kopyalamayı **yazılı izne** bağlıyor. Template kuralı gereği `high` riskli kaynak **ancak yazılı izinle** `allowed` olabilir |
| **İŞKUR** (src-tr-006) | `conditional`, `policy_risk: medium` | Wave 2 adayı. robots izinli, kamu hizmeti; ancak **açık yeniden kullanım lisansı bulunamadı**. Kamu kurumuyla resmî veri paylaşımı, scraping'e tercih edilen yoldur |

## 2. Bütün mesajlarda ortak duruş

Her iki taslak da şu ilkelere uyar — sapma olursa mesaj gönderilmemelidir:

- **Hukuki pozisyon alınmaz.** "Bizim yaptığımız hukuka uygundur", "robots.txt izin
  veriyor dolayısıyla hakkımız var" gibi ifadeler **kullanılmaz.** Sadece izin ve uygun
  entegrasyon yöntemi sorulur.
- **Karşı tarafın şartları bizim lehimize yorumlanmaz.** Sözleşme maddelerine kendi
  okumamız dayatılmaz.
- **Restriction bypass edilmeyeceği** açıkça yazılır.
- **Veri satılmayacağı** açıkça yazılır.
- **Kaynak adı ve orijinal ilan URL'inin korunacağı**, başvurunun **orijinal kaynak
  üzerinden** yapılacağı belirtilir.
- Rate limit ve attribution şartlarına uyulacağı taahhüt edilir.
- İlan kaldırma/güncelleme taleplerinin destekleneceği belirtilir.
- Pilotun **Türkiye'de ve sınırlı kapsamda** olduğu belirtilir.
- Ürün abartılmaz; henüz geliştirme aşamasında olduğu dürüstçe söylenir.

---

## 3. Taslak A — İşin Olsun / Kariyer.net Grubu

### 3.1 Önerilen subject

```
İş İlanı Verilerine Erişim ve İşbirliği Talebi — Kişiselleştirilmiş İş Eşleştirme Projesi
```

### 3.2 Kısa e-posta sürümü

```
Sayın Yetkili,

Türkiye'de iş arayanlara yönelik, kişiselleştirilmiş iş ilanı önerileri sunan bir
platform geliştiriyoruz. Ürün henüz geliştirme aşamasındadır ve yayında değildir.

Amacımız, ilanları kendi platformumuzda yayınlamak değil; kullanıcıya mesleğine
uygun ilanları göstererek onu ilanın orijinal kaynağına yönlendirmektir. Her
ilanda kaynak adı ve orijinal ilan bağlantısı korunur, başvurular sizin
platformunuz üzerinden yapılır.

Platform Üyelik Sözleşmenizin 4.12 maddesinde platform verilerinin yazılı onay
olmadan kopyalanamayacağı belirtiliyor. Bu nedenle herhangi bir veri erişimi
başlatmadan önce sizden izin ve uygun yöntem konusunda görüş almak istiyoruz.

Sizin için uygun olan yöntem hangisidir?
  • Resmî API veya veri beslemesi (feed)
  • Veri ortaklığı / iş birliği anlaşması
  • Belirli koşullarla yazılı erişim izni
  • Bu aşamada erişim mümkün değil

Hangi yöntemi uygun görürseniz, belirleyeceğiniz teknik ve ticari koşullara
(hız sınırı, atıf biçimi, kapsam) uyacağımızı belirtmek isteriz.

Görüşme veya yazılı yanıt için uygun kanalınızı öğrenebilir miyiz?

Saygılarımızla,
[Ad Soyad] — [Rol]
[İletişim bilgisi]
```

### 3.3 Detaylı e-posta sürümü

```
Sayın Yetkili,

Türkiye'de iş arayan bireylere yönelik bir iş keşif ve eşleştirme platformu
geliştiriyoruz. Ürün geliştirme aşamasındadır, henüz yayında değildir ve şu anda
hiçbir kaynaktan veri toplamamaktadır. Bu nedenle, herhangi bir teknik çalışma
başlatmadan önce sizinle iletişime geçmeyi tercih ettik.

PROJENİN AMACI
Platformumuz, kullanıcının mesleki profilini (eğitim, deneyim, belgeler, çalışma
tercihleri) yapılandırarak ona uygun ilanları önermeyi hedefliyor. Özellikle
sürücü, depo görevlisi, muhasebe, satış ve sağlık meslekleri gibi alanlarda,
mesleğe özgü şartların (ehliyet sınıfı, meslek belgesi, vardiya uygunluğu)
doğru değerlendirilmesine odaklanıyoruz. Her öneriyle birlikte kullanıcıya
"bu ilan neden size uygun, hangi şartlar karşılanıyor, hangi bilgi eksik"
açıklaması sunuyoruz.

İLANLARIN NASIL KULLANILACAĞI
• İlanlar bizim platformumuzda nihai başvuru noktası olarak sunulmaz.
• Her ilanda kaynak adı ve orijinal ilan bağlantısı korunur ve kullanıcıya
  görünür biçimde gösterilir.
• Başvuru akışı sizin platformunuza yönlendirilerek tamamlanır; başvuruyu biz
  toplamayız ve aracılık etmeyiz.
• İlan içeriği bütünüyle yeniden yayımlanmaz; sizin uygun göreceğiniz kapsamda
  (örneğin başlık, konum, çalışma şekli ve kısa özet) gösterim yapılır.
• Toplanan hiçbir veri satılmaz, üçüncü taraflara devredilmez veya reklam amaçlı
  kullanılmaz.
• Kaldırılan veya güncellenen ilanların bizim tarafımızda da kaldırılması/
  güncellenmesi için düzenli kontrol ve talep üzerine acil kaldırma mekanizması
  uygulanır.

TEKNİK YAKLAŞIM VE SINIRLAR
• Herhangi bir giriş (login) duvarı, CAPTCHA, bot koruması veya erişim kısıtlaması
  aşılmaz. Bu, projemizin değiştirilemez bir kuralıdır.
• robots.txt kurallarına ve belirlediğiniz hız sınırlarına uyulur; hız sınırı
  belirtmezseniz muhafazakâr bir varsayılan uygulanır.
• Tanımlanabilir bir user-agent kullanılır ve iletişim bilgisi içerir.
• Pilot kapsam Türkiye ile ve sınırlı sayıda meslek grubuyla sınırlıdır.

TALEBİMİZ
Platform Üyelik Sözleşmenizin 4.12 maddesini dikkate alarak, verilerinize dair
herhangi bir işlem yapmadan önce iznini̇zi ve uygun gördüğünüz yöntemi öğrenmek
istiyoruz. Sözleşmenizin kapsamına ilişkin bir yorum yapmıyor, yalnızca sizin
değerlendirmenizi rica ediyoruz.

Aşağıdaki seçeneklerden hangisi sizin için uygundur?
  1. Resmî API erişimi (varsa koşulları)
  2. Veri beslemesi (feed) paylaşımı
  3. Veri ortaklığı / iş birliği anlaşması
  4. Belirli koşullar altında yazılı erişim izni
  5. Bu aşamada erişim mümkün değildir

Hangi seçeneği uygun görürseniz görün, belirleyeceğiniz kapsam, atıf biçimi, hız
sınırı ve gösterim koşullarına uyacağımızı taahhüt ederiz.

Konuyu görüşebileceğimiz bir yetkili veya kanal önerebilir misiniz?

Saygılarımızla,
[Ad Soyad] — [Rol]
[Kurum / proje adı]
[İletişim bilgisi]
```

### 3.4 Teknik ek bilgi listesi *(talep edilirse iletilecek)*

- Kullanılacak user-agent dizesi ve iletişim adresi
- Tahmini istek hacmi ve sıklığı (günlük/haftalık)
- Hangi alanların işleneceği (başlık, işveren, konum, çalışma şekli, şartlar, ilan tarihi,
  orijinal URL)
- Hangi alanların **işlenmeyeceği** (başvuran bilgileri, aday verileri, iletişim kişileri)
- Gösterim örneği (ilan kartı taslağı: kaynak adı + orijinal bağlantı görünür)
- Kaldırma/güncelleme talebi için iletişim kanalı ve hedef yanıt süresi
- Veri saklama süresi yaklaşımı
- Pilot kapsamı: hedef meslek grupları ve süre

### 3.5 Sorulması gereken net sorular

1. Veri erişimi için resmî bir API veya feed mevcut mu? Varsa koşulları nelerdir?
2. §4.12 kapsamında yazılı izin verilmesi mümkün mü, hangi süreçle?
3. İlan içeriğinin ne kadarını gösterebiliriz? (başlık/özet/tam metin)
4. Atıf biçimi konusunda beklentiniz nedir?
5. Kabul edilebilir istek hızı/hacmi nedir?
6. İlan kaldırma taleplerini hangi kanaldan iletmemizi istersiniz?
7. Pilot dönem için sınırlı kapsamlı bir deneme mümkün mü?
8. Bu konuda görüşebileceğimiz doğru birim/kişi kim?

### 3.6 Takip mesajı *(yanıt gelmezse, ~10 iş günü sonra)*

```
Sayın Yetkili,

[Tarih] tarihinde ilettiğimiz iş ilanı verilerine erişim ve iş birliği talebimizle
ilgili bilgi almak istiyoruz.

Konu ulaşmadıysa veya farklı bir birime iletilmesi gerekiyorsa yönlendirmeniz
bizim için yeterli olacaktır.

Yanıt alamamamız durumunda projemizde ilgili kaynağı kullanmama yönünde
ilerleyeceğimizi belirtmek isteriz; herhangi bir erişim başlatmayacağız.

Saygılarımızla,
[Ad Soyad]
```

---

## 4. Taslak B — İŞKUR (Türkiye İş Kurumu)

> **Kanal notu:** İŞKUR bir kamu kurumudur; bu tür talepler için kurumların bilgi edinme
> ve resmî yazışma kanalları kullanılır. `iskur.gov.tr` robots.txt dosyasında
> `/kurumsal/bilgi-sayfalari/bilgi-edinme/` yolunun taramaya açık olduğu görülmüştür
> (kontrol: 2026-07-21) — ancak **doğru başvuru kanalı ve adres doğrulanmamıştır**
> (`Unknown`). Gönderimden önce kurumun güncel resmî kanalı teyit edilmelidir.

### 4.1 Önerilen subject

```
Açık İş İlanı Verilerinin Yeniden Kullanımı Hakkında Bilgi ve İzin Talebi
```

### 4.2 Kısa e-posta / dilekçe sürümü

```
Sayın İlgili,

Türkiye'de iş arayan bireylere yönelik, kişiselleştirilmiş iş ilanı önerileri
sunmayı amaçlayan bir platform geliştiriyoruz. Proje geliştirme aşamasındadır ve
şu anda hiçbir kaynaktan veri toplamamaktadır.

Kurumunuzun e-Şube üzerinden kamuya açık olarak yayımladığı açık iş ilanlarının,
iş arayanlara yönlendirme amacıyla kullanılabilmesi konusunda bilgi ve izin talep
ediyoruz.

Kullanım biçimimiz şu şekilde olacaktır:
  • İlanın kaynağı olarak Kurumunuz açıkça belirtilir.
  • Kullanıcı, ilanın orijinal sayfasına yönlendirilir; başvuru Kurumunuzun
    sistemi üzerinden yapılır.
  • Veriler satılmaz veya üçüncü taraflara devredilmez.
  • Erişim kısıtlaması, giriş gerekliliği veya güvenlik önlemi aşılmaz.

Öğrenmek istediklerimiz:
  1. Bu veriler için resmî bir API, açık veri seti veya veri paylaşım yöntemi
     bulunmakta mıdır?
  2. Yoksa, kamuya açık ilan sayfalarının otomatik olarak okunmasına ilişkin
     Kurumunuzun bir kuralı veya koşulu var mıdır?
  3. Atıf ve yeniden gösterim konusunda uymamız gereken şartlar nelerdir?

Bilgilerinize arz ederiz.

[Ad Soyad] — [Rol]
[İletişim bilgisi]
```

### 4.3 Detaylı sürüm

```
Sayın İlgili,

KONU: Kamuya açık iş ilanı verilerinin yeniden kullanımı hakkında bilgi ve izin
talebi.

Türkiye'de iş arayan bireylere yönelik bir iş keşif ve eşleştirme platformu
geliştirmekteyiz. Platform geliştirme aşamasındadır, yayında değildir ve şu anda
hiçbir kaynaktan veri toplamamaktadır. Herhangi bir teknik çalışma başlatmadan
önce Kurumunuzun görüşünü almak istedik.

PROJENİN AMACI VE KAMU YARARI
Platform, kullanıcının mesleki bilgilerini yapılandırarak ona uygun ilanları
önermeyi ve her öneri için "bu ilan neden uygun, hangi şartlar karşılanıyor,
hangi bilgi eksik" açıklamasını sunmayı hedefler. Öncelikli meslek gruplarımız
sürücü, depo görevlisi, muhasebe, satış temsilcisi, hemşire ve sağlık
teknisyenidir. Amacımız, iş arayanların kendilerine uygun ilanlara daha kolay
ulaşmasıdır; Kurumunuzun ilanlarına yönlendirme yaparak bu ilanların
görünürlüğüne katkı sağlamayı öngörüyoruz.

VERİLERİN KULLANIM BİÇİMİ
• Kaynak olarak Kurumunuz her ilanda açıkça belirtilir.
• Orijinal ilan bağlantısı korunur; kullanıcı başvuru için Kurumunuzun sistemine
  yönlendirilir. Başvuruyu biz almayız ve aracılık etmeyiz.
• İlan içeriği bütünüyle yeniden yayımlanmaz; Kurumunuzun uygun göreceği kapsamda
  gösterim yapılır.
• Veriler hiçbir şekilde satılmaz, üçüncü taraflara devredilmez veya reklam amaçlı
  kullanılmaz.
• Kaldırılan veya güncellenen ilanlar bizim tarafımızda da kaldırılır/güncellenir;
  bu konuda talep üzerine acil işlem mekanizması uygularız.
• Kamu sektörü ilanları için, sınav puanı ve mevzuat şartları tam olarak
  modellenmediğinden, kullanıcıya uygunluk puanı gösterilmez; ilan yalnızca
  listelenir ve resmî kaynağa yönlendirilir.

TEKNİK YAKLAŞIM VE SINIRLAR
• Giriş duvarı, CAPTCHA, bot koruması veya herhangi bir erişim kısıtlaması
  aşılmaz. Bu, projemizin değiştirilemez bir kuralıdır.
• robots.txt kurallarına ve belirlenecek hız sınırlarına uyulur.
• Tanımlanabilir bir user-agent ve iletişim bilgisi kullanılır.
• Erişim, sistemlerinize yük bindirmeyecek şekilde düşük sıklıkta planlanır.

TALEBİMİZ
1. Açık iş ilanı verileri için resmî bir API, açık veri seti veya veri paylaşım
   protokolü bulunmakta mıdır?
2. Bulunmuyorsa, kamuya açık ilan sayfalarının otomatik olarak okunmasına ilişkin
   Kurumunuzun belirlediği koşullar nelerdir?
3. Atıf biçimi, gösterim kapsamı ve güncelleme sıklığı konusunda uymamız gereken
   şartlar nelerdir?
4. Bu konuda görüşebileceğimiz birim hangisidir?

Gereğini bilgilerinize arz ederiz.

[Ad Soyad] — [Rol]
[Kurum / proje adı]
[İletişim bilgisi]
```

### 4.4 Teknik ek bilgi listesi

Taslak A §3.4 ile aynı; ek olarak:
- Kamu sektörü ilanları için **listing-only** davranışının açıklaması (uygunluk puanı
  üretilmemesi)
- Erişimin planlanan sıklığı ve saat aralığı (yük dengeleme)

### 4.5 Sorulması gereken net sorular

1. Resmî API / açık veri seti var mı?
2. Yoksa otomatik okuma için kurumun koşulu nedir?
3. Atıf ve gösterim kapsamı şartları nelerdir?
4. Hız/sıklık sınırı önerisi var mı?
5. Kaldırma/güncelleme talepleri hangi kanaldan iletilmeli?
6. Yetkili birim hangisidir?

### 4.6 Takip mesajı

```
Sayın İlgili,

[Tarih] tarihli, kamuya açık iş ilanı verilerinin yeniden kullanımına ilişkin
bilgi ve izin talebimizin durumu hakkında bilgi almak istiyoruz.

Talebimizin farklı bir birime yönlendirilmesi gerekiyorsa bilgilendirmeniz
yeterli olacaktır. Yanıt alınana kadar herhangi bir veri erişimi
başlatmayacağımızı belirtmek isteriz.

Saygılarımızla,
[Ad Soyad]
```

---

## 5. İletişim Kanalları — **Unknown**

| Kurum | Kanal | Durum |
|---|---|---|
| İşin Olsun / Kariyer.net | Kurumsal iletişim / veri sorumlusu adresi | **Unknown — doğrulanmadı.** Aday yollar: sitedeki "İletişim" sayfası, KVKK aydınlatma metnindeki veri sorumlusu iletişim bilgisi, kurumsal LinkedIn üzerinden yetkili yönlendirmesi |
| İŞKUR | Resmî başvuru kanalı | **Unknown — doğrulanmadı.** Aday yollar: kurumun bilgi edinme sayfası (`iskur.gov.tr` robots.txt'te taramaya açık görüldü, 2026-07-21), resmî yazışma adresi, kurumsal iletişim sayfası |

> **Adres uydurulmamıştır.** Gönderimden önce kanalın güncelliği doğrulanmalı; yanlış
> kanala gönderim, talebin kaybolmasına ve gereksiz gecikmeye yol açar.

## 6. Gelen Cevabın Source Registry'ye İşlenmesi

Yanıt geldiğinde [SOURCE_REGISTRY.md](../architecture/SOURCE_REGISTRY.md) §5'teki ilgili
kayıt şu kurala göre güncellenir:

| Gelen yanıt | `scraping_permission` | `policy_risk` | `status` | Ek işlem |
|---|---|---|---|---|
| Resmî API/feed sunuldu | `allowed` | `low` | `under_review` → `active_limited` | `access_method` = `api`/`feed`; koşullar `rate_limit.declared`'a yazılır |
| Yazılı izin verildi (koşullu) | `allowed` | `medium` | `under_review` → `active_limited` | Koşullar `policy_risk_note`'a; `reevaluation_due` atanır |
| "Şu an mümkün değil" | `rejected` | mevcut değer korunur | `rejected` | Kayıt **silinmez**; gerekçe + tarih yazılır (§2 kuralı) |
| Yanıt yok (takip sonrası) | `unknown` | mevcut değer korunur | `candidate` | "Yanıt alınamadı" notu + tarih; **crawl başlatılmaz** |
| Kısmi/belirsiz yanıt | `conditional` | mevcut değer korunur | `under_review` | T-008 rubriğine (OPEN-09) girdi olarak işaretlenir |

Her durumda `policy_reviewed_by`, `policy_reviewed_at` ve `reevaluation_due` alanları
doldurulur. **Hiçbir yanıt, `policy_risk: high` bir kaynağı yazılı izin olmadan `allowed`
yapamaz** (SOURCE_REGISTRY §4 kuralı).

## 7. Açık Sorular

- **❓ PQ-1:** Mesajlar hangi kimlikle gönderilecek — şahıs, şirket, proje adı?
  *(kurumsal muhatap ciddiyeti etkiler; kullanıcı kararı)*
- **❓ PQ-2:** Yanıt gelmezse ne kadar beklenecek ve kaç takip yapılacak?
  *(öneri: ~10 iş günü, tek takip)*
- **❓ PQ-3:** İzin alınamazsa Wave 1 fallback'e mi geçilecek yoksa T-008 rubriği mi
  beklenecek? *(kullanıcı kararı — T-003 §6'daki fallback listesi hazır)*
- **❓ PQ-4:** Kariyer.net grubuna yapılacak talep yalnızca İşin Olsun'u mu, kariyer.net'i
  de mi kapsayacak? *(ikisi aynı grup; tek talepte birleştirmek mümkün)*
