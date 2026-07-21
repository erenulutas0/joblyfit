# CONTEXT.md — Projenin Güncel Durumu

> **Purpose:** Her session başında okunacak tek dosya. Projenin şu anki durumunu, aktif
> hedefi ve kritik kısıtları özetler. Tarihçe için [PROGRESS.md](PROGRESS.md), detay için
> ilgili dokümanlara bakılır. **Bu dosya her anlamlı değişiklikten sonra güncellenir.**

_Last updated: 2026-07-20_

## Ne İnşa Ediyoruz?

Her meslek dalına hitap eden AI-powered job discovery and matching platform:
CV/profil → normalize edilmiş Career Profile; public source'lardan toplanan ilanlar →
normalize edilmiş Job Posting'ler; ikisi arasında hybrid + explainable matching.
Detay: [PRODUCT.md](docs/product/PRODUCT.md), [PRD.md](docs/product/PRD.md).

## Şu Anki Faz

**Faz 0 — Product Design & Architecture Documentation.**
Implementation code yok, technology stack seçilmedi (bilinçli karar: D-001,
[DECISIONS.md](DECISIONS.md)). Bütün documentation seti 2026-07-20 tarihinde oluşturuldu.

## Aktif Hedef

Documentation setinin kullanıcı tarafından review edilmesi ve open question'ların
kapatılması. Sonraki adımlar: [TASKS.md](TASKS.md) → T-001'den itibaren.

## Kritik Kısıtlar (özet)

- **Compliance-first ingestion:** Login wall / CAPTCHA / bot-detection bypass yok;
  robots ve ToS'a saygı. → [SCRAPING_SYSTEM.md](docs/architecture/SCRAPING_SYSTEM.md)
- **Fairness:** Sensitive attribute'lar matching score'a giremez.
  → [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md)
- **Explainability:** Her recommendation gerekçeli olmak zorunda; Match Score kullanıcıya
  kesin gerçek/garanti olarak sunulmaz.
- **Meslek genişliği:** Sistem yalnızca white-collar için değil; blue-collar, healthcare,
  education, retail, logistics, hospitality, manufacturing, finance, creative, public
  sector ve freelance meslekler de birinci sınıf kullanıcı.
- **Regulated profession güvenliği:** License eksikse kullanıcı açıkça bilgilendirilir,
  yanlış yönlendirme yapılmaz.

## Açık Konular (en kritik 5)

Tam liste ilgili dokümanlarda `❓ OPEN:` olarak işaretli; risk boyutu için
[RISK_REGISTER.md](docs/security/RISK_REGISTER.md).

1. ❓ Hedef launch pazarı/ülkesi hangisi? (taxonomy, dil, compliance önceliğini belirler)
2. ❓ MVP'de hangi 3-5 job source ile başlanacak?
3. ❓ Business model (kullanıcıya ücretsiz mi, employer-side gelir mi?)
4. ❓ Occupation Taxonomy için ESCO/O*NET'ten hangisi baz alınacak?
5. ❓ Technology stack kararının (D-001) hedef tarihi ne?
