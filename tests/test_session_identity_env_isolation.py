"""The suite strips every live agent session identity variable (#8778).

``tests/conftest.py`` deletes ``SESSION_IDENTITY_ENV_VARS`` before each test.
This module parses the sites that export identity into an agent session and
fails when one of them exports a name the tuple does not cover.
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path

import pytest

from tests.conftest import SESSION_IDENTITY_ENV_VARS

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
_DELEGATE = REPO_ROOT / "scripts" / "delegate.py"
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
_WORKER_ENV_KEY = re.compile(r'worker_env\["([A-Z_][A-Z0-9_]*)"\]\s*=')


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


def _delegate_worker_env_names() -> set[str]:
    source = _DELEGATE.read_text(encoding="utf-8")
    start = source.index("def _build_worker_env(")
    end = source.index("\ndef ", start + 1)
    return set(_WORKER_ENV_KEY.findall(source[start:end]))


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


def _exported_identity_namespace_names() -> dict[str, set[str]]:
    sites = {
        "shell export sites": _shell_exports(),
        "session_supervisor.sh lease capsule": set(
            _SUPERVISOR_KEY.findall(_SESSION_SUPERVISOR.read_text(encoding="utf-8"))
        ),
        "profile_resolver.sh": _profile_resolver_names(),
        "session_record.append_to_env_file": _session_record_env_file_names(),
        "delegate worker env": _delegate_worker_env_names(),
        "telemetry ids": _telemetry_minted_names(),
    }
    return {site: {name for name in names if name.startswith(_IDENTITY_NAMESPACES)} for site, names in sites.items()}


def test_parsers_see_the_known_export_sites() -> None:
    """Guard the parsers themselves: a silent zero match would pass vacuously."""
    sites = _exported_identity_namespace_names()
    assert "SESSION_HANDOFF_AGENT" in sites["shell export sites"]
    assert "LEARN_UKRAINIAN_THREAD_LEASE_GENERATION" in sites["shell export sites"]
    assert "CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID" in sites["shell export sites"]
    assert "SESSION_STREAM_SESSION_ID" in sites["session_supervisor.sh lease capsule"]
    assert "LEARN_UKRAINIAN_MAIN_MODEL_ID" in sites["profile_resolver.sh"]
    assert "LEARN_UKRAINIAN_SESSION_ID" in sites["session_record.append_to_env_file"]
    assert "LEARN_UKRAINIAN_DISPATCH_TASK_ID" in sites["delegate worker env"]
    assert "LU_SESSION_ID" in sites["telemetry ids"]


def test_every_exported_session_identity_name_is_stripped() -> None:
    covered = set(SESSION_IDENTITY_ENV_VARS) | _HOST_CONFIG_EXPORTS
    unclassified = {
        site: sorted(names - covered) for site, names in _exported_identity_namespace_names().items() if names - covered
    }
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
