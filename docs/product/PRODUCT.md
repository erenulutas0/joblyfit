# PRODUCT.md — Product Vision ve Temel Çerçeve

> **Purpose:** Ürünün vision, problem statement, value proposition, target user groups,
> jobs-to-be-done ve core capability tanımlarının sahibi. Scope (MVP/V1/Future) burada
> değil, [PRD.md](PRD.md) dosyasındadır. Personas: [USER_PERSONAS.md](USER_PERSONAS.md).
> Terimler: [GLOSSARY.md](GLOSSARY.md).

## 1. Product Vision

**Her meslekten insanın, dağınık ilan dünyasında kendisine gerçekten uyan işleri —
neden uyduğunu ve neyin eksik olduğunu anlayarak — tek yerden keşfedebildiği bir platform.**

İş arama bugün mesleğe göre eşitsiz bir deneyim: yazılımcılar için onlarca özel platform
varken bir hemşire, şoför veya tekniker için ilanlar devlet portalları, yerel siteler ve
kurumsal kariyer sayfalarına dağılmış durumda. Vizyonumuz, bu dağınıklığı meslek ayrımı
yapmadan kapatmak ve "keyword eşleşmesi" yerine mesleğin gerçek qualification yapısını
anlayan bir eşleştirme sunmaktır.

## 2. Problem Statement

İş arayanlar için üç temel problem:

1. **Dağınıklık:** İlanlar yüzlerce job board, company career page, ATS sayfası,
   government portal ve sektörel kaynağa yayılmış durumda. Tek kaynak hiçbirini tam
   kapsamıyor; kullanıcı aynı aramayı birçok yerde tekrarlıyor, duplicate ve expired
   ilanlarla vakit kaybediyor.
2. **Alakasızlık:** Mevcut platformların önerileri büyük ölçüde keyword benzerliğine
   dayanıyor. Bir hemşirenin shift availability'si, bir şoförün ehliyet kategorisi, bir
   muhasebecinin mevzuat bilgisi gibi meslek-spesifik nitelikler anlaşılmıyor; sonuç,
   "uygun görünen ama başvurmaya değmeyen" ilan yığını.
3. **Belirsizlik:** Kullanıcı bir ilana bakarken "bana uyar mı, neyim eksik, başvursam
   şansım var mı" sorularının cevabını alamıyor. Öneri sistemleri kapalı kutu; skorlar
   açıklamasız.

Bu üçlünün maliyeti: uzayan iş arama süreleri, kaçırılan uygun fırsatlar ve özellikle
white-collar dışı mesleklerde dijital iş aramadan dışlanma.

## 3. Value Proposition

> **Vaat hiyerarşisi (audit PS-02 düzeltmesi):** Coverage bir **taban şarttır**,
> ayrıştırıcı değildir — ve compliance-first ingestion (D-002) gereği "her ilan" iddiası
> dürüst değildir. Ayrıştırıcı olan, meslek-spesifik eşleştirme derinliği ve
> explainability'dir. Coverage ölçülür (METRICS → Market coverage) ve eşik altında
> kalırsa T-021'de tanımlı karar uygulanır.

| Kullanıcıya vaat | Nasıl |
|---|---|
| "Aradığın işler dağınık değil, tek yerde" *(taban şart — ölçülür)* | Çok kaynaklı, source-independent ingestion; duplicate ve expired temizliği; source transparency. **Kapsama sınırı kullanıcıdan gizlenmez:** hangi kaynakların tarandığı görünür |
| "Mesleğini gerçekten anlayan eşleştirme" | Occupation Taxonomy + hybrid matching (hard requirements + qualifications + preferences) |
| "Nedenini bilerek başvur" | Her öneri için Match Explanation: karşılanan/eksik requirement'lar, başvurmaya değer mi, CV'de ne güçlendirilebilir |
| "Kariyerinde sonraki adımı gör" | Transferable skill'ler üzerinden gerçekçi Career Transition önerileri; regulated profession'larda dürüst eksik-license uyarısı |
| "Verin sana ait" | Şeffaf veri kullanımı, export ve deletion hakları ([PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md)) |

**Ayrıştırıcı konum:** Genel job board'lar kapsamada geniş ama eşleştirmede yüzeysel;
niş platformlar derin ama tek sektörlü. Bu ürün, *kapsama genişliğini* meslek-spesifik
*eşleştirme derinliğiyle* ve *explainability* ile birleştirir.

## 4. Target User Groups

Birincil kullanıcı **iş arayan bireydir** (employer tarafı MVP'de yok — bkz.
[PRD.md](PRD.md) → Excluded). Meslek yelpazesi bilinçli olarak geniştir ve **vision
universal kalır**.

> **MVP kapsamı ile vision farkı (D-008):** Aşağıdaki grupların tamamı hedef kitledir,
> ancak MVP'de yalnızca üç cluster / altı occupation **first-class** desteklenir
> (Driver, Warehouse Worker, Accountant, Sales Representative, Nurse, Health Technician).
> Diğer gruplar generic tier'da hizmet alır: eşleştirme yapılır ama Match Confidence
> düşüktür ve kullanıcıya coverage limitation açıklaması gösterilir. Kimse dışlanmaz;
> yalnızca ne kadar iddialı davranıldığı değişir
> ([OCCUPATION_TAXONOMY.md](../architecture/OCCUPATION_TAXONOMY.md) → Support Tiers).

