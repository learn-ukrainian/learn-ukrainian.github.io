"""Tests for scripts/check_issue_task_quality.py (#7854)."""

from __future__ import annotations

from scripts.check_issue_task_quality import main, score_body

COMPLETE = """
## User-visible outcome
Ship the advisory checker.

## Why / evidence
#7854 audit showed empty DoD cards.

## In scope
`scripts/check_issue_task_quality.py` and issue templates.

## Non-goals
No blocking CI gate.

## Denominator
All templates under .github/ISSUE_TEMPLATE/.

## Verify
```bash
.venv/bin/python scripts/check_issue_task_quality.py --help
```

## Dependencies
none

## Definition of Done
- [ ] PR merged with CF + green CI

## Terminal goal
merge

## Residual
none — owner: n/a
"""

HEADINGS_ONLY = """
## User-visible outcome
## Why / evidence
## In scope
## Non-goals
## Denominator
## Verify
## Dependencies
## Definition of Done
## Terminal goal
## Residual
"""


def test_complete_card_passes() -> None:
    result = score_body(COMPLETE)
    assert result["verdict"] == "PASS"
    assert result["missing"] == []


def test_missing_fields_warn() -> None:
    result = score_body("## Overview\nDo a thing somehow.\n")
    assert result["verdict"] == "WARN"
    assert "non_goals" in result["missing"]
    assert "why" in result["missing"]


def test_headings_only_warns() -> None:
    result = score_body(HEADINGS_ONLY)
    assert result["verdict"] == "WARN"
    assert "outcome" in result["missing"]
    assert "terminal_goal" in result["missing"]


def test_empty_body_warns() -> None:
    result = score_body("")
    assert result["verdict"] == "WARN"
    assert len(result["missing"]) >= 8


def test_trivial_exemption() -> None:
    result = score_body("trivial: yes\nFix typo in README\n", trivial=False)
    assert result["verdict"] == "PASS"
    assert result["trivial"] is True


def test_prose_mentioning_trivial_is_not_exempt() -> None:
    result = score_body(
        "## Overview\nDiscusses trivial exempt cases but is not itself trivial.\n",
        trivial=False,
    )
    assert result["trivial"] is False
    assert result["verdict"] == "WARN"


def test_missing_body_file_is_fail_open(tmp_path) -> None:
    missing = tmp_path / "does-not-exist.md"
    code = main(["--body-file", str(missing), "--json"])
    assert code == 0


def test_missing_body_file_strict_fails(tmp_path) -> None:
    missing = tmp_path / "does-not-exist.md"
    code = main(["--body-file", str(missing), "--strict"])
    assert code == 1


def test_cli_help(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    assert "Advisory" in out or "task-quality" in out or "--issue" in out
