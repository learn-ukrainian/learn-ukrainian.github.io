"""Delegate observability API router."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sqlite3
import stat
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

try:
    from scripts.lib.readonly_sqlite import SQLiteConnection
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    from lib.readonly_sqlite import SQLiteConnection  # type: ignore[no-redef]

from scripts.orchestration.dead_worker_state import worker_liveness
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME as TASK_ARCHIVE_DIR_NAME
from scripts.orchestration.task_record_store import iter_task_records
from scripts.orchestration.worktree_claims import RELEASED_TASK_STATUSES
from scripts.work.sources_public import public_repository_id

from .monitor_context import MonitorContext, get_ctx, resolve_context
from .monitor_context import production_context as production_context  # re-export: test monkeypatches
from .state_helpers import cache_get_or_compute_async, cache_retain, ctx_scoped_ttl_key

router = APIRouter(tags=["delegate"])

RESULT_BYTES_LIMIT = 64 * 1024
TASK_READ_RETRIES = 2
TASK_READ_RETRY_SECONDS = 0.01
ACTIVE_FACT_CACHE_LIMIT = 16_384
ACTIVE_FACT_STATUS_LIMIT = 64
ACTIVE_TASK_STATUSES = {"running", "spawning"}
# History listing cache only. Active observations share in-flight work but
# always bypass completed snapshots.
DELEGATE_LIST_TTL_S = 2.0
_TASK_SCAN_LOCK = threading.Lock()
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


def _task_state_path(task_id: str, ctx: MonitorContext | None = None, *, archived: bool = False) -> str:
    """Resolve ``task_id`` to a state JSON path under the context tasks dir.

    ``archived`` resolves the ``archive/`` copy that
    ``scripts/orchestration/stale_task_records.py archive`` moves old terminal
    records into (#8625).

    Slash/backslash sanitization alone is not enough. Callers that ``open``
    must re-check ``startswith(root + os.sep)`` in the *same* function as the
    sink — CodeQL does not treat a previously returned path as sanitized
    (#317). Escapes collapse to a guaranteed-nonexistent path inside the root.
    """
    safe = task_id.replace("/", "_").replace("\\", "_")
    root = _tasks_root(ctx)
    name = os.path.join(TASK_ARCHIVE_DIR_NAME, f"{safe}.json") if archived else f"{safe}.json"
    fullpath = os.path.realpath(os.path.join(root, name))
    if not fullpath.startswith(root + os.sep):
        fullpath = os.path.join(root, "__rejected__.json")
    return fullpath


def _read_task_state(path: str, ctx: MonitorContext | None = None, root: str | None = None) -> dict[str, Any] | None:
    """Read task JSON only after a local containment check (CodeQL sink guard)."""
    # Active scans supply the already-resolved parent. Resolve only a link or
    # a non-sibling, then refuse a leaf-link swap at open time.
    scan_root = root is not None
    if root is None:
        root = _tasks_root(ctx)
    fullpath = os.path.abspath(path)
    if not fullpath.startswith(root + os.sep):
        return None
    if not scan_root or os.path.dirname(fullpath) != root or os.path.islink(fullpath):
        fullpath = os.path.realpath(fullpath)
    if not fullpath.startswith(root + os.sep):
        return None
    for attempt in range(TASK_READ_RETRIES):
        try:
            fd = os.open(fullpath, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    return None
                with os.fdopen(fd, encoding="utf-8", closefd=False) as handle:
                    data = json.loads(handle.read())
            finally:
                os.close(fd)
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


_TASK_STATE_CACHE: dict[str, tuple[float, dict[str, Any], str, bool, str | None, int | None]] = {}
_LAST_TASKS_DIR_STR: str = ""


def _task_cache_db_path(tasks_dir_str: str) -> Path:
    return Path(tasks_dir_str) / ".task_cache.sqlite3"


def _init_task_cache_db(db_path: Path, ctx: MonitorContext | None = None) -> SQLiteConnection | None:
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
                run_nonce TEXT,
                linked_issues TEXT
            )
            """
        )
        with contextlib.suppress(sqlite3.OperationalError):
            conn.execute("ALTER TABLE task_cache ADD COLUMN run_nonce TEXT")
        with contextlib.suppress(sqlite3.OperationalError):
            conn.execute("ALTER TABLE task_cache ADD COLUMN linked_issues TEXT")
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
                   substitution, claimed_repo, run_nonce, linked_issues
            FROM task_cache
            """
        )
        rows = cursor.fetchall()
        conn.close()
        cache: dict[str, tuple[float, dict[str, Any], str, bool, str | None, int | None]] = {}
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
                linked_issues_raw,
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
            linked_issues = _decode_linked_issues(linked_issues_raw)
            if linked_issues is not None:
                summary["linked_issues"] = linked_issues
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
            INSERT OR REPLACE INTO task_cache VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            records,
        )
        conn.commit()
        conn.close()
    except (OSError, sqlite3.Error):
        pass


def _delete_task_cache_entries(
    tasks_dir_str: str,
    paths: list[str],
    ctx: MonitorContext | None = None,
) -> None:
    db_path = _task_cache_db_path(tasks_dir_str)
    if not db_path.exists():
        return
    try:
        conn = _init_task_cache_db(db_path, ctx)
        if conn is None:
            return
        conn.executemany("DELETE FROM task_cache WHERE path = ?", [(path,) for path in paths])
        conn.commit()
        conn.close()
    except (OSError, sqlite3.Error):
        pass


def _decode_linked_issues(raw: Any) -> list[dict[str, Any]] | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        payload = raw
    elif isinstance(raw, str):
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None
    else:
        return None
    if not isinstance(payload, list):
        return None
    return payload


def _linked_issues_from_dor(task: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Canonical issue links from a DoR-checked preflight, or None when absent.

    Foreign repositories are recorded on ``issue_repositories`` and also counted
    inside ``issues``. One canonical link is emitted only for the remainder.
    """
    preflight = task.get("dor_preflight")
    if not isinstance(preflight, dict):
        return None
    if "issues" not in preflight and "issue_repositories" not in preflight:
        return None

    canonical = public_repository_id()
    foreign_by_number: dict[int, list[str]] = {}
    foreign_links: list[dict[str, Any]] = []
    raw_foreign = preflight.get("issue_repositories") or []
    if isinstance(raw_foreign, list):
        for entry in raw_foreign:
            if not isinstance(entry, dict):
                continue
            try:
                number = int(entry.get("issue"))
            except (TypeError, ValueError):
                continue
            repo = entry.get("repo") if isinstance(entry.get("repo"), str) else entry.get("repository")
            if not isinstance(repo, str) or not repo or number <= 0:
                continue
            foreign_by_number.setdefault(number, []).append(repo)
            foreign_links.append({"issue": number, "repository": repo})
    counts: dict[int, int] = {}
    raw_issues = preflight.get("issues") or []
    if isinstance(raw_issues, list):
        for raw_issue in raw_issues:
            try:
                number = int(raw_issue)
            except (TypeError, ValueError):
                continue
            if number > 0:
                counts[number] = counts.get(number, 0) + 1
    links: list[dict[str, Any]] = []
    for number, count in sorted(counts.items()):
        if count - len(foreign_by_number.get(number, [])) > 0:
            links.append({"issue": number, "repository": canonical})
    links.extend(foreign_links)
    return links


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

    History (#8625): ``stale_task_records archive`` moves old terminal records
    into ``archive/``. A query that can match a terminal status (``None`` for
    all, ``done``, ``failed``, …) reads the hot directory and the archive
    through :func:`iter_task_records`, so totals and listings keep the full
    history. Active queries (running, spawning, ``needs_finalize``) read the
    hot directory only: nothing in the archive can match them.
    """
    # One scan mutates the process-wide task cache and the sidecar index.
    # Concurrent scans used to interleave those updates and pile SQLite writes
    # on the same file until the request timeout fired.
    with _TASK_SCAN_LOCK:
        return _delegate_task_rows_locked(statuses, repository=repository, ctx=ctx)


def _delegate_task_rows_locked(
    statuses: set[str] | None = None,
    *,
    repository: str | None = None,
    ctx: MonitorContext | None = None,
) -> list[dict[str, Any]]:
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
    include_archive = statuses is None or bool(statuses & RELEASED_TASK_STATUSES)
    scanned_dirs = {tasks_dir_str}
    if include_archive:
        scanned_dirs.add(os.path.join(tasks_dir_str, TASK_ARCHIVE_DIR_NAME))

    dirty_records: list[tuple] = []
    seen_paths: set[str] = set()

    for path in iter_task_records(tasks_dir, include_archive=include_archive):
        path_str = str(path)
        seen_paths.add(path_str)

        try:
            mtime = os.stat(path_str).st_mtime
        except OSError:
            continue

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
            task_id = str(task.get("task_id") or path.stem)
            raw_status = str(task.get("status") or "")
            subst = task.get("substitution")
            run_nonce = task.get("run_nonce")
            linked_issues = _linked_issues_from_dor(task)
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
            if linked_issues is not None:
                summary["linked_issues"] = linked_issues
            cached_tuple = (
                mtime,
                summary,
                derived_status,
                alive,
                claimed_repo,
                pid_int,
            )
            _TASK_STATE_CACHE[path_str] = cached_tuple
            subst_str = json.dumps(subst) if isinstance(subst, dict) else (str(subst) if subst is not None else None)
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
                    json.dumps(linked_issues) if linked_issues is not None else None,
                )
            )

        if statuses is not None and derived_status not in statuses:
            continue

        # Scope applies on raw task state only — never re-emit repository identity.
        if repo_predicate is not None and (claimed_repo is None or claimed_repo != repo_predicate):
            continue

        task_id = summary["task_id"]
        row = {
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
        if "linked_issues" in summary:
            row["linked_issues"] = summary["linked_issues"]
        rows.append(row)

    if dirty_records:
        _save_task_cache_entries(tasks_dir_str, dirty_records, resolved)
    # Records archived (#8625) or removed since the last scan leave the cache too.
    # Only directories this query scanned are judged, so a hot-only query never
    # evicts the archive entries an all-history query cached.
    vanished = [path for path in _TASK_STATE_CACHE if path not in seen_paths and os.path.dirname(path) in scanned_dirs]
    if vanished:
        for path in vanished:
            del _TASK_STATE_CACHE[path]
        _delete_task_cache_entries(tasks_dir_str, vanished, resolved)

    rows.sort(
        key=lambda item: _parse_iso_datetime(item.get("started_at")) or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return rows


def list_delegate_tasks(
    *,
    status: Literal[
        "running",
        "done",
        "failed",
        "timeout",
        "spawning",
        "needs_finalize",
        "no_deliverable",
        "all",
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
    attribution fields. ``all`` and terminal statuses include records archived
    by ``stale_task_records`` (#8625), so ``total`` counts the full history.
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
    archived = False
    if task is None:
        task = _read_task_state(_task_state_path(task_id, ctx, archived=True), ctx)
        archived = task is not None
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
            if result_text is None and archived:
                # The record keeps the hot-directory path; the sidecar moved with it.
                archived_result = os.path.join(
                    _tasks_root(ctx), TASK_ARCHIVE_DIR_NAME, os.path.basename(str(result_file))
                )
                result_text = _read_result_file(archived_result, ctx)
            if result_text is not None and len(result_text.encode("utf-8")) > RESULT_BYTES_LIMIT:
                while len(result_text.encode("utf-8")) > RESULT_BYTES_LIMIT:
                    result_text = result_text[:-1]
                truncated = True

    return (
        task,
        {
            "task": task,
            "result": result_text,
            "result_truncated": truncated,
            "alive": alive,
        },
        False,
    )


def active_delegate_count(ctx: MonitorContext | None = None) -> int:
    return active_delegate_tasks(ctx=ctx)["total"]


def _observation_token(stat: os.stat_result) -> tuple[int, ...]:
    """Bind an observation to content generation, ignoring read-induced atime."""
    return (stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)


def _active_worker_liveness(task: dict[str, Any]) -> tuple[bool | None, str | None]:
    """Qualify healer evidence for the API's task-attempt observation."""
    try:
        alive = worker_liveness(task, pid_alive=_pid_alive)
    except (OverflowError, ValueError):
        alive = None
    if alive is True and task.get("worker_identity") is None:
        return None, "legacy_worker_identity_unattested"
    return alive, "worker_identity_or_visibility_unknown" if alive is None else None


def _is_closeout_artifact(record: dict[str, Any]) -> bool:
    """Recognize the state written by review.closeout_cli, never by filename."""
    fields = {"target", "target_args", "baseline", "behavior_proof", "cycle_outstanding_counts", "findings"}
    return (
        fields <= record.keys() <= fields | {"resolved_reviewer"}
        and all(record[key] is None or isinstance(record[key], dict) for key in ("target", "target_args", "baseline"))
        and isinstance(record["behavior_proof"], dict)
        and isinstance(record["cycle_outstanding_counts"], list)
        and isinstance(record["findings"], list)
        and ("resolved_reviewer" not in record or isinstance(record["resolved_reviewer"], dict))
    )


def _active_candidate_names(tasks_dir: Path) -> list[str]:
    """Use the same hot-record predicate for initial and final enumeration."""
    with os.scandir(tasks_dir) as entries:
        return sorted(
            entry.name
            for entry in entries
            if entry.name.endswith(".json") and not entry.name.endswith(".snapshots.json")
        )


def active_delegate_tasks(
    *,
    repository: str | None = None,
    ctx: MonitorContext | None = None,
) -> dict[str, Any]:
    """Observe hot running/spawning attempts with fresh scope and liveness checks.

    Preserve the legacy active scope: proven-dead running attempts are excluded
    from tasks/total, but disclosed in observations. Unknown liveness stays None.
    A failed or changing authority refuses the inventory rather than returning zero.
    """
    resolved = resolve_context(ctx)
    tasks_dir = _tasks_dir(resolved)
    root = os.path.realpath(str(tasks_dir))
    # Immutable terminal facts only: never retain payloads or derived liveness.
    holder = resolved.runtime.get_or_create_derived("delegate_active_facts", dict)
    facts = holder.get("facts", {})
    next_facts: dict[str, tuple[tuple[int, ...], str | None]] = {}
    artifacts = 0
    started = datetime.now(UTC)
    predicate = _normalize_repository_predicate(repository)
    rows: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    signatures: dict[str, os.stat_result] = {}
    link_signatures: dict[str, os.stat_result] = {}
    process_checks: list[tuple[dict[str, Any], tuple[bool | None, str | None]]] = []
    try:
        directory_before = tasks_dir.stat()
        names = _active_candidate_names(tasks_dir)
        paths = [os.path.join(str(tasks_dir), name) for name in names]
    except OSError:
        raise HTTPException(
            503,
            detail={
                "status": "unknown",
                "reason": "task_directory_unavailable",
            },
        ) from None

    for path in paths:
        try:
            leaf = os.lstat(path)
            if stat.S_ISLNK(leaf.st_mode):
                link_signatures[path] = leaf
                signatures[path] = os.stat(path)
            else:
                signatures[path] = leaf
        except OSError:
            raise HTTPException(
                503,
                detail={
                    "status": "unknown",
                    "reason": "task_authority_changed",
                },
            ) from None
        token = _observation_token(signatures[path])
        key = str(path)
        cached = facts.get(key) if path not in link_signatures else None
        if cached is not None and cached[0] == token:
            task = {"status": cached[1]} if cached[1] is not None else None
            artifact = cached[1] is None
        else:
            try:
                task = _read_task_state(key, ctx, root)
            except (OSError, UnicodeError):
                task = None
            artifact = task is not None and _is_closeout_artifact(task)
        if artifact:
            artifacts += 1
        elif task is None or not isinstance(task.get("status"), str) or not task["status"]:
            raise HTTPException(
                503,
                detail={
                    "status": "unknown",
                    "reason": "task_record_unreadable_or_invalid",
                },
            )
        status = None if artifact else task["status"]
        if status not in ACTIVE_TASK_STATUSES:
            if len(next_facts) < ACTIVE_FACT_CACHE_LIMIT and (
                status is None or len(status) <= ACTIVE_FACT_STATUS_LIMIT
            ):
                next_facts[key] = (token, status)
            continue
        if predicate is not None and _authoritative_task_repository(task) != predicate:
            continue
        record_observed = datetime.now(UTC)
        alive, liveness_reason = _active_worker_liveness(task)
        process_checks.append((task, (alive, liveness_reason)))
        observed = datetime.now(UTC)
        summary = {
            "task_id": str(task.get("task_id") or Path(path).stem),
            "agent": task.get("agent"),
            "model": task.get("model"),
            "effort": task.get("effort"),
            "cli_version": task.get("cli_version"),
            "substitution": task.get("substitution"),
            "status": status,
            "started_at": task.get("started_at"),
            "duration_s": task.get("duration_s"),
            "age_s": _task_age_seconds(task.get("started_at")),
            "alive": alive,
        }
        linked_issues = _linked_issues_from_dor(task)
        if linked_issues is not None:
            summary["linked_issues"] = linked_issues
        excluded = status == "running" and alive is False
        observations.append(
            {
                "task_id": summary["task_id"],
                "run_nonce": task.get("run_nonce"),
                "record_status": status,
                "alive": alive,
                "excluded_dead_running": excluded,
                "liveness_basis": "worker_identity"
                if task.get("worker_identity") is not None
                else "legacy_pid_namespace",
                "liveness_reason": liveness_reason,
                "liveness_observed_at": observed.isoformat(),
                "record_observed_at": record_observed.isoformat(),
                "record_updated_at": datetime.fromtimestamp(signatures[path].st_mtime, UTC).isoformat(),
            }
        )
        if not excluded:
            rows.append(summary)

    changed = any(_active_worker_liveness(task) != sample for task, sample in process_checks)
    try:
        # Equality includes inode, nanosecond timestamps and size, so replacement
        # and in-place writes are detected, even if a writer restores mtime.
        directory_after = tasks_dir.stat()
        changed = changed or (directory_before.st_dev, directory_before.st_ino) != (
            directory_after.st_dev,
            directory_after.st_ino,
        )
        if _observation_token(directory_before) != _observation_token(directory_after):
            changed = changed or names != _active_candidate_names(tasks_dir)
        changed = changed or any(
            _observation_token(before) != _observation_token(os.stat(path, follow_symlinks=path in link_signatures))
            for path, before in signatures.items()
        )
        changed = changed or any(
            _observation_token(before) != _observation_token(os.lstat(path)) for path, before in link_signatures.items()
        )
        # Directory metadata may also change while checking records. Recheck
        # the same membership and tokens once, allowing only non-task changes.
        if _observation_token(directory_after) != _observation_token(tasks_dir.stat()):
            final_directory = tasks_dir.stat()
            changed = changed or (directory_before.st_dev, directory_before.st_ino) != (
                final_directory.st_dev,
                final_directory.st_ino,
            )
            changed = changed or any(
                _observation_token(before) != _observation_token(os.stat(path, follow_symlinks=path in link_signatures))
                for path, before in signatures.items()
            )
            changed = changed or any(
                _observation_token(before) != _observation_token(os.lstat(path))
                for path, before in link_signatures.items()
            )
            changed = changed or names != _active_candidate_names(tasks_dir)
            last_directory = tasks_dir.stat()
            changed = changed or (directory_before.st_dev, directory_before.st_ino) != (
                last_directory.st_dev,
                last_directory.st_ino,
            )
    except OSError:
        changed = True
    if changed:
        raise HTTPException(503, detail={"status": "unknown", "reason": "task_authority_changed"})
    holder["facts"] = next_facts
    finished = datetime.now(UTC)
    for observation in observations:
        observation["record_age_s"] = (
            finished - datetime.fromisoformat(observation["record_updated_at"])
        ).total_seconds()
        observation["liveness_age_s"] = (
            finished - datetime.fromisoformat(observation["liveness_observed_at"])
        ).total_seconds()
    rows.sort(
        key=lambda row: _parse_iso_datetime(row.get("started_at")) or datetime.min.replace(tzinfo=UTC), reverse=True
    )
    return {
        "total": len(rows),
        "tasks": rows,
        "observations": observations,
        "cache_age_s": 0.0,
        "source": {
            "status": "ok",
            "scope": "hot running/spawning records, excluding proven-dead running attempts; no archive or snapshot sidecars",
            "filtered": predicate is not None,
            "scan_started_at": started.isoformat(),
            "observed_at": finished.isoformat(),
            "age_s": 0.0,
            "records_scanned": len(paths) - artifacts,
            "closeout_artifacts": artifacts,
            "records_in_scope": len(observations),
            "excluded_dead_running": sum(item["excluded_dead_running"] for item in observations),
        },
    }


def seat_delegate_tasks(
    *,
    repository: str | None = None,
    ctx: MonitorContext | None = None,
) -> dict[str, Any]:
    """Return running, spawning, and derived-dead task summaries.

    The active listing omits derived zombie rows; this includes them for
    diagnostics. Fleet board uses this collector for source health only, since
    task rows have no approved seat identity binding. Returned rows keep the
    legacy summary shape and never include repository attribution.
    """
    statuses = set(ACTIVE_TASK_STATUSES)
    statuses.add("zombie")
    rows = _delegate_task_rows(statuses, repository=repository, ctx=ctx)
    return {"total": len(rows), "tasks": rows}


def _dir_token(path: Path) -> str:
    """Cheap generation for a directory: changes when entries are added or removed."""
    try:
        st = os.stat(path)
    except OSError:
        return "missing"
    return f"{st.st_mtime_ns}:{getattr(st, 'st_nlink', 0)}"


def _delegate_list_cache_key(
    ctx: MonitorContext,
    kind: str,
    *,
    status: str,
    limit: int,
) -> str:
    resolved = resolve_context(ctx)
    tasks_dir = _tasks_dir(resolved)
    prefix = ctx_scoped_ttl_key(resolved, "delegate", kind, status, limit)
    # A new directory generation replaces the previous snapshot. Keeping every
    # generation would retain obsolete task lists for the life of the process.
    key = f"{prefix}:{_dir_token(tasks_dir)}:{_dir_token(tasks_dir / TASK_ARCHIVE_DIR_NAME)}"
    cache_retain(f"{prefix}:", key)
    return key


@router.get("/tasks")
async def delegate_tasks(
    status: Literal[
        "running",
        "done",
        "failed",
        "timeout",
        "spawning",
        "needs_finalize",
        "no_deliverable",
        "all",
    ] = Query("all"),
    limit: int = Query(50, ge=1, le=500),
    ctx: MonitorContext = Depends(get_ctx),
):
    cache_key = _delegate_list_cache_key(ctx, "tasks", status=status, limit=limit)
    return await cache_get_or_compute_async(
        cache_key,
        DELEGATE_LIST_TTL_S,
        lambda: list_delegate_tasks(status=status, limit=limit, ctx=ctx),
    )


@router.get("/active")
async def delegate_active(ctx: MonitorContext = Depends(get_ctx)):
    cache_key = _delegate_list_cache_key(ctx, "active", status="active", limit=0)
    return await cache_get_or_compute_async(
        cache_key,
        DELEGATE_LIST_TTL_S,
        lambda: active_delegate_tasks(ctx=ctx),
        force=True,
    )


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
