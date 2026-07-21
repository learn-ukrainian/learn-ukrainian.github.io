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
import socket
import subprocess
import threading
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from scripts.guardrails import worktree_containment
from scripts.research import registry as reg

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

from scripts.orchestration.reap_worktrees import primary_checkout_root, reap_worktrees

from . import delegate_router as delegate_api
from . import runtime_router as runtime_api
from . import state_router as state_api
from . import wiki_router as wiki_api
from ._signal_log import install_signal_logging
from .admin_router import router as admin_router
from .agent_router import router as agent_router
from .artifacts_router import router as artifacts_router
from .blue_router import router as blue_router
from .build_events_router import router as build_events_router
from .comms_router import ensure_broker_db_ready
from .comms_router import router as comms_router
from .config import (
    BATCH_STATE_DIR,
    CURRICULUM_ROOT,
    DASHBOARDS_DIR,
    LEVELS,
    LIVE_REPO_ROOT,
    MESSAGE_DB,
    PROJECT_ROOT,
)
from .consultation_router import router as consultation_router
from .coordination_router import router as coordination_router
from .cost_router import router as cost_router
from .dashboard_router import router as dashboard_router
from .decisions_router import router as decisions_router
from .delegate_router import router as delegate_router
from .discussions_router import router as discussions_router
from .docs_router import router as docs_router
from .git_hygiene_router import router as git_hygiene_router
from .gold_router import router as gold_router
from .governance_router import collect_governance_summary
from .governance_router import router as governance_router
from .hermes_cron_router import router as hermes_cron_router
from .images_router import router as images_router
from .issues_router import router as issues_router
from .knowledge_router import router as knowledge_router
from .preload import preload_all
from .rag_router import router as rag_router
from .repository_authority import build_repository_authority
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
from .worktrees_router import router as worktrees_router


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Lifespan hook — wrap uvicorn signal handlers so we record WHO killed us.

    Without this, "Shutting down" lines in logs/api.log have no provenance.
    See scripts/api/_signal_log.py for the wrapper rationale.
    """
    preload_all()
    install_signal_logging()
    ensure_broker_db_ready()
    yield


app = FastAPI(
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
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(resilience_middleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Consistent JSON error format for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": str(exc)},
    )


# Mount team routers — each team owns their own file
app.include_router(admin_router, prefix="/api/admin")
app.include_router(agent_router, prefix="/api/agent", tags=["agent"])
app.include_router(artifacts_router, prefix="/api/artifacts", tags=["artifacts"])
app.include_router(blue_router, prefix="/api/blue")
app.include_router(comms_router, prefix="/api/comms")
app.include_router(session_streams_router, prefix="/api/session-streams", tags=["session-streams"])
app.include_router(coordination_router, prefix="/api/coordination")
app.include_router(consultation_router, prefix="/api/consultation")
app.include_router(cost_router, prefix="/api/cost")
app.include_router(cost_router, prefix="/api/analytics/cost")
app.include_router(contracts_router, prefix="/api/contracts", tags=["contracts"])
app.include_router(dashboard_router, prefix="/api/dashboard")
app.include_router(decisions_router, prefix="/api/decisions", tags=["decisions"])
app.include_router(delegate_router, prefix="/api/delegate")
app.include_router(docs_router, prefix="/artifacts")
app.include_router(docs_router, prefix="/files")
app.include_router(discussions_router, prefix="/api/discussions", tags=["discussions"])
app.include_router(git_hygiene_router, prefix="/api/git", tags=["git"])
app.include_router(gold_router, prefix="/api/gold")
app.include_router(governance_router, prefix="/api/state/governance", tags=["governance"])
app.include_router(hermes_cron_router, prefix="/api/hermes-cron", tags=["hermes-cron"])
app.include_router(build_events_router, prefix="/api/build/events")
app.include_router(images_router, prefix="/api/images")
app.include_router(issues_router, prefix="/api/issues", tags=["issues"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(rag_router, prefix="/api/rag")
# GH #1529 P3 — reviewer-ghost telemetry nested under /api/state so clients
# can discover it alongside the other state-query endpoints.
app.include_router(
    reviewer_ghosts_router,
    prefix="/api/state/reviewer-ghosts",
    tags=["reviewer-ghosts"],
)
app.include_router(rollover_router, prefix="/api/rollovers", tags=["rollovers"])
app.include_router(rules_router, prefix="/api/rules", tags=["rules"])
app.include_router(runtime_router, prefix="/api/runtime")
app.include_router(session_router, prefix="/api/session", tags=["session"])
app.include_router(site_router, prefix="/api/site", tags=["site"])
app.include_router(state_router, prefix="/api/state")
app.include_router(telemetry_router)
app.include_router(wiki_router, prefix="/api/wiki", tags=["wiki"])
app.include_router(worktrees_router, prefix="/api/worktrees", tags=["worktrees"])


# Server start time for uptime calculation
_SERVER_START = datetime.now(UTC)
SOURCES_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
SESSION_STATE_DIR = PROJECT_ROOT / "docs" / "session-state"

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
#   - ``runtime``, ``delegate``, ``wiki``, ``health``, ``session_hints``
#                            — pure-Python / filesystem, no inner
#                              timeout; they rely on being cheap.
# If a sync collector ever starts to block (e.g. a network FS hang), it
# will tie up a threadpool slot past the hard timeout. See
# MONITOR-API.md for the full breakdown.
ORIENT_SECTION_TTLS: dict[str, float] = {
    "git": 30.0,
    "issues": 120.0,
    # Pipeline has TTL 0 on purpose — ``_collect_pipeline_orient_data``
    # calls ``state_summary()`` which has its own 60 s cache. Stacking
    # caches produced staleness up to 119 s with ``generated_at``
    # labelled fresh (reviewer BLOCKER #1309 / B2).
    "pipeline": 0.0,
    "runtime": 60.0,
    "delegate": 30.0,
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
    "pipeline": "fs",
    "runtime": "fs",
    "delegate": "fs",
    "bridge_pending": "sqlite",
    "rollovers": "fs",
    "wiki": "fs",
    "governance": "fs",
    "health": "probe",
    "session_hints": "fs",
}

ORIENT_SECTION_HARD_TIMEOUT_S = 5.0

ORIENT_SECTION_KEYS: tuple[str, ...] = tuple(ORIENT_SECTION_TTLS.keys())

# Lean cold-start preset (``?lean=true``): the small, lane-agnostic sections an agent needs to
# orient BEFORE it has selected work — tree state (git), active dispatches (delegate), pending
# bridge asks, blocking decisions (governance), health, and the handoff pointers / current goal
# (session_hints). Excludes the three heavy sections — ``pipeline`` (~2k module stats),
# ``issues`` (full gh list), ``wiki`` (per-track coverage) — which are fetched on demand via
# ``?sections=...``. Cuts the default cold-start payload sharply (codex cold-start review; #4728).
LEAN_ORIENT_SECTIONS: tuple[str, ...] = (
    "git",
    "runtime",
    "delegate",
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


def _run_command(args: list[str], *, timeout: float = 2.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=LIVE_REPO_ROOT if args and args[0] == "git" else PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _collect_git_orient_data() -> dict:
    branch_proc = _run_command(["git", "branch", "--show-current"])
    head_proc = _run_command(["git", "rev-parse", "--short=9", "HEAD"])
    ahead_proc = _run_command(["git", "rev-list", "--count", "origin/main..HEAD"])
    log_proc = _run_command(["git", "log", "--oneline", "-5"])

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
        primary_status = worktree_containment.primary_checkout_dirty_status(LIVE_REPO_ROOT)
    except Exception as exc:
        branch = branch_proc.stdout.strip()
        primary_status = {
            "main_root": str(LIVE_REPO_ROOT),
            "branch": branch,
            "protected_branch": branch in worktree_containment.PROTECTED_BRANCHES,
            "dirty": False,
            "dirty_count": 0,
            "tracked_dirty_count": 0,
            "untracked_dirty_count": 0,
            "entries": [],
            "checked_cwd": str(LIVE_REPO_ROOT),
            "checked_command": "git status --porcelain=v1 -z --untracked-files=all",
            "error": str(exc),
        }

    branch = branch_proc.stdout.strip()
    authority = build_repository_authority(
        project_root=PROJECT_ROOT,
        live_repo_root=LIVE_REPO_ROOT,
        data_branch=branch,
    )
    return {
        "branch": branch,
        "head": head_proc.stdout.strip(),
        "ahead_of_origin": ahead_value,
        "recent_commits": recent_commits,
        "primary_checkout_dirty": primary_status["dirty"],
        "primary_checkout": primary_status,
        "authority": authority,
    }


def _collect_issues_orient_data() -> dict:
    """Fetch open GitHub issues via ``gh``.

    Raises ``RuntimeError`` on any failure (subprocess error, non-zero
    exit, malformed JSON). Raising is important — ``_cached_orient_section``
    only caches successful returns, so a transient ``gh`` blip must
    not poison the issues cache for the full TTL window (reviewer
    BLOCKER, GH #1309).
    """
    proc = _run_command(
        [
            "gh",
            "issue",
            "list",
            "--state",
            "open",
            "--limit",
            "10",
            "--json",
            "number,title,labels,createdAt",
        ],
        # /api/orient is part of dashboard cold load. Issue details are useful,
        # but not important enough to let a slow gh/network path dominate it.
        timeout=5.0,
    )

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


async def _collect_pipeline_orient_data() -> dict:
    return {"summary": await state_api.state_summary()}


_gc_sweep_lock = threading.Lock()
_gc_sweep_thread: threading.Thread | None = None
_last_gc_sweep_summary: dict[str, Any] | None = None


def _maybe_run_worktree_gc_sweep() -> None:
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

    global _gc_sweep_thread
    with _gc_sweep_lock:
        if _gc_sweep_thread is not None and _gc_sweep_thread.is_alive():
            return
        _gc_sweep_thread = threading.Thread(
            target=_run_worktree_gc_sweep, daemon=True
        )
        _gc_sweep_thread.start()


def _run_worktree_gc_sweep() -> None:
    global _last_gc_sweep_summary
    try:
        repo_root = primary_checkout_root(PROJECT_ROOT)

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
        logger.info(
            "worktree GC sweep: removed=%d, skipped=%d, errors=%d",
            removed, skipped, errors
        )
    except Exception as exc:
        logger.exception("worktree GC sweep failed: %s", exc)


def _collect_runtime_orient_data() -> dict:
    _maybe_run_worktree_gc_sweep()
    agents = runtime_api.list_runtime_agents()
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

    res = {
        "agents": [agent["name"] for agent in agents if agent.get("name")],
        "recent_outcomes": runtime_api.runtime_recent_outcomes_today(),
        "headroom": headroom,
    }
    if _last_gc_sweep_summary is not None:
        res["worktree_gc"] = _last_gc_sweep_summary
    return res


def _collect_delegate_orient_data() -> dict:
    recent = delegate_api.list_delegate_tasks(status="all", limit=5)
    return {
        "active_count": delegate_api.active_delegate_count(),
        "recent": recent["tasks"],
    }


def _collect_bridge_pending_orient_data() -> dict:
    from scripts.ai_agent_bridge import _channels  # noqa: PLC0415 — optional broker bridge

    return _channels.bridge_pending_summary()


def _collect_rollovers_orient_data() -> dict:
    return collect_rollover_orient_data()


def _collect_wiki_orient_data() -> dict:
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
    wiki_api.wiki_state.get_status_summary()

    candidates = wiki_api._list_article_candidates()  # one full-tree scan
    wiki_dir = wiki_api.wiki_config.WIKI_DIR

    by_track: dict[str, dict[str, Any]] = {}
    for track in wiki_api._known_tracks():
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


def _collect_governance_orient_data() -> dict[str, int]:
    return collect_governance_summary()


logger = logging.getLogger(__name__)


def _port_open(host: str, port: int, timeout_s: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def _readable_file(path: Path) -> bool:
    return path.exists() and path.is_file() and os.access(path, os.R_OK)


def _core_bare_canary() -> bool:
    """Detection canary for issue #2842: ``core.bare`` must stay false.

    ``core.bare`` lives in the SHARED ``.git/config``; if any subprocess flips it
    to ``true`` it silently breaks ``git`` work-tree ops for the main checkout AND
    every linked worktree at once. Reading/writing git config does not need a work
    tree, so this check still functions while the footgun is active — which is when
    it's needed. On drift it auto-resets to false and logs an alert. Never raises:
    the canary must not break health collection.
    """
    try:
        from scripts.audit.check_core_bare import check_core_bare  # noqa: PLC0415 — script-path fallback
    except ImportError:  # path-flavoured import for test/script contexts
        from audit.check_core_bare import check_core_bare  # noqa: PLC0415 — script-path fallback
    try:
        ok, message = check_core_bare(PROJECT_ROOT, fix=True)
    except Exception:
        logger.exception("core.bare canary (#2842) failed to run")
        return True  # fail-open: don't raise a false alarm on canary error
    if "reset" in message or not ok:
        logger.warning("core.bare canary (#2842): %s", message)
    return ok


def _self_symlink_canary() -> bool:
    """Detection canary for the node_modules ELOOP footgun.

    A self-referential ``node_modules`` symlink (``X -> X``) is an infinite
    loop. ``npm run <script>`` builds its child PATH by walking the directory
    tree upward and prepending every ancestor ``node_modules/.bin``; resolving
    the looping ancestor makes ``spawn`` return ``ELOOP``, so every npm build
    dies instantly with exit 194 and no output — looking like "Astro is broken"
    when it is not. The loop is gitignored so CI cannot catch it; only a local
    canary can. On detection it auto-removes the looping link and logs an alert.
    Never raises: the canary must not break health collection. See the autopsy
    ``docs/bug-autopsies/node-modules-eloop-symlink.md``.
    """
    try:
        from scripts.audit.check_self_symlinks import check_self_symlinks  # noqa: PLC0415 — script-path fallback
    except ImportError:  # path-flavoured import for test/script contexts
        from audit.check_self_symlinks import check_self_symlinks  # noqa: PLC0415 — script-path fallback
    try:
        ok, message = check_self_symlinks(PROJECT_ROOT, fix=True)
    except Exception:
        logger.exception("node_modules ELOOP canary failed to run")
        return True  # fail-open: don't raise a false alarm on canary error
    if "removed" in message or not ok:
        logger.warning("node_modules ELOOP canary: %s", message)
    return ok


def _collect_health_orient_data() -> dict:
    return {
        "api": True,
        "mcp_rag": _port_open("127.0.0.1", 8766, 0.2),
        "sources_db": _readable_file(SOURCES_DB_PATH),
        "message_broker": _readable_file(MESSAGE_DB),
        "git_core_bare_ok": _core_bare_canary(),
        "node_modules_symlinks_ok": _self_symlink_canary(),
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


def _collect_session_hints_orient_data() -> list[dict]:
    if not SESSION_STATE_DIR.exists():
        return []
    hints = []
    for path in sorted(SESSION_STATE_DIR.glob("*.md"), reverse=True)[:10]:
        hints.append(
            {
                "file": str(path.relative_to(PROJECT_ROOT)),
                "first_line": _first_non_empty_line(path),
            }
        )
    return hints


# ==================== SHARED ENDPOINTS ====================


@app.get("/api/health")
async def health_check():
    """Root health check — returns server status, version, uptime."""
    now = datetime.now(UTC)
    uptime = now - _SERVER_START
    return {
        "status": "ok",
        "version": app.version,
        "uptime_seconds": int(uptime.total_seconds()),
        "started_at": _SERVER_START.isoformat(),
        "checked_at": now.isoformat(),
        "resilience": get_resilience_snapshot(),
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
        "pipeline": (_collect_pipeline_orient_data, {"summary": {}}, True),
        "runtime": (_collect_runtime_orient_data, {}, False),
        "delegate": (_collect_delegate_orient_data, {"active_count": 0, "recent": []}, False),
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


@app.get("/api/orient")
async def orient(
    request: Request,
    fresh: bool = False,
    lean: bool = Query(
        False,
        description="Lean cold-start preset: return only the lightweight sections "
        "(git, runtime, delegate, bridge_pending, rollovers, governance, health, session_hints), "
        "skipping the heavy pipeline/issues/wiki. Ignored when 'sections' is given.",
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
            120 s for ``issues``/``wiki``). Reviewer BLOCKER B3 / #1309.
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
                collector,
                fallback,
                is_async=is_async,
            )
            for key, (collector, fallback, is_async) in section_specs.items()
            if key in selected
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
    if "pipeline" in section_data:
        response["pipeline"] = section_data["pipeline"]
    if "runtime" in section_data:
        response["runtime"] = section_data["runtime"]
    if "delegate" in section_data:
        response["delegate"] = section_data["delegate"]
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


@app.get("/api/config")
async def get_config():
    # Import pipeline phase config — single source of truth
    try:
        from scripts.build.phase_constants import PHASE_LABELS, PHASES  # noqa: PLC0415 — preserves endpoint fallback

        pipeline_info = {"phases": PHASES, "phase_labels": PHASE_LABELS}
    except ImportError:
        pipeline_info = {}
    return {"levels": LEVELS, "api_version": app.version, "pipeline": pipeline_info}


@app.get("/api/batch/dispatcher")
async def get_dispatcher_state():
    state_file = BATCH_STATE_DIR / "dispatcher_state.json"
    if not state_file.exists():
        return {"tracks": {}}
    with open(state_file) as f:
        return json.load(f)


@app.get("/api/batch/active")
async def get_active_orchestration():
    active = []
    for track_dir in CURRICULUM_ROOT.iterdir():
        if not track_dir.is_dir():
            continue
        orch_dir = track_dir / "orchestration"
        if not orch_dir.exists():
            continue
        for module_dir in orch_dir.iterdir():
            if not module_dir.is_dir():
                continue
            latest_mtime = 0
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


@app.get("/api/batch/failures")
async def get_failure_queue():
    f_file = BATCH_STATE_DIR / "failure_queue.json"
    if not f_file.exists():
        return []
    with open(f_file) as f:
        return json.load(f)


@app.get("/api/batch/usage")
async def get_batch_usage():
    usage_dir = BATCH_STATE_DIR / "api_usage"
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


@app.get("/api/batch/checkpoints")
async def get_all_checkpoints():
    results = {}
    for f in BATCH_STATE_DIR.glob("checkpoint_*.json"):
        track = f.stem.replace("checkpoint_", "")
        try:
            with open(f) as fh:
                results[track] = json.load(fh)
        except Exception:
            pass
    return results


@app.get("/api/batch/dispatcher/running")
async def dispatcher_running():
    return {"running": False}


@app.post("/api/batch/dispatcher/scan")
async def run_dispatcher_scan():
    cmd = [
        str(LIVE_REPO_ROOT / ".venv" / "bin" / "python"),
        str(LIVE_REPO_ROOT / "scripts" / "batch_dispatcher.py"),
        "scan",
    ]
    # Use asyncio.to_thread to avoid blocking the event loop
    result = await asyncio.to_thread(subprocess.run, cmd, cwd=LIVE_REPO_ROOT)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Dispatcher scan failed")
    return {"status": "ok"}


@app.get("/api/batch/dispatcher/logs")
async def get_dispatcher_logs(lines: int = 50):
    log_file = PROJECT_ROOT / "logs" / "dispatcher.log"
    if not log_file.exists():
        return {"lines": []}
    return {"lines": log_file.read_text().splitlines()[-lines:]}


# ==================== WEBSOCKET ====================


@app.websocket("/ws/batch")
async def batch_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"type": "heartbeat"})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass


# ==================== IMAGE SERVING ====================

_IMAGE_DIR = PROJECT_ROOT / "data" / "textbook_images"
_ALLOWED_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
_MIME_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _safe_join(base: Path, *parts: str | Path) -> Path | None:
    try:
        return safe_join(base, *parts)
    except ValueError:
        return None


@app.get("/images/{path:path}")
async def serve_image(path: str):
    """Serve textbook images with caching. Path relative to data/textbook_images/."""
    file_path = _safe_join(_IMAGE_DIR, path)
    if file_path is None:
        raise HTTPException(status_code=403, detail="Invalid image path")
    if file_path.suffix.lower() not in _ALLOWED_IMG_EXT:
        raise HTTPException(status_code=403, detail="Forbidden file type")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404)
    # Prevent path traversal
    try:
        file_path.resolve().relative_to(_IMAGE_DIR.resolve())
    except ValueError as e:
        raise HTTPException(status_code=403, detail="Path traversal not allowed") from e
    return FileResponse(
        file_path,
        media_type=_MIME_TYPES.get(file_path.suffix.lower(), "application/octet-stream"),
        headers={"Cache-Control": "max-age=3600"},
    )


# ==================== STATIC FILES (MUST BE LAST) ====================


@app.get("/{path:path}")
async def serve_static(path: str):
    if not path or path == "/":
        return FileResponse(DASHBOARDS_DIR / "index.html")
    file_path = _safe_join(DASHBOARDS_DIR, path)
    if file_path is None:
        raise HTTPException(status_code=403, detail="Path traversal not allowed")
    dashboards_root = DASHBOARDS_DIR.resolve()
    # Keep explicit traversal guard if relative path join bypassed via symlink tricks.
    if not file_path.resolve().is_relative_to(dashboards_root):
        raise HTTPException(status_code=403, detail="Path traversal not allowed")
    if file_path.is_file():
        return FileResponse(file_path)
    if file_path.is_dir() and (file_path / "index.html").is_file():
        return FileResponse(file_path / "index.html")
    raise HTTPException(status_code=404)
