"""Run shared Bash Python hooks at their source and deployed depths."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_ROOT = REPO_ROOT / "agents_extensions" / "shared" / "hooks"
SETTINGS = REPO_ROOT / "agents_extensions" / "shared" / "settings.json"


def _bash_python_hooks() -> tuple[str, ...]:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    names = {
        Path(hook["command"]).name
        for group in settings["hooks"]["PreToolUse"]
        if group["matcher"] == "Bash"
        for hook in group["hooks"]
        if hook["command"].endswith(".py")
    }
    assert names
    assert all((HOOKS_ROOT / name).is_file() for name in names)
    return tuple(sorted(names))


@pytest.mark.parametrize("hook_name", _bash_python_hooks())
@pytest.mark.parametrize("layout", ["source", "deployed"])
def test_shared_bash_python_hook_runs_at_both_depths(
    tmp_path: Path, hook_name: str, layout: str
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=30)
    (repo / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)

    relative_hooks = (
        Path("agents_extensions/shared/hooks")
        if layout == "source"
        else Path(".claude/hooks")
    )
    hooks_dir = repo / relative_hooks
    hooks_dir.parent.mkdir(parents=True)
    shutil.copytree(HOOKS_ROOT, hooks_dir)
    hook = hooks_dir / hook_name

    def run_hook(command: str) -> subprocess.CompletedProcess[str]:
        payload = {"tool_name": "Bash", "tool_input": {"command": command}}
        result = subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            cwd=repo,
            timeout=30,
        )
        assert "Traceback" not in result.stderr, result.stderr
        assert result.returncode == 0, (hook_name, layout, command, result.stderr)
        return result

    run_hook("git status")
    run_hook("true")

    if hook_name == "heal-core-bare.py":
        subprocess.run(
            ["git", "config", "core.bare", "true"], cwd=repo, check=True, timeout=30
        )
        run_hook("git status")
        bare = subprocess.run(
            ["git", "config", "core.bare"],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
        assert bare.stdout.strip() == "false"


def test_guard_without_sibling_helper_fails_closed(tmp_path: Path) -> None:
    hook = tmp_path / ".claude" / "hooks" / "guard-secret-print.py"
    hook.parent.mkdir(parents=True)
    shutil.copy2(HOOKS_ROOT / hook.name, hook)

    payload = {"tool_name": "Bash", "tool_input": {"command": "git status"}}
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=tmp_path,
        timeout=30,
    )
    assert result.returncode == 2
    assert "guard dependency unavailable: shell_shlex" in result.stderr
    assert "Traceback" not in result.stderr


def test_heal_core_bare_silently_allows_missing_repo_marker(tmp_path: Path) -> None:
    hook = tmp_path / ".claude" / "hooks" / "heal-core-bare.py"
    hook.parent.mkdir(parents=True)
    shutil.copy2(HOOKS_ROOT / hook.name, hook)

    for command in ("git status", "true"):
        payload = {"tool_name": "Bash", "tool_input": {"command": command}}
        result = subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            cwd=tmp_path,
            timeout=30,
        )
        assert result.returncode == 0
        assert result.stdout == result.stderr == ""
