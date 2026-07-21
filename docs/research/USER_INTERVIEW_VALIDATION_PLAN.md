# USER_INTERVIEW_VALIDATION_PLAN.md — T-022 Saha Araştırması Materyalleri

> **Purpose:** T-022 (User Interview and Problem Validation) için saha materyalleri:
> katılımcı kriterleri, tarafsız görüşme script'i, rıza metni, kanıt kodlama çerçevesi ve
> sentez şablonları. **Bu dosya hazırlık materyalidir — hiçbir görüşme sonucu içermez.**
>
> Görüşmeleri **kullanıcı yürütür**; Claude gerçek katılımcıyla görüşmemiştir ve
> görüşmemektedir. Cevaplar
> [USER_INTERVIEW_RESPONSE_TEMPLATE.csv](USER_INTERVIEW_RESPONSE_TEMPLATE.csv) ile
> kaydedilir. Test edilen varsayımlar: [PRD.md](../product/PRD.md) → A-2, A-4, A-10.

**Hazırlık tarihi:** 2026-07-21 · **Durum:** T-022A hazırlık tamam · T-022B saha bekliyor

---

## 1. Research Objective

Türkiye'de MVP cluster'larındaki gerçek iş arayanların **mevcut davranışını ve yaşadığı
gerçek problemleri** önyargısız biçimde öğrenmek; ürün konseptinin bu problemlere karşılık
gelip gelmediğini test etmek.

Bu çalışma **ürünü satmaya değil, tezi çürütmeye** çalışır. Başarılı bir görüşme, ürünün
gereksiz olduğunu gösteren bir görüşme de olabilir — bu bir başarısızlık değil, erken ve
ucuz bir öğrenmedir.

**Cevaplaması gereken üç soru:**
1. Mevcut iş arama kanallarında tekrar eden, adı konabilir bir problem var mı?
2. Bu problem, insanların yeni bir platforma geçmesini haklı çıkaracak kadar can yakıyor mu?
3. Ürünün ayrıştırıcı olduğunu iddia ettiği şeyler (meslek-spesifik eşleştirme,
   açıklanabilirlik, kaynak şeffaflığı) gerçekten değer taşıyor mu?

## 2. Test Edilen Kritik Assumption'lar

| Assumption | İfade | Bu görüşmede nasıl test edilir | Neye bakılır |
|---|---|---|---|
| **A-10** | Kullanıcılar mevcut platformlar dururken bu ürünü tercih eder (switching nedeni gerçektir) | Geçmiş davranış: kanal değiştirme öyküsü, terk edilmiş platform, "neden bıraktın" | Gerçekten yaşanmış bir geçiş/terk olayı anlatılıyor mu |
| **A-2** | Hedef kitlenin önemli bölümü mobile-first; blue-collar segmentte masaüstü erişimi sınırlı | Son başvurunun hangi cihazdan yapıldığı; bilgisayar erişimi | Beyan değil, son somut olay |
| **A-4** | Kullanıcılar CV parse edilmesine, sonucu doğrulayabildikleri sürece olumlu yaklaşır | Mevcut CV durumu + iki yol gösterilip tercih sorulur | Güncel CV'si olmayanların davranışı |
| **A-9 (ön sinyal)** | Explainable Match Score güven ve karar netliği üretir | Konsept testinde açıklama kartı gösterilir | "Ne işime yarar" cevabı somut mu |
| **A-13 (ön sinyal)** | Haftalık e-posta digest hedef segmentte re-engagement üretir | Mevcut bildirim davranışı + kanal tercihi | E-posta gerçekten kullanılıyor mu |

> **Kapsam sınırı:** A-9 ve A-13'ün **asıl** testi T-023 (wizard-of-oz) ve T-027'dir.
> Buradan çıkan yalnızca **ön sinyaldir** ve tek başına doğrulama sayılmaz.

## 3. Participant Criteria

**Dahil etme:**
- Son 6 ay içinde iş aramış **veya** hâlen aktif arıyor
- MVP cluster'larından birinde çalışıyor/çalışmış veya o alanda iş arıyor
- Türkiye'de yaşıyor ve Türkiye'de iş arıyor
- 18 yaş ve üzeri

**Hariç tutma:**
- İK profesyonelleri, işe alım uzmanları, kariyer danışmanları (kullanıcı değil, uzman
  bakışı getirir ve cevapları çarpıtır)
- Job board şirketlerinde çalışanlar
- Projeyi önceden bilen tanıdıklar (nezaket yanlılığı)

**Çeşitlilik hedefleri (zorunlu kota değil, gözetilecek denge):**
aktif arayan / son 6 ayda aramış / çalışırken arayan · güncel CV'si olan / olmayan ·
mobile-first / masaüstü kullanan · farklı deneyim seviyeleri · en az 3 farklı il.

