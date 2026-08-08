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
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

from scripts.fleet_comms.efficiency_metrics import (
    collect_dead_letters,
    collect_delivery_backlog,
    collect_stream_bottleneck_metrics,
)
from scripts.fleet_comms.message_plane import default_plane_root, read_plane_status

try:
    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.handoff import diagnose_handoff
    from agents_extensions.shared.session_streams.model import entry_as_dict
    from agents_extensions.shared.session_streams.store import SessionStreamStore

    HAS_SESSION_STREAMS = True
except ImportError:
    HAS_SESSION_STREAMS = False

MAX_STRING_LEN = 200
MAX_LIST_LEN = 5
MAX_BOARD_BYTES = 16384  # 16KiB


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
    return {
        "stream_id": resolved_stream,
        "agent": resolved_agent,
        "transport": os.environ.get("LU_AGENT_COMM_TRANSPORT", "acp"),
        "plane_mode": os.environ.get("FLEET_COMMS_PLANE_MODE", "off"),
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
    db_path = _resolve_broker_db_ro(root, repo_root)

    if not db_path.is_file():
        return {
            "db_missing": True,
            "db_path": str(db_path),
            "backlog_total": 0,
            "dead_letters_total": 0,
        }

    backlog = collect_delivery_backlog(db_path, limit=5, exclude_retired=True)
    dead_letters = collect_dead_letters(db_path, limit=5)
    return {
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
    url = f"{base_url}/api/orient"
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
        return ProbeResult(
            status="degraded",
            elapsed_ms=elapsed,
            error=f"monitor_api_unreachable: {type(exc).__name__}",
            data={"api_reachable": False, "git_fallback": git_info},
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
            status="degraded",
            elapsed_ms=elapsed,
            error="session_streams_module_unavailable",
            data={"stream_id": stream_id},
        )

    r_root = repo_root or Path.cwd()
    db_path = r_root / ".agent" / "session-streams" / "v1" / "session-streams.sqlite3"
    if not db_path.is_file():
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="degraded",
            elapsed_ms=elapsed,
            data={
                "stream_id": stream_id,
                "db_exists": False,
                "db_path": str(db_path),
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
            data={"stream_id": stream_id, "db_exists": True},
        )


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

    db_path = _resolve_broker_db_ro(root, repo_root)
    if not db_path.is_file():
        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="ok",
            elapsed_ms=elapsed,
            data={"agent": agent, "inbox_pending_count": 0, "db_missing": True},
        )

    try:
        import sqlite3

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """SELECT message_id, channel, sender, kind, created_at
                   FROM deliveries
                   WHERE recipient = ? AND status IN ('pending', 'dispatched')
                   ORDER BY created_at DESC LIMIT 5""",
                (agent,),
            ).fetchall()
            deliveries = [dict(r) for r in rows]
            count_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM deliveries WHERE recipient = ? AND status IN ('pending', 'dispatched')",
                (agent,),
            ).fetchone()
            total = count_row["cnt"] if count_row else len(deliveries)
        finally:
            conn.close()

        elapsed = (time.perf_counter() - start) * 1000.0
        return ProbeResult(
            status="ok",
            elapsed_ms=elapsed,
            data={
                "agent": agent,
                "inbox_pending_count": total,
                "recent_deliveries": deliveries,
            },
        )
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

    statuses = [p["status"] for p in probes.values()]
    board_status = (
        "degraded" if ("error" in statuses or "degraded" in statuses) else "ok"
    )

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


def render_markdown_board(board_data: dict[str, Any]) -> str:
    """Render board data dictionary as a readable Markdown briefing."""
    lines: list[str] = []
    status = str(board_data.get("board_status", "unknown")).upper()
    stream_id = board_data.get("stream_id") or "N/A"
    agent = board_data.get("agent") or "N/A"
    ts = board_data.get("timestamp") or "N/A"

    lines.append("# Driver Cold Start Board\n")
    lines.append(f"- **Status:** `{status}`")
    lines.append(f"- **Timestamp:** `{ts}`")
    lines.append(f"- **Stream ID:** `{stream_id}`")
    lines.append(f"- **Agent:** `{agent}`")

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
