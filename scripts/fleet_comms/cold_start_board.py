"""Fleet-comms driver cold start board (Sol PR-2 / WP-A).

Fail-open diagnostic board for cold-starting drivers and launcher sessions.
Collects session/plane/stream/inbox telemetry without making any writes,
lease claims, or network POSTs.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.fleet_comms.efficiency_metrics import (
    _AUTHORITY_BACKLOG_STATES,
    _column_names,
    _table_exists,
    collect_dead_letters,
    collect_dead_letters_authority,
    collect_delivery_backlog,
    collect_delivery_backlog_authority,
    collect_stream_bottleneck_metrics,
    resolve_metrics_source,
)
from scripts.fleet_comms.message_plane import (
    default_plane_root,
    read_plane_status,
    resolve_plane_mode,
)

try:
    from agents_extensions.shared.session_streams.db import (
        SessionStreamDatabase,
        default_database_path,
    )
    from agents_extensions.shared.session_streams.handoff import diagnose_handoff
    from agents_extensions.shared.session_streams.model import entry_as_dict
    from agents_extensions.shared.session_streams.store import SessionStreamStore

    HAS_SESSION_STREAMS = True
except ImportError:
    HAS_SESSION_STREAMS = False
    default_database_path = None  # type: ignore[assignment]

MAX_STRING_LEN = 200
MAX_LIST_LEN = 5
MAX_BOARD_BYTES = 16384  # 16KiB

# Probes that may flip board_status to degraded. Optional/best-effort probes
# (orient_lean, gh_pr_list, needle_search, bottleneck_slice, …) must not.
LOAD_BEARING_PROBES = frozenset(
    {
        "plane_status",
        "inbox_check",
        "backlog_and_dead_letters",
    }
)
SESSION_STREAMS_REL = Path(".agent/session-streams/v1/session-streams.sqlite3")


@dataclass
class ProbeResult:
    """Fail-open outcome container for one diagnostic probe."""

    status: str  # "ok" | "degraded" | "error" | "skipped"
    elapsed_ms: float
    error: str | None = None
    data: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "error": self.error,
            "data": self.data,
        }


def run_fail_open_probe(name: str, fn: Any, *args: Any, **kwargs: Any) -> ProbeResult:
    """Execute a probe function with timing and fail-open exception handling.

    Never raises an exception out of the probe wrapper.
    """
    start = time.perf_counter()
    try:
        res = fn(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000.0
        if isinstance(res, ProbeResult):
            res.elapsed_ms = round(elapsed, 2)
            return res
        return ProbeResult(status="ok", elapsed_ms=elapsed, data=res)
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="error",
            elapsed_ms=elapsed,
            error=f"{type(exc).__name__}: {exc}",
            data=None,
        )


def cap_data(
    data: Any,
    max_str: int = MAX_STRING_LEN,
    max_list: int = MAX_LIST_LEN,
) -> Any:
    """Recursively cap strings to max_str and lists to max_list elements."""
    if isinstance(data, str):
        if len(data) > max_str:
            return data[:max_str] + f"...[truncated {len(data) - max_str} chars]"
        return data
    elif isinstance(data, list):
        capped = [cap_data(item, max_str, max_list) for item in data[:max_list]]
        if len(data) > max_list:
            capped.append({"_truncated": f"{len(data) - max_list} items omitted"})
        return capped
    elif isinstance(data, dict):
        return {k: cap_data(v, max_str, max_list) for k, v in data.items()}
    return data


def _probe_capsule_session_env(
    stream_id: str | None, agent: str | None
) -> dict[str, Any]:
    resolved_stream = stream_id or os.environ.get("SESSION_STREAM_ID")
    resolved_agent = (
        agent
        or os.environ.get("SESSION_HANDOFF_AGENT")
        or os.environ.get("AGENT")
        or os.environ.get("X_AGENT")
    )
    try:
        plane_mode: str = resolve_plane_mode(None)
    except Exception:
        # Fail-open: never crash the board on a bad env/config value.
        plane_mode = "off"
    return {
        "stream_id": resolved_stream,
        "agent": resolved_agent,
        "transport": os.environ.get("LU_AGENT_COMM_TRANSPORT", "acp"),
        "plane_mode": plane_mode,
        "capsule_id": os.environ.get("CAPSULE_ID"),
        "session_id": os.environ.get("SESSION_ID"),
        "task_id": os.environ.get("TASK_ID"),
        "correlation_id": os.environ.get("CORRELATION_ID"),
        "user": os.environ.get("USER"),
    }


def _probe_plane_status(root: Path | None, repo_root: Path | None) -> dict[str, Any]:
    return read_plane_status(
        repo_root=repo_root,
        root=root,
        recent_limit=5,
    )


def _resolve_broker_db_ro(root: Path | None, repo_root: Path | None) -> Path:
    from scripts.fleet_comms.cli import _default_message_db

    db_env = os.environ.get("AB_DB_PATH")
    if db_env:
        return Path(db_env).expanduser()
    return _default_message_db()


def _probe_backlog_and_dead_letters(
    root: Path | None, repo_root: Path | None
) -> dict[str, Any]:
    """Backlog + dead-letters; prefer authority tables when plane mode is authority."""
    source = resolve_metrics_source()
    plane_root = root if root is not None else default_plane_root(repo_root=repo_root)

    if source == "authority":
        db_path = plane_root / "comms.sqlite3"
        if not db_path.is_file():
            return {
                "source": source,
                "db_missing": True,
                "db_path": str(db_path),
                "backlog_total": 0,
                "dead_letters_total": 0,
            }
        backlog = collect_delivery_backlog_authority(
            db_path, limit=5, exclude_retired=True
        )
        dead_letters = collect_dead_letters_authority(db_path, limit=5)
        label = "authority"
    else:
        db_path = _resolve_broker_db_ro(root, repo_root)
        if not db_path.is_file():
            return {
                "source": "legacy",
                "db_missing": True,
                "db_path": str(db_path),
                "backlog_total": 0,
                "dead_letters_total": 0,
            }
        backlog = collect_delivery_backlog(db_path, limit=5, exclude_retired=True)
        dead_letters = collect_dead_letters(db_path, limit=5)
        label = "legacy"

    return {
        "source": label,
        "db_path": str(db_path),
        "db_exists": True,
        "backlog_total": backlog.get("total", 0),
        "backlog_by_agent": backlog.get("by_agent", {}),
        "backlog_rows": backlog.get("rows", [])[:5],
        "dead_letters_total": dead_letters.get("total", 0),
        "dead_letters_by_reason": dead_letters.get("by_reason", {}),
        "dead_letters_rows": dead_letters.get("rows", [])[:5],
    }


def _probe_bottleneck_slice(
    root: Path | None,
    repo_root: Path | None,
    stream_id: str | None,
) -> dict[str, Any]:
    plane_root = root if root is not None else default_plane_root(repo_root=repo_root)
    plane_db = plane_root / "comms.sqlite3"
    tasks_dir = (repo_root or Path.cwd()) / "batch_state" / "tasks"

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir,
        plane_db=plane_db,
        github_lookup=lambda repo, pr_number: (None, "skipped_for_cold_start"),
    )
    streams = payload.get("by_stream_epic") or {}

    if stream_id and stream_id in streams:
        selected = {stream_id: streams[stream_id]}
    else:
        items = list(streams.items())[:5]
        selected = dict(items)

    return {
        "total_streams": len(streams),
        "slice": selected,
        "tasks_dir": str(tasks_dir),
        "plane_db": str(plane_db),
        "db_missing": not plane_db.is_file(),
    }



def _get_local_git_info() -> dict[str, Any]:
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1.0,
        ).strip()
        head = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1.0,
        ).strip()
        return {"branch": branch, "head": head}
    except Exception as exc:
        return {"error": str(exc)}


def _probe_orient_lean(
    base_url: str = "http://localhost:8765",
    timeout_s: float = 0.5,
) -> ProbeResult:
    start = time.perf_counter()
    # drive-epic contract: lean orient (do not pull the full briefing).
    url = f"{base_url}/api/orient?lean=true"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "fleet-comms-cold-start/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = (time.perf_counter() - start) * 1000.0
            return ProbeResult(
                status="ok",
                elapsed_ms=elapsed,
                data={"api_reachable": True, "orient": data},
            )
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000.0
        git_info = _get_local_git_info()
        # Optional Monitor probe: skip (do not poison board_status).
        return ProbeResult(
            status="skipped",
            elapsed_ms=elapsed,
            error=f"monitor_api_unreachable: {type(exc).__name__}",
            data={
                "api_reachable": False,
                "reason": "monitor_unreachable",
                "git_fallback": git_info,
            },
        )


def _probe_issues_streams_membership(orient_result: ProbeResult) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if orient_result.status == "ok" and isinstance(orient_result.data, dict):
        orient_data = orient_result.data.get("orient") or {}
        raw_issues = orient_data.get("issues") or []
        for issue in raw_issues[:5]:
            if isinstance(issue, dict):
                issues.append({
                    "number": issue.get("number"),
                    "title": str(issue.get("title", ""))[:80],
                    "state": issue.get("state"),
                })

    return {
        "top_issues": issues,
        "issue_count": len(issues),
    }


def _resolve_session_streams_db(repo_root: Path | None) -> Path:
    """Resolve primary-checkout session-streams DB (not worktree-local Path.cwd())."""
    if HAS_SESSION_STREAMS and default_database_path is not None:
        try:
            return default_database_path(repo_root)
        except Exception:
            pass

    active = (repo_root or Path.cwd()).resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=active,
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
        common_dir_text = result.stdout.strip()
        if result.returncode == 0 and common_dir_text:
            common_dir = Path(common_dir_text)
            if common_dir.is_absolute() and common_dir.name == ".git":
                return common_dir.parent.resolve() / SESSION_STREAMS_REL
    except Exception:
        pass
    return active / SESSION_STREAMS_REL


def _probe_session_streams_and_handoff(
    repo_root: Path | None,
    stream_id: str | None,
) -> ProbeResult:
    start = time.perf_counter()
    if not stream_id:
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="skipped",
            elapsed_ms=elapsed,
            data={"reason": "no_stream_id_provided"},
        )

    if not HAS_SESSION_STREAMS:
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="skipped",
            elapsed_ms=elapsed,
            error="session_streams_module_unavailable",
            data={"stream_id": stream_id, "reason": "module_unavailable"},
        )

    db_path = _resolve_session_streams_db(repo_root)
    if not db_path.is_file():
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="skipped",
            elapsed_ms=elapsed,
            data={
                "stream_id": stream_id,
                "db_exists": False,
                "db_path": str(db_path),
                "reason": "session_streams_db_missing",
            },
        )

    try:
        store = SessionStreamStore(SessionStreamDatabase(db_path))
        handoff_data = diagnose_handoff(store, stream_id).as_dict()
        digest = store.load_digest(stream_id, limit=5)
        digest_data = {
            "pinned_count": len(digest.pinned),
            "recent_count": len(digest.recent),
            "pinned": [entry_as_dict(e) for e in digest.pinned[:5]],
            "recent": [entry_as_dict(e) for e in digest.recent[:5]],
        }
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="ok",
            elapsed_ms=elapsed,
            data={
                "stream_id": stream_id,
                "db_exists": True,
                "db_path": str(db_path),
                "handoff": handoff_data,
                "digest": digest_data,
            },
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="degraded",
            elapsed_ms=elapsed,
            error=str(exc),
            data={"stream_id": stream_id, "db_exists": True, "db_path": str(db_path)},
        )


def _inbox_agent_candidates(agent: str) -> list[str]:
    """Exact agent first; cheap slash/hyphen base aliases as fallbacks."""
    candidates = [agent]
    if "/" in agent:
        base = agent.split("/", 1)[0].strip()
        if base and base not in candidates:
            candidates.append(base)
    if "-" in agent:
        base = agent.split("-", 1)[0].strip()
        if base and base not in candidates:
            candidates.append(base)
    return candidates


def _probe_inbox_authority(
    plane_db: Path,
    agent: str,
) -> dict[str, Any]:
    """Body-free pending inbox rows from authority_deliveries (queued/running)."""
    import sqlite3

    if not plane_db.is_file():
        return {
            "source": "authority",
            "agent": agent,
            "inbox_pending_count": 0,
            "db_missing": True,
            "db_path": str(plane_db),
            "recent_deliveries": [],
        }

    placeholders = ",".join("?" for _ in _AUTHORITY_BACKLOG_STATES)
    matched_agent = agent
    deliveries: list[dict[str, Any]] = []
    total = 0

    conn = sqlite3.connect(f"file:{plane_db.resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        if not _table_exists(conn, "authority_deliveries"):
            return {
                "source": "authority",
                "agent": agent,
                "inbox_pending_count": 0,
                "db_path": str(plane_db),
                "table_missing": True,
                "recent_deliveries": [],
            }
        for candidate in _inbox_agent_candidates(agent):
            count_row = conn.execute(
                f"""
                SELECT COUNT(*) AS cnt FROM authority_deliveries
                WHERE recipient = ? AND state IN ({placeholders})
                """,
                (candidate, *_AUTHORITY_BACKLOG_STATES),
            ).fetchone()
            candidate_total = int(count_row["cnt"] if count_row else 0)
            if candidate_total == 0:
                continue
            rows = conn.execute(
                f"""
                SELECT delivery_id, message_id, recipient, state,
                       attempt_count, created_at, updated_at
                FROM authority_deliveries
                WHERE recipient = ? AND state IN ({placeholders})
                ORDER BY COALESCE(updated_at, created_at, '') DESC
                LIMIT 5
                """,
                (candidate, *_AUTHORITY_BACKLOG_STATES),
            ).fetchall()
            matched_agent = candidate
            total = candidate_total
            deliveries = [
                {
                    "delivery_id": r["delivery_id"],
                    "message_id": r["message_id"],
                    "recipient": r["recipient"],
                    "to_agent": r["recipient"],
                    "state": r["state"],
                    "status": r["state"],
                    "attempt_count": int(r["attempt_count"] or 0),
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                }
                for r in rows
            ]
            break
    finally:
        conn.close()

    return {
        "source": "authority",
        "agent": agent,
        "matched_agent": matched_agent,
        "inbox_pending_count": total,
        "db_path": str(plane_db),
        "recent_deliveries": deliveries,
    }


def _probe_inbox_legacy(db_path: Path, agent: str) -> dict[str, Any]:
    """Body-free pending inbox from legacy broker deliveries (schema-tolerant)."""
    import sqlite3

    if not db_path.is_file():
        return {
            "source": "legacy",
            "agent": agent,
            "inbox_pending_count": 0,
            "db_missing": True,
            "db_path": str(db_path),
            "recent_deliveries": [],
        }

    status_filter = ("pending", "dispatched", "processing")
    status_placeholders = ",".join("?" for _ in status_filter)
    matched_agent = agent
    deliveries: list[dict[str, Any]] = []
    total = 0

    conn = sqlite3.connect(f"file:{db_path.resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        if not _table_exists(conn, "deliveries"):
            return {
                "source": "legacy",
                "agent": agent,
                "inbox_pending_count": 0,
                "db_path": str(db_path),
                "table_missing": True,
                "recent_deliveries": [],
            }
        cols = _column_names(conn, "deliveries")
        agent_col = "to_agent" if "to_agent" in cols else (
            "recipient" if "recipient" in cols else None
        )
        if agent_col is None:
            return {
                "source": "legacy",
                "agent": agent,
                "inbox_pending_count": 0,
                "db_path": str(db_path),
                "schema_unsupported": True,
                "recent_deliveries": [],
            }
        if "status" not in cols:
            return {
                "source": "legacy",
                "agent": agent,
                "inbox_pending_count": 0,
                "db_path": str(db_path),
                "schema_unsupported": True,
                "recent_deliveries": [],
            }

        select_parts = [
            c
            for c in (
                "delivery_id",
                "message_id",
                agent_col,
                "status",
                "attempt_count",
                "dispatched_at",
                "created_at",
            )
            if c in cols
        ]
        order_col = (
            "dispatched_at"
            if "dispatched_at" in cols
            else ("created_at" if "created_at" in cols else select_parts[0])
        )

        join_sql = ""
        extra_select: list[str] = []
        if _table_exists(conn, "channel_messages") and "message_id" in cols:
            cm_cols = _column_names(conn, "channel_messages")
            join_sql = " LEFT JOIN channel_messages cm ON cm.message_id = d.message_id"
            for alias, expr in (
                ("channel", "cm.channel" if "channel" in cm_cols else None),
                ("sender", "cm.from_agent" if "from_agent" in cm_cols else None),
                ("kind", "cm.kind" if "kind" in cm_cols else None),
                (
                    "created_at",
                    "cm.created_at"
                    if "created_at" in cm_cols and "created_at" not in cols
                    else None,
                ),
            ):
                if expr is not None:
                    extra_select.append(f"{expr} AS {alias}")

        select_sql = ", ".join([f"d.{c}" for c in select_parts] + extra_select)

        for candidate in _inbox_agent_candidates(agent):
            count_row = conn.execute(
                f"""
                SELECT COUNT(*) AS cnt FROM deliveries
                WHERE {agent_col} = ? AND status IN ({status_placeholders})
                """,
                (candidate, *status_filter),
            ).fetchone()
            candidate_total = int(count_row["cnt"] if count_row else 0)
            if candidate_total == 0:
                continue
            rows = conn.execute(
                f"""
                SELECT {select_sql}
                FROM deliveries d
                {join_sql}
                WHERE d.{agent_col} = ? AND d.status IN ({status_placeholders})
                ORDER BY COALESCE(d.{order_col}, '') DESC
                LIMIT 5
                """,
                (candidate, *status_filter),
            ).fetchall()
            matched_agent = candidate
            total = candidate_total
            deliveries = []
            for r in rows:
                row = dict(r)
                # Normalize recipient alias without inventing bodies.
                if "to_agent" not in row and agent_col in row:
                    row["to_agent"] = row[agent_col]
                if "recipient" not in row and agent_col in row:
                    row["recipient"] = row[agent_col]
                deliveries.append(row)
            break
    finally:
        conn.close()

    return {
        "source": "legacy",
        "agent": agent,
        "matched_agent": matched_agent,
        "inbox_pending_count": total,
        "db_path": str(db_path),
        "recent_deliveries": deliveries,
    }


def _probe_inbox(
    root: Path | None,
    repo_root: Path | None,
    agent: str | None,
) -> ProbeResult:
    start = time.perf_counter()
    if not agent:
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="skipped",
            elapsed_ms=elapsed,
            data={"reason": "no_agent_specified"},
        )

    try:
        source = resolve_metrics_source()
        plane_root = root if root is not None else default_plane_root(repo_root=repo_root)
        if source == "authority":
            plane_db = plane_root / "comms.sqlite3"
            if plane_db.is_file():
                data = _probe_inbox_authority(plane_db, agent)
            else:
                # Authority preferred but plane DB missing → legacy fallback.
                data = _probe_inbox_legacy(_resolve_broker_db_ro(root, repo_root), agent)
                data["authority_db_missing"] = True
        else:
            data = _probe_inbox_legacy(_resolve_broker_db_ro(root, repo_root), agent)

        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(status="ok", elapsed_ms=elapsed, data=data)
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="degraded",
            elapsed_ms=elapsed,
            error=str(exc),
            data={"agent": agent},
        )


def _probe_gh_pr_list() -> ProbeResult:
    start = time.perf_counter()
    gh_bin = shutil.which("gh")
    if not gh_bin:
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="skipped",
            elapsed_ms=elapsed,
            data={"gh_available": False, "reason": "gh_binary_not_found"},
        )

    try:
        proc = subprocess.run(
            [
                gh_bin,
                "pr",
                "list",
                "--limit",
                "5",
                "--json",
                "number,title,headRefName,state",
            ],
            capture_output=True,
            text=True,
            timeout=2.0,
        )
        elapsed = (time.perf_counter() - start) * 1000.0
        if proc.returncode == 0:
            prs = json.loads(proc.stdout)
            return ProbeResult(
                status="ok",
                elapsed_ms=elapsed,
                data={"gh_available": True, "prs": prs[:5]},
            )
        else:
            return ProbeResult(
                status="degraded",
                elapsed_ms=elapsed,
                error=proc.stderr.strip()[:200]
                or f"gh returned code {proc.returncode}",
                data={"gh_available": True, "prs": []},
            )
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="degraded",
            elapsed_ms=elapsed,
            error=f"{type(exc).__name__}: {exc}",
            data={"gh_available": True, "prs": []},
        )


def _probe_needle_search(
    needle: str | None,
    probes_data: dict[str, Any],
) -> ProbeResult:
    start = time.perf_counter()
    if not needle or not needle.strip():
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="skipped",
            elapsed_ms=elapsed,
            data={"needle": None},
        )

    token = needle.strip().lower()
    matches: list[dict[str, str]] = []

    def search_obj(path: str, obj: Any) -> None:
        if len(matches) >= 5:
            return
        if isinstance(obj, str):
            if token in obj.lower():
                matches.append({"path": path, "snippet": obj[:150]})
        elif isinstance(obj, dict):
            for k, v in obj.items():
                search_obj(f"{path}.{k}" if path else k, v)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_obj(f"{path}[{i}]", item)

    search_obj("", probes_data)

    elapsed = (time.perf_counter() - start) * 1000.0
    return ProbeResult(
        status="ok",
        elapsed_ms=elapsed,
        data={
            "needle": needle,
            "match_count": len(matches),
            "matches": matches,
        },
    )


def compute_board_status(probes: dict[str, Any]) -> str:
    """Headline status from load-bearing probes only.

    Optional probes (orient_lean, gh_pr_list, needle_search, …) never flip the
    headline. session_streams_and_handoff is load-bearing only when the DB exists
    and the probe degraded/errored (missing DB / no stream_id stay skipped).
    """
    for name in LOAD_BEARING_PROBES:
        status = (probes.get(name) or {}).get("status")
        if status in {"degraded", "error"}:
            return "degraded"

    ss = probes.get("session_streams_and_handoff") or {}
    if ss.get("status") in {"degraded", "error"}:
        data = ss.get("data") or {}
        if data.get("db_exists"):
            return "degraded"
    return "ok"


def build_cold_start_board(
    stream_id: str | None = None,
    agent: str | None = None,
    needle: str | None = None,
    root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build driver cold start board with fail-open diagnostic probes."""
    r_root = repo_root or Path.cwd()
    p_root = root if root is not None else default_plane_root(repo_root=r_root)

    env_probe = run_fail_open_probe(
        "capsule_session_env", _probe_capsule_session_env, stream_id, agent
    )

    res_env = env_probe.data or {}
    eff_stream_id = stream_id or res_env.get("stream_id")
    eff_agent = agent or res_env.get("agent")

    plane_probe = run_fail_open_probe(
        "plane_status", _probe_plane_status, p_root, r_root
    )

    backlog_probe = run_fail_open_probe(
        "backlog_and_dead_letters",
        _probe_backlog_and_dead_letters,
        p_root,
        r_root,
    )

    bottleneck_probe = run_fail_open_probe(
        "bottleneck_slice",
        _probe_bottleneck_slice,
        p_root,
        r_root,
        eff_stream_id,
    )

    orient_probe = _probe_orient_lean()

    issues_probe = run_fail_open_probe(
        "issues_streams_membership",
        _probe_issues_streams_membership,
        orient_probe,
    )

    session_streams_probe = _probe_session_streams_and_handoff(
        r_root, eff_stream_id
    )

    inbox_probe = run_fail_open_probe(
        "inbox_check", _probe_inbox, p_root, r_root, eff_agent
    )

    gh_probe = run_fail_open_probe("gh_pr_list", _probe_gh_pr_list)

    probes: dict[str, Any] = {
        "capsule_session_env": env_probe.to_dict(),
        "plane_status": plane_probe.to_dict(),
        "backlog_and_dead_letters": backlog_probe.to_dict(),
        "bottleneck_slice": bottleneck_probe.to_dict(),
        "orient_lean": orient_probe.to_dict(),
        "issues_streams_membership": issues_probe.to_dict(),
        "session_streams_and_handoff": session_streams_probe.to_dict(),
        "inbox_check": inbox_probe.to_dict(),
        "gh_pr_list": gh_probe.to_dict(),
    }

    needle_probe = run_fail_open_probe(
        "needle_search", _probe_needle_search, needle, probes
    )
    probes["needle_search"] = needle_probe.to_dict()

    board_status = compute_board_status(probes)

    capped_probes = cap_data(probes, max_str=MAX_STRING_LEN, max_list=MAX_LIST_LEN)

    board: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "board_status": board_status,
        "stream_id": eff_stream_id,
        "agent": eff_agent,
        "needle": needle,
        "probes": capped_probes,
    }

    json_bytes = json.dumps(board, indent=2).encode("utf-8")
    if len(json_bytes) > MAX_BOARD_BYTES:
        stricter_probes = cap_data(probes, max_str=100, max_list=3)
        board["probes"] = stricter_probes
        board["_board_truncated"] = True

    return board