## 4. Cluster Bazlı Recruitment Kotası

**Toplam hedef: 12-18 katılımcı.**

| Cluster | Occupation'lar | Asgari | Hedef |
|---|---|---|---|
| Logistics & Operations | Driver, Warehouse Worker | **4** | 4-6 |
| Office & Commercial | Accountant, Sales Representative | **4** | 4-6 |
| Healthcare | Nurse, Health Technician | **4** | 4-6 |

Cluster içinde iki occupation'a da en az birer katılımcı olması hedeflenir.

> **Bu bilimsel bir örneklem değildir.** 12-18 kişi istatistiksel temsil sağlamaz; erken
> ürün doğrulaması için desen görmeye yeter. Sonuçlar "Türkiye'deki iş arayanlar şöyle
> düşünüyor" diye genellenemez — "görüştüğümüz 14 kişiden 9'u şunu anlattı" diye
> raporlanır.

## 5. Recruitment Kanalları

| Cluster | Kanal fikirleri | Not |
|---|---|---|
| Logistics & Operations | Şoför durakları, lojistik/nakliye firmaları çıkışı, depo bölgeleri, şoför WhatsApp/Telegram grupları, mesleki Facebook grupları | Yüz yüze yaklaşım bu segmentte online çağrıdan daha verimli olabilir |
| Office & Commercial | Muhasebe meslek odaları/kursları, SMMM stajyer çevreleri, satış temsilcisi LinkedIn grupları, KOBİ çevreleri | Online çağrı çalışır |
| Healthcare | Hemşire dernek/forumları, hastane çıkışları (kurum izniyle), sağlık meslek lisesi mezun grupları | **Hastane içinde kurum izni olmadan görüşme yapılmamalı** |
| Genel | Tanıdık zinciri (snowball) — ama "projeyi bilmeyen" filtresiyle | İlk 2-3 görüşme için pratik |

**Teşvik:** Küçük bir teşekkür (hediye çeki vb.) uygun; **teşvik miktarı katılımcıyı
olumlu cevap vermeye itecek düzeyde olmamalı** ve görüşme başında "olumsuz görüş de
aynı derecede değerli, teşvik cevaba bağlı değil" denmeli.

## 6. Screening Soruları

Görüşmeden önce, 2 dakikalık ön eleme. **Ürün anlatılmaz.**

1. Şu anda çalışıyor musunuz? (çalışıyor / çalışmıyor / çalışıyor ama iş arıyor)
2. Son 6 ay içinde hiç iş aradınız mı? *(hayır → görüşmeye alınmaz)*
3. Mesleğiniz nedir? *(cluster eşleşmesi)*
4. En son ne zaman bir işe başvurdunuz? (bu hafta / bu ay / 1-3 ay / 3-6 ay önce)
5. İş ararken en çok hangi araçları kullanıyorsunuz? *(açık uçlu, seçenek okunmaz)*
6. Güncel bir CV'niz var mı? (var ve güncel / var ama eski / yok)
7. İnsan kaynakları veya işe alım alanında mı çalışıyorsunuz? *(evet → hariç)*

## 7. Katılımcı Davet Mesajı

> Metin sade tutulmuştur; ürün adı ve özellikleri **kasıtlı olarak** yazılmaz.

```
Merhaba,

İş arama deneyimi üzerine kısa bir araştırma yapıyoruz. Amacımız insanların iş
ararken gerçekte neler yaşadığını anlamak.

Yaklaşık 25-30 dakikalık bir görüşme olacak. Bir şey satmıyoruz, size bir ürün
kullandırmıyoruz ve doğru/yanlış cevap yok. Kötü deneyimlerinizi duymak bizim
için en az iyi deneyimleriniz kadar değerli.

Görüşmede CV'nizi, kimlik bilgilerinizi veya kişisel belgelerinizi istemiyoruz.
Notlarımızda isminiz geçmez. İstediğiniz an "bu soruyu geçelim" veya "burada
bitirelim" diyebilirsiniz.

Uygun olduğunuz bir zaman var mı?

Teşekkürler.
```

## 8. Kısa Rıza ve Gizlilik Metni

> Görüşmenin başında **yüksek sesle okunur** ve sözlü onay alınır. Bu metin hukuki
> danışmanlık değildir; T-008 hukuki doğrulaması sonrasında gözden geçirilmelidir.

