# USER_PERSONAS.md — Farklı Mesleklerden Personas

> **Purpose:** Tasarım ve önceliklendirme kararlarında referans alınacak temsili
> kullanıcılar. Her persona, [PRODUCT.md](PRODUCT.md) → Target User Groups içindeki bir
> segmenti somutlaştırır ve en az bir tasarım gerilimini görünür kılar. Personas
> kurgusaldır; pazar araştırmasıyla doğrulanmaları beklenir (Assumption A-2, A-4 —
> [PRD.md](PRD.md)).

## P1 — Elif, 29, Registered Nurse (Healthcare, regulated)

- **Durum:** 5 yıllık yoğun bakım hemşiresi; şehir değiştirmek istiyor. Gece vardiyasına
  devam edebilir ama sabit gündüz tercih ediyor.
- **Qualification profili:** Nursing degree, aktif hemşirelik lisansı, ICU deneyimi,
  temel İngilizce.
- **İhtiyaç:** Yeni şehirdeki hastane/klinik ilanlarını tek yerde görmek; department ve
  shift uyumuna göre eleme; hangi ilanların lisans/denklik şartını karşıladığını bilmek.
- **Tasarım gerilimi:** Regulated profession — sistem lisans şartını **hard requirement**
  olarak işlemeli, lisansı olmayan alanlara (ör. başhemşirelik için ek sertifika)
  yönlendirirken eksikliği açıkça söylemeli.
- **Başarı anı:** "3 hastane ilanında da shift ve department uyumumu, birinde eksik olan
  sertifikayı net gördüm."

## P2 — Hasan, 41, Heavy Vehicle Driver (Logistics, blue-collar)

- **Durum:** Şehirlerarası tır şoförü; eve daha yakın, bölgesel rota istiyor. Telefonu
  var, bilgisayarı yok; uzun form doldurmaya tahammülü düşük.
- **Qualification profili:** CE sınıfı ehliyet, SRC belgeleri, psikoteknik, 12 yıl rota
  deneyimi. CV'si yok.
- **İhtiyaç:** CV'siz, birkaç soruyla profil kurmak; ehliyet kategorisi ve lokasyona göre
  eşleşme; yeni uygun ilan çıkınca bildirim.
- **Tasarım gerilimi:** Mobile-first + CV'siz onboarding (F-03) birinci sınıf yol olmalı;
  explanation'lar sade dilde olmalı. Ehliyet kategorisi taxonomy'de yapılandırılmış alan
  olmalı, serbest metin değil.
- **Başarı anı:** "Beş dakikada profil kurdum; ertesi gün bölgemden iki uygun ilan
  bildirimi geldi."

## P3 — Zeynep, 34, Accountant (Finance/Office)

- **Durum:** KOBİ muhasebecisi; daha kurumsal bir şirkete geçmek ve SMMM yetkisini
  kullanacağı bir role ulaşmak istiyor.
- **Qualification profili:** İşletme lisansı, SMMM ruhsatı, Luca/Logo yazılımları,
  e-fatura/e-defter mevzuatı, orta İngilizce.
- **İhtiyaç:** Certification ve yazılım bilgisine göre gerçek eşleşme; ilanın "SMMM
  şart" mı "tercih" mi dediğinin ayrışması; CV'sinde neyi öne çıkaracağı önerisi.
- **Tasarım gerilimi:** Required vs Preferred Qualification ayrımının extraction'da doğru
  yakalanması; mevzuat bilgisi gibi yerel qualification'ların taxonomy extension'ı
  gerektirmesi.
- **Başarı anı:** "İlanın benden istediği 8 şartın 7'sini karşıladığımı, eksik olanın ne
  olduğunu ve CV'me e-defter deneyimimi eklememi söyledi."

## P4 — Mert, 26, UX/UI Designer (Creative)

- **Durum:** Ajansta 3 yıl; remote çalışabileceği product şirketi arıyor; freelance
  projelere de açık.
- **Qualification profili:** Figma, design system deneyimi, portfolio sitesi, iyi
  İngilizce.
- **İhtiyaç:** Portfolio requirement'ı olan ilanların işaretlenmesi; remote/hybrid
  filtresi; freelance ilanlarının da akışa girmesi.
- **Tasarım gerilimi:** Portfolio, klasik "skill" modellenemez — link + nitelik olarak
  ayrı qualification türü olmalı. Freelance ilanları work type olarak modellenmeli
  (marketplace mekaniği olmadan — [PRD.md](PRD.md) → Excluded).
