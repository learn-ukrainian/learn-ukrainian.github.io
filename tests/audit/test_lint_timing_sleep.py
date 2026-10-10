"""New test sleeps fail the frozen baseline. The helper file stays exempt."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.audit.lint_timing_sleep import drift, sleep_counts

_ROOT = Path(__file__).resolve().parents[2]


def test_an_unlisted_sleep_is_drift(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_new.py").write_text("import time\n\ndef test_x():\n    time.sleep(0.01)\n", encoding="utf-8")
    assert drift(sleep_counts(tmp_path), {}) == ["tests/test_new.py sleeps=1 allowed=0"]


def test_wait_helper_is_not_counted(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "wait_helpers.py").write_text("import time\n\ndef wait():\n    time.sleep(0.01)\n", encoding="utf-8")
    assert sleep_counts(tmp_path) == {}


def test_this_tree_matches_the_baseline() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/audit/lint_timing_sleep.py"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout
