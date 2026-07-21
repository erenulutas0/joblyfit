# ADR-001 — Technology stack: Python veri katmanı + TypeScript arayüz

- **Status:** Accepted (kullanıcı onayı, 2026-07-21)
- **Date:** 2026-07-21
- **Related:** [DECISIONS.md](../../DECISIONS.md) → D-001 (kapanır), D-018 · [TASKS.md](../../TASKS.md) → T-012

## Context

D-001 uyarınca stack seçimi Faz 0 boyunca bilinçli olarak ertelendi. Karar artık şu
kısıtlar altında veriliyor:

- **Kapasite:** tek geliştirici + coding agent (ROADMAP assumption).
- **En riskli iki teknik kalem:** extraction kalitesi (R-09, A-7) ve parser kırılganlığı
  (R-10, olasılık H). İkisi de scraping/PDF/NLP tarafında.
- **En görünür kalem:** explainability arayüzü (D-005) — üç durumlu şart defteri,
  evidence gösterimi.
- **Ölçek:** MVP'de 2-3 source, ~6 occupation, 12-18 beta kullanıcı. NFR-203 ölçek
  şartı **tasarım hedefi**, MVP implementation'ı basit kalabilir.
- **Audit dersi:** iki CRITICAL bulgunun ikisi de "model geçersiz durumu ifade edebiliyor"
  tipindeydi (MAT-01 `unmet`/`unknown` ayrımı, AIX-01 doğrulanmamış license). Seçilen
  dilin bu durumları **temsil edilemez** kılabilmesi bir gerekliliktir, tercih değil.

## Decision

**Hibrit: veri/işleme katmanı Python, kullanıcı arayüzü TypeScript.**

| Katman | Seçim | Gerekçe |
|---|---|---|
| Ingestion (fetch/parse/normalize/dedupe) | **Python** — `httpx`, `selectolax`, `pydantic` | R-10'un yaşadığı yer; HTML parsing ve normalizasyon ekosistemi en olgun burada |
| CV parsing / extraction | **Python** — `pypdf`/`pdfplumber` | R-09'un yaşadığı yer; PDF metin katmanı işleme ve LLM tooling en güçlü burada (MVP kapsamı: PDF + Türkçe, OCR yok) |
| Matching + explanation | **Python** | Extraction ile aynı veri yapılarını paylaşır; ayrı runtime'a taşımak gereksiz sınır yaratır |
| API | **Python / FastAPI** | Pydantic modelleri doğrudan OpenAPI üretir → §Şema sözleşmesi |
| Web arayüz | **TypeScript / Next.js** | Explainability arayüzü iterasyon hızı ister; mevcut prototip buraya taşınır |
| Veritabanı | **PostgreSQL + pgvector** | Türkçe full-text search yerleşik; semantic katkı ≤~%10 (D-017) olduğu için ayrı vector DB gereksiz |
| Şema/migration | Düz SQL migration dosyaları | Tek geliştiricide ORM soyutlamasından çok şema okunabilirliği değerli |
| Çalışma ortamı | **Docker Compose** — uzun ömürlü worker'lar | Crawl scheduler uzun ömürlü süreç ister; yerel geliştirme üretimle aynı şekle sahip olur |

## Alternatives Considered

| Alternatif | Artıları | Eksileri | Neden seçilmedi |
|---|---|---|---|
| **TypeScript her yerde** | Tek dil, tek runtime; discriminated union'lar domain invariant'larını derleme zamanında yakalar; agent hatası daha erken görünür | Scraping/PDF/NLP ekosistemi belirgin şekilde zayıf; R-09 ve R-10 tam da orada | Projenin en riskli iki kalemi için en zayıf araç setini seçmek olurdu |
| **Python her yerde** (FastAPI + HTMX) | Tek dil, en güçlü veri ekosistemi, en az ops | Explainability ağırlıklı arayüzde iterasyon yavaş; mevcut prototipi taşımak zahmetli | Ürünün en görünür ayrıştırıcısı arayüz; orada hız kaybı kabul edilmedi |
| **Hibrit (seçilen)** | Her katman için en uygun araç | İki runtime, iki dil, **şema kayması riski** | Seçildi — şema kayması riski aşağıdaki mekanizmayla yapısal olarak kapatıldı |

