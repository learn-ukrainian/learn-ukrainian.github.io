"""The suite strips every live agent session identity variable (#8778).

``tests/conftest.py`` deletes ``SESSION_IDENTITY_ENV_VARS`` before each test's
fixtures set up. This module parses the sites that export identity into an
agent session and fails when one of them exports a name the tuple does not
cover.
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path

import pytest

from tests.conftest import SESSION_IDENTITY_ENV_VARS

pytest_plugins = ("pytester",)

# The export sites are repository trees (launchers, hooks, agent runtime) that
# this module globs rather than imports, so import selection cannot pick it (#8707).
pytestmark = pytest.mark.repo_wide

REPO_ROOT = Path(__file__).resolve().parents[1]

_SHELL_EXPORT_SITES = (
    *sorted(REPO_ROOT.glob("start-*.sh")),
    *sorted((REPO_ROOT / "scripts" / "lib").glob("*.sh")),
    *sorted((REPO_ROOT / "scripts" / "launchers").glob("*.sh")),
    *sorted((REPO_ROOT / "agents_extensions" / "shared" / "hooks").glob("*.sh")),
)
_SESSION_RECORD = REPO_ROOT / "scripts" / "lib" / "session_record.py"
_SESSION_SUPERVISOR = REPO_ROOT / "scripts" / "lib" / "session_supervisor.sh"
_PROFILE_RESOLVER = REPO_ROOT / "scripts" / "lib" / "profile_resolver.sh"
_SUPERVISOR = REPO_ROOT / "scripts" / "orchestration" / "claudex_supervisor.py"
# Python code that builds the environment of a spawned agent session.
_PYTHON_ENV_SITES = (
    REPO_ROOT / "scripts" / "delegate.py",
    _SUPERVISOR,
    *sorted((REPO_ROOT / "scripts" / "agent_runtime").glob("*.py")),
)
_TELEMETRY = REPO_ROOT / "scripts" / "telemetry" / "emit.py"

# Exported names in these namespaces must be classified: either session
# identity (the conftest tuple) or host configuration (below). Other names
# (PATH, ANTHROPIC_*, GIT_OPTIONAL_LOCKS, ...) are provider or host setup.
_IDENTITY_NAMESPACES = ("LEARN_UKRAINIAN_", "LU_", "SESSION_", "CODEX_", "CLAUDE_CODE_SESSION")

# Exported in an identity namespace, but host or tool configuration that tests
# may inherit. Each entry is a deliberate decision, not a default.
_HOST_CONFIG_EXPORTS = frozenset(
    {
        "CODEX_CANONICAL_REPO_ROOT",  # checkout path, not a session
        "CODEX_CC_AUTH_SOURCE",  # credential provenance label
        "LU_AGENT_GITHUB_IDENTITY_SOURCE",  # credential provenance label
        "LEARN_UKRAINIAN_LOCK_TIMEOUT_SECONDS",  # SessionStart-local subprocess bound
        "LU_AGENT_COMM_TRANSPORT",  # fleet comms transport choice
        "LU_MONITOR_HOST_ID",  # this host, shared by every session on it
        "LU_RUNTIME_TMP_BASE_ROOT",  # storage root
        "LU_RUNTIME_TMP_ROOT",  # storage root
    }
)

_SHELL_EXPORT = re.compile(r"\bexport\s+([A-Z_][A-Z0-9_]*(?:\s+[A-Z_][A-Z0-9_]*)*)\s*(?==|$|;|\\n|')")
_SUPERVISOR_KEY = re.compile(r'^\s*(?:exports\[)?"(SESSION_STREAM_[A-Z0-9_]+)"\]?\s*[:=]', re.MULTILINE)
_PROFILE_KEYS = re.compile(r"^\s*(PROFILE_ID\|[A-Z0-9_|]+)\)\s*$", re.MULTILINE)


def _shell_exports() -> set[str]:
    names: set[str] = set()
    for path in _SHELL_EXPORT_SITES:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("#"):
                continue
            for match in _SHELL_EXPORT.finditer(line):
                names.update(match.group(1).split())
    return names


def _session_record_env_file_names() -> set[str]:
    tree = ast.parse(_SESSION_RECORD.read_text(encoding="utf-8"))
    function = next(
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "append_to_env_file"
    )
    names = {
        key.value
        for node in ast.walk(function)
        if isinstance(node, ast.Dict)
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    assert names, "append_to_env_file no longer builds a literal export dict; update this parser"
    return names


def _profile_resolver_names() -> set[str]:
    match = _PROFILE_KEYS.search(_PROFILE_RESOLVER.read_text(encoding="utf-8"))
    assert match, "profile_resolver.sh key allowlist moved; update this parser"
    return {f"LEARN_UKRAINIAN_{key}" for key in match.group(1).split("|")}


def _is_env_mapping(node: ast.expr) -> bool:
    name = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else None
    return name is not None and (name in {"env", "environ"} or name.endswith("_env"))


def _python_env_assignment_names(source: str) -> set[str]:
    """String keys written into an ``env``/``environ``/``*_env`` mapping.

    Covers ``env["X"] = ...``, ``env.update({"X": ...})``, ``env.update(X=...)``
    and ``env.setdefault("X", ...)``.
    """
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        targets = node.targets if isinstance(node, ast.Assign) else []
        if isinstance(node, ast.AugAssign | ast.AnnAssign):
            targets = [node.target]
        names.update(
            target.slice.value
            for target in targets
            if isinstance(target, ast.Subscript)
            and _is_env_mapping(target.value)
            and isinstance(target.slice, ast.Constant)
            and isinstance(target.slice.value, str)
        )
        if not (
            isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and _is_env_mapping(node.func.value)
        ):
            continue
        if node.func.attr == "update":
            names.update(keyword.arg for keyword in node.keywords if keyword.arg)
            names.update(
                key.value
                for arg in node.args
                if isinstance(arg, ast.Dict)
                for key in arg.keys
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            )
        elif node.func.attr == "setdefault" and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                names.add(first.value)
    return names


def _telemetry_minted_names() -> set[str]:
    """Names ``_current_or_new_env_id`` mints into ``os.environ`` when absent."""
    tree = ast.parse(_TELEMETRY.read_text(encoding="utf-8"))
    constants = {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    return {
        constants[node.args[0].id]
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_current_or_new_env_id"
        and node.args
        and isinstance(node.args[0], ast.Name)
    }


def _identity_namespace(names: set[str]) -> set[str]:
    return {name for name in names if name.startswith(_IDENTITY_NAMESPACES)}


def _exported_identity_namespace_names() -> dict[str, set[str]]:
    sites = {
        "shell export sites": _shell_exports(),
        "session_supervisor.sh lease capsule": set(
            _SUPERVISOR_KEY.findall(_SESSION_SUPERVISOR.read_text(encoding="utf-8"))
        ),
        "profile_resolver.sh": _profile_resolver_names(),
        "session_record.append_to_env_file": _session_record_env_file_names(),
        "telemetry ids": _telemetry_minted_names(),
        **{
            str(path.relative_to(REPO_ROOT)): _python_env_assignment_names(path.read_text(encoding="utf-8"))
            for path in _PYTHON_ENV_SITES
        },
    }
    return {site: _identity_namespace(names) for site, names in sites.items()}


def _unclassified(sites: dict[str, set[str]]) -> dict[str, list[str]]:
    covered = set(SESSION_IDENTITY_ENV_VARS) | _HOST_CONFIG_EXPORTS
    return {site: sorted(names - covered) for site, names in sites.items() if names - covered}


def test_parsers_see_the_known_export_sites() -> None:
    """Guard the parsers themselves: a silent zero match would pass vacuously."""
    sites = _exported_identity_namespace_names()
    assert "SESSION_HANDOFF_AGENT" in sites["shell export sites"]
    assert "LEARN_UKRAINIAN_THREAD_LEASE_GENERATION" in sites["shell export sites"]
    assert "CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID" in sites["shell export sites"]
    assert "SESSION_STREAM_SESSION_ID" in sites["session_supervisor.sh lease capsule"]
    assert "LEARN_UKRAINIAN_MAIN_MODEL_ID" in sites["profile_resolver.sh"]
    assert "LEARN_UKRAINIAN_SESSION_ID" in sites["session_record.append_to_env_file"]
    assert "LEARN_UKRAINIAN_DISPATCH_TASK_ID" in sites["scripts/delegate.py"]
    assert "LU_X_AGENT_TRAILER" in sites["scripts/delegate.py"]
    assert {"LEARN_UKRAINIAN_CLAUDEX_RUN_ID", "LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION"} <= sites[
        "scripts/orchestration/claudex_supervisor.py"
    ]
    assert "LU_SESSION_ID" in sites["telemetry ids"]


def test_python_env_parser_sees_every_assignment_form() -> None:
    source = """
