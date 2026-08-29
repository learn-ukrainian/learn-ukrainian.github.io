"""
FastAPI server for playground dashboards.

Architecture:
  - main.py: shared endpoints (config, batch state, dispatcher, websocket, static files)
  - blue_router.py: Blue team endpoints at /api/blue/...
  - gold_router.py: Gold team endpoints at /api/gold/...

Each team owns their router file. No conflicts.
"""

import asyncio
import json
import logging
import os
import re
import socket
import subprocess
import threading
import time
import uuid
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from scripts.common.release_layout import is_release_root
from scripts.guardrails import worktree_containment
from scripts.research import registry as reg

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

from scripts.orchestration import issue_stream_audit as isa
from scripts.orchestration.reap_worktrees import primary_checkout_root, reap_worktrees

from . import delegate_router as delegate_api
from . import runtime_router as runtime_api
from . import state_router as state_api
from . import wiki_router as wiki_api
from ._signal_log import install_signal_logging
from .admin_router import router as admin_router
from .agent_monitor_router import router as agent_monitor_router
from .agent_router import router as agent_router
from .artifacts_router import router as artifacts_router
from .atlas_jobs_router import router as atlas_jobs_router
from .blue_router import router as blue_router
from .build_events_router import router as build_events_router
from .cluster_router import router as cluster_router
from .codexbar_usage import scheduler_status, start_periodic_refresh, stop_periodic_refresh
from .comms_router import ensure_broker_db_ready
from .comms_router import router as comms_router
from .config import (
    LEVELS,
)
from .consultation_router import router as consultation_router
from .coordination_router import router as coordination_router
from .cost_router import router as cost_router
from .dashboard_router import router as dashboard_router
from .decisions_router import router as decisions_router
from .delegate_router import router as delegate_router
from .discussions_router import router as discussions_router
from .docs_router import router as docs_router
from .epics_router import router as epics_router
from .epics_router import seed_manifest_inventory
from .fleet_router import router as fleet_router
from .fleet_workers_router import router as fleet_workers_router
from .git_hygiene_router import router as git_hygiene_router
from .gold_router import router as gold_router
from .governance_router import collect_governance_summary
from .governance_router import router as governance_router
from .hermes_cron_router import router as hermes_cron_router
from .images_router import router as images_router
from .issues_router import router as issues_router
from .knowledge_router import router as knowledge_router
from .monitor_context import MonitorContext, get_ctx, production_context
from .observer_presence import router as observer_presence_router
from .occupancy import router as occupancy_router
from .occupancy_local import resolve_launcher_host_id
from .ops_router import router as ops_router
from .preload import preload_all
from .project_state_router import router as project_state_router
from .rag_router import router as sources_router
from .repository_authority import build_repository_authority, cwd_role
from .resilience import get_resilience_snapshot, resilience_middleware
from .reviewer_ghosts_router import router as reviewer_ghosts_router
from .rollover_router import collect_rollover_orient_data
from .rollover_router import router as rollover_router
from .route_contracts import router as contracts_router
from .rules_router import router as rules_router
from .runtime_router import router as runtime_router
from .session_router import router as session_router
from .session_streams_router import router as session_streams_router
from .site_router import router as site_router
from .state_helpers import cache_get, cache_invalidate, cache_set
from .state_router import router as state_router
from .telemetry.response import add_json_telemetry, session_id_from_request
from .telemetry_router import router as telemetry_router
from .wiki_router import router as wiki_router
from .work_router import router as work_router
from .work_router import warm_projection_cache
from .worktrees_router import router as worktrees_router

core_router = APIRouter()


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Lifespan hook — wrap uvicorn signal handlers so we record WHO killed us.

    Without this, "Shutting down" lines in logs/api.log have no provenance.
    See scripts/api/_signal_log.py for the wrapper rationale.
    """
    preload_all()
    install_signal_logging()
    ensure_broker_db_ready()
    ctx = _app.state.ctx
    seed_manifest_inventory(
        ctx.roots.project_root,
        store=ctx.stores.epics_store,
        handoff_root=ctx.roots.live_repo_root,
        ctx=ctx,
    )
    try:
        isa.schedule_refresh(force=False)
    except Exception as exc:
        logger.warning("Issue stream audit refresh schedule on startup failed: %s", exc)
    try:
        warm_projection_cache(ctx=ctx)
    except Exception as exc:
        logger.warning("Work projection warmup schedule on startup failed: %s", exc)
    start_periodic_refresh()
    try:
        yield
    finally:
        stop_periodic_refresh()


def _error_envelope(
    error: str, detail: Any, *, status_code: int, headers: dict[str, str] | None = None
) -> JSONResponse:
    """Build the public error shape without serializing exception text.

    Route-specific ``HTTPException`` details remain available when they are
    already structured or short, stable API messages. Unhandled exceptions
    never pass their ``str(exc)`` representation to a client; the correlation
    id is the only diagnostic handle exposed on the wire.
    """
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "error": error,
            "error_id": uuid.uuid4().hex,
            "detail": detail,
        },
    )


def _sanitize_public_detail(detail: Any) -> Any:
    """Retain stable API details while dropping raw exception-shaped values."""
    if isinstance(detail, dict):
        return {str(key): _sanitize_public_detail(value) for key, value in detail.items() if key != "input"}
    if isinstance(detail, list):
        return [_sanitize_public_detail(value) for value in detail]
    if not isinstance(detail, str):
        return detail

    suspicious = (
        "Traceback (most recent call last)",
        "No such file or directory",
        "OperationalError:",
        "FileNotFoundError:",
        "PermissionError:",
        "ValueError:",
        "RuntimeError:",
        "status_failed:",
        "digest_failed:",
        "drift_failed:",
    )
    if any(marker in detail for marker in suspicious):
        return "request rejected"
    if re.search(
        r"(?<![A-Za-z0-9/])/(?:home|Users|Volumes|private|opt|srv|tmp|var)(?:/[^\s\"'<>]*)?",
        detail,
    ):
        return "request rejected"
    return detail


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Normalize handled HTTP errors without changing their status codes."""
    del request
    return _error_envelope(
        "http_error",
        _sanitize_public_detail(exc.detail),
        status_code=exc.status_code,
        headers=exc.headers,
    )


