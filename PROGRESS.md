# PROGRESS.md — İlerleme Kaydı

> **Purpose:** Mevcut durumun ve son tamamlanan işlerin kaydı; kronolojik, en yeni üstte.
> Her session sonunda entry eklenir. Güncel durum özeti için [CONTEXT.md](CONTEXT.md);
> task status'ları için [TASKS.md](TASKS.md); milestone/release kayıtları için
> [CHANGELOG.md](CHANGELOG.md).
>
> Faz kapanışında eski entry'ler `archive/PROGRESS-<faz>.md` altına taşınır; aktif dosyada
> güncel faz kalır.

## 2026-07-21 — Arayüz elden geçirildi: filtre, ilan linki, tam metin, okunabilirlik

Kullanıcı üç şey söyledi: filtre yok, tasarım sönük, ilan linki ve tam gereksinimler
görünmüyor, profil sayfası okunaksız. Hepsi haklıydı.

**En ciddisi: "İlana git" düğmesi hiç yoktu.** Ürünün asıl eylemi kullanıcıyı ilanın
kendi sayfasına götürmek — D-020'nin bütün gerekçesi buydu — ama arayüzde URL yalnızca
düz metin olarak duruyordu. Artık hem kartta hem detay sayfasının başvuru panelinde
belirgin bir bağlantı var (`target="_blank" rel="noopener noreferrer"`), yanında
"başvuru ilanın kendi sayfasından yapılır, biz aracı değiliz" notuyla.

**İlanın tam metni** detay sayfasına eklendi. Adapter'ın `lists`'ten koruduğu bölüm
başlıkları (`## Requirements` gibi) artık başlık ve madde listesi olarak render
ediliyor; uzun metin katlanıp "Tamamını aç" ile açılıyor.

**Filtreler:** serbest arama (başlık + işveren + şehir + şart), şehir, işveren, meslek
alanı ve durum (tümü / değerlendirilenler / güçlü-iyi). 61 ilan bellekte olduğu için
filtreleme istemci tarafında ve anında; kalıcılığa geçilince sunucuya taşınmalı.

**Profil sayfası yeniden kuruldu.** 82 alanın düz liste hâlinde dökülmesi okunaksızdı.
Artık 15 açılır grup var ve yalnızca kullanıcının kaydı olan gruplar açık geliyor;
üstte seçilenlerin rozet listesi, doğrulanmış oranını gösteren ilerleme çubuğu ve
alan araması var. CV önerileri için "hepsini onayla" eklendi.

**Görsel dil güçlendirildi.** Bant rengine göre kart şeridi, işveren monogramı,
karşılanan şartların yeşil etiketleri, başlıkta canlı istatistikler (ilan / eşleşme /
işveren), sekmelerde sayaç. Renk paleti derinleştirildi ama kural korundu: `unknown`
hâlâ **mavi/bilgilendirici**, amber/uyarı değil — D-011'in görsel karşılığı.

**Hacim araştırıldı, artmıyor.** ~120 Türk şirketi slug'ı beş ATS platformunda tarandı;
yalnızca bir pano daha bulundu (Çiçeksepeti, 2 ilan). Türkiye'de Lever/Greenhouse/
Recruitee kullanan şirket sayısı gerçekten az. **Hacim ve mavi yaka kapsamı için
Careerjet/Jooble şart** (OPEN-24); publisher kaydı kullanıcıya ait. Bu sınır arayüzde
açıkça yazılıyor.

