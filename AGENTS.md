# AGENTS.md — Bütün Coding Agent'lar İçin Ortak Kurallar

> **Purpose:** Bu dosya, projede çalışan **her** coding agent'ın (Claude, Copilot, Cursor,
> diğerleri) uyacağı ortak kuralları tanımlar. Claude-spesifik ek kurallar
> [CLAUDE.md](CLAUDE.md) dosyasındadır.

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
5. **İzlenebilirlik.** Yaptığın her anlamlı değişikliği [PROGRESS.md](PROGRESS.md) ve
   [CHANGELOG.md](CHANGELOG.md) dosyalarına işle; task status'unu
   [TASKS.md](TASKS.md) içinde güncelle.

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
- Kullanıcı onayı olmadan technology stack seçmek veya scope değiştirmek.
- Var olan dokümanları sebepsiz silmek veya baştan yazmak.

## Çalışma Sırası

1. Task'ı [TASKS.md](TASKS.md) üzerinden al; dependency'leri tamamlanmamış task'a başlama.
2. Task'ı `In Progress` olarak işaretle.
3. İşi yap; [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) kriterlerini karşıla.
4. Status'u güncelle, PROGRESS ve HANDOFF kayıtlarını yaz.

## Çakışma Durumu

- İki doküman birbiriyle çelişiyorsa: GLOSSARY.md terminoloji için, DECISIONS.md kararlar
  için, PRD.md scope için otoritedir. Çelişkiyi düzelt ve PROGRESS.md'ye not düş.
- Emin olamadığın durumda değişikliği yapma; open question olarak işaretle ve kullanıcıya sor.