```
Başlamadan önce birkaç şey söylemek istiyorum:

• Bu bir araştırma görüşmesi. Size bir ürün satmıyorum.
• Notlarımda isminizi, telefonunuzu veya e-postanızı yazmayacağım. Kayıtlarda
  sadece "Katılımcı 03" gibi bir numara olacak.
• CV'nizi, kimlik bilgilerinizi veya herhangi bir belgenizi istemiyorum. Lütfen
  paylaşmayın.
• Sağlık durumunuz, dini veya siyasi görüşünüz gibi özel konuları sormayacağım.
  Konuşma sırasında böyle bir bilgi geçerse notlarıma yazmayacağım.
• Söylediklerinizi sadece ürün tasarımı için kullanacağız; kimseyle paylaşmayacağız
  ve satmayacağız.
• İstediğiniz soruyu geçebilirsiniz, istediğiniz an bitirebilirsiniz. Bu durumda
  teşekkür hediyeniz yine sizindir.
• Ses kaydı almamı ister misiniz? İstemezseniz sadece not alacağım.

Kabul ediyor musunuz? Başlayabilir miyiz?
```

**Görüşmeci kuralı:** Katılımcı kendiliğinden hassas bilgi anlatırsa (sağlık durumu,
ailevi durum, maaş bordrosu vb.) **not alınmaz**; konuşma nazikçe göreve döndürülür.
Bu kural [PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md)
§1 minimization ilkesinin saha karşılığıdır.

---

## 9. Interview Script (25-35 dakika)

**Yapı:** Bölüm A ve B'de **ürün hiç anlatılmaz.** Konsept yalnızca Bölüm C'de gösterilir.
Bu sıra bozulursa görüşme kanıt değerini kaybeder.

### Bölüm 0 — Açılış (2 dk)
Rıza metni (§8) → sözlü onay → "Biraz kendinizden ve işinizden bahseder misiniz?"

### Bölüm A — Son iş arama deneyimi (10-12 dk) · *ürün anlatılmaz*

> Amaç: **anlatılan genel alışkanlık değil, yaşanmış somut olay.** Katılımcı genelleme
> yaparsa ("genelde şöyle yaparım") mutlaka somuta çekilir: "en son ne zaman oldu, o gün
> tam olarak ne yaptınız?"

1. En son ne zaman iş aradınız? O dönemi anlatır mısınız — nasıl başladı?
2. **O gün nereden baktınız?** İlk açtığınız şey neydi?
3. Şu anda aklınıza gelen **son üç ilanı** anlatır mısınız? Her biri için: nereden
   gördünüz, ne zamandı, başvurdunuz mu?
4. *(Başvurmadığı bir ilan varsa)* Neden başvurmadınız?
5. Bir ilanı görüp "bu bana göre değil" dediğiniz **son sefer** ne oldu? Neden öyle
   düşündünüz?
