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
import re
import subprocess
import textwrap
from collections import Counter, defaultdict
from pathlib import Path
from typing import NamedTuple

import pytest

from scripts.ci.test_source_cache import parse_test_source, read_test_source
from tests.project_python import project_python

pytestmark = pytest.mark.repo_invariant

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTS_ROOT = _REPO_ROOT / "tests"
_SCRIPTS_ROOT = _REPO_ROOT / "scripts"
_ALLOWLIST_PATH = _SCRIPTS_ROOT / "ci" / "subprocess_timeout_allowlist.txt"
_BOUNDED_FUNCS = frozenset({"run", "check_output", "call", "check_call"})
_SUBPROCESS_IMPORT_RE = re.compile(r"(?m)^\s*(?:import subprocess|from subprocess import)\b")

# Documented per-test budget (must stay aligned with pyproject + ci.yml).
_EXPECTED_PYTEST_TIMEOUT_SECONDS = 120
_EXPECTED_TIMEOUT_METHOD = "thread"


class TimeoutLessCall(NamedTuple):
    lineno: int
    name: str
    qualname: str


class _SubprocessCallVisitor(ast.NodeVisitor):
    def __init__(self, aliases: dict[str, str | None]) -> None:
        self._aliases = aliases
        self._scope_stack: list[str] = []
        self.hits: list[TimeoutLessCall] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        name: str | None = None
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            base = node.func.value.id
            if base in self._aliases and self._aliases[base] is None and node.func.attr in _BOUNDED_FUNCS:
                name = f"subprocess.{node.func.attr}"
        elif isinstance(node.func, ast.Name) and node.func.id in self._aliases:
            attr = self._aliases[node.func.id]
            if attr in _BOUNDED_FUNCS:
                name = f"subprocess.{attr}"
        if name is not None:
            kwargs = {kw.arg for kw in node.keywords if kw.arg}
            if "timeout" not in kwargs:
                qualname = ".".join(self._scope_stack) if self._scope_stack else "<module>"
                self.hits.append(TimeoutLessCall(node.lineno, name, qualname))
        self.generic_visit(node)


def _timeout_less_calls(path: Path) -> list[TimeoutLessCall]:
    src = read_test_source(path)
    if "subprocess" not in src or not _SUBPROCESS_IMPORT_RE.search(src):
        return []
    tree = parse_test_source(path)
    aliases: dict[str, str | None] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    aliases[alias.asname or "subprocess"] = None
    visitor = _SubprocessCallVisitor(aliases)
    visitor.visit(tree)
    return visitor.hits


def _load_subprocess_timeout_allowlist() -> list[str]:
    text = _ALLOWLIST_PATH.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def test_pytest_timeout_budget_is_documented_in_pyproject() -> None:
    """The 120s per-test budget must stay explicit in tool.pytest.ini_options."""
    # Avoid importing tomllib only for this — pyproject is small; parse lightly.
    text = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "timeout = 120" in text or "timeout = 120" in text
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
        try:
            hits = _timeout_less_calls(path)
        except SyntaxError as exc:
            offenders.append(f"{path}: syntax error while scanning ({exc})")
            continue
        for hit in hits:
            offenders.append(f"{path.relative_to(_REPO_ROOT)}:{hit.lineno} {hit.name}")

    assert not offenders, (
        "Timeout-less subprocess calls under tests/ (issue #5740). "
        "Pass an explicit timeout= (typically 30 for git fixtures, 60–120 for "
        "heavier scripts). Popen must bound wait()/communicate() instead.\n" + "\n".join(offenders)
    )


def test_subprocess_timeout_allowlist_is_sorted_and_valid() -> None:
    """The allowlist must be non-empty, sorted, and well-formed (#7176)."""
    assert _ALLOWLIST_PATH.is_file(), f"allowlist not found at {_ALLOWLIST_PATH}"
    entries = _load_subprocess_timeout_allowlist()
    assert entries, "subprocess timeout allowlist must not be empty"
    assert entries == sorted(entries), (
        "subprocess timeout allowlist must be sorted alphabetically. "
        "Run a sort on scripts/ci/subprocess_timeout_allowlist.txt."
    )
    for entry in entries:
        parts = entry.split("::")
        assert len(parts) >= 3, f"invalid allowlist entry format (expected path::qualname::callee): {entry}"
        path = _REPO_ROOT / parts[0]
        assert path.is_file(), f"allowlist entry refers to non-existent file: {parts[0]}"


