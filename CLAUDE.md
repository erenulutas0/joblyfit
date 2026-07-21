# CLAUDE.md — Claude'a Özgü Çalışma Talimatları

> **Purpose:** Yalnızca Claude'a özgü, session düzeyindeki asgari talimatlar.
> **Bütün agent'lar için geçerli normatif kurallar (yasaklar, çalışma sırası, çakışma
> otoritesi, dosya hijyeni) tek yerde: [AGENTS.md](AGENTS.md). Bu dosya onları tekrar
> etmez.** Çelişki görürsen AGENTS.md kazanır.

## Session Başında (sırayla)

1. [CONTEXT.md](CONTEXT.md) — projenin güncel durumu, açık kararlar, Open Question Index.
2. [SESSION_HANDOFF.md](SESSION_HANDOFF.md) — en üstteki (en yeni) handoff kaydı.
3. [TASKS.md](TASKS.md) — çalışılacak task'ı seç; Dependency alanına uy.

## Session Sonunda (sırayla)

1. [PROGRESS.md](PROGRESS.md) — yapılan işi ekle.
2. [SESSION_HANDOFF.md](SESSION_HANDOFF.md) — şablonu kullanarak yeni handoff yaz.
3. [TASKS.md](TASKS.md) — task status'larını güncelle.
4. [CONTEXT.md](CONTEXT.md) — proje durumu değiştiyse **Şu Anki Faz / Aktif Hedef /
   Open Question Index**'i güncelle ve `Last updated` tarihini yenile.
5. [CHANGELOG.md](CHANGELOG.md) — **yalnızca** bir milestone/release kapanıyorsa.
6. `git commit` — session'ın çıktısını commit'le (remote yok, push yok).

## Bu Projede Claude'un Sık Düştüğü Tuzaklar

- **Faz sırası:** Stack kararı (D-001 → T-012) kapanmadan implementation task'ına
  (T-013 ve sonrası) başlama. Validation gate (D-010) kapanmadan M1 geçilmiş sayılmaz.
- **Onaysız karar:** Technology stack, scope değişikliği, yeni source'a scraping
  başlatma ve privacy/compliance politikası değişikliği kullanıcı onayı ister
  (gerekçe ve tam liste: AGENTS.md → Yasaklar).
- **Türkiye ≠ core:** Launch pazarı Türkiye'dir (D-009) ama TR'ye özgü hiçbir şey core
  architecture varsayımı yapılmaz; extension/policy katmanında modellenir.
- **Hukuki dil:** Legal değerlendirmeler kesin hukuki görüş gibi yazılmaz; T-008'e
  bağlanır ve "hukuki görüş değildir" çerçevesi korunur.
- **Match Score dili:** Hiçbir yerde işe alınma olasılığı veya garanti gibi sunulmaz
  (D-005).
