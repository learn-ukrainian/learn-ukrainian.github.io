"""
FastAPI server for playground dashboards.

Architecture:
  - main.py: shared endpoints (config, static files, health, orient)
  - batch_router.py: batch state, dispatcher, and websocket
"""

import asyncio
import functools
import json
import logging
import os
import re
import socket
import subprocess
import threading
import time
import uuid
from collections.abc import Awaitable, Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from prometheus_client import CollectorRegistry, Counter, Histogram, make_asgi_app
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

import scripts.github_rest_cache as github_rest
from scripts.common.jsonl import physical_lines
from scripts.common.release_layout import is_release_root
from scripts.control_plane.storage import StoreId, assert_component_supported
from scripts.github_check_rollup import group_collapsed_by_name
from scripts.guardrails import worktree_containment
from scripts.orientation_packet import PACKET_MAX_BYTES, cap_response, json_bytes
from scripts.research import registry as reg

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

from scripts.orchestration import issue_stream_audit as isa

from . import delegate_router as delegate_api
from . import runtime_router as runtime_api
from . import state_router as state_api
from ._signal_log import install_signal_logging
from .agent_monitor_router import router as agent_monitor_router
from .cluster_router import router as cluster_router
from .codexbar_usage import scheduler_status, start_periodic_refresh, stop_periodic_refresh
from .comms_router import ensure_broker_db_ready
from .comms_router import router as comms_router
from .coordination_router import router as coordination_router
from .delegate_router import router as delegate_router
from .discussions_router import router as discussions_router
from .docs_router import router as docs_router
from .epics_router import router as epics_router
from .epics_router import seed_manifest_inventory
from .fleet_board.router import router as fleet_board_router
from .fleet_router import router as fleet_router
from .fleet_workers_router import router as fleet_workers_router
from .git_hygiene_router import router as git_hygiene_router
from .issues_router import router as issues_router
from .knowledge_router import router as knowledge_router
from .monitor_context import MonitorContext, get_ctx, production_context, resolve_context
from .observer_presence import router as observer_presence_router
from .occupancy import router as occupancy_router
from .occupancy_local import resolve_launcher_host_id
from .ops_router import router as ops_router
from .opsec_sanitize import opsec_path_sanitizer_middleware
from .preload import preload_all
from .product_contribution import OrientSection, ProductContribution, install_providers, load_product
from .project_state_router import router as project_state_router
from .repository_authority import build_repository_authority, cwd_role
from .resilience import get_resilience_snapshot, resilience_middleware
from .rollover_router import collect_rollover_orient_data
from .rollover_router import router as rollover_router
from .route_contracts import router as contracts_router
from .rules_router import router as rules_router
from .runtime_router import router as runtime_router
from .session_router import router as session_router
from .session_streams_router import router as session_streams_router
from .state_helpers import cache_get, cache_invalidate, cache_set, ctx_cache_scope
from .state_router import router as state_router
from .state_router import schedule_state_scan_warmup
from .telemetry.response import add_json_telemetry, session_id_from_request
from .telemetry_router import router as telemetry_router
from .work_router import drain_context_background_work, refresh_projection_cache_periodically, warm_projection_cache
from .work_router import router as work_router
from .worktrees_router import router as worktrees_router

# Read-only Git children (status refreshing the index) must never take
# index.lock: a request killed mid-call would leave it behind (#8874). Every
# child inherits this; an explicit operator value wins.
os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")

core_router = APIRouter()


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Lifespan hook — wrap uvicorn signal handlers so we record WHO killed us.

    Without this, "Shutting down" lines in logs/api.log have no provenance.
    See scripts/api/_signal_log.py for the wrapper rationale.

    Startup uses the authority-service interlock. An authority that component
    cannot write refuses startup, so plane-status cannot report a store the
    seats do not write. Sqlite and shadow stay allowed.
    """
    ctx = _app.state.ctx
    product: ProductContribution = _app.state.product
    projection_refresh_task = None
    try:
        # Reuse assert_component_supported; do not add a second allow-list.
        # ControlPlaneUnsupportedComponentError names the store and authority
        # and carries no connection string.
        assert_component_supported(StoreId.FLEET_COMMS, "authority_service")
        preload_all(product.preload, product.preload_optional)
        install_signal_logging()
        ensure_broker_db_ready(ctx=ctx)
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
        try:
            schedule_state_scan_warmup(ctx, product.warmup)
        except Exception as exc:
            logger.warning("State scan warmup schedule on startup failed: %s", exc)
        projection_refresh_task = asyncio.create_task(
            refresh_projection_cache_periodically(ctx), name="work-projection-refresh"
        )
        start_periodic_refresh()
        yield
    finally:
        if projection_refresh_task is not None:
            projection_refresh_task.cancel()
            with suppress(asyncio.CancelledError):
                await projection_refresh_task
        try:
            stop_periodic_refresh()
        finally:
            try:
                await drain_context_background_work(ctx)
            finally:
                await ctx.runtime.close_resources()


def _error_envelope(
    error: str, detail: Any, *, status_code: int, headers: dict[str, str] | None = None, bounded: bool = False
) -> JSONResponse:
    """Build the public error shape without serializing exception text.

    Route-specific ``HTTPException`` details remain available when they are
    already structured or short, stable API messages. Unhandled exceptions
    never pass their ``str(exc)`` representation to a client; the correlation
    id is the only diagnostic handle exposed on the wire.
    """
    content = {"error": error, "error_id": uuid.uuid4().hex, "detail": detail}
    if bounded:
        content = cap_response(content, locator="/api/work/v1/projection")
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content=content,
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
    return _error_envelope(
        "http_error",
        _sanitize_public_detail(exc.detail),
        status_code=exc.status_code,
        headers=exc.headers,
        bounded=request.url.path == "/api/work/v1/projection",
    )


async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return validation shape without echoing submitted values."""
    sanitized_errors = []
    for error in exc.errors():
        sanitized = {key: _sanitize_public_detail(value) for key, value in error.items() if key not in {"ctx", "input"}}
        sanitized_errors.append(sanitized)
    return _error_envelope(
        "validation_error", sanitized_errors, status_code=422, bounded=request.url.path == "/api/work/v1/projection"
    )


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
#   - ``runtime``, ``wiki``, ``session_hints``
#                            — pure-Python / filesystem, no inner
#                              timeout; they rely on being cheap.
#   - ``idle_prs``           — cache-first detached worker; ``gh`` never runs
#                              in the request path.
#   - ``capacity``, ``health`` — cache-first detached worker (#6983); CodexBar
#                              / canaries never pin the lean gather.
#   - ``delegate``, ``rollovers`` — cache-first detached worker (#10866); a hung
#                              collector must not pin the lean gather.
# If a sync collector ever starts to block (e.g. a network FS hang), it
# will tie up a threadpool slot past the hard timeout. See
# MONITOR-API.md for the full breakdown.
ORIENT_SECTION_TTLS: dict[str, float] = {
    "git": 30.0,
    "issues": 120.0,
    "idle_prs": 60.0,
    "runtime": 60.0,
    "delegate": 30.0,
    "capacity": 15.0,
    "bridge_pending": 15.0,
    "rollovers": 15.0,
    "health": 15.0,
    "session_hints": 60.0,
}