def _summary_fields(board_data: dict[str, Any]) -> dict[str, str]:
    """Extract the six lead Summary fields drivers see first."""
    probes = board_data.get("probes") or {}
    plane_data = (probes.get("plane_status") or {}).get("data") or {}
    env_data = (probes.get("capsule_session_env") or {}).get("data") or {}
    inbox_data = (probes.get("inbox_check") or {}).get("data") or {}

    plane_mode = plane_data.get("mode") or env_data.get("plane_mode") or "unknown"
    schema = plane_data.get("schema") or {}
    schema_version: Any
    if isinstance(schema, dict):
        schema_version = schema.get("applied_version")
        if schema_version is None:
            schema_version = schema.get("known_version")
        if schema_version is None:
            schema_version = schema.get("version")
    else:
        schema_version = schema
    if schema_version is None:
        schema_version = "unknown"

    inbox_pending = inbox_data.get("inbox_pending_count")
    if inbox_pending is None:
        inbox_pending = "n/a"

    return {
        "plane_mode": str(plane_mode),
        "schema_version": str(schema_version),
        "inbox_pending": str(inbox_pending),
        "board_status": str(board_data.get("board_status", "unknown")),
        "stream_id": str(board_data.get("stream_id") or "N/A"),
        "agent": str(board_data.get("agent") or "N/A"),
    }


