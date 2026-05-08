from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT = Path("scripts/audit/lint_anti_menu.py")
PYTHON = Path(".venv/bin/python")


def run_linter(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(PYTHON), str(SCRIPT), "--text", str(path)],
        capture_output=True,
        check=False,
        text=True,
    )


def write_fixture(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "fixture.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_parenthesized_signoff_menu_triggers(tmp_path: Path) -> None:
    path = write_fixture(
        tmp_path,
        "Decision: do we (a) merge the PR now or (b) wait for another review?\n",
    )

    result = run_linter(path)

    assert result.returncode == 1
    assert "anti-menu pattern detected" in result.stdout
    assert "(a) merge the PR now or (b)" in result.stdout


def test_inline_numbered_which_menu_triggers(tmp_path: Path) -> None:
    path = write_fixture(
        tmp_path,
        "1) Keep current prompt 2) Switch output filter 3) Wait for review -- which?\n",
    )

    result = run_linter(path)

    assert result.returncode == 1
    assert "1) Keep current prompt" in result.stdout
    assert "which?" in result.stdout


def test_signoff_options_menu_triggers(tmp_path: Path) -> None:
    path = write_fixture(
        tmp_path,
        """Sign off on these 3 options:
1) Ship the guardrail
2) Wait for another review
3) Defer the issue
""",
    )

    result = run_linter(path)

    assert result.returncode == 1
    assert "Sign off on these 3 options" in result.stdout


def test_signoff_options_period_numbered_list_triggers(tmp_path: Path) -> None:
    path = write_fixture(
        tmp_path,
        """Sign off on these 3 options:
1. Ship the guardrail
2. Wait for another review
3. Defer the issue
""",
    )

    result = run_linter(path)

    assert result.returncode == 1
    assert "Sign off on these 3 options" in result.stdout


def test_acceptance_criteria_numbered_list_does_not_trigger(tmp_path: Path) -> None:
    path = write_fixture(
        tmp_path,
        """## Acceptance criteria

1) Detect direct sign-off menus
2) Ignore status reports
3) Exit non-zero on violations
""",
    )

    result = run_linter(path)

    assert result.returncode == 0
    assert result.stdout == ""


def test_parenthesized_acceptance_criteria_heading_does_not_trigger(tmp_path: Path) -> None:
    path = write_fixture(
        tmp_path,
        """## Acceptance criteria (numbered, all required)

1) Want me to merge now, rerun tests, or wait for another review?
""",
    )

    result = run_linter(path)

    assert result.returncode == 0
    assert result.stdout == ""


def test_forbidden_patterns_preamble_exempts_following_examples(tmp_path: Path) -> None:
    path = write_fixture(
        tmp_path,
        """Forbidden patterns:

- Should I merge this now or wait for another review?
- Want me to rerun tests or open the PR?
""",
    )

    result = run_linter(path)

    assert result.returncode == 0
    assert result.stdout == ""


def test_adr_options_inside_code_fence_do_not_trigger(tmp_path: Path) -> None:
    path = write_fixture(
        tmp_path,
        """# ADR sketch

```md
Should I adopt Option A or Option B?
Sign off on these 2 options:
1) Option A
2) Option B
```
""",
    )

    result = run_linter(path)

    assert result.returncode == 0
    assert result.stdout == ""


def test_status_prefixed_list_does_not_trigger(tmp_path: Path) -> None:
    path = write_fixture(
        tmp_path,
        "Status: 1) implemented 2) tested 3) documented -- which landed today?\n",
    )

    result = run_linter(path)

    assert result.returncode == 0
    assert result.stdout == ""


def test_real_shaped_handoff_does_not_trigger(tmp_path: Path) -> None:
    path = write_fixture(
        tmp_path,
        """# Session Handoff -- 2026-05-08

> Mode: autonomous code guardrail dispatch.
> Scope: audit script, tests, docs entry.

## TL;DR

One guardrail is ready for implementation. The worktree is isolated and the
main checkout stays on main. The pending Multi-UI decision does not block this
audit-only change.

## Merged today

| PR | What | Status |
|---|---|---|
| #1781 | Prompt hard stop | merged |
| #1783 | Warm cache | merged |
| #1784 | Codex launcher parity | merged |

## Open work

| Priority | Task | Next action |
|---|---|---|
| 1 | Anti-menu linter | implement script |
| 2 | Handoff verifier | file follow-up |
| 3 | python_qg failure | investigate separately |

## Plan

Plan:
1) Read the rule and recent handoffs.
2) Implement the scanner.
3) Run targeted tests.
4) Validate against session-state docs.

## Validation commands

```bash
.venv/bin/python scripts/audit/lint_anti_menu.py --text docs/session-state/current.md
.venv/bin/python -m pytest tests/audit/test_lint_anti_menu.py -x
```

## Status

Done: scoped the change to three files.
Status: validation remains before opening the PR.

## Acceptance criteria

1) Script exits 0 on clean markdown.
2) Script exits 1 on sign-off menu prompts.
3) Docs entry lists the command.

## Notes

ADR option enumerations remain valid inside decision documents. This guardrail
targets handoff-style requests that ask the user to pick from a menu instead of
making a concrete recommendation.
""",
    )

    result = run_linter(path)

    assert result.returncode == 0
    assert result.stdout == ""


def test_stdin_uses_stdin_label_and_informative_snippet() -> None:
    result = subprocess.run(
        [str(PYTHON), str(SCRIPT), "--stdin"],
        capture_output=True,
        check=False,
        input="Should I merge this now or wait for another review?\n",
        text=True,
    )

    assert result.returncode == 1
    assert "<stdin>:1: anti-menu pattern detected —" in result.stdout
    assert "Should I merge this now or wait" in result.stdout


def test_non_utf8_input_exits_2(tmp_path: Path) -> None:
    path = tmp_path / "fixture.md"
    path.write_bytes(b"\xff")

    result = run_linter(path)

    assert result.returncode == 2
    assert f"{path}: not utf-8" in result.stderr
    assert result.stdout == ""
