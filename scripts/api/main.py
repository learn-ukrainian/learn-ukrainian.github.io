"""
FastAPI server for dashboard visualizations and curriculum management.

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
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

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
    DISPATCHER_LOG,
    LEVELS,
    MESSAGE_DB,
    PROJECT_ROOT,
    SOURCES_DB,
    TEXTBOOK_IMAGES_DIR,
)
from .consultation_router import router as consultation_router
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
from .images_router import router as images_router
from .issues_router import router as issues_router
from .rag_router import router as rag_router
from .resilience import get_resilience_snapshot, resilience_middleware
from .reviewer_ghosts_router import router as reviewer_ghosts_router
from .rules_router import router as rules_router
from .runtime_router import router as runtime_router
from .session_router import router as session_router
from .site_router import router as site_router
from .state_helpers import cache_get, cache_invalidate, cache_set
from .state_router import router as state_router
from .telemetry_router import router as telemetry_router
from .wiki_router import router as wiki_router
from .worktrees_router import router as worktrees_router


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Lifespan hook — wrap uvicorn signal handlers so we record WHO killed us."""
    install_signal_logging()
    ensure_broker_db_ready()
    yield


app = FastAPI(
    title="Dashboard API",
    version="2.0.0",
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


# Mount team routers
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
app.include_router(docs_router, prefix="/artifacts")
app.include_router(docs_router, prefix="/files")
app.include_router(discussions_router, prefix="/api/discussions", tags=["discussions"])
app.include_router(git_hygiene_router, prefix="/api/git", tags=["git"])
app.include_router(gold_router, prefix="/api/gold")
app.include_router(governance_router, prefix="/api/state/governance", tags=["governance"])
app.include_router(build_events_router, prefix="/api/build/events")
app.include_router(images_router, prefix="/api/images")
app.include_router(issues_router, prefix="/api/issues", tags=["issues"])
app.include_router(rag_router, prefix="/api/rag")
app.include_router(
    reviewer_ghosts_router,
    prefix="/api/state/reviewer-ghosts",
    tags=["reviewer-ghosts"],
)
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
SESSION_STATE_DIR = PROJECT_ROOT / "docs" / "session-state"

ORIENT_SECTION_TTLS: dict[str, float] = {
    "git": 30.0,
    "issues": 120.0,
    "pipeline": 0.0,
    "runtime": 60.0,
    "delegate": 30.0,
    "bridge_pending": 15.0,
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
    "wiki": "fs",
    "governance": "fs",
    "health": "probe",
    "session_hints": "fs",
}

ORIENT_SECTION_HARD_TIMEOUT_S = 5.0

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
    """Fetch open GitHub issues via ``gh``."""
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
        timeout=0.25,
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


def _collect_bridge_pending_orient_data() -> dict:
    from scripts.ai_agent_bridge import _channels

    return _channels.bridge_pending_summary()


def _collect_wiki_orient_data() -> dict:
    """Per-track compiled article counts."""
    wiki_api.wiki_state.get_status_summary()

    candidates = wiki_api._list_article_candidates()
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
            domain_matches = [
                c for c in slug_cands
                if wiki_api._matches_track_domain(track, c["path"])
            ]
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
        "sources_db": _readable_file(SOURCES_DB),
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
        "resilience": get_resilience_snapshot(),
    }


async def _cached_orient_section(
    key: str,
    collector: Callable[[], Any] | Callable[[], Awaitable[Any]],
    fallback: Any,
    *,
    is_async: bool = False,
) -> tuple[Any, dict]:
    """Run one orient collector with TTL cache + hard timeout + fallback."""
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
        short_err = f"section_timeout_{ORIENT_SECTION_HARD_TIMEOUT_S}s"
        meta["error"] = short_err
        if isinstance(fallback, dict):
            return {**fallback, "error": short_err}, meta
        return fallback, meta
    except Exception as exc:
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
    """One-shot agent orientation."""
    if fresh:
        cache_invalidate("orient_")

    (
        (git_info, git_meta),
        (issues_info, issues_meta),
        (pipeline_info, pipeline_meta),
        (runtime_info, runtime_meta),
        (delegate_info, delegate_meta),
        (bridge_pending_info, bridge_pending_meta),
        (wiki_info, wiki_meta),
        (governance_info, governance_meta),
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
        _cached_orient_section(
            "bridge_pending",
            _collect_bridge_pending_orient_data,
            {},
        ),
        _cached_orient_section("wiki", _collect_wiki_orient_data, {"by_track": {}}),
        _cached_orient_section(
            "governance",
            _collect_governance_orient_data,
            {
                "decisions_total": 0,
                "decisions_stale": 0,
                "decisions_approaching_expiry": 0,
                "adrs_total": 0,
                "adrs_warnings": 0,
                "adrs_errors": 0,
            },
        ),
        _cached_orient_section("health", _collect_health_orient_data, {"api": True}),
        _cached_orient_section("session_hints", _collect_session_hints_orient_data, []),
    )

    section_metas = {
        "git": git_meta,
        "issues": issues_meta,
        "pipeline": pipeline_meta,
        "runtime": runtime_meta,
        "delegate": delegate_meta,
        "bridge_pending": bridge_pending_meta,
        "wiki": wiki_meta,
        "governance": {**governance_meta, **governance_info},
        "health": health_meta,
        "session_hints": session_hints_meta,
    }

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
        "bridge_pending": bridge_pending_info,
        "wiki": wiki_info,
        "governance": governance_info,
        "health": health_info,
        "session_hints": session_hints,
        "meta": section_metas,
    }

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
    result = await asyncio.to_thread(subprocess.run, cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Dispatcher scan failed")
    return {"status": "ok"}


@app.get("/api/batch/dispatcher/logs")
async def get_dispatcher_logs(lines: int = 50):
    if not DISPATCHER_LOG.exists():
        return {"lines": []}
    return {"lines": DISPATCHER_LOG.read_text().splitlines()[-lines:]}


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

_ALLOWED_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
_MIME_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _safe_join(base: Path, *parts: str | Path) -> Path | None:
    try:
        return safe_join(base, *parts)
    except ValueError:
        return None


@app.get("/images/{path:path}")
async def serve_image(path: str):
    """Serve textbook images with caching. Path relative to TEXTBOOK_IMAGES_DIR."""
    file_path = _safe_join(TEXTBOOK_IMAGES_DIR, path)
    if file_path is None:
        raise HTTPException(status_code=403, detail="Invalid image path")
    if file_path.suffix.lower() not in _ALLOWED_IMG_EXT:
        raise HTTPException(status_code=403, detail="Forbidden file type")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404)
    # Prevent path traversal
    try:
        file_path.resolve().relative_to(TEXTBOOK_IMAGES_DIR.resolve())
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
