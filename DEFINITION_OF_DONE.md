# DEFINITION_OF_DONE.md

> **Purpose:** Bir task'ın "Done" sayılabilmesi için sağlanması gereken şartlar. Bu
> kriterler [TASKS.md](TASKS.md) içindeki her task'ın acceptance criteria'sına ek olarak
> uygulanır. Faz 0 (documentation) ve implementation fazları için ayrı bölümler vardır.

## Faz 0 — Documentation Task'ları İçin

Bir documentation task'ı şu şartların tümü sağlanınca Done'dır:

1. **Content:** Task'ın acceptance criteria'sındaki bütün maddeler karşılandı.
2. **Single ownership:** Eklenen bilgi başka bir dosyada tekrar edilmiyor; ilgili
   dosyalara link verildi.
3. **Terminology:** Kullanılan bütün terimler [GLOSSARY.md](docs/product/GLOSSARY.md)
   ile tutarlı; yeni terim gerekiyorsa glossary'ye eklendi.
4. **Assumption/Decision ayrımı:** Yeni varsayımlar "Assumption" olarak, kararlar
   [DECISIONS.md](DECISIONS.md)/ADR olarak işaretlendi.
5. **Open questions:** Cevaplanamayan konular `❓ OPEN-NN:` ile işaretlendi **ve**
   [CONTEXT.md](CONTEXT.md) → Open Question Index'e satır olarak eklendi (ID, soru,
   severity, sahip dosya, bağlı task, durum).
6. **Bookkeeping:** TASKS.md status'u, PROGRESS.md ve SESSION_HANDOFF.md güncellendi;
   **proje durumu değiştiyse CONTEXT.md** (Şu Anki Faz / Aktif Hedef / Open Question
   Index + `Last updated`) tazelendi; iş bir milestone kapatıyorsa CHANGELOG.md'ye kayıt
   düşüldü (CHANGELOG session bazlı değil, milestone bazlıdır).
7. **Versiyon kontrolü:** Değişiklikler commit'lendi (remote yok, push yok).

## Implementation Fazları İçin (stack seçildikten sonra geçerli)

Bir implementation task'ı şu şartların tümü sağlanınca Done'dır:

### Documentation
- Davranış değişikliği ilgili architecture/product dokümanına yansıtıldı.
- Public interface değişiklikleri [API_CONTRACTS.md](docs/architecture/API_CONTRACTS.md)
  ile tutarlı.

### Test
- [TEST_STRATEGY.md](docs/quality/TEST_STRATEGY.md) uyarınca: yeni davranış için test
  yazıldı, mevcut testler geçiyor.
- Matching değişikliklerinde golden-set regression testi çalıştırıldı
  (bkz. TEST_STRATEGY.md → Matching Quality Tests).
- Parser/adapter değişikliklerinde fixture-based contract testleri geçiyor.

### Security & Privacy
- [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md)
  sınırları ihlal edilmedi (data lifecycle, sensitive attribute yasağı, source policy).
- Yeni PII alanı eklendiyse **veri envanterine satır eklendi** ve deletion/export kapsamı
  ile test kapsamı buna göre güncellendi.
- **Bypass yasağı kontrolü (D-002):** değişiklik kimlik doğrulama taşıma, CAPTCHA çözme,
  bot-detection kaçınma veya paywall aşma amacı taşımıyor; erişim engeliyle karşılaşan
  kod yeniden deneme veya alternatif yol aramıyor, durup source'u `Suspended` yapıyor.
- **Gate koruması (D-012):** gate-relevant alanla ilgili değişiklik, `unverified` verinin
  hard requirement'ı `met` yapamayacağı kuralını korumuş.
- Secrets kod içine yazılmadı.

### Observability
- Yeni component/flow için [OBSERVABILITY.md](docs/quality/OBSERVABILITY.md) uyarınca
  log ve metric eklendi. **Yeni alert bir runbook girdisine bağlanmadan Done olmaz**
  (NFR-602 ile hizalama).
- Scraper değişikliklerinde Scraper Health Monitor metrikleri çalışıyor.
- Rollback yeteneği etkileyen değişikliklerde RB-5 ön şartları hâlâ sağlanıyor
  (eski versiyon çalıştırılabilir, yeniden hesaplama tetikleniyor).

### Acceptance
- Task'taki acceptance criteria'nın tamamı doğrulandı (nasıl doğrulandığı task notuna yazıldı).
- Review'dan geçti (insan veya ikinci agent).
- TASKS.md, PROGRESS.md, CHANGELOG.md güncellendi.
