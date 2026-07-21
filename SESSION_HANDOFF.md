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
