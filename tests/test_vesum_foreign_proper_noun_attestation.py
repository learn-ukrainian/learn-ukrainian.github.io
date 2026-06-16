from __future__ import annotations

import pytest

from scripts.build import linear_pipeline


def _vesum_rejects_all(words: list[str]) -> dict[str, list[dict[str, str]]]:
    return {word: [] for word in words}


def _gate(text: str, *, level: str = "folk") -> dict[str, object]:
    return linear_pipeline._vesum_gate(
        module_text=text,
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=_vesum_rejects_all,
        level=level,
    )


def test_folk_vesum_gate_accepts_attested_foreign_proper_nouns() -> None:
    gate = _gate("Йоль Йолем Ялда Ялду")

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["heritage_attested"] == 0
    assert gate["foreign_proper_noun_attested"] == 4
    assert set(gate["foreign_proper_noun_attested_words"]) == {
        "Йолем",
        "Йоль",
        "Ялда",
        "Ялду",
    }


def test_folk_vesum_gate_treats_attested_foreign_proper_nouns_consistently() -> None:
    gate = _gate("Сатурналії Йоль")

    assert gate["passed"] is True
    assert gate["missing"] == []
    assert gate["foreign_proper_noun_attested"] == 2
    assert set(gate["foreign_proper_noun_attested_words"]) == {"Сатурналії", "Йоль"}


def test_folk_vesum_gate_rejects_unattested_capitalized_foreign_coinage() -> None:
    gate = _gate("Йолькове")

    assert gate["passed"] is False
    assert gate["missing"] == ["Йолькове"]
    assert gate["foreign_proper_noun_attested"] == 0


def test_folk_vesum_gate_rejects_lowercase_foreign_proper_noun_surfaces() -> None:
    gate = _gate("йоль ялда ялду")

    assert gate["passed"] is False
    assert set(gate["missing"]) == {"йоль", "ялда", "ялду"}
    assert gate["foreign_proper_noun_attested"] == 0


def test_folk_vesum_gate_rejects_invalid_foreign_proper_noun_case_forms() -> None:
    gate = _gate("Ірана Ялдаа")

    assert gate["passed"] is False
    assert set(gate["missing"]) == {"Ірана", "Ялдаа"}
    assert gate["foreign_proper_noun_attested"] == 0


def test_folk_vesum_gate_rejects_mixed_case_foreign_proper_noun_surfaces() -> None:
    gate = _gate("ЙОль ЯЛду ІРан")

    assert gate["passed"] is False
    assert set(gate["missing"]) == {"ЙОль", "ЯЛду", "ІРан"}
    assert gate["foreign_proper_noun_attested"] == 0


def test_foreign_proper_noun_fallback_does_not_apply_to_core_levels() -> None:
    gate = _gate("Йоль Ялда Ялду", level="a1")

    assert gate["passed"] is False
    assert set(gate["missing"]) == {"Йоль", "Ялда", "Ялду"}
    assert gate["foreign_proper_noun_attested"] == 0


def test_foreign_proper_noun_fallback_does_not_exempt_class_d_coinages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        linear_pipeline,
        "_resolve_folk_heritage_attested_missing",
        lambda *args, **kwargs: set(),
    )

    gate = _gate("Йоль дерево-явір першопочаток")

    assert gate["passed"] is False
    assert gate["foreign_proper_noun_attested_words"] == ["Йоль"]
    assert {"дерево-явір", "першопочаток"} <= set(gate["missing"])