os.environ["LU_A"] = "1"
env["LU_B"] = "1"
worker_env["LU_C"] = "1"
launch_env.update({"LU_D": "1"})
launch_env.update(LU_E="1")
env.setdefault("LU_F", "1")
unrelated["LU_G"] = "1"
"""
    assert _python_env_assignment_names(source) == {"LU_A", "LU_B", "LU_C", "LU_D", "LU_E", "LU_F"}


def test_a_new_supervisor_export_fails_the_completeness_check() -> None:
    source = _SUPERVISOR.read_text(encoding="utf-8")
    anchor = '"LEARN_UKRAINIAN_CLAUDEX_RUN_ID": self.run_id,'
    assert anchor in source, "claudex_supervisor launch env moved; update this test"
    patched = source.replace(anchor, f'{anchor}\n"LEARN_UKRAINIAN_CLAUDEX_NEW_ID": "x",')
    sites = {"supervisor": _identity_namespace(_python_env_assignment_names(patched))}
    assert _unclassified(sites) == {"supervisor": ["LEARN_UKRAINIAN_CLAUDEX_NEW_ID"]}


def test_every_exported_session_identity_name_is_stripped() -> None:
    unclassified = _unclassified(_exported_identity_namespace_names())
    assert not unclassified, (
        "New session-scoped exports: add session identity to SESSION_IDENTITY_ENV_VARS in "
        f"tests/conftest.py, or host configuration to _HOST_CONFIG_EXPORTS here: {unclassified}"
    )


def test_identity_tuple_has_no_duplicates_or_host_config() -> None:
    assert len(SESSION_IDENTITY_ENV_VARS) == len(set(SESSION_IDENTITY_ENV_VARS))
    assert not set(SESSION_IDENTITY_ENV_VARS) & _HOST_CONFIG_EXPORTS


@pytest.mark.parametrize("name", SESSION_IDENTITY_ENV_VARS)
def test_identity_variable_is_absent_inside_tests(name: str) -> None:
    assert name not in os.environ


_NESTED_TEST = """
import os
import pytest

