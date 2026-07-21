# PROGRESS.md — İlerleme Kaydı

> **Purpose:** Mevcut durumun ve son tamamlanan işlerin kaydı; kronolojik, en yeni üstte.
> Her session sonunda entry eklenir. Güncel durum özeti için [CONTEXT.md](CONTEXT.md);
> task status'ları için [TASKS.md](TASKS.md); milestone/release kayıtları için
> [CHANGELOG.md](CHANGELOG.md).
>
> Faz kapanışında eski entry'ler `archive/PROGRESS-<faz>.md` altına taşınır; aktif dosyada
> güncel faz kalır.

## 2026-07-21 — T-022A: Interview hazırlığı + OPEN-19 izin taslakları (Done)

T-003 kullanıcı tarafından kabul edildi; `fb3bf17` T-003 final baseline'ı olarak
sabitlendi. Ardından T-022 ikiye ayrıldı ve hazırlık aşaması tamamlandı.

**T-022A — saha materyalleri (Done).**
[USER_INTERVIEW_VALIDATION_PLAN.md](docs/research/USER_INTERVIEW_VALIDATION_PLAN.md):
25 bölüm + CSV kod defteri. Tasarımın çekirdeği, görüşmenin ilk iki bölümünde ürünün
**hiç anlatılmaması** ve yalnızca geçmiş davranışın sorulması; konsept ancak Bölüm C'de
tek bir kartla gösteriliyor. Hipotetik olumluluk ("kullanırdım", "güzelmiş") açıkça
**kanıt sayılmıyor**; kanıt gücü dört kademeli kodlanıyor (strong/moderate/weak/invalid)
ve yalnızca ilk ikisi sentezde sayılıyor. Yönlendirici soru kaçınma rehberi, red flag
listesi ve "bizi yanlışlayan bulgular" bölümü zorunlu tutulan sentez şablonu eklendi.
Kota: 12-18 katılımcı, cluster başına en az 4.

[USER_INTERVIEW_RESPONSE_TEMPLATE.csv](docs/research/USER_INTERVIEW_RESPONSE_TEMPLATE.csv):
34 alanlı, **yalnızca başlık satırı** — hiçbir örnek/hayali yanıt yok. İsim, telefon,
e-posta ve doğrudan kimlik alanı **bilinçli olarak yok**; katılımcılar `P-01` gibi
takma kimlikle kaydediliyor.

**T-022B — Pending Fieldwork / Blocked (External Input).** Görüşmeleri kullanıcı yürütür.
Gerçek katılımcı verisi olmadan tamamlanamaz; hayali görüşme cevabı veya validation
sonucu üretilmedi ve üretilmeyecek.

**OPEN-19 — izin talebi taslakları (gönderilmedi).**
[SOURCE_PERMISSION_REQUESTS_TR.md](docs/research/SOURCE_PERMISSION_REQUESTS_TR.md):
İşin Olsun/Kariyer.net grubu ve İŞKUR için ayrı taslaklar; her biri kısa + detaylı
sürüm, teknik ek bilgi listesi, net sorular, takip mesajı ve **gelen cevabın Source
Registry'ye nasıl işleneceği** tablosu içeriyor. Taslaklar hukuki pozisyon almıyor,
karşı tarafın şartlarını kendi lehimize yorumlamıyor; yalnızca izin ve uygun entegrasyon
yöntemini soruyor. Restriction bypass edilmeyeceği, verinin satılmayacağı, kaynak ve
orijinal URL'in korunacağı, başvurunun orijinal kaynaktan yapılacağı açıkça yazılı.
**İletişim adresleri uydurulmadı — `Unknown` bırakıldı** ve gönderim öncesi doğrulama
şartı kondu.

**Yeni açık soru:** OPEN-21 (teşvik, ses kaydı ve kayıt saklama süresi — kullanıcı kararı).

## 2026-07-21 — T-003: Türkiye source landscape araştırması (Done)

15 aday kaynak, birincil kanıta (robots.txt, public ToS/sözleşme sayfaları, sitemap'ler,
public listing sayfaları) dayanarak incelendi. Kanıt dosyası:
[TURKEY_SOURCE_LANDSCAPE.md](docs/research/TURKEY_SOURCE_LANDSCAPE.md); registry kayıtları
[SOURCE_REGISTRY.md](docs/architecture/SOURCE_REGISTRY.md) §5.

**Tavsiye: CONDITIONAL GO.** Wave 1 = isinolsun.com (iki cluster'ı tek başına taşıyor,
robots tam izinli, sitemap'li, adapter karmaşıklığı düşük). Wave 2 = İŞKUR e-Şube (farklı
işveren havuzu → gerçek cross-source dedupe testi) + Kamu İlan/SBB (D-015 listing-only
davranışını gerçek veriyle test eder). Fallback: SecretCV, Boğaziçi Kariyer Merkezi,
ATS tenant'ları.

**En önemli bulgu — izin belirsizliği kaynak yokluğundan daha bağlayıcı:** MVP'ye aday
hiçbir kaynak koşulsuz `allowed` değil. isinolsun robots açısından tam izinli ama üyelik
sözleşmesi §4.12 veri kopyalamayı yazılı izne bağlıyor; kariyer.net'in ToS sayfası
otomatik erişime 403 dönüyor; yenibiris.com'un robots.txt'i bile 403; Indeed ve LinkedIn
iş ilanı path'lerini açıkça yasaklıyor (LinkedIn ayrıca dosya başında açık ifadeyle).
Kamu kaynaklarında robots izinli ama hiçbirinde yeniden kullanım lisansı yok.

**Rejected:** Indeed, LinkedIn, eleman.net (robots ilan path'lerini kapatıyor),
yenibiris.com (robots okunamıyor), ODTÜ KPM (login wall), iskur.gov.tr kurumsal host
(`/is-arama?*` disallow — e-şube host'undan ayrı kayıt). Hiçbiri için bypass
araştırılmadı, önerilmedi veya tasarlanmadı.

**Tasarımı doğrulayan iki bulgu:** (1) FS-12 access-change detection spekülatif değil —
araştırma sırasında üç canlı 403 örneği görüldü. (2) Tek source ile core loop
doğrulaması teknik olarak mümkün (isinolsun iki cluster'ı taşıyor) → ROADMAP M2 ve
T-017'nin düzeltilmiş dependency yapısı destekleniyor.

**Acceptance sapması (bilinçli):** "cluster başına asgari ilan hacmi doğrulandı" kriteri
niceliksel karşılanamadı; hacim tahminleri niteliksel kaldı. Nicel ölçüm T-021'e
devredildi ve T-021 acceptance'ı buna göre genişletildi (çapraz yayın, işveren gizleme,
posted_at görünürlük oranları da aynı örneklemden ölçülecek).

**Yeni açık sorular:** OPEN-18 (§4.12 kapsamı), OPEN-19 (yazılı izin talebi — kullanıcı
kararı), OPEN-20 (healthcare cluster zayıflığı). OPEN-09 M1-blocker'a yükseltildi.

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
