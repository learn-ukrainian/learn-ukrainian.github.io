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


def test_casefolded_fallback_casing_accepts_sentence_initial_hyphenated_compound() -> None:
    """Sentence-initial hyphenation is one capital; later segment capitals are not.

    «Кобзарсько-Лірницький» stays valid only because each hyphen segment is
    already title case. The sentence-initial rule does not decide that form.
    """
    valid = linear_pipeline._vesum_casefolded_fallback_casing_is_valid
    proper = linear_pipeline._is_titlecase_ukrainian_proper_noun_surface

    assert valid("Кобзарсько-лірницький") is True
    assert valid("кобзарсько-лірницький") is True
    assert valid("Івано-Франківськ") is True
    assert proper("Кобзарсько-Лірницький") is True
    assert valid("Кобзарсько-Лірницький") is True
    assert valid("ІРан") is False
    assert valid("ЙОль") is False
    assert valid("ГАГілка") is False
    assert valid("ІРАН") is False
    assert valid("кобзарсько-Лірницький") is False


def _write_fixture_heritage(path: Path, lemma: str | None) -> None:
    if lemma is None:
        path.write_text("attestations: []\n", encoding="utf-8")
        return
    path.write_text(
        "attestations:\n"
        f"  - lemma: {lemma}\n"
        "    is_russianism: false\n"
        "    citations:\n"
        "      - dictionary_slug: fixture\n"
        f"        url: https://slovnyk.me/dict/fixture/{lemma}\n",
        encoding="utf-8",
    )


def test_folk_vesum_gate_fixture_accepts_sentence_initial_hyphenated_compound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """«Кобзарсько-лірницький» passes when the fixture heritage index attests it.

    Fixture VESUM has no row for the compound or its parts (VESUM itself has
    no whole-word entry either). An empty index leaves the surface missing.
    A capital after the lowercase first segment stays missing (#9344).
    """
    passage = "Кобзарсько-лірницький дерево."
    with _fixture_vesum_gate(tmp_path, monkeypatch) as (fixture, gate):
        parts = ["кобзарсько-лірницький", "кобзарсько", "кобзарський", "лірницький"]
        assert verify_words(parts, db_path=fixture) == {word: [] for word in parts}

        empty_index = tmp_path / "empty-heritage.yaml"
        _write_fixture_heritage(empty_index, None)
        monkeypatch.setattr(linear_pipeline, "FOLK_HERITAGE_ATTESTATIONS_PATH", empty_index)
        unattested = gate(passage)
        assert unattested["passed"] is False
        assert unattested["missing"] == ["Кобзарсько-лірницький"]
        assert unattested["heritage_attested"] == 0

        heritage_index = tmp_path / "heritage.yaml"
        _write_fixture_heritage(heritage_index, "кобзарсько-лірницький")
        monkeypatch.setattr(linear_pipeline, "FOLK_HERITAGE_ATTESTATIONS_PATH", heritage_index)

        accepted = gate(passage)
        assert accepted["passed"] is True
        assert accepted["missing"] == []
        assert accepted["heritage_attested_words"] == ["Кобзарсько-лірницький"]

        lowercase = gate("кобзарсько-лірницький дерево")
        assert lowercase["passed"] is True
        assert lowercase["missing"] == []
        assert lowercase["heritage_attested_words"] == ["кобзарсько-лірницький"]

        internal_capital = gate("кобзарсько-Лірницький дерево")
        assert internal_capital["passed"] is False
        assert internal_capital["missing"] == ["кобзарсько-Лірницький"]
        assert internal_capital["heritage_attested_words"] == []


def _write_fixture_foreign_attestations(path: Path) -> None:
    path.write_text(
        "attestations:\n"
        "  - lemma: Йоль\n"
        "    forms: [Йоль, Йолем]\n"
        "    wikipedia_urls: ['https://uk.wikipedia.org/wiki/Йоль']\n",
        encoding="utf-8",
    )


@contextmanager
def _fixture_foreign_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    heritage_lemma: str | None = None,
) -> Iterator[Callable[..., dict[str, object]]]:
    """Fixture VESUM, foreign attestations and heritage index; no local databases."""
    foreign_index = tmp_path / "foreign.yaml"
    _write_fixture_foreign_attestations(foreign_index)
    monkeypatch.setattr(linear_pipeline, "FOREIGN_PROPER_NOUN_ATTESTATIONS_PATH", foreign_index)
    heritage_index = tmp_path / "heritage.yaml"
    _write_fixture_heritage(heritage_index, heritage_lemma)
    monkeypatch.setattr(linear_pipeline, "FOLK_HERITAGE_ATTESTATIONS_PATH", heritage_index)
    with _fixture_vesum_gate(tmp_path, monkeypatch) as (_fixture, gate):
        yield gate


@pytest.mark.parametrize("level", ["folk", "bio", "hist"])
@pytest.mark.parametrize(
    ("text", "malformed"),
    [
        ("ЙОль Йоль", "ЙОль"),
        ("Йоль ЙОль", "ЙОль"),
        ("ЙОль **Йоль**", "ЙОль"),
        ("ЙОЛЬ Йоль", "ЙОЛЬ"),
        ("йоль Йоль", "йоль"),
    ],
)
def test_foreign_attestation_does_not_excuse_sibling_with_other_casing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    level: str,
    text: str,
    malformed: str,
) -> None:
    """An attested «Йоль» must not carry «ЙОль» through the shared key (#9368).

    The foreign path attests title-case surfaces only, so each surface is
    judged on its own. «ЙОль» alone was already rejected; beside «Йоль» it
    used to pass with both surfaces listed as attested.
    """
    with _fixture_foreign_gate(tmp_path, monkeypatch) as gate:
        result = gate(text, level=level)

    assert result["passed"] is False
    assert result["missing"] == [malformed]
    assert malformed not in result["foreign_proper_noun_attested_words"]
    assert result["foreign_proper_noun_attested"] == 1
    assert result["heritage_attested_words"] == []


@pytest.mark.parametrize("level", ["folk", "bio", "hist"])
def test_foreign_attestation_keeps_valid_forms_attested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    level: str,
) -> None:
    with _fixture_foreign_gate(tmp_path, monkeypatch) as gate:
        result = gate("Йоль **Йолем** Йолем дерево", level=level)

    assert result["passed"] is True
    assert result["missing"] == []
    assert result["foreign_proper_noun_attested_words"] == ["**Йолем**", "Йоль"]
    assert result["heritage_attested_words"] == []


def test_foreign_attestation_leaves_unattested_sibling_to_later_fallbacks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sibling the foreign path does not attest keeps its key open (#9368).

    With «йоль» in the heritage index, the lowercase surface is accepted by the
    heritage fallback on its own merits, while «ЙОль» stays rejected on folk.
    """
    with _fixture_foreign_gate(tmp_path, monkeypatch, heritage_lemma="йоль") as gate:
        lowercase = gate("йоль Йоль")
        malformed = gate("йоль ЙОль Йоль")

    assert lowercase["passed"] is True
    assert lowercase["missing"] == []
    assert lowercase["foreign_proper_noun_attested_words"] == ["Йоль"]
    assert lowercase["heritage_attested_words"] == ["йоль"]

    assert malformed["passed"] is False
    assert malformed["missing"] == ["ЙОль"]
    assert malformed["foreign_proper_noun_attested_words"] == ["Йоль"]
    assert malformed["heritage_attested_words"] == ["йоль"]
