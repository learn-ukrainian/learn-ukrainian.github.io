"""#9739: ``dispatch-fix`` writes only with the owned paths and planned risk its brief names."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pytest

from scripts.ai_agent_bridge import _dispatch_wrappers as wrappers

BRIEF = """# Fix the reviewer gate

## Outcome
Refuse the dead-end route.

## Review plan
Risk: high.

## Owned paths (frozen)
`scripts/delegate.py`, `scripts/review/reviewer_resolver.py`; tests: `tests/test_delegate.py` and
`tests/new_test.py`. Not `/abs/path.py`, not `../escape.py`, not a `word`.

```text
scripts/review/record_cf_verdict.py
```

### Notes inside the section
`scripts/review/closeout_cli.py`

## Verify
`tests/not_owned.py`
"""


def _owned(command: list[str]) -> list[str]:
    return [command[index + 1] for index, item in enumerate(command) if item == "--owned-path"]


def test_fix_command_carries_the_brief_owned_paths_and_risk(tmp_path):
    brief = tmp_path / "brief.md"
    brief.write_text(BRIEF, encoding="utf-8")

    command = wrappers.build_dispatch_fix_command("9739", brief)

    assert _owned(command) == [
        "scripts/delegate.py",
        "scripts/review/reviewer_resolver.py",
        "tests/test_delegate.py",
        "tests/new_test.py",
        "scripts/review/closeout_cli.py",
        "scripts/review/record_cf_verdict.py",
    ]
    assert command[command.index("--authoring-review-risk") + 1] == "high"
    assert command[command.index("--mode") + 1] == "danger"


@pytest.mark.parametrize(
    "text",
    [
        "# Fix\n\nNo scope here.\n",
        "# Fix\n\n## Owned paths\n\nTo be decided.\n\n## Verify\n`scripts/x.py`\n",
        "# Fix\n\n## Owned paths\n`/abs/only.py` and `../escape/x.py`\n",
    ],
)
def test_fix_without_derivable_owned_paths_refuses_before_any_dispatch(monkeypatch, tmp_path, capsys, text):
    monkeypatch.delenv("LU_RUNTIME_TMP_ROOT", raising=False)
    brief = tmp_path / "brief.md"
    brief.write_text(text, encoding="utf-8")

    def unexpected(command, **kwargs):
        pytest.fail(f"an unscoped fix must not run {command}")

    monkeypatch.setattr(wrappers.subprocess, "run", unexpected)
    rc = wrappers.handle_dispatch_fix(argparse.Namespace(task_id="9739", brief_file=str(brief), dry_run=False))

    assert rc == 2
    assert "no '## Owned paths' section" in capsys.readouterr().err


def test_ambiguous_risk_lines_leave_the_planned_risk_unset(tmp_path):
    brief = tmp_path / "brief.md"
    brief.write_text("## Owned paths\n`scripts/a.py`\n\nRisk: low\n\nRisk: critical\n", encoding="utf-8")

    command = wrappers.build_dispatch_fix_command("1", brief)

    # Two different planned risks are not a plan; delegate then checks at critical.
    assert "--authoring-review-risk" not in command
    assert _owned(command) == ["scripts/a.py"]


def test_scoped_fix_dispatches_with_its_paths(monkeypatch, tmp_path):
    monkeypatch.delenv("LU_RUNTIME_TMP_ROOT", raising=False)
    brief = tmp_path / "brief.md"
    brief.write_text(BRIEF, encoding="utf-8")
    calls: list[list[str]] = []
    monkeypatch.setattr(
        wrappers.subprocess,
        "run",
        lambda command, **kwargs: calls.append(command) or subprocess.CompletedProcess(command, 0),
    )

    rc = wrappers.handle_dispatch_fix(argparse.Namespace(task_id="9739", brief_file=str(brief), dry_run=False))

    assert rc == 0 and len(calls) == 1
    assert "scripts/delegate.py" in _owned(calls[0])
    assert Path(calls[0][calls[0].index("--prompt-file") + 1]).name == "dispatch-fix-9739.md"
