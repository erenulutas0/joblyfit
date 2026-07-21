# PROGRESS.md — İlerleme Kaydı

> **Purpose:** Mevcut durumun ve son tamamlanan işlerin kaydı; kronolojik, en yeni üstte.
> Her session sonunda entry eklenir. Güncel durum özeti için [CONTEXT.md](CONTEXT.md);
> task status'ları için [TASKS.md](TASKS.md); milestone/release kayıtları için
> [CHANGELOG.md](CHANGELOG.md).
>
> Faz kapanışında eski entry'ler `archive/PROGRESS-<faz>.md` altına taşınır; aktif dosyada
> güncel faz kalır.

## 2026-07-21 — Audit ve hedefli documentation revision

**Audit (12 bağımsız reviewer, 35 dosya):** 134 bulgu üretildi ve yüksek-severity
bulgular adversarial doğrulamadan geçirildi. Sonuç: 0 BLOCKER, 2 CRITICAL, 19 HIGH,
96 MEDIUM, 17 LOW. Hiçbir bulgu tümüyle çürütülmedi; 33'ünün şiddeti doğrulama sonrası
düşürüldü. Genel değerlendirme: set "review-ready" ama "build-ready" değildi.

**Kullanıcı kararları (K-1…K-10 → D-008…D-017):** MVP kapsamı üç cluster / ~6 first-class
occupation'a daraltıldı; launch pazarı Türkiye seçildi (core market-neutral kalmak
şartıyla); implementation öncesi validation gate zorunlu kılındı; requirement
değerlendirmesi üç durumlu (met/unmet/unknown) yapıldı; gate-relevant alanlar için
doğrulama şartı getirildi; legal eligibility kavramı sensitive attribute'tan ayrıldı;
Manual Review Queue minimal moda alındı (~2 saat/hafta); public sector listing-only
tanımlandı; notification sabit haftalık e-posta digest'e sabitlendi; matching ~8 MVP
faktörü + ≤~%10 semantic reranking ile sınırlandı.

**Kapatılan iki CRITICAL:**
- *Missing information ≠ unmet requirement:* üç durumlu değerlendirme veri modeline,
  invariant'lara, matching pipeline'ına, flow'lara ve requirement'lara işlendi.
- *Unverified license gate'i geçebiliyordu:* `verification_state` modeli, gate-relevant
  alan sınıfı ve invariant #8 genişletmesiyle kapatıldı.

**Kapatılan uygulanabilirlik boşlukları:** requirements şemasına min_years/level/
jurisdiction/verification/evidence alanları; skills ve languages için ortak proficiency
ölçeği; shift_info structured şeması; Employer entity + Employer Identity Resolver;
Feed & Search Service'in arama sahipliği; freshness'ın final ranking'deki yeri;
extraction'ın pipeline'daki tek konumu (iki fazlı yazma); MatchResult invalidation
tetikleyicileri; cold start davranışı; yield/coverage anomali izlemesi; access-change
(login wall) tespiti; source emergency takedown; MatchResult/analytics/backup/MRQ/
iletişim bilgisi için privacy envanteri.

**Süreç düzeltmeleri:** AGENTS.md tek normatif kural seti oldu ve otorite tablosu
kazandı; CLAUDE.md Claude'a özgü minimuma indirildi; CONTEXT.md'ye 17 kalemlik Open
Question Index eklendi ve güncelleme tetiği checklist'e bağlandı; TASKS.md status
semantiği ve arşiv kuralı tanımlandı; ADR tetiğinin tek sahibi docs/adr/README.md oldu;
CHANGELOG milestone bazlıya çekildi; GLOSSARY'ye 16 eksik terim eklendi; PRD'ye
Feature→Requirement→Flow traceability matrisi ve MoSCoW↔scope kuralı eklendi.

**Task revizyonu:** 11 yeni task (T-021…T-031: yedi validation çalışması + golden set
üretimi + employer identity + privacy inventory + MVP faktör seti + public sector
davranışı); T-017'nin dependency'si düzeltildi — core loop artık tek source ile
doğrulanabiliyor, cross-source dedupe (T-015) ön şart değil.

**Version control:** Repository git altına alındı; revizyon öncesi durum ayrı bir
snapshot commit'te korundu.

**Bilinen açık:** Open Question Index'teki M1-blocker kalemler (özellikle retention/SLA
değerleri, taxonomy standardı, harici AI servis izni) T-008 ve T-004 ile kapanacak.

## 2026-07-20 — Faz 0: Documentation seti oluşturuldu

- Boş repository üzerinde tam documentation yapısı kuruldu (root + docs/product +
  docs/architecture + docs/security + docs/quality + docs/operations + docs/adr).
- Product vision, PRD (MVP/V1/Future scope), personas, flows, requirements, roadmap,
  metrics ve glossary yazıldı.
- System architecture, scraping/ingestion mimarisi, Source Registry, Matching Engine,
  Occupation Taxonomy, AI system, domain/data model ve API contract'ları tasarlandı.
- Privacy/security/compliance çerçevesi, risk register, test stratejisi, observability
  ve runbook oluşturuldu.
- İlk kararlar [DECISIONS.md](DECISIONS.md)'ye kaydedildi (D-001…D-007). *(Düzeltme
  2026-07-21: bu kayıtlar ADR değildir; docs/adr/ altında henüz ADR yoktur — bkz.
  [BUGS.md](BUGS.md) BUG-001.)*
- Initial task breakdown [TASKS.md](TASKS.md) içine eklendi (T-001…T-020).
- Bilinen eksik: hedef pazar, başlangıç source listesi ve business model kullanıcı
  onayı bekliyor (bkz. CONTEXT.md → Açık Konular).
