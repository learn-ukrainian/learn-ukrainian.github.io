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
from pathlib import Path

import pytest

from scripts.ci import fastlane_requirements
from scripts.ci.test_source_cache import parse_test_source, read_test_source
from tests.project_python import project_python

pytestmark = pytest.mark.repo_invariant

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTS_ROOT = _REPO_ROOT / "tests"
_BOUNDED_FUNCS = frozenset({"run", "check_output", "call", "check_call"})
_SUBPROCESS_IMPORT_RE = re.compile(r"(?m)^\s*(?:import subprocess|from subprocess import)\b")

# Documented per-test budget (must stay aligned with pyproject + ci.yml).
_EXPECTED_PYTEST_TIMEOUT_SECONDS = 120
_EXPECTED_TIMEOUT_METHOD = "thread"


def _timeout_less_calls(path: Path) -> list[tuple[int, str]]:
    src = read_test_source(path)
    if not _SUBPROCESS_IMPORT_RE.search(src):
        return []
    tree = parse_test_source(path)
    aliases: dict[str, str | None] = {}
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    aliases[alias.asname or "subprocess"] = None
        elif isinstance(node, ast.Call):
            calls.append(node)

    found: list[tuple[int, str]] = []
    for node in calls:
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
    assert completed.returncode != 0, (
        "hanging test must fail under pytest-timeout, not pass/skip:\n" + combined
    )
    assert "test_intentional_forever_sleep" in combined, (
        "pytest-timeout must name the hanging test in its output "
        f"(budget={_EXPECTED_PYTEST_TIMEOUT_SECONDS}s documented; child used 0.25s):\n"
        + combined
    )
    # Either Failed: Timeout / +++ Timeout / Failed: Timeout >… depending on version.
    assert "timeout" in combined.lower(), (
        "expected a timeout failure signal in child pytest output:\n" + combined
    )


_FASTLANE_MANIFEST = _REPO_ROOT / "scripts" / "ci" / "fastlane_always_tests.txt"
_FASTLANE_BASE_REQUIREMENTS = _REPO_ROOT / "scripts" / "ci" / "requirements-fastlane.txt"
_REQUIREMENTS_LOCK = _REPO_ROOT / "requirements-lock.txt"


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
    assert manifest - marked == set(), (
        "manifest entries missing repo_invariant marker: " + ", ".join(sorted(manifest - marked))
    )
    assert marked - manifest == set(), (
        "repo_invariant test modules missing from fastlane manifest: " + ", ".join(sorted(marked - manifest))
    )


def test_fastlane_manifest_requirements_fit_slim_profile() -> None:
    manifest = [
        _REPO_ROOT / entry
        for entry in _fastlane_manifest()
    ]
    try:
        selected = fastlane_requirements.select_requirements(
            manifest,
            base_requirements=fastlane_requirements.read_requirements(_FASTLANE_BASE_REQUIREMENTS),
            lock_requirements=fastlane_requirements.read_lock(_REQUIREMENTS_LOCK),
            project_root=_REPO_ROOT,
        )
    except fastlane_requirements.RequirementSelectionError as exc:
        pytest.fail(f"fastlane invariant manifest imports are not satisfiable by the slim profile: {exc}")

    lock = fastlane_requirements.read_lock(_REQUIREMENTS_LOCK)
    exact_pins = set(lock.values()) | set(fastlane_requirements.EXPLICIT_REQUIREMENTS.values())
    for requirement in selected:
        assert requirement in exact_pins, (
            f"fastlane requirement is not an exact lock pin: {requirement}"
        )
