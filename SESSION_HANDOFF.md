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