**Bulunan hata: sayfa "Yükleniyor…"da dondu.** Açıklama render'ını eklerken Python
heredoc'unda `
` kaçışı kayboldu, gerçek satır sonuna dönüşüp regex'i bozdu ve
**script hiç parse edilmedi**. Konsola hata düşmediği ve API 200 döndüğü için sorun
backend'de sanılabilirdi. `node --check` ile yakalandı; bu kontrol artık handoff'ta
zorunlu adım olarak yazılı.

**Doğrulama.** 70 test geçiyor. Arayüz gerçekten gezilerek doğrulandı: filtre 61 → 14
(güçlü/iyi), "devops" araması 6 ilgili ilan, profil araması "ehliyet" → 3 alan, detay
sayfasında 2 bölüm başlığı + 12 madde + başvuru bağlantısı.

---

## 2026-07-21 — Gerçek ilanlar: izinli ATS API'leri (D-020) + paylaşılan sözlük

Kullanıcı kendi CV'sini yükledi ve **hiçbir alan eşleşmedi**; ayrıca LinkedIn'den
ilan çekmek istediğini söyledi. İkisi de haklı eleştiriydi ve ikisi de düzeltildi.

**LinkedIn: yasal yolu yok — ve aranmadı.** Araştırma sonucu: LinkedIn'in okuma
API'si **hiç yok**; Job Posting API ters yönde çalışıyor (ATS → LinkedIn) ve
Microsoft'un kendi dokümanı yeni partner alınmadığını yazıyor; robots.txt
`Disallow: /` ve otomatik erişimi açıkça yasaklıyor. Indeed'in publisher API'si de
kapatılmış. Bunları aşmanın yolu **önerilmedi**.

**D-020 — izinli ATS API'leri açıldı.** Lever, Greenhouse ve Recruitee'nin public
job board uçları, şirketlerin kendi kariyer sayfalarını kurması için yayınladığı,
kimlik doğrulaması istemeyen API'lerdir; yanıt ilanın **kendi sayfasına** giden URL
taşır — yani kullanıcıyı kaynağa yönlendirmek amaçlanan kullanım. İzin kanıtları
(`api.lever.co/robots.txt` → `Allow: /` + `Crawl-delay: 1` vb.) doğrulanıp
Source Registry'ye **kanıt alanıyla** yazıldı. D-018'in "hiçbir kaynağa crawl yok"
maddesinin yerini yeni bir denetim aldı: **izin iddiası kanıtsız yazılamaz.**

Sonuç: 5 pano (Trendyol, Dream Games, iyzico, Commencis, Macellan), 70 ilan çekildi,
18'i Türkiye dışı olduğu için elendi, **52 gerçek Türkiye ilanı** gösteriliyor.
Crawl-delay uygulanıyor; pano listesi elle tutuluyor, otomatik keşif yok.

**CV'nin neden eşleşmediği — kök neden.** Katalog *korpustan* türetiliyordu: profil
editörü yalnızca 8 sentetik ilandaki 18 alanı tanıyordu. İki taraf da aynı sentetik
korpustan geldiği için sistem "çalışıyor" görünüyordu. Gerçek bir CV yüklendiğinde
eşleşecek **hiçbir alan yoktu** — extraction bozuk değildi, hedef yoktu.

Düzeltme: ilan tarafı ile CV tarafı artık **aynı sözlüğe** bağlı
(`isuygun_ingest.lexicon`, 82 terim, 15 meslek kümesi — yazılımdan kaynakçılığa,
hemşirelikten aşçılığa). Katalog korpustan bağımsız. Bir yazılımcı CV'siyle test:
önce 0 alan, şimdi 13 alan (Python 4 yıl dahil, doğru okundu).

**Gerçek veri üç ciddi hata gösterdi.**

1. **Yanlış duplicate birleştirme.** iyzico'nun "Instore Sales Manager" ile
   "Senior AML Analyst" ilanları %100 benzer çıkıp tek ilana indirgeniyordu. Sebep:
   Lever'ın `descriptionPlain` alanı çoğu ilanda yalnızca şirket tanıtımıdır ve
   firmanın bütün ilanlarında birebir aynıdır. Asıl içerik `lists` altındaki
   bölümlerde. Adapter düzeltildi; ayrıca Geçit B'ye koruma eklendi — aynı **bilinen**
   işverenin ilanları B'den geçemez (B'nin amacı işvereni *gizlenmiş* kopyalar).
2. **Parantez soyma yanlıştı.** "Software Engineer" ile "Software Engineer (New Grad)"
   aynı anahtara düşüp Geçit A'da birleşiyordu. Artık soyulmuyor: yanlış birleştirme
   gerçek bir ilanı kullanıcıdan **tamamen gizler**, kaçırılan birleştirme yalnızca
   iki kez gösterir. Asimetri kararı belirledi.
3. **D-021 — ayırt edici olmayan şartlar sahte güven üretiyordu.** Bir yazılımcı
   profiline **"Legal Professionals — Labor Law"** ilanı *Güçlü eşleşme* çıktı; o
   ilandan yalnızca "İngilizce" ve "Lisans mezuniyeti" çıkarılabilmişti ve geliştirici
   ikisine de sahipti → 1/1 → güçlü. Artık değerlendirilebilen şartların hepsi
   `language`/`education`/`shift` kategorisindeyse bant üretilmiyor. Eşleşen ilan
   sayısı 34'ten 16'ya düştü — **kasıtlı**: az ve doğru, çok ve yanlıştan iyidir.

**Diğer düzeltmeler.** Meslek kümesi tahmininde başlık ağırlığı (önce "Accounting
Intern" ilanı metninde SQL geçtiği için "Yazılım" kümesine düşüyordu) · "What We
Offer" bölümü şart sayılmıyor · Türkiye dışı ilanlar eleniyor (pazar filtresi core'a
gömülmedi, D-009 gereği politika parametresi) · olumlu bantlı ilanda açıklama önce
karşılanan şartları söylüyor.

**Doğrulama.** 70 test geçiyor (core 19, ingest 29, API 22). API testleri artık
**ağa çıkmıyor** — canlı ingest'i her testte çağırmak hem yavaştı hem de dış servise
gereksiz yüktü, ayrıca testi uzak sunucunun o anki içeriğine bağlıyordu.

**Kapsam sınırı gizlenmiyor.** ATS panoları ağırlıklı olarak teknoloji/kurumsal ilan
içerir; arayüz bunu açıkça yazıyor. Mavi yaka kapsamı için Careerjet/Jooble publisher
kaydı gerekiyor — kayıt kullanıcıya ait (OPEN-24).

---

## 2026-07-21 — Uygulama ayağa kalktı: API + arayüz (fixture veriyle uçtan uca)

Kullanıcı "her şeyi başlatalım ve bir tur test edeyim" dedi. API ve arayüz katmanları
kuruldu; uygulama tek komutla çalışıyor ve gerçekten tıklanabilir durumda.

**`services/api` — FastAPI.** Katman **iş kuralı içermiyor**; değerlendirme mantığı
core'da, toplama mantığı ingest'te kalıyor. Kural API'de tekrar edilseydi iki yerde
birbirinden sapardı. Uçlar: feed, ilan detayı, profil CRUD, belge doğrulama, CV
yükleme, kaynak şeffaflığı. OpenAPI şeması `/openapi.json`'dan üretiliyor —
TypeScript tipleri buradan gelecek (ADR-001 şema kayması önlemi).

**`web/` — arayüz.** Tasarım yönü bilinçli olarak iş ilanı sitelerinin tersi: "%95
uyum!" bağırışı yerine **ilan panosu / basılı kayıt** estetiği. Serif başlıklar,
ruled satırlar, tek aksan rengi (emaye mavisi). Kritik karar: `unknown` durumu
**mavi/bilgilendirici** renkte, amber/uyarı değil — D-011'in görsel karşılığı.
"Bilinmiyor" bölümü "eksiğin var" değil "bilmediğimiz şeyler" diye yazıldı ve her
satır bir eylem sunuyor. Açık/koyu tema ve dar ekran desteği var.

**Next.js'e taşıma ertelendi.** Kullanıcının bugün test edebilmesi için arayüz statik
HTML olarak yazıldı ve FastAPI tarafından servis ediliyor — tek süreç, build adımı
yok. OpenAPI tipleri hazır olduğu için taşıma mekanik bir iş.

**`taxonomy.py` — profil kataloğu korpustan türetiliyor.** Matching, şart anahtarı ile
profil alanı eşitliğine dayanıyor; gerçek sistemde bu bir **ontoloji** işi (ESCO
benzeri). MVP'de ontoloji **yok**; katalog doğrudan ilanlardaki şartlardan üretiliyor
ki profil editörü ile ilanlar arasında sessiz kayma oluşamasın. Bu kasıtlı bir
sadeleştirme — **OPEN-23** olarak açıldı.

**CV akışı (T-016).** PDF'ten metin çıkarılıyor, alan **öneriliyor**, hiçbir şey
profile yazılmıyor; kullanıcı tek tek onaylıyor. Sensitive alanlar (D-006) okuma
anında tespit edilip atılıyor ve yalnızca **alan adı** raporlanıyor — içerik hiçbir
yere yazılmıyor. Test CV'sindeki doğum tarihi ve medeni hal doğru şekilde imha edildi.

**CV önerisinde iki gerçek hata bulundu ve düzeltildi.** İlk koşuda şoför CV'sine
**"Hemşirelik tescil belgesi"** öneriliyordu — "belgesi" kelimesi eşleştiği için.
Ayrıca **"Gece vardiyası"** öneriliyordu: "geçerli" kelimesinin *içinde* "gece"
geçiyor. Substring eşleşmesi kelime sınırı tanımıyordu. Üçüncüsü: CV'ler Türkçe
karakter kullanmadan da yazılıyor ("Agir vasita") ve katlama olmadığı için bu CV'ler
hiç eşleşmiyordu. Üçü de düzeltildi (kelime sınırı + genel kelime süzgeci + `fold()`);
öneri sayısı 11'den 7'ye düştü ve hepsi şoförle ilgili. Regresyon testleriyle kilitlendi.

**Arayüzde yön hatası.** Metinler sağa yaslanmıştı; Türkçe soldan sağa yazılır.
Liste ve tablo hizalamaları düzeltildi.

**Doğrulama.** 65 test geçiyor (core 17, ingest 27, API 21). API testleri iş kuralını
tekrar doğrulamıyor; kuralın **HTTP sınırında kaybolmadığını** doğruluyor — bir kural
orada düşerse core testleri geçmeye devam eder ama kullanıcı yanlış şey görür.
Kapsananlar: boş profilde hiçbir ilanın "zayıf" etiketlenmemesi, doğrulanmamış
ehliyetin `met` sayılmaması, askerlik şartının katalogda bulunmaması ve yazılamaması,
kamu ilanının puanlanmaması, hiçbir uçtan yüzde sızmaması, hiçbir gerçek kaynağın
ağ erişimine açık olmaması.

**Bilinen sınırlar.** Kalıcılık **yok** — profil bellekte tutuluyor, sunucu kapanınca
gidiyor (PostgreSQL sıradaki iş). CI yok. Belge doğrulama akışı MVP'de **simüle**
ediliyor ve arayüzde öyle etiketleniyor. Taranmış PDF'te OCR yok.

**Bu session'da da hiçbir kaynağa ağ isteği gönderilmedi.** İlanlar sentetiktir.

---

## 2026-07-21 — Stack kararı + çalışan çekirdek (core + ingest, fixture veriyle)

Kullanıcı Seçenek B'yi seçti: stack'i belirle, mimari kararları al, uygulamaya geç.
Üç karar alındı (AskUserQuestion): **Python veri + TS arayüz**, **M1 gate kısmi
revizyon**, **tek sunucu/container**.

**D-001 kapandı — [ADR-001](docs/adr/ADR-001-technology-stack.md).** Python
(ingest + matching + API/FastAPI) + TypeScript/Next.js (web) + PostgreSQL/pgvector,
Docker Compose ile tek makinede. Hibrit stack'in asıl riski **şema kayması**; çözüm
yapısal: FastAPI → OpenAPI → generated TypeScript tipleri, CI regenerate diff'inde
kırılır. Python tarafının seçilme gerekçesi audit'ten geliyor — iki CRITICAL bulgunun
ikisi de "model geçersiz durumu ifade edebiliyor" tipindeydi; `Literal` union'lar ve
frozen dataclass'lar bu durumları temsil edilemez kılıyor.

**D-018 — M1 gate kısmen revize edildi.** Implementation fixture veriyle başlar; gate
(1) gerçek source'a crawl ve (2) gerçek kullanıcı alma için aynen durur.

**`services/core` — domain + matching + explanation.** Audit'in iki CRITICAL bulgusu
tip düzeyinde temsil edilemez kılındı: `RequirementState` üç varyantlı
(`met`/`unmet`/`unknown`), `unknown` **gerekçesiz oluşturulamıyor** (`__post_init__`
ValueError atıyor); gate-relevant kategoriler (`license`, `work_authorization`,
`legally_required_certificate`) `verified` olmadan `met` üretemiyor. `unknown` skorun
paydasına girmiyor — cezalandırılmıyor, yalnızca confidence'ı düşürüyor.

**D-019 — implementation sırasında bulunan gerçek hata.** Uçtan uca ilk koşuda şoför
profiline hemşire ilanı **"Zayıf eşleşme"** çıktı. Nedeni şartların karşılanmaması
değil, hiç değerlendirilememesiydi: değerlendirilebilir kütle sıfır olunca skor 0
çıkıyor ve zayıf banda düşüyordu — `unknown`'ın arka kapıdan `unmet` gibi
cezalandırılması, yani D-011'in **bant düzeyindeki** ihlali. Skor katmanı doğruydu,
kaçak bant katmanındaydı. Artık hiçbir şart değerlendirilemiyorsa bant üretilmiyor
(`insufficient_data`). Aynı koşuda ikinci bir hata daha çıktı: explanation katmanı
karşılanan şart yokken "Mesleğin ilanla örtüşüyor" diye **kanıtsız iddia** üretiyordu;
kaldırıldı.

**`services/ingest` — Source Registry + pipeline.** Registry, D-002/D-018'in kod
düzeyindeki zorlayıcısı: `assert_fetchable()` izinsiz kaynakta uyarı değil
**exception** atıyor ve mesaj bypass yolu değil izin yolunu (OPEN-19/OPEN-09)
gösteriyor. Kayıtlı 6 kaynağın hiçbiri gerçek+`allowed` değil; tek çalıştırılabilir
kaynak `src-fixture-001`.

Dedupe, audit'in SCR-02 bulgusuna göre **blocking ile matching ayrılarak** yazıldı:
Geçit A (employer+title+city) anahtar eşitliğiyle birleştirir; Geçit B işverenden ve
başlıktan bağımsız kaba blok üretir, karar blok içi Jaccard benzerliğiyle verilir.
Tek anahtarlı tasarım, agency'nin işvereni gizleyip başlığı değiştirdiği kopyayı
*hiç karşılaştırmadan* kaçırıyordu; iki aşamalı yapı yeniden yazılmış kopyaları da
yakalıyor. Blok büyüklüğü sınırı aşılırsa kayıtlar sessizce atılmıyor,
`oversized_blocks` olarak raporlanıyor.

**Türkçe normalizasyonda iki gerçek bug bulundu ve düzeltildi.** `unicodedata
.normalize("NFKD", ...)` Türkçe harfleri parçalıyordu (`ş` → `s` + birleşen çengel);
sonraki noktalama temizliği çengeli silince "şirketi" → "s irketi" oluyor ve kelime
sınırı bozuluyordu. Ayrıca NFKD, legal-form eşleşmesinden **önce** çalıştığı için
"anonim şirketi" hiç yakalanmıyordu — yani duplicate anahtarı sessizce çalışmıyordu.
Açık bir Türkçe katlama tablosuyla değiştirildi; hukuki form yalnızca **sondan**
soyuluyor ("Ticaret Lisesi Vakfı" bozulmuyor). Regresyon testleriyle kilitlendi.

**Doğrulama.** 44 test geçiyor (core 17, ingest 27). Uçtan uca fixture koşusu:
8 ilan → 7 canonical, 1 agency kopyası birleşti, kullanıcıya işvereni **yazan** sürüm
gösteriliyor. Kamu ilanı skor üretmiyor (D-015), askerlik şartı bilgilendirme olarak
görünüyor (D-013), doğrulanmamış ehliyet şartlı banda düşürüyor (D-012).

**Bu session'da yapılmayanlar:** hiçbir kaynağa ağ isteği gönderilmedi; gerçek ilan
verisi kullanılmadı; T-021/T-022B'ye dokunulmadı. Fixture'lardaki tüm ilanlar
sentetiktir, `example.invalid` alan adı kullanır.

---

## 2026-07-21 — T-022A: Interview hazırlığı + OPEN-19 izin taslakları (Done)

T-003 kullanıcı tarafından kabul edildi; `fb3bf17` T-003 final baseline'ı olarak
sabitlendi. Ardından T-022 ikiye ayrıldı ve hazırlık aşaması tamamlandı.

**T-022A — saha materyalleri (Done).**
[USER_INTERVIEW_VALIDATION_PLAN.md](docs/research/USER_INTERVIEW_VALIDATION_PLAN.md):
25 bölüm + CSV kod defteri. Tasarımın çekirdeği, görüşmenin ilk iki bölümünde ürünün
**hiç anlatılmaması** ve yalnızca geçmiş davranışın sorulması; konsept ancak Bölüm C'de
tek bir kartla gösteriliyor. Hipotetik olumluluk ("kullanırdım", "güzelmiş") açıkça
**kanıt sayılmıyor**; kanıt gücü dört kademeli kodlanıyor (strong/moderate/weak/invalid)
ve yalnızca ilk ikisi sentezde sayılıyor. Yönlendirici soru kaçınma rehberi, red flag
listesi ve "bizi yanlışlayan bulgular" bölümü zorunlu tutulan sentez şablonu eklendi.
Kota: 12-18 katılımcı, cluster başına en az 4.

[USER_INTERVIEW_RESPONSE_TEMPLATE.csv](docs/research/USER_INTERVIEW_RESPONSE_TEMPLATE.csv):
34 alanlı, **yalnızca başlık satırı** — hiçbir örnek/hayali yanıt yok. İsim, telefon,
e-posta ve doğrudan kimlik alanı **bilinçli olarak yok**; katılımcılar `P-01` gibi
takma kimlikle kaydediliyor.

**T-022B — Pending Fieldwork / Blocked (External Input).** Görüşmeleri kullanıcı yürütür.
Gerçek katılımcı verisi olmadan tamamlanamaz; hayali görüşme cevabı veya validation
sonucu üretilmedi ve üretilmeyecek.

**OPEN-19 — izin talebi taslakları (gönderilmedi).**
[SOURCE_PERMISSION_REQUESTS_TR.md](docs/research/SOURCE_PERMISSION_REQUESTS_TR.md):
İşin Olsun/Kariyer.net grubu ve İŞKUR için ayrı taslaklar; her biri kısa + detaylı
sürüm, teknik ek bilgi listesi, net sorular, takip mesajı ve **gelen cevabın Source
Registry'ye nasıl işleneceği** tablosu içeriyor. Taslaklar hukuki pozisyon almıyor,
karşı tarafın şartlarını kendi lehimize yorumlamıyor; yalnızca izin ve uygun entegrasyon
yöntemini soruyor. Restriction bypass edilmeyeceği, verinin satılmayacağı, kaynak ve
orijinal URL'in korunacağı, başvurunun orijinal kaynaktan yapılacağı açıkça yazılı.
**İletişim adresleri uydurulmadı — `Unknown` bırakıldı** ve gönderim öncesi doğrulama
şartı kondu.

**Yeni açık soru:** OPEN-21 (teşvik, ses kaydı ve kayıt saklama süresi — kullanıcı kararı).

## 2026-07-21 — T-003: Türkiye source landscape araştırması (Done)

15 aday kaynak, birincil kanıta (robots.txt, public ToS/sözleşme sayfaları, sitemap'ler,
public listing sayfaları) dayanarak incelendi. Kanıt dosyası:
[TURKEY_SOURCE_LANDSCAPE.md](docs/research/TURKEY_SOURCE_LANDSCAPE.md); registry kayıtları
[SOURCE_REGISTRY.md](docs/architecture/SOURCE_REGISTRY.md) §5.

**Tavsiye: CONDITIONAL GO.** Wave 1 = isinolsun.com (iki cluster'ı tek başına taşıyor,
robots tam izinli, sitemap'li, adapter karmaşıklığı düşük). Wave 2 = İŞKUR e-Şube (farklı
işveren havuzu → gerçek cross-source dedupe testi) + Kamu İlan/SBB (D-015 listing-only
davranışını gerçek veriyle test eder). Fallback: SecretCV, Boğaziçi Kariyer Merkezi,
ATS tenant'ları.

**En önemli bulgu — izin belirsizliği kaynak yokluğundan daha bağlayıcı:** MVP'ye aday
hiçbir kaynak koşulsuz `allowed` değil. isinolsun robots açısından tam izinli ama üyelik
sözleşmesi §4.12 veri kopyalamayı yazılı izne bağlıyor; kariyer.net'in ToS sayfası
otomatik erişime 403 dönüyor; yenibiris.com'un robots.txt'i bile 403; Indeed ve LinkedIn
iş ilanı path'lerini açıkça yasaklıyor (LinkedIn ayrıca dosya başında açık ifadeyle).
Kamu kaynaklarında robots izinli ama hiçbirinde yeniden kullanım lisansı yok.

**Rejected:** Indeed, LinkedIn, eleman.net (robots ilan path'lerini kapatıyor),
yenibiris.com (robots okunamıyor), ODTÜ KPM (login wall), iskur.gov.tr kurumsal host
(`/is-arama?*` disallow — e-şube host'undan ayrı kayıt). Hiçbiri için bypass
araştırılmadı, önerilmedi veya tasarlanmadı.

**Tasarımı doğrulayan iki bulgu:** (1) FS-12 access-change detection spekülatif değil —
araştırma sırasında üç canlı 403 örneği görüldü. (2) Tek source ile core loop
doğrulaması teknik olarak mümkün (isinolsun iki cluster'ı taşıyor) → ROADMAP M2 ve
T-017'nin düzeltilmiş dependency yapısı destekleniyor.

**Acceptance sapması (bilinçli):** "cluster başına asgari ilan hacmi doğrulandı" kriteri
niceliksel karşılanamadı; hacim tahminleri niteliksel kaldı. Nicel ölçüm T-021'e
devredildi ve T-021 acceptance'ı buna göre genişletildi (çapraz yayın, işveren gizleme,
posted_at görünürlük oranları da aynı örneklemden ölçülecek).

**Yeni açık sorular:** OPEN-18 (§4.12 kapsamı), OPEN-19 (yazılı izin talebi — kullanıcı
kararı), OPEN-20 (healthcare cluster zayıflığı). OPEN-09 M1-blocker'a yükseltildi.

## 2026-07-21 — Audit ve hedefli documentation revision

**Audit (12 bağımsız reviewer, 35 dosya):** 134 bulgu üretildi ve yüksek-severity
bulgular adversarial doğrulamadan geçirildi. Sonuç: 0 BLOCKER, 2 CRITICAL, 19 HIGH,
96 MEDIUM, 17 LOW. Hiçbir bulgu tümüyle çürütülmedi; 33'ünün şiddeti doğrulama sonrası
düşürüldü. Genel değerlendirme: set "review-ready" ama "build-ready" değildi.

**Kullanıcı kararları (K-1…K-10 → D-008…D-017):** MVP kapsamı üç cluster / ~6 first-class
occupation'a daraltıldı; launch pazarı Türkiye seçildi (core market-neutral kalmak
şartıyla); implementation öncesi validation gate zorunlu kılındı; requirement
değerlendirmesi üç durumlu (met/unmet/unknown) yapıldı; gate-relevant alanlar için
doğrulama şartı getirildi; legal eligibility kavramı sensitive attribute'tan ayrıldı;
Manual Review Queue minimal moda alındı (~2 saat/hafta); public sector listing-only
tanımlandı; notification sabit haftalık e-posta digest'e sabitlendi; matching ~8 MVP
faktörü + ≤~%10 semantic reranking ile sınırlandı.

**Kapatılan iki CRITICAL:**
- *Missing information ≠ unmet requirement:* üç durumlu değerlendirme veri modeline,
  invariant'lara, matching pipeline'ına, flow'lara ve requirement'lara işlendi.
- *Unverified license gate'i geçebiliyordu:* `verification_state` modeli, gate-relevant
  alan sınıfı ve invariant #8 genişletmesiyle kapatıldı.

**Kapatılan uygulanabilirlik boşlukları:** requirements şemasına min_years/level/
jurisdiction/verification/evidence alanları; skills ve languages için ortak proficiency
ölçeği; shift_info structured şeması; Employer entity + Employer Identity Resolver;
Feed & Search Service'in arama sahipliği; freshness'ın final ranking'deki yeri;
extraction'ın pipeline'daki tek konumu (iki fazlı yazma); MatchResult invalidation
tetikleyicileri; cold start davranışı; yield/coverage anomali izlemesi; access-change
(login wall) tespiti; source emergency takedown; MatchResult/analytics/backup/MRQ/
iletişim bilgisi için privacy envanteri.

**Süreç düzeltmeleri:** AGENTS.md tek normatif kural seti oldu ve otorite tablosu
kazandı; CLAUDE.md Claude'a özgü minimuma indirildi; CONTEXT.md'ye 17 kalemlik Open
Question Index eklendi ve güncelleme tetiği checklist'e bağlandı; TASKS.md status
semantiği ve arşiv kuralı tanımlandı; ADR tetiğinin tek sahibi docs/adr/README.md oldu;
CHANGELOG milestone bazlıya çekildi; GLOSSARY'ye 16 eksik terim eklendi; PRD'ye
Feature→Requirement→Flow traceability matrisi ve MoSCoW↔scope kuralı eklendi.

**Task revizyonu:** 11 yeni task (T-021…T-031: yedi validation çalışması + golden set
üretimi + employer identity + privacy inventory + MVP faktör seti + public sector
davranışı); T-017'nin dependency'si düzeltildi — core loop artık tek source ile
doğrulanabiliyor, cross-source dedupe (T-015) ön şart değil.

**Version control:** Repository git altına alındı; revizyon öncesi durum ayrı bir
snapshot commit'te korundu.

**Bilinen açık:** Open Question Index'teki M1-blocker kalemler (özellikle retention/SLA
değerleri, taxonomy standardı, harici AI servis izni) T-008 ve T-004 ile kapanacak.

## 2026-07-20 — Faz 0: Documentation seti oluşturuldu

- Boş repository üzerinde tam documentation yapısı kuruldu (root + docs/product +
  docs/architecture + docs/security + docs/quality + docs/operations + docs/adr).
- Product vision, PRD (MVP/V1/Future scope), personas, flows, requirements, roadmap,
  metrics ve glossary yazıldı.
- System architecture, scraping/ingestion mimarisi, Source Registry, Matching Engine,
  Occupation Taxonomy, AI system, domain/data model ve API contract'ları tasarlandı.
- Privacy/security/compliance çerçevesi, risk register, test stratejisi, observability
  ve runbook oluşturuldu.
- İlk kararlar [DECISIONS.md](DECISIONS.md)'ye kaydedildi (D-001…D-007). *(Düzeltme
  2026-07-21: bu kayıtlar ADR değildir; docs/adr/ altında henüz ADR yoktur — bkz.
  [BUGS.md](BUGS.md) BUG-001.)*
- Initial task breakdown [TASKS.md](TASKS.md) içine eklendi (T-001…T-020).
- Bilinen eksik: hedef pazar, başlangıç source listesi ve business model kullanıcı
  onayı bekliyor (bkz. CONTEXT.md → Açık Konular).
