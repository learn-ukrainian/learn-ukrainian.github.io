"""Decision doc and code must agree on LLM QG review floors."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from common.thresholds import LEVEL_THRESHOLDS, QG_DIMS, REVIEW_REJECT_FLOOR

DOC_PATH = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "decisions"
    / "2026-04-26-llm-qg-per-dim-thresholds.md"
)


def _parse_doc_floor_table() -> dict[str, dict[str, float]]:
    text = DOC_PATH.read_text("utf-8")
    pattern = re.compile(
        r"^\|\s*(A1|A2|B1|B2|C1|C2)\s*"
        r"\|\s*(\d+\.\d)\s*"
        r"\|\s*(\d+\.\d)\s*"
        r"\|\s*(\d+\.\d)\s*"
        r"\|\s*(\d+\.\d)\s*"
        r"\|\s*(\d+\.\d)\s*\|$",
        re.MULTILINE,
    )
    rows = {}
    for match in pattern.finditer(text):
        level, *values = match.groups()
        rows[level] = dict(zip(QG_DIMS, [float(value) for value in values], strict=True))
    return rows


def test_review_floor_code_matches_decision_doc_table() -> None:
    doc_table = _parse_doc_floor_table()

    assert set(doc_table) == set(LEVEL_THRESHOLDS)
    for level, expected in doc_table.items():
        actual = {
            dim: LEVEL_THRESHOLDS[level].review_floors[dim].pass_floor
            for dim in QG_DIMS
        }
        assert actual == expected


def test_all_review_reject_floors_match_decision_doc_constant() -> None:
    text = DOC_PATH.read_text("utf-8")
    assert "REJECT floor: **6.0 across all (level, dim)**" in text

    for thresholds in LEVEL_THRESHOLDS.values():
        for floor in thresholds.review_floors.values():
            assert floor.reject_floor == REVIEW_REJECT_FLOOR
