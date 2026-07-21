# SESSION_HANDOFF.md — Session Devir Kayıtları

> **Purpose:** Bir çalışma session'ı biterken bir sonraki session'ın (insan veya agent)
> kaldığı yerden devam edebilmesi için yazılan devir kayıtları. Aşağıdaki template her
> session sonunda kopyalanıp doldurulur; en yeni kayıt en üstte durur.
> Kalıcı proje durumu [CONTEXT.md](CONTEXT.md) dosyasındadır — burada tekrar edilmez,
> yalnızca session'a özgü bilgiler yazılır.

---

## Template (kopyala ve doldur)

```markdown
## [YYYY-MM-DD] — [kısa session başlığı]

**Bu session'da yapılanlar:**
- ...

**Yarım kalanlar (dosya/konum ile):**
- ...

**Bir sonraki session'ın ilk adımı:**
- ...

**Bu session'da alınan kararlar / yeni assumption'lar:**
- ... (DECISIONS.md / ilgili dokümana işlendi mi? ✔/✘)

**Yeni open question'lar:**
- ...

**Dikkat edilmesi gerekenler / tuzaklar:**
- ...
```

---

## 2026-07-21 — Avrupa/ABD kapsamı (70 pano) + performans + D-022

**Bu session'da yapılanlar:**
- 70 ATS panosu (ABD/AB/TR), Ashby fetcher, pano başına 40 ilan sınırı.
- `regions.py` — bölge sınıflandırma (politika katmanı), arayüzde bölge filtresi.
- Performans: önbellekten yükleme **100s → 16s** (iki gerçek hata düzeltildi).
- **D-022** — bant tavanı: kanıt miktarı iddianın gücünü sınırlar.
- Aynı rolün farklı konumları gösterimde gruplanıyor.
- Detay: [PROGRESS.md](PROGRESS.md) → "Avrupa/ABD kapsamı".

**Yarım kalanlar:**
- **OPEN-24 kullanıcı kararı bekliyor:** ek kaynaklar (Arbeitsagentur, JobTechDev,
  The Muse, Himalayas, Arbeitnow auth'suz; Adzuna/USAJOBS/Reed ücretsiz kayıt).
  **Kaynak eklemek onay gerektirir — kendiliğinden ekleme.**
- **OPEN-25:** registry `attribution_required` / `min_poll_interval` /
  `redistribution_policy` taşımıyor. RemoteOK ve Jobicy sert atıf şartı koyuyor,
  Remotive günde 4 istekle sınırlı — bunlar modellenmeden eklenmemeli.
- Kalıcılık yok (açılış 16s, önbellek `.cache/` altında, 6 saat TTL).
- Mavi yaka ve TR hacmi hâlâ düşük (62 ilan).

**Dikkat edilmesi gerekenler / tuzaklar:**
- **`.cache/ats_postings.json` 16 MB ve git'te değil.** Silinirse ilk açılış
  dakikalarca sürer (70 pano × crawl-delay).
- **`lexicon.scan` sıcak yol.** Property içinde regex derleme veya terim başına
  ayrı arama eklersen ingest 5 kat yavaşlar. Test: 2445 ilan < 20 sn.
- **LinkedIn/Indeed'e dokunma.** Kullanıcı iki kez istedi; ikisinde de yasal yol
  olmadığı için yapılmadı. `test_rejected_sources_stay_rejected` bunu denetliyor.
- `web/index.html` düzenledikten sonra `node --check` (bkz. önceki handoff).

---

## 2026-07-21 — Arayüz elden geçirildi: filtreler, ilan linki, tam metin

**Bu session'da yapılanlar:**
- **İlan linki eklendi** — hem kartta hem detayda "İlana git ↗". Ürünün asıl eylemi
  buydu ve arayüzde hiç yoktu; URL yalnızca düz metin olarak duruyordu.
- **İlanın tam metni** detay sayfasına eklendi (bölüm başlıkları + madde listesi).
- **Filtreler:** arama, şehir, işveren, meslek alanı, durum. İstemci tarafında
  (59 ilan bellekte; anında tepki için).
- **Profil sayfası** açılır/kapanır gruplara bölündü (15 grup, yalnızca dolu olanlar
  açık), arama kutusu + seçilenler özeti + ilerleme çubuğu eklendi.
- Görsel dil güçlendirildi: bant rengine göre kart şeridi, işveren monogramı,
  karşılanan şart etiketleri, başlıkta canlı istatistikler.
- Çiçeksepeti panosu eklendi (61 ilan).

**Yarım kalanlar:**
- **Hacim düşük ve artmıyor.** Geniş tarama yapıldı; Türkiye'de Lever/Greenhouse/
  Recruitee kullanan şirket sayısı çok az. Hacim ve mavi yaka kapsamı için
  Careerjet/Jooble şart (OPEN-24) — publisher kaydını kullanıcı yapacak.
- Kalıcılık yok, CI yok, Next.js'e taşınmadı.
- Filtreleme istemci tarafında; kalıcılığa geçince sunucu tarafına taşınmalı.

**Bir sonraki session'ın ilk adımı:**
- Kullanıcı onayı bekleniyor. Öncelik: Careerjet (hacim) mi, kalıcılık mı?

**Dikkat edilmesi gerekenler / tuzaklar:**
- **`web/index.html` düzenledikten sonra `node --check` çalıştır.** Sözdizimi hatası
  olunca script hiç parse edilmiyor, sayfa "Yükleniyor…"da donuyor ve **konsola hata
  düşmüyor**; API 200 döndüğü için sorun backend'de sanılıyor. Bu session'da tam
  olarak bu oldu (Python heredoc'unda `
` kaçışı kaybolup regex'i bozdu).
- **HTML içine JS yazarken Python heredoc + `str.replace` kullanma** — kaçış
  karakterleri sessizce bozuluyor. Edit tool birebir yazar.
- Browser panelinin `screenshot`'ı bu projede sık sık **bayat kare** döndürüyor;
  doğrulamayı `get_page_text` veya DOM sorgusuyla yap.

---

## 2026-07-21 — Gerçek ilanlar akıyor (D-020) + paylaşılan sözlük

**Bu session'da yapılanlar:**
- **D-020**: izinli ATS API'leri (Lever/Greenhouse/Recruitee) açıldı, kanıtla.
  **D-021**: ayırt edici olmayan şartlar tek başına bant üretemez. ✔
- `lexicon.py` (82 terim) — ilan ve CV **aynı** sözlüğe bağlandı.
- 52 gerçek Türkiye ilanı akıyor. **70 test geçiyor.**
- Detay: [PROGRESS.md](PROGRESS.md) → "Gerçek ilanlar: izinli ATS API'leri".

**Yarım kalanlar:**
- **Careerjet/Jooble adapter'ı yazılmadı** (OPEN-24) — publisher kaydını kullanıcı
  yapacak. ATS kapsamı tech ağırlıklı; mavi yaka bunu bekliyor.
- Kalıcılık yok (bellekte), CI yok, Next.js'e taşınmadı, Docker Compose yok.
- Sözlük elle yazıldı, serbest metni anlamıyor (OPEN-23 kısmen azaldı).
- İlan başına ortalama ~2.8 şart çıkarılıyor — zayıf. 2 ilanda hiç şart yok.

**Bir sonraki session'ın ilk adımı:**
- Kullanıcı onayı bekleniyor. Öncelik sırası ona ait: Careerjet entegrasyonu
  (kapsam) mı, kalıcılık (PostgreSQL) mi, extraction kalitesi mi.

**Bu session'da alınan kararlar:**
- D-020, D-021 — ikisi de DECISIONS.md'de ✔
- Pazar filtresi (Türkiye) **core'a gömülmedi**, `run_live_ingest` parametresi —
  D-009 gereği pazara özgü her şey politika katmanında.

**Yeni open question'lar:**
- **OPEN-24** — Careerjet/Jooble publisher kaydı yapılacak mı? Mavi yaka kapsamı
  buna bağlı.

**Dikkat edilmesi gerekenler / tuzaklar:**
- **LinkedIn ve Indeed'e dokunma.** LinkedIn'in okuma API'si yok, robots.txt
  `Disallow: /`. D-020 gate'i açtı ama onları kapsamıyor; `test_rejected_sources_
  stay_rejected` bunu denetliyor.
- **`allowed` yazarken `permission_evidence` doldur.** Kanıtsız izin iddiası
  `test_allowed_sources_must_carry_evidence` ile düşer.
- **Testlerde canlı ingest çağırma.** `STORE.load(live=False)` kullan; aksi halde
  her test ağa çıkar ve `Crawl-delay: 1` yüzünden dakikalarca sürer.
- **İlan ve CV aynı sözlüğü kullanmak zorunda.** Ayrı liste tutmak tam olarak bu
  session'da düzeltilen hatanın kendisidir.
- **Lever'da `descriptionPlain` yeterli değil** — çoğu ilanda sadece şirket
  tanıtımıdır ve firmanın bütün ilanlarında aynıdır. `lists` kullan.
- **Yeni pano eklerken `registry.BOARDS`'a elle yaz.** Otomatik keşif yok; kaynak
  listesinin sessizce büyümemesi kasıtlı.

---

## 2026-07-21 — Uygulama ayağa kalktı (API + arayüz)

**Bu session'da yapılanlar:**
- `services/api` (FastAPI) + `web/` (arayüz) kuruldu; uygulama çalışıyor.
- CV upload akışı, profil editörü, belge doğrulama, kaynak şeffaflık sayfası.
- **65 test geçiyor** (core 17, ingest 27, API 21).
- **OPEN-23** açıldı (ontoloji eksikliği). Detay: [PROGRESS.md](PROGRESS.md).

**Çalıştırma:**
```
python -m pip install fastapi "uvicorn[standard]" python-multipart pypdf
set PYTHONPATH=services/api/src;services/core/src;services/ingest/src
python -m uvicorn isuygun_api.main:app --port 8137
```
Sonra http://localhost:8137 — API dokümanı `/docs`, şema `/openapi.json`.

**Yarım kalanlar (dosya/konum ile):**
- **Kalıcılık yok** — [store.py](services/api/src/isuygun_api/store.py) bellekte
  çalışıyor. Sunucu kapanınca profil gidiyor. `db/001_init.sql` yazılmadı.
- **Next.js'e taşınmadı** — [web/index.html](web/index.html) statik; OpenAPI tipleri
  hazır olduğu için taşıma mekanik.
- **CI yok**, lint yapılandırması yok, Docker Compose yok.
- Belge doğrulama **simüle** (`store.verify_fact`); gerçek akış yazılmadı.
- Fixture korpusu 8 ilan / 5 meslek — dar.

**Bir sonraki session'ın ilk adımı:**
- Kullanıcı onayı bekleniyor. Onaylanırsa: `db/001_init.sql` + store'un PostgreSQL'e
  taşınması (arayüz değişmez, `Store` sınıfı tek değişecek yer).

**Bu session'da alınan kararlar / yeni assumption'lar:**
- Arayüz **şimdilik statik HTML**, Next.js sonra — kullanıcının bugün test
  edebilmesi için. ADR-001'i değiştirmez, sırayı değiştirir.
- Feed'de "değerlendirilemedi" ilanlar **ayrı bölümde**, bant sırasına sokulmadan —
  OPEN-22'nin geçici çözümü, kalıcı karar değil.

**Yeni open question'lar:**
- **OPEN-23** — profil alanı ↔ ilan şartı eşlemesi için ontoloji (ESCO benzeri) ne
  zaman ve nasıl kurulacak? MVP'de katalog korpustan türetiliyor, serbest metin
  eşlemesi yok.

**Dikkat edilmesi gerekenler / tuzaklar:**
- **`--reload` ile çalıştırma.** Uvicorn her dosya değişiminde yeniden başlıyor ve
  bellekteki profil siliniyor. [launch.json](.claude/launch.json) bu yüzden
  `--reload` içermiyor.
- **CV eşleşmesinde substring kullanma.** Kelime sınırı olmadan "geçerli" içindeki
  "gece" eşleşiyor. `cv._find()` kullan.
- **Genel kelimeler kanıt değildir.** "belgesi", "ehliyet", "deneyimi" gibi terimler
  `_TOO_GENERIC` süzgecinde; kaldırılırsa şoföre hemşire lisansı önerilir.
- **Türkçe soldan sağa yazılır.** Arayüzde `text-align:right` kullanma.
- API katmanına **iş kuralı yazma**. Kural core'da; API yalnızca taşır.

---

## 2026-07-21 — Stack kararı + çalışan çekirdek (core + ingest)

**Bu session'da yapılanlar:**
- **D-001 kapandı** → [ADR-001](docs/adr/ADR-001-technology-stack.md). T-012 Done,
  OPEN-17 kapandı.
- **D-018** (M1 gate kısmi revizyon) ve **D-019** (değerlendirilemeyen ilana bant
  üretilmez) DECISIONS.md'ye işlendi. ✔
- `services/core` (domain + matching + explanation) ve `services/ingest`
  (registry + pipeline) yazıldı; **44 test geçiyor**.
- Detay: [PROGRESS.md](PROGRESS.md) → 2026-07-21 "Stack kararı + çalışan çekirdek".

**Yarım kalanlar (dosya/konum ile):**
- **Kalıcılık yok.** `db/001_init.sql` yazılmadı; her şey bellekte çalışıyor.
- **API katmanı yok.** `services/api` (FastAPI) ve OpenAPI → TS tip üretimi yok.
- **Web arayüzü yok.** [prototype/index.html](prototype/index.html) hâlâ statik mockup;
  gerçek core'a bağlı değil.
- **CI yok.** Testler yalnızca elle koşuyor; lint yapılandırması yok.
- Fixture korpusu 8 ilan — meslek çeşitliliği dar (driver, warehouse, nurse, account,
  sales). D-008 cluster'larını tam kapsamıyor.

**Bir sonraki session'ın ilk adımı:**
- Kullanıcı onayı bekleniyor. Onaylanırsa sıra: `db/001_init.sql` (DATA_MODEL.md'yi
  yansıtan şema) → `services/api` (FastAPI, feed + ilan detayı) → OpenAPI'den TS tipi
  üretimi → Next.js arayüzü.

**Bu session'da alınan kararlar / yeni assumption'lar:**
- D-001 (stack), D-018 (gate revizyonu), D-019 (bant üretilmeyen durum) — üçü de
  DECISIONS.md'ye işlendi ✔
- `CONTENT_SIMILARITY_THRESHOLD = 0.75` ve `KIND_WEIGHT` **kalibrasyon hedefidir**,
  evrensel doğru değil. Gerçek korpusla (T-021) ölçülmeden savunulamaz.

**Yeni open question'lar:**
- **OPEN-22** — "Değerlendirilemedi" durumundaki ilanlar feed'de nasıl sıralanır ve
  gösterilir? D-019 bu dördüncü durumu yarattı; bant üzerinden sıralanamıyor.

**Dikkat edilmesi gerekenler / tuzaklar:**
- **`registry.assert_fetchable()` bir engel değil, mimarinin parçasıdır.** Gerçek
  kaynağa bağlanmak için bu fonksiyonu gevşetmek D-002 ihlalidir. Kayıtlı hiçbir
  gerçek kaynak `allowed` değil ve bu durum `test_no_real_source_is_allowed` ile
  denetleniyor.
- **Türkçe metin normalizasyonunda `unicodedata.normalize("NFKD", ...)` KULLANMA.**
  Türkçe harfleri parçalayıp kelime sınırını bozuyor; bu session'da tam olarak bu bug
  duplicate anahtarını sessizce çalışmaz hale getirmişti. `pipeline.fold()` kullan.
- Fixture'lar sentetiktir ve `example.invalid` alan adını kullanır. Gerçek ilan gibi
  sunulmamalı, gerçek URL'e çevrilmemeli.
- `services/core` ve `services/ingest` editable install edilmedi; testler
  `pyproject.toml` içindeki `pythonpath` ayarıyla çalışıyor. Elle koşarken
  `PYTHONPATH="services/core/src;services/ingest/src"` gerekiyor (Windows ayracı `;`).

---

## 2026-07-21 — T-022A interview hazırlığı + OPEN-19 izin taslakları

**Bu session'da yapılanlar:**
- T-003 kabul edildi; `fb3bf17` final baseline olarak CONTEXT'e kaydedildi.
- T-022 → **T-022A (Done)** ve **T-022B (Pending Fieldwork)** olarak ayrıldı.
- Saha materyalleri + response CSV + OPEN-19 izin taslakları hazırlandı.
- Detay: [PROGRESS.md](PROGRESS.md) → 2026-07-21 T-022A girdisi.

**Yarım kalanlar (dosya/konum ile):**
- **T-022B saha çalışması** — bu bir eksiklik değil, tasarım gereği kullanıcıya ait iş.

**🔴 KULLANICININ GERÇEK HAYATTA YAPMASI GEREKENLER (bu olmadan ilerlenemez):**
1. **Görüşmeleri yürütmek.** 12-18 katılımcı, cluster başına en az 4
   (Logistics & Operations / Office & Commercial / Healthcare).
   Script: [USER_INTERVIEW_VALIDATION_PLAN.md](docs/research/USER_INTERVIEW_VALIDATION_PLAN.md) §9.
   Görüşme başına 25-35 dk. **Bölüm A ve B'de ürün anlatılmaz** — bu kural bozulursa
   o görüşmenin kanıt değeri düşer.
2. **Cevapları template'e girmek.**
   [USER_INTERVIEW_RESPONSE_TEMPLATE.csv](docs/research/USER_INTERVIEW_RESPONSE_TEMPLATE.csv)
   — her satır bir görüşme. İzinli değerler: plan §19.1 kod defteri.
   **Gerçek isim/telefon/e-posta yazılmaz**; `P-01` gibi takma kimlik kullanılır.
3. **Her görüşmeden sonra 10 dk içinde** plan §20 özetini doldurmak (hafıza tazeyken).
4. **İzin taslakları için karar vermek:** gönderilecek mi, hangi kimlikle (PQ-1)?
   Gönderilecekse **önce iletişim kanalını doğrulamak** — taslaklardaki adresler
   bilinçli olarak `Unknown` bırakıldı, uydurulmadı.

**Bir sonraki session'ın ilk adımı:**
- CSV'de **en az 12 satır** (cluster başına ≥4) varsa: sentez — plan §21 şablonu,
  §19 kodlama kuralı, §22 Go/Revise/Stop çerçevesi. T-022B ancak o zaman Done olur.
- CSV boş veya eksikse: **sentez yapılmaz**, T-022B `Pending Fieldwork` kalır.
- İzin yanıtı geldiyse: Source Registry §5 güncellemesi —
  [SOURCE_PERMISSION_REQUESTS_TR.md](docs/research/SOURCE_PERMISSION_REQUESTS_TR.md) §6
  tablosuna göre.

**Bu session'da alınan kararlar / yeni assumption'lar:**
- Yeni karar (D-) **yok** — T-022A hazırlık task'ıdır, karar üretmez.
- Yeni assumption yok; test edilecek olanlar zaten A-2, A-4, A-10 (+A-9/A-13 ön sinyal).

**Yeni open question'lar:**
- OPEN-21 (teşvik / ses kaydı / kayıt saklama süresi) → CONTEXT index'ine eklendi ✔
- Plan §25'te TQ-1…TQ-6, izin dosyası §7'de PQ-1…PQ-4 (dosya-içi açık sorular).

**Dikkat edilmesi gerekenler / tuzaklar:**
- **T-022B hiçbir koşulda hayali cevapla kapatılmaz.** Claude görüşme yapmadı ve
  yapmayacak; sentez yalnızca kullanıcının girdiği gerçek veriyle üretilir.
- Plan §23'teki calibration target'lar **eşik değil**; bir hedefin kıl payı kaçırılması
  otomatik "Stop" değildir (METRICS §5 hedef revizyon kuralı).
- **T-021 başlatılmadı** ve kullanıcı onayı olmadan başlatılmayacak.
- **T-003 final** (`fb3bf17`): üzerinde yeni audit/enum/cross-reference kontrolü veya ek
  araştırma yapılmaz.
- İzin taslakları **gönderilmedi**; hiçbir kaynağa erişim başlatılmadı, Registry'de
  `allowed` kayıt yok.

## 2026-07-21 — T-003 Türkiye source landscape araştırması

**Bu session'da yapılanlar:**
- T-003 tamamlandı: 15 aday kaynak birincil kanıtla incelendi, `docs/research/`
  altında kanıt dosyası oluşturuldu, Source Registry §5'e aday kayıtları eklendi.
- Tavsiye **CONDITIONAL GO**; Wave 1/Wave 2/fallback/rejected ayrımı yapıldı.
- Detay: [PROGRESS.md](PROGRESS.md) → 2026-07-21 T-003 girdisi.

**Yarım kalanlar (dosya/konum ile):**
- Yok. T-003 kapandı. Ancak **nicel hacim ölçümü bilinçli olarak T-021'e devredildi**
  (TASKS.md T-003 sonuç notu + T-021 acceptance).

**Bir sonraki session'ın ilk adımı:**
- [TASKS.md](TASKS.md) → **T-021** (Source Coverage Validation). Örneklem planı hazır:
  [TURKEY_SOURCE_LANDSCAPE.md](docs/research/TURKEY_SOURCE_LANDSCAPE.md) §9.
  T-022 (user interview) paralel yürütülebilir ve T-021'in bağımsız örneklem derlemesine
  girdi verir ("son başvurduğun ilanı nereden buldun" sorusu).

**Bu session'da alınan kararlar / yeni assumption'lar:**
- Yeni karar (D-) **yok** — T-003 bir araştırma task'ıdır, karar üretmez; öneri sunar.
- Yeni assumption'lar TR-A1…TR-A5 araştırma dosyası §10'da işaretlendi ✔

**Yeni open question'lar:**
- OPEN-18 (isinolsun §4.12 kapsamı), OPEN-19 (yazılı izin talebi — **kullanıcı kararı**),
  OPEN-20 (healthcare cluster zayıflığı) → [CONTEXT.md](CONTEXT.md) index'ine eklendi ✔
- OPEN-09 `pre-build` → **M1-blocker**'a yükseltildi (bütün adaylar `conditional` çıktığı
  için artık crawl'ın önündeki tek kapı).

**Dikkat edilmesi gerekenler / tuzaklar:**
- **Hiçbir kaynak için crawl başlatılmamalıdır.** Registry'deki bütün kayıtlar
  `candidate`/`under_review`; `allowed` yok. Bu, D-002 ve SCRAPING_SYSTEM §4 gri alan
  kuralının doğrudan sonucudur.
- Araştırmadaki policy değerlendirmeleri **hukuki görüş değildir**; hepsi T-008 girdisi.
- `Unknown` işaretli alanlar (structured data varlığı, salary alanı, gerçek hacimler,
  ilan.gov.tr ve Kariyer Kapısı erişimi) **tahminle doldurulmamalıdır**.
- İŞKUR'un iki host'u (esube / kurumsal) **farklı policy taşıyor** ve registry'de ayrı
  kayıtlar — birleştirilmemeli.

## 2026-07-21 — Audit sonrası hedefli documentation revision

**Bu session'da yapılanlar:**
- 12 reviewer'lı documentation audit (134 bulgu, adversarial doğrulamalı) ve raporu.
- Kullanıcının onayladığı K-1…K-10 kararlarının D-008…D-017 olarak kayda geçirilmesi.
- İki CRITICAL bulgunun ve doğrulanmış HIGH boşlukların ilgili dokümanlara işlenmesi.
- Süreç düzeltmeleri (kural dosyalarının tekilleştirilmesi, Open Question Index, TASKS
  semantiği, ADR tetiği, CHANGELOG tetiği, GLOSSARY, traceability).
- TASKS.md revizyonu: 11 yeni task, T-017 dependency düzeltmesi.
- git init + snapshot commit + revision commit.
- Detay: [PROGRESS.md](PROGRESS.md) → 2026-07-21 girdisi.

**Yarım kalanlar (dosya/konum ile):**
- Yok; revizyon bütün olarak tamamlandı. Sıradaki iş task yürütmesidir, doküman değil.

**Bir sonraki session'ın ilk adımı:**
- [TASKS.md](TASKS.md) → T-003 (Türkiye source landscape) veya T-021/T-022 (validation).
  Bu ikisi paralel yürüyebilir; T-003 çıktısı T-021'i besler.

**Bu session'da alınan kararlar / yeni assumption'lar:**
- D-008…D-017 kayıt altına alındı ✔; D-003/D-004/D-006/D-007 statüleri netleştirildi ✔
- Yeni assumption'lar A-9…A-13 (talep tarafı) PRD'ye eklendi ✔; A-1 kapandı (D-009)

**Yeni open question'lar:**
- Yeni soru üretilmedi; mevcut sorular [CONTEXT.md](CONTEXT.md) → Open Question Index'te
  OPEN-01…OPEN-17 olarak envanterlendi (daha önce dağınıktı).

**Dikkat edilmesi gerekenler / tuzaklar:**
- **M1 validation gate'i kapanmadan (D-010) implementation task'larına başlanmaz.**
- Türkiye kararı (D-009) core architecture varsayımı yapılmamalı; TR'ye özgü her şey
  extension/policy katmanında kalmalı.
- Retention/SLA değerleri hâlâ **öneri** — hiçbir dokümanda kesin referans verilmemeli;
  T-008'de karara çevrilecek.
- İki CRITICAL'ın regression koruması TEST_STRATEGY §4'teki iki teste bağlı; matching
  veya profil şeması değişirken bu testler korunmalı.

## 2026-07-20 — Faz 0 documentation setinin oluşturulması

**Bu session'da yapılanlar:**
- Tüm documentation yapısı sıfırdan oluşturuldu (detay: [PROGRESS.md](PROGRESS.md)).

**Yarım kalanlar (dosya/konum ile):**
- Yok; documentation seti bütün olarak tamamlandı, kullanıcı review'u bekliyor.

**Bir sonraki session'ın ilk adımı:**
- [TASKS.md](TASKS.md) → T-001 (kullanıcı ile open question'ların üzerinden geçilmesi).

**Bu session'da alınan kararlar / yeni assumption'lar:**
- D-001…D-007 kayıt altına alındı ✔ ([DECISIONS.md](DECISIONS.md))
- Product assumption'ları A-1…A-8 olarak işaretlendi ✔ ([PRD.md](docs/product/PRD.md))

**Yeni open question'lar:**
- [CONTEXT.md](CONTEXT.md) → Açık Konular listesine bakınız.

**Dikkat edilmesi gerekenler / tuzaklar:**
- Stack seçilmeden implementation task'larına (T-013 sonrası) başlanmamalı.
- Dokümanlar arasında bilgi tekrarı bilinçli olarak önlendi; bir bölümü güncellerken
  link verilen sahibi dosyayı güncelleyin, kopya oluşturmayın.
