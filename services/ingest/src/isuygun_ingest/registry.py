"""Source Registry — dış dünyayla tek temas kapısı.

Bu modül D-002 ve D-018'in **kod düzeyindeki zorlayıcısıdır**:

* Registry'de kayıtlı olmayan source'tan ingestion yapılamaz (FR-202).
* ``scraping_permission`` ``allowed`` değilse ağ erişimi **başlatılamaz** —
  bu bir uyarı değil, exception'dır.
* D-018 gereği MVP'de yalnızca ``fixture`` access_method çalıştırılabilir;
  gerçek kaynağa bağlanmak OPEN-09/OPEN-19 kapanmadan mümkün değildir.

Kayıtların kanıtı ve gerekçesi:
``docs/architecture/SOURCE_REGISTRY.md`` §5 ve
``docs/research/TURKEY_SOURCE_LANDSCAPE.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

ScrapingPermission = Literal["allowed", "conditional", "rejected", "unknown"]
#: "submission" = içerik bize GÖNDERİLİR, biz çekmeyiz (D-078 işveren panosu).
#: Diğer yöntemlerden kategorik olarak farklı: çekim izni sorusu hiç doğmaz.
AccessMethod = Literal["api", "feed", "structured_data", "html", "fixture",
                       "submission", "unknown"]
SourceStatus = Literal[
    "candidate", "under_review", "rejected",
    "active_limited", "active", "degraded", "suspended",
]


class PermissionError_(RuntimeError):
    """İzin durumu ağ erişimine elvermiyor."""


@dataclass(frozen=True, slots=True)
class SourceRecord:
    source_id: str
    name: str
    source_type: str
    base_url: str | None
    access_method: AccessMethod
    scraping_permission: ScrapingPermission
    policy_risk: Literal["low", "medium", "high", "unknown"]
    status: SourceStatus
    note: str = ""
    # Fixture modunda okunacak yerel dizin (D-018)
    fixture_dir: str | None = None
    # `allowed` işaretlemenin dayanağı. İzin iddiası kanıtsız yazılamaz (D-020);
    # `audit()` bunu denetler.
    permission_evidence: str = ""
    # --- kaynak başına kullanım şartları (D-023) ---
    # Kaynaklar aynı şartlarla gelmiyor: kimi geri bağlantı ister, kimi saatte
    # tek istek, kimi yeniden yayına hiç izin vermez. Bunlar kod dışında bir
    # yerde tutulursa ihlal sessizce olur.
    #: Arayüzde kaynağa görünür atıf zorunlu mu
    attribution_required: bool = False
    #: Aynı kaynağa iki çekim arasındaki asgari süre (saat)
    min_poll_hours: float = 6.0
    #: İçeriğin yeniden yayınına dair kaynağın kendi kuralı
    redistribution_policy: str = "link-only"

    @property
    def may_fetch_network(self) -> bool:
        """Ağ erişimi yalnızca açıkça izinli VE aktif kayıtlarda mümkündür.

        ``submission`` kaynakları HER ZAMAN ``False`` döner: içerik bize
        gönderiliyor, biz ondan çekmiyoruz (D-078, işveren panosu). "İzin yok"
        demek yanlış olurdu — çekilecek bir şey yok. Bu ayrım kaynak politikası
        denetiminde de karşılığını bulur: çekim izni kuralı, çekim yapmayan bir
        kaynağa uygulanmaz.
        """
        if self.access_method == "submission":
            return False
        return (
            self.scraping_permission == "allowed"
            and self.status in ("active", "active_limited")
        )


# T-003 çıktısı. Hiçbiri `allowed` DEĞİL — bu kasıtlıdır (bkz. TURKEY_SOURCE_LANDSCAPE §13).
REGISTRY: dict[str, SourceRecord] = {
    r.source_id: r
    for r in [
        SourceRecord(
            source_id="src-tr-001", name="İşin Olsun", source_type="job_board",
            base_url="https://isinolsun.com", access_method="feed",
            scraping_permission="conditional", policy_risk="high",
            status="under_review",
            note="Wave 1 adayı. robots izinli; üyelik sözleşmesi §4.12 reuse kısıtı "
                 "→ yazılı izin gerekiyor (OPEN-19).",
        ),
        SourceRecord(
            source_id="src-tr-006", name="İŞKUR e-Şube", source_type="government_portal",
            base_url="https://esube.iskur.gov.tr", access_method="html",
            scraping_permission="conditional", policy_risk="medium",
            status="under_review",
            note="Wave 2 adayı. robots izinli; reuse lisansı yok.",
        ),
        SourceRecord(
            source_id="src-tr-008", name="Kamu İlan (SBB)", source_type="government_portal",
            base_url="https://kamuilan.sbb.gov.tr", access_method="html",
            scraping_permission="conditional", policy_risk="low",
            status="candidate",
            note="Wave 2 adayı. D-015 listing-only; hacim düşük.",
        ),
        SourceRecord(
            source_id="src-tr-014", name="Indeed Türkiye", source_type="job_board",
            base_url="https://tr.indeed.com", access_method="html",
            scraping_permission="rejected", policy_risk="high", status="rejected",
            note="robots ilan yollarını açıkça disallow ediyor (AI bot'ları dahil).",
        ),
        SourceRecord(
            source_id="src-tr-015", name="LinkedIn", source_type="job_board",
            base_url="https://www.linkedin.com", access_method="html",
            scraping_permission="rejected", policy_risk="high", status="rejected",
            note="robots.txt başında otomatik erişim açıkça yasak + login wall.",
        ),
        # D-018: geliştirme ve test için tek çalıştırılabilir kaynak.
        SourceRecord(
            source_id="src-fixture-001", name="Fixture Korpusu (geliştirme)",
            source_type="fixture", base_url=None, access_method="fixture",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            fixture_dir="fixtures/isinolsun_like",
            note="Sentetik ilanlar. Gerçek kaynak DEĞİLDİR; şema ve pipeline "
                 "doğrulaması için kullanılır (D-018).",
        ),
        # ------------------------------------------------------------------
        # D-020 — ATS public job board API'leri.
        # Bunlar şirketlerin kendi kariyer sayfalarını kurmaları için yayınladığı
        # kimlik doğrulaması istemeyen public uçlardır. İzin kanıtı `permission_evidence`
        # alanındadır; robots.txt kayıtları 2026-07-21'de doğrulanmıştır.
        # ------------------------------------------------------------------
        SourceRecord(
            source_id="src-ats-lever", name="Lever public job board API",
            source_type="ats_api", base_url="https://api.lever.co", access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "api.lever.co/robots.txt → 'User-agent: * / Allow: / / Crawl-delay: 1' "
                "(doğrulandı 2026-07-21). Uç kimlik doğrulaması istemez ve yanıt, "
                "ilanın kendi sayfasına giden hostedUrl taşır."
            ),
            note="Crawl-delay: 1 uygulanıyor. Yalnızca kayıtlı board slug'ları çekilir.",
        ),
        SourceRecord(
            source_id="src-ats-greenhouse", name="Greenhouse job board API",
            source_type="ats_api", base_url="https://boards-api.greenhouse.io",
            access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "boards-api.greenhouse.io/robots.txt → yalnızca '/embed/' disallow; "
                "'/v1/boards/' serbest (doğrulandı 2026-07-21). Resmî doküman uçların "
                "amacını 'build careers pages with a unique look and feel' diye tanımlar: "
                "developers.greenhouse.io/job-board.html"
            ),
        ),
        SourceRecord(
            source_id="src-ats-ashby", name="Ashby public posting API",
            source_type="ats_api", base_url="https://api.ashbyhq.com", access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "api.ashbyhq.com/posting-api/job-board/<firma> kimlik doğrulaması "
                "istemez ve şirketlerin kendi kariyer sayfalarını beslemesi için "
                "yayınlanır; yanıt ilanın kendi sayfasına giden jobUrl taşır "
                "(doğrulandı 2026-07-21)."
            ),
        ),
        SourceRecord(
            source_id="src-ats-recruitee", name="Recruitee public offers API",
            source_type="ats_api", base_url="https://*.recruitee.com", access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "<firma>.recruitee.com/robots.txt → yalnızca '/v/' disallow; "
                "'/api/offers/' serbest (doğrulandı 2026-07-21)."
            ),
        ),
        # ------------------------------------------------------------------
        # D-023 — kayıt gerektirmeyen public iş ilanı API'leri.
        # Her birinin şartı farklıdır; farklar aşağıdaki alanlarda tutulur.
        # ------------------------------------------------------------------
        SourceRecord(
            source_id="src-api-arbeitsagentur",
            name="Arbeitsagentur Jobsuche (Almanya İş Ajansı)",
            source_type="government_portal",
            base_url="https://rest.arbeitsagentur.de", access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "Resmî açık API; jobsuche.api.bund.dev'de dokümante. Kimlik "
                "doğrulaması yerine yayınlanmış statik anahtar kullanılır "
                "(kullanıcıya özel değildir). Yanıt ilanın kendi sayfasına giden "
                "externeUrl / jobdetail bağlantısı taşır (doğrulandı 2026-07-21)."
            ),
            min_poll_hours=6.0, redistribution_policy="link-only",
            note="Mavi yaka kapsamı en geniş kaynak. Liste ucu açıklama metni "
                 "vermez; şart çıkarımı başlık + meslek adıyla sınırlıdır.",
        ),
        SourceRecord(
            source_id="src-api-arbeitnow", name="Arbeitnow Job Board API",
            source_type="aggregator", base_url="https://www.arbeitnow.com",
            access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "arbeitnow.com/blog/job-board-api — public, auth'suz, kullanım "
                "için yayınlanmış; karşılığında ilana geri bağlantı isteniyor "
                "(doğrulandı 2026-07-21)."
            ),
            attribution_required=True, min_poll_hours=6.0,
            redistribution_policy="link-back-required",
        ),
        SourceRecord(
            source_id="src-api-themuse", name="The Muse Public Jobs API",
            source_type="job_board", base_url="https://www.themuse.com",
            access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "themuse.com/developers/api/v2 — key'siz saatte 500 istek. "
                "ToS §3.4 ilana geri bağlantıyı ZORUNLU kılar (doğrulandı "
                "2026-07-21). Not: yaygın kopyalanan api.themuse.com adresi ölü; "
                "doğrusu www.themuse.com/api/public/jobs."
            ),
            attribution_required=True, min_poll_hours=6.0,
            redistribution_policy="link-back-required",
        ),
        SourceRecord(
            source_id="src-api-himalayas", name="Himalayas (uzaktan çalışma)",
            source_type="job_board", base_url="https://himalayas.app",
            access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "himalayas.app/jobs/api — public, auth'suz; atıf isteniyor. "
                "Yanıt expiryDate taşır, süresi geçmiş ilanlar çekimde ayıklanır "
                "(doğrulandı 2026-07-21)."
            ),
            attribution_required=True, min_poll_hours=6.0,
            redistribution_policy="link-back-required",
        ),
        SourceRecord(
            source_id="src-api-jooble", name="Jooble (Türkiye toplayıcı)",
            source_type="aggregator", base_url="https://jooble.org",
            access_method="api",
            scraping_permission="allowed", policy_risk="low", status="active_limited",
            permission_evidence=(
                "jooble.org/api/about — resmî public REST API. Amacı belgede "
                "açıkça 'webmaster'ların Jooble sonuçlarını kendi sitesinde "
                "göstermesi' olarak tanımlı; her ilan kaynağa `link` taşır. "
                "D-041 ÇÖZÜLDÜ (2026-07-24): Jooble ülke sitesi başına AYRI "
                "indeks ve AYRI anahtar kullanır. tr.jooble.org anahtarı alındı "
                "ve Türkiye ilanlarını veriyor (5441 kanonik ilan). Doğrulama: "
                "aynı anahtar jooble.org'da 403, uluslararası anahtar ise "
                "tr.jooble.org'da 403 — anahtar host'la eşleşmeli "
                "(ISUYGUN_JOOBLE_HOST). ÖLÇÜLEN SINIRLAR: ResultOnPage tavanı "
                "100 (500 istenirse sessizce 20'ye düşer); sayfalama ~10 sayfada "
                "kesilir, yani tek sorgu en fazla ~1000 ilan verir; "
                "keywords='' + location='Türkiye' totalCount=11338 (tüm ülke "
                "indeksi). TÜRKÇE KARAKTER KRİTİK: 'yazilim' 10 ilan, 'yazılım' "
                "985 ilan. Anahtarın 500 istek sınırı var (dönem belirsiz; "
                "Jooble e-postasına yanıt yazarak artırılabiliyor) — bu yüzden "
                "min_poll_hours=12 ve adaptörde max_requests bütçesi var. "
                "NOT: anahtar alınırken Jooble API kullanım "
                "şartları kullanıcı tarafından onaylanmalıdır (hukuki görüş değil)."
            ),
            attribution_required=True, min_poll_hours=12.0,
            redistribution_policy="link-back-required",
        ),
        SourceRecord(
            source_id="src-direct-employer",
            name="İşveren doğrudan girişi (JoblyFit panosu)",
            source_type="direct", base_url="https://app.joblyfit.com",
            access_method="submission",
            # Burada "izin" bir robots.txt yorumu DEĞİL: içeriği işverenin
            # kendisi bize gönderiyor ve gönderim eylemi yayımlama iznidir.
            # Kayıttaki diğer kaynaklardan kategorik olarak farklı; bu yüzden
            # ayrı bir access_method ile duruyor.
            scraping_permission="allowed", policy_risk="low", status="active",
            permission_evidence=(
                "D-078: içerik kazınmıyor, işveren gönderim formuyla KENDİSİ "
                "gönderiyor; gönderim yayımlama iznidir. Hesap/oturum YOK — "
                "e-posta altyapısı olmadığı için işverenin kimliği "
                "doğrulanamıyor, dolayısıyla self-servis yayın da yok: her "
                "gönderim MODERASYON kuyruğuna düşer ve onaylanmadan korpusa "
                "girmez. Ayrımcı ifade (hard) burada BLOKLANIR, yalnızca "
                "işaretlenmez — üçüncü taraf akışlarında yayımcı biz değiliz, "
                "burada biziz. Şart sayısı ölçülen asıl kazançtır: aggregator "
                "ilan başına ~1,3 şart veriyor, yapılandırılmış giriş 5-6 "
                "veriyor ve bantlar ancak o zaman ayrışıyor. Ücret alınmıyor ve "
                "SIRALAMA SATILMIYOR: doğrudan ilanlar diğerleriyle aynı "
                "sıralama kurallarına tabidir, yalnızca kaynağı rozetle "
                "görünür. Süresi geçen ilan (son başvuru tarihi) korpustan "
                "otomatik düşer."
            ),
            attribution_required=False, min_poll_hours=0.0,
            redistribution_policy="own-content",
        ),
    ]
}

# D-020 — çekilmesine izin verilen şirket panoları.
#
# Kapsam bilinçli olarak **dar**: her slug elle doğrulanmıştır. Otomatik keşif
# yoktur; listede olmayan bir şirket çekilmez. Bu, kaynak listesinin sessizce
# büyümesini engeller.
BOARDS: tuple[tuple[str, str, str, str], ...] = (
    # (source_id, platform, slug, işveren adı)
    # ---- Türkiye ----
    ("src-ats-lever", "lever", "trendyol", "Trendyol"),
    ("src-ats-lever", "lever", "dreamgames", "Dream Games"),
    ("src-ats-lever", "lever", "iyzico", "iyzico"),
    ("src-ats-lever", "lever", "commencis", "Commencis"),
    ("src-ats-lever", "lever", "ciceksepeti", "Çiçeksepeti"),
    ("src-ats-ashby", "ashby", "biggergames", "Bigger Games"),
    ("src-ats-recruitee", "recruitee", "macellan", "Macellan"),
    # NOT (D-043): 98 Türk firması adayı 3 ATS platformunda tarandı; TR ilanı
    # taşıyan **yalnızca** bu pano çıktı. Peak Games'in Lever panosunda konum
    # alanı istihdam türüyle dolu ("Full-time"), Insider/Picus/Peak panoları
    # ABD/Avrupa ilanı taşıyor. Türk şirketleri ağırlıkla Kariyer.net ve yerel
    # ATS'ler kullanıyor — bu yol Türkiye için düşük tavanlı.
    # ---- Avrupa ----
    ("src-ats-greenhouse", "greenhouse", "adyen", "Adyen"),
    ("src-ats-greenhouse", "greenhouse", "wolt", "Wolt"),
    ("src-ats-greenhouse", "greenhouse", "sumup", "SumUp"),
    ("src-ats-greenhouse", "greenhouse", "hellofresh", "HelloFresh"),
    ("src-ats-greenhouse", "greenhouse", "celonis", "Celonis"),
    ("src-ats-greenhouse", "greenhouse", "n26", "N26"),
    ("src-ats-greenhouse", "greenhouse", "monzo", "Monzo"),
    ("src-ats-greenhouse", "greenhouse", "tide", "Tide"),
    ("src-ats-greenhouse", "greenhouse", "gocardless", "GoCardless"),
    ("src-ats-greenhouse", "greenhouse", "doctolib", "Doctolib"),
    ("src-ats-greenhouse", "greenhouse", "getyourguide", "GetYourGuide"),
    ("src-ats-greenhouse", "greenhouse", "contentful", "Contentful"),
    ("src-ats-greenhouse", "greenhouse", "dataiku", "Dataiku"),
    ("src-ats-greenhouse", "greenhouse", "algolia", "Algolia"),
    ("src-ats-greenhouse", "greenhouse", "mirakl", "Mirakl"),
    ("src-ats-greenhouse", "greenhouse", "typeform", "Typeform"),
    ("src-ats-greenhouse", "greenhouse", "cabify", "Cabify"),
    ("src-ats-greenhouse", "greenhouse", "neo4j", "Neo4j"),
    ("src-ats-lever", "lever", "spotify", "Spotify"),
    ("src-ats-lever", "lever", "qonto", "Qonto"),
    ("src-ats-lever", "lever", "swile", "Swile"),
    # ---- ABD ----
    ("src-ats-greenhouse", "greenhouse", "stripe", "Stripe"),
    ("src-ats-greenhouse", "greenhouse", "databricks", "Databricks"),
    ("src-ats-greenhouse", "greenhouse", "datadog", "Datadog"),
    ("src-ats-greenhouse", "greenhouse", "anthropic", "Anthropic"),
    ("src-ats-greenhouse", "greenhouse", "mongodb", "MongoDB"),
    ("src-ats-greenhouse", "greenhouse", "samsara", "Samsara"),
    ("src-ats-greenhouse", "greenhouse", "cloudflare", "Cloudflare"),
    ("src-ats-greenhouse", "greenhouse", "brex", "Brex"),
    ("src-ats-greenhouse", "greenhouse", "braze", "Braze"),
    ("src-ats-greenhouse", "greenhouse", "airbnb", "Airbnb"),
    ("src-ats-greenhouse", "greenhouse", "elastic", "Elastic"),
    ("src-ats-greenhouse", "greenhouse", "reddit", "Reddit"),
    ("src-ats-greenhouse", "greenhouse", "pinterest", "Pinterest"),
    ("src-ats-greenhouse", "greenhouse", "figma", "Figma"),
    ("src-ats-greenhouse", "greenhouse", "gitlab", "GitLab"),
    ("src-ats-greenhouse", "greenhouse", "twilio", "Twilio"),
    ("src-ats-greenhouse", "greenhouse", "coinbase", "Coinbase"),
    ("src-ats-greenhouse", "greenhouse", "lyft", "Lyft"),
    ("src-ats-greenhouse", "greenhouse", "klaviyo", "Klaviyo"),
    ("src-ats-greenhouse", "greenhouse", "asana", "Asana"),
    ("src-ats-greenhouse", "greenhouse", "intercom", "Intercom"),
    ("src-ats-greenhouse", "greenhouse", "instacart", "Instacart"),
    ("src-ats-greenhouse", "greenhouse", "robinhood", "Robinhood"),
    ("src-ats-greenhouse", "greenhouse", "postman", "Postman"),
    ("src-ats-greenhouse", "greenhouse", "vercel", "Vercel"),
    ("src-ats-greenhouse", "greenhouse", "gusto", "Gusto"),
    ("src-ats-greenhouse", "greenhouse", "duolingo", "Duolingo"),
    ("src-ats-greenhouse", "greenhouse", "discord", "Discord"),
    ("src-ats-greenhouse", "greenhouse", "dropbox", "Dropbox"),
    ("src-ats-greenhouse", "greenhouse", "webflow", "Webflow"),
    ("src-ats-greenhouse", "greenhouse", "calendly", "Calendly"),
    ("src-ats-lever", "lever", "palantir", "Palantir"),
    ("src-ats-ashby", "ashby", "openai", "OpenAI"),
    ("src-ats-ashby", "ashby", "harvey", "Harvey"),
    ("src-ats-ashby", "ashby", "elevenlabs", "ElevenLabs"),
    ("src-ats-ashby", "ashby", "cohere", "Cohere"),
    ("src-ats-ashby", "ashby", "ramp", "Ramp"),
    ("src-ats-ashby", "ashby", "cursor", "Cursor"),
    ("src-ats-ashby", "ashby", "perplexity", "Perplexity"),
    ("src-ats-ashby", "ashby", "linear", "Linear"),
    ("src-ats-ashby", "ashby", "posthog", "PostHog"),
    ("src-ats-ashby", "ashby", "modal", "Modal"),
    ("src-ats-ashby", "ashby", "abridge", "Abridge"),

    # ---- 2026-07-21 taraması: 121 pano tarandı, 8+ ilanı olanlar alındı.
    # Mavi yaka çeşitliliği için lojistik/perakende/üretim/sağlık dahil edildi
    # (Carvana: oto teknisyeni ve nakliye; Gopuff: depo ve dağıtım;
    #  Lucid Motors: üretim; One Medical: sağlık; Flexport: lojistik).
    ("src-ats-greenhouse", "greenhouse", "carvana", "Carvana"),
    ("src-ats-lever", "lever", "gopuff", "Gopuff"),
    ("src-ats-ashby", "ashby", "snowflake", "Snowflake"),
    ("src-ats-greenhouse", "greenhouse", "onemedical", "One Medical"),
    ("src-ats-greenhouse", "greenhouse", "lucidmotors", "Lucid Motors"),
    ("src-ats-greenhouse", "greenhouse", "natera", "Natera"),
    ("src-ats-greenhouse", "greenhouse", "roblox", "Roblox"),
    ("src-ats-greenhouse", "greenhouse", "scaleai", "Scale AI"),
    ("src-ats-greenhouse", "greenhouse", "fivetran", "Fivetran"),
    ("src-ats-greenhouse", "greenhouse", "clickhouse", "ClickHouse"),
    ("src-ats-greenhouse", "greenhouse", "riotgames", "Riot Games"),
    ("src-ats-greenhouse", "greenhouse", "flexport", "Flexport"),
    ("src-ats-ashby", "ashby", "notion", "Notion"),
    ("src-ats-greenhouse", "greenhouse", "epicgames", "Epic Games"),
    ("src-ats-ashby", "ashby", "uipath", "UiPath"),
    ("src-ats-ashby", "ashby", "plaid", "Plaid"),
    ("src-ats-greenhouse", "greenhouse", "nuro", "Nuro"),
    ("src-ats-greenhouse", "greenhouse", "justworks", "Justworks"),
    ("src-ats-greenhouse", "greenhouse", "misfitsmarket", "Misfits Market"),
    ("src-ats-greenhouse", "greenhouse", "tripadvisor", "Tripadvisor"),
    ("src-ats-ashby", "ashby", "synthesia", "Synthesia"),
    ("src-ats-greenhouse", "greenhouse", "hightouch", "Hightouch"),
    ("src-ats-ashby", "ashby", "suno", "Suno"),
    ("src-ats-greenhouse", "greenhouse", "carta", "Carta"),
    ("src-ats-greenhouse", "greenhouse", "peloton", "Peloton"),
    ("src-ats-greenhouse", "greenhouse", "twitch", "Twitch"),
    ("src-ats-greenhouse", "greenhouse", "newrelic", "New Relic"),
    ("src-ats-greenhouse", "greenhouse", "fireblocks", "Fireblocks"),
    ("src-ats-greenhouse", "greenhouse", "sweetgreen", "Sweetgreen"),
    ("src-ats-greenhouse", "greenhouse", "mercury", "Mercury"),
    ("src-ats-ashby", "ashby", "supabase", "Supabase"),
    ("src-ats-ashby", "ashby", "thumbtack", "Thumbtack"),
    ("src-ats-greenhouse", "greenhouse", "bitpanda", "Bitpanda"),
    ("src-ats-lever", "lever", "ro", "Ro"),
    ("src-ats-greenhouse", "greenhouse", "fastly", "Fastly"),
    ("src-ats-ashby", "ashby", "sentry", "Sentry"),
    ("src-ats-greenhouse", "greenhouse", "attentive", "Attentive"),
    ("src-ats-ashby", "ashby", "pleo", "Pleo"),
    ("src-ats-greenhouse", "greenhouse", "amplitude", "Amplitude"),
    ("src-ats-ashby", "ashby", "angi", "Angi"),
    ("src-ats-greenhouse", "greenhouse", "gemini", "Gemini"),
    ("src-ats-greenhouse", "greenhouse", "tanium", "Tanium"),
    ("src-ats-greenhouse", "greenhouse", "marqeta", "Marqeta"),
    ("src-ats-ashby", "ashby", "mollie", "Mollie"),
    ("src-ats-ashby", "ashby", "supercell", "Supercell"),
    ("src-ats-ashby", "ashby", "miro", "Miro"),
    ("src-ats-greenhouse", "greenhouse", "mixpanel", "Mixpanel"),
    ("src-ats-greenhouse", "greenhouse", "airtable", "Airtable"),
    ("src-ats-greenhouse", "greenhouse", "cockroachlabs", "Cockroach Labs"),
    ("src-ats-ashby", "ashby", "confluent", "Confluent"),
    ("src-ats-ashby", "ashby", "render", "Render"),
    ("src-ats-lever", "lever", "outreach", "Outreach"),
    ("src-ats-greenhouse", "greenhouse", "salesloft", "Salesloft"),
    ("src-ats-greenhouse", "greenhouse", "careem", "Careem"),
    ("src-ats-greenhouse", "greenhouse", "iterable", "Iterable"),
    ("src-ats-lever", "lever", "contentsquare", "Contentsquare"),
    ("src-ats-greenhouse", "greenhouse", "customerio", "Customer.io"),
    ("src-ats-lever", "lever", "rover", "Rover"),
    ("src-ats-lever", "lever", "angellist", "AngelList"),
    ("src-ats-ashby", "ashby", "patreon", "Patreon"),
    ("src-ats-greenhouse", "greenhouse", "thrivemarket", "Thrive Market"),
    ("src-ats-greenhouse", "greenhouse", "nintex", "Nintex"),
    ("src-ats-greenhouse", "greenhouse", "ledgy", "Ledgy"),
    ("src-ats-ashby", "ashby", "alchemy", "Alchemy"),
    ("src-ats-ashby", "ashby", "oyster", "Oyster"),
    ("src-ats-greenhouse", "greenhouse", "honeycomb", "Honeycomb"),
    ("src-ats-greenhouse", "greenhouse", "taskrabbit", "TaskRabbit"),
    ("src-ats-greenhouse", "greenhouse", "labelbox", "Labelbox"),
    ("src-ats-ashby", "ashby", "airbyte", "Airbyte"),
    ("src-ats-lever", "lever", "neon", "Neon"),
    ("src-ats-greenhouse", "greenhouse", "buildkite", "Buildkite"),
    ("src-ats-greenhouse", "greenhouse", "coursera", "Coursera"),
    ("src-ats-greenhouse", "greenhouse", "descript", "Descript"),
    ("src-ats-ashby", "ashby", "substack", "Substack"),
    ("src-ats-greenhouse", "greenhouse", "talkspace", "Talkspace"),
    ("src-ats-greenhouse", "greenhouse", "truelayer", "TrueLayer"),
    ("src-ats-greenhouse", "greenhouse", "planetscale", "PlanetScale"),
    ("src-ats-ashby", "ashby", "railway", "Railway"),
    ("src-ats-greenhouse", "greenhouse", "circleci", "CircleCI"),
    ("src-ats-greenhouse", "greenhouse", "udemy", "Udemy"),
    ("src-ats-ashby", "ashby", "unit", "Unit"),
)

def get(source_id: str) -> SourceRecord:
    if source_id not in REGISTRY:
        raise KeyError(
            f"Kayıtsız source: {source_id!r}. Registry'de olmayan kaynaktan "
            "ingestion yapılamaz (FR-202)."
        )
    return REGISTRY[source_id]


def assert_fetchable(source_id: str) -> SourceRecord:
    """Ağ erişimi başlatmadan önce çağrılır. İzin yoksa **exception atar**.

    Bu fonksiyon D-002'nin kod düzeyindeki bekçisidir. Bypass edilmesi
    gereken bir engel değil, mimarinin bir parçasıdır.
    """
    rec = get(source_id)
    if rec.access_method == "fixture":
        return rec
    if not rec.may_fetch_network:
        raise PermissionError_(
            f"{rec.name} ({rec.source_id}) için ağ erişimi başlatılamaz.\n"
            f"  scraping_permission = {rec.scraping_permission}\n"
            f"  status              = {rec.status}\n"
            f"  gerekçe             = {rec.note}\n"
            "Bu kaynağa bağlanmak için önce yazılı izin (OPEN-19) veya "
            "T-008 Conditional rubriği (OPEN-09) gerekir. "
            "Bypass edilmez — D-002."
        )
    return rec


def allowed_without_evidence() -> list[SourceRecord]:
    """`allowed` işaretli ama gerekçesi yazılmamış kayıtlar. **Boş olmalı.**

    D-018'in "hiçbir kaynağa crawl yok" maddesi D-020 ile izinli API kanalları
    için revize edildi. Kuralın yerini alan yeni denetim budur: izin iddiası
    kanıtsız yazılamaz. Bu liste boş değilse birisi bir kaynağı gerekçesiz
    açmış demektir.
    """
    return [
        r for r in REGISTRY.values()
        if r.scraping_permission == "allowed"
        and r.access_method != "fixture"
        and not r.permission_evidence.strip()
    ]


def api_sources() -> list[SourceRecord]:
    """Pano tabanlı olmayan, doğrudan sorgulanan izinli API kaynakları."""
    return [r for r in REGISTRY.values()
            if r.source_id.startswith("src-api-") and r.may_fetch_network]


def audit() -> dict[str, int]:
    """Registry sağlık denetimi (D-020)."""
    return {
        "toplam": len(REGISTRY),
        "allowed": sum(1 for r in REGISTRY.values() if r.scraping_permission == "allowed"),
        "kanitsiz_allowed": len(allowed_without_evidence()),  # 0 olmalı
        "conditional": sum(1 for r in REGISTRY.values() if r.scraping_permission == "conditional"),
        "rejected": sum(1 for r in REGISTRY.values() if r.scraping_permission == "rejected"),
        "board_sayisi": len(BOARDS),
    }
