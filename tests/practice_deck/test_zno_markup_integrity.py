from __future__ import annotations

import pytest

from scripts.practice_deck.markup_integrity import (
    apply_markup_overlay,
    assert_emit_integrity,
    item_has_required_marks,
    stem_requires_markup,
    stem_requires_option_marks,
)

ZNO_457_STEM = "Однаковий звук позначають букви, виділені в кожному слові рядка"
ZNO_457_OPTIONS = [
    "бігти, поріг, злегка",
    "повість, сяйво, свічка",
    "лічба, почасти, чітко",
    "кістці, тім'я, житній",
]
ZNO_457_MARKS = [
    [{"start": 2, "end": 3, "style": "underline"}],
    [{"start": 4, "end": 5, "style": "underline"}],
    [{"start": 2, "end": 3, "style": "underline"}],
    [{"start": 3, "end": 4, "style": "underline"}],
]


def test_detector_flags_zno_457_style_stem_without_marks() -> None:
    assert stem_requires_option_marks(ZNO_457_STEM)
    assert stem_requires_markup(ZNO_457_STEM)
    assert not item_has_required_marks({"stem": ZNO_457_STEM, "options": ZNO_457_OPTIONS})


def test_apply_overlay_quarantines_markup_dependent_items_without_overlay() -> None:
    item = {"znoTaskId": "zno:457", "stem": ZNO_457_STEM, "options": ZNO_457_OPTIONS}
    enriched, reason = apply_markup_overlay(item, overlay=None)
    assert enriched is None
    assert reason == "broken_missing_markup"


def test_apply_overlay_emits_item_when_marks_present() -> None:
    item = {"znoTaskId": "zno:457", "stem": ZNO_457_STEM, "options": ZNO_457_OPTIONS}
    overlay = {"optionMarks": ZNO_457_MARKS}
    enriched, reason = apply_markup_overlay(item, overlay)
    assert reason is None
    assert enriched is not None
    assert enriched["optionMarks"] == ZNO_457_MARKS
    assert item_has_required_marks(enriched)


def test_integrity_gate_rejects_emitted_markup_dependent_items_without_marks() -> None:
    shards = {
        "phonetics": {
            "items": [{"znoTaskId": "zno:457", "stem": ZNO_457_STEM, "options": ZNO_457_OPTIONS}],
        },
    }
    with pytest.raises(RuntimeError, match="broken_missing_markup"):
        assert_emit_integrity(shards)


def test_plain_stress_stem_does_not_require_option_marks() -> None:
    stem = "На другий склад падає наголос у слові"
    assert not stem_requires_option_marks(stem)
    assert not stem_requires_markup(stem)
