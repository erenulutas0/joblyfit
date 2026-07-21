# Job Recommender — AI-Powered Job Discovery and Matching Platform

> **Purpose:** Bu dosya projenin giriş noktasıdır. Ürünün ne olduğunu bir bakışta anlatır ve
> bütün documentation dosyalarına yol gösterir. Detaylı bilgi burada tekrar edilmez; ilgili
> dosyaya link verilir.

## Ürün Nedir?

Her meslek dalından kullanıcıya hitap eden, **AI-powered job discovery and matching platform**.
Kullanıcı CV yükler veya Career Profile'ını manuel oluşturur; sistem public job source'lardan
düzenli olarak iş ilanı toplar, normalize eder ve kullanıcının profiline göre **explainable**
şekilde sıralayıp önerir.

Üç temel ayrıştırıcı özellik:

1. **Occupation Taxonomy:** Yalnızca keyword matching değil; hemşireden şoföre, öğretmenden
   yazılımcıya kadar meslek-spesifik qualification yapılarını anlayan merkezi taxonomy.
   → [OCCUPATION_TAXONOMY.md](docs/architecture/OCCUPATION_TAXONOMY.md)
2. **Hybrid Matching + Explainability:** Hard requirement kontrolü + semantic similarity +
   preference matching. Her öneri "neden uygun, ne eksik, başvurmaya değer mi" şeklinde
   açıklanır. → [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md)
3. **Compliant, source-independent ingestion:** API + scraping karışımı, tek platforma bağımlı
   olmayan, source policy'lere saygılı ingestion mimarisi.
   → [SCRAPING_SYSTEM.md](docs/architecture/SCRAPING_SYSTEM.md)

> ⚠️ **Not:** Bu repository şu anda yalnızca product design ve system architecture
> documentation içerir. Implementation code ve technology stack seçimi henüz yapılmamıştır
> (bkz. [DECISIONS.md](DECISIONS.md) → D-001).

## Documentation Haritası

### Proje Yönetimi (root)

| Dosya | İçerik |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Coding agent'ın bu projede çalışma kuralları |
| [AGENTS.md](AGENTS.md) | Bütün coding agent'lar için ortak kurallar |
| [CONTEXT.md](CONTEXT.md) | Projenin güncel durumu ve bağlamı (her session başında oku) |
| [TASKS.md](TASKS.md) | Küçük, doğrulanabilir, sıralı task listesi |
| [PROGRESS.md](PROGRESS.md) | İlerleme kaydı |
| [SESSION_HANDOFF.md](SESSION_HANDOFF.md) | Session'lar arası devir şablonu ve kayıtları |
| [DECISIONS.md](DECISIONS.md) | Karar kaydı (decision / reason / alternatives / consequence); ileriki büyük kararlar için docs/adr/ |
| [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) | Bir işin "bitti" sayılma şartları |
| [BUGS.md](BUGS.md) | Bilinen hatalar |
| [CHANGELOG.md](CHANGELOG.md) | Değişiklik kaydı |

### Product (docs/product/)

| Dosya | İçerik |
|---|---|
| [PRODUCT.md](docs/product/PRODUCT.md) | Vision, problem statement, value proposition, target users, JTBD, core capabilities |
| [PRD.md](docs/product/PRD.md) | MVP / V1 / Future scope ve explicitly excluded features |
| [USER_PERSONAS.md](docs/product/USER_PERSONAS.md) | Farklı mesleklerden personas |
| [USER_FLOWS.md](docs/product/USER_FLOWS.md) | Ana user journey'ler |
| [REQUIREMENTS.md](docs/product/REQUIREMENTS.md) | Functional ve non-functional requirements |
| [ROADMAP.md](docs/product/ROADMAP.md) | MVP roadmap ve major milestones |
| [METRICS.md](docs/product/METRICS.md) | Product, matching quality ve scraper health metrics |
| [GLOSSARY.md](docs/product/GLOSSARY.md) | **Terminology kaynağı — bütün dokümanlar bu terimleri kullanır** |

### Architecture (docs/architecture/)

| Dosya | İçerik |
|---|---|
| [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | High-level system architecture, component responsibilities, data flow, failure scenarios |
| [DOMAIN_MODEL.md](docs/architecture/DOMAIN_MODEL.md) | Domain kavramları ve ilişkileri |
| [DATA_MODEL.md](docs/architecture/DATA_MODEL.md) | Kavramsal (technology-independent) data model |
| [SCRAPING_SYSTEM.md](docs/architecture/SCRAPING_SYSTEM.md) | Job ingestion ve scraping mimarisi, data quality, duplicate/freshness stratejileri |
| [SOURCE_REGISTRY.md](docs/architecture/SOURCE_REGISTRY.md) | Source Registry tasarımı ve source record template |
| [MATCHING_ENGINE.md](docs/architecture/MATCHING_ENGINE.md) | Hybrid matching, ranking, explainability, feedback loop |
| [OCCUPATION_TAXONOMY.md](docs/architecture/OCCUPATION_TAXONOMY.md) | Occupation Taxonomy tasarımı ve yeni occupation ekleme süreci |
| [AI_SYSTEM.md](docs/architecture/AI_SYSTEM.md) | CV parsing, profile extraction, AI bias ve fairness |
| [API_CONTRACTS.md](docs/architecture/API_CONTRACTS.md) | Component'lar arası kavramsal contract'lar |

### Security, Quality, Operations

| Dosya | İçerik |
|---|---|
| [PRIVACY_SECURITY_COMPLIANCE.md](docs/security/PRIVACY_SECURITY_COMPLIANCE.md) | Privacy, data lifecycle, security boundaries, compliance ve source policy |
| [RISK_REGISTER.md](docs/security/RISK_REGISTER.md) | Risk register |
| [TEST_STRATEGY.md](docs/quality/TEST_STRATEGY.md) | Test stratejisi |
| [OBSERVABILITY.md](docs/quality/OBSERVABILITY.md) | Logging, metrics, alerting yaklaşımı |
| [RUNBOOK.md](docs/operations/RUNBOOK.md) | Operasyonel senaryolar ve müdahale adımları |
| [docs/adr/README.md](docs/adr/README.md) | ADR süreci ve indeks |

## Nereden Başlamalı?

1. Yeni katılan biri: [PRODUCT.md](docs/product/PRODUCT.md) → [PRD.md](docs/product/PRD.md) → [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)
2. Coding agent: [CLAUDE.md](CLAUDE.md) → [CONTEXT.md](CONTEXT.md) → [TASKS.md](TASKS.md)
3. Terminoloji sorusu olan herkes: [GLOSSARY.md](docs/product/GLOSSARY.md)
