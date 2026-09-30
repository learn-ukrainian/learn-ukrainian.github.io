from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from scripts.build import linear_pipeline
from scripts.lexicon.heritage_classifier import _normalize_word, _vesum_attestation
from scripts.verification.vesum import close_vesum_conn, verify_words


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


def test_folk_vesum_gate_rejects_mixed_case_foreign_proper_noun_surfaces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Corpus-absent boundary: the classifier is unavailable, so nothing is
    # heritage-attested. The fixture-VESUM test below covers the corpus-present
    # path where capitalization would otherwise accept «ІРан» (#9344).
    monkeypatch.setattr(linear_pipeline, "_engine_classifies_authentic", lambda _candidate: False)
    monkeypatch.setattr(linear_pipeline, "_engine_flags_russianism", lambda _candidate: False)

    gate = _gate("ЙОль ЯЛду ІРан")

    assert gate["passed"] is False
    assert set(gate["missing"]) == {"ЙОль", "ЯЛду", "ІРан"}
    assert gate["foreign_proper_noun_attested"] == 0


def _write_fixture_vesum(path: Path) -> None:
    """Minimal forms table. Tags match VESUM for «Іран» and «дерево»."""
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        connection.executemany(
            "INSERT INTO forms (word_form, lemma, pos, tags) VALUES (?, ?, ?, ?)",
            [
                ("Іран", "Іран", "noun", "noun:inanim:m:v_naz:prop:geo"),
                ("Іран", "Іран", "noun", "noun:inanim:m:v_zna:prop:geo"),
                ("дерево", "дерево", "noun", "noun:inanim:n:v_naz"),
                ("дерево", "дерево", "noun", "noun:inanim:n:v_zna"),
                ("дерево", "дерево", "noun", "noun:inanim:n:v_kly"),
            ],
        )
        connection.commit()
    finally:
        connection.close()


@contextmanager
def _fixture_vesum_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[Path, Callable[..., dict[str, object]]]]:
    """Gate backed only by the fixture VESUM. No data/sources.db or data/vesum.db."""
    fixture = tmp_path / "vesum.db"
    _write_fixture_vesum(fixture)

    def classify_from_fixture(form: str, *_args: object, **_kwargs: object) -> dict[str, object]:
        vesum = _vesum_attestation(_normalize_word(form), surface=True, vesum_db_path=fixture)
        if not vesum:
            return {"classification": "unknown", "is_russianism": False}
        return {"classification": "standard", "is_russianism": False, "vesum_attested": True}

    monkeypatch.setattr(
        "scripts.lexicon.heritage_classifier.classify_surface_form",
        classify_from_fixture,
    )

    def verify(words: list[str]) -> dict[str, list[dict[str, str]]]:
        return verify_words(words, db_path=fixture)

    def gate(text: str, *, level: str = "folk") -> dict[str, object]:
        return linear_pipeline._vesum_gate(
            module_text=text,
            activities=[],
            vocabulary=[],
            resources=[],
            verify_words_fn=verify,
            level=level,
        )

    try:
        yield fixture, gate
    finally:
        close_vesum_conn()


def test_folk_vesum_gate_fixture_vesum_rejects_mixed_case_proper_noun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """«ІРан» must not inherit the VESUM lemma «Іран» through casefolding (#9344).

    The fixture is the only dictionary. No data/sources.db or data/vesum.db.
    """
    with _fixture_vesum_gate(tmp_path, monkeypatch) as (fixture, gate):
        # The real classifier capitalizes a casefolded miss. Pin that mechanism:
        # without the gate's casing check, «ІРан» would be heritage_attested.
        capitalized = _vesum_attestation(_normalize_word("ІРан"), surface=True, vesum_db_path=fixture)
        assert capitalized is not None
        assert "Іран" in str(capitalized.get("ref"))

        rejected = gate("ІРан ЙОль ЯЛду")
        assert rejected["passed"] is False
        assert set(rejected["missing"]) == {"ІРан", "ЙОль", "ЯЛду"}
        assert rejected["heritage_attested"] == 0
        assert rejected["heritage_attested_words"] == []

        accepted_proper = gate("Іран")
        assert accepted_proper["passed"] is True
        assert accepted_proper["missing"] == []
        assert accepted_proper["heritage_attested"] == 0

        common = gate("дерево Дерево")
        assert common["passed"] is True
        assert common["missing"] == []
        assert common["heritage_attested"] == 0

        allowlisted = gate("гагілка Гагілка")
        assert allowlisted["passed"] is True
        assert allowlisted["missing"] == []
        assert set(allowlisted["heritage_attested_words"]) == {"гагілка", "Гагілка"}

        mixed_allowlisted = gate("ГАГілка")
        assert mixed_allowlisted["passed"] is False
        assert mixed_allowlisted["missing"] == ["ГАГілка"]
        assert mixed_allowlisted["heritage_attested"] == 0

        mixed_with_valid = gate("гагілка ГАГілка")
        assert mixed_with_valid["passed"] is False
        assert mixed_with_valid["missing"] == ["ГАГілка"]
        assert mixed_with_valid["heritage_attested_words"] == ["гагілка"]

        sibling = gate("ІРан Іран дерево")
        assert sibling["passed"] is False
        assert sibling["missing"] == ["ІРан"]
        assert "ІРан" not in sibling["heritage_attested_words"]


@pytest.mark.parametrize(
    "text",
    [
        "ІРан Іран",
        "ІРан **Іран**",
        "ІРан Іра́н",
    ],
)
def test_folk_vesum_gate_fixture_rejects_malformed_casing_beside_sibling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    text: str,
) -> None:
    """A valid sibling must not hide «ІРан», including a decorated sibling (#9344).

    Plain «Іран», bold «**Іран**», and stressed «Іра́н» each share the lowercase
    key. Decoration matching has to keep «ІРан» so the casing check can reject it.
    """
    with _fixture_vesum_gate(tmp_path, monkeypatch) as (_fixture, gate):
        rejected = gate(text)

    assert rejected["passed"] is False
    assert rejected["missing"] == ["ІРан"]
    assert rejected["heritage_attested"] == 0


@pytest.mark.parametrize("level", ["bio", "hist"])
@pytest.mark.parametrize(
    ("text", "heritage_words"),
    [
        ("ІРан", ["ІРан"]),
        ("ІРан Іран", []),
        ("ІРан **Іран**", []),
        ("ІРан Іра́н", []),
        ("ГАГілка", ["ГАГілка"]),
        ("дерево Дерево", []),
    ],
)
def test_bio_and_hist_vesum_gate_keeps_casefold_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    level: str,
    text: str,
    heritage_words: list[str],
) -> None:
    """The #9344 casing rejection is folk-only. Bio and hist keep the prior result."""
    with _fixture_vesum_gate(tmp_path, monkeypatch) as (_fixture, gate):
        result = gate(text, level=level)

    assert result["passed"] is True
    assert result["missing"] == []
    assert result["heritage_attested_words"] == heritage_words


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
