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
import os
import socket
import subprocess
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from . import delegate_router as delegate_api
from . import runtime_router as runtime_api
from . import state_router as state_api
from . import wiki_router as wiki_api
from .admin_router import router as admin_router
from .agent_router import router as agent_router
from .artifacts_router import router as artifacts_router
from .blue_router import router as blue_router
from .build_events_router import router as build_events_router
from .comms_router import router as comms_router
from .config import (
    BATCH_STATE_DIR,
    CURRICULUM_ROOT,
    LEVELS,
    MESSAGE_DB,
    PLAYGROUNDS_DIR,
    PROJECT_ROOT,
)
from .consultation_router import router as consultation_router
from .cost_router import router as cost_router
from .dashboard_router import router as dashboard_router
from .decisions_router import router as decisions_router
from .delegate_router import router as delegate_router
from .gold_router import router as gold_router
from .images_router import router as images_router
from .issues_router import router as issues_router
from .rag_router import router as rag_router
from .rules_router import router as rules_router
from .runtime_router import router as runtime_router
from .session_router import router as session_router
from .site_router import router as site_router
from .state_helpers import cache_get, cache_invalidate, cache_set
from .state_router import router as state_router
from .wiki_router import router as wiki_router
from .worktrees_router import router as worktrees_router

app = FastAPI(
    title="Playground API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(consultation_router, prefix="/api/consultation")
app.include_router(cost_router, prefix="/api/analytics/cost")
app.include_router(dashboard_router, prefix="/api/dashboard")
app.include_router(decisions_router, prefix="/api/decisions", tags=["decisions"])
app.include_router(delegate_router, prefix="/api/delegate")
app.include_router(gold_router, prefix="/api/gold")
app.include_router(build_events_router, prefix="/api/build/events")
app.include_router(images_router, prefix="/api/images")
app.include_router(issues_router, prefix="/api/issues", tags=["issues"])
app.include_router(rag_router, prefix="/api/rag")
app.include_router(rules_router, prefix="/api/rules", tags=["rules"])
app.include_router(runtime_router, prefix="/api/runtime")
app.include_router(session_router, prefix="/api/session", tags=["session"])
app.include_router(site_router, prefix="/api/site", tags=["site"])
app.include_router(state_router, prefix="/api/state")
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
    "wiki": 120.0,
    "health": 15.0,
    "session_hints": 60.0,
}

ORIENT_SECTION_SOURCES: dict[str, str] = {
    "git": "git",
    "issues": "gh",
    "pipeline": "fs",
    "runtime": "fs",
    "delegate": "fs",
    "wiki": "fs",
    "health": "probe",
    "session_hints": "fs",
}

