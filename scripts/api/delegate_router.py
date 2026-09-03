"""Delegate observability API router."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from .monitor_context import MonitorContext, get_ctx, resolve_context

router = APIRouter(tags=["delegate"])

RESULT_BYTES_LIMIT = 64 * 1024
TASK_READ_RETRIES = 2
TASK_READ_RETRY_SECONDS = 0.01
ACTIVE_TASK_STATUSES = {"running", "spawning"}
# Authoritative repository-attribution fields on task state. Paths, branch names,
# cwd, worktree, and task_id are never used for repository matching.
DELEGATE_REPOSITORY_ATTR_FIELDS = ("repository_id", "repository")




def _tasks_dir(ctx: MonitorContext | None = None) -> Path:
    if isinstance(ctx, MonitorContext):
        return ctx.roots.batch_state_dir / "tasks"
    # Plain-Python callers (fleet workers collect, research consumption)
    # historically read BATCH_STATE_DIR / "tasks". Keep that cheap fallback
    # so they do not construct a production MonitorContext (and its git
    # session-streams probe) just to resolve a directory.
    from scripts.api import config  # noqa: PLC0415, I001  # lazy-ok: cheap BATCH_STATE_DIR fallback without production_context

    return Path(config.BATCH_STATE_DIR) / "tasks"


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


def _tasks_root(ctx: MonitorContext | None = None) -> str:
    return os.path.realpath(str(_tasks_dir(ctx)))


def _task_state_path(task_id: str, ctx: MonitorContext | None = None) -> str:
    """Resolve ``task_id`` to a state JSON path under the context tasks dir.

    Slash/backslash sanitization alone is not enough. Callers that ``open``
    must re-check ``startswith(root + os.sep)`` in the *same* function as the
    sink — CodeQL does not treat a previously returned path as sanitized
    (#317). Escapes collapse to a guaranteed-nonexistent path inside the root.
    """
    safe = task_id.replace("/", "_").replace("\\", "_")
    root = _tasks_root(ctx)
    fullpath = os.path.realpath(os.path.join(root, f"{safe}.json"))
    if not fullpath.startswith(root + os.sep):
        fullpath = os.path.join(root, "__rejected__.json")
    return fullpath


def _read_task_state(path: str, ctx: MonitorContext | None = None) -> dict[str, Any] | None:
    """Read task JSON only after a local containment check (CodeQL sink guard)."""
    root = _tasks_root(ctx)
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


def _read_result_file(result_file: str, ctx: MonitorContext | None = None) -> str | None:
    """Read a ``.result`` sibling under the context tasks dir (check + open colocated)."""
    root = _tasks_root(ctx)
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


_TASK_STATE_CACHE: dict[
    str, tuple[float, dict[str, Any], str, bool, str | None, int | None]
] = {}
_LAST_TASKS_DIR_STR: str = ""


def _task_cache_db_path(tasks_dir_str: str) -> Path:
    return Path(tasks_dir_str) / ".task_cache.sqlite3"


def _init_task_cache_db(db_path: Path, ctx: MonitorContext | None = None) -> sqlite3.Connection | None:
    try:
        conn = resolve_context(ctx)._open_db(db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_cache (
                path TEXT PRIMARY KEY,
                mtime REAL NOT NULL,
                task_id TEXT NOT NULL,
                status TEXT NOT NULL,
                derived_status TEXT NOT NULL,
                pid INTEGER,
                alive INTEGER NOT NULL,
                started_at TEXT,
                duration_s REAL,
                agent TEXT,
                model TEXT,
                effort TEXT,
                cli_version TEXT,
                substitution TEXT,
                claimed_repo TEXT,
                run_nonce TEXT
            )
            """
        )
        with contextlib.suppress(sqlite3.OperationalError):
            conn.execute("ALTER TABLE task_cache ADD COLUMN run_nonce TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_cache_mtime ON task_cache(mtime)")
        conn.commit()
        return conn
    except (OSError, sqlite3.Error):
        return None


