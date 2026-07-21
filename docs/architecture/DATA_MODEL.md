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
notification_settings       — kanal, frekans, eşik, opt-out
consent_records[]           — hangi izne ne zaman onay/geri çekme (privacy gereği)
status                      — active | deactivated | deletion_pending | deleted
```

## CareerProfile

```
user_id
occupation_ids[]            — taxonomy referansı (birincil + ikincil)
headline?                   — kısa tanıtım
education[]                 — {level, field, institution?, year?, verified}
work_experience[]           — {title, occupation_id?, employer?, sector?, start, end?, 
                               description?, verified}
skills[]                    — {qualification_id | free_text, level?, years?, verified, 
                               source: cv_parsed | user_entered}
certifications[]            — {qualification_id | free_text, issuer?, valid_until?, verified}
professional_licenses[]     — {license_type_id, jurisdiction, valid_until?, verified}
languages[]                 — {language, level, verified}
portfolio[]                 — {url, type, description?}
occupation_specific[]       — Occupation Profile template'inden gelen ek alanlar
                              (ör. ehliyet kategorisi, vardiya uygunluğu, ekipman bilgisi)
completeness_score          — hesaplanan
parsing_metadata?           — hangi CV versiyonundan, hangi parser versiyonuyla
```

> **Not:** Sensitive attribute'lar (doğum tarihi, fotoğraf, medeni durum vb.) bu
> entity'de **yer almaz**; CV'den çıkarsa Sensitive Data Vault'a gider (aşağıda).

## Preference

```
profile_id
preferred_locations[]       — {location_ref, radius?, relocation_ok}
salary_expectation?         — {min, currency, period}
work_types[]                — on_site | hybrid | remote
employment_types[]          — full_time | part_time | contract | seasonal | freelance
shift_availability?         — {days, night_ok, weekend_ok, flexible}
sectors_preferred[]?, sectors_excluded[]?
excluded_employers[]?       — "mevcut işverenimden gizle" dahil
matching_factor_overrides[]? — V1 (F-18): kullanıcının faktör öncelik ayarları
```

## SensitiveDataVault (kayıt)

```
user_id
field_type                  — birth_date | photo_ref | marital_status | ...
value                       — encrypted
origin                      — cv_parsed | user_entered
retention_note              — neden tutuluyor / ne zaman silinecek
```
Erişim: yalnızca kullanıcının kendi görüntülemesi ve deletion/export akışları.
**Matching veri yoluna çıkışı yoktur** (NFR-403).

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
employer?                   — {name_raw, normalized_ref?}
locations[]                 — {location_ref, remote_flag}
work_types[], employment_types[]
shift_info?                 — extraction sonucu
salary?                     — {min?, max?, currency, period, disclosed: bool}
description_raw             — orijinal metin (copyright: yalnızca işleme ve kullanıcıya
                              source'a atıfla kısmi gösterim; bkz. PRIVACY_SECURITY_COMPLIANCE.md)
requirements[]              — {qualification_ref | free_text, kind: hard | required | preferred,
                               category: skill|education|experience|license|certification|
                               language|portfolio|other, confidence}
language                    — ilan dili
posted_at?, expires_at?
status                      — active | expired | suspicious | under_review
freshness_score
quality                     — {validation_passed, missing_fields[], quality_score}
provenance                  — {fetched_at, adapter_version, parser_version, extractor_version}
```

## CanonicalJobPosting

```
member_posting_ids[]        — duplicate cluster
representative_posting_id   — gösterim için seçilen üye (en taze + en kaliteli)
merge_log[]                 — geri alınabilirlik için (FS-3)
status                      — üyelerden türetilir (biri aktifse aktif)
first_seen_at, last_verified_at
```

## MatchResult

```
profile_id, canonical_id
score                       — toplam Match Score
confidence                  — Match Confidence
factor_scores[]             — {factor_id, score, weight_used, evidence_refs[]}
hard_requirement_status     — all_met | missing: [requirement_ref]
computed_at, engine_version — reproducibility için
```

## MatchExplanation

```
match_result_id
met_requirements[]          — kullanıcı diliyle
missing_requirements[]      — hard/required/preferred ayrımıyla
worth_applying_assessment   — kısa değerlendirme + gerekçe
cv_suggestions[]            — "şunu öne çıkar" önerileri
missing_qualification_recs[] — F-20 (V1'de zenginleşir)
```

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
- ❓ OPEN: `description_raw` saklama süresi ve gösterim sınırı (copyright riski) —
  hukuki doğrulama (T-008) ile netleşecek.
