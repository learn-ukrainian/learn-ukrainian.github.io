"""Anti-rot guard for #5740 — every test subprocess call must be bounded.

Background: a timeout-less ``subprocess.*`` hang held a CI runner for 357 minutes
(run ``30109965086``) because three guards were missing at once: call-site
``timeout=``, job ``timeout-minutes``, and ``pytest-timeout``. Job caps landed in
PR #5735; ``pytest-timeout`` is pinned in ``requirements*.txt`` and enforced via
``pyproject.toml`` (``timeout = 120``, ``timeout_method = "thread"``) plus the
CI pytest invocation. This module keeps the *call-site* fence from regrowing and
proves a hang fails fast *and names the test*.

``subprocess.Popen`` cannot take ``timeout=`` at construction; callers must bound
``.wait()`` / ``.communicate()`` (or an equivalent deadline). The AST guard below
covers ``run`` / ``check_output`` / ``call`` / ``check_call`` only.
"""

from __future__ import annotations

import ast
import os
import subprocess
import textwrap
from pathlib import Path

from tests.project_python import project_python

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTS_ROOT = _REPO_ROOT / "tests"
_BOUNDED_FUNCS = frozenset({"run", "check_output", "call", "check_call"})

# Documented per-test budget (must stay aligned with pyproject + ci.yml).
_EXPECTED_PYTEST_TIMEOUT_SECONDS = 120
_EXPECTED_TIMEOUT_METHOD = "thread"


def _subprocess_aliases(tree: ast.AST) -> dict[str, str | None]:
    """Map local names to subprocess attrs (None => the module itself)."""
    aliases: dict[str, str | None] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    aliases[alias.asname or "subprocess"] = None
    return aliases


def _timeout_less_calls(path: Path) -> list[tuple[int, str]]:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    aliases = _subprocess_aliases(tree)
    found: list[tuple[int, str]] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            name: str | None = None
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                base = node.func.value.id
                if base in aliases and aliases[base] is None and node.func.attr in _BOUNDED_FUNCS:
                    name = f"subprocess.{node.func.attr}"
            elif isinstance(node.func, ast.Name) and node.func.id in aliases:
                attr = aliases[node.func.id]
                if attr in _BOUNDED_FUNCS:
                    name = f"subprocess.{attr}"
            if name is not None:
                kwargs = {kw.arg for kw in node.keywords if kw.arg}
                if "timeout" not in kwargs:
                    found.append((node.lineno, name))
            self.generic_visit(node)

    Visitor().visit(tree)
    return found


def test_pytest_timeout_budget_is_documented_in_pyproject() -> None:
    """The 120s per-test budget must stay explicit in tool.pytest.ini_options."""
    # Avoid importing tomllib only for this — pyproject is small; parse lightly.
    text = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "timeout = 120" in text or 'timeout = 120' in text
    assert 'timeout_method = "thread"' in text or "timeout_method = 'thread'" in text
    assert "pytest-timeout" in (_REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    lock = (_REPO_ROOT / "requirements-lock.txt").read_text(encoding="utf-8")
    assert "pytest-timeout==" in lock


def test_ci_pytest_invokes_timeout_flags() -> None:
    ci = (_REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "--timeout=120" in ci
    assert "--timeout-method=thread" in ci


def test_no_timeout_less_subprocess_calls_under_tests() -> None:
    """Fail CI when a new ``subprocess.run``/``check_*``/``call`` lacks ``timeout=``."""
    offenders: list[str] = []
    for path in sorted(_TESTS_ROOT.rglob("*.py")):
        if path.name == Path(__file__).name:
            # This file deliberately constructs a hanging child; its own
            # subprocess.run calls carry timeout=.
            pass
        try:
            hits = _timeout_less_calls(path)
        except SyntaxError as exc:
            offenders.append(f"{path}: syntax error while scanning ({exc})")
            continue
        for lineno, name in hits:
            offenders.append(f"{path.relative_to(_REPO_ROOT)}:{lineno} {name}")

    assert not offenders, (
        "Timeout-less subprocess calls under tests/ (issue #5740). "
        "Pass an explicit timeout= (typically 30 for git fixtures, 60–120 for "
        "heavier scripts). Popen must bound wait()/communicate() instead.\n"
        + "\n".join(offenders)
    )


def test_deliberately_hanging_test_is_named_by_pytest_timeout(tmp_path: Path) -> None:
    """Prove pytest-timeout fails fast and names the hanging nodeid (#5740 AC).

    Runs an isolated child pytest so the hang cannot stall this suite. The child
    uses a 2-second budget; we allow a generous outer bound so flake from
    process startup does not become another hang.
    """
    hang_dir = tmp_path / "hang_suite"
    hang_dir.mkdir()
    hang_test = hang_dir / "test_intentional_hang.py"
    hang_test.write_text(
        textwrap.dedent(
            """\
            import time

            def test_intentional_forever_sleep():
                time.sleep(3600)
            """
        ),
        encoding="utf-8",
    )

    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("PYTEST_") and key not in {"PYTEST_CURRENT_TEST", "PYTEST_ADDOPTS"}
    }

    completed = subprocess.run(
        [
            str(project_python()),
            "-m",
            "pytest",
            str(hang_test),
            "-p",
            "no:xdist",
            "-p",
            "timeout",
            "--timeout=2",
            f"--timeout-method={_EXPECTED_TIMEOUT_METHOD}",
            "-o",
            "addopts=",
            "-q",
            "--tb=line",
        ],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )

    combined = f"{completed.stdout}\n{completed.stderr}"
    assert completed.returncode != 0, (
        "hanging test must fail under pytest-timeout, not pass/skip:\n" + combined
    )
    assert "test_intentional_forever_sleep" in combined, (
        "pytest-timeout must name the hanging test in its output "
        f"(budget={_EXPECTED_PYTEST_TIMEOUT_SECONDS}s documented; child used 2s):\n"
        + combined
    )
    # Either Failed: Timeout / +++ Timeout / Failed: Timeout >… depending on version.
    assert "timeout" in combined.lower(), (
        "expected a timeout failure signal in child pytest output:\n" + combined
    )