ORIENT_SECTION_SOURCES: dict[str, str] = {
    "git": "git",
    "issues": "gh",
    "idle_prs": "gh",
    "runtime": "fs",
    "delegate": "fs",
    "capacity": "fs",
    "bridge_pending": "sqlite",
    "rollovers": "fs",
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

# Machinery sections only. The product contribution adds pipeline, wiki and
# governance (``ProductContribution.orient_sections``); ``_orient_layout``
# composes both in the response order the endpoint always had. Pipeline has
# TTL 0 on purpose: its collector wraps ``/api/state/summary``, which has its
# own 60 s cache, and stacking both labelled up-to-119 s old data as fresh
# (reviewer BLOCKER #1309 / B2).
ORIENT_SECTION_KEYS: tuple[str, ...] = tuple(ORIENT_SECTION_TTLS.keys())

# Lean cold-start preset (``?lean=true``): the small, lane-agnostic sections an agent needs to
# orient BEFORE it has selected work — tree state (git), active dispatches (delegate), pending
# bridge asks, blocking decisions (governance), health, and the handoff pointers / current goal
# (session_hints). Excludes the three heavy sections — ``pipeline`` (~2k module stats),
# ``issues`` (full gh list), ``wiki`` (per-track coverage) — which are fetched on demand via
# ``?sections=...``. ``capacity``, ``health``, ``delegate``, and ``rollovers`` stay in the
# preset but are cache-first / detached so a hung collector cannot pin the gather at 5 s
# (#6983, #10866).
LEAN_ORIENT_SECTIONS: tuple[str, ...] = (
    "git",
    "runtime",
    "delegate",
    "capacity",
    "bridge_pending",
    "rollovers",
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

# Lean ``capacity``, ``health``, ``delegate``, and ``rollovers`` are cache-first
# and detached: CodexBar, integrity canaries, and hung delegate/rollover
# collectors must not pin ``asyncio.gather`` at the 5 s section wall
# (#6983, #10866). A short join lets cheap (test) collectors populate the
# same request; a live hang returns fallback immediately after this wait.
DETACHED_ORIENT_SECTION_KEYS: frozenset[str] = frozenset({"capacity", "health", "delegate", "rollovers"})
DETACHED_ORIENT_INLINE_WAIT_S = 0.4
_detached_orient_lock = threading.Lock()
_detached_orient_threads: dict[str, threading.Thread] = {}
_detached_orient_last_good: dict[str, tuple[Any, str]] = {}
_detached_orient_last_error: dict[str, str] = {}

# The idle-PR feed is deliberately cache-first. A live GitHub request is run by
# one detached daemon worker, never by the ASGI request path. The last successful
# result remains available as a stale fallback when GitHub is slow or unavailable.
_idle_pr_refresh_lock = threading.Lock()
_idle_pr_refresh_threads: dict[str, threading.Thread] = {}
_idle_pr_last_good: dict[str, tuple[dict[str, Any], str]] = {}
_idle_pr_last_error: dict[str, str] = {}
_idle_pr_next_retry_at: dict[str, float] = {}


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


def _run_command(
    args: list[str], *, timeout: float = 2.0, ctx: MonitorContext | None = None
) -> subprocess.CompletedProcess[str]:
    resolved_ctx = resolve_context(ctx)
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
    except (FileNotFoundError, OSError, AssertionError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(args=args, returncode=127, stdout="", stderr=str(exc))


def _collect_git_orient_data(ctx: MonitorContext | None = None) -> dict:
    resolved_ctx = resolve_context(ctx)
    branch_proc = _run_command(["git", "--no-optional-locks", "branch", "--show-current"], ctx=ctx)
    head_proc = _run_command(["git", "--no-optional-locks", "rev-parse", "--short=9", "HEAD"], ctx=ctx)
    full_head_proc = _run_command(["git", "--no-optional-locks", "rev-parse", "HEAD"], ctx=ctx)
    ahead_proc = _run_command(["git", "--no-optional-locks", "rev-list", "--count", "origin/main..HEAD"], ctx=ctx)
    log_proc = _run_command(["git", "--no-optional-locks", "log", "--oneline", "-5"], ctx=ctx)

    if branch_proc.returncode != 0:
        raise RuntimeError(branch_proc.stderr.strip() or "git branch failed")
    if head_proc.returncode != 0:
        raise RuntimeError(head_proc.stderr.strip() or "git rev-parse failed")
    if log_proc.returncode != 0:
        raise RuntimeError(log_proc.stderr.strip() or "git log failed")

    recent_commits = []
    # One ``--oneline`` record per physical line; a subject may contain NEL/LS/PS.
    for line in physical_lines(log_proc.stdout):
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
    """Fetch open GitHub issues via conditional REST.

    Raises ``RuntimeError`` on any failure. Raising is important —
    ``_cached_orient_section`` only caches successful returns, so a
    transient GitHub blip must not poison the issues cache for the full
    TTL window (reviewer BLOCKER, GH #1309). Timeouts surface as
    ``RuntimeError`` the same way a failed ``gh`` subprocess did.
    """
    issue_limit = 10
    try:
        payload = github_rest.list_open_issues(IDLE_PR_REPOSITORY, limit=issue_limit, timeout=5.0)
    except github_rest.GitHubRestTimeout as exc:
        raise RuntimeError(str(exc)) from exc
    except github_rest.GitHubRestError as exc:
        raise RuntimeError(str(exc)) from exc
    if getattr(payload, "truncated", False) and len(payload) < issue_limit:
        raise RuntimeError("GitHub issue list truncated")

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


def _idle_check_row_green(check: dict[str, Any]) -> bool:
    status = str(check.get("status") or "").upper()
    if status and status not in {"COMPLETED", "SUCCESS"}:
        return False
    outcome = str(check.get("conclusion") or check.get("state") or "").upper()
    return outcome in IDLE_PR_SUCCESSFUL_CONCLUSIONS


def _idle_pr_checks_green(pr: dict[str, Any]) -> bool:
    """Return whether every surviving non-advisory check for a PR is green.

    Historical runs collapse through :func:`group_collapsed_by_name`. A name
    stays red or pending when any surviving row is: a later success in another
    workflow does not hide an earlier failure, and a timestamp tie keeps both.
    Missing or malformed status data fails closed. Explicitly advisory checks
    follow the repository merge-hook convention and do not block eligibility.
    """
    rollup = pr.get("statusCheckRollup")
    if not isinstance(rollup, list) or not rollup:
        return False

    named, other = group_collapsed_by_name(rollup)
    if other or not named:
        return False

    blocking_count = 0
    for name, rows in named.items():
        if IDLE_PR_ADVISORY_MARKER in name.casefold():
            continue
        blocking_count += 1
        if any(not _idle_check_row_green(row) for row in rows):
            return False

    return blocking_count > 0


def _idle_pr_has_review_gate(pr: dict[str, Any]) -> bool:
    """Return whether a proven review decision or a review comment clears the gate.

    One GitHub ``APPROVED`` review is not enough. REST cannot see how many
    approvals branch protection requires, so eligibility needs ``reviewDecision``
    ``APPROVED`` (only when that state is known) or an explicit cross-family
    comment. A missing decision fails closed.
    """
    if str(pr.get("reviewDecision") or "").upper() == "APPROVED":
        return True

    head_sha = pr.get("headRefOid")
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
    itself uses ``_cached_idle_pr_section`` and never waits for GitHub.
    Check runs, reviews, and issue comments are conditional REST reads bounded
    by the open PR count. A timeout raises ``subprocess.TimeoutExpired`` so the
    worker reports ``gh_timeout``. Other failures raise ``RuntimeError`` and
    are not cached.
    """
    try:
        payload = github_rest.list_open_prs(
            IDLE_PR_REPOSITORY,
            limit=1000,
            timeout=IDLE_PR_FETCH_TIMEOUT_S,
            include_comments=True,
        )
    except github_rest.GitHubRestTimeout as exc:
        raise subprocess.TimeoutExpired(cmd=["gh", "api"], timeout=exc.timeout) from exc
    except github_rest.GitHubRestError as exc:
        raise RuntimeError(str(exc)) from exc
    if not isinstance(payload, list):
        raise RuntimeError("gh pr list returned a non-list payload")
    if getattr(payload, "truncated", False):
        raise RuntimeError("GitHub pull list truncated")

    now = datetime.now(UTC)
    rows = [row for item in payload if isinstance(item, dict) if (row := _eligible_idle_pr(item, now=now)) is not None]
    rows.sort(key=lambda row: (-row["minutes_idle"], row["number"]))
    return {"idle_prs": rows}


def _run_idle_pr_refresh(collector: Callable[[], Any], scope: str) -> None:
    try:
        value = collector()
        if not isinstance(value, dict) or not isinstance(value.get("idle_prs"), list):
            raise RuntimeError("idle PR collector returned an invalid payload")
    except subprocess.TimeoutExpired:
        _idle_pr_last_error[scope] = "gh_timeout"
        _idle_pr_next_retry_at[scope] = time.monotonic() + 30.0
        return
    except Exception:
        _idle_pr_last_error[scope] = "gh_unavailable"
        _idle_pr_next_retry_at[scope] = time.monotonic() + 30.0
        return

    generated_at = _isoformat_z(datetime.now(UTC))
    cache_set(f"{IDLE_PR_CACHE_KEY}{scope}", (value, generated_at))
    _idle_pr_last_good[scope] = (value, generated_at)
    _idle_pr_last_error.pop(scope, None)
    _idle_pr_next_retry_at[scope] = 0.0


def _schedule_idle_pr_refresh(collector: Callable[[], Any], scope: str) -> None:
    if time.monotonic() < _idle_pr_next_retry_at.get(scope, 0.0):
        return
    with _idle_pr_refresh_lock:
        thread = _idle_pr_refresh_threads.get(scope)
        if thread is not None and thread.is_alive():
            return
        worker = threading.Thread(
            target=_run_idle_pr_refresh,
            args=(collector, scope),
            daemon=True,
            name="orient-idle-pr-refresh",
        )
        _idle_pr_refresh_threads[scope] = worker
        worker.start()


def _cached_idle_pr_section(
    collector: Callable[..., Any],
    fallback: dict[str, Any],
    *,
    ctx: MonitorContext | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ttl = ORIENT_SECTION_TTLS["idle_prs"]
    scope = _ctx_cache_scope(ctx)
    collector = functools.partial(collector, ctx)
    cached = cache_get(f"{IDLE_PR_CACHE_KEY}{scope}", ttl=ttl)
    if isinstance(cached, tuple) and len(cached) == 2:
        value, generated_at = cached
        if isinstance(value, dict) and isinstance(generated_at, str):
            return value, {
                "generated_at": generated_at,
                "stale_after_s": ttl,
                "source": "gh",
                "cache": "hit",
            }

    _schedule_idle_pr_refresh(collector, scope)
    scoped_last_good = _idle_pr_last_good.get(scope)
    if scoped_last_good is not None:
        value, generated_at = scoped_last_good
        meta: dict[str, Any] = {
            "generated_at": generated_at,
            "stale_after_s": ttl,
            "source": "gh",
            "cache": "miss",
            "stale": True,
            "refreshing": (_t := _idle_pr_refresh_threads.get(scope)) is not None and _t.is_alive(),
        }
        if (_err := _idle_pr_last_error.get(scope)) is not None:
            meta["error"] = _err
        return value, meta

    meta = {
        "generated_at": _isoformat_z(datetime.now(UTC)),
        "stale_after_s": ttl,
        "source": "gh",
        "cache": "miss",
        "refreshing": (_t := _idle_pr_refresh_threads.get(scope)) is not None and _t.is_alive(),
    }
    if (_err := _idle_pr_last_error.get(scope)) is not None:
        meta["error"] = _err
    return fallback, meta


def reset_detached_orient_state_for_tests() -> None:
    """Drop detached-orient last-good so tests do not leak across cases."""
    with _detached_orient_lock:
        threads = list(_detached_orient_threads.values())
    for thread in threads:
        thread.join(timeout=2.0)
    with _detached_orient_lock:
        _detached_orient_threads.clear()
    _detached_orient_last_good.clear()
    _detached_orient_last_error.clear()


def _schedule_detached_orient_refresh(key: str, collector: Callable[[], Any], cache_key: str | None = None) -> bool:
    """Start a single-flight worker for ``key``. Return True if this call started it."""
    with _detached_orient_lock:
        state_key = cache_key or f"orient_{key}"
        thread = _detached_orient_threads.get(state_key)
        if thread is not None and thread.is_alive():
            return False
        worker = threading.Thread(
            target=_run_detached_orient_refresh,
            args=(key, collector, state_key),
            daemon=True,
            name=f"orient-{key}-refresh",
        )
        _detached_orient_threads[state_key] = worker
        worker.start()
        return True


def _run_detached_orient_refresh(key: str, collector: Callable[[], Any], cache_key: str) -> None:
    ttl = ORIENT_SECTION_TTLS.get(key, 60.0)
    try:
        value = collector()
        generated_at = _isoformat_z(datetime.now(UTC))
        if ttl > 0:
            cache_set(cache_key, (value, generated_at))
        _detached_orient_last_good[cache_key] = (value, generated_at)
        _detached_orient_last_error.pop(cache_key, None)
    except Exception as exc:
        _detached_orient_last_error[cache_key] = str(exc)


async def _cached_detached_orient_section(
    key: str,
    collector: Callable[..., Any],
    fallback: Any,
    *,
    ctx: MonitorContext | None = None,
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
    collector = functools.partial(collector, ctx)
    cache_key = f"orient_{key}{_ctx_cache_scope(ctx)}"
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

    started = _schedule_detached_orient_refresh(key, collector, cache_key)
    thread = _detached_orient_threads.get(cache_key)
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

    last_good = _detached_orient_last_good.get(cache_key)
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
        last_error = _detached_orient_last_error.get(cache_key)
        if last_error is not None:
            meta["error"] = last_error
        return value, meta

    short_err = _detached_orient_last_error.get(cache_key) or "refreshing"
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


def _collect_runtime_orient_data(ctx: MonitorContext | None = None) -> dict:
    resolved = resolve_context(ctx)
    # One shared counter across every usage read this section makes — agent
    # inventory (last-used models), the day usage summary, today's outcome
    # counts, and the per-agent headroom scan — so corrupt usage evidence is
    # surfaced on the runtime section instead of discarded (#9924).
    unreadable: dict[str, int] = {"files": 0, "lines": 0, "records": 0}
    agents = runtime_api.list_runtime_agents(ctx=resolved, unreadable=unreadable)
    usage = runtime_api.summarize_runtime_usage(days=1, ctx=resolved, unreadable=unreadable)
    recent = runtime_api.runtime_recent_outcomes_today(ctx=resolved, unreadable=unreadable)
    headroom = {}
    for agent_info in agents:
        name = agent_info.get("name")
        model = agent_info.get("default_model")
        if not name or not model:
            continue
        try:
            ok, _ = runtime_api.has_headroom(str(name), str(model), unreadable=unreadable)
        except Exception:
            ok = False
        headroom[str(name)] = ok

    by_agent = usage.get("by_agent", {})

    return {
        "agents": [agent["name"] for agent in agents if agent.get("name")],
        "recent_outcomes": recent,
        "by_agent": by_agent,
        "headroom": headroom,
        "unreadable": runtime_api._unreadable_summary(unreadable),
    }


def _collect_delegate_orient_data(ctx: MonitorContext | None = None) -> dict:
    resolved_ctx = resolve_context(ctx)
    recent = delegate_api.list_delegate_tasks(status="all", limit=5, ctx=resolved_ctx)
    active = delegate_api.active_delegate_count(ctx=resolved_ctx)
    return {
        "active_count": active,
        "recent": recent["tasks"],
    }


def _collect_capacity_orient_data(ctx: MonitorContext | None = None) -> dict:
    resolved_ctx = resolve_context(ctx)
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
    resolve_context(ctx)
    from scripts.ai_agent_bridge import _channels  # noqa: PLC0415 — optional broker bridge

    return _channels.bridge_pending_summary()


def _collect_rollovers_orient_data(ctx: MonitorContext | None = None) -> dict:
    resolved_ctx = resolve_context(ctx)
    return collect_rollover_orient_data(live_repo_root=resolved_ctx.roots.live_repo_root)


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
    resolved_ctx = resolve_context(ctx)
    try:
        from scripts.hygiene.check_core_bare import check_core_bare  # noqa: PLC0415 — script-path fallback
    except ImportError:  # path-flavoured import for test/script contexts
        from hygiene.check_core_bare import check_core_bare  # noqa: PLC0415 — script-path fallback
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
    resolved_ctx = resolve_context(ctx)
    try:
        from scripts.hygiene.check_self_symlinks import check_self_symlinks  # noqa: PLC0415 — script-path fallback
    except ImportError:  # path-flavoured import for test/script contexts
        from hygiene.check_self_symlinks import check_self_symlinks  # noqa: PLC0415 — script-path fallback
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
    resolved_ctx = resolve_context(ctx)
    try:
        from scripts.hygiene.check_primary_integrity import (  # noqa: PLC0415 — script-path fallback
            check_primary_integrity,
        )
    except ImportError:  # path-flavoured import for test/script contexts
        from hygiene.check_primary_integrity import check_primary_integrity  # noqa: PLC0415 — script-path fallback
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

    #6818 follow-up: sharing the primary's `node_modules`/`site/node_modules`
    with dispatch worktrees lets worktree writes reach the primary's real
    files (#6805 incident). ALERT-only, same posture as
    `_primary_integrity_canary` — detects and records, never repairs. Never
    raises: the canary must not break health collection.
    """
    resolved_ctx = resolve_context(ctx)
    try:
        from scripts.hygiene.check_node_modules_integrity import (  # noqa: PLC0415 — script-path fallback
            check_node_modules_integrity,
        )
    except ImportError:  # path-flavoured import for test/script contexts
        from hygiene.check_node_modules_integrity import (  # noqa: PLC0415 — script-path fallback
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
    resolved_ctx = resolve_context(ctx)
    try:
        from scripts.hygiene.check_venv_integrity import check_venv_integrity  # noqa: PLC0415 — script-path fallback
    except ImportError:  # path-flavoured import for test/script contexts
        from hygiene.check_venv_integrity import check_venv_integrity  # noqa: PLC0415 — script-path fallback
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
    resolved_ctx = resolve_context(ctx)
    try:
        from scripts.hygiene.check_worktree_cleanup_integrity import (  # noqa: PLC0415 — script-path fallback
            check_worktree_cleanup_integrity,
        )
    except ImportError:  # path-flavoured import for test/script contexts
        from hygiene.check_worktree_cleanup_integrity import (  # noqa: PLC0415 — script-path fallback
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
        from scripts.hygiene.check_tmp_usability import probe_tmp_usability  # noqa: PLC0415 — script-path fallback
    except ImportError:  # path-flavoured import for test/script contexts
        from hygiene.check_tmp_usability import probe_tmp_usability  # noqa: PLC0415 — script-path fallback
    try:
        return probe_tmp_usability()
    except Exception:
        logger.exception("tmp-usability canary (#7164) failed to run")
        # fail-open: don't raise a false alarm on canary error
        return {"ok": True, "writable": True, "error": None, "probe_error": True}


def _backup_last_run_health(batch_state_dir: Path, *, now: datetime | None = None) -> dict[str, Any]:
    receipt = batch_state_dir / "backups" / "last-run.json"
    try:
        data = json.loads(receipt.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"status": "unknown", "reason": "no_receipt"}
    except (OSError, ValueError):
        return {"status": "unknown", "reason": "unreadable_receipt"}
    if not isinstance(data, dict) or type(data.get("exit_status")) is not int:
        return {"status": "unknown", "reason": "invalid_receipt"}
    finished = data.get("finished_at_utc")
    if not isinstance(finished, str):
        return {"status": "unknown", "reason": "invalid_receipt"}
    try:
        finished_at = datetime.fromisoformat(finished.replace("Z", "+00:00"))
    except ValueError:
        return {"status": "unknown", "reason": "invalid_receipt"}
    if finished_at.tzinfo is None:
        return {"status": "unknown", "reason": "invalid_receipt"}
    current = now or datetime.now(UTC)
    status = "failed" if data["exit_status"] != 0 else "ok"
    if status == "ok" and current - finished_at > timedelta(hours=26):
        status = "stale"
    return {
        "status": status,
        "exit_status": data["exit_status"],
        "finished_at_utc": finished,
    }


def _collect_health_orient_data(
    ctx: MonitorContext | None = None,
    product_health: Callable[[MonitorContext], Mapping[str, Any]] | None = None,
) -> dict:
    resolved_ctx = resolve_context(ctx)
    mcp_sources_ok = _port_open("127.0.0.1", 8766, 0.2)
    tmp_usability = _tmp_usability_canary()
    core_bare_ok = _core_bare_canary(ctx=resolved_ctx)
    self_symlink_ok = _self_symlink_canary(ctx=resolved_ctx)
    primary_integrity_ok = _primary_integrity_canary(ctx=resolved_ctx)
    node_modules_integrity_ok = _node_modules_integrity_canary(ctx=resolved_ctx)
    venv_integrity_ok = _venv_integrity_canary(ctx=resolved_ctx)
    worktree_cleanup_integrity_ok = _worktree_cleanup_integrity_canary(ctx=resolved_ctx)
    fields: dict[str, Any] = {
        "api": True,
        "mcp_sources": mcp_sources_ok,
        "mcp_rag": mcp_sources_ok,
    }
    if product_health is not None:
        fields.update(product_health(resolved_ctx))
    return {
        **fields,
        "message_broker": _readable_file(resolved_ctx.roots.message_db_path),
        "git_core_bare_ok": core_bare_ok,
        "node_modules_symlinks_ok": self_symlink_ok,
        "primary_integrity_ok": primary_integrity_ok,
        "node_modules_integrity_ok": node_modules_integrity_ok,
        "venv_integrity_ok": venv_integrity_ok,
        "worktree_cleanup_integrity_ok": worktree_cleanup_integrity_ok,
        "tmp_usability_ok": bool(tmp_usability.get("ok")),
        "tmp_usability": tmp_usability,
        "backup_last_run": _backup_last_run_health(resolved_ctx.roots.batch_state_dir),
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
    resolved_ctx = resolve_context(ctx)
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
    resolved_ctx = resolve_context(ctx)
    host_label = resolve_launcher_host_id()
    head_proc = _run_command(["git", "--no-optional-locks", "rev-parse", "HEAD"], ctx=ctx)
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


def _ctx_cache_scope(ctx: MonitorContext | None) -> str:
    """Cache-key scope for one app context (#7494 / design goal 4.4).

    Two app instances with different roots must never share orient cache
    entries; the project root is the identity that matters.
    """
    return ctx_cache_scope(ctx)


async def _cached_orient_section(
    key: str,
    collector: Callable[..., Any] | Callable[..., Awaitable[Any]],
    fallback: Any,
    *,
    is_async: bool = False,
    ctx: MonitorContext | None = None,
    ttl: float | None = None,
    source: str | None = None,
) -> tuple[Any, dict]:
    """Run one orient collector with TTL cache + hard timeout + fallback.

    Returns (value, meta). Meta always includes ``generated_at``,
    ``stale_after_s``, ``source``, and ``cache`` ("hit" / "miss"); it
    adds ``error`` on failure so callers can tell a populated section
    from a degraded one.

    Errors are NOT cached — the next call retries. This is intentional:
    a transient git/gh hiccup shouldn't poison a 2-minute TTL window.

    ``ttl`` and ``source`` come from a product section; a machinery section
    takes them from ``ORIENT_SECTION_TTLS`` and ``ORIENT_SECTION_SOURCES``.
    """
    if key == "idle_prs":
        return _cached_idle_pr_section(collector, fallback, ctx=ctx)  # type: ignore[arg-type]
    if key in DETACHED_ORIENT_SECTION_KEYS:
        return await _cached_detached_orient_section(key, collector, fallback, ctx=ctx)  # type: ignore[arg-type]

    ttl = ORIENT_SECTION_TTLS.get(key, 60.0) if ttl is None else ttl
    source = ORIENT_SECTION_SOURCES.get(key, "fs") if source is None else source
    cache_key = f"orient_{key}{_ctx_cache_scope(ctx)}"

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
                collector(ctx),  # type: ignore[misc]
                timeout=ORIENT_SECTION_HARD_TIMEOUT_S,
            )
        else:
            loop = asyncio.get_running_loop()
            value = await asyncio.wait_for(
                loop.run_in_executor(
                    _ORIENT_SYNC_EXECUTOR,
                    functools.partial(collector, ctx),  # type: ignore[arg-type]
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


@dataclass(frozen=True)
class OrientLayout:
    """The orient sections of one app: machinery sections plus the product's, in response order."""

    keys: tuple[str, ...]
    lean: tuple[str, ...]
    specs: Mapping[str, tuple[Callable[..., Any], Any, bool]]
    product: Mapping[str, OrientSection]


def _orient_layout(product: ProductContribution) -> OrientLayout:
    """Compose the machinery sections with the product's at their ``after`` anchors."""
    specs: dict[str, tuple[Callable[..., Any], Any, bool]] = dict(_orient_section_specs(product))
    sections = dict(product.orient_sections())
    keys = list(ORIENT_SECTION_KEYS)
    pending = dict(sections)
    while pending:
        placed = [key for key, section in pending.items() if section.after in keys]
        if not placed:
            raise RuntimeError(f"orient sections with unknown anchors: {sorted(pending)}")
        for key in placed:
            section = pending.pop(key)
            keys.insert(keys.index(section.after) + 1, key)
            specs[key] = (section.collector, section.fallback, section.is_async)
    lean_keys = set(LEAN_ORIENT_SECTIONS) | {key for key, section in sections.items() if section.lean}
    lean = tuple(key for key in keys if key in lean_keys)
    return OrientLayout(tuple(keys), lean, specs, sections)


def _parse_orient_sections(sections_param: str | None, *, lean: bool = False, layout: OrientLayout) -> list[str]:
    """Validate and expand the optional ``sections`` query param.

    An explicit ``sections`` list always wins. When it is absent, ``lean`` selects the
    lightweight cold-start preset (``layout.lean``); otherwise the full payload.
    """
    default = list(layout.lean if lean else layout.keys)
    if sections_param is None:
        return default
    keys = [part.strip() for part in sections_param.split(",") if part.strip()]
    if not keys:
        return default
    unknown = [key for key in keys if key not in layout.specs]
    if unknown:
        valid = ", ".join(layout.keys)
        raise HTTPException(
            status_code=400,
            detail=f"Unknown orient section(s): {', '.join(unknown)}. Valid keys: {valid}",
        )
    return keys


def _orient_section_specs(product: ProductContribution) -> dict[str, tuple[Callable[..., Any], Any, bool]]:
    """Return machinery orient collector specs using live module attributes (test-friendly)."""
    health = (
        _collect_health_orient_data
        if product.health is None
        else functools.partial(_collect_health_orient_data, product_health=product.health)
    )
    return {
        "git": (_collect_git_orient_data, {}, False),
        "issues": (_collect_issues_orient_data, {"issues": []}, False),
        "idle_prs": (_collect_idle_prs_orient_data, {"idle_prs": []}, False),
        "runtime": (_collect_runtime_orient_data, {}, False),
        "delegate": (_collect_delegate_orient_data, {"active_count": 0, "recent": []}, False),
        "capacity": (_collect_capacity_orient_data, {"lanes": {}}, False),
        "bridge_pending": (_collect_bridge_pending_orient_data, {}, False),
        "rollovers": (
            _collect_rollovers_orient_data,
            {"counts": {}, "actionable": [], "errors": []},
            False,
        ),
        "health": (health, {"api": True}, False),
        "session_hints": (_collect_session_hints_orient_data, [], False),
    }


def _cap_lean_orient(response: dict[str, Any]) -> dict[str, Any]:
    """Keep the lean preset inside the orientation byte bound.

    Sections and section metadata that do not fit become locators.
    ``generated_at`` stays. The full ``/api/orient`` payload is unchanged.
    """
    protected = {"generated_at", "meta", "_telemetry", "orientation_bound"}

    def size(body: dict[str, Any]) -> int:
        return len(json_bytes(body))

    if size(response) <= PACKET_MAX_BYTES:
        return response
    omitted: list[str] = []
    bound: dict[str, Any] = {
        "max_bytes": PACKET_MAX_BYTES,
        "complete": False,
        "omitted": {"count": 0, "locators": omitted},
    }
    response["orientation_bound"] = bound
    candidates = [(response, key) for key in response if key not in protected]
    meta = response.get("meta", {})
    candidates.extend((meta, key) for key in meta)
    while size(response) > PACKET_MAX_BYTES:
        if not candidates:
            break
        candidate = max(
            candidates,
            key=lambda item: len(json_bytes({item[1]: item[0][item[1]]})),
        )
        candidates.remove(candidate)
        container, key = candidate
        locator = f"GET /api/orient?sections={key}"
        section = container[key]
        stub: dict[str, Any] = {
            "omitted": True,
            "locator": locator,
            "bytes": len(json_bytes({key: section})),
        }
        if isinstance(section, dict):
            if isinstance(section.get("generated_at"), str):
                stub["generated_at"] = section["generated_at"]
            counts = section.get("counts")
            if isinstance(counts, dict) and len(json_bytes(counts)) <= 400:
                stub["counts"] = counts
        container[key] = stub
        if locator not in omitted:
            omitted.append(locator)
        bound["omitted"]["count"] = len(omitted)
    if size(response) > PACKET_MAX_BYTES:
        response.pop("orientation_bound", None)
        for key, value in list(response.items()):
            if key in {"generated_at", "meta", "_telemetry"} or not isinstance(value, dict):
                continue
            value.pop("counts", None)
    return response


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

    layout = _orient_layout(request.app.state.product)
    selected = _parse_orient_sections(sections, lean=lean, layout=layout)
    section_specs = layout.specs
    # #7494: thread THIS app's context into every collector — the zero-arg
    # invocation made all 14 collectors fall back to production_context(),
    # defeating create_app() isolation (and rebuilding contexts per call).
    request_ctx = get_ctx(request)
    gather_results = await asyncio.gather(
        *[
            _cached_orient_section(
                key,
                section_specs[key][0],
                section_specs[key][1],
                is_async=section_specs[key][2],
                ctx=request_ctx,
                ttl=layout.product[key].ttl_s if key in layout.product else None,
                source=layout.product[key].source if key in layout.product else None,
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

    for key in layout.keys:
        if key not in section_data:
            continue
        value = section_data[key]
        if key in ("issues", "idle_prs"):
            response[key] = value.get(key, []) if isinstance(value, dict) else []
        else:
            response[key] = value
        product_section = layout.product.get(key)
        if product_section is not None and product_section.merge_meta:
            section_metas[key] = {**section_metas[key], **value}

    if "issues" in section_data:
        issues_info = section_data["issues"]
        if isinstance(issues_info, dict) and issues_info.get("error"):
            response["issues_error"] = issues_info["error"]
    if "idle_prs" in section_data:
        idle_prs_info = section_data["idle_prs"]
        if isinstance(idle_prs_info, dict) and idle_prs_info.get("error"):
            response["idle_prs_error"] = idle_prs_info["error"]

    _attach_cold_start_research(response, role)
    body = add_json_telemetry(response, session_id=session_id_from_request(request))
    if lean and not (sections and sections.strip()):
        body = _cap_lean_orient(body)
    return body


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
        # Do not interpolate the role string — it is request-derived and would
        # reintroduce py/log-injection even after control-char scrubbing.
        logger.warning(
            "orient: cold-start research selector failed unexpectedly; omitting research section",
            exc_info=True,
        )
        response.pop("research", None)


# ==================== STATIC FILES (MUST BE LAST) ====================


def _safe_join(base: Path, *parts: str | Path) -> Path | None:
    try:
        return safe_join(base, *parts)
    except ValueError:
        return None


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


_HTTP_METHODS = frozenset({"DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"})


def _route_template(scope: Scope) -> str:
    """Return the matched route template, never the request path or query."""
    metrics_path = PrometheusMetricsMiddleware.METRICS_PATH
    if scope.get("method") == "GET" and scope.get("path") == metrics_path:
        return metrics_path
    route = scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path.startswith("/") and '"' not in path and "\n" not in path and "\r" not in path:
        return path
    return "unmatched"


def _status_class(status_code: int) -> str:
    hundred = status_code // 100
    if 1 <= hundred <= 5:
        return f"{hundred}xx"
    return "5xx"


def _scope_without_accept(scope: Scope) -> Scope:
    """Return a scope whose ``Accept`` header is absent.

    ``prometheus_client`` negotiates OpenMetrics or Prometheus text 1.0.0 from
    that header. With it removed, ``make_asgi_app`` stays on Prometheus text
    0.0.4 (``text/plain; version=0.0.4; charset=utf-8``).
    """
    headers = scope.get("headers")
    if not headers:
        return scope
    pinned = [header for header in headers if header[0].lower() != b"accept"]
    if len(pinned) == len(headers):
        return scope
    return {**scope, "headers": pinned}


class PrometheusMetricsMiddleware:
    """Record request totals, latency, and 5xx responses, and serve GET /metrics.

    Exposition is pinned to Prometheus text 0.0.4
    (``text/plain; version=0.0.4; charset=utf-8``). ``Accept`` is removed
    before ``prometheus_client.make_asgi_app`` builds the body, so every
    response uses that content type. Metric names, labels, and counting are
    unchanged. The process still binds the existing loopback listener; this
    adds no socket.

    ``METRICS_PATH`` is the path the route inventory records with FastAPI's
    framework routes. Those paths are served and are outside the OpenAPI
    operation count.
    """

    METRICS_PATH = "/metrics"

    def __init__(self, app: ASGIApp) -> None:
        registry = CollectorRegistry()
        self.app = app
        self._requests = Counter(
            "monitor_http_requests_total",
            "HTTP requests handled by the Monitor API.",
            labelnames=("method", "route", "status"),
            registry=registry,
        )
        self._errors = Counter(
            "monitor_http_responses_5xx_total",
            "HTTP responses whose status class is 5xx.",
            labelnames=("method", "route", "status"),
            registry=registry,
        )
        self._latency = Histogram(
            "monitor_http_request_duration_seconds",
            "HTTP request latency in seconds.",
            labelnames=("method", "route", "status"),
            registry=registry,
        )
        self._metrics_app = make_asgi_app(registry=registry, disable_compression=True)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
            await send(message)

        try:
            if scope.get("method") == "GET" and scope.get("path") == self.METRICS_PATH:
                await self._metrics_app(_scope_without_accept(scope), receive, send_wrapper)
            else:
                await self.app(scope, receive, send_wrapper)
        finally:
            self._record(scope, status_code, time.perf_counter() - started)

    def _record(self, scope: Scope, status_code: int, elapsed: float) -> None:
        method = scope.get("method")
        if method not in _HTTP_METHODS:
            method = "OTHER"
        status = _status_class(status_code)
        labels = {"method": method, "route": _route_template(scope), "status": status}
        self._requests.labels(**labels).inc()
        self._latency.labels(**labels).observe(max(elapsed, 0.0))
        if status == "5xx":
            self._errors.labels(**labels).inc()


def create_app(
    context: MonitorContext,
    *,
    lifespan: Any = None,
    product: ProductContribution | None = None,
) -> FastAPI:
    """Build a fresh Ops API app bound to one context.

    ``product`` is the product contribution; when omitted it is loaded through
    the configured product entry (``load_product``). Its routers are included
    ahead of the machinery routers and the core catch-all stays last.
    """
    factory_lifespan = _lifespan if lifespan is None else lifespan
    product = load_product(context) if product is None else product
    factory_app = FastAPI(
        title="Ops API",
        version="2.0.0",
        description=(
            "Operator API (Ops API) for the Ukrainian curriculum pipeline. "
            "Application version 2.0.0 (also on GET /api/health and /api/config). "
            "Stream key remains `monitor`; historic Monitor docs paths are progressive rename. "
            "Versioning layers: app 2.0.0 · URL namespaces `/api/*/v1/*` · "
            "payload `response_schema_version` / `schema_version` on contracts. "
            "Agent onboard: GET /api/rules, GET /api/orient?lean=true, "
            "GET /api/contracts/routes, then docs/MONITOR-API.md. "
            "Interactive explorer: /docs (Swagger) and /redoc. "
            "Powers ops dashboards (root /), cold-start, state, comms, delegate, "
            "build events, and operational tooling."
        ),
        lifespan=factory_lifespan,
    )
    factory_app.state.ctx = context
    factory_app.state.product = product
    install_providers(product)
    factory_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    factory_app.middleware("http")(resilience_middleware)
    factory_app.middleware("http")(opsec_path_sanitizer_middleware)
    factory_app.add_middleware(PrometheusMetricsMiddleware)
    factory_app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    factory_app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    factory_app.add_exception_handler(Exception, global_exception_handler)

    # Product routers first, then the machinery routers in their established
    # order. The core router must remain last so its catch-all route keeps
    # today's matching precedence.
    for mount in product.routers:
        factory_app.include_router(mount.router, prefix=mount.prefix, tags=list(mount.tags) or None)
    factory_app.include_router(agent_monitor_router, prefix="/api/agent-monitor")
    factory_app.include_router(occupancy_router, prefix="/api/occupancy", tags=["occupancy"])
    factory_app.include_router(observer_presence_router, prefix="/api/observer", tags=["observer"])
    factory_app.include_router(epics_router, prefix="/api/epics", tags=["epics"])
    factory_app.include_router(comms_router, prefix="/api/comms")
    factory_app.include_router(fleet_router, prefix="/api/fleet", tags=["fleet"])
    factory_app.include_router(project_state_router, prefix="/api/fleet", tags=["fleet"])
    factory_app.include_router(fleet_workers_router, prefix="/api/fleet", tags=["fleet"])
    factory_app.include_router(fleet_board_router, prefix="/api/fleet/v1", tags=["fleet-v1"])
    factory_app.include_router(session_streams_router, prefix="/api/session-streams", tags=["session-streams"])
    factory_app.include_router(coordination_router, prefix="/api/coordination")
    factory_app.include_router(cluster_router, prefix="/api/cluster", tags=["cluster"])
    factory_app.include_router(contracts_router, prefix="/api/contracts", tags=["contracts"])
    factory_app.include_router(delegate_router, prefix="/api/delegate")
    factory_app.include_router(docs_router, prefix="/artifacts")
    factory_app.include_router(docs_router, prefix="/files")
    factory_app.include_router(discussions_router, prefix="/api/discussions", tags=["discussions"])
    factory_app.include_router(git_hygiene_router, prefix="/api/git", tags=["git"])
    factory_app.include_router(ops_router, prefix="/api/ops", tags=["ops"])
    factory_app.include_router(issues_router, prefix="/api/issues", tags=["issues"])
    factory_app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])
    factory_app.include_router(rollover_router, prefix="/api/rollovers", tags=["rollovers"])
    factory_app.include_router(rules_router, prefix="/api/rules", tags=["rules"])
    factory_app.include_router(runtime_router, prefix="/api/runtime")
    factory_app.include_router(session_router, prefix="/api/session", tags=["session"])
    factory_app.include_router(state_router, prefix="/api/state")
    factory_app.include_router(telemetry_router)
    factory_app.include_router(worktrees_router, prefix="/api/worktrees", tags=["worktrees"])
    factory_app.include_router(work_router, prefix="/api/work", tags=["work"])
    factory_app.include_router(core_router)
    return factory_app


app = create_app(production_context())
