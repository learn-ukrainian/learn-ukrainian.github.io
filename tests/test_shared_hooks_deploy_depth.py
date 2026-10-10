"""Run shared Bash Python hooks at their source and deployed depths."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_ROOT = REPO_ROOT / "agents_extensions" / "shared" / "hooks"
SETTINGS = REPO_ROOT / "agents_extensions" / "shared" / "settings.json"


def test_shell_shlex_importers_do_not_write_bytecode() -> None:
    """Guards must disable bytecode before importing the sibling helper (#9108)."""
    importers = sorted(HOOKS_ROOT.glob("*.py"))
    found = False
    for path in importers:
        text = path.read_text(encoding="utf-8")
        marker = "from shell_shlex import"
        if marker not in text:
            continue
        found = True
        assert text.index("sys.dont_write_bytecode = True") < text.index(marker), path.name
    assert found


@pytest.mark.parametrize("hook_name", ["guard-admin-merge.py", "guard-branch-switch-in-main.py", "guard-pr-merge.py"])
@pytest.mark.parametrize("helper", ["shell_bash"])
@pytest.mark.parametrize("failure", ["missing", "syntax", "raises"])
def test_issue_9479_broken_helper_fails_closed(tmp_path, hook_name, helper, failure):
    hooks = tmp_path / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    for name in (hook_name, "shell_bash.py"):
        if name == helper + ".py" and failure == "missing":
            continue
        shutil.copy2(HOOKS_ROOT / name, hooks / name)
    if failure != "missing":
        (hooks / (helper + ".py")).write_text(
            "def broken(:\n" if failure == "syntax" else "raise RuntimeError('fixture failure')\n"
        )
    result = subprocess.run(
        [sys.executable, str(hooks / hook_name)],
        input=json.dumps({"tool_input": {"command": "git switch -c fixture && gh pr merge 5 --admin"}}),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2, result.stderr
    assert "guard dependency unavailable: shell_bash" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (hooks / "__pycache__").exists()


def _bash_python_hooks() -> tuple[str, ...]:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    names = {
        Path(shlex.split(hook["command"])[-1]).name
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
def test_shared_bash_python_hook_runs_at_both_depths(tmp_path: Path, hook_name: str, layout: str) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=30)
    (repo / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)

    relative_hooks = Path("agents_extensions/shared/hooks") if layout == "source" else Path(".claude/hooks")
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
        subprocess.run(["git", "config", "core.bare", "true"], cwd=repo, check=True, timeout=30)
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


@pytest.mark.parametrize("hook_name", ["guard-pr-merge.py", "guard-branch-switch-in-main.py", "guard-admin-merge.py"])
def test_guard_wrapper_ignores_system_python_on_path(tmp_path, hook_name):
    import os

    fake = tmp_path / "python3"
    fake.write_text("#!/bin/sh\nexit 99\n")
    fake.chmod(0o755)
    wrapper = HOOKS_ROOT / "run-project-python-hook.sh"
    result = subprocess.run(
        ["bash", str(wrapper), hook_name],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "CLAUDE_PROJECT_DIR": str(REPO_ROOT),
            "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"],
        },
        input=json.dumps({"tool_input": {"command": "echo 'git checkout -b fixture; gh pr merge 5 --admin'"}}),
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr


_GUARDED_HOOKS = ["guard-pr-merge.py", "guard-branch-switch-in-main.py", "guard-admin-merge.py"]


@pytest.mark.parametrize("hook_name", _GUARDED_HOOKS)
@pytest.mark.parametrize(
    "failure",
    [
        "no_git",
        "git_failure",
        "missing_project",
        "missing_helper",
        "helper_exit",
        "missing_interpreter",
        "invalid_interpreter",
    ],
)
@pytest.mark.parametrize(
    "command,expected",
    [("ls", 0), ("uv sync", 0), ("git status", 0), ("git switch -c fixture && gh pr merge 5 --admin", 2)],
)
def test_guard_wrapper_errors_keep_unrelated_commands_usable(tmp_path, hook_name, failure, command, expected):
    project = tmp_path / "project"
    project.mkdir()
    helper = project / "scripts/lib/project_interpreter.sh"
    helper.parent.mkdir(parents=True)
    helper.write_text("project_interpreter_resolve() { return 1; }\n")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project)}
    binaries = tmp_path / "bin"
    binaries.mkdir()
    # Deliberately use the wrong interpreter: it has no pinned parser packages.
    # No project virtualenv is created, copied, or used by these error fixtures.
    wrong_python = shutil.which("python3", path="/usr/bin:/bin")
    assert wrong_python
    (binaries / "python3").symlink_to(wrong_python)
    (binaries / "dirname").symlink_to(shutil.which("dirname"))
    env["PATH"] = str(binaries)
    if failure in {"no_git", "git_failure"}:
        env.pop("CLAUDE_PROJECT_DIR")
        if failure == "git_failure":
            git = binaries / "git"
            git.write_text("#!/bin/sh\nexit 128\n")
            git.chmod(0o755)
    elif failure == "missing_project":
        env["CLAUDE_PROJECT_DIR"] = str(tmp_path / "absent")
    elif failure == "missing_helper":
        helper.unlink()
    elif failure == "helper_exit":
        helper.write_text("exit 1\n")
    elif failure == "missing_interpreter":
        shutil.copy2(REPO_ROOT / "scripts/lib/project_interpreter.sh", helper)
    elif failure == "invalid_interpreter":
        helper.write_text("project_interpreter_resolve() { printf '%s' /nonexistent/guard-python; }\n")
    result = subprocess.run(
        ["/bin/bash", str(HOOKS_ROOT / "run-project-python-hook.sh"), hook_name],
        cwd=tmp_path,
        env=env,
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == expected, result.stderr
    assert "Traceback" not in result.stderr
    if expected:
        assert "guard dependency unavailable: shell_bash" in result.stderr
        assert "repair:" in result.stderr


@pytest.mark.parametrize("hook_name", _GUARDED_HOOKS)
@pytest.mark.parametrize(
    "failure", ["no_python", "hook_missing", "interpreter_exits_1", "interpreter_exits_128", "helper_syntax"]
)
def test_guard_wrapper_never_returns_an_allow_error(tmp_path, hook_name, failure):
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    shutil.copy2(HOOKS_ROOT / "run-project-python-hook.sh", hooks)
    if failure != "hook_missing":
        shutil.copy2(HOOKS_ROOT / hook_name, hooks)
    project = tmp_path / "project"
    helper = project / "scripts/lib/project_interpreter.sh"
    helper.parent.mkdir(parents=True)
    helper.write_text("project_interpreter_resolve() { return 1; }\n")
    binaries = tmp_path / "bin"
    binaries.mkdir()
    (binaries / "dirname").symlink_to(shutil.which("dirname"))
    if failure != "no_python":
        (binaries / "python3").symlink_to(shutil.which("python3", path="/usr/bin:/bin"))
    if failure.startswith("interpreter_exits_"):
        interpreter = tmp_path / "fixture-interpreter"
        interpreter.write_text("#!/bin/sh\nexit " + failure.rsplit("_", 1)[1] + "\n")
        interpreter.chmod(0o755)
        helper.write_text("project_interpreter_resolve() { printf '%s' " + shlex.quote(str(interpreter)) + "; }\n")
    elif failure == "helper_syntax":
        helper.write_text("this is not valid ( shell syntax\n")
    result = subprocess.run(
        ["/bin/bash", str(hooks / "run-project-python-hook.sh"), hook_name],
        cwd=tmp_path,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(project), "PATH": str(binaries)},
        input=json.dumps({"tool_input": {"command": "git switch -c fixture && gh pr merge 5 --admin"}}),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2, result.stderr


def test_guard_wrapper_unknown_hook_is_blocked(tmp_path):
    result = subprocess.run(
        ["/bin/bash", str(HOOKS_ROOT / "run-project-python-hook.sh"), "unknown.py"],
        cwd=tmp_path,
        input=json.dumps({"tool_input": {"command": "git checkout -b fixture"}}),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert "BLOCKED: unknown guard hook" in result.stderr