ORIENT_SECTION_HARD_TIMEOUT_S = 5.0


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
        cwd=PROJECT_ROOT,
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

    return {
        "branch": branch_proc.stdout.strip(),
        "head": head_proc.stdout.strip(),
        "ahead_of_origin": ahead_value,
        "recent_commits": recent_commits,
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
        timeout=2.0,
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
        issues.append({
            "number": item.get("number"),
            "title": item.get("title"),
            "labels": [label.get("name") for label in labels if isinstance(label, dict) and label.get("name")],
            "age_days": max(0, (now.date() - created.date()).days) if created else None,
        })
    return {"issues": issues}


async def _collect_pipeline_orient_data() -> dict:
    return {"summary": await state_api.state_summary()}


def _collect_runtime_orient_data() -> dict:
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
    return {
        "agents": [agent["name"] for agent in agents if agent.get("name")],
        "recent_outcomes": runtime_api.runtime_recent_outcomes_today(),
        "headroom": headroom,
    }


def _collect_delegate_orient_data() -> dict:
    recent = delegate_api.list_delegate_tasks(status="all", limit=5)
    return {
        "active_count": delegate_api.active_delegate_count(),
        "recent": recent["tasks"],
    }


def _collect_wiki_orient_data() -> dict:
    wiki_api.wiki_state.get_status_summary()
    by_track = {}
    for track in wiki_api._known_tracks():
        slugs = wiki_api._track_slugs(track)
        if not slugs:
            continue
        compiled = 0
        for slug in slugs:
            article = wiki_api._resolve_article(track, slug)
            if not article:
                continue
            article_path = wiki_api.wiki_config.WIKI_DIR / article["path"]
            if article_path.exists():
                compiled += 1
        total = len(slugs)
        by_track[track] = {
            "compiled": compiled,
            "total": total,
            "pct": round(compiled / total * 100, 1) if total else 0,
        }
    return {"by_track": by_track}


def _port_open(host: str, port: int, timeout_s: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def _readable_file(path: Path) -> bool:
    return path.exists() and path.is_file() and os.access(path, os.R_OK)


def _collect_health_orient_data() -> dict:
    return {
        "api": True,
        "mcp_rag": _port_open("127.0.0.1", 8766, 0.2),
        "sources_db": _readable_file(SOURCES_DB_PATH),
        "message_broker": _readable_file(MESSAGE_DB),
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
        hints.append({
            "file": str(path.relative_to(PROJECT_ROOT)),
            "first_line": _first_non_empty_line(path),
        })
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
            value = await asyncio.wait_for(
                asyncio.to_thread(collector),  # type: ignore[arg-type]
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


@app.get("/api/orient")
async def orient(fresh: bool = False):
    """One-shot agent orientation.

    Query params:
        fresh: if true, invalidate every ``orient_*`` cache entry before
            gathering. Use it when an agent just committed, renamed a
            file, or otherwise needs to see a change it made moments
            ago without waiting for the longest section TTL (up to
            120 s for ``issues``/``wiki``). Reviewer BLOCKER B3 / #1309.
    """
    if fresh:
        cache_invalidate("orient_")

    (
        (git_info, git_meta),
        (issues_info, issues_meta),
        (pipeline_info, pipeline_meta),
        (runtime_info, runtime_meta),
        (delegate_info, delegate_meta),
        (wiki_info, wiki_meta),
        (health_info, health_meta),
        (session_hints, session_hints_meta),
    ) = await asyncio.gather(
        _cached_orient_section("git", _collect_git_orient_data, {}),
        _cached_orient_section("issues", _collect_issues_orient_data, {"issues": []}),
        _cached_orient_section(
            "pipeline",
            _collect_pipeline_orient_data,
            {"summary": {}},
            is_async=True,
        ),
        _cached_orient_section("runtime", _collect_runtime_orient_data, {}),
        _cached_orient_section(
            "delegate",
            _collect_delegate_orient_data,
            {"active_count": 0, "recent": []},
        ),
        _cached_orient_section("wiki", _collect_wiki_orient_data, {"by_track": {}}),
        _cached_orient_section("health", _collect_health_orient_data, {"api": True}),
        _cached_orient_section("session_hints", _collect_session_hints_orient_data, []),
    )

    section_metas = {
        "git": git_meta,
        "issues": issues_meta,
        "pipeline": pipeline_meta,
        "runtime": runtime_meta,
        "delegate": delegate_meta,
        "wiki": wiki_meta,
        "health": health_meta,
        "session_hints": session_hints_meta,
    }

    # Top-level ``generated_at`` is the FLOOR across sections, not the
    # request time. On a full cache hit it reflects the oldest piece of
    # data the caller is looking at; on an all-miss it equals the
    # collector timestamp (which is also "now"). Reviewer CONCERN C1 /
    # #1309: request-time was misleading consumers into thinking a
    # 119-s-old payload was fresh.
    generated_candidates: list[str] = [
        ts for m in section_metas.values()
        if isinstance(ts := m.get("generated_at"), str)
    ]
    top_generated_at = (
        min(generated_candidates) if generated_candidates
        else _isoformat_z(datetime.now(UTC))
    )

    response: dict[str, Any] = {
        "generated_at": top_generated_at,
        "git": git_info,
        "issues": issues_info.get("issues", []) if isinstance(issues_info, dict) else [],
        "pipeline": pipeline_info,
        "runtime": runtime_info,
        "delegate": delegate_info,
        "wiki": wiki_info,
        "health": health_info,
        "session_hints": session_hints,
        "meta": section_metas,
    }

    # ``_collect_issues_orient_data`` raises on failure now. The error
    # branch of ``_cached_orient_section`` writes the short
    # ``str(exc)`` form into the fallback payload and the richer
    # ``TypeName: msg`` form into meta. Keep the top-level
    # ``issues_error`` key on the short form for back-compat with
    # clients that were reading it before per-section meta existed.
    if isinstance(issues_info, dict) and issues_info.get("error"):
        response["issues_error"] = issues_info["error"]
    return response


@app.get("/api/config")
async def get_config():
    # Import pipeline phase config — single source of truth
    try:
        from scripts.build.v6_build import PHASE_LABELS, PHASES
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
                active.append({
                    "slug": module_dir.name,
                    "track": track_dir.name,
                    "seconds_ago": int(datetime.now().timestamp() - latest_mtime),
                })
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
        str(PROJECT_ROOT / ".venv" / "bin" / "python"),
        str(PROJECT_ROOT / "scripts" / "batch_dispatcher.py"),
        "scan",
    ]
    # Use asyncio.to_thread to avoid blocking the event loop
    result = await asyncio.to_thread(subprocess.run, cmd, cwd=PROJECT_ROOT)
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


@app.get("/images/{path:path}")
async def serve_image(path: str):
    """Serve textbook images with caching. Path relative to data/textbook_images/."""
    file_path = _IMAGE_DIR / path
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
        return FileResponse(PLAYGROUNDS_DIR / "index.html")
    file_path = (PLAYGROUNDS_DIR / path).resolve()
    playgrounds_root = PLAYGROUNDS_DIR.resolve()
    # Prevent path traversal — resolved path must stay within playgrounds dir
    if not file_path.is_relative_to(playgrounds_root):
        raise HTTPException(status_code=403, detail="Path traversal not allowed")
    if file_path.is_file():
        return FileResponse(file_path)
    if file_path.is_dir() and (file_path / "index.html").is_file():
        return FileResponse(file_path / "index.html")
    raise HTTPException(status_code=404)
