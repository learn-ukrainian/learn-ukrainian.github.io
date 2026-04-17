"""Worktree registry — what's checked out where (#1313 / Codex-5).

Mounted at /api/worktrees in main.py.

Endpoints:
    GET /api/worktrees      Active git worktrees + per-wt metadata

Why this exists: this session lost time to confusion about which
worktree held which branch. A deterministic view — "here are all the
worktrees right now, what branch each is on, whether it's dirty" —
prevents that. Read-only: never modifies git state.

Parses ``git worktree list --porcelain``, enriches with
``git status --porcelain=v1`` for a cheap dirty/clean check and
``git log -1`` for the last commit. No shell=True; no tainted input
makes it to the process args.
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from .config import PROJECT_ROOT

router = APIRouter(tags=["worktrees"])

# Keep the per-subprocess timeout tight — a wedged NFS mount or
# hanging git hook would otherwise block the response. Each call is
# bounded; the aggregate endpoint budget is ~4 × timeout_s per
# worktree.
_GIT_TIMEOUT_S = 2.0


def _run(cmd: list[str], cwd: Path, timeout_s: float = _GIT_TIMEOUT_S) -> tuple[int, str, str]:
    """Subprocess helper that never raises. Mirrors the pattern used
    in ``site_router._run`` — see that file for the rationale.
    """
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"TimeoutExpired after {exc.timeout}s"
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return 127, "", f"{type(exc).__name__}: {exc}"


def _parse_worktree_list(porcelain: str) -> list[dict[str, Any]]:
    """Parse ``git worktree list --porcelain`` output.

    Format (blank-line separated, one record per worktree):
        worktree /abs/path
        HEAD <sha>
        branch refs/heads/<name>     (or `detached`)
        <prunable>                    (optional)
        locked <reason>               (optional)

    See ``man git-worktree`` for the full grammar.
    """
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in porcelain.splitlines():
        if not line.strip():
            if current:
                records.append(current)
                current = {}
            continue
        if " " in line:
            key, _, value = line.partition(" ")
        else:
            key, value = line, ""
        if key == "worktree":
            current["path"] = value
        elif key == "HEAD":
            current["head"] = value
        elif key == "branch":
            # "refs/heads/xyz" → "xyz"; detached HEAD sends "detached".
            current["branch"] = value.removeprefix("refs/heads/") if value else None
        elif key == "detached":
            current["branch"] = None
            current["detached"] = True
        elif key in {"locked", "prunable"}:
            current[key] = value or True

    if current:
        records.append(current)
    return records


def _wt_status(path: Path) -> dict[str, Any]:
    """Cheap dirty/clean + last-commit check for one worktree.

    Returns an ``error`` field when git can't answer — e.g. the
    worktree directory has been deleted without ``git worktree
    remove``. Callers should still surface the record.
    """
    out: dict[str, Any] = {}

    if not path.is_dir():
        return {"error": "worktree path missing on disk"}

    code, stdout, stderr = _run(["git", "status", "--porcelain=v1"], cwd=path)
    if code != 0:
        out["status_error"] = stderr.strip()
    else:
        out["dirty"] = bool(stdout.strip())
        # Compact change-type summary without dumping the whole file list.
        types: set[str] = set()
        for line in stdout.splitlines():
            if len(line) >= 2:
                types.add(line[:2].strip())
        out["change_types"] = sorted(types)

    code, stdout, stderr = _run(
        ["git", "log", "-1", "--format=%h %cI %s"],
        cwd=path,
    )
    if code == 0 and stdout.strip():
        parts = stdout.strip().split(" ", 2)
        out["last_commit"] = {
            "sha": parts[0] if parts else None,
            "committed_at": parts[1] if len(parts) > 1 else None,
            "subject": parts[2] if len(parts) > 2 else "",
        }
    elif stderr:
        out["log_error"] = stderr.strip()

    return out


@router.get("")
async def list_worktrees():
    """Active git worktrees with per-worktree status.

    Shape::
        {
          "count": 3,
          "worktrees": [
            {
              "path": "/abs/path",
              "branch": "main" | null,
              "detached": false,
              "head": "abc1234...",
              "dirty": false,
              "change_types": ["M", "??"],
              "last_commit": {"sha": "...", "committed_at": "...", "subject": "..."},
              "is_primary": true
            },
            ...
          ]
        }

    ``is_primary`` flags the main worktree (the one whose ``path``
    matches ``PROJECT_ROOT``). Every other worktree was created with
    ``git worktree add`` and is a sibling checkout.

    Reviewer Codex-5 / #1313: "would have prevented the branch /
    worktree confusion we hit". Read-only; never mutates git state.
    """
    def _compute() -> dict:
        code, stdout, stderr = _run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=PROJECT_ROOT,
        )
        if code != 0:
            return {
                "count": 0,
                "worktrees": [],
                "error": stderr.strip() or "git worktree list failed",
            }

        parsed = _parse_worktree_list(stdout)
        project_root_str = str(PROJECT_ROOT.resolve())
        enriched: list[dict[str, Any]] = []
        for record in parsed:
            path_str = record.get("path")
            if not path_str:
                continue
            wt_path = Path(path_str)
            record["is_primary"] = (
                wt_path.resolve().as_posix() == Path(project_root_str).as_posix()
            )
            record.update(_wt_status(wt_path))
            enriched.append(record)

        return {"count": len(enriched), "worktrees": enriched}

    return await asyncio.to_thread(_compute)