## Şema sözleşmesi — hibrit'in tek gerçek riski ve çözümü

İki runtime'lı mimarinin asıl tehlikesi, Python tarafındaki model ile TypeScript
tarafındaki tipin **sessizce ayrışmasıdır.** Elle senkron tutmaya güvenilmez. Bu yüzden:

1. Domain modeli **tek yerde** tanımlanır: `services/core` içindeki Pydantic modelleri.
2. FastAPI bu modellerden **OpenAPI şemasını otomatik üretir.**
3. TypeScript tipleri OpenAPI'dan **üretilir** (`openapi-typescript`), elle yazılmaz.
4. Üretilen tipler repoya işlenir; CI'da yeniden üretip fark oluşursa **build kırılır.**

Böylece "Python'da alan eklendi, TS'te unutuldu" durumu derleme hatasına dönüşür.

## Domain invariant'larının kodda karşılığı

Audit'in iki CRITICAL bulgusu tip düzeyinde kapatılır:

```
RequirementState   = Literal["met", "unmet", "unknown"]      # bool YOK
UnknownReason      = Literal["missing_profile_data",
                             "unverified_gate_field",
                             "low_confidence_extraction"]
VerificationState  = Literal["unverified", "user_asserted", "verified"]
```

- `unknown` durumu `Optional[bool]` ile değil, **ayrı bir varyant** olarak modellenir —
  MAT-01'in tekrarı yapısal olarak imkânsız hale gelir.
- Gate-relevant alan `verified` değilse değerlendirme fonksiyonu `met` **döndüremez**;
  bu bir runtime kontrolü değil, fonksiyon imzasının garantisidir (AIX-01).
- Match Score hiçbir yerde yüzde olarak temsil edilmez; `MatchBand` enum'dur (D-005).

## Consequences

**Pozitif:** her katman kendi güçlü ekosisteminde; extraction ve parser bakımı Python'da;
arayüz iterasyonu hızlı; Postgres tek veri deposu olarak hem ilişkisel hem full-text hem
vector ihtiyacını karşılıyor; yerel geliştirme üretimle aynı şekilde.

**Negatif / kabul edilen maliyet:** iki runtime'ın kurulum ve CI maliyeti; şema üretim
adımının disipline uyulmasını gerektirmesi; iki dilde bağlam değiştirme yükü. Bu maliyet
bilinçli olarak, R-09/R-10 riskini azaltmak karşılığında kabul edildi.

**Etkilenen dokümanlar:** DECISIONS.md (D-001 kapanır, D-018 eklenir), TASKS.md (T-012
Done, T-013+ açılır), ARCHITECTURE.md (deployment görünümü somutlaşır),
TEST_STRATEGY.md (fixture ve contract testleri bu araçlara bağlanır).

## Geri dönüş koşulu

Bu karar şu durumlarda yeniden açılır: (a) şema üretim disiplini pratikte tutmaz ve
kayma tekrarlarsa — o zaman tek dile konsolidasyon değerlendirilir; (b) Python tarafı
tek geliştirici için ops yükü olarak taşınamaz hale gelirse; (c) T-009'un CV parsing
yaklaşımı kararı harici bir servise dayanır ve Python avantajı ortadan kalkarsa.

## Open Questions

- ❓ OPEN-03: harici AI servisi kullanılacak mı? Bu karar CV parsing implementasyonunun
  şeklini belirler; T-008 doğrulaması olmadan gerçek kullanıcı verisi harici servise
  gönderilemez.
- ❓ OPEN-12/13: MVP-required test ve observability alt kümesi (T-011) hâlâ açık; CI
  kapsamı bu karara göre kesinleşecek.
