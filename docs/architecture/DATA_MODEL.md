# DATA_MODEL.md — Kavramsal Data Model

> **Purpose:** Ana entity'lerin alan seviyesinde, **technology-independent** kavramsal
> şeması. Belirli bir database modeli (relational/document/graph) ima etmez — o karar
> stack ADR'siyle verilir (D-001). Kavramların anlamı ve ilişki kuralları:
> [DOMAIN_MODEL.md](DOMAIN_MODEL.md). Source Record şeması ayrı dosyadadır:
> [SOURCE_REGISTRY.md](SOURCE_REGISTRY.md).
>
> Gösterim: `alan_adı : tür — açıklama`. `?` = opsiyonel. Bütün entity'lerde `id`,
> `created_at`, `updated_at` var sayılır ve tekrar yazılmaz.

## User

```
email / auth kimliği        — hesap düzeyinde
locale, timezone
notification_settings       — MVP: yalnızca `digest_opt_out` (D-016). Kanal/frekans/eşik
                              alanları V1'de eklenir (F-15)
consent_records[]           — hangi izne ne zaman onay/geri çekme (privacy gereği)
status                      — active | deactivated | deletion_pending | deleted
```

## CareerProfile

Aşağıdaki alanlarda geçen ortak yapılar:
- `verification_state` : `unverified | user_asserted | verified` — bkz. §Verification States
- `provenance` : `{source: cv_parsed | user_entered, confidence?, source_span?}` —
  `source_span` yalnızca cv_parsed alanlarda; kaynak belge silinse de kanıt yaşasın diye
  offset yerine **kısa alıntı (excerpt)** olarak saklanır.
- `level` : ortak proficiency ölçeği — bkz. §Proficiency Scale

```
user_id
occupation_ids[]            — {occupation_id, role: primary | secondary}
headline?                   — kısa tanıtım (serbest metin — sensitive tarama kapsamında)
education[]                 — {level, field, institution?, year?, verification_state, provenance}
work_experience[]           — {title, occupation_id?, employer_ref?, sector?, start, end?,
                               description?, verification_state, provenance}
skills[]                    — {qualification_id | free_text, level?, years?,
                               verification_state, provenance}
certifications[]            — {qualification_id | free_text, issuer?, valid_until?,
                               verification_state, provenance}
professional_licenses[]     — {license_type_id, category?, jurisdiction, valid_until?,
                               verification_state, provenance}   ← GATE-RELEVANT
work_authorization?         — {jurisdiction, has_right: yes | no | unknown,
                               verification_state}                ← GATE-RELEVANT
languages[]                 — {language, level, verification_state, provenance}
portfolio[]                 — {url, type, description?}
occupation_specific[]       — Occupation Profile template'inden gelen, license/certification
                              OLMAYAN meslek-özgü alanlar (ör. vardiya uygunluğu, ekipman
                              bilgisi, bölge tercihi)
parsing_metadata?           — hangi CV versiyonundan, hangi parser/extractor versiyonuyla
```

> **Tek ev kuralı:** License niteliğindeki her şey — **ehliyet kategorisi dahil** —
> `professional_licenses[]` içinde yaşar (`category` alanıyla). `occupation_specific[]`
> license/certification ile kesişmez.
>
> **Kaldırılan alan:** `completeness_score` — F-19 V1'e taşındı (D-008).
>
> **Sensitive alanlar bu entity'de yer almaz** ve D-006 güçlendirmesi uyarınca
> **hiç saklanmaz**: photo, religion, ethnicity, marital status, health information,
> union membership, gender, full birth date. CV'de bulunurlarsa profile taslağına
> aktarılmadan discard edilir ([AI_SYSTEM.md](AI_SYSTEM.md) §1.2).

### Verification States

