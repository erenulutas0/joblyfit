# CLAUDE.md — Coding Agent Çalışma Kuralları

> **Purpose:** Bu dosya, Claude (ve bu dosyayı okuyan diğer coding agent'ların) bu proje
> üzerinde nasıl çalışacağını tanımlar. Bütün agent'lar için ortak kurallar
> [AGENTS.md](AGENTS.md) dosyasındadır; bu dosya onun üzerine proje-spesifik kuralları ekler.

## Proje Durumu

- Proje şu anda **documentation-only** aşamasındadır. Implementation code yoktur.
- Technology stack (language, framework, database, cloud provider) **henüz seçilmemiştir**
  ve seçilene kadar hiçbir doküman belirli bir teknolojiye bağımlı yazılmaz
  (bkz. [DECISIONS.md](DECISIONS.md) → D-001).

## Her Session Başında

1. [CONTEXT.md](CONTEXT.md) dosyasını oku — projenin güncel durumu buradadır.
2. [SESSION_HANDOFF.md](SESSION_HANDOFF.md) içindeki son handoff kaydını oku.
3. [TASKS.md](TASKS.md) içinden üzerinde çalışılacak task'ı belirle; task'ların
   dependency sırasına uy.

## Her Session Sonunda

1. [PROGRESS.md](PROGRESS.md) dosyasına yapılan işi ekle.
2. [SESSION_HANDOFF.md](SESSION_HANDOFF.md) şablonunu kullanarak yeni handoff kaydı yaz.
3. Tamamlanan task'ların status'unu [TASKS.md](TASKS.md) içinde güncelle.
4. Anlamlı değişiklikleri [CHANGELOG.md](CHANGELOG.md) dosyasına ekle.

## Çalışma Kuralları

### Documentation

- Yeni bilgi eklerken önce hangi dosyanın o bilginin **tek sahibi (single owner)**
  olduğunu belirle; aynı bilgiyi ikinci bir dosyada tekrar etme, link ver.
- Terminoloji için tek kaynak [GLOSSARY.md](docs/product/GLOSSARY.md) dosyasıdır.
  Yeni bir terim gerekiyorsa önce oraya ekle, sonra kullan.
- **Assumption** ile **confirmed decision** ayrımını koru: assumption'lar
  "Assumption" olarak işaretlenir; onaylanan kararlar [DECISIONS.md](DECISIONS.md)
  ve gerekiyorsa bir ADR ([docs/adr/](docs/adr/README.md)) ile kayda geçer.
- Open question'ları `❓ OPEN:` prefix'i ile işaretle; çözülen soruyu cevabıyla
  birlikte ilgili dokümana taşı.

### Kararlar

- Mimari veya product yönünü değiştiren her karar için [ADR_TEMPLATE.md](docs/adr/ADR_TEMPLATE.md)
  kullanarak ADR yaz ve [DECISIONS.md](DECISIONS.md) içine özet satırı ekle.
- Kullanıcı onayı olmadan şu kararları **verme**: technology stack seçimi, scope değişikliği
  (MVP'ye feature ekleme/çıkarma), yeni bir external source'a scraping başlatılması,
  privacy veya compliance politikasında değişiklik.

### Implementation Aşamasına Geçildiğinde

- Kod yazmaya başlamadan önce D-001 (stack kararı) kapatılmış olmalı.
- Her task [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) şartlarını sağlamadan
  "Done" işaretlenmez.
- Scraping ile ilgili her kod değişikliği [SCRAPING_SYSTEM.md](docs/architecture/SCRAPING_SYSTEM.md)
  içindeki compliance kurallarına ve [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md)
  sınırlarına uymak zorundadır. Login wall, CAPTCHA veya bot-detection bypass eden
  kod **hiçbir koşulda yazılmaz**.
- Matching ile ilgili değişikliklerde sensitive attribute yasağına
  ([MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md) → Fairness Constraints) uy.

### Dosya Hijyeni

- Var olan dosyaları sebepsiz silme veya overwrite etme; içeriği değiştirmeden önce oku.
- Geçici dosyaları repository içine değil scratchpad'e yaz.
- Bug bulursan [BUGS.md](BUGS.md) dosyasına kaydet; sessizce geçme.
