"""Claude project-directory keys: token report matching and the post-compact memory hint."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "agents_extensions/shared/hooks/post-compact.sh"
RUNNER = ROOT / "scripts/agent_runtime/bounded_command.py"

_spec = importlib.util.spec_from_file_location("token_usage_under_test", ROOT / "scripts/token_usage.py")
assert _spec and _spec.loader
token_usage = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(token_usage)


def _key(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9-]", "-", path)


@pytest.mark.parametrize(
    ("checkout", "expected"),
    [
        ("/work/learn-ukrainian", "learn-ukrainian"),
        ("/work/learn-ukrainian/.worktrees/dispatch/codex/issue-1", "learn-ukrainian"),
        ("/work/learn-ukrainian/.claude/worktrees/feature", "learn-ukrainian"),
        ("/work/kubedojo", "kubedojo"),
        ("/work/kubedojo/.worktrees/lane", "kubedojo"),
        # Sibling copies and other checkouts are never counted.
        ("/work/learn-ukrainian--backup", None),
        ("/work/learn-ukrainian__backup", None),
        ("/work/learn-ukrainian/.cache/x", None),
        ("/work/learn-ukrainian-infra-private", None),
        ("/work/other", None),
    ],
)
def test_project_name_matches_only_the_checkout_and_its_worktrees(checkout, expected) -> None:
    assert token_usage.resolve_project_name(_key(checkout)) == expected


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=30)


ROLLOVER_STUB = """import sys
print("rollover-stub " + " ".join(sys.argv[1:]))
"""


def _primary_with_worktree(tmp_path: Path) -> tuple[Path, Path]:
    """A primary checkout and a linked worktree; the worktree has no venv."""
    primary = tmp_path / "learn-ukrainian"
    primary.mkdir()
    _git("init", "-q", "-b", "main", cwd=primary)
    runner = primary / "scripts/agent_runtime/bounded_command.py"
    runner.parent.mkdir(parents=True)
    shutil.copyfile(RUNNER, runner)
    rollover = primary / "scripts/orchestration/thread_handoff.py"
    rollover.parent.mkdir(parents=True)
    rollover.write_text(ROLLOVER_STUB)
    _git("add", "scripts", cwd=primary)
    _git(
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.invalid",
        "commit",
        "-q",
        "-m",
        "init",
        cwd=primary,
    )
    worktree = primary / ".worktrees" / "dispatch" / "lane"
    _git("worktree", "add", "-q", "--detach", str(worktree), cwd=primary)
    return primary, worktree


def _run_hook(worktree: Path, **overrides: str) -> str:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("CODEX_", "CLAUDE_", "SESSION_", "GROK_", "GEMINI_", "THREAD_ROLLOVER_"))
        and key != "LEARN_UKRAINIAN_PIPELINE"
    }
    environment.update(CLAUDE_PROJECT_DIR=str(worktree), SESSION_HANDOFF_AGENT="claude", **overrides)
    result = subprocess.run(
        ["bash", str(HOOK)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["additionalContext"]


def _line(context: str, marker: str) -> str:
    return next(line for line in context.splitlines() if marker in line)


@pytest.mark.skipif(shutil.which("jq") is None, reason="jq is required by the hook")
def test_post_compact_memory_hint_uses_the_primary_checkout_from_a_worktree(tmp_path: Path) -> None:
    primary, worktree = _primary_with_worktree(tmp_path)
    context = _run_hook(
        worktree,
        THREAD_ROLLOVER_PYTHON=sys.executable,
        THREAD_ROLLOVER_SCRIPT=str(tmp_path / "absent.py"),
        SESSION_BOUNDED_RUNNER=str(RUNNER),
    )
    memory = _line(context, "MEMORY:")
    assert f"/{_key(str(primary.resolve()))}/memory/MEMORY.md" in memory
    assert _key(str(worktree)) not in memory


@pytest.mark.skipif(shutil.which("jq") is None, reason="jq is required by the hook")
def test_post_compact_uses_the_primary_checkout_venv_with_production_defaults(tmp_path: Path) -> None:
    # No interpreter, runner or rollover override: the shared venv exists only in
    # the primary checkout, exactly as for a real linked worktree.
    primary, worktree = _primary_with_worktree(tmp_path)
    venv_python = primary / ".venv/bin/python"
    venv_python.parent.mkdir(parents=True)
    venv_python.symlink_to(sys.executable)
    assert not (worktree / ".venv").exists()

    context = _run_hook(worktree)

    memory = _line(context, "MEMORY:")
    assert f"/{_key(str(primary.resolve()))}/memory/MEMORY.md" in memory
    assert _key(str(worktree)) not in memory
    # The rollover probe ran through the shared interpreter against the primary checkout.
    health = _line(context, "Thread rollover health")
    assert f"rollover-stub --repo-root {primary.resolve()} detect --agent claude" in health
