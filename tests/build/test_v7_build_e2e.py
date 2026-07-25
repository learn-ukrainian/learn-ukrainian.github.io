from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from scripts.orchestration.reap_worktrees import primary_checkout_root

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Always invoke from the primary checkout. Local agents often run pytest from a
# dispatch worktree, which accidentally satisfies the primary-checkout guard and
# hides the CI failure mode (#5766 residue). Pass --worktree — the escape the
# guard documents — so the entrypoint provisions an isolated build worktree.
INVOCATION_ROOT = primary_checkout_root(PROJECT_ROOT).resolve()


def _json_events(stdout: str) -> list[dict[str, Any]]:
    """Parse JSONL telemetry; ignore non-JSON --worktree summary lines."""
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _run_dry_run(*extra_args: str) -> subprocess.CompletedProcess[str]:
    assert (INVOCATION_ROOT / ".git").is_dir(), (
        f"e2e must invoke v7_build from a primary checkout, got {INVOCATION_ROOT}"
    )
    return subprocess.run(
        [
            ".venv/bin/python",
            "scripts/build/v7_build.py",
            "a1",
            "my-morning",
            *extra_args,
            "--dry-run",
            "--worktree",
        ],
        cwd=INVOCATION_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )


def test_v7_build_dry_run_emits_module_start() -> None:
    result = _run_dry_run()

    assert result.returncode == 0, result.stderr
    events = _json_events(result.stdout)

    assert events[0]["event"] == "module_start"
    assert events[0]["level"] == "a1"
    assert events[0]["slug"] == "my-morning"


def test_v7_build_dry_run_accepts_writer_alias() -> None:
    result = _run_dry_run("--writer", "gemini")

    assert result.returncode == 0, result.stderr
    events = _json_events(result.stdout)

    assert events[-1]["event"] == "module_done"
    assert events[-1]["dry_run"] is True
