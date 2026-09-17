"""Tests for TypeSafe System One Verbatim Structure Recovery & De-Hyphenation."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from scripts.projects.open_model_data.typesafe_structure_recovery import (
    BlockType,
    TypeSafeStructureRecovery,
    recover_source_text,
)


def test_dehyphenation_and_stitching() -> None:
    """Verify that mid-word broken hyphens are cleanly joined without altering words."""
    raw = """
    Українське національне відро-
    дження XIX століття мало глибо-
    ке коріння в народній культурі.
    """
    engine = TypeSafeStructureRecovery(api_key="")  # heuristic mode
    report = engine.recover(raw)

    assert report.dehyphenated_count == 2
    assert report.recovered_block_count == 1
    assert "відродження" in report.blocks[0].merged_text
    assert "глибоке" in report.blocks[0].merged_text
    assert report.character_preservation_ratio == 1.0


def test_block_classification_heuristic() -> None:
    """Verify classification of headings, exercises, and list items."""
    raw = """
    Розділ II. Синтаксис речення

    Синтаксис вивчає будову та значення словосполучень і речень.
    Це один із найважливіших розділів мовознавства.

    Вправа 12. Прочитайте текст і визначте головні члени речення.

    1. Підмет відповідає на питання хто? що?
    2. Присудок означає дію предмета.
    """
    engine = TypeSafeStructureRecovery(api_key="")
    report = engine.recover(raw)

    assert len(report.blocks) == 6
    # Block 0: Heading
    assert report.blocks[0].block_type == BlockType.HEADING
    assert "# Розділ II. Синтаксис речення" in report.rendered_markdown

    # Blocks 1 & 2: Paragraphs
    assert report.blocks[1].block_type == BlockType.PARAGRAPH
    assert report.blocks[2].block_type == BlockType.PARAGRAPH

    # Block 3: Exercise
    assert report.blocks[3].block_type == BlockType.EXERCISE
    assert "> **Вправа 12." in report.rendered_markdown

    # Blocks 4 & 5: List items
    assert report.blocks[4].block_type == BlockType.LIST_ITEM
    assert report.blocks[5].block_type == BlockType.LIST_ITEM


def test_100_percent_character_preservation() -> None:
    """Verify zero hallucinated or modified Ukrainian characters."""
    raw = """
    Тарас Шевченко народився у Моринцях.
    Його творчість стала основою сучасної
    української літературної мови.
    """
    report = recover_source_text(raw)
    assert report.character_preservation_ratio == 1.0

    # Ensure all original words are present verbatim
    original_words = set(raw.split())
    rendered_words = set(report.rendered_markdown.split())
    for w in original_words:
        assert w in rendered_words


@patch("urllib.request.urlopen")
def test_remote_api_mocking(mock_urlopen: MagicMock) -> None:
    """Verify remote TypeSafe System One Pass 1 and Pass 2 handling."""
    # Setup mock returns
    resp_pass1 = MagicMock()
    resp_pass1.read.return_value = json.dumps(
        {
            "model": "jev-latest",
            "answers": {"is_continuation": {"noul": 0.95}},
        }
    ).encode("utf-8")

    resp_pass2 = MagicMock()
    resp_pass2.read.return_value = json.dumps(
        {
            "model": "jev-latest",
            "answers": {
                "block_type": {"choice": "heading", "confidence": 0.90},
                "heading_level": {"score": 2.0, "confidence": 0.88},
            },
        }
    ).encode("utf-8")

    # Cycle responses for urlopen
    mock_urlopen.return_value.__enter__.side_effect = [resp_pass1, resp_pass2]

    engine = TypeSafeStructureRecovery(api_key="ts-fake-key")
    raw = "Тема уроку\nПродовження теми"
    report = engine.recover(raw)

    assert report.recovered_block_count == 1
    assert report.blocks[0].block_type == BlockType.HEADING
    assert report.blocks[0].heading_level == 2
    assert "## Тема уроку Продовження теми" in report.rendered_markdown
