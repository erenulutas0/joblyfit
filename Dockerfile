# İşe Uygun — üretim imajı (D-049).
#
# Uygulama saf Python'dır; derleme adımı yoktur. Tek süreç: FastAPI/uvicorn.
# İçinde ingest de koşar (151 pano + API'ler), bu yüzden çıktı **statik değildir**
# ve Cloudflare Pages gibi statik barındırmada çalışmaz — her zaman açık bir
# sunucu ister.
#
# KALICI DİSK ŞART: `.cache/` (ilan korpusu, ~76 MB) ve `.data/` (SQLite profil).
# Bunlar volume'a bağlanmazsa her yeniden başlatmada korpus yeniden çekilir
# (~250 sn) ve panolara gereksiz yük biner. Barındırıcıda bu iki yola volume ver.

FROM python:3.13-slim

# Ağ çekimi için sertifikalar; başka sistem bağımlılığı yok.
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bağımlılıklar — pyproject'lerdeki sürümlerle aynı. psycopg opsiyonel: prod'da
# SQLite yeterli (kalıcı volume ile). İstenirse ISUYGUN_DSN verip Postgres'e
# bağlanır (D-048'deki connect_timeout fallback'i korur).
RUN pip install --no-cache-dir \
    "fastapi>=0.115" "uvicorn[standard]>=0.30" "python-multipart>=0.0.9" "pypdf>=4.0"

# Kaynak. `web/` (arayüz) ve `db/` (opsiyonel Postgres şeması) dahil.
COPY services/ /app/services/
COPY web/ /app/web/
COPY db/ /app/db/

# Üç paket editable-install değil; PYTHONPATH ile koşulur (repo düzeniyle aynı).
ENV PYTHONPATH=/app/services/api/src:/app/services/core/src:/app/services/ingest/src \
    PYTHONIOENCODING=utf-8 \
    PYTHONUNBUFFERED=1

# Kalıcı yollar. Barındırıcıda volume bağla: /app/.cache ve /app/.data
VOLUME ["/app/.cache", "/app/.data"]

EXPOSE 8137

# `$PORT` verilirse ona bağlan (PaaS'ler bunu enjekte eder); yoksa 8137.
CMD ["sh", "-c", "uvicorn isuygun_api.main:app --host 0.0.0.0 --port ${PORT:-8137}"]