async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return validation shape without echoing submitted values."""
    del request
    sanitized_errors = []
    for error in exc.errors():
        sanitized = {key: _sanitize_public_detail(value) for key, value in error.items() if key not in {"ctx", "input"}}
        sanitized_errors.append(sanitized)
    return _error_envelope("validation_error", sanitized_errors, status_code=422)


async def global_exception_handler(request: Request, exc: Exception):
    """Consistent JSON error format for unhandled exceptions."""
    error_id = uuid.uuid4().hex
    logger.error("Unhandled Monitor API exception [%s]", error_id, exc_info=exc)
    del request
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "error_id": error_id,
            "detail": "internal server error",
        },
    )


# Server start time for uptime calculation
_SERVER_START = datetime.now(UTC)


def _resolve_context(ctx: MonitorContext | None = None) -> MonitorContext:
    """Fall back to the live production context for plain-Python callers."""
    if isinstance(ctx, MonitorContext):
        return ctx
    app_ctx = getattr(app.state, "ctx", None) if "app" in globals() else None
    if isinstance(app_ctx, MonitorContext):
        return app_ctx
    return production_context()

# --- /api/orient caching + failure isolation (GH #1309) ----------------
#
# Per-section TTLs (seconds). Tuned for each collector's cost + change
# frequency. Shared in-memory cache lives in state_helpers.cache_*; keys
# are prefixed with "orient_" so ``?fresh=true`` can invalidate exactly
# this router's keys (and nothing else's).
#
# A TTL of ``0`` means "never cache at the orient layer" — the collector
# is called on every request. Use it for sections that already carry
# their own downstream cache (e.g. ``pipeline`` wraps
# ``/api/state/summary`` which has its own 60 s TTL — an orient-layer
# cache on top would stack the two windows and label up-to-119 s old
# data as fresh, reviewer BLOCKER #1309).
#
# Hard per-section timeout caps one wedged async collector. See the
# first entry in docs/monitor-api/cold-start-baseline.md for the
# incident that motivated this.
#
# Scope caveat on the hard timeout: only the ``pipeline`` collector is
# a true async coroutine; ``asyncio.wait_for`` properly cancels it. For
# the sync collectors run via ``asyncio.to_thread`` the hard timeout is
# advisory — Python threads are not cancellable once started. Real
# protection per sync collector:
#   - ``git``, ``issues``     — subprocess timeout 2 s (``_run_command``)
#   - ``runtime``, ``delegate``, ``wiki``, ``session_hints``
#                            — pure-Python / filesystem, no inner
#                              timeout; they rely on being cheap.
#   - ``idle_prs``           — cache-first detached worker; ``gh`` never runs
#                              in the request path.
#   - ``capacity``, ``health`` — cache-first detached worker (#6983); CodexBar
#                              / canaries never pin the lean gather.
# If a sync collector ever starts to block (e.g. a network FS hang), it
# will tie up a threadpool slot past the hard timeout. See
# MONITOR-API.md for the full breakdown.
ORIENT_SECTION_TTLS: dict[str, float] = {
    "git": 30.0,
    "issues": 120.0,
    "idle_prs": 60.0,
    # Pipeline has TTL 0 on purpose — ``_collect_pipeline_orient_data``
    # calls ``state_summary()`` which has its own 60 s cache. Stacking
    # caches produced staleness up to 119 s with ``generated_at``
    # labelled fresh (reviewer BLOCKER #1309 / B2).
    "pipeline": 0.0,
    "runtime": 60.0,
    "delegate": 30.0,
    "capacity": 15.0,
    "bridge_pending": 15.0,
    "rollovers": 15.0,
    "wiki": 120.0,
    "governance": 120.0,
    "health": 15.0,
    "session_hints": 60.0,
}

ORIENT_SECTION_SOURCES: dict[str, str] = {
    "git": "git",
    "issues": "gh",
    "idle_prs": "gh",
    "pipeline": "fs",
    "runtime": "fs",
    "delegate": "fs",
    "capacity": "fs",
    "bridge_pending": "sqlite",
    "rollovers": "fs",
    "wiki": "fs",
    "governance": "fs",
    "health": "probe",
    "session_hints": "fs",
}

ORIENT_SECTION_HARD_TIMEOUT_S = 5.0

IDLE_PR_THRESHOLD_S = 60 * 60
IDLE_PR_FETCH_TIMEOUT_S = 4.0
IDLE_PR_REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
IDLE_PR_CACHE_KEY = "orient_idle_prs"
IDLE_PR_SUCCESSFUL_CONCLUSIONS = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})
IDLE_PR_ADVISORY_MARKER = "advisory"
_CROSS_FAMILY_REVIEW_RE = re.compile(r"\bcross[- ]family\b", re.IGNORECASE)
_REVIEW_PASS_RE = re.compile(r"\b(?:approve(?:d)?|pass(?:ed)?)\b", re.IGNORECASE)
_REVIEW_BLOCK_RE = re.compile(
    r"\b(?:changes?[- ]requested|needs?[- ]work|blocked|fail(?:ed|ure)?)\b",
    re.IGNORECASE,
)
_REVIEW_HEAD_RE = re.compile(
    r"\b(?:at\s+)?head\b\s*[:=]?\s*`?([0-9a-f]{40})`?",
    re.IGNORECASE,
)

ORIENT_SECTION_KEYS: tuple[str, ...] = tuple(ORIENT_SECTION_TTLS.keys())

# Lean cold-start preset (``?lean=true``): the small, lane-agnostic sections an agent needs to
# orient BEFORE it has selected work — tree state (git), active dispatches (delegate), pending
# bridge asks, blocking decisions (governance), health, and the handoff pointers / current goal
# (session_hints). Excludes the three heavy sections — ``pipeline`` (~2k module stats),
# ``issues`` (full gh list), ``wiki`` (per-track coverage) — which are fetched on demand via
# ``?sections=...``. ``capacity`` and ``health`` stay in the preset but are cache-first /
# detached so CodexBar or a hung canary cannot pin the gather at 5 s (#6983).
LEAN_ORIENT_SECTIONS: tuple[str, ...] = (
    "git",
    "runtime",
    "delegate",
    "capacity",
    "bridge_pending",
    "rollovers",
    "governance",
    "health",
    "session_hints",
)

# Orient sync collectors use a dedicated executor instead of the loop's
# shared default pool. This isolates cheap orient reads from unrelated
# ``asyncio.to_thread()`` backlog elsewhere in the process, which was
# causing false ``section_timeout_0.1s`` fallbacks for ``runtime`` under
# the hard-timeout test path on loaded CI runners.
_ORIENT_SYNC_EXECUTOR = ThreadPoolExecutor(
    max_workers=8,
    thread_name_prefix="orient-sync",
)

# Lean ``capacity`` / ``health`` are cache-first and detached: CodexBar and
# integrity canaries must not pin ``asyncio.gather`` at the 5 s section
# wall (#6983). A short join lets cheap (test) collectors populate the
# same request; a live hang returns fallback immediately after this wait.
DETACHED_ORIENT_SECTION_KEYS: frozenset[str] = frozenset({"capacity", "health"})
DETACHED_ORIENT_INLINE_WAIT_S = 0.4
_detached_orient_lock = threading.Lock()
_detached_orient_threads: dict[str, threading.Thread] = {}
_detached_orient_last_good: dict[str, tuple[Any, str]] = {}
_detached_orient_last_error: dict[str, str] = {}

# The idle-PR feed is deliberately cache-first. A live GitHub request is run by
# one detached daemon worker, never by the ASGI request path. The last successful
# result remains available as a stale fallback when GitHub is slow or unavailable.
_idle_pr_refresh_lock = threading.Lock()
_idle_pr_refresh_thread: threading.Thread | None = None
_idle_pr_last_good: tuple[dict[str, Any], str] | None = None
_idle_pr_last_error: str | None = None
_idle_pr_next_retry_at = 0.0


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


def _isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _run_command(args: list[str], *, timeout: float = 2.0, ctx: MonitorContext | None = None) -> subprocess.CompletedProcess[str]:
    resolved_ctx = _resolve_context(ctx)
    cwd = resolved_ctx.roots.live_repo_root if args and args[0] == "git" else resolved_ctx.roots.project_root
    if not Path(cwd).exists():
        return subprocess.CompletedProcess(args=args, returncode=127, stdout="", stderr="cwd does not exist")
    try:
        return subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(args=args, returncode=127, stdout="", stderr=str(exc))


def _collect_git_orient_data(ctx: MonitorContext | None = None) -> dict:
    resolved_ctx = _resolve_context(ctx)
    branch_proc = _run_command(["git", "branch", "--show-current"], ctx=ctx) if ctx is not None else _run_command(["git", "branch", "--show-current"])
    head_proc = _run_command(["git", "rev-parse", "--short=9", "HEAD"], ctx=ctx) if ctx is not None else _run_command(["git", "rev-parse", "--short=9", "HEAD"])
    full_head_proc = _run_command(["git", "rev-parse", "HEAD"], ctx=ctx) if ctx is not None else _run_command(["git", "rev-parse", "HEAD"])
    ahead_proc = _run_command(["git", "rev-list", "--count", "origin/main..HEAD"], ctx=ctx) if ctx is not None else _run_command(["git", "rev-list", "--count", "origin/main..HEAD"])
    log_proc = _run_command(["git", "log", "--oneline", "-5"], ctx=ctx) if ctx is not None else _run_command(["git", "log", "--oneline", "-5"])

    if branch_proc.returncode != 0:
        raise RuntimeError(branch_proc.stderr.strip() or "git branch failed")
    if head_proc.returncode != 0:
        raise RuntimeError(head_proc.stderr.strip() or "git rev-parse failed")
    if log_proc.returncode != 0:
        raise RuntimeError(log_proc.stderr.strip() or "git log failed")

    recent_commits = []
    for line in log_proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        sha, _, subject = line.partition(" ")
        recent_commits.append({"sha": sha, "subject": subject})

    ahead_value = 0
    if ahead_proc.returncode == 0:
        try:
            ahead_value = int(ahead_proc.stdout.strip() or "0")
        except ValueError:
            ahead_value = 0
    try:
        primary_status = worktree_containment.primary_checkout_dirty_status(resolved_ctx.roots.live_repo_root)
    except Exception:
        branch = branch_proc.stdout.strip()
        primary_status = {
            "role": "primary",
            "head_sha": (full_head_proc.stdout.strip() if full_head_proc.returncode == 0 else None),
            "branch": branch,
            "protected_branch": branch in worktree_containment.PROTECTED_BRANCHES,
            "dirty": False,
            "dirty_count": 0,
        }

    branch = branch_proc.stdout.strip()
    authority = build_repository_authority(
        project_root=resolved_ctx.roots.project_root,
        live_repo_root=resolved_ctx.roots.live_repo_root,
        data_branch=branch,
    )
    return {
        "branch": branch,
        "head": head_proc.stdout.strip(),
        "ahead_of_origin": ahead_value,
        "recent_commits": recent_commits,
        "primary_checkout_dirty": primary_status["dirty"],
        "primary_checkout": {
            "role": primary_status.get("role", "primary"),
            "head_sha": primary_status.get("head_sha")
            or (full_head_proc.stdout.strip() if full_head_proc.returncode == 0 else None),
            "dirty_count": int(primary_status.get("dirty_count", 0)),
        },
        "cwd_role": cwd_role(Path(resolved_ctx.roots.live_repo_root)),
        "authority": authority,
    }


def _collect_issues_orient_data(ctx: MonitorContext | None = None) -> dict:
    """Fetch open GitHub issues via ``gh``.

    Raises ``RuntimeError`` on any failure (subprocess error, non-zero
    exit, malformed JSON). Raising is important — ``_cached_orient_section``
    only caches successful returns, so a transient ``gh`` blip must
    not poison the issues cache for the full TTL window (reviewer
    BLOCKER, GH #1309).
    """
    cmd = [
        "gh",
        "issue",
        "list",
        "--state",
        "open",
        "--limit",
        "10",
        "--json",
        "number,title,labels,createdAt",
    ]
    proc = _run_command(cmd, timeout=5.0, ctx=ctx) if ctx is not None else _run_command(cmd, timeout=5.0)

    if proc.returncode != 0:
        error = proc.stderr.strip() or proc.stdout.strip() or "gh issue list failed"
        raise RuntimeError(error)

    try:
        payload = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid gh json: {exc}") from exc

    now = datetime.now(UTC)
    issues = []
    for item in payload:
        created = _parse_iso_datetime(item.get("createdAt"))
        labels = item.get("labels") or []
        issues.append(
            {
                "number": item.get("number"),
                "title": item.get("title"),
                "labels": [label.get("name") for label in labels if isinstance(label, dict) and label.get("name")],
                "age_days": max(0, (now.date() - created.date()).days) if created else None,
            }
        )
    return {"issues": issues}


def _pr_check_timestamp(check: dict[str, Any]) -> datetime | None:
    for field in ("startedAt", "createdAt", "updatedAt", "completedAt"):
        parsed = _parse_iso_datetime(check.get(field))
        if parsed is not None:
            return parsed
    return None


def _idle_pr_checks_green(pr: dict[str, Any]) -> bool:
    """Return whether every latest non-advisory check for a PR is green.

    ``statusCheckRollup`` contains historical runs when a check has been
    restarted. Grouping by context and selecting the newest timestamp avoids
    resurrecting an old green run after a newer run went red or pending.
    Missing or malformed status data fails closed. Explicitly advisory checks
    follow the repository merge-hook convention and do not block eligibility.
    """
    rollup = pr.get("statusCheckRollup")
    if not isinstance(rollup, list) or not rollup:
        return False

    latest: dict[str, tuple[datetime, dict[str, Any]]] = {}
    for raw in rollup:
        if not isinstance(raw, dict):
            return False
        name = raw.get("name") or raw.get("context")
        timestamp = _pr_check_timestamp(raw)
        if not isinstance(name, str) or not name.strip() or timestamp is None:
            return False
        current = latest.get(name)
        if current is None or timestamp >= current[0]:
            latest[name] = (timestamp, raw)

    blocking_count = 0
    for name, (_timestamp, check) in latest.items():
        if IDLE_PR_ADVISORY_MARKER in name.casefold():
            continue
        blocking_count += 1
        status = str(check.get("status") or "").upper()
        if status and status not in {"COMPLETED", "SUCCESS"}:
            return False
        outcome = str(check.get("conclusion") or check.get("state") or "").upper()
        if outcome not in IDLE_PR_SUCCESSFUL_CONCLUSIONS:
            return False

    return blocking_count > 0


def _idle_pr_has_review_gate(pr: dict[str, Any]) -> bool:
    """Return whether GitHub or a review comment proves a passed review gate."""
    if str(pr.get("reviewDecision") or "").upper() == "APPROVED":
        return True

    head_sha = pr.get("headRefOid")
    reviews = pr.get("reviews")
    if isinstance(reviews, list):
        for review in reviews:
            if not isinstance(review, dict) or str(review.get("state") or "").upper() != "APPROVED":
                continue
            commit = review.get("commit")
            commit_sha = commit.get("oid") if isinstance(commit, dict) else commit
            if not isinstance(head_sha, str) or not commit_sha or commit_sha == head_sha:
                return True

    comments = pr.get("comments")
    if not isinstance(comments, list):
        return False
    ordered_comments = sorted(
        (comment for comment in comments if isinstance(comment, dict)),
        key=lambda comment: _parse_iso_datetime(comment.get("createdAt")) or datetime.min.replace(tzinfo=UTC),
    )
    for comment in reversed(ordered_comments):
        body = comment.get("body")
        if not isinstance(body, str) or not _CROSS_FAMILY_REVIEW_RE.search(body):
            continue
        head_match = _REVIEW_HEAD_RE.search(body)
        if (
            head_match is not None
            and isinstance(head_sha, str)
            and head_match.group(1).casefold() != head_sha.casefold()
        ):
            continue
        if _REVIEW_BLOCK_RE.search(body):
            return False
        return _REVIEW_PASS_RE.search(body) is not None
    return False


def _eligible_idle_pr(pr: dict[str, Any], *, now: datetime) -> dict[str, Any] | None:
    if pr.get("state") is not None and str(pr.get("state")).upper() != "OPEN":
        return None
    merge_state = pr.get("mergeStateStatus")
    if merge_state is not None and str(merge_state).upper() == "DIRTY":
        return None
    if pr.get("isDraft") is True or not _idle_pr_checks_green(pr):
        return None
    if not _idle_pr_has_review_gate(pr):
        return None

    number = pr.get("number")
    branch = pr.get("headRefName")
    updated_at = _parse_iso_datetime(pr.get("updatedAt"))
    if (
        not isinstance(number, int)
        or isinstance(number, bool)
        or number <= 0
        or not isinstance(branch, str)
        or not branch
        or updated_at is None
    ):
        return None

    idle_seconds = (now - updated_at).total_seconds()
    if idle_seconds <= IDLE_PR_THRESHOLD_S:
        return None
    return {
        "number": number,
        "branch": branch,
        "minutes_idle": max(0, int(idle_seconds // 60)),
    }


def _collect_idle_prs_orient_data(ctx: MonitorContext | None = None) -> dict[str, Any]:
    """Fetch and filter the compact green+reviewed+idle PR projection.

    This function is only called by the detached refresh worker. The endpoint
    itself uses ``_cached_idle_pr_section`` and never waits for this ``gh``
    subprocess.
    """
    cmd = [
        "gh",
        "pr",
        "list",
        "--repo",
        IDLE_PR_REPOSITORY,
        "--state",
        "open",
        "--limit",
        "1000",
        "--json",
        "number,state,isDraft,headRefName,headRefOid,updatedAt,reviewDecision,reviews,comments,statusCheckRollup,mergeStateStatus",
    ]
    proc = _run_command(cmd, timeout=IDLE_PR_FETCH_TIMEOUT_S, ctx=ctx) if ctx is not None else _run_command(cmd, timeout=IDLE_PR_FETCH_TIMEOUT_S)
    if proc.returncode != 0:
        error = proc.stderr.strip() or proc.stdout.strip() or "gh pr list failed"
        raise RuntimeError(error)
    try:
        payload = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid gh json: {exc}") from exc
    if not isinstance(payload, list):
        raise RuntimeError("gh pr list returned a non-list payload")

    now = datetime.now(UTC)
    rows = [row for item in payload if isinstance(item, dict) if (row := _eligible_idle_pr(item, now=now)) is not None]
    rows.sort(key=lambda row: (-row["minutes_idle"], row["number"]))
    return {"idle_prs": rows}


def _run_idle_pr_refresh(collector: Callable[[], Any]) -> None:
    global _idle_pr_last_error, _idle_pr_last_good, _idle_pr_next_retry_at
    try:
        value = collector()
        if not isinstance(value, dict) or not isinstance(value.get("idle_prs"), list):
            raise RuntimeError("idle PR collector returned an invalid payload")
    except subprocess.TimeoutExpired:
        _idle_pr_last_error = "gh_timeout"
        _idle_pr_next_retry_at = time.monotonic() + 30.0
        return
    except Exception:
        _idle_pr_last_error = "gh_unavailable"
        _idle_pr_next_retry_at = time.monotonic() + 30.0
        return

    generated_at = _isoformat_z(datetime.now(UTC))
    cache_set(IDLE_PR_CACHE_KEY, (value, generated_at))
    _idle_pr_last_good = (value, generated_at)
    _idle_pr_last_error = None
    _idle_pr_next_retry_at = 0.0


def _schedule_idle_pr_refresh(collector: Callable[[], Any]) -> None:
    global _idle_pr_refresh_thread
    if time.monotonic() < _idle_pr_next_retry_at:
        return
    with _idle_pr_refresh_lock:
        if _idle_pr_refresh_thread is not None and _idle_pr_refresh_thread.is_alive():
            return
        _idle_pr_refresh_thread = threading.Thread(
            target=_run_idle_pr_refresh,
            args=(collector,),
            daemon=True,
            name="orient-idle-pr-refresh",
        )
        _idle_pr_refresh_thread.start()


def _cached_idle_pr_section(
    collector: Callable[[], Any],
    fallback: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    ttl = ORIENT_SECTION_TTLS["idle_prs"]
    cached = cache_get(IDLE_PR_CACHE_KEY, ttl=ttl)
    if isinstance(cached, tuple) and len(cached) == 2:
        value, generated_at = cached
        if isinstance(value, dict) and isinstance(generated_at, str):
            return value, {
                "generated_at": generated_at,
                "stale_after_s": ttl,
                "source": "gh",
                "cache": "hit",
            }

    _schedule_idle_pr_refresh(collector)
    if _idle_pr_last_good is not None:
        value, generated_at = _idle_pr_last_good
        meta: dict[str, Any] = {
            "generated_at": generated_at,
            "stale_after_s": ttl,
            "source": "gh",
            "cache": "miss",
            "stale": True,
            "refreshing": _idle_pr_refresh_thread is not None and _idle_pr_refresh_thread.is_alive(),
        }
        if _idle_pr_last_error is not None:
            meta["error"] = _idle_pr_last_error
        return value, meta

    meta = {
        "generated_at": _isoformat_z(datetime.now(UTC)),
        "stale_after_s": ttl,
        "source": "gh",
        "cache": "miss",
        "refreshing": _idle_pr_refresh_thread is not None and _idle_pr_refresh_thread.is_alive(),
    }
    if _idle_pr_last_error is not None:
        meta["error"] = _idle_pr_last_error
    return fallback, meta


def reset_detached_orient_state_for_tests() -> None:
    """Drop capacity/health last-good so tests do not leak across cases."""
    with _detached_orient_lock:
        threads = list(_detached_orient_threads.values())
    for thread in threads:
        thread.join(timeout=2.0)
    with _detached_orient_lock:
        _detached_orient_threads.clear()
    _detached_orient_last_good.clear()
    _detached_orient_last_error.clear()


def _schedule_detached_orient_refresh(key: str, collector: Callable[[], Any]) -> bool:
    """Start a single-flight worker for ``key``. Return True if this call started it."""
    with _detached_orient_lock:
        thread = _detached_orient_threads.get(key)
        if thread is not None and thread.is_alive():
            return False
        worker = threading.Thread(
            target=_run_detached_orient_refresh,
            args=(key, collector),
            daemon=True,
            name=f"orient-{key}-refresh",
        )
        _detached_orient_threads[key] = worker
        worker.start()
        return True


def _run_detached_orient_refresh(key: str, collector: Callable[[], Any]) -> None:
    ttl = ORIENT_SECTION_TTLS.get(key, 60.0)
    try:
        value = collector()
        generated_at = _isoformat_z(datetime.now(UTC))
        if ttl > 0:
            cache_set(f"orient_{key}", (value, generated_at))
        _detached_orient_last_good[key] = (value, generated_at)
        _detached_orient_last_error.pop(key, None)
    except Exception as exc:
        _detached_orient_last_error[key] = str(exc)


async def _cached_detached_orient_section(
    key: str,
    collector: Callable[[], Any],
    fallback: Any,
) -> tuple[Any, dict]:
    """Cache-first section: never let a hung collector pin the gather.

    On a miss, one detached worker runs the collector. This request waits
    up to ``DETACHED_ORIENT_INLINE_WAIT_S`` only if *this* call started
    that worker (so cheap test doubles still populate the same response).
    Overlapping requests and live hangs return last-good or fallback with
    honest ``meta.error``.
    """
    ttl = ORIENT_SECTION_TTLS.get(key, 60.0)
    source = ORIENT_SECTION_SOURCES.get(key, "fs")
    cache_key = f"orient_{key}"
    if ttl > 0:
        cached = cache_get(cache_key, ttl=ttl)
        if cached is not None:
            value, generated_at = cached  # type: ignore[misc]
            return value, {
                "generated_at": generated_at,
                "stale_after_s": ttl,
                "source": source,
                "cache": "hit",
            }

    started = _schedule_detached_orient_refresh(key, collector)
    thread = _detached_orient_threads.get(key)
    if started and thread is not None and thread.is_alive():
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _ORIENT_SYNC_EXECUTOR,
            thread.join,
            DETACHED_ORIENT_INLINE_WAIT_S,
        )

    if ttl > 0:
        cached = cache_get(cache_key, ttl=ttl)
        if cached is not None:
            value, generated_at = cached  # type: ignore[misc]
            return value, {
                "generated_at": generated_at,
                "stale_after_s": ttl,
                "source": source,
                "cache": "miss",
            }

    last_good = _detached_orient_last_good.get(key)
    if last_good is not None:
        value, generated_at = last_good
        meta: dict[str, Any] = {
            "generated_at": generated_at,
            "stale_after_s": ttl,
            "source": source,
            "cache": "miss",
            "stale": True,
            "refreshing": thread is not None and thread.is_alive(),
        }
        last_error = _detached_orient_last_error.get(key)
        if last_error is not None:
            meta["error"] = last_error
        return value, meta

    short_err = _detached_orient_last_error.get(key) or "refreshing"
    meta = {
        "generated_at": _isoformat_z(datetime.now(UTC)),
        "stale_after_s": ttl,
        "source": source,
        "cache": "miss",
        "refreshing": thread is not None and thread.is_alive(),
        "error": short_err,
    }
    if isinstance(fallback, dict):
        return {**fallback, "error": short_err}, meta
    return fallback, meta


async def _collect_pipeline_orient_data(ctx: MonitorContext | None = None) -> dict:
    resolved_ctx = _resolve_context(ctx)
    return {"summary": await state_api.state_summary(fresh=False, ctx=resolved_ctx)}


_gc_sweep_lock = threading.Lock()
_gc_sweep_thread: threading.Thread | None = None
_last_gc_sweep_summary: dict[str, Any] | None = None


def _maybe_run_worktree_gc_sweep(ctx: MonitorContext | None = None) -> None:
    # Check kill switch first
    kill_switch = os.environ.get("LEARN_UK_WORKTREE_GC", "1")
    if kill_switch in ("0", "false", "no", "False", "NO"):
        return

    # Check cache TTL (default 60 minutes)
    try:
        interval_min = float(os.environ.get("LEARN_UK_WORKTREE_GC_INTERVAL_MIN", "60"))
    except ValueError:
        interval_min = 60.0
    interval_s = interval_min * 60.0

    if cache_get("worktree_gc_sweep", ttl=interval_s) is not None:
        return

    # Set cache to prevent concurrent triggering
    cache_set("worktree_gc_sweep", True)

    resolved_ctx = _resolve_context(ctx)
    global _gc_sweep_thread
    with _gc_sweep_lock:
        if _gc_sweep_thread is not None and _gc_sweep_thread.is_alive():
            return
        _gc_sweep_thread = threading.Thread(target=_run_worktree_gc_sweep, args=(resolved_ctx,), daemon=True)
        _gc_sweep_thread.start()


def _run_worktree_gc_sweep(ctx: MonitorContext | None = None) -> None:
    global _last_gc_sweep_summary
    try:
        resolved_ctx = _resolve_context(ctx)
        repo_root = primary_checkout_root(resolved_ctx.roots.project_root)

        results = reap_worktrees(
            repo_root=repo_root,
            apply=True,
            prune_merged_branches=True,
            safe_only=True,
        )

        removed = sum(1 for r in results if r.action in ("removed", "preserved_then_removed"))
        skipped = sum(1 for r in results if r.action == "skipped")
        errors = sum(1 for r in results if r.action == "error")

        _last_gc_sweep_summary = {
            "time": _isoformat_z(datetime.now(UTC)),
            "removed": removed,
            "skipped": skipped,
            "errors": errors,
        }
        logger.info("worktree GC sweep: removed=%d, skipped=%d, errors=%d", removed, skipped, errors)
    except Exception as exc:
        logger.exception("worktree GC sweep failed: %s", exc)


def _collect_runtime_orient_data(ctx: MonitorContext | None = None) -> dict:
    if ctx is not None:
        _maybe_run_worktree_gc_sweep(ctx=ctx)
        agents = runtime_api.list_runtime_agents(ctx=ctx)
        usage = runtime_api.summarize_runtime_usage(days=1, ctx=ctx)
        recent = runtime_api.runtime_recent_outcomes_today(ctx=ctx)
    else:
        _maybe_run_worktree_gc_sweep()
        agents = runtime_api.list_runtime_agents()
        usage = runtime_api.summarize_runtime_usage(days=1)
        recent = runtime_api.runtime_recent_outcomes_today()
    headroom = {}
    for agent_info in agents:
        name = agent_info.get("name")
        model = agent_info.get("default_model")
        if not name or not model:
            continue
        try:
            ok, _ = runtime_api.has_headroom(str(name), str(model))
        except Exception:
            ok = False
        headroom[str(name)] = ok

    by_agent = usage.get("by_agent", {})

    res = {
        "agents": [agent["name"] for agent in agents if agent.get("name")],
        "recent_outcomes": recent,
        "by_agent": by_agent,
        "headroom": headroom,
    }
    if _last_gc_sweep_summary is not None:
        res["worktree_gc"] = _last_gc_sweep_summary
    return res


def _collect_delegate_orient_data(ctx: MonitorContext | None = None) -> dict:
    if ctx is not None:
        recent = delegate_api.list_delegate_tasks(status="all", limit=5, ctx=ctx)
        active = delegate_api.active_delegate_count(ctx=ctx)
    else:
        recent = delegate_api.list_delegate_tasks(status="all", limit=5)
        active = delegate_api.active_delegate_count()
    return {
        "active_count": active,
        "recent": recent["tasks"],
    }


def _collect_capacity_orient_data(ctx: MonitorContext | None = None) -> dict:
    resolved_ctx = _resolve_context(ctx)
    budget = state_api.compute_routing_budget(
        budget_config_path=resolved_ctx.roots.project_root / "scripts" / "config" / "agent_budgets.yaml",
        tasks_dir=resolved_ctx.roots.batch_state_dir / "tasks",
        project_root=resolved_ctx.roots.project_root,
        curriculum_root=resolved_ctx.roots.curriculum_root,
        batch_state_dir=resolved_ctx.roots.batch_state_dir,
    )
    lanes_summary = {}
    agents = budget.get("agents", {})
    in_flight = budget.get("in_flight", {})
    for lane in state_api.SUBSCRIPTION_LANES:
        data = agents.get(lane, {})
        health = data.get("health", {})
        healthy = health.get("healthy", True) if isinstance(health, dict) else True
        lanes_summary[lane] = {
            "in_flight": in_flight.get(lane, 0),
            "healthy": healthy,
            "burn_pct_7d": data.get("burn_pct_7d"),
            "remaining_pct": data.get("remaining_pct"),
            "status": data.get("status", "unknown"),
        }
    rec = budget.get("recommendation", {}).get("primary_agent_for_code")
    return {
        "lanes": lanes_summary,
        "primary_recommendation": rec,
    }


def _collect_bridge_pending_orient_data(ctx: MonitorContext | None = None) -> dict:
    _resolve_context(ctx)
    from scripts.ai_agent_bridge import _channels  # noqa: PLC0415 — optional broker bridge

    return _channels.bridge_pending_summary()


def _collect_rollovers_orient_data(ctx: MonitorContext | None = None) -> dict:
    resolved_ctx = _resolve_context(ctx)
    return collect_rollover_orient_data(live_repo_root=resolved_ctx.roots.live_repo_root)


def _collect_wiki_orient_data(ctx: MonitorContext | None = None) -> dict:
    """Per-track compiled article counts.

    The previous implementation called ``_resolve_article`` inside the per-slug
    loop (~22 tracks × ~80 slugs = ~1776 calls). Each ``_resolve_article``
    rebuilds the full slug→candidates index from a wiki-tree scan, so the
    1776 calls × ~4 ms = ~7 s consistently exceeded the 5 s
    ``ORIENT_SECTION_HARD_TIMEOUT_S`` cap and the section returned
    ``error: section_timeout_5.0s`` on every cold cache miss.

    Fix: build the candidates index once (~6 ms) and resolve in pure dict
    lookups + Path.exists() checks. Same answer, ~50× faster.
    """
    resolved_ctx = _resolve_context(ctx)
    wiki_api.wiki_state.get_status_summary()

    candidates = wiki_api._list_article_candidates()  # one full-tree scan
    wiki_dir = resolved_ctx.roots.project_root / "wiki"

    by_track: dict[str, dict[str, Any]] = {}
    known_tracks = wiki_api._known_tracks(ctx=ctx) if ctx is not None else wiki_api._known_tracks()
    for track in known_tracks:
        slugs = wiki_api._track_slugs(track)
        if not slugs:
            continue
        compiled = 0
        for slug in slugs:
            slug_cands = candidates.get(slug)
            if not slug_cands:
                continue
            # Mirror _resolve_article: prefer domain-matching candidates,
            # fall back to any candidate. Take the lexicographically-first
            # path within the chosen group, then check it actually exists.
            domain_matches = [c for c in slug_cands if wiki_api._matches_track_domain(track, c["path"])]
            chosen = sorted(
                domain_matches or slug_cands,
                key=lambda item: item["path"],
            )[0]
            if (wiki_dir / chosen["path"]).exists():
                compiled += 1
        total = len(slugs)
        by_track[track] = {
            "compiled": compiled,
            "total": total,
            "pct": round(compiled / total * 100, 1) if total else 0,
        }
    return {"by_track": by_track}


def _collect_governance_orient_data(ctx: MonitorContext | None = None) -> dict[str, int]:
    return collect_governance_summary(ctx=ctx) if ctx is not None else collect_governance_summary()


logger = logging.getLogger(__name__)


def _port_open(host: str, port: int, timeout_s: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def _readable_file(path: Path) -> bool:
    return path.exists() and path.is_file() and os.access(path, os.R_OK)


def _core_bare_canary(ctx: MonitorContext | None = None) -> bool:
    """Detection canary for issue #2842: ``core.bare`` must stay false.

    ``core.bare`` lives in the SHARED ``.git/config``; if any subprocess flips it
    to ``true`` it silently breaks ``git`` work-tree ops for the main checkout AND
    every linked worktree at once. Reading/writing git config does not need a work
    tree, so this check still functions while the footgun is active — which is when
    it's needed. On drift it auto-resets to false and logs an alert. Never raises:
    the canary must not break health collection.
    """
    resolved_ctx = _resolve_context(ctx)
    try:
        from scripts.audit.check_core_bare import check_core_bare  # noqa: PLC0415 — script-path fallback
    except ImportError:  # path-flavoured import for test/script contexts
        from audit.check_core_bare import check_core_bare  # noqa: PLC0415 — script-path fallback
    try:
        ok, message = check_core_bare(resolved_ctx.roots.project_root, fix=True)
    except Exception:
        logger.exception("core.bare canary (#2842) failed to run")
        return True  # fail-open: don't raise a false alarm on canary error
    if "reset" in message or not ok:
        logger.warning("core.bare canary (#2842): %s", message)
    return ok


def _self_symlink_canary(ctx: MonitorContext | None = None) -> bool:
    """Detection canary for the node_modules ELOOP footgun.

    A self-referential ``node_modules`` symlink (``X -> X``) is an infinite
    loop. ``npm run <script>`` builds its child PATH by walking the directory
    tree upward and prepending every ancestor ``node_modules/.bin``; resolving
    the looping ancestor makes ``spawn`` return ``ELOOP``, so every npm build
    dies instantly with exit 194 and no output — looking like "Astro is broken"
    when it is not. The loop is gitignored so CI cannot catch it; only a local
    canary can. On detection it reports the link without removing it; repair is
    an explicit doctor action. Never raises: the canary must not break health
    collection. See the autopsy
    ``docs/bug-autopsies/node-modules-eloop-symlink.md``.
    """
    resolved_ctx = _resolve_context(ctx)
    try:
        from scripts.audit.check_self_symlinks import check_self_symlinks  # noqa: PLC0415 — script-path fallback
    except ImportError:  # path-flavoured import for test/script contexts
        from audit.check_self_symlinks import check_self_symlinks  # noqa: PLC0415 — script-path fallback
    try:
        ok, message = check_self_symlinks(resolved_ctx.roots.project_root, fix=False)
    except Exception:
        logger.exception("node_modules ELOOP canary failed to run")
        return True  # fail-open: don't raise a false alarm on canary error
    if not ok:
        logger.warning("node_modules ELOOP canary: %s", message)
    return ok


def _primary_integrity_canary(ctx: MonitorContext | None = None) -> bool:
    """Read-only checkout diagnostic for primary-checkout drift.

    #5803 follow-up: a worker detached the primary checkout (`checkout: moving
    from main to FETCH_HEAD`). Git-layer prevention was proven impossible
    against a same-UID process (design panel: gpt-5.6-sol + agy), so this
    canary detects drift and records diagnostic evidence without switching,
    fetching, or pulling the human's checkout.
    Never raises: the canary must not break health collection.
    """
    resolved_ctx = _resolve_context(ctx)
    try:
        from scripts.audit.check_primary_integrity import (  # noqa: PLC0415 — script-path fallback
            check_primary_integrity,
        )
    except ImportError:  # path-flavoured import for test/script contexts
        from audit.check_primary_integrity import check_primary_integrity  # noqa: PLC0415 — script-path fallback
    try:
        ok, message = check_primary_integrity(
            resolved_ctx.roots.project_root,
            fix=False,
            tasks_dir=resolved_ctx.roots.batch_state_dir / "tasks",
        )
    except Exception:
        logger.exception("primary-integrity canary failed to run")
        return True  # fail-open: don't raise a false alarm on canary error
    if not ok:
        logger.warning("primary-integrity canary: %s", message)
    return ok


def _node_modules_integrity_canary(ctx: MonitorContext | None = None) -> bool:
    """Read-only diagnostic for symlink corruption of the primary's node_modules.

    #6818 follow-up: `_provision_data_symlinks` (`scripts/delegate.py`)
    symlinks the primary's `node_modules`/`site/node_modules` directly into
    every dispatch worktree, so a worktree write lands in the primary's real
    files (#6805 incident). ALERT-only, same posture as
    `_primary_integrity_canary` — detects and records, never repairs. Never
    raises: the canary must not break health collection.
    """
    resolved_ctx = _resolve_context(ctx)
    try:
        from scripts.audit.check_node_modules_integrity import (  # noqa: PLC0415 — script-path fallback
            check_node_modules_integrity,
        )
    except ImportError:  # path-flavoured import for test/script contexts
        from audit.check_node_modules_integrity import (  # noqa: PLC0415 — script-path fallback
            check_node_modules_integrity,
        )
    try:
        ok, message = check_node_modules_integrity(
            resolved_ctx.roots.project_root,
            tasks_dir=resolved_ctx.roots.batch_state_dir / "tasks",
        )
    except Exception:
        logger.exception("node_modules-integrity canary failed to run")
        return True  # fail-open: don't raise a false alarm on canary error
    if not ok:
        logger.warning("node_modules-integrity canary: %s", message)
    return ok


def _venv_integrity_canary(ctx: MonitorContext | None = None) -> bool:
    """Read-only diagnostic for an empty/broken primary venv.

    #6830 follow-up: a mid-session venv rebuild left `.venv` with no
    site-packages, and separately, console-script launchers
    (`pytest`/`py.test`/`cbor2`) were found pointing at a deleted worktree
    venv. ALERT-only, same posture as `_node_modules_integrity_canary` —
    detects and records, never repairs. Never raises: the canary must not
    break health collection.
    """
    resolved_ctx = _resolve_context(ctx)
    try:
        from scripts.audit.check_venv_integrity import check_venv_integrity  # noqa: PLC0415 — script-path fallback
    except ImportError:  # path-flavoured import for test/script contexts
        from audit.check_venv_integrity import check_venv_integrity  # noqa: PLC0415 — script-path fallback
    try:
        ok, message = check_venv_integrity(
            resolved_ctx.roots.project_root,
            tasks_dir=resolved_ctx.roots.batch_state_dir / "tasks",
        )
    except Exception:
        logger.exception("venv-integrity canary failed to run")
        return True  # fail-open: don't raise a false alarm on canary error
    if not ok:
        logger.warning("venv-integrity canary: %s", message)
    return ok


def _worktree_cleanup_integrity_canary(ctx: MonitorContext | None = None) -> bool:
    """Read-only diagnostic for a dark/red worktree-cleanup LaunchAgent.

    #6937 follow-up: launchd stopped starting the job after a venv rewrite
    (LWCR init failure, exit 78) and no receipt landed for two days.
    ALERT-only, same posture as `_venv_integrity_canary` — detects and
    records, never reloads launchd. Never raises: the canary must not break
    health collection.
    """
    resolved_ctx = _resolve_context(ctx)
    try:
        from scripts.audit.check_worktree_cleanup_integrity import (  # noqa: PLC0415 — script-path fallback
            check_worktree_cleanup_integrity,
        )
    except ImportError:  # path-flavoured import for test/script contexts
        from audit.check_worktree_cleanup_integrity import (  # noqa: PLC0415 — script-path fallback
            check_worktree_cleanup_integrity,
        )
    try:
        ok, message = check_worktree_cleanup_integrity(
            resolved_ctx.roots.project_root,
            tasks_dir=resolved_ctx.roots.batch_state_dir / "tasks",
        )
    except Exception:
        logger.exception("worktree-cleanup-integrity canary failed to run")
        return True  # fail-open: don't raise a false alarm on canary error
    if not ok:
        logger.warning("worktree-cleanup-integrity canary: %s", message)
    return ok


def _tmp_usability_canary() -> dict:
    """Detection probe for issue #7164: /tmp usage plus a small write probe.

    A quota-exhausted tmpfs fails every write with EDQUOT while ``df`` still
    looks healthy; the probe classifies EDQUOT distinctly so the state is
    visible on the health glance instead of masquerading as random crashes.
    Never raises: the canary must not break health collection.
    """
    try:
        from scripts.audit.check_tmp_usability import probe_tmp_usability  # noqa: PLC0415 — script-path fallback
    except ImportError:  # path-flavoured import for test/script contexts
        from audit.check_tmp_usability import probe_tmp_usability  # noqa: PLC0415 — script-path fallback
    try:
        return probe_tmp_usability()
    except Exception:
        logger.exception("tmp-usability canary (#7164) failed to run")
        # fail-open: don't raise a false alarm on canary error
        return {"ok": True, "writable": True, "error": None, "probe_error": True}


def _collect_health_orient_data(ctx: MonitorContext | None = None) -> dict:
    resolved_ctx = _resolve_context(ctx)
    mcp_sources_ok = _port_open("127.0.0.1", 8766, 0.2)
    tmp_usability = _tmp_usability_canary()
    if ctx is not None:
        core_bare_ok = _core_bare_canary(ctx=ctx)
        self_symlink_ok = _self_symlink_canary(ctx=ctx)
        primary_integrity_ok = _primary_integrity_canary(ctx=ctx)
        node_modules_integrity_ok = _node_modules_integrity_canary(ctx=ctx)
        venv_integrity_ok = _venv_integrity_canary(ctx=ctx)
        worktree_cleanup_integrity_ok = _worktree_cleanup_integrity_canary(ctx=ctx)
    else:
        core_bare_ok = _core_bare_canary()
        self_symlink_ok = _self_symlink_canary()
        primary_integrity_ok = _primary_integrity_canary()
        node_modules_integrity_ok = _node_modules_integrity_canary()
        venv_integrity_ok = _venv_integrity_canary()
        worktree_cleanup_integrity_ok = _worktree_cleanup_integrity_canary()
    return {
        "api": True,
        "mcp_sources": mcp_sources_ok,
        "mcp_rag": mcp_sources_ok,
        "sources_db": _readable_file(resolved_ctx.roots.sources_db_path),
        "message_broker": _readable_file(resolved_ctx.roots.message_db_path),
        "git_core_bare_ok": core_bare_ok,
        "node_modules_symlinks_ok": self_symlink_ok,
        "primary_integrity_ok": primary_integrity_ok,
        "node_modules_integrity_ok": node_modules_integrity_ok,
        "venv_integrity_ok": venv_integrity_ok,
        "worktree_cleanup_integrity_ok": worktree_cleanup_integrity_ok,
        "tmp_usability_ok": bool(tmp_usability.get("ok")),
        "tmp_usability": tmp_usability,
    }


def _first_non_empty_line(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    except OSError:
        return ""
    return ""


def _collect_session_hints_orient_data(ctx: MonitorContext | None = None) -> list[dict]:
    resolved_ctx = _resolve_context(ctx)
    session_state_dir = resolved_ctx.roots.project_root / "docs" / "session-state"
    if not session_state_dir.exists():
        return []
    hints = []
    for path in sorted(session_state_dir.glob("*.md"), reverse=True)[:10]:
        hints.append(
            {
                "file": str(path.relative_to(resolved_ctx.roots.project_root)),
                "first_line": _first_non_empty_line(path),
            }
        )
    return hints


# ==================== SHARED ENDPOINTS ====================


def _health_instance_identity(ctx: MonitorContext | None = None) -> dict[str, str | None]:
    """Return loopback-safe opaque host id and serving vs checkout SHAs for /api/health."""
    resolved_ctx = _resolve_context(ctx)
    host_label = resolve_launcher_host_id()
    head_proc = _run_command(["git", "rev-parse", "HEAD"], ctx=ctx) if ctx is not None else _run_command(["git", "rev-parse", "HEAD"])
    checkout_sha = head_proc.stdout.strip() if head_proc.returncode == 0 else None
    project_root = resolved_ctx.roots.project_root.resolve()
    if is_release_root(project_root):
        serving_sha = project_root.name
        serving_mode = "release"
    else:
        serving_sha = None
        serving_mode = "checkout"
    return {
        "host": host_label,
        "git_sha": checkout_sha,
        "checkout_sha": checkout_sha,
        "serving_sha": serving_sha,
        "serving_mode": serving_mode,
    }


@core_router.get("/api", status_code=307)
async def api_index():
    """API root — redirect humans to the interactive docs explorer (#7090)."""
    return RedirectResponse(url="/docs", status_code=307)


@core_router.get("/api/health")
async def health_check(request: Request, ctx: MonitorContext = Depends(get_ctx)):
    """Root health check — returns server status, version, uptime."""
    now = datetime.now(UTC)
    uptime = now - _SERVER_START
    return {
        "status": "ok",
        "version": request.app.version,
        "uptime_seconds": int(uptime.total_seconds()),
        "started_at": _SERVER_START.isoformat(),
        "checked_at": now.isoformat(),
        "instance": _health_instance_identity(ctx),
        "resilience": get_resilience_snapshot(),
        "codexbar": scheduler_status(),
    }


async def _cached_orient_section(
    key: str,
    collector: Callable[[], Any] | Callable[[], Awaitable[Any]],
    fallback: Any,
    *,
    is_async: bool = False,
) -> tuple[Any, dict]:
    """Run one orient collector with TTL cache + hard timeout + fallback.

    Returns (value, meta). Meta always includes ``generated_at``,
    ``stale_after_s``, ``source``, and ``cache`` ("hit" / "miss"); it
    adds ``error`` on failure so callers can tell a populated section
    from a degraded one.

    Errors are NOT cached — the next call retries. This is intentional:
    a transient git/gh hiccup shouldn't poison a 2-minute TTL window.
    """
    if key == "idle_prs":
        return _cached_idle_pr_section(collector, fallback)  # type: ignore[arg-type]
    if key in DETACHED_ORIENT_SECTION_KEYS:
        return await _cached_detached_orient_section(key, collector, fallback)  # type: ignore[arg-type]

    ttl = ORIENT_SECTION_TTLS.get(key, 60.0)
    source = ORIENT_SECTION_SOURCES.get(key, "fs")
    cache_key = f"orient_{key}"

    # ttl == 0 means "don't cache at the orient layer". Skip both the
    # cache read AND the cache write paths so callers never see stale
    # data and no zombie entries linger in the dict.
    if ttl > 0:
        cached = cache_get(cache_key, ttl=ttl)
        if cached is not None:
            value, generated_at = cached  # type: ignore[misc]
            return value, {
                "generated_at": generated_at,
                "stale_after_s": ttl,
                "source": source,
                "cache": "hit",
            }

    generated_at = _isoformat_z(datetime.now(UTC))
    meta: dict[str, Any] = {
        "generated_at": generated_at,
        "stale_after_s": ttl,
        "source": source,
        "cache": "miss",
    }

    try:
        if is_async:
            value = await asyncio.wait_for(
                collector(),  # type: ignore[misc]
                timeout=ORIENT_SECTION_HARD_TIMEOUT_S,
            )
        else:
            loop = asyncio.get_running_loop()
            value = await asyncio.wait_for(
                loop.run_in_executor(
                    _ORIENT_SYNC_EXECUTOR,
                    collector,  # type: ignore[arg-type]
                ),
                timeout=ORIENT_SECTION_HARD_TIMEOUT_S,
            )
    except TimeoutError:
        # Short, machine-readable code in the value; richer detail in meta.
        short_err = f"section_timeout_{ORIENT_SECTION_HARD_TIMEOUT_S}s"
        meta["error"] = short_err
        if isinstance(fallback, dict):
            return {**fallback, "error": short_err}, meta
        return fallback, meta
    except Exception as exc:
        # Preserve original API contract: value error = str(exc). Meta
        # gets the richer "TypeName: msg" form for debugging.
        short_err = str(exc)
        meta["error"] = f"{type(exc).__name__}: {exc}"
        if isinstance(fallback, dict):
            return {**fallback, "error": short_err}, meta
        return fallback, meta

    if ttl > 0:
        cache_set(cache_key, (value, generated_at))
    return value, meta


def _parse_orient_sections(sections_param: str | None, *, lean: bool = False) -> list[str]:
    """Validate and expand the optional ``sections`` query param.

    An explicit ``sections`` list always wins. When it is absent, ``lean`` selects the
    lightweight cold-start preset (``LEAN_ORIENT_SECTIONS``); otherwise the full payload.
    """
    default = list(LEAN_ORIENT_SECTIONS if lean else ORIENT_SECTION_KEYS)
    if sections_param is None:
        return default
    keys = [part.strip() for part in sections_param.split(",") if part.strip()]
    if not keys:
        return default
    unknown = [key for key in keys if key not in ORIENT_SECTION_TTLS]
    if unknown:
        valid = ", ".join(ORIENT_SECTION_KEYS)
        raise HTTPException(
            status_code=400,
            detail=f"Unknown orient section(s): {', '.join(unknown)}. Valid keys: {valid}",
        )
    return keys


def _orient_section_specs() -> dict[str, tuple[Callable[..., Any], Any, bool]]:
    """Return orient collector specs using live module attributes (test-friendly)."""
    return {
        "git": (_collect_git_orient_data, {}, False),
        "issues": (_collect_issues_orient_data, {"issues": []}, False),
        "idle_prs": (_collect_idle_prs_orient_data, {"idle_prs": []}, False),
        "pipeline": (_collect_pipeline_orient_data, {"summary": {}}, True),
        "runtime": (_collect_runtime_orient_data, {}, False),
        "delegate": (_collect_delegate_orient_data, {"active_count": 0, "recent": []}, False),
        "capacity": (_collect_capacity_orient_data, {"lanes": {}}, False),
        "bridge_pending": (_collect_bridge_pending_orient_data, {}, False),
        "rollovers": (
            _collect_rollovers_orient_data,
            {"counts": {}, "actionable": [], "errors": []},
            False,
        ),
        "wiki": (_collect_wiki_orient_data, {"by_track": {}}, False),
        "governance": (
            _collect_governance_orient_data,
            {
                "decisions_total": 0,
                "decisions_stale": 0,
                "decisions_approaching_expiry": 0,
                "adrs_total": 0,
                "adrs_warnings": 0,
                "adrs_errors": 0,
            },
            False,
        ),
        "health": (_collect_health_orient_data, {"api": True}, False),
        "session_hints": (_collect_session_hints_orient_data, [], False),
    }


@core_router.get("/api/orient")
async def orient(
    request: Request,
    fresh: bool = False,
    lean: bool = Query(
        False,
        description="Lean cold-start preset: return only the lightweight sections "
        "(git, runtime, delegate, bridge_pending, rollovers, governance, health, session_hints), "
        "skipping the heavy pipeline/issues/wiki and idle_prs. Ignored when 'sections' is given.",
    ),
    sections: str | None = Query(
        None,
        description="Comma-separated subset of orient sections to collect.",
    ),
    role: str | None = Query(
        None,
        max_length=reg.MAX_QUERY_VALUE_LEN,
        description="Opt-in ADR-011 P3 cold-start research role. Adds pointer-only research.",
    ),
):
    """One-shot agent orientation.

    Query params:
        fresh: if true, invalidate every ``orient_*`` cache entry before
            gathering. Use it when an agent just committed, renamed a
            file, or otherwise needs to see a change it made moments
            ago without waiting for the longest section TTL (up to
            120 s for ``issues``/``wiki``). The idle-PR refresh remains
            cache-first and detached. Reviewer BLOCKER B3 / #1309.
        sections: comma-separated list of section keys to collect. Unknown
            keys return 400. Omitted = full payload (back-compat).
        role: ADR-011 P3 opt-in. Absent → the response is byte-identical to
            the pre-P3 orient (no research key, no shared-cache contamination).
            Present + registry enabled → a pointer-only ``research`` section of
            the role's ``cold_start_roles`` announcements (≤5 / ≤1.5 KB, bodies
            fetched on demand). Computed fresh per request and never stored in
            the shared ``orient_*`` cache, so two roles can never contaminate
            each other's pointers.
    """
    if fresh:
        cache_invalidate("orient_")

    selected = _parse_orient_sections(sections, lean=lean)
    section_specs = _orient_section_specs()
    gather_results = await asyncio.gather(
        *[
            _cached_orient_section(
                key,
                section_specs[key][0],
                section_specs[key][1],
                is_async=section_specs[key][2],
            )
            for key in selected
        ]
    )

    section_data: dict[str, Any] = {}
    section_metas: dict[str, dict[str, Any]] = {}
    for key, (value, meta) in zip(selected, gather_results, strict=True):
        section_data[key] = value
        section_metas[key] = meta

    generated_candidates: list[str] = [
        ts for m in section_metas.values() if isinstance(ts := m.get("generated_at"), str)
    ]
    top_generated_at = min(generated_candidates) if generated_candidates else _isoformat_z(datetime.now(UTC))

    response: dict[str, Any] = {
        "generated_at": top_generated_at,
        "meta": section_metas,
    }

    if "git" in section_data:
        response["git"] = section_data["git"]
    if "issues" in section_data:
        issues_info = section_data["issues"]
        response["issues"] = issues_info.get("issues", []) if isinstance(issues_info, dict) else []
    if "idle_prs" in section_data:
        idle_prs_info = section_data["idle_prs"]
        response["idle_prs"] = idle_prs_info.get("idle_prs", []) if isinstance(idle_prs_info, dict) else []
    if "pipeline" in section_data:
        response["pipeline"] = section_data["pipeline"]
    if "runtime" in section_data:
        response["runtime"] = section_data["runtime"]
    if "delegate" in section_data:
        response["delegate"] = section_data["delegate"]
    if "capacity" in section_data:
        response["capacity"] = section_data["capacity"]
    if "bridge_pending" in section_data:
        response["bridge_pending"] = section_data["bridge_pending"]
    if "rollovers" in section_data:
        response["rollovers"] = section_data["rollovers"]
    if "wiki" in section_data:
        response["wiki"] = section_data["wiki"]
    if "governance" in section_data:
        governance_info = section_data["governance"]
        response["governance"] = governance_info
        section_metas["governance"] = {**section_metas["governance"], **governance_info}
    if "health" in section_data:
        response["health"] = section_data["health"]
    if "session_hints" in section_data:
        response["session_hints"] = section_data["session_hints"]

    if "issues" in section_data:
        issues_info = section_data["issues"]
        if isinstance(issues_info, dict) and issues_info.get("error"):
            response["issues_error"] = issues_info["error"]
    if "idle_prs" in section_data:
        idle_prs_info = section_data["idle_prs"]
        if isinstance(idle_prs_info, dict) and idle_prs_info.get("error"):
            response["idle_prs_error"] = idle_prs_info["error"]

    _attach_cold_start_research(response, role)
    return add_json_telemetry(response, session_id=session_id_from_request(request))


def _attach_cold_start_research(response: dict[str, Any], role: str | None) -> None:
    """Add the ADR-011 P3 pointer-only research section for an opt-in role.

    No-op (leaving the response byte-identical to the pre-P3 orient) when no role
    is given, the kill switch is off, the registry cannot be exposed, or anything
    in the selector/loader path raises unexpectedly — fail-open, never a 500 for
    orient as a whole. POINTERS ONLY: it calls the role-only cold-start selector
    (``cold_start_roles``, never the AND matcher), never ``select_bodies``; record
    bodies are fetched on demand from the documented, well-known
    ``GET /api/knowledge/record/{id}`` (see ``docs/MONITOR-API.md``) — omitted here
    rather than repeated per response so the envelope stays inside the same
    ``MAX_FILTERED_BYTES`` (1536 B) budget the selector already caps pointers to.
    Computed inline, never cached at the orient layer, so role-specific pointers
    never share a cache key.
    """
    if not role or not role.strip():
        return
    try:
        if not reg.is_enabled():
            return
        runtime = reg.load_runtime_safe()
        if runtime is None:
            return
        pointers, _dropped = reg.select_cold_start_pointers(runtime, role)
        response["research"] = {"enabled": True, "records": pointers}
    except Exception:
        logger.warning(
            "orient: cold-start research selector failed unexpectedly for role %r; omitting research section",
            role,
            exc_info=True,
        )
        response.pop("research", None)


@core_router.get("/api/config")
async def get_config(request: Request, ctx: MonitorContext = Depends(get_ctx)):
    # Import pipeline phase config — single source of truth
    try:
        from scripts.build.phase_constants import PHASE_LABELS, PHASES  # noqa: PLC0415 — preserves endpoint fallback

        pipeline_info = {"phases": PHASES, "phase_labels": PHASE_LABELS}
    except ImportError:
        pipeline_info = {}
    return {"levels": LEVELS, "api_version": request.app.version, "pipeline": pipeline_info}


@core_router.get("/api/batch/dispatcher")
async def get_dispatcher_state(ctx: MonitorContext = Depends(get_ctx)):
    state_file = ctx.roots.batch_state_dir / "dispatcher_state.json"
    if not state_file.exists():
        return {"tracks": {}}
    with open(state_file) as f:
        return json.load(f)


@core_router.get("/api/batch/active")
async def get_active_orchestration(ctx: MonitorContext = Depends(get_ctx)):
    active = []
    if not ctx.roots.curriculum_root.exists():
        return active
    for track_dir in ctx.roots.curriculum_root.iterdir():
        if not track_dir.is_dir():
            continue
        orch_dir = track_dir / "orchestration"
        if not orch_dir.exists():
            continue
        for module_dir in orch_dir.iterdir():
            if not module_dir.is_dir():
                continue
            latest_mtime = 0.0
            for f in module_dir.iterdir():
                if f.is_file():
                    latest_mtime = max(latest_mtime, f.stat().st_mtime)
            if (datetime.now().timestamp() - latest_mtime) < 900:
                active.append(
                    {
                        "slug": module_dir.name,
                        "track": track_dir.name,
                        "seconds_ago": int(datetime.now().timestamp() - latest_mtime),
                    }
                )
    return active


@core_router.get("/api/batch/failures")
async def get_failure_queue(ctx: MonitorContext = Depends(get_ctx)):
    f_file = ctx.roots.batch_state_dir / "failure_queue.json"
    if not f_file.exists():
        return []
    with open(f_file) as f:
        return json.load(f)


@core_router.get("/api/batch/usage")
async def get_batch_usage(ctx: MonitorContext = Depends(get_ctx)):
    usage_dir = ctx.roots.batch_state_dir / "api_usage"
    if not usage_dir.exists():
        return {}
    summaries = {}
    for f in sorted(usage_dir.glob("summary_*.json")):
        track = f.stem.replace("summary_", "")
        try:
            with open(f) as fh:
                summaries[track] = json.load(fh)
        except Exception:
            pass
    return summaries


@core_router.get("/api/batch/checkpoints")
async def get_all_checkpoints(ctx: MonitorContext = Depends(get_ctx)):
    results = {}
    if not ctx.roots.batch_state_dir.exists():
        return results
    for f in ctx.roots.batch_state_dir.glob("checkpoint_*.json"):
        track = f.stem.replace("checkpoint_", "")
        try:
            with open(f) as fh:
                results[track] = json.load(fh)
        except Exception:
            pass
    return results


@core_router.get("/api/batch/dispatcher/running")
async def dispatcher_running():
    return {"running": False}


@core_router.post("/api/batch/dispatcher/scan")
async def run_dispatcher_scan(ctx: MonitorContext = Depends(get_ctx)):
    cmd = [
        str(ctx.roots.live_repo_root / ".venv" / "bin" / "python"),
        str(ctx.roots.live_repo_root / "scripts" / "batch_dispatcher.py"),
        "scan",
    ]
    # Use asyncio.to_thread to avoid blocking the event loop
    result = await asyncio.to_thread(subprocess.run, cmd, cwd=ctx.roots.live_repo_root)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Dispatcher scan failed")
    return {"status": "ok"}


@core_router.get("/api/batch/dispatcher/logs")
async def get_dispatcher_logs(lines: int = 50, ctx: MonitorContext = Depends(get_ctx)):
    log_file = ctx.roots.project_root / "logs" / "dispatcher.log"
    if not log_file.exists():
        return {"lines": []}
    return {"lines": log_file.read_text().splitlines()[-lines:]}


# ==================== WEBSOCKET ====================


@core_router.websocket("/ws/batch")
async def batch_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"type": "heartbeat"})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass


# ==================== IMAGE SERVING ====================

_ALLOWED_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
_MIME_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _safe_join(base: Path, *parts: str | Path) -> Path | None:
    try:
        return safe_join(base, *parts)
    except ValueError:
        return None


@core_router.get("/images/{path:path}")
async def serve_image(path: str, ctx: MonitorContext = Depends(get_ctx)):
    """Serve textbook images with caching. Path relative to data/textbook_images/."""
    image_dir = ctx.roots.images_dir or (ctx.roots.project_root / "data" / "textbook_images")
    file_path = _safe_join(image_dir, path)
    if file_path is None:
        raise HTTPException(status_code=403, detail="Invalid image path")
    if file_path.suffix.lower() not in _ALLOWED_IMG_EXT:
        raise HTTPException(status_code=403, detail="Forbidden file type")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404)
    # Prevent path traversal
    try:
        file_path.resolve().relative_to(image_dir.resolve())
    except ValueError as e:
        raise HTTPException(status_code=403, detail="Path traversal not allowed") from e
    return FileResponse(
        file_path,
        media_type=_MIME_TYPES.get(file_path.suffix.lower(), "application/octet-stream"),
        headers={"Cache-Control": "max-age=3600"},
    )


# ==================== STATIC FILES (MUST BE LAST) ====================


@core_router.get("/{path:path}")
async def serve_static(path: str, ctx: MonitorContext = Depends(get_ctx)):
    dashboards_dir = ctx.roots.dashboards_dir
    if not path or path == "/":
        return FileResponse(dashboards_dir / "index.html")
    file_path = _safe_join(dashboards_dir, path)
    if file_path is None:
        raise HTTPException(status_code=403, detail="Path traversal not allowed")
    dashboards_root = dashboards_dir.resolve()
    # Keep explicit traversal guard if relative path join bypassed via symlink tricks.
    if not file_path.resolve().is_relative_to(dashboards_root):
        raise HTTPException(status_code=403, detail="Path traversal not allowed")
    if file_path.is_file():
        return FileResponse(file_path)
    if file_path.is_dir() and (file_path / "index.html").is_file():
        return FileResponse(file_path / "index.html")
    if not file_path.suffix:
        html_candidate = _safe_join(dashboards_dir, f"{path}.html")
        if (
            html_candidate is not None
            and html_candidate.resolve().is_relative_to(dashboards_root)
            and html_candidate.is_file()
        ):
            return FileResponse(html_candidate)
    raise HTTPException(status_code=404)


def create_app(context: MonitorContext, *, lifespan: Any = None) -> FastAPI:
    """Build a fresh Monitor API app bound to one context."""
    factory_lifespan = _lifespan if lifespan is None else lifespan
    factory_app = FastAPI(
        title="Playground API",
        version="2.0.0",
        description=(
            "Monitor API for the Ukrainian curriculum pipeline. "
            "Powers the ukraine-ops dashboards (root /), agent cold-start (orient, rules, session), "
            "state queries, comms, delegate, build events, and operational tooling. "
            "Interactive explorer: /docs (Swagger) and /redoc. "
            "Machine-readable route contracts: /api/contracts/routes. "
            "See docs/MONITOR-API.md for the full reference."
        ),
        lifespan=factory_lifespan,
    )
    factory_app.state.ctx = context
    factory_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    factory_app.middleware("http")(resilience_middleware)
    factory_app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    factory_app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    factory_app.add_exception_handler(Exception, global_exception_handler)

    # Mount team routers in the established order. The core router must remain
    # last so its catch-all route keeps today's matching precedence.
    factory_app.include_router(admin_router, prefix="/api/admin")
    factory_app.include_router(agent_router, prefix="/api/agent", tags=["agent"])
    factory_app.include_router(agent_monitor_router, prefix="/api/agent-monitor")
    factory_app.include_router(artifacts_router, prefix="/api/artifacts", tags=["artifacts"])
    factory_app.include_router(atlas_jobs_router, prefix="/api/atlas-jobs", tags=["atlas-jobs"])
    factory_app.include_router(occupancy_router, prefix="/api/occupancy", tags=["occupancy"])
    factory_app.include_router(observer_presence_router, prefix="/api/observer", tags=["observer"])
    factory_app.include_router(epics_router, prefix="/api/epics", tags=["epics"])
    factory_app.include_router(blue_router, prefix="/api/blue")
    factory_app.include_router(comms_router, prefix="/api/comms")
    factory_app.include_router(fleet_router, prefix="/api/fleet", tags=["fleet"])
    factory_app.include_router(project_state_router, prefix="/api/fleet", tags=["fleet"])
    factory_app.include_router(fleet_workers_router, prefix="/api/fleet", tags=["fleet"])
    factory_app.include_router(session_streams_router, prefix="/api/session-streams", tags=["session-streams"])
    factory_app.include_router(coordination_router, prefix="/api/coordination")
    factory_app.include_router(consultation_router, prefix="/api/consultation")
    factory_app.include_router(cluster_router, prefix="/api/cluster", tags=["cluster"])
    factory_app.include_router(cost_router, prefix="/api/cost")
    factory_app.include_router(cost_router, prefix="/api/analytics/cost")
    factory_app.include_router(contracts_router, prefix="/api/contracts", tags=["contracts"])
    factory_app.include_router(dashboard_router, prefix="/api/dashboard")
    factory_app.include_router(decisions_router, prefix="/api/decisions", tags=["decisions"])
    factory_app.include_router(delegate_router, prefix="/api/delegate")
    factory_app.include_router(docs_router, prefix="/artifacts")
    factory_app.include_router(docs_router, prefix="/files")
    factory_app.include_router(discussions_router, prefix="/api/discussions", tags=["discussions"])
    factory_app.include_router(git_hygiene_router, prefix="/api/git", tags=["git"])
    factory_app.include_router(ops_router, prefix="/api/ops", tags=["ops"])
    factory_app.include_router(gold_router, prefix="/api/gold")
    factory_app.include_router(governance_router, prefix="/api/state/governance", tags=["governance"])
    factory_app.include_router(hermes_cron_router, prefix="/api/hermes-cron", tags=["hermes-cron"])
    factory_app.include_router(build_events_router, prefix="/api/build/events")
    factory_app.include_router(images_router, prefix="/api/images")
    factory_app.include_router(issues_router, prefix="/api/issues", tags=["issues"])
    factory_app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])
    factory_app.include_router(sources_router, prefix="/api/sources", tags=["sources"])
    factory_app.include_router(sources_router, prefix="/api/rag", tags=["rag"], deprecated=True)
    # GH #1529 P3 — reviewer-ghost telemetry nested under /api/state so clients
    # can discover it alongside the other state-query endpoints.
    factory_app.include_router(
        reviewer_ghosts_router,
        prefix="/api/state/reviewer-ghosts",
        tags=["reviewer-ghosts"],
    )
    factory_app.include_router(rollover_router, prefix="/api/rollovers", tags=["rollovers"])
    factory_app.include_router(rules_router, prefix="/api/rules", tags=["rules"])
    factory_app.include_router(runtime_router, prefix="/api/runtime")
    factory_app.include_router(session_router, prefix="/api/session", tags=["session"])
    factory_app.include_router(site_router, prefix="/api/site", tags=["site"])
    factory_app.include_router(state_router, prefix="/api/state")
    factory_app.include_router(telemetry_router)
    factory_app.include_router(wiki_router, prefix="/api/wiki", tags=["wiki"])
    factory_app.include_router(worktrees_router, prefix="/api/worktrees", tags=["worktrees"])
    factory_app.include_router(work_router, prefix="/api/work", tags=["work"])
    factory_app.include_router(core_router)
    return factory_app


app = create_app(production_context())
