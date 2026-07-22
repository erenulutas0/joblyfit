"""Profil kalıcılığı.

Kalıcılık sessiz bir güvenlik yüzeyi açar: veritabanındaki bir değer, kod
katmanındaki bütün kontrollerden **sonra** okunur. Bir alanın `verified` olarak
geri gelmesi D-012'nin tamamını atlatabilir. Buradaki testler bu yüzeyi kapatır.
"""

from __future__ import annotations

import pytest

from isuygun_core.domain import CareerProfile, ProfileFact
from isuygun_api.storage import (
    MemoryProfileStore,
    SqliteProfileStore,
    _as_verification,
    open_store,
)


@pytest.fixture()
def store(tmp_path):
    s = SqliteProfileStore(path=tmp_path / "p.db")
    yield s
    s.close()


def _profile(**kw):
    return CareerProfile(profile_id="local", **kw)


def test_profile_survives_reopen(tmp_path):
    """Asıl amaç: süreç kapanınca profil kaybolmasın."""
    path = tmp_path / "p.db"
    s1 = SqliteProfileStore(path=path)
    s1.save(_profile(
        occupation_ids=("Yazılım ve veri",),
        facts=(ProfileFact(key="python", category="skill",
                           verification="user_asserted", years=5.0),),
    ))
    s1.close()

    s2 = SqliteProfileStore(path=path)
    p = s2.load("local")
    s2.close()

    assert p.occupation_ids == ("Yazılım ve veri",)
    assert p.facts[0].key == "python" and p.facts[0].years == 5.0


def test_save_is_a_full_replace_not_a_merge(store):
    """Silinen alan veritabanında kalmamalı.

    Kısmi güncelleme, kullanıcının kaldırdığı bir belgenin sessizce yaşamaya
    devam etmesine yol açardı — ve o belge bir gate alanıysa eşleşmeyi etkiler.
    """
    store.save(_profile(facts=(
        ProfileFact(key="a", category="skill", verification="user_asserted"),
        ProfileFact(key="b", category="skill", verification="user_asserted"),
    )))
    store.save(_profile(facts=(
        ProfileFact(key="a", category="skill", verification="user_asserted"),
    )))
    assert [f.key for f in store.load("local").facts] == ["a"]


def test_unknown_verification_value_falls_back_to_unverified():
    """Veritabanından gelen tanınmayan değer **en güvenli** duruma düşer.

    Sessizce `verified` kabul etmek, D-012'nin gate mantığını veritabanı
    üzerinden atlatılabilir yapardı.
    """
    assert _as_verification("verified") == "verified"
    assert _as_verification("user_asserted") == "user_asserted"
    assert _as_verification("VERIFIED") == "unverified"
    assert _as_verification("admin") == "unverified"
    assert _as_verification("") == "unverified"


def test_tampered_verification_does_not_pass_the_gate(store):
    """Veritabanına elle yazılmış bozuk değer gate'i geçemez."""
    store.save(_profile(facts=(
        ProfileFact(key="license_ce", category="license", verification="verified"),
    )))
    store._db.execute(
        "UPDATE profile_fact SET verification = 'yes' WHERE key = 'license_ce'"
    )
    store._db.commit()

    fact = store.load("local").facts[0]
    assert fact.verification == "unverified"
    assert fact.counts_as_present is False, "gate alanı doğrulanmadan geçti"


def test_verified_gate_field_round_trips(store):
    """Meşru `verified` değeri korunmalı — aşırı temkinli olmak da hata olur."""
    store.save(_profile(facts=(
        ProfileFact(key="src", category="license", verification="verified"),
    )))
    assert store.load("local").facts[0].counts_as_present is True


def test_missing_profile_returns_empty_not_error(store):
    p = store.load("henuz-yok")
    assert p.facts == () and p.occupation_ids == ()


def test_cv_suggestions_are_stored_apart_from_profile(store):
    """Öneriler profil verisi DEĞİLDİR; ayrı tabloda durur (T-016)."""
    store.save_suggestions("local", [{"key": "python", "label": "Python"}])
    assert store.load("local").facts == (), "öneri profile sızdı"
    assert store.load_suggestions("local")[0]["key"] == "python"


def test_suggestions_are_replaced_not_appended(store):
    store.save_suggestions("local", [{"key": "a"}, {"key": "b"}])
    store.save_suggestions("local", [{"key": "a"}])
    assert [s["key"] for s in store.load_suggestions("local")] == ["a"]


def test_open_store_falls_back_to_memory_when_path_unusable(tmp_path):
    """Disk yazılamıyorsa uygulama çalışmaya devam etmeli — ama sessizce değil."""
    blocker = tmp_path / "blocked"
    blocker.write_text("bu bir dosya, dizin değil", encoding="utf-8")
    s = open_store(blocker / "sub" / "p.db")
    assert isinstance(s, MemoryProfileStore)


def test_memory_store_satisfies_the_same_contract():
    s = MemoryProfileStore()
    s.save(_profile(facts=(
        ProfileFact(key="x", category="skill", verification="user_asserted"),)))
    assert [f.key for f in s.load("local").facts] == ["x"]
    s.save_suggestions("local", [{"key": "y"}])
    assert s.load_suggestions("local") == [{"key": "y"}]
