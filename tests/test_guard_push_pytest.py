"""Unit tests for the #M-7 direct-main push pytest guard."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-push-pytest.py"
STAMP_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "stamp-pytest.sh"


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_push_pytest", GUARD_PATH)
    assert spec and spec.loader, f"could not load hook at {GUARD_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_hook()


def _run(
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    *,
    branch: str = "main",
    paths: tuple[str, ...] = ("tests/test_guard_push_pytest.py",),
    marker_fresh: bool | None = False,
) -> int:
    payload = json.dumps({"tool_input": {"command": command}})
    marker = Path("/tmp/learn-uk-pytest.main.stamp")
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setattr(guard, "_current_branch", lambda: branch)
    monkeypatch.setattr(guard, "_changed_paths", lambda: list(paths))
    monkeypatch.setattr(guard, "_marker_path", lambda _branch: marker)
    monkeypatch.setattr(guard, "_marker_is_fresh", lambda _marker: marker_fresh)
    monkeypatch.delenv("SKIP_PYTEST_HOOK", raising=False)
    return guard.main()


def test_push_to_main_with_trigger_path_and_stale_marker_blocks(monkeypatch, capsys):
    assert _run(monkeypatch, "git push origin main") == 2
    err = capsys.readouterr().err
    assert "/tmp/learn-uk-pytest.main.stamp" in err
    assert "SKIP_PYTEST_HOOK=1" in err


def test_push_to_main_with_fresh_marker_allows(monkeypatch):
    assert _run(monkeypatch, "git push origin main", marker_fresh=True) == 0


def test_non_main_branch_allows(monkeypatch):
    assert _run(monkeypatch, "git push -u origin feature", branch="feature") == 0


def test_non_push_command_allows(monkeypatch):
    assert _run(monkeypatch, "git status") == 0


def test_skip_env_allows(monkeypatch):
    payload = json.dumps({"tool_input": {"command": "git push origin main"}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setenv("SKIP_PYTEST_HOOK", "1")
    assert guard.main() == 0


def test_quoted_push_in_commit_body_allows(monkeypatch):
    assert _run(monkeypatch, 'git commit -m "docs: mention git push origin main"') == 0


def test_dry_run_push_allows(monkeypatch):
    assert _run(monkeypatch, "git push --dry-run origin main") == 0


def test_non_trigger_diff_allows(monkeypatch):
    assert _run(monkeypatch, "git push origin main", paths=("README.md",)) == 0


def test_hook_errors_fail_open(monkeypatch):
    payload = json.dumps({"tool_input": {"command": "git push origin main"}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setattr(guard, "_current_branch", lambda: None)
    monkeypatch.delenv("SKIP_PYTEST_HOOK", raising=False)
    assert guard.main() == 0


def test_stamp_pytest_bash_smoke(tmp_path):
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    marker = tmp_path / f"learn-uk-pytest.{branch}.stamp"
    payload = json.dumps({"tool_input": {"command": ".venv/bin/python -m pytest tests/test_guard_push_pytest.py -q"}})
    env = os.environ.copy()
    env["TMPDIR"] = str(tmp_path)

    result = subprocess.run(
        [str(STAMP_PATH)],
        cwd=REPO_ROOT,
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert marker.exists()
