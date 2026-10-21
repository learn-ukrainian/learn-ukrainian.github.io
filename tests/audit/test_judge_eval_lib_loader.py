"""Regression test for `pull_calibration_cases` loader preference order.

Failure shape this guards against: 2026-05-23 attempt to re-run the
qwen judge calibration died at first call because the loader still
defaulted to ``git show origin/pr-2006:<blob>`` even though PR #2006
merged 2026-05-15 (commit ``82afad7438``) and the branch was pruned.
The fixture has lived on main for over a week; the loader should
read the working tree first.
"""

from __future__ import annotations

from scripts.audit._judge_eval_lib import (
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
