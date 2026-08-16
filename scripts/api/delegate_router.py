"""Delegate observability API router."""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query

from .config import BATCH_STATE_DIR

router = APIRouter(tags=["delegate"])

TASKS_DIR = BATCH_STATE_DIR / "tasks"
RESULT_BYTES_LIMIT = 64 * 1024
TASK_READ_RETRIES = 2
TASK_READ_RETRY_SECONDS = 0.01
ACTIVE_TASK_STATUSES = {"running", "spawning"}
# Authoritative repository-attribution fields on task state. Paths, branch names,
# cwd, worktree, and task_id are never used for repository matching.
DELEGATE_REPOSITORY_ATTR_FIELDS = ("repository_id", "repository")


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _tasks_root() -> str:
    return os.path.realpath(str(TASKS_DIR))


def _task_state_path(task_id: str) -> str:
    """Resolve ``task_id`` to a state JSON path under ``TASKS_DIR``.

    Slash/backslash sanitization alone is not enough. Callers that ``open``
    must re-check ``startswith(root + os.sep)`` in the *same* function as the
    sink — CodeQL does not treat a previously returned path as sanitized
    (#317). Escapes collapse to a guaranteed-nonexistent path inside the root.
    """
    safe = task_id.replace("/", "_").replace("\\", "_")
    root = _tasks_root()
    fullpath = os.path.realpath(os.path.join(root, f"{safe}.json"))
    if not fullpath.startswith(root + os.sep):
        fullpath = os.path.join(root, "__rejected__.json")
    return fullpath


def _read_task_state(path: str) -> dict[str, Any] | None:
    """Read task JSON only after a local containment check (CodeQL sink guard)."""
    root = _tasks_root()
    fullpath = os.path.realpath(path)
    if not fullpath.startswith(root + os.sep):
        return None
    for attempt in range(TASK_READ_RETRIES):
        try:
            with open(fullpath, encoding="utf-8") as handle:
                data = json.loads(handle.read())
        except (OSError, json.JSONDecodeError):
            if attempt + 1 == TASK_READ_RETRIES:
                return None
            time.sleep(TASK_READ_RETRY_SECONDS)
            continue
        return data if isinstance(data, dict) else None
    return None


def _read_result_file(result_file: str) -> str | None:
    """Read a ``.result`` sibling under ``TASKS_DIR`` (check + open colocated)."""
    root = _tasks_root()
    fullpath = os.path.realpath(result_file)
    if not fullpath.startswith(root + os.sep):
        return None
    try:
        with open(fullpath, encoding="utf-8") as handle:
            return handle.read(RESULT_BYTES_LIMIT + 1)
    except OSError:
        return None


def _pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _task_age_seconds(started_at: str | None) -> float | None:
    started = _parse_iso_datetime(started_at)
    if started is None:
        return None
    return round((datetime.now(UTC) - started).total_seconds(), 1)


def _derived_task_status(task: dict[str, Any]) -> tuple[str, bool]:
    status = str(task.get("status") or "")
    pid = task.get("pid")
    alive = _pid_alive(pid) if pid else False
    if status == "running" and pid and not alive:
        return "zombie", False
    return status, alive


def _normalize_repository_predicate(repository: str | None) -> str | None:
    """Return a non-empty exact repository predicate, or None when unscoped."""
    if repository is None:
        return None
    text = str(repository).strip()
    return text or None


def _authoritative_task_repository(task: dict[str, Any]) -> str | None:
    """Return the single authoritative repository claim from task state.

    Only ``repository_id`` and ``repository`` are accepted. When both are
    present they must agree after strip. Missing, blank, or conflicting claims
    are unclassified (``None``). Paths, branch, cwd, worktree, and task_id are
    never consulted.
    """
    claimed: list[str] = []
    for attr_name in DELEGATE_REPOSITORY_ATTR_FIELDS:
        raw = task.get(attr_name)
        if raw is None or raw == "":
            continue
        text = str(raw).strip()
        if not text:
            continue
        claimed.append(text)
    if not claimed:
        return None
    unique = set(claimed)
    if len(unique) != 1:
        return None
    return claimed[0]


_TASK_STATE_CACHE: dict[str, tuple[float, dict[str, Any] | None, str, bool]] = {}
_LAST_TASKS_DIR_STR: str = ""