def test_no_unallowlisted_timeout_less_subprocess_calls_under_scripts() -> None:
    """Fail CI on unallowlisted timeout-less subprocess calls in scripts/ and reject stale allowlist entries (#7176)."""
    allowlist_entries = _load_subprocess_timeout_allowlist()
    allowlist_counts = Counter(allowlist_entries)

    actual_hits: dict[str, list[tuple[Path, TimeoutLessCall]]] = defaultdict(list)
    scan_errors: list[str] = []

    for path in sorted(_SCRIPTS_ROOT.rglob("*.py")):
        try:
            hits = _timeout_less_calls(path)
        except SyntaxError as exc:
            scan_errors.append(f"{path}: syntax error while scanning ({exc})")
            continue
        rel = path.relative_to(_REPO_ROOT).as_posix()
        for hit in hits:
            key = f"{rel}::{hit.qualname}::{hit.name}"
            actual_hits[key].append((path, hit))

    if scan_errors:
        pytest.fail("Syntax errors encountered while scanning scripts/:\n" + "\n".join(scan_errors))

    unallowlisted: list[str] = []
    for key, hits in sorted(actual_hits.items()):
        allowed_count = allowlist_counts.get(key, 0)
        if len(hits) > allowed_count:
            excess = hits[allowed_count:]
            for path, hit in excess:
                rel = path.relative_to(_REPO_ROOT).as_posix()
                unallowlisted.append(
                    f"{rel}:{hit.lineno} {hit.name} in {hit.qualname} "
                    f"(found {len(hits)}, allowlist permits {allowed_count})"
                )

    stale_entries: list[str] = []
    for key, allowed_count in sorted(allowlist_counts.items()):
        actual_count = len(actual_hits.get(key, []))
        if allowed_count > actual_count:
            stale_entries.append(f"{key} (allowlist has {allowed_count}, actual violations {actual_count})")

    errors: list[str] = []
    if unallowlisted:
        errors.append(
            "Timeout-less subprocess calls under scripts/ not in allowlist (issue #7176).\n"
            "Pass an explicit timeout= (typically 30 for git fixtures/helpers, 60–120 for "
            "heavier scripts) to bound the subprocess call. Popen callers must bound "
            ".wait() / .communicate() instead.\n" + "\n".join(unallowlisted)
        )
    if stale_entries:
        errors.append(
            "Stale entries in scripts/ci/subprocess_timeout_allowlist.txt (issue #7176).\n"
            "The allowlist is shrink-only. When a subprocess call is given a timeout= or removed, "
            "its entry must be removed from scripts/ci/subprocess_timeout_allowlist.txt:\n" + "\n".join(stale_entries)
        )

    assert not errors, "\n\n".join(errors)


def test_deliberately_hanging_test_is_named_by_pytest_timeout(tmp_path: Path) -> None:
    """Prove pytest-timeout fails fast and names the hanging nodeid (#5740 AC).

    Runs an isolated child pytest so the hang cannot stall this suite. The child
    uses a 0.25-second budget; we allow a generous outer bound so flake from
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
            "--timeout=0.25",
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
    assert completed.returncode != 0, "hanging test must fail under pytest-timeout, not pass/skip:\n" + combined
    assert "test_intentional_forever_sleep" in combined, (
        "pytest-timeout must name the hanging test in its output "
        f"(budget={_EXPECTED_PYTEST_TIMEOUT_SECONDS}s documented; child used 0.25s):\n" + combined
    )
    # Either Failed: Timeout / +++ Timeout / Failed: Timeout >… depending on version.
    assert "timeout" in combined.lower(), "expected a timeout failure signal in child pytest output:\n" + combined


_FASTLANE_MANIFEST = _REPO_ROOT / "scripts" / "ci" / "fastlane_always_tests.txt"


def _fastlane_manifest() -> list[str]:
    return [
        line.strip()
        for line in _FASTLANE_MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _has_repo_invariant_marker(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    if "repo_invariant" not in source:
        return False
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        pytest.fail(f"cannot parse test module {path}: {exc}")

    for statement in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(statement, ast.Assign):
            targets = [target for target in statement.targets if isinstance(target, ast.expr)]
            value = statement.value
        elif isinstance(statement, ast.AnnAssign):
            targets = [statement.target]
            value = statement.value
        if not value or not any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in targets):
            continue
        if any(
            isinstance(node, ast.Attribute)
            and node.attr == "repo_invariant"
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "mark"
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "pytest"
            for node in ast.walk(value)
        ):
            return True
    return False


def _marked_repo_invariant_modules() -> set[str]:
    return {
        path.relative_to(_REPO_ROOT).as_posix()
        for path in sorted(_TESTS_ROOT.rglob("test_*.py"))
        if _has_repo_invariant_marker(path)
    }


def test_fastlane_manifest_entries_exist_and_excludes_work_privacy() -> None:
    entries = _fastlane_manifest()
    assert entries == sorted(set(entries)), "fastlane invariant manifest must be sorted and duplicate-free"
    assert entries, "fastlane invariant manifest must not be empty"
    assert "tests/test_work_privacy.py" not in entries
    for entry in entries:
        path = _REPO_ROOT / entry
        assert path.is_file(), f"fastlane invariant manifest entry does not exist: {entry}"
        assert entry.startswith("tests/") and entry.endswith(".py"), f"invalid manifest entry: {entry}"


def test_fastlane_manifest_matches_repo_invariant_markers() -> None:
    manifest = set(_fastlane_manifest())
    marked = _marked_repo_invariant_modules()
    assert manifest - marked == set(), "manifest entries missing repo_invariant marker: " + ", ".join(
        sorted(manifest - marked)
    )
    assert marked - manifest == set(), "repo_invariant test modules missing from fastlane manifest: " + ", ".join(
        sorted(marked - manifest)
    )