def render_markdown_board(board_data: dict[str, Any]) -> str:
    """Render board data dictionary as a readable Markdown briefing."""
    lines: list[str] = []
    summary = _summary_fields(board_data)
    ts = board_data.get("timestamp") or "N/A"

    lines.append("# Driver Cold Start Board\n")
    lines.append("## Summary\n")
    lines.append(f"- **plane_mode:** `{summary['plane_mode']}`")
    lines.append(f"- **schema_version:** `{summary['schema_version']}`")
    lines.append(f"- **inbox_pending:** `{summary['inbox_pending']}`")
    lines.append(f"- **board_status:** `{summary['board_status']}`")
    lines.append(f"- **stream_id:** `{summary['stream_id']}`")
    lines.append(f"- **agent:** `{summary['agent']}`")
    lines.append("")
    lines.append(f"- **Timestamp:** `{ts}`")

    needle = board_data.get("needle")
    if needle:
        lines.append(f"- **Needle:** `{needle}`")
    lines.append("")

    lines.append("## Diagnostic Probes\n")
    probes = board_data.get("probes") or {}

    for name, pdict in probes.items():
        p_status = pdict.get("status", "unknown")
        p_time = pdict.get("elapsed_ms", 0.0)
        lines.append(f"### `{name}` ({p_status}, {p_time}ms)")
        if pdict.get("error"):
            lines.append(f"- **Error:** `{pdict['error']}`")
        p_data = pdict.get("data")
        if p_data is not None:
            if isinstance(p_data, dict):
                for k, v in p_data.items():
                    lines.append(f"- **{k}:** `{v}`")
            else:
                lines.append(f"- `{p_data}`")
        lines.append("")

    if board_data.get("_board_truncated"):
        lines.append("_Note: Board content was truncated to fit 16KiB limit._\n")

    output = "\n".join(lines) + "\n"
    if len(output.encode("utf-8")) > MAX_BOARD_BYTES:
        output = (
            output.encode("utf-8")[:MAX_BOARD_BYTES].decode("utf-8", errors="ignore")
            + "\n...[truncated]\n"
        )
    return output
