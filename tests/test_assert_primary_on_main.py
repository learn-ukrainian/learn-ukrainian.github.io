"""Tests for scripts/guardrails/assert_primary_on_main.py (#4857)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.guardrails.assert_primary_on_main import heal_primary_to_main, primary_head_state


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_PREFIX",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        env.pop(name, None)
    return subprocess.run(
        list(args),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )


@pytest.fixture
def primary_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    assert _run(root, "git", "init", "-b", "main").returncode == 0
    assert _run(root, "git", "config", "user.name", "Test").returncode == 0
    assert _run(root, "git", "config", "user.email", "t@example.invalid").returncode == 0
    assert _run(root, "git", "commit", "--allow-empty", "-m", "init").returncode == 0
    return root


def test_on_main_ok(primary_repo: Path) -> None:
    state = primary_head_state(primary_repo)
    assert state["ok"] is True
    assert state["branch"] == "main"


def test_detached_detected(primary_repo: Path) -> None:
    r = _run(primary_repo, "git", "switch", "--detach", "HEAD")
    assert r.returncode == 0, r.stderr
    state = primary_head_state(primary_repo)
    assert state["ok"] is False
    assert state["reason"] == "detached_head"


def test_heal_reattaches_main(primary_repo: Path) -> None:
    assert _run(primary_repo, "git", "switch", "--detach", "HEAD").returncode == 0
    ok, _detail = heal_primary_to_main(primary_repo)
    assert ok is True
    state = primary_head_state(primary_repo)
    assert state["ok"] is True
    assert state["branch"] == "main"


# ---------------------------------------------------------------------------
# CLI env gate (#5908): heal/assert must be inert outside operator contexts.
# CI checkouts are detached PR-merge SHAs BY DESIGN; healing one mid-test-run
# checkouts+pulls main under the live suite and swaps the source tree.
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI = _REPO_ROOT / "scripts" / "guardrails" / "assert_primary_on_main.py"
_GATE_ENVS = ("LEARN_UK_PRIMARY_HEAL_DISABLE", "GITHUB_ACTIONS", "CI")


def _run_cli(repo: Path, extra_env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    venv_python = _REPO_ROOT / ".venv" / "bin" / "python"
    if not venv_python.is_file():  # repo forbids sys.executable / bare python
        pytest.skip("project .venv interpreter not found; repo forbids sys.executable here")
    env = os.environ.copy()
    for name in _GATE_ENVS:
        env.pop(name, None)
    env.update(extra_env)
    return subprocess.run(
        [str(venv_python), str(_CLI), "--cwd", str(repo), *args],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )


def _is_detached(repo: Path) -> bool:
    r = _run(repo, "git", "rev-parse", "--abbrev-ref", "HEAD")
    return r.stdout.strip() == "HEAD"


@pytest.mark.parametrize("gate_env", ["GITHUB_ACTIONS", "CI", "LEARN_UK_PRIMARY_HEAL_DISABLE"])
def test_cli_heal_is_inert_in_non_operator_context(primary_repo: Path, gate_env: str) -> None:
    assert _run(primary_repo, "git", "switch", "--detach", "HEAD").returncode == 0
    r = _run_cli(primary_repo, {gate_env: "true"}, "--heal")
    assert r.returncode == 0, r.stderr
    assert "SKIP" in r.stdout
    assert _is_detached(primary_repo), (
        "heal MUTATED a detached checkout despite the non-operator gate — "
        "this is the mid-test tree-swap class (#5908)"
    )


def test_cli_falsey_gate_values_do_not_suppress(primary_repo: Path) -> None:
    assert _run(primary_repo, "git", "switch", "--detach", "HEAD").returncode == 0
    r = _run_cli(primary_repo, {"CI": "false", "GITHUB_ACTIONS": "0"}, "--heal")
    assert r.returncode == 0, r.stderr
    assert _is_detached(primary_repo) is False, "falsey gate values must not block the operator heal"


def test_cli_heal_still_heals_operator_context(primary_repo: Path) -> None:
    assert _run(primary_repo, "git", "switch", "--detach", "HEAD").returncode == 0
    r = _run_cli(primary_repo, {}, "--heal")
    assert r.returncode == 0, r.stderr
    assert _is_detached(primary_repo) is False
    state = primary_head_state(primary_repo)
    assert state["ok"] is True and state["branch"] == "main"