| Grup | Örnek meslekler | Ayırt edici ihtiyaç |
|---|---|---|
| Healthcare | Nurse, paramedic, technician | License, department experience, shift availability |
| Blue-collar / Manufacturing | Machine operator, welder, technician | Vocational certification, vardiya, lokasyon yakınlığı |
| Logistics / Driving | Driver, courier, warehouse staff | Driving license category, route/bölge, esnek saat |
| Education | Teacher, instructor, academic | Branch, teaching certificate, degree denklikleri |
| Retail / Hospitality | Sales rep, cashier, chef, receptionist | Sektör deneyimi, dil, vardiya, part-time |
| Finance / Office | Accountant, HR specialist, admin | Certification, software, mevzuat bilgisi |
| Software / Tech | Engineer, data analyst, IT support | Languages/frameworks, project experience, remote tercihi |
| Creative | Designer, copywriter, video editor | Portfolio, tool proficiency, freelance/proje bazlı iş |
| Public sector adayları | Memur adayları, kamu sağlık/eğitim | Government portal ilanları, resmi şart listeleri. **MVP'de listing-only / guidance mode** (D-015): ilanlar listelenir ve resmi kaynağa yönlendirilir, Match Score üretilmez — sınav puanı ve mevzuat modellenmeden "uygunsun" demek yanlış yönlendirme olur |
| Kariyer değiştirenler & yeni mezunlar | Tüm alanlar | Career Transition, missing qualification yol haritası |

İkincil kullanıcılar (ileri fazlar): kariyer danışmanları, işkur benzeri kurumlar,
recruitment agency'ler (bkz. [PRD.md](PRD.md) → Future Scope).

## 5. Jobs-to-be-Done

Kullanıcının "işe aldığı" işler:

1. *"İş aramam gerektiğinde"* → bana uyan ilanları **benim yerime bul ve sırala**,
   böylece onlarca sitede aynı aramayı tekrarlamayayım.
2. *"Bir ilan gördüğümde"* → **uyup uymadığımı ve nedenini söyle**, böylece boşa
   başvuru yapmayayım veya uygun fırsatı çekinip kaçırmayayım.
3. *"Başvuruya karar verdiğimde"* → **CV'mde neyi öne çıkaracağımı söyle**, böylece
   şansımı artırayım.
4. *"Aktif aramadığım dönemde"* → **gerçekten uyan yeni ilan çıkınca haber ver**, böylece
   fırsat kaçırmayayım ama bildirim çöplüğüne de boğulmayayım.
5. *"Mesleğimde tıkandığımda"* → **mevcut becerilerimle geçebileceğim yakın meslekleri ve
   eksiklerimi göster**, böylece kariyer değişimini gerçekçi planlayayım.
6. *"Başvurularım çoğaldığında"* → **neye başvurduğumu ve durumunu takip etmemi sağla**,
   böylece süreci kontrol edeyim.

## 6. Core Product Capabilities

Feature listesi ve scope ataması [PRD.md](PRD.md) dosyasındadır; buradaki liste ürünün
kalıcı yetenek alanlarını tanımlar:

1. **Profile Capability** — CV upload & parsing, manuel Career Profile editörü, profile
   verification, completeness score, preference configuration.
2. **Ingestion Capability** — çok kaynaklı, compliant job ingestion; normalization,
   duplicate/expiration handling, provenance ve freshness
   ([SCRAPING_SYSTEM.md](../architecture/SCRAPING_SYSTEM.md)).
3. **Understanding Capability** — Occupation Taxonomy, ilanlardan structured requirement
   extraction, CV'den qualification extraction
   ([OCCUPATION_TAXONOMY.md](../architecture/OCCUPATION_TAXONOMY.md),
   [AI_SYSTEM.md](../architecture/AI_SYSTEM.md)).
4. **Matching Capability** — hybrid matching, ranking, Match Explanation, feedback
   learning, career transition ([MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md)).
5. **Engagement Capability** — personalized feed, search & filters, saved/applied
   tracking, notifications & digest.
6. **Trust Capability** — source transparency, explainability, fairness kısıtları, veri
   hakları, report akışları
   ([PRIVACY_SECURITY_COMPLIANCE.md](../security/PRIVACY_SECURITY_COMPLIANCE.md)).

## 7. Platform Deneyimi (mobile + web)

> Not: Bu bölüm deneyim beklentisi tanımlar; platform teknolojisi seçimi yapılmamıştır (D-001).

- **Mobile ağırlıklı kullanım varsayımı:** Blue-collar, retail, logistics ve hospitality
  kullanıcılarının önemli bölümünün masaüstü bilgisayara düzenli erişimi olmadığı
  varsayılır (Assumption A-2, [PRD.md](PRD.md)). Bu nedenle bütün core flow'lar
  (onboarding, profil, feed, başvuru takibi) küçük ekranda eksiksiz çalışmalıdır.
- **Web:** CV yükleme, uzun profil düzenleme ve karşılaştırmalı ilan inceleme gibi
  "oturarak yapılan" işler için daha zengin düzen sunar.
- **Düşük dijital okuryazarlık desteği:** Kısa adımlı onboarding, sade dil, form yerine
  seçenek sunma; explanation'lar teknik jargon içermez.
