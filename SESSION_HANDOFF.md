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
