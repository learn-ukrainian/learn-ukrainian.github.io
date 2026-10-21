"""Unit tests for Multi-Dictionary Entity Alignment and Decolonization Gate."""

from __future__ import annotations

from scripts.atlas.typesafe_entity_aligner import (
    AlignmentAction,
    DictionaryEntry,
    TypeSafeEntityAligner,
)


def test_authentic_decolonized_synonym_merge():
    """Verify authentic Ukrainian synonym pair is marked for merge with level 2 score."""
    aligner = TypeSafeEntityAligner(mock=True)
    entry_a = DictionaryEntry(
        headword="пилосмок",
        source="СУМ-20",
        definition="Апарат для всмоктування пилу й сміття.",
        pos="noun",
        gender="m",
    )
    entry_b = DictionaryEntry(
        headword="порохотяг",
        source="Грінченко-1907",
        definition="Прилад для втягування пилу.",
        pos="noun",
        gender="m",
    )

    result = aligner.align_entries(entry_a, entry_b)
    assert result.action == AlignmentAction.MERGE
    assert result.score_level == 2
    assert result.score_label == "same_lexical_entity"
    assert result.confidence > 0.85
    assert result.is_decolonized_preferred is True
    assert result.identical_pos_and_gender is True
    assert result.definition_semantic_match is True


def test_decolonized_vs_soviet_calque_routes_to_curator():
    """Verify pair contrasting authentic standard vs Soviet calque flags decolonization and routes to curator."""
    aligner = TypeSafeEntityAligner(mock=True)
    entry_a = DictionaryEntry(
        headword="праска",
        source="СУМ-20",
        definition="Прилад для розгладжування складок на одязі.",
        pos="noun",
        gender="f",
    )
    entry_b = DictionaryEntry(
        headword="утюг",
        source="СУМ-11",
        definition="Те саме, що праска (суржик, російська калька).",
        pos="noun",
        gender="m",
    )

    result = aligner.align_entries(entry_a, entry_b)
    assert result.action == AlignmentAction.CURATOR_REVIEW
    assert result.score_level == 1
    assert result.score_label == "related_or_polysemous_needs_curator"
    assert result.is_decolonized_preferred is True
    assert "Decolonized" in result.curator_notes


def test_alignment_result_serialization():
    """Verify dictionary serialization preserves all fields required by Atlas pipelines."""
    aligner = TypeSafeEntityAligner(mock=True)
    entry_a = DictionaryEntry(
        headword="авто",
        source="СУМ-20",
        definition="Скорочення від автомобіль.",
        pos="noun",
        gender="n",
    )
    entry_b = DictionaryEntry(
        headword="автомобіль",
        source="ВТС",
        definition="Самохідна колісна машина з двигуном.",
        pos="noun",
        gender="m",
    )

    result = aligner.align_entries(entry_a, entry_b)
    data = result.to_dict()

    assert data["candidate_a"] == "авто"
    assert data["candidate_b"] == "автомобіль"
    assert data["action"] == "merge"
    assert "probabilities" in data
    assert isinstance(data["confidence"], float)


def test_live_api_failure_does_not_mask_with_mock(monkeypatch):
    """Verify live API exceptions do NOT silently mask with fabricated mock confidence."""
    aligner = TypeSafeEntityAligner(api_key="fake-key-for-test", mock=False)
    entry_a = DictionaryEntry(headword="тест1", source="СУМ-20", definition="деф1", pos="noun")
    entry_b = DictionaryEntry(headword="тест2", source="ВТС", definition="деф2", pos="noun")

    def _mock_failure(*args, **kwargs):
        raise ConnectionError("Simulated network drop")

    monkeypatch.setattr("urllib.request.urlopen", _mock_failure)
    monkeypatch.setattr("scripts.atlas.typesafe_entity_aligner.TypeSafeClient", None)

    result = aligner.align_entries(entry_a, entry_b)
    assert result.action == AlignmentAction.CURATOR_REVIEW
    assert result.confidence == 0.0
    assert "Live TypeSafe API failure" in result.curator_notes