NAME = "LEARN_UKRAINIAN_SESSION_ID"
SEEN = {}


@pytest.fixture(scope="session", autouse=True)
def session_fixture():
    SEEN["session"] = os.environ.get(NAME)


@pytest.fixture(autouse=True)
def function_fixture(monkeypatch):
    SEEN["function"] = os.environ.get(NAME)
    yield
    SEEN["teardown"] = os.environ.get(NAME)


def test_identity_is_absent_from_every_fixture():
    SEEN["call"] = os.environ.get(NAME)
    os.environ[NAME] = "set-by-test"


def test_report():
    assert SEEN == {"session": None, "function": None, "call": None, "teardown": "set-by-test"}
"""


def test_isolation_runs_before_every_fixture_and_restores_after(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A leaked identity is invisible to session and function fixtures (#8778)."""
    pytester.makeconftest(
        f"""
import importlib.util
spec = importlib.util.spec_from_file_location("project_tests_conftest", {str(REPO_ROOT / "tests" / "conftest.py")!r})
project_tests_conftest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project_tests_conftest)
pytest_runtest_protocol = project_tests_conftest.pytest_runtest_protocol


def pytest_sessionfinish(session):
    import os
    print("AFTER", os.environ.get("LEARN_UKRAINIAN_SESSION_ID"))
"""
    )
    pytester.makepyfile(_NESTED_TEST)
    monkeypatch.setenv("LEARN_UKRAINIAN_SESSION_ID", "live-operator-session")
    # A dispatch worker exports the repo's ci.* xdist cap plugin, which a
    # pytest rooted outside the repo cannot import.
    monkeypatch.delenv("PYTEST_PLUGINS", raising=False)

    result = pytester.runpytest_subprocess("-q", "-s")

    result.assert_outcomes(passed=2)
    # The test's own write is undone; the launching session's value returns.
    result.stdout.fnmatch_lines(["*AFTER live-operator-session"])