| Değer | Anlamı | Gate davranışı (D-012) |
|---|---|---|
| `unverified` | Parse edildi, kullanıcı görmedi/onaylamadı | Gate'i `met` yapamaz → `unknown` |
| `user_asserted` | Kullanıcı beyan etti veya parse sonucunu onayladı | Gate-relevant olmayan alanlar için yeterli |
| `verified` | Gate-relevant alan için gereken doğrulama adımı tamamlandı | Gate'i `met` yapabilir |

**Gate-relevant alanlar** (`verified` şartı olanlar): `professional_licenses[]` (ehliyet
kategorisi dahil), `work_authorization`, yasal zorunlu sertifikalar
(`certifications[]` içinde `is_legally_required: true` olanlar) ve country-specific
professional authorization kayıtları. Bu alanlar `verified` değilse hard requirement
`unknown / verification required` üretir — `met` de `unmet` de değil.

> MVP'de "doğrulama" belge yükleme/otomatik kontrol anlamına gelmez; kullanıcının
> onboarding'de bu alanı **açıkça teyit etme adımından geçmesi** anlamına gelir
> (bkz. [USER_FLOWS.md](../product/USER_FLOWS.md) Flow 1/2). Belge tabanlı doğrulama V1+
> konusudur.

### Proficiency Scale

`skills[].level` ve `languages[].level` ortak, extensible bir ölçek kullanır:

```
level = { scale: string, value: string, normalized: 0..1 }
```

- MVP varsayılan skala: `basic | intermediate | advanced | expert` (normalized:
  0.25 / 0.5 / 0.75 / 1.0).
- Dil için yaygın bir dış skala (ör. A1–C2) kullanılırsa `scale` alanı onu adlandırır ve
  `normalized` ile karşılaştırılabilir hale gelir.
- `level` yoksa faktör o alanı `unknown` işler; **seviyesizlik düşük seviye demek
  değildir.**

## Preference

```
profile_id
preferred_locations[]       — {location_ref, radius?, relocation_ok}
salary_expectation?         — {min, currency, period}
work_types[]                — on_site | hybrid | remote            (tercih)
employment_types[]          — full_time | part_time | contract | seasonal | freelance
shift_preference?           — {preferred_pattern, weekend_preference}   (tercih)
shift_capability?           — {can_work_night: bool, can_work_weekend: bool,
                               unavailable_days[]}                      (yapabilirlik kısıtı)
sectors_preferred[]?, sectors_excluded[]?
excluded_employers[]?       — employer_ref listesi; employer identity resolution'a bağımlı
matching_factor_overrides[]? — V1 (F-18): kullanıcının faktör öncelik ayarları
```

> **Tercih ≠ yapabilirlik:** `shift_preference` yalnızca sıralamayı etkiler;
> `shift_capability` gate olabilir (kural:
> [MATCHING_ENGINE.md](MATCHING_ENGINE.md) §1.2).

## Employer

> **Yeni entity (audit SCR-01/ARC-04).** Duplicate blocking anahtarı, cluster temsilci
> seçimi ve `excluded_employers` bu çözünürlüğe bağımlıydı ama sahibi yoktu.

```
canonical_name
aliases[]                   — {name, source_id?, confidence}
legal_form_normalized?      — "A.Ş." / "Anonim Şirketi" gibi varyantlar normalize edilir
ats_domains[]?              — ATS subdomain eşlemeleri (ör. firma.ornekats.example)
resolution_confidence       — düşük confidence'ta blocking anahtarı employer'sız kurulur
```

**Sahibi:** Normalizer içindeki **Employer Identity Resolver** adımı
([SCRAPING_SYSTEM.md](SCRAPING_SYSTEM.md) §3). `JobPosting.employer.employer_ref` bu
entity'ye işaret eder. Çözümlenemeyen employer'da dedupe, employer'sız fallback blocking
anahtarı kullanır (title + location + içerik fingerprint).

## SensitiveDataVault (kayıt) — *extension, varsayılan değil*

