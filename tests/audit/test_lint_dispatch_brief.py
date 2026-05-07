from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit import lint_dispatch_brief


@pytest.mark.parametrize(
    "body",
    [
        """```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python scripts/delegate.py dispatch --task-id example
```""",
        """```bash
# venv symlinked
.venv/bin/python scripts/delegate.py dispatch --task-id example
```""",
    ],
)
def test_brief_passes_with_required_venv_guard(tmp_path: Path, body: str) -> None:
    brief = tmp_path / "pass.md"
    brief.write_text(f"# Brief\n\n{body}\n", encoding="utf-8")

    assert lint_dispatch_brief.main(["--brief", str(brief)]) == 0


@pytest.mark.parametrize(
    "body,line",
    [
        (
            """```bash
.venv/bin/python scripts/delegate.py dispatch --task-id example
```""",
            4,
        ),
        (
            """```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/example
.venv/bin/python scripts/delegate.py dispatch --task-id example
```""",
            5,
        ),
    ],
)
def test_brief_fails_without_required_venv_guard(tmp_path: Path, capsys, body: str, line: int) -> None:
    brief = tmp_path / "fail.md"
    brief.write_text(f"# Brief\n\n{body}\n", encoding="utf-8")

    assert lint_dispatch_brief.main(["--brief", str(brief)]) == 1
    output = capsys.readouterr().out
    assert f"{brief}:{line}: missing cd-to-main or symlinked-venv before .venv/bin/python" in output