def _load_task_cache_from_db(
    tasks_dir_str: str,
    ctx: MonitorContext | None = None,
) -> dict[str, tuple[float, dict[str, Any], str, bool, str | None, int | None]]:
    db_path = _task_cache_db_path(tasks_dir_str)
    if not db_path.exists():
        return {}
    try:
        conn = _init_task_cache_db(db_path, ctx)
        if conn is None:
            return {}
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT path, mtime, task_id, status, derived_status, pid, alive,
                   started_at, duration_s, agent, model, effort, cli_version,
                   substitution, claimed_repo, run_nonce
            FROM task_cache
            """
        )
        rows = cursor.fetchall()
        conn.close()
        cache: dict[
            str, tuple[float, dict[str, Any], str, bool, str | None, int | None]
        ] = {}
        for row in rows:
            (
                path_str,
                mtime,
                task_id,
                raw_status,
                derived_status,
                pid,
                alive_int,
                started_at,
                duration_s,
                agent,
                model,
                effort,
                cli_version,
                subst_str,
                claimed_repo,
                run_nonce,
            ) = row
            subst = None
            if subst_str:
                try:
                    subst = json.loads(subst_str)
                except (json.JSONDecodeError, TypeError):
                    subst = subst_str
            summary = {
                "task_id": task_id,
                "agent": agent,
                "model": model,
                "effort": effort,
                "cli_version": cli_version,
                "substitution": subst,
                "status": raw_status,
                "started_at": started_at,
                "duration_s": duration_s,
                "run_nonce": run_nonce,
            }
            cache[path_str] = (
                float(mtime),
                summary,
                str(derived_status),
                bool(alive_int),
                claimed_repo,
                int(pid) if pid is not None else None,
            )
        return cache
    except (OSError, sqlite3.Error):
        return {}


def _save_task_cache_entries(
    tasks_dir_str: str,
    records: list[tuple],
    ctx: MonitorContext | None = None,
) -> None:
    db_path = _task_cache_db_path(tasks_dir_str)
    try:
        conn = _init_task_cache_db(db_path, ctx)
        if conn is None:
            return
        conn.executemany(
            """
            INSERT OR REPLACE INTO task_cache VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            records,
        )
        conn.commit()
        conn.close()
    except (OSError, sqlite3.Error):
        pass