> **D-006 güçlendirmesi (2026-07-21):** Vault **varsayılan saklama alanı değildir.**
> Açık product/legal amacı ve consent'i olmayan sensitive alan hiç saklanmaz; parse
> anında discard edilir ve yalnızca "tespit edildi ve atıldı" meta-kaydı tutulur.
> Vault yalnızca ileride tanımlanmış bir amaç ve consent ortaya çıkarsa kullanılacak bir
> extension noktası olarak modelde durur. **MVP'de aktif kullanımı yoktur.**

```
user_id
field_type                  — yalnızca amacı ve hukuki dayanağı politika dokümanında
                              yazılmış alanlar
value                       — encrypted
consent_ref                 — hangi consent kaydına dayanıyor (zorunlu)
purpose                     — neden tutuluyor (zorunlu; boş olamaz)
retention_until             — ne zaman silinecek (zorunlu)
```
Erişim: yalnızca kullanıcının kendi görüntülemesi ve deletion/export akışları.
**Matching veri yoluna çıkışı yoktur** (NFR-403).

## DataRightsRequest

> **Yeni entity (audit OPS-07).** RB-7 ve "Deletion/export SLA uyumu" metriği takip
> edilebilir bir kayıt gerektiriyordu.

```
user_id
type                        — export | deletion
requested_at, status        — received | in_progress | completed | cancelled
class_progress[]            — {data_class, done_at?}  ← envanterdeki her sınıf için
completed_at?, note?
```
Veri sınıfları listesi:
[PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md) → veri
envanteri (tek sahip orası).

## ManualReviewItem

> Minimal MRQ (D-014) için asgari kayıt.

```
reason_code                 — source_permission | low_confidence_extraction |
                              regulated_ambiguity | sensitive_requirement |
                              coverage_anomaly | removal_request
subject_ref                 — ilgili kayıt (source / posting / requirement)
priority                    — compliance | quality
created_at, status          — open | resolved | dismissed
decision_note?              — kim, ne zaman, neden (audit log)
```

## JobSource

Alan listesi [SOURCE_REGISTRY.md](SOURCE_REGISTRY.md) → Source Record Template'tedir
(tek sahip orası).

## JobPosting

```
source_id, source_posting_ref — provenance çekirdeği
canonical_id                — bağlı olduğu CanonicalJobPosting
url
title_raw, title_normalized
occupation_ids[]            — {occupation_id, confidence}
employer?                   — {name_raw, employer_ref?, resolution_confidence}
locations[]                 — {location_ref, remote_flag}
work_types[], employment_types[]
shift_info?                 — {shift_pattern: day | night | rotating | split | flexible,
                               weekend_required?: bool, days?: [..], confidence}
                              ← Preference.shift_capability ile simetrik
salary?                     — {min?, max?, currency, period, disclosed: bool}
is_public_sector            — true ise listing-only / guidance mode (D-015, FR-410)
description_raw             — orijinal metin (copyright: yalnızca işleme ve kullanıcıya
                              source'a atıfla kısmi gösterim; bkz. PRIVACY_SECURITY_COMPLIANCE.md)
requirements[]              — {qualification_ref | free_text,
                               kind: hard | required | preferred,
                               category: skill|education|experience|license|certification|
                                         language|portfolio|equipment|other,
                               min_years?: number,          ← "3 yıl deneyim"
                               level?: Proficiency,          ← "ileri düzey"
                               jurisdiction?: string,        ← license şartlarında
                               requires_verification?: bool, ← gate-relevant ise true
                               is_legal_eligibility?: bool,  ← age/health/military vb.
                                                               (D-013: skora girmez,
                                                                bilgilendirme + uyarı)
                               source_span?: excerpt,        ← evidence (kısa alıntı)
                               confidence}
language                    — ilan dili
posted_at?, expires_at?
status                      — active | stale | expired | suspicious | under_review
freshness_score
quality                     — {validation_passed, missing_fields[], quality_score,
                               field_accuracy_flags[]}   ← "veri var ama yanlış" sinyali
provenance                  — {fetched_at, adapter_version, parser_version,
                               extractor_version, taxonomy_version}
```

