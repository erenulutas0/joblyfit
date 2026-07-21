# BUGS.md — Bilinen Hatalar

> **Purpose:** Bilinen bug'ların kaydı. Documentation fazında doküman tutarsızlıkları da
> buraya yazılır. Her kayıt aşağıdaki formatı kullanır. Kapatılan bug'lar "Closed"
> bölümüne taşınır ve çözümü not edilir.

## Format

```markdown
### BUG-XXX — [kısa başlık]
- **Status:** Open | In Progress | Closed
- **Severity:** Critical | High | Medium | Low
- **Reported:** YYYY-MM-DD
- **Area:** [ilgili doküman veya component]
- **Description:** Ne yanlış, nasıl gözlemlendi?
- **Expected:** Doğrusu ne olmalı?
- **Resolution:** (kapatılırken) Ne yapıldı?
```

## Open

_Şu anda açık bug yok._

## Closed

### BUG-001 — PROGRESS.md, DECISIONS kayıtlarını "ADR" olarak adlandırıyordu
- **Status:** Closed
- **Severity:** Low
- **Reported:** 2026-07-21 (documentation audit, DOC-05)
- **Area:** PROGRESS.md ↔ docs/adr/README.md
- **Description:** PROGRESS.md'nin 2026-07-20 girdisi "İlk ADR'ler yazıldı (D-001…D-007)"
  diyordu; oysa docs/adr/ altında template dışında dosya yok ve index'i "Henüz ADR yok"
  diyor. D-001…D-007 birer DECISIONS.md kaydıdır, ADR değildir.
- **Expected:** İki dosya birbiriyle tutarlı olmalı; ADR ile decision kaydı
  karıştırılmamalı.
- **Resolution:** PROGRESS.md ifadesi "İlk kararlar DECISIONS.md'ye kaydedildi" olarak
  düzeltildi ve düzeltme notu eklendi. ADR yazma tetiğinin tek sahibi
  [docs/adr/README.md](docs/adr/README.md) yapıldı (DOC-06).
