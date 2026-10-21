"""Tests for TypeSafe System One Verbatim Structure Recovery & De-Hyphenation."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from scripts.projects.open_model_data.typesafe_structure_recovery import (
    BlockType,
    RecoveredBlock,
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


def test_100_percent_character_preservation() -> None:
    """Verify zero hallucinated or modified Ukrainian characters."""
    raw = """
    Тарас Шевченко народився у Моринцях.
    Його творчість стала основою сучасної
    української літературної мови.
    """
    engine = TypeSafeStructureRecovery(api_key="")
    report = recover_source_text(raw, engine=engine)
    assert report.character_preservation_ratio == 1.0

    original_words = set(raw.split())
    rendered_words = set(report.rendered_markdown.split())
    for w in original_words:
        assert w in rendered_words


def test_literal_hyphen_preservation_and_soft_hyphen_handling() -> None:
    """Verify that literal hyphens are preserved and soft hyphens (U+00AD) are de-hyphenated."""
    engine = TypeSafeStructureRecovery(api_key="")

    # 1. Single character affix / identifier compound must preserve literal hyphen
    rep_literal = engine.recover("x-\nа")
    assert "x-" in rep_literal.blocks[0].merged_text
    assert rep_literal.character_preservation_ratio == 1.0

    # 2. Compound prefix (фізико-) must preserve literal hyphen
    rep_compound = engine.recover("фізико-\nматематичний факультет")
    assert "фізико-" in rep_compound.blocks[0].merged_text
    assert rep_compound.character_preservation_ratio == 1.0

    # 3. Unicode soft hyphen (\u00ad) must be de-hyphenated cleanly
    rep_soft = engine.recover("відро\u00ad\nдження культури")
    assert "відродження" in rep_soft.blocks[0].merged_text
    assert rep_soft.character_preservation_ratio == 1.0


def test_character_preservation_detects_tampering() -> None:
    """Preservation audit must check character identity, rejecting substitutions and length illusions."""
    # Length equal but different characters ("abc" vs "xyz")
    ratio = TypeSafeStructureRecovery._calculate_preservation(
        "abc", [RecoveredBlock(1, ["abc"], "xyz")], 0
    )
    assert ratio == 0.0

    # Unauthorized deletion of character
    ratio_del = TypeSafeStructureRecovery._calculate_preservation(
        "словник", [RecoveredBlock(1, ["словник"], "слово")], 0
    )
    assert ratio_del < 1.0


@patch("urllib.request.urlopen")
def test_remote_api_mocking_single(mock_urlopen: MagicMock) -> None:
    """Verify single-call remote TypeSafe System One Pass 1 and Pass 2 handling."""
    resp_pass1 = MagicMock()
    resp_pass1.read.return_value = json.dumps(
        {
            "model": "jev-latest",
            "answers": {"is_continuation": {"type": "noul", "noul": 0.95}},
        }
    ).encode("utf-8")

    resp_pass2 = MagicMock()
    resp_pass2.read.return_value = json.dumps(
        {
            "model": "jev-latest",
            "answers": {
                "block_type": {"type": "choice", "choice": "heading", "confidence": 0.90},
                "heading_level": {"type": "score", "score": 1.0, "confidence": 0.88},
            },
        }
    ).encode("utf-8")

    mock_urlopen.return_value.__enter__.side_effect = [resp_pass1, resp_pass2]

    engine = TypeSafeStructureRecovery(api_key="ts-fake-key", batch_size=1)
    raw = "Тема уроку\nПродовження теми"
    report = engine.recover(raw)

    assert report.recovered_block_count == 1
    assert report.blocks[0].block_type == BlockType.HEADING
    assert report.blocks[0].heading_level == 2
    assert "## Тема уроку Продовження теми" in report.rendered_markdown
    assert engine.api_calls >= 2
