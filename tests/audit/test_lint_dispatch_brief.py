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
        "This is an inline `.venv/bin/python scripts/delegate.py` mention in prose.",
        """```bash
cd /some/dir
.venv/bin/pytest tests/
.venv/bin/ruff check .
```""",
        "Use `.venv/bin/python` for python script execution.",
        """```bash
# Avoid using `.venv/bin/python` directly
```""",
        """```bash
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python scripts/delegate.py
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
        (
            """```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python scripts/delegate.py dispatch --task-id 1
echo "1"
echo "2"
echo "3"
echo "4"
echo "5"
.venv/bin/python scripts/delegate.py dispatch --task-id 2
```""",
            11,
        ),
        (
            """```bash
git checkout main && .venv/bin/python scripts/delegate.py
```""",
            4,
        ),
        (
            """```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/example && .venv/bin/python scripts/delegate.py
```""",
            4,
        ),
        (
            """```bash
.venv/bin/python --version
```""",
            4,
        ),
    ],
)
def test_brief_fails_without_required_venv_guard(tmp_path: Path, capsys, body: str, line: int) -> None:
    brief = tmp_path / "fail.md"
    brief.write_text(f"# Brief\n\n{body}\n", encoding="utf-8")

    assert lint_dispatch_brief.main(["--brief", str(brief)]) == 1
    output = capsys.readouterr().out
    assert f"{brief}:{line}: missing cd-to-main or symlinked-venv before .venv/bin/python" in output


@pytest.mark.parametrize(
    "body",
    [
        """```bash
// BAD
pytest tests/ -x
```""",
        """```bash
// NOT THIS
pytest -x
```""",
        """```markdown
// BAD
pytest --exitfirst
```""",
        "This test suite uses `pytest tests/ -v`.",
        "We also run `pytest tests/ --maxfail=5`.",
        "Another check: `pytest tests/test_foo.py -q`.",
    ],
)
def test_brief_passes_with_pytest_x_guard_or_no_x(tmp_path: Path, body: str) -> None:
    brief = tmp_path / "pass_pytest.md"
    brief.write_text(f"# Brief\n\n{body}\n", encoding="utf-8")

    assert lint_dispatch_brief.main(["--brief", str(brief)]) == 0


@pytest.mark.parametrize(
    "body,line",
    [
        (
            """```bash
pytest tests/ -x
```""",
            4,
        ),
        (
            """```bash
pytest -x tests/
```""",
            4,
        ),
        (
            "Avoid using `pytest -x`.",
            3,
        ),
        (
            """```bash
pytest --exitfirst
```""",
            4,
        ),
    ],
)
def test_brief_fails_with_pytest_x(tmp_path: Path, capsys, body: str, line: int) -> None:
    brief = tmp_path / "fail_pytest.md"
    brief.write_text(f"# Brief\n\n{body}\n", encoding="utf-8")

    assert lint_dispatch_brief.main(["--brief", str(brief)]) == 1
    output = capsys.readouterr().out
    assert f"{brief}:{line}: forbid pytest -x in dispatch briefs" in output


def test_brief_custom_project_root(tmp_path: Path) -> None:
    custom_root = tmp_path / "my-custom-curriculum"
    custom_root.mkdir()

    brief = tmp_path / "custom_pass.md"
    brief.write_text(
        f"# Brief\n\n```bash\ncd {custom_root}\n.venv/bin/python scripts/delegate.py\n```\n",
        encoding="utf-8",
    )

    assert lint_dispatch_brief.main(["--brief", str(brief), "--project-root", str(custom_root)]) == 0


def test_brief_custom_project_root_fail(tmp_path: Path) -> None:
    custom_root = tmp_path / "my-custom-curriculum"
    custom_root.mkdir()

    brief = tmp_path / "custom_fail.md"
    brief.write_text(
        "# Brief\n\n```bash\n.venv/bin/python scripts/delegate.py\n```\n",
        encoding="utf-8",
    )

    assert lint_dispatch_brief.main(["--brief", str(brief), "--project-root", str(custom_root)]) == 1


def test_brief_binary_input_exit_2(tmp_path: Path) -> None:
    brief = tmp_path / "binary.md"
    brief.write_bytes(b"\x80\x81\x82")

    with pytest.raises(SystemExit) as exc_info:
        lint_dispatch_brief.main(["--brief", str(brief)])
    assert exc_info.value.code == 2
