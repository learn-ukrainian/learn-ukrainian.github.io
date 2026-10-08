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


@pytest.mark.skipif(shutil.which("jq") is None, reason="jq is required by the hook")
def test_post_compact_memory_hint_uses_the_primary_checkout_from_a_worktree(tmp_path: Path) -> None:
    primary = tmp_path / "learn-ukrainian"
    primary.mkdir()
    _git("init", "-q", "-b", "main", cwd=primary)
    _git(
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.invalid",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        "init",
        cwd=primary,
    )
    worktree = primary / ".worktrees" / "dispatch" / "lane"
    _git("worktree", "add", "-q", "--detach", str(worktree), cwd=primary)
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("CODEX_", "CLAUDE_", "SESSION_", "GROK_", "GEMINI_"))
        and key != "LEARN_UKRAINIAN_PIPELINE"
    }
    environment.update(
        CLAUDE_PROJECT_DIR=str(worktree),
        SESSION_HANDOFF_AGENT="claude",
        THREAD_ROLLOVER_PYTHON=sys.executable,
        THREAD_ROLLOVER_SCRIPT=str(tmp_path / "absent.py"),
        SESSION_BOUNDED_RUNNER=str(RUNNER),
    )
    result = subprocess.run(
        ["bash", str(HOOK)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)["additionalContext"]
    memory = next(line for line in context.splitlines() if "MEMORY:" in line)
    assert f"/{_key(str(primary.resolve()))}/memory/MEMORY.md" in memory
    assert _key(str(worktree)) not in memory
