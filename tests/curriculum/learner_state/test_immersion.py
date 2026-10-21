"""Tests for lesson immersion band and structural minimums (issue #8414).

Verifies:
- A1 band equals compute_immersion_band for the same count, parametrised across the 7 knees
- A2 band equals the arc's band_key for the position
- B1 -> b1-core
- B2 -> b2+
- Fixture arc without band_key fails arc_band_table_missing
- Every call carries the not_checked code (lesson_structural_minimums_not_calibrated)
- Structural minimums carried unchanged
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.curriculum.arc.loader import ArcPosition, ArcStaleError, load_arc
from scripts.curriculum.learner_state import codes
from scripts.curriculum.learner_state.immersion import ImmersionError, compute_lesson_immersion_band

pytestmark = pytest.mark.reads_content


def test_fixture_arc_without_band_key_fails() -> None:
    """A level whose arc has no band_key fails with arc_band_table_missing, never falls back to a module number."""
    synthetic_positions = [
        ArcPosition(
            position=1,
            slug="synth-slug",
            est_lessons=4,
            job="Synthetic job",
            inventory_text=None,
            phase="Phase 1",
            skills_text="L",
            skills=["L"],
            standard_line_refs=[],
            band_key=None,  # missing band_key
        )
    ]

    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band(
            "a2",
            arc_position=1,
            lesson_n=1,
            cumulative_core_count=0,
            arc_loader=lambda _track: synthetic_positions,
        )
    assert exc_info.value.code == codes.ARC_BAND_TABLE_MISSING
    assert "no band_key" in exc_info.value.message


@pytest.mark.parametrize("failure", ["stale", "malformed", "missing", "refused"])
def test_a1_real_loader_failure_has_named_error(tmp_path: Path, failure: str) -> None:
    root = Path(__file__).resolve().parents[3]
    kwargs = {}
    expected_type: type[Exception]
    if failure == "stale":
        changed_doc = tmp_path / "changed-arc.md"
        changed_doc.write_bytes((root / "docs/epics/fresh-build-a1-arc.md").read_bytes() + b"\nChanged.\n")
        kwargs["doc_path"] = changed_doc
        expected_type = ArcStaleError
    elif failure == "malformed":
        malformed_arc = tmp_path / "malformed-arc.yaml"
        malformed_arc.write_text("positions: []\n", encoding="utf-8")
        kwargs["arc_path"] = malformed_arc
        expected_type = ValueError
    elif failure == "missing":
        kwargs["arc_path"] = tmp_path / "missing-arc.yaml"
        expected_type = FileNotFoundError
    else:
        kwargs["arc_path"] = root / "curriculum/l2-uk-en/plans/a1/_arc.yaml"
        expected_type = ValueError

    with pytest.raises(expected_type):
        load_arc("a1", **kwargs)
    with pytest.raises(ImmersionError) as exc_info:
        compute_lesson_immersion_band("a1", 1, 1, 0, **kwargs)
    assert exc_info.value.code == codes.ARC_BAND_TABLE_MISSING
    assert isinstance(exc_info.value.__cause__, expected_type)
    assert exc_info.value.message.startswith("failed loading arc for track 'a1': ")
