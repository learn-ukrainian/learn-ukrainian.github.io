"""The bypass-word lint fails on a comment and passes once that comment is gone."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.audit.lint_workaround_comments import findings

_ROOT = Path(__file__).resolve().parents[2]


def test_a_bypass_comment_is_a_finding(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    word = "work" "around"
    (scripts / "sample.py").write_text(f"# {word}: pass the prompt on stdin\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    assert findings(tmp_path) == ["scripts/sample.py:1"]


def test_checked_trees_have_no_bypass_word() -> None:
    assert findings(_ROOT) == []


def test_cli_exits_zero_on_this_tree() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/audit/lint_workaround_comments.py"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout
