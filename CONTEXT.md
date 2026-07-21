# CONTEXT.md — Projenin Güncel Durumu

> **Purpose:** Her session başında okunacak tek dosya. Projenin şu anki durumunu, aktif
> hedefi, kritik kısıtları ve **bütün açık soruların indeksini** tutar. Tarihçe için
> [PROGRESS.md](PROGRESS.md), kararlar için [DECISIONS.md](DECISIONS.md), scope için
> [PRD.md](docs/product/PRD.md).
>
> **Güncelleme tetiği:** Her session sonunda ([CLAUDE.md](CLAUDE.md) → Session Sonunda
> adım 4; [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) → Bookkeeping). Proje durumu
> değiştiyse Şu Anki Faz / Aktif Hedef / Open Question Index güncellenir ve aşağıdaki
> tarih yenilenir.

_Last updated: 2026-07-21 (T-003 tamamlandı)_

## Ne İnşa Ediyoruz?

Her meslek dalına hitap eden AI-powered job discovery and matching platform:
CV/profil → normalize edilmiş Career Profile; public source'lardan toplanan ilanlar →
normalize edilmiş Job Posting; ikisi arasında hybrid + explainable matching.
Detay: [PRODUCT.md](docs/product/PRODUCT.md), [PRD.md](docs/product/PRD.md).

## Şu Anki Faz

**Faz 1 — Doğrulama & Hazırlık.** (Faz 0 documentation 2026-07-20'de tamamlandı;
2026-07-21'de 12 reviewer'lı audit yapıldı ve bulgular dokümanlara işlendi.)

Implementation code yok, technology stack seçilmedi (D-001). Build'e geçiş
[ROADMAP.md](docs/product/ROADMAP.md) → M1 validation gate'ine bağlıdır.

## Aktif Hedef

**M1 validation gate'ini kapatmak** (D-010): yedi validation çalışması (T-021…T-027)
ve mevcut Faz 1 task'ları tamamlanıp **go / revise / stop** kararı verilene kadar
implementation başlamaz.

**T-003 tamamlandı (2026-07-21).** Sonuç: 15 aday incelendi, tavsiye **CONDITIONAL GO** —
Wave 1 = isinolsun.com, Wave 2 = İŞKUR e-Şube + Kamu İlan (SBB). **Kritik bulgu: MVP'ye
aday hiçbir kaynak koşulsuz `allowed` değil**; crawl başlatılması yazılı izne (OPEN-19)
veya T-008'in `Conditional` rubriğine (OPEN-09) bağlı. Detay:
[TURKEY_SOURCE_LANDSCAPE.md](docs/research/TURKEY_SOURCE_LANDSCAPE.md).

Sıradaki iş: [TASKS.md](TASKS.md) → T-021 (coverage validation; planı hazır) ve T-022.

## Karara Bağlanmış Temeller (2026-07-21)

| Konu | Karar |
|---|---|
| MVP kapsamı | 3 cluster, ~6 first-class occupation, 2-3 source (D-008) |
| Launch pazarı | Türkiye — **core architecture market-neutral kalır** (D-009) |
| Validation | Implementation öncesi zorunlu, M1 go/revise/stop kapısı (D-010) |
| Requirement durumu | met / unmet / **unknown** üçlüsü (D-011) |
| Gate alanları | verified olmadan `met` sayılmaz (D-012) |
| Legal eligibility | sensitive attribute'tan ayrı; health matching'e girmez (D-013) |
| Manual Review Queue | minimal mod, ~2 saat/hafta kapasite (D-014) |
| Public sector | listing-only / guidance mode (D-015) |
| Notification | sabit haftalık e-posta digest + opt-out (D-016) |
| Matching | ~8 MVP faktörü; semantic ≤ ~%10 reranking (D-017) |

## Kritik Kısıtlar (özet — sahibi dokümanlar linklerde)

- **Compliance-first ingestion:** login wall / CAPTCHA / bot-detection bypass yok;
  robots ve ToS'a saygı (D-002 → [SCRAPING_SYSTEM.md](docs/architecture/SCRAPING_SYSTEM.md)).
- **Fairness:** sensitive attribute'lar matching'e giremez; listedeki alanlar hiç
  saklanmaz (D-006 → [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md)).
- **Explainability:** her recommendation gerekçeli; Match Score kesinlik veya işe alınma
  olasılığı olarak sunulmaz (D-005).
- **Meslek genişliği:** vision universal; MVP'de 6 occupation first-class, diğerleri
  generic matching + coverage limitation açıklaması (D-008).
- **Regulated dürüstlüğü:** license eksikse veya doğrulanmamışsa kullanıcı açıkça
  bilgilendirilir; "uygunsun" izlenimi verilmez (D-012, FR-408).
- **Türkiye ≠ core:** TR'ye özgü her şey extension/policy katmanında (D-009).

## Open Question Index