def _delegate_task_rows(
    statuses: set[str] | None = None,
    *,
    repository: str | None = None,
) -> list[dict[str, Any]]:
    """Load public-safe task summaries, optionally scoped to one repository.

    When *repository* is set, raw task state is filtered by the authoritative
    ``repository`` / ``repository_id`` contract **before** totals, sorting, and
    any caller-side pagination. Unscoped calls (Monitor HTTP + other consumers)
    keep the historical full inventory.

    Repository attribution is filter-only: the returned summary rows preserve the
    legacy public shape and never include ``repository`` / ``repository_id``.
    Repository is never inferred from path, cwd, worktree, branch, or task id.
    """
    global _TASK_STATE_CACHE, _LAST_TASKS_DIR_STR

    tasks_dir_str = str(TASKS_DIR)
    if tasks_dir_str != _LAST_TASKS_DIR_STR:
        _TASK_STATE_CACHE.clear()
        _LAST_TASKS_DIR_STR = tasks_dir_str

    repo_predicate = _normalize_repository_predicate(repository)

    rows: list[dict[str, Any]] = []
    if not TASKS_DIR.exists():
        return rows

    is_active_query = (statuses == ACTIVE_TASK_STATUSES)

    try:
        entries = list(os.scandir(tasks_dir_str))
    except OSError:
        return rows

    for entry in entries:
        if not entry.name.endswith(".json"):
            continue

        try:
            mtime = entry.stat().st_mtime
        except OSError:
            continue

        path_str = entry.path
        cached = _TASK_STATE_CACHE.get(path_str)

        if cached and cached[0] == mtime:
            _, task, derived_status, alive = cached
            if is_active_query and derived_status not in statuses:
                continue
            if task is None:
                task = _read_task_state(path_str)
                if task is None:
                    continue
                derived_status, alive = _derived_task_status(task)
                _TASK_STATE_CACHE[path_str] = (mtime, task, derived_status, alive)
        else:
            task = _read_task_state(path_str)
            if task is None:
                continue
            derived_status, alive = _derived_task_status(task)
            if derived_status not in ACTIVE_TASK_STATUSES:
                _TASK_STATE_CACHE[path_str] = (mtime, task, derived_status, alive)

        if statuses is not None and derived_status not in statuses:
            continue

        # Scope applies on raw task state only — never re-emit repository identity.
        if repo_predicate is not None:
            claimed_repo = _authoritative_task_repository(task)
            if claimed_repo is None or claimed_repo != repo_predicate:
                continue

        task_id = task.get("task_id") or entry.name[:-5]
        rows.append(
            {
                "task_id": task_id,
                "agent": task.get("agent"),
                "model": task.get("model"),
                "effort": task.get("effort"),
                "cli_version": task.get("cli_version"),
                "substitution": task.get("substitution"),
                "status": derived_status,
                "started_at": task.get("started_at"),
                "duration_s": task.get("duration_s"),
                "age_s": _task_age_seconds(task.get("started_at")),
                "alive": alive,
            }
        )

    rows.sort(
        key=lambda item: _parse_iso_datetime(item.get("started_at")) or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return rows


def list_delegate_tasks(
    *,
    status: Literal[
        "running", "done", "failed", "timeout", "spawning",
        "needs_finalize", "no_deliverable", "all",
    ] = "all",
    limit: int = 50,
    repository: str | None = None,
) -> dict[str, Any]:
    """List delegate task summaries.

    Optional *repository* is an internal exact-match predicate applied before
    total/count and limit slicing. Not exposed on the public HTTP query surface
    (Work passes the already-admitted public singleton via the Python loader).
    Returned rows keep the legacy summary shape and never include repository
    attribution fields.
    """
    task_limit = min(max(1, int(limit)), 500)
    statuses = None if status == "all" else {status}
    rows = _delegate_task_rows(statuses, repository=repository)
    return {"total": len(rows), "tasks": rows[:task_limit]}


def get_delegate_task_detail(task_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    path = _task_state_path(task_id)
    task = _read_task_state(path)
    if task is None:
        return None, None

    _, alive = _derived_task_status(task)
    result_text = None
    truncated = False
    if task.get("status") != "running":
        result_file = task.get("result_file")
        if result_file:
            result_text = _read_result_file(str(result_file))
            if result_text is not None and len(result_text.encode("utf-8")) > RESULT_BYTES_LIMIT:
                while len(result_text.encode("utf-8")) > RESULT_BYTES_LIMIT:
                    result_text = result_text[:-1]
                truncated = True

    return task, {
        "task": task,
        "result": result_text,
        "result_truncated": truncated,
        "alive": alive,
    }


def active_delegate_count() -> int:
    return len(_delegate_task_rows(ACTIVE_TASK_STATUSES))


def active_delegate_tasks(*, repository: str | None = None) -> dict[str, Any]:
    """Return active (running/spawning) task summaries.

    Optional *repository* filters task state before total construction. Internal
    only — the HTTP ``/active`` route remains unscoped for other Monitor consumers.
    Returned rows keep the legacy summary shape and never include repository
    attribution fields.
    """
    active = _delegate_task_rows(ACTIVE_TASK_STATUSES, repository=repository)
    return {"total": len(active), "tasks": active}


@router.get("/tasks")
async def delegate_tasks(
    status: Literal[
        "running", "done", "failed", "timeout", "spawning",
        "needs_finalize", "no_deliverable", "all",
    ] = Query("all"),
    limit: int = Query(50, ge=1, le=500),
):
    return await asyncio.to_thread(list_delegate_tasks, status=status, limit=limit)


@router.get("/active")
async def delegate_active():
    return await asyncio.to_thread(active_delegate_tasks)


@router.get("/tasks/{task_id}")
async def delegate_task_detail(task_id: str):
    task, response = await asyncio.to_thread(get_delegate_task_detail, task_id)
    if task is None or response is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return response