> `stale`: [SCRAPING_SYSTEM.md](SCRAPING_SYSTEM.md) §7 yaş sinyaliyle işaretlenen,
> doğrulama crawl'ı bekleyen ilan. Feed'de gösterilir ama freshness bonusu almaz.

## CanonicalJobPosting

```
member_posting_ids[]        — duplicate cluster
representative_posting_id   — gösterim için seçilen üye (en taze + en kaliteli)
repost_of?                  — daha önce expire olmuş bir cluster'ın yeniden yayını
merge_log[]                 — geri alınabilirlik için (FS-3)
status                      — üyelerden türetilir (biri aktifse aktif)
display_source              — feed kartında gösterilecek source + freshness; temsilci
                              üyeden türer. Diğer üyeler "ayrıca şurada da yayında"
                              listesi olarak gösterilebilir (C-5 garantisi)
first_seen_at, last_verified_at
```

## MatchResult

```
profile_id, canonical_id
score                       — toplam Match Score
confidence                  — Match Confidence
factor_scores[]             — {factor_id, state: met | unmet | unknown, score?,
                               weight_used, evidence_refs[]}
                              ← unknown olan faktör skora girmez, confidence'ı düşürür
hard_requirement_status     — all_met
                            | unmet: [requirement_ref]
                            | unknown: [{requirement_ref, reason: missing_profile_data
                                                                | unverified_gate_field
                                                                | low_confidence_extraction}]
                              ← D-011 / D-012
ranking_inputs              — {freshness_applied, personalization_applied}  ← §4.1
computed_at                 — hesaplama zamanı
engine_version, taxonomy_version  — reproducibility ve invalidation için
staleness                   — current | stale (yeniden hesaplama bekliyor)
                              ← invalidation tetikleri: MATCHING_ENGINE.md §2.3
```

## MatchExplanation

```
match_result_id
met_requirements[]          — {text, evidence_refs[]}
unmet_requirements[]        — {text, kind, evidence_refs[]}
unknown_requirements[]      — {text, missing_field, what_changes_if_added,
                               why_uncertain, evidence_refs[]}   ← FR-411
legal_eligibility_notices[] — {text, "kaynağı kontrol et" yönlendirmesi}  ← D-013/FR-412
coverage_limitation_notice? — occupation kalibre değilse gösterilir (D-008)
worth_applying_assessment   — {text, rule_id, evidence_refs[]}   ← kural tablosu: §4
cv_suggestions[]            — V1 (F-20)
missing_qualification_recs[] — V1 (F-20)
```

> **Evidence kuralı:** MatchExplanation'daki her alan `evidence_refs[]` taşır; bir
> `evidence_ref` ya bir `JobPosting.requirements[].source_span`'ine ya bir Career Profile
> alanına ya da bir structured data alanına işaret eder. Evidence'ı olmayan iddia
> explanation'a giremez — bu, [TEST_STRATEGY.md](../quality/TEST_STRATEGY.md) §3'teki
> otomatik kontrolün dayanağıdır.

## FeedbackSignal

```
user_id, canonical_id
type                        — saved | not_interested | applied | reported | 
                              viewed | dismissed
reason?                     — not_interested/report nedeni (enum + serbest metin)
context                     — feed | search | digest | notification
occurred_at
```

## Application

```
user_id, canonical_id
status                      — applied | interview | offer | rejected | withdrawn
status_history[]            — {status, at, note?}
applied_via_source_id       — hangi source'a yönlendirildi
```

## Taxonomy Entity'leri

Occupation, OccupationProfile, Qualification tanım şemaları
[OCCUPATION_TAXONOMY.md](OCCUPATION_TAXONOMY.md) dosyasındadır (tek sahip orası).

## Saklama Notları

- Retention süreleri ve silme davranışı entity başına
  [PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md) → Data
  Lifecycle tablosundadır; burada tekrar edilmez.
- ❓ OPEN-06: `description_raw` saklama süresi ve gösterim sınırı (copyright riski) —
  hukuki doğrulama (T-008) ile netleşecek.
