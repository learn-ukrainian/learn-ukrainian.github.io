from __future__ import annotations

import pytest

import scripts.lexicon.derivational_morphology as dm
from scripts.lexicon.derivational_morphology import derivational_bases


def _bases(surface: str) -> set[str]:
    return {row["base"] for row in derivational_bases(surface)}


def test_denominal_adjective_rules_emit_full_noun_bases() -> None:
    assert "гаївка" in _bases("гаївковий")
    assert "кришталь" in _bases("кришталевий")
    assert "обряд" in _bases("обрядний")
    assert "київ" in _bases("київський")


@pytest.mark.parametrize("surface", ["веснянкова", "веснянкове", "веснянкові"])
def test_inflected_denominal_adjectives_emit_full_noun_base(surface: str) -> None:
    assert "веснянка" in _bases(surface)


def test_deverbal_adjective_rules_emit_full_infinitive_bases() -> None:
    assert "знеособлювати" in _bases("знеособлювальними")
    assert "читати" in _bases("читальний")
    assert "розподілити" in _bases("розподільний")


def test_secondary_imperfective_rule_emits_perfective_base_from_lemma() -> None:
    assert _bases("виворожувати") == {"виворожити"}
    assert _bases("виворожують") == {"виворожити"}


def test_active_participle_suffixes_are_not_rescued() -> None:
    for surface in ("получаючий", "поступаючий", "находячийся"):
        assert _bases(surface) == set()


@pytest.mark.parametrize(
    "surface,dangerous_base",
    [
        ("глазний", "глаз"),
        ("вкусний", "вкус"),
        ("слідувати", "слідити"),
        ("оказувати", "оказити"),
        ("заказувати", "заказити"),
        ("настаювати", "настаїти"),
        ("решати", "рішити"),
    ],
)
def test_russianism_leak_surfaces_do_not_emit_dangerous_bases(
    surface: str,
    dangerous_base: str,
) -> None:
    assert dangerous_base not in _bases(surface)


def test_coinages_do_not_emit_broad_stem_fragment_rescues() -> None:
    assert _bases("двохоровий") == {"двохор"}
    assert _bases("обрядознавчий") == set()
    assert _bases("городалька") == set()


def test_derivational_bases_degrades_without_morph_analyzer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dm, "_UK_MORPH_ANALYZER", None)
    monkeypatch.setattr(dm, "_UK_MORPH_ANALYZER_TRIED", True)

    assert derivational_bases("гаївковий") == []
