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
5. **Open questions:** Cevaplanamayan konular `❓ OPEN:` ile görünür şekilde işaretlendi.
6. **Bookkeeping:** TASKS.md status'u, PROGRESS.md ve (anlamlıysa) CHANGELOG.md güncellendi.

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
- Yeni PII alanı eklendiyse data inventory güncellendi.
- Secrets kod içine yazılmadı.

### Observability
- Yeni component/flow için [OBSERVABILITY.md](docs/quality/OBSERVABILITY.md) uyarınca
  log ve metric eklendi; kritik hata yolu alert'e bağlandı.
- Scraper değişikliklerinde Scraper Health Monitor metrikleri çalışıyor.

### Acceptance
- Task'taki acceptance criteria'nın tamamı doğrulandı (nasıl doğrulandığı task notuna yazıldı).
- Review'dan geçti (insan veya ikinci agent).
- TASKS.md, PROGRESS.md, CHANGELOG.md güncellendi.