> Setteki **bütün** `❓ OPEN` kalemlerinin tek envanteri. Sahibi dosyada işaret kalır,
> envanter burada tutulur. Severity: **M1-blocker** (validation gate'i kapatmadan
> çözülmeli) · **pre-build** (implementation başlamadan) · **later** (V1 veya sonrası).
> Yeni bir `❓ OPEN` eklendiğinde bu tabloya da satır eklenir.

| ID | Soru | Severity | Sahip dosya | Bağlı task | Durum |
|---|---|---|---|---|---|
| OPEN-01 | Analitik veri toplama izin modeli (opt-in kapsamı) nedir? | M1-blocker | [METRICS.md](docs/product/METRICS.md) | T-008, T-011 | Open |
| OPEN-02 | Taxonomy çekirdeği ESCO mu O*NET mi? | M1-blocker | [OCCUPATION_TAXONOMY.md](docs/architecture/OCCUPATION_TAXONOMY.md) | T-004 | Open |
| OPEN-03 | Harici AI servisi kullanılacak mı; hangi veri sınıflarıyla? | M1-blocker | [AI_SYSTEM.md](docs/architecture/AI_SYSTEM.md) | T-009 (+T-008 doğrulaması) | Open |
| OPEN-04 | CV dosyasının retention süresi ve gerekçesi | M1-blocker | [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md) | T-008 | Open |
| OPEN-05 | Deletion SLA'sı ve geri alma penceresi | M1-blocker | [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md) | T-008 | Open |
| OPEN-06 | İlan içeriğinin gösterim sınırı (telif) ve `description_raw` retention'ı | M1-blocker | [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md) | T-008 | Open |
| OPEN-07 | Expired posting arşiv süresi | pre-build | [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md) | T-008 | Open |
| OPEN-08 | Log / backup / analytics retention süreleri | pre-build | [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md) | T-008 | Open |
| OPEN-09 | `Conditional` source'lar için karar rubriği | **M1-blocker (yükseldi)** | [SCRAPING_SYSTEM.md](docs/architecture/SCRAPING_SYSTEM.md) | T-008 | **Open — aciliyet arttı:** T-003 sonucunda MVP'ye aday **bütün** kaynaklar `conditional` çıktı; bu rubrik kapanmadan hiçbir crawl başlatılamaz |
| OPEN-18 | isinolsun üyelik sözleşmesi §4.12 (veri kopyalama yasağı) üye olmayan otomatik erişime uygulanır mı? | M1-blocker | [TURKEY_SOURCE_LANDSCAPE.md](docs/research/TURKEY_SOURCE_LANDSCAPE.md) | T-008 | Open — Wave 1'in başlayabilmesi buna bağlı |
| OPEN-19 | Kariyer.net grubuna ve İŞKUR'a **yazılı izin / resmi feed talebi** yapılacak mı? | M1-blocker | [TURKEY_SOURCE_LANDSCAPE.md](docs/research/TURKEY_SOURCE_LANDSCAPE.md) | — | Open — **kullanıcı kararı**; SCRAPING_SYSTEM §4/5'in tercih ettiği yol |
| OPEN-20 | Healthcare cluster'ının compliant coverage zayıflığı D-008 cluster seçimini değiştirir mi? | pre-build | [PRD.md](docs/product/PRD.md) | T-021 | Open — **kullanıcı kararı**, T-021 ölçümünden sonra |
| OPEN-10 | Ayrımcı/hukuken belirsiz şart içeren ilanlar gizlensin mi, uyarıyla mı gösterilsin? | pre-build | [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md) | T-008 | Kısmen kapandı (D-013: uyarı + Manual Review; gizleme kararı hukuki görüşe bağlı) |
| OPEN-11 | Minimum kullanıcı yaşı ve reşit olmayan kullanıcı politikası | pre-build | [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md) | T-008 | Open |
| OPEN-12 | MVP-required test katmanları alt kümesi | pre-build | [TEST_STRATEGY.md](docs/quality/TEST_STRATEGY.md) | T-011 | Open |
| OPEN-13 | MVP-required observability/alert alt kümesi | pre-build | [OBSERVABILITY.md](docs/quality/OBSERVABILITY.md) | T-011 | Open |
| OPEN-14 | Hedef erişilebilirlik düzeyi (ör. WCAG seviyesi) | later | [REQUIREMENTS.md](docs/product/REQUIREMENTS.md) | T-007 | Open |
| OPEN-15 | Public sector sınav puanı/kadro mekaniği ne zaman modellenecek? | later | [PRD.md](docs/product/PRD.md) | — (V1 değerlendirmesi) | Ertelendi (D-015: MVP'de listing-only) |
| OPEN-16 | Business model / gelir yolu (A-5) | later | [PRD.md](docs/product/PRD.md) | — | Open |
| OPEN-17 | Technology stack (D-001) | pre-build | [DECISIONS.md](DECISIONS.md) | T-012 | Open — M1 sonrası |

**Kapanma kuralı:** Bir soru kapandığında sahibi dosyadaki `❓ OPEN` işareti cevabıyla
değiştirilir, karar gerektiriyorsa DECISIONS.md'ye kayıt düşülür ve buradaki satırın
durumu `Kapandı (D-0XX)` yapılır — satır silinmez.