def _delegate_task_rows(
    statuses: set[str] | None = None,
    *,
    repository: str | None = None,
    ctx: MonitorContext | None = None,
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

    resolved = resolve_context(ctx)
    tasks_dir = _tasks_dir(resolved)
    tasks_dir_str = str(tasks_dir)
    if tasks_dir_str != _LAST_TASKS_DIR_STR:
        _TASK_STATE_CACHE.clear()
        _TASK_STATE_CACHE.update(_load_task_cache_from_db(tasks_dir_str, resolved))
        _LAST_TASKS_DIR_STR = tasks_dir_str

    repo_predicate = _normalize_repository_predicate(repository)

    rows: list[dict[str, Any]] = []
    if not tasks_dir.exists():
        return rows

    is_active_query = statuses == ACTIVE_TASK_STATUSES

    try:
        entries = list(os.scandir(tasks_dir_str))
    except OSError:
        return rows

    dirty_records: list[tuple] = []

    for entry in entries:
        if not entry.name.endswith(".json"):
            continue

        try:
            mtime = entry.stat().st_mtime
        except OSError:
            continue

        path_str = entry.path
        cached = _TASK_STATE_CACHE.get(path_str)

        if cached is not None and cached[0] == mtime:
            _, summary, derived_status, alive, claimed_repo, pid = cached
            if is_active_query and derived_status not in statuses:
                continue
            if derived_status == "running" and pid:
                alive = _pid_alive(pid)
                if not alive:
                    derived_status = "zombie"
        else:
            task = _read_task_state(path_str, resolved)
            if task is None:
                continue
            derived_status, alive = _derived_task_status(task)
            claimed_repo = _authoritative_task_repository(task)
            pid = task.get("pid")
            pid_int = int(pid) if pid and str(pid).isdigit() else None
            task_id = str(task.get("task_id") or entry.name[:-5])
            raw_status = str(task.get("status") or "")
            subst = task.get("substitution")
            run_nonce = task.get("run_nonce")
            summary = {
                "task_id": task_id,
                "agent": task.get("agent"),
                "model": task.get("model"),
                "effort": task.get("effort"),
                "cli_version": task.get("cli_version"),
                "substitution": subst,
                "status": raw_status,
                "started_at": task.get("started_at"),
                "duration_s": task.get("duration_s"),
                "run_nonce": run_nonce,
            }
            cached_tuple = (
                mtime,
                summary,
                derived_status,
                alive,
                claimed_repo,
                pid_int,
            )
            _TASK_STATE_CACHE[path_str] = cached_tuple
            subst_str = (
                json.dumps(subst)
                if isinstance(subst, dict)
                else (str(subst) if subst is not None else None)
            )
            dirty_records.append(
                (
                    path_str,
                    mtime,
                    task_id,
                    raw_status,
                    derived_status,
                    pid_int,
                    1 if alive else 0,
                    summary["started_at"],
                    summary["duration_s"],
                    summary["agent"],
                    summary["model"],
                    summary["effort"],
                    summary["cli_version"],
                    subst_str,
                    claimed_repo,
                    run_nonce,
                )
            )

        if statuses is not None and derived_status not in statuses:
            continue

        # Scope applies on raw task state only — never re-emit repository identity.
        if repo_predicate is not None and (
            claimed_repo is None or claimed_repo != repo_predicate
        ):
            continue

        task_id = summary["task_id"]
        rows.append(
            {
                "task_id": task_id,
                "agent": summary.get("agent"),
                "model": summary.get("model"),
                "effort": summary.get("effort"),
                "cli_version": summary.get("cli_version"),
                "substitution": summary.get("substitution"),
                "status": derived_status,
                "started_at": summary.get("started_at"),
                "duration_s": summary.get("duration_s"),
                "age_s": _task_age_seconds(summary.get("started_at")),
                "alive": alive,
            }
        )

    if dirty_records:
        _save_task_cache_entries(tasks_dir_str, dirty_records, resolved)

    rows.sort(
        key=lambda item: _parse_iso_datetime(item.get("started_at"))
        or datetime.min.replace(tzinfo=UTC),
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
    ctx: MonitorContext | None = None,
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
    rows = _delegate_task_rows(statuses, repository=repository, ctx=ctx)
    return {"total": len(rows), "tasks": rows[:task_limit]}


def get_delegate_task_detail(
    task_id: str,
    *,
    run_nonce: str | None = None,
    ctx: MonitorContext | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
    path = _task_state_path(task_id, ctx)
    task = _read_task_state(path, ctx)
    if task is None:
        return None, None, False

    if run_nonce is not None and task.get("run_nonce") != run_nonce:
        return task, None, True

    _, alive = _derived_task_status(task)
    result_text = None
    truncated = False
    if task.get("status") != "running":
        result_file = task.get("result_file")
        if result_file:
            result_text = _read_result_file(str(result_file), ctx)
            if result_text is not None and len(result_text.encode("utf-8")) > RESULT_BYTES_LIMIT:
                while len(result_text.encode("utf-8")) > RESULT_BYTES_LIMIT:
                    result_text = result_text[:-1]
                truncated = True

    return task, {
        "task": task,
        "result": result_text,
        "result_truncated": truncated,
        "alive": alive,
    }, False


def active_delegate_count(ctx: MonitorContext | None = None) -> int:
    return len(_delegate_task_rows(ACTIVE_TASK_STATUSES, ctx=ctx))


def active_delegate_tasks(
    *,
    repository: str | None = None,
    ctx: MonitorContext | None = None,
) -> dict[str, Any]:
    """Return active (running/spawning) task summaries.

    Optional *repository* filters task state before total construction. Internal
    only — the HTTP ``/active`` route remains unscoped for other Monitor consumers.
    Returned rows keep the legacy summary shape and never include repository
    attribution fields.
    """
    active = _delegate_task_rows(ACTIVE_TASK_STATUSES, repository=repository, ctx=ctx)
    return {"total": len(active), "tasks": active}


@router.get("/tasks")
async def delegate_tasks(
    status: Literal[
        "running", "done", "failed", "timeout", "spawning",
        "needs_finalize", "no_deliverable", "all",
    ] = Query("all"),
    limit: int = Query(50, ge=1, le=500),
    ctx: MonitorContext = Depends(get_ctx),
):
    return await asyncio.to_thread(list_delegate_tasks, status=status, limit=limit, ctx=ctx)


@router.get("/active")
async def delegate_active(ctx: MonitorContext = Depends(get_ctx)):
    return await asyncio.to_thread(active_delegate_tasks, ctx=ctx)


@router.get("/tasks/{task_id}")
async def delegate_task_detail(
    task_id: str,
    run_nonce: str | None = Query(None),
    ctx: MonitorContext = Depends(get_ctx),
):
    task, response, nonce_mismatch = await asyncio.to_thread(
        get_delegate_task_detail,
        task_id,
        run_nonce=run_nonce,
        ctx=ctx,
    )
    if nonce_mismatch:
        raise HTTPException(
            status_code=409,
            detail=f"Task run_nonce mismatch: expected {run_nonce!r}, got {task.get('run_nonce')!r}",
        )
    if task is None or response is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return response
