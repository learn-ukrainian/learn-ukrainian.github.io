"""Tests for fresh build engine Part E2 immersion payload (#8414, #8431 §6/§7)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.build.fresh.immersion import (
    compute_immersion_payload,
)
from scripts.curriculum.learner_state.immersion import ImmersionError, LessonBand


def test_unsupported_band_key_fails_closed():
    """Where the contract gives no row, fail closed with unsupported_immersion_band (#8431, Finding 6)."""
    with patch("scripts.build.fresh.immersion.compute_lesson_immersion_band") as mock_band:
        mock_band.return_value = LessonBand(
            band_key="nonexistent-band",
            advisory_uk_share=(50, 50),
            module_structural={"min_uk_dialogue_lines": 1, "min_uk_example_sentences": 1, "min_vocab_entries": 1},
            source="arc_table",
            not_checked=[],
        )
        with pytest.raises(ImmersionError) as exc_info:
            compute_immersion_payload("a2", 1, 1)
        assert exc_info.value.code == "unsupported_immersion_band"
