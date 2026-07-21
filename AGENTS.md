# AGENTS.md — Bütün Coding Agent'lar İçin Ortak Kurallar

> **Purpose:** Bu dosya, projede çalışan **her** coding agent'ın (Claude, Copilot, Cursor,
> diğerleri) uyacağı kuralların **tek normatif kaynağıdır**: yasaklar, çalışma sırası,
> çakışma otoritesi ve dosya hijyeni yalnızca burada tanımlanır ve başka dosyada tekrar
> edilmez. [CLAUDE.md](CLAUDE.md) yalnızca Claude'a özgü session adımlarını içerir ve bu
> dosyaya referans verir; çelişki halinde **bu dosya kazanır**.

## Temel İlkeler

1. **Önce oku, sonra yaz.** Session'a [CONTEXT.md](CONTEXT.md) ve
   [SESSION_HANDOFF.md](SESSION_HANDOFF.md) okuyarak başla. Bir dosyayı değiştirmeden
   önce mevcut içeriğini oku.
2. **Tek doğruluk kaynağı (single source of truth).** Her bilginin sahibi olan tek bir
   doküman vardır (bkz. [README.md](README.md) → Documentation Haritası). Bilgiyi
   kopyalama, link ver.
3. **Terminology tutarlılığı.** [GLOSSARY.md](docs/product/GLOSSARY.md) dışında tanım
   uydurma. Glossary'deki terimleri bütün dokümanlarda ve kodda aynı şekilde kullan
   (ör. "Job Posting", "Career Profile", "Source Adapter").
4. **Assumption ≠ Decision.** Varsayımları açıkça "Assumption" olarak işaretle.
   Kararlar yalnızca [DECISIONS.md](DECISIONS.md) + ADR ile "confirmed" olur.
5. **İzlenebilirlik.** Yaptığın işi [PROGRESS.md](PROGRESS.md) dosyasına işle, task
   status'unu [TASKS.md](TASKS.md) içinde güncelle ve proje durumu değiştiyse
   [CONTEXT.md](CONTEXT.md)'yi tazele. [CHANGELOG.md](CHANGELOG.md) **yalnızca
   milestone/release kapanışında** güncellenir — her session'da değil.
6. **Dosya hijyeni.** Var olan dosyayı sebepsiz silme veya baştan yazma; değiştirmeden
   önce oku ve targeted edit yap. Geçici dosyalar repository'ye değil scratchpad'e yazılır.
   Yeni documentation dosyası eklemeyi minimumda tut; eklenen her dosyanın gerekçesi
   yazılır. Bulunan bug/tutarsızlık [BUGS.md](BUGS.md) dosyasına kaydedilir.

## Yasaklar (bütün agent'lar için geçerli)

- Login wall, CAPTCHA, bot-detection veya paywall **bypass** eden herhangi bir mekanizma
  tasarlamak veya implement etmek.
- robots kurallarını, source Terms of Service'i veya rate limit'leri ihlal eden
  scraping davranışı eklemek.
- Matching score hesabına sensitive attribute (age, gender, photo, ethnicity, religion,
  marital status vb.) dahil etmek — tam liste:
  [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md) → Fairness Constraints.
- Kullanıcı verisini [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md)
  içinde tanımlanan lifecycle dışında saklamak veya üçüncü tarafa aktarmak.
- Var olan dokümanları sebepsiz silmek veya baştan yazmak.
- Legal değerlendirmeyi kesin hukuki görüş gibi yazmak; hukuki doğrulama bekleyen bir
  konuyu (T-008) confirmed fact olarak sunmak.
- Match Score'u işe alınma olasılığı, garanti veya objektif gerçek gibi sunmak (D-005).

**Kullanıcı onayı olmadan verilemeyecek kararlar:** technology stack seçimi; scope
değişikliği (MVP'ye feature ekleme/çıkarma, occupation veya source kapsamının
değiştirilmesi); yeni bir external source'a scraping başlatılması; privacy, compliance
veya fairness politikasında değişiklik; onaylanmış bir kararın (DECISIONS.md → Confirmed)
revize edilmesi.

## Çalışma Sırası

1. Task'ı [TASKS.md](TASKS.md) üzerinden al; dependency'leri tamamlanmamış task'a başlama.
2. Task'ı `In Progress` olarak işaretle.
3. İşi yap; [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) kriterlerini karşıla.
4. Status'u güncelle, PROGRESS ve HANDOFF kayıtlarını yaz.

## Çakışma Durumu — Otorite Tablosu

İki doküman çelişiyorsa aşağıdaki sahibi esas al, çelişkiyi düzelt ve PROGRESS.md'ye
not düş. Emin olamadığın durumda değişikliği yapma; `❓ OPEN` olarak işaretle,
[CONTEXT.md](CONTEXT.md) → Open Question Index'e ekle ve kullanıcıya sor.

| Alan | Otorite |
|---|---|
| Terminoloji | [GLOSSARY.md](docs/product/GLOSSARY.md) |
| Kararlar ve statüleri | [DECISIONS.md](DECISIONS.md) |
| Scope (MVP/V1/Future, feature listesi) | [PRD.md](docs/product/PRD.md) |
| Requirement ifadesi ve MoSCoW seviyesi | [REQUIREMENTS.md](docs/product/REQUIREMENTS.md) |
| Bileşen sorumlulukları, sınırlar, data flow | [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) |
| Entity alanları ve şemalar | [DATA_MODEL.md](docs/architecture/DATA_MODEL.md) |
| Matching davranışı, faktörler, fairness | [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md) |
| Ingestion davranışı, source policy | [SCRAPING_SYSTEM.md](docs/architecture/SCRAPING_SYSTEM.md) |
| Metrik tanımı ve hedefi | [METRICS.md](docs/product/METRICS.md) |
| Privacy, retention, security sınırları | [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md) |
| ADR yazma tetiği ve süreci | [docs/adr/README.md](docs/adr/README.md) |

Tablo dışı bir çelişkide: ilgili dosyaların `Purpose` satırları sahipliği belirler;
yine de belirsizse kullanıcıya sor.

## Türkiye Kuralı (D-009)

Launch pazarı Türkiye'dir, **ama core architecture market-neutral kalır.** TR'ye özgü
job source, legal requirement, license, denklik, dil, lokasyon yapısı, public sector
davranışı ve retention kararları country-specific extension/policy katmanında modellenir.
Bir TR ayrıntısını core model varsayımı haline getirmek architecture review bulgusudur.
