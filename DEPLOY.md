# Canlıya Alma — VPS + joblyfit.com (D-049)

> Bu kılavuz **senin** çalıştıracağın adımlardır (hesap/ödeme/ToS bende değil).
> Ben imajı (`Dockerfile`), üretim compose'unu ve otomatik-HTTPS'i hazırladım;
> aşağıdakiler onları canlıya alır. Takıldığın adımı bana yaz, birlikte çözeriz.

Sonuç: **https://app.joblyfit.com** üzerinde çalışan gerçek uygulama. Ardından
tr.jooble.org / Careerjet kaydında "Website" olarak bu adresi verirsin.

---

## 1. VPS aç (~5 dk, ~$5/ay)

- **Hetzner Cloud** (CX22, ~€4/ay) veya **DigitalOcean** ($6/ay droplet).
- **Ubuntu 24.04**, en küçük paket yeterli (2 GB RAM önerilir — korpus bellekte).
- Kurulumda SSH anahtarını ekle. Sana bir **IP adresi** verecek — not al.

## 2. Cloudflare DNS: domaini VPS'e yönlendir

Cloudflare → joblyfit.com → **DNS** → Add record:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `app` | `<VPS_IP>` | **DNS only (gri bulut)** |

> **Gri bulut önemli:** Caddy'nin Let's Encrypt sertifikasını sorunsuz alması
> için. (İstersen sonra turuncu buluta + Full SSL'e geçeriz; şimdilik gri en
> basiti.)

## 3. VPS'e bağlan ve Docker'ı kur

```bash
ssh root@<VPS_IP>
curl -fsSL https://get.docker.com | sh
```

## 4. Kodu VPS'e taşı

Yerel bilgisayarından (proje klasöründe), **rsync ile** (git remote gerekmez):

```bash
rsync -avz --exclude '.git' --exclude '.cache' --exclude '.data' --exclude '.env.local' \
  ./ root@<VPS_IP>:/opt/iseuygun/
```

> Windows'ta rsync yoksa: WSL kullan ya da `scp -r` ile klasörü kopyala.

## 5. Sırları ayarla (VPS'te)

```bash
cd /opt/iseuygun
cat > .env.prod <<'EOF'
DOMAIN=app.joblyfit.com
# Jooble TR anahtarı geldiğinde doldur (şimdilik boş bırakabilirsin):
ISUYGUN_JOOBLE_KEY=
ISUYGUN_JOOBLE_HOST=tr.jooble.org
ISUYGUN_JOOBLE_LOCATION=Türkiye
EOF
```

## 6. Başlat

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

İlk açılışta imaj derlenir (~1-2 dk). Uygulama **anında** ayağa kalkar (fixture ile),
ilk gerçek çekim **arka planda** birkaç dakikada dolar (D-047). Caddy sertifikayı
otomatik alır.

## 7. Doğrula

- Tarayıcıda: **https://app.joblyfit.com/app** → yeni tasarım açılmalı.
- Loglar: `docker compose -f docker-compose.prod.yml logs -f app`

---

## Sonra

- **tr.jooble.org + Careerjet kaydı:** "Website" = https://app.joblyfit.com.
  Anahtar gelince `.env.prod`'a yaz, `docker compose -f docker-compose.prod.yml up -d`
  ile yeniden başlat → Türkiye ilanları akar.
- **Güncelleme:** kodu tekrar `rsync`'le, sonra `... up -d --build`.
- **Not — auth yok (tek kiracı):** Şu an bütün ziyaretçiler aynı profilleri
  paylaşır. Demo/kayıt için sorun değil; gerçek çok-kullanıcılı launch öncesi
  auth eklenmeli (ayrı milestone).
- **Yedek:** profiller `profiles` volume'unda. Önemliyse
  `docker run --rm -v iseuygun_profiles:/d -v $PWD:/b alpine tar czf /b/profiles.tgz /d`.
