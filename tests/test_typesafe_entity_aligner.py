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


def test_unrelated_entities_unlinked():
    """Verify distinct concepts evaluate to level 0 (unlinked) with high confidence."""
    aligner = TypeSafeEntityAligner(mock=True)
    entry_a = DictionaryEntry(
        headword="книга",
        source="СУМ-20",
        definition="Зшите або зв'язане в одне ціле друковане видання.",
        pos="noun",
        gender="f",
    )
    entry_b = DictionaryEntry(
        headword="трактор",
        source="ВТС",
        definition="Самохідна машина на колісному або гусеничному ходу.",
        pos="noun",
        gender="m",
    )

    result = aligner.align_entries(entry_a, entry_b)
    assert result.action == AlignmentAction.UNLINKED
    assert result.score_level == 0
    assert result.score_label == "different_lexical_entity"
    assert result.confidence >= 0.90
    assert result.definition_semantic_match is False


def test_cross_dictionary_identical_headword_merge():
    """Verify identical headword across СУМ-20 and ВТС merges when senses agree."""
    aligner = TypeSafeEntityAligner(mock=True)
    entry_a = DictionaryEntry(
        headword="соловей",
        source="СУМ-20",
        definition="Маленький перелітний птах родини дроздових з гарним співом.",
        pos="noun",
        gender="m",
    )
    entry_b = DictionaryEntry(
        headword="соловей",
        source="ВТС",
        definition="Маленький перелітний співочий птах родини дроздових.",
        pos="noun",
        gender="m",
    )

    result = aligner.align_entries(entry_a, entry_b)
    assert result.action == AlignmentAction.MERGE
    assert result.score_level == 2
    assert result.confidence >= 0.90
    assert result.identical_pos_and_gender is True
    assert result.definition_semantic_match is True


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
