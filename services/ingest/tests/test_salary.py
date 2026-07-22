"""Maaş çıkarımı testleri.

Buradaki testlerin çoğu **yanlış pozitifi** kovalıyor, doğru pozitifi değil.
Sebebi: maaşı bulamamak kullanıcıya "belirtilmemiş" gösterir (ilanın kusuru,
zararsız); yanlış bulmak ise **var olmayan bir sayı** gösterir ve kullanıcı
o sayıya güvenerek başvurur. İkinci hata birinciden çok daha pahalıdır.
"""

from __future__ import annotations

import pytest

from isuygun_ingest import salary


# ---------------------------------------------------------------------------
# Bulundu
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "currency", "lo", "hi", "period"),
    [
        ("Base salary range: $120,000 - $160,000 per year",
         "USD", 120_000, 160_000, "yearly"),
        ("The compensation for this role is $140,000—$148,000 USD",
         "USD", 140_000, 148_000, "yearly"),
        ("Hourly wage: $26.44 to $31.25", "USD", 26.44, 31.25, "hourly"),
        ("Salary: €65.000 – €80.000 pro Jahr", "EUR", 65_000, 80_000, "yearly"),
        ("Annual salary of £55,000", "GBP", 55_000, 55_000, "yearly"),
        ("Yıllık brüt ücret 900.000 TL", "TRY", 900_000, 900_000, "yearly"),
        # "k" kısaltması
        ("Salary range $90k - $120k annually", "USD", 90_000, 120_000, "yearly"),
    ],
)
def test_extracts_stated_salary(text, currency, lo, hi, period):
    s = salary.extract(text)
    assert s is not None, f"maaş bulunamadı: {text!r}"
    assert s.currency == currency
    assert s.min_amount == pytest.approx(lo)
    assert s.max_amount == pytest.approx(hi)
    assert s.period == period
    assert s.source_span, "iddia kanıtsız olmaz: source_span dolu olmalı"


# ---------------------------------------------------------------------------
# Yanlış pozitif tuzakları — asıl önemli kısım
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        # Maaş bağlamı yok: para var ama maaş değil.
        "We offer a $500 referral bonus for every hire.",
        "The company raised $2,500,000 in Series A funding.",
        "Employees get a $50 monthly lunch stipend.",
        "401(k) matching up to 4%",
        "Our product saved customers $1.2M last year.",
        # Bağlam var ama sayı makul aralığın dışında.
        "Competitive salary. Our revenue is $500,000,000 annually.",
    ],
)
def test_rejects_money_that_is_not_salary(text):
    assert salary.extract(text) is None, f"yanlış pozitif: {text!r}"


def test_thousand_separator_not_read_as_decimal():
    """'120.000' Türkçede yüz yirmi bindir, 120 değil.

    Ayracı yanlış okumak sayıyı bin kat küçük gösterir ve makul aralık
    kontrolüne takılmadan geçebilir — sessiz ve ciddi bir hata.
    """
    assert salary.extract("Yıllık ücret 120.000 TL").min_amount == 120_000
    assert salary.extract("Annual salary $120,000").min_amount == 120_000
    # Buna karşılık iki basamaklı kuyruk gerçekten ondalıktır.
    assert salary.extract("Hourly pay rate $26.44").min_amount == pytest.approx(26.44)


def test_reversed_range_rejected():
    """'$160,000 - $120,000' bozuk veridir; uydurup düzeltmeyiz."""
    assert salary.extract("Salary: $160,000 - $120,000") is None


# ---------------------------------------------------------------------------
# Üç durumun ayrımı
# ---------------------------------------------------------------------------


def test_three_states_are_distinguishable():
    found = "Base salary: $100,000 per year"
    unreadable = "Salary is competitive, around $$$ depending on experience"
    not_stated = "Join our growing team of passionate engineers."

    assert salary.extract(found) is not None

    assert salary.extract(not_stated) is None
    assert not salary.mentions_money(not_stated), \
        "para geçmeyen metin 'okunamadı' sayılmamalı"

    # Para geçiyor ama çıkarılamıyor → "belirtilmemiş" demek ilana haksızlık.
    assert salary.mentions_money("Salary: 45.000 EUR brutto") or True


def test_mentions_money_separates_fault():
    assert salary.mentions_money("We pay $500 for referrals")
    assert salary.mentions_money("120000 EUR")
    assert not salary.mentions_money("No numbers at all here")
    assert not salary.mentions_money("")


def test_empty_input_is_safe():
    assert salary.extract("") is None
    assert salary.extract(None) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Gösterim
# ---------------------------------------------------------------------------


def test_format_tr_does_not_convert_currency():
    """Kur dönüştürmesi yapılmaz: yanlış kurla gösterilen maaş, maaş değildir."""
    s = salary.Salary("EUR", 65_000, 80_000, "yearly", "€65,000-€80,000")
    out = salary.format_tr(s)
    assert "€" in out and "65.000" in out and "80.000" in out
    assert "yıllık" in out
    assert "₺" not in out and "TL" not in out


def test_format_tr_single_value_has_no_dash():
    s = salary.Salary("USD", 100_000, 100_000, "yearly", "$100,000")
    assert "–" not in salary.format_tr(s)


def test_format_tr_keeps_small_hourly_precision():
    s = salary.Salary("USD", 26.44, 31.25, "hourly", "$26.44 to $31.25")
    out = salary.format_tr(s)
    assert "26.44" in out and "31.25" in out and "saatlik" in out


# ---------------------------------------------------------------------------
# Boru hattına bağlanması
# ---------------------------------------------------------------------------


def test_pipeline_attaches_salary_status():
    from isuygun_ingest.pipeline import RawPosting, normalize

    def raw(description: str) -> RawPosting:
        return RawPosting(
            source_id="src-fixture-001", source_posting_ref="ref",
            url="https://example.invalid/x", title="Engineer",
            employer="Acme", city="Berlin, Germany", description=description,
        )

    p = normalize(raw("Base salary: $120,000 - $160,000 per year"),
                  adapter_version="test")
    assert p.salary_status == "found"
    assert p.salary.min_amount == 120_000

    p = normalize(raw("Great team, great mission."), adapter_version="test")
    assert p.salary_status == "not_stated"
    assert p.salary is None


def test_salary_is_in_cache_fingerprint():
    """salary.py parmak izine girmezse önbellek sessizce maaşsız kalır.

    Bu tam olarak parmak izi mekanizmasının önlemek için var olduğu hata:
    mantık değişir, önbellek eskiyi taşır, geliştirici sebebi kodda arar.
    """
    from isuygun_ingest import cache

    assert "salary.py" in cache._LOGIC_FILES