- **Başarı anı:** "Remote + portfolio isteyen ilanlar öne geldi; iki ilanda portfolio
  yerine geçen case study istendiğini explanation'dan gördüm."

## P5 — Ayşe, 45, Sınıf Öğretmeni → Kurumsal Eğitmen adayı (Education, career transition)

- **Durum:** 20 yıllık öğretmen; özel sektörde kurumsal eğitmenliğe/eğitim içerik
  geliştirmeye geçmek istiyor.
- **Qualification profili:** Eğitim fakültesi lisansı, öğretmenlik sertifikası, sınıf
  yönetimi, müfredat geliştirme, sunum becerisi.
- **İhtiyaç:** Mevcut becerilerinin hangi mesleklere transfer olduğunu görmek; eksik
  qualification'lar (ör. e-learning araçları) için yol haritası.
- **Tasarım gerilimi:** Career Transition (F-21) tam bu persona için: sistem "kurumsal
  eğitmen" ilanlarını transferable skill'ler üzerinden önermeli, ama gerçekçilikten
  taviz vermemeli (senior instructional designer rolü için eksikler açıkça listelenmeli).
- **Başarı anı:** "Öğretmenlikten eğitmenliğe geçiş için 3 gerçekçi rol ve her biri için
  2-3 eksik becerimi gördüm."

## P6 — Emre, 22, Yeni mezun Software Engineer (Tech, entry-level)

- **Durum:** Yeni mezun; staj + bitirme projesi dışında deneyimi yok. Her ilana başvurup
  hiçbirinden dönüş alamama döngüsünde.
- **Qualification profili:** CS lisansı, Python/JS, 2 staj, GitHub projeleri.
- **İhtiyaç:** "3+ yıl deneyim" isteyen ilan yığını yerine gerçekçi entry-level eşleşme;
  hangi ilanda şansı olduğunu gösteren dürüst değerlendirme.
- **Tasarım gerilimi:** Experience/seniority faktörü "eksik yıl"ı hard elemeye çevirmemeli
  (deneyim şartı çoğu ilanda esnektir) ama Match Explanation "deneyim beklentisinin
  altındasın" demeli — seniority kalibrasyonu [MATCHING_ENGINE.md](../architecture/MATCHING_ENGINE.md).
- **Başarı anı:** "Junior uyumlu 12 ilan gördüm; ikisinde staj deneyimimin required'ı
  karşıladığı yazıyordu."

## P7 — Fatma, 31, Satış Danışmanı (Retail, vardiyalı + part-time)

- **Durum:** AVM mağazasında satış danışmanı; çocuğu nedeniyle hafta içi gündüz part-time
  arıyor; B sınıfı ehliyeti var, saha satışına da açık.
- **Qualification profili:** Lise, 8 yıl perakende satış, kasa/stok sistemleri, iyi
  iletişim, B ehliyeti.
- **İhtiyaç:** Shift/part-time filtresinin gerçekten çalışması; ev-iş mesafesi; sektör
  deneyiminin (tekstil perakende) hesaba katılması.
- **Tasarım gerilimi:** Shift availability ve part-time, retail ilanlarında çoğu zaman
  metin içinde gömülü — extraction bu alanları yapılandırmalı; lokasyon mahalle/ilçe
  hassasiyetinde anlamlı olmalı.
- **Başarı anı:** "Sadece gündüz part-time ilanları geldi; ehliyetim sayesinde saha
  satış ilanı da önerildi ve nedeni yazıyordu."

## Persona → Tasarım Gereksinimi Özeti

| Persona | Zorladığı yetenek |
|---|---|
| P1 Elif | Hard requirement (license), shift, regulated profession dürüstlüğü |
| P2 Hasan | CV'siz onboarding, mobile-first, structured license category, bildirim |
| P3 Zeynep | Required/Preferred ayrımı, lokal qualification extension, CV önerileri |
| P4 Mert | Portfolio qualification türü, remote filtresi, freelance work type |
| P5 Ayşe | Career Transition, transferable skills, missing qualification yolu |
| P6 Emre | Seniority kalibrasyonu, entry-level gerçekçiliği, dürüst explanation |
| P7 Fatma | Shift/part-time extraction, lokasyon hassasiyeti, sektör deneyimi |
