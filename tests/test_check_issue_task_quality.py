"""Tests for scripts/check_issue_task_quality.py (#7854)."""

from __future__ import annotations

from scripts.check_issue_task_quality import score_body

COMPLETE = """
## User-visible outcome
Ship the advisory checker.

## Non-goals
No blocking CI gate.

## Denominator
All templates under .github/ISSUE_TEMPLATE/.

## Verify
```bash
.venv/bin/python scripts/check_issue_task_quality.py --help
```

## Definition of Done
- [ ] PR merged

## Terminal goal
merge

## Residual
none — owner: n/a
"""


def test_complete_card_passes() -> None:
    result = score_body(COMPLETE)
    assert result["verdict"] == "PASS"
    assert result["missing"] == []


def test_missing_fields_warn() -> None:
    result = score_body("## Overview\nDo a thing somehow.\n")
    assert result["verdict"] == "WARN"
    assert "outcome" in result["missing"] or "dod" in result["missing"]
    assert "non_goals" in result["missing"]


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


def test_cli_help(capsys) -> None:
    from scripts import check_issue_task_quality as mod

    try:
        mod.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    assert "Advisory" in out or "task-quality" in out or "--issue" in out
