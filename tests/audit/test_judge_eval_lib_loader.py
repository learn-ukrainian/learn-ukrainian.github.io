"""Regression test for `pull_calibration_cases` loader preference order.

Failure shape this guards against: 2026-05-23 attempt to re-run the
qwen judge calibration died at first call because the loader still
defaulted to ``git show origin/pr-2006:<blob>`` even though PR #2006
merged 2026-05-15 (commit ``82afad7438``) and the branch was pruned.
The fixture has lived on main for over a week; the loader should
read the working tree first.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit._judge_eval_lib import (
    CALIBRATION_BLOB,
    PROJECT_ROOT,
    pull_calibration_cases,
)


def test_loader_uses_working_tree_when_file_present():
    """Working-tree file is the preferred source on main."""
    cases = pull_calibration_cases()
    assert len(cases) >= 1, "expected at least one calibration case"
    first = cases[0]
    assert "prompt_id" in first
    assert "gold" in first
    assert "output_text" in first


def test_loader_uses_explicit_ref_when_given(tmp_path: Path):
    """Explicit ``ref=`` bypasses working-tree lookup."""
    blob_path = tmp_path / "fake-blob.jsonl"
    payload = {
        "prompt_id": "ut_only",
        "gold": {"expected_clean": True, "min_sev2_count": 0},
        "output_text": "test",
        "status": "ok",
        "model": "n/a",
    }
    blob_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    cases = pull_calibration_cases(blob=str(blob_path.name), project_root=tmp_path)
    assert len(cases) == 1
    assert cases[0]["prompt_id"] == "ut_only"


def test_loader_errors_clearly_when_both_paths_missing(tmp_path: Path):
    """When working-tree path and ref both miss, sys.exit with both paths in message."""
    with pytest.raises(SystemExit) as exc_info:
        pull_calibration_cases(
            ref="origin/nonexistent-branch-1234567890",
            blob="nonexistent-blob.jsonl",
            project_root=tmp_path,
        )
    msg = str(exc_info.value)
    assert "Working-tree path also missing" in msg
    assert "origin/nonexistent-branch" in msg


def test_canonical_blob_path_exists_on_main():
    """Sanity: the canonical fixture should exist on main."""
    p = PROJECT_ROOT / CALIBRATION_BLOB
    assert p.exists(), (
        f"{CALIBRATION_BLOB} missing from main working tree — "
        "PR #2006 may have regressed."
    )