6. Bir ilana başvurdunuz ama **başvurmamış olmayı** dilediğiniz oldu mu? Ne olmuştu?
7. Şu anda kaç farklı yer/uygulama kullanıyorsunuz? *(sayı ve isim)*
8. Bunlardan birini **bırakma** ya da yenisine geçme durumunuz oldu mu? Ne olmuştu?
   *(A-10'un çekirdek sorusu — hipotetik değil, yaşanmış geçiş)*
9. En son başvuruyu **hangi cihazdan** yaptınız? *(A-2)*
10. Bilgisayardan mı telefondan mı bakıyorsunuz genelde? Neden?

### Bölüm B — Problem sondajı (6-8 dk) · *ürün anlatılmaz*

> Amaç: problemi **katılımcının kendi ağzından** duymak. Aşağıdaki problemler
> **isimlendirilmeden** sorulur; katılımcı kendiliğinden söylerse güçlü kanıt sayılır.

11. İş ararken sizi **en çok yoran** şey ne? *(açık uçlu; ilk cevap beklenir, yönlendirme yok)*
12. Karşınıza çıkan ilanların ne kadarı size gerçekten uygun oluyor? Uygun olmayanlara
    örnek verir misiniz?
13. Aynı ilanı birden fazla yerde ya da tekrar tekrar gördüğünüz oluyor mu? Örnek?
14. Başvurmak istediğiniz bir ilanın **artık geçersiz** olduğunu fark ettiğiniz oldu mu?
    Nasıl anladınız?
15. Bir ilanın şartlarını okuyup "acaba ben uygun muyum" diye emin olamadığınız oldu mu?
    Hangi kısımda takıldınız?
16. İlanlarda **eksik veya yanıltıcı** bulduğunuz bilgi oluyor mu? *(maaş, konum, vardiya,
    şartlar)*
17. Başvurduğunuz işleri nasıl takip ediyorsunuz? *(defter, not, hafıza, uygulama…)*
18. Yeni ilan çıktığında haberdar oluyor musunuz? Nasıl? *(e-posta/SMS/uygulama bildirimi/
    hiçbiri)*
19. *(Bildirim alıyorsa)* Bu bildirimleri açıyor musunuz? En son ne zaman açtınız?
20. CV'niz var mı, ne zaman güncellediniz? Güncellemek size nasıl geliyor?

### Bölüm C — Konsept testi (8-10 dk) · *ürün ilk kez burada gösterilir*

> **Görüşmeci metni (kısa ve iddiasız okunur):**
> "Şimdi üzerinde çalıştığımız bir fikri göstermek istiyorum. Henüz yapılmadı, sadece
> bir taslak. Beğenmezseniz veya işe yaramaz derseniz bu bizim için en değerli cevap."

Katılımcıya **basılı/ekranda tek bir örnek kart** gösterilir: bir iş ilanı + yanında
"neden uygun" açıklaması (karşılanan şartlar ✔ / karşılanmayan ✘ / **bilinmeyen ?**) +
kaynak adı + ilan yaşı.

21. Bu kartta ne görüyorsunuz? Kendi cümlelerinizle anlatır mısınız?
    *(anlaşılırlık testi — açıklamadan önce sorulur)*
22. Bu bilgi kararınızı değiştirir miydi? **Nasıl?** *(somut cevap istenir; "iyiymiş"
    kabul edilmez)*
23. "?" işaretli satır ne anlama geliyor sizce? *(unknown durumunun anlaşılırlığı — D-011)*
24. Burada yazan "hemşirelik belgesi doğrulanmadı" ifadesi size ne hissettiriyor?
    *(gate-relevant doğrulama davranışı — D-012)*
25. Kartta ilanın **hangi siteden** geldiği yazıyor. Bu sizin için fark eder mi? Neden?
26. Sistemin bu eşleştirmeyi ne kadar iyi bildiğine dair bir "emin olma" bilgisi de var.
    Buna bakar mıydınız?
27. **İki yol var:** (a) CV'nizi yükleyip sistemin doldurması, (b) 5 soruya cevap verip
    kendinizin doldurması. **Hangisini seçerdiniz, neden?** *(A-4 — iki seçenek eşit tonda
    okunur)*
28. *(Güncel CV'si yoksa)* CV'niz olmadan devam edebilseydiniz bu sizin için fark eder miydi?
29. Haftada bir kez, size uyan yeni ilanların listesi gelse — **nereden gelmesini**
    isterdiniz? *(kanal seçenekleri **okunmaz**, katılımcı söyler; A-13 ön sinyali)*
30. Böyle bir sistemin sizin bilgilerinizi tutması konusunda aklınıza takılan bir şey var mı?
    *(privacy — açık uçlu, korkutmadan)*

### Bölüm D — Kapanış (2-3 dk)

31. Bugün konuştuklarımızdan **en önemlisi** hangisiydi sizce?
32. Sormadığım ama sormam gereken bir şey var mı?
33. İleride kısa bir görüşme daha yapabilir miyiz? *(T-023/T-024 için havuz)*

---

## 10. Past-Behavior Soruları — neden bu sırada

Bölüm A ve B'nin tamamı geçmiş davranışa dayanır çünkü **insanlar gelecekteki
davranışlarını kötü tahmin eder ama geçmiş davranışlarını iyi hatırlar.**
"Kullanır mıydınız?" sorusu sistematik olarak fazla olumlu cevap üretir; "en son ne
yaptınız?" üretmez.

Kanıt gücü sıralaması (yüksekten düşüğe):
1. Yaşanmış somut olay, tarih ve ayrıntıyla, **sorulmadan** anlatıldı
2. Yaşanmış somut olay, sorunca hatırlandı
3. Genel alışkanlık ("genelde şöyle olur"), somut örnek verilemedi
4. Hipotetik niyet ("kullanırdım", "iyi olurdu") → **kanıt sayılmaz**

## 11. Product Concept Test Soruları

Bölüm C'deki 21-30. sorular. Tasarım kuralları:
- Konsept **tek kart** olarak gösterilir; tur atılmaz, demo yapılmaz.
- Görüşmeci konsepti **savunmaz**. Katılımcı eleştirirse "haklısınız, not alıyorum" denir;
  açıklama/ikna girişimi yapılmaz.
- Özellik ismi kullanılmaz ("Match Confidence" denmez; "emin olma bilgisi" denir).
- Her olumlu cevaba **"nasıl?"** eklenir. Nasıl'ı cevaplanamayan olumluluk kayda `weak`
  geçer.

## 12. CV Upload vs Manual Profile Testi

Soru 27-28. **Kritik tasarım kuralı:** iki seçenek **eşit uzunlukta ve eşit olumlu**
tonda okunur. Sıralama katılımcılar arasında **dönüşümlü** olur (tek numaralı
katılımcılarda önce CV, çift numaralılarda önce manuel) — sıra etkisini kırmak için.

Ayrıca kaydedilir: katılımcının **gerçekte güncel CV'si var mı** (screening 6). "CV
yüklerim" diyen ama güncel CV'si olmayan katılımcı, A-4 için **zayıf** kanıttır.

## 13. Explainability Testi

Soru 21-24, 26. Ölçülen şey "beğendi mi" değil, **anladı mı ve kararını değiştirir mi**:
- 21. soruda kartı **doğru okuyabildi mi** (görüşmeci açıklamadan önce)
- 22'de **somut bir davranış değişikliği** tarif edebildi mi
- 23'te `unknown` durumunu doğru yorumladı mı — yoksa "eksiğim var" diye mi anladı?
  *(bu ayrım D-011'in ürün tarafındaki en kritik sorusudur)*
- 24'te doğrulanmamış lisans ifadesi güven mi yarattı, endişe mi?

## 14. Notification Kanal Testi

Soru 18-19 (mevcut davranış) + 29 (tercih). **Seçenek listesi okunmaz.** Katılımcı
kendiliğinden söylemezse "başka?" diye bir kez açılır, yine liste verilmez.

Ayrıca 19. sorudaki "en son ne zaman açtınız" cevabı, 29'daki beyandan **daha güçlü
kanıttır** — beyan ile davranış çeliştiğinde davranış kazanır.

## 15. Görüşmeci Talimatları

**Önce:** rıza metnini oku · kayıt izni al · not şablonunu hazırla · sıra dönüşümünü
(§12) not et.

**Sırasında:**
- **Sessizliği doldurma.** 3-5 saniye bekle; en iyi cevaplar sessizlikten sonra gelir.
- Katılımcının kelimelerini kullan, kendi terimlerini dayatma.
- "Yani şunu mu demek istiyorsunuz…" diye **özetleyip onaylatma** — bu yönlendirmedir.
  Bunun yerine: "biraz daha anlatır mısınız?"
- Ürünü savunma, düzeltme, "aslında öyle çalışmıyor" deme.
- Not alırken **doğrudan alıntıyı** tırnak içinde yaz; parafraz ayrı işaretlenir.
- Konu dağılırsa: "az önce … demiştiniz, oraya dönebilir miyiz?"

**Sonra:** 10 dakika içinde §20 özetini doldur (hafıza en tazeyken) · CSV satırını gir ·
hassas bilgi geçtiyse notlardan temizle.

## 16. Leading-Question Kaçınma Rehberi

| ❌ Yönlendirici | ✅ Tarafsız karşılığı |
|---|---|
| "Alakasız ilanlar sizi rahatsız ediyor mu?" | "Karşınıza çıkan ilanların ne kadarı size uygun oluyor?" |
| "Böyle bir açıklama faydalı olur muydu?" | "Bu bilgi kararınızı değiştirir miydi? Nasıl?" |
| "CV yüklemek kolay olurdu değil mi?" | "Bu iki yoldan hangisini seçerdiniz? Neden?" |
| "Haftalık e-posta ister miydiniz?" | "Yeni ilanların size nereden ulaşmasını isterdiniz?" |
| "Kariyer.net'te bu sorunu yaşıyor musunuz?" | "Kullandığınız yerlerde sizi en çok ne yoruyor?" |
| "Bu özellik güven verir mi?" | "Bu ekranda size tuhaf veya güvensiz gelen bir şey var mı?" |
| "Yani mobil kullanıyorsunuz, doğru mu?" | "En son başvuruyu hangi cihazdan yaptınız?" |

**Genel kural:** Soru, cevabı içinde taşıyorsa yönlendiricidir. Problemi **adlandıran**
taraf görüşmeci olmamalı; katılımcı olmalı.

## 17. Red Flags ve Geçersiz Kanıt

Bir cevap şu durumlarda `invalid` kodlanır ve sentezde **sayılmaz**:

| Red flag | Neden geçersiz |
|---|---|
| Problemi görüşmeci adlandırdı, katılımcı onayladı | Onay yanlılığı; problem katılımcının değil |
| Yalnızca hipotetik olumluluk ("kullanırdım", "güzelmiş") | Niyet ≠ davranış |
| Katılımcı somut tek bir örnek veremedi | Genelleme, yaşanmış deneyim değil |
| Katılımcı projeyi/ekibi tanıyor | Nezaket yanlılığı |
| Katılımcı İK/işe alım profesyoneli | Kullanıcı değil, uzman bakışı |
| Cevap teşvikten sonra belirgin şekilde olumluya döndü | Teşvik yanlılığı |
| Görüşmeci konsepti savundu/açıkladı, sonra olumlu cevap geldi | Kirlenmiş kanıt |

**Ayrıca kayda geçer:** görüşme sırasında yapılan yönlendirme hatası, o soruyu geçersiz
kılar ama görüşmeyi geçersiz kılmaz — dürüstçe işaretlenir.

## 18. Not Alma Şablonu (görüşme sırasında)

```
Katılımcı: P-__    Cluster: ____________    Tarih: __________
Occupation: ____________   Sıra dönüşümü (§12): CV önce / Manuel önce
Kayıt izni: var / yok

[A] Son iş arama — somut olaylar
  Son 3 ilan:  1) kaynak ___ ne zaman ___ başvurdu? ___
               2) ...
               3) ...
  Kanal değiştirme/terk öyküsü: ____________________
  Cihaz (son başvuru): ____________

[B] Problemler — KATILIMCININ kendi sözleriyle
  Kendiliğinden söylediği problemler (sorulmadan):
    • ______________________________________
  Sorunca çıkanlar:
    • ______________________________________
  Doğrudan alıntı: "_____________________________"

[C] Konsept tepkisi
  Kartı doğru okudu mu? evet / kısmen / hayır
  "?" satırını nasıl yorumladı: ______________
  Doğrulanmamış lisans ifadesi: güven / endişe / fark etmedi
  CV vs manuel tercihi: ______  Gerekçe: ______________
  Bildirim kanalı (kendiliğinden): ______________
  Privacy endişesi: ______________

[D] Genel
  En güçlü problem: ______________
  Geçiş nedeni olabilir mi? evet / belirsiz / hayır
  Kanıt gücü: strong / moderate / weak / invalid
  Görüşmeci hatası oldu mu? ______________
```

## 19. Evidence Coding Framework

Her görüşme, her tema için tek bir kod alır:

| Kod | Tanım |
|---|---|
| `strong` | Yaşanmış somut olay, ayrıntılı; çoğunlukla **sorulmadan** anlatıldı |
| `moderate` | Somut ama sorunca çıkan; ayrıntı sınırlı |
| `weak` | Genel alışkanlık beyanı; somut örnek yok |
| `invalid` | §17'deki red flag'lerden biri geçerli |
| `n/a` | Soru sorulamadı / konu açılmadı |

**Sentez kuralı:** yalnızca `strong` ve `moderate` sayılır. Bir temanın "doğrulandığı"
söylenebilmesi için o temanın **birden fazla cluster'da** ve **birbirinden bağımsız
katılımcılarda** tekrar etmesi gerekir. Tek cluster'da yoğunlaşan bulgu, o cluster'a özgü
olarak raporlanır — genele yayılmaz.

### 19.1 CSV Kod Defteri

[USER_INTERVIEW_RESPONSE_TEMPLATE.csv](USER_INTERVIEW_RESPONSE_TEMPLATE.csv) alanları için
izinli değerler. **Emin olunmayan alan boş bırakılır veya `unknown` yazılır — tahminle
doldurulmaz.**

| Alan | İzinli değerler / format |
|---|---|
| `participant_id` | `P-01`, `P-02`… **Gerçek isim, telefon, e-posta, kimlik bilgisi yazılmaz.** |
| `interview_date` | `YYYY-MM-DD` |
| `cluster` | `logistics_ops` · `office_commercial` · `healthcare` |
| `occupation` | `driver` · `warehouse_worker` · `accountant` · `sales_rep` · `nurse` · `health_technician` |
| `employment_status` | `employed_not_looking` · `employed_looking` · `unemployed_looking` · `other` |
| `recent_job_search` | `active_now` · `within_3m` · `within_6m` |
| `primary_job_sources` | Serbest metin; birden çok ise `;` ile ayır (katılımcının söylediği adlar) |
| `last_job_found_source` | Serbest metin (tek kaynak adı) veya `unknown` |
| `device_last_application` | `mobile` · `desktop` · `both` · `unknown` *(A-2)* |
| `irrelevant_job_frequency` | `never` · `rare` · `sometimes` · `often` · `unknown` |
| `expired_job_experience` | `yes_with_example` · `yes_no_example` · `no` · `unknown` |
| `duplicate_job_experience` | `yes_with_example` · `yes_no_example` · `no` · `unknown` |
| `qualification_confusion` | `yes_with_example` · `yes_no_example` · `no` · `unknown` |
| `current_application_tracking_method` | `none` · `memory` · `notebook_paper` · `phone_notes` · `spreadsheet` · `platform_builtin` · `other` |
| `cv_available` | `current` · `outdated` · `none` |
| `cv_option_order` | `cv_first` · `manual_first` *(§12 sıra dönüşümü — sıra etkisi analizi için zorunlu)* |
| `cv_upload_preference` | `strong` · `mild` · `neutral` · `against` · `unknown` |
| `manual_profile_preference` | `strong` · `mild` · `neutral` · `against` · `unknown` |
| `concept_card_read_unaided` | `yes` · `partial` · `no` *(görüşmeci açıklamadan önce — §13)* |
| `explanation_usefulness` | `changed_decision_concrete` · `useful_vague` · `neutral` · `not_useful` · `unknown` |
| `unknown_row_interpretation` | `correct_unknown` · `misread_as_missing` · `misread_other` · `did_not_understand` *(D-011'in en kritik ölçümü)* |
| `verified_license_reaction` | `trust` · `concern` · `indifferent` · `did_not_notice` *(D-012)* |
| `source_transparency_value` | `matters_with_reason` · `matters_vague` · `indifferent` · `unknown` |
| `explanation_trust_concern` | Serbest metin veya `none` |
| `preferred_notification_channel` | Katılımcının **kendiliğinden** söylediği: `email` · `sms` · `whatsapp` · `app_push` · `phone_call` · `none` · `other:<metin>` |
| `acceptable_notification_frequency` | `daily` · `few_per_week` · `weekly` · `less_than_weekly` · `none` · `unknown` |
| `privacy_concern` | `none` · `mild` · `strong` + serbest metin gerekçe |
| `strongest_problem` | Serbest metin — **katılımcının kendi kelimeleriyle** |
| `switching_reason` | `real_past_switch` · `stated_intent_only` · `none` · `unknown` *(A-10; `stated_intent_only` kanıt sayılmaz)* |
| `willingness_for_second_session` | `yes` · `no` · `maybe` |
| `key_quote_summary` | Kısa doğrudan alıntı (tırnak içinde). Kimlik ipucu içeriyorsa yazılmaz. |
| `evidence_strength` | `strong` · `moderate` · `weak` · `invalid` *(§19 tanımları)* |
| `interviewer_error` | Yönlendirme/hata olduysa kısa açıklama; yoksa `none` |
| `interviewer_notes` | Serbest metin |

## 20. Görüşme Başına Özet Şablonu

```
P-__ | Cluster: ______ | Occupation: ______ | Tarih: ______

1. Bu kişi işi nasıl arıyor? (2-3 cümle)
2. En güçlü problem (kendi sözleriyle + alıntı):
3. Kanal değiştirme öyküsü var mı? Ne oldu?
4. Konsept tepkisi — anladı mı, kararını değiştirir mi?
5. CV vs manuel: tercih + gerekçe + güncel CV'si var mı?
6. Bildirim kanalı tercihi (kendiliğinden söylediği):
7. Privacy endişesi:
8. Bizi ŞAŞIRTAN şey: ______________________
   (bu alan boşsa görüşme muhtemelen yeterince açık uçlu değildi)
9. Tema bazlı kodlar: problem=__ switching=__ explanation=__ cv=__ notif=__
10. Bu görüşmede yaptığım hata:
```

## 21. Görüşmeler Arası Sentez Şablonu

```
SENTEZ — __ görüşme tamamlandı (__ Log&Ops, __ Office, __ Healthcare)
Tarih aralığı: ______   Geçersiz sayılan görüşme/soru: ______

A. TEKRAR EDEN PROBLEMLER
   Tema | Kaç kişide | Hangi cluster'larda | Kanıt gücü dağılımı | Örnek alıntı
   -----|-----------|--------------------|--------------------|-------------

B. CLUSTER FARKLARI
   Bir cluster'da güçlü, diğerinde olmayan bulgular:

C. BİZİ YANLIŞLAYAN BULGULAR   ← bu bölüm boş olamaz
   Tasarımımızın varsaydığı ama görüşmelerin desteklemediği şeyler:

D. ASSUMPTION DEĞERLENDİRMESİ
   A-10 (switching): destekleniyor / kısmen / desteklenmiyor — gerekçe:
   A-2  (mobile-first): ...
   A-4  (CV upload): ...
   A-9  ön sinyal (explainability): ...
   A-13 ön sinyal (kanal): ...

E. PERSONA DÜZELTMELERİ
   USER_PERSONAS.md'de değişmesi gereken varsayımlar:
   Eksik olduğu görülen persona tipleri (audit XP-07: gerilim personası, kamu adayı):

F. SONRAKİ ADIM
   Go / Revise / Stop önerisi + gerekçe:
   T-023 ve T-024 için taşınması gereken sorular:
```

## 22. Go / Revise / Stop Karar Çerçevesi

T-022B tamamlandığında verilecek karar. **Bu karar M1 validation gate'inin (D-010)
girdilerinden biridir; tek başına gate'i kapatmaz.**

| Karar | Ne zaman | Sonucu |
|---|---|---|
| **Go** | Birden çok cluster'da tekrar eden, adı konabilir bir problem var **ve** en az birkaç katılımcı gerçek bir kanal değiştirme/terk öyküsü anlattı **ve** konsept kartı çoğunlukla yardım almadan doğru okundu | T-023/T-024 planlandığı gibi devam eder |
| **Revise** | Problem var ama ürünün sunduğu çözümle örtüşmüyor; ya da bir cluster belirgin şekilde ayrışıyor; ya da konsept anlaşılmıyor | Konumlandırma, cluster seçimi (D-008) veya explanation tasarımı revize edilir; görüşmeler hedefli olarak sürdürülür |
| **Stop** | Tekrar eden anlamlı problem yok; katılımcılar mevcut kanallardan memnun; hipotetik olumluluk dışında kanıt üretilemedi | Ürün yönü kullanıcıyla yeniden değerlendirilir (D-010'un öngördüğü meşru sonuç) |

## 23. Önerilen Calibration Target'lar

> ⚠️ **Bunlar başarı/başarısızlık eşiği değildir.** [METRICS.md](../product/METRICS.md) §5
> hedef revizyon kuralına tabidir: ilk ölçüm baseline sayılır ve hedef gerekçeyle revize
> edilebilir. 12-18 kişilik bir çalışmada yüzdeler **yön gösterir, kanıtlamaz** — bir
> eşiğin kıl payı kaçırılması otomatik "Stop" değildir.

| Gözlem alanı | Önerilen ilk kalibrasyon | Nasıl okunur |
|---|---|---|
| Tekrar eden anlamlı problem | Katılımcıların **yarısından fazlasında**, en az **2 cluster'da** | Altındaysa: problem ya dar ya da bizim çerçevemizde |
| Gerçek kanal değiştirme/terk öyküsü (A-10) | En az **3-4 katılımcı** somut öykü anlattı | Hiç yoksa switching nedeni zayıf |
| Konsept kartını yardımsız doğru okuma | Katılımcıların **çoğunluğu** | Altındaysa explanation tasarımı revize |
| `unknown` satırını "eksiğim var" değil "bilinmiyor" diye okuma | Belirgin çoğunluk | Altındaysa D-011'in ürün dili yeniden yazılır |
| CV vs manuel tercih dağılımı | **Bilerek hedef konmadı** | Amaç kazanan seçmek değil, dağılımı ve gerekçeyi öğrenmek (A-4) |
| Bildirim kanalı tercihi | **Bilerek hedef konmadı** | E-posta baskın çıkmazsa D-016 T-027 ile yeniden açılır |

## 24. Limitations

- **12-18 kişi istatistiksel temsil değildir.** Bulgular desen gösterir, oran vermez.
- **Seçilim yanlılığı:** görüşmeyi kabul edenler, iş arama konusunda daha istekli/
  konuşkan kişiler olabilir. Sessiz çoğunluk temsil edilmeyebilir.
- **Konsept kartı gerçek ürün değil.** Statik bir kart üzerinden ölçülen anlaşılırlık,
  çalışan bir üründeki deneyimi garanti etmez.
- **A-9 ve A-13 burada tam test edilmez** — T-023 ve T-027 asıl testlerdir.
- **Görüşmeci etkisi:** tek görüşmeci varsa kendi yanlılığı bütün veriye yayılır.
  Mümkünse ilk 2 görüşmede ikinci bir gözlemci bulunması önerilir.
- **Dil ve bölge:** görüşmeler Türkçe ve sınırlı sayıda ilde yapılacak; bölgesel farklar
  yakalanmayabilir.
- Bu çalışma **coverage ölçmez** — o T-021'in işidir ve karıştırılmamalıdır.

## 25. Open Questions

- **❓ TQ-1:** Teşvik verilecek mi, ne kadar? *(yanlılık ↔ katılım dengesi — kullanıcı kararı)*
- **❓ TQ-2:** İkinci gözlemci bulunabilecek mi? *(görüşmeci yanlılığı azaltma)*
- **❓ TQ-3:** Konsept kartı hangi occupation için hazırlanacak — her cluster'a ayrı kart mı,
  tek jenerik kart mı? *(cluster'a özel kart daha gerçekçi ama karşılaştırmayı zorlaştırır)*
- **❓ TQ-4:** Ses kaydı alınacak mı? Alınırsa kayıtların saklama süresi ne olacak?
  *(PRIVACY §2 ile hizalanmalı; T-008 girdisi)*
- **❓ TQ-5:** Hastane/işyeri ortamında görüşme yapılacaksa kurum izni nasıl alınacak?
- **❓ TQ-6:** Kaç görüşmeden sonra sentez yapılacak? *(öneri §"sonraki adım": cluster
  başına en az 4, toplam en az 12 — ama doygunluk erken gelirse daha az olabilir)*
