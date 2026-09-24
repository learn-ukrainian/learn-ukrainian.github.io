"""Sol PR-M: efficiency metrics from durable broker timestamps (no content).

WP-C (#cold-start-opt): when the message plane is ``authority``, backlog /
dead-letters / metrics prefer Fleet Comms authority tables (RO). Legacy broker
collectors stay byte-compatible; callers add an additive ``source`` label.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from scripts.control_plane.storage import (
    Authority,
    ControlPlaneError,
    StoreId,
    assert_component_supported,
    resolve_authority,
)
from scripts.control_plane.storage import connect as cp_connect
from scripts.fleet_comms.message_plane import resolve_plane_mode
from scripts.fleet_comms.opsec_store import batch_tasks_store, comms_plane_store
from scripts.orchestration.task_record_store import iter_task_records

# Alert thresholds are intentionally reported, not enforced here. #5646 owns
# consuming them. Dispatch uses the delegate default floor of 7,200 seconds.
DISPATCH_BOTTLENECK_THRESHOLD_S = 7_200
FORMAL_CF_PUBLICATION_THRESHOLD_S = 3_600
GATE_TO_MERGE_THRESHOLD_S = 3_600

# ``mergedAt`` is immutable once GitHub sets it. The plane connection opened
# below is read-only and must not grow a cache table, so facts live in a JSON
# file under ``batch_state/``. A null ``mergedAt`` is not final (the PR can
# still merge) and is never stored. Closed-unmerged PRs are left uncached
# because this lookup does not fetch ``closedAt``.
_MERGE_CACHE_ENV = "FLEET_COMMS_PR_MERGE_CACHE"
_MERGE_CACHE_REL = Path("batch_state") / "fleet-comms" / "pr-merge-facts.json"
_GRAPHQL_BATCH_SIZE = 50
_GH_TIMEOUT_S = 30
_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

MetricsSource = Literal["authority", "legacy", "legacy_forced"]
_AUTHORITY_BACKLOG_STATES = ("queued", "running")
_RETIRED_AGENTS = frozenset({"gemini"})


@contextmanager
def _connect_legacy(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Open a read path connection and always close it (sqlite3 `with` only commits)."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class EfficiencyMetricsReadError(ControlPlaneError):
    """Authority metrics could not be read; contains no driver details or content."""


def _authority_file_missing(db_path: Path) -> bool:
    """Only file-backed authorities depend on a local database file."""
    return resolve_authority(StoreId.FLEET_COMMS) is not Authority.PG and not db_path.is_file()


@contextmanager
def _connect_ro(db_path: Path) -> Iterator[Any]:
    """Open the configured authority read-only, without creating schema or files."""
    import psycopg
    from psycopg.rows import dict_row

    authority = assert_component_supported(StoreId.FLEET_COMMS, "efficiency_metrics")
    if authority is not Authority.PG and not db_path.is_file():
        raise FileNotFoundError(db_path)
    conn = cp_connect(StoreId.FLEET_COMMS, path=db_path, read_only=True)
    try:
        if authority is Authority.PG:
            conn.row_factory = dict_row
            conn.autocommit = True
            conn.execute("SET TIME ZONE 'UTC'")
        else:
            conn.row_factory = sqlite3.Row
        yield conn
    except psycopg.Error as exc:
        raise EfficiencyMetricsReadError("control-plane store 'fleet_comms' metrics read failed") from exc
    finally:
        conn.close()


def _placeholder(conn: Any) -> str:
    return "?" if isinstance(conn, sqlite3.Connection) else "%s"


def _table_exists(conn: Any, name: str) -> bool:
    if isinstance(conn, sqlite3.Connection):
        query = "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?"
    else:
        query = "SELECT 1 FROM pg_class WHERE oid = to_regclass(%s) AND relkind IN ('r', 'p')"
    exists = conn.execute(query, (name,)).fetchone() is not None
    if not exists and not isinstance(conn, sqlite3.Connection):
        raise EfficiencyMetricsReadError("control-plane store 'fleet_comms' metrics table unavailable")
    return exists


def _column_names(conn: Any, table: str) -> set[str]:
    if isinstance(conn, sqlite3.Connection):
        return {str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    return {
        str(r["attname"])
        for r in conn.execute(
            "SELECT attname FROM pg_attribute WHERE attrelid = to_regclass(%s) "
            "AND attnum > 0 AND NOT attisdropped",
            (table,),
        ).fetchall()
    }


def _delivery_latency(
    conn: Any, *, table: str, start: str, end: str, delivered_only: bool = False,
) -> dict[str, Any] | None:
    """Aggregate durable timestamps; identifiers are collector-owned constants."""
    if isinstance(conn, sqlite3.Connection):
        duration = f"(julianday({end}) - julianday({start})) * 86400.0"
    else:
        duration = f"EXTRACT(EPOCH FROM ({end}::timestamptz - {start}::timestamptz))"
    state_filter = "AND status = 'delivered'" if delivered_only else ""
    row = conn.execute(
        f"""
        SELECT COUNT(*) AS n, AVG({duration}) AS avg_s,
               MIN({duration}) AS min_s, MAX({duration}) AS max_s
        FROM {table}
        WHERE {end} IS NOT NULL AND {end} != ''
          AND {start} IS NOT NULL AND {start} != ''
          {state_filter}
        """
    ).fetchone()
    if not row or not row["n"]:
        return None
    return {
        "n": int(row["n"]),
        "avg": round(float(row["avg_s"] or 0.0), 3),
        "min": round(float(row["min_s"] or 0.0), 3),
        "max": round(float(row["max_s"] or 0.0), 3),
    }


def resolve_metrics_source(*, force_legacy: bool = False) -> MetricsSource:
    """Choose metrics read source from plane mode and optional ``--legacy`` force."""
    if force_legacy:
        return "legacy_forced"
    if resolve_plane_mode() == "authority":
        return "authority"
    return "legacy"


def collect_delivery_backlog(
    db_path: Path,
    *,
    limit: int = 100,
    exclude_retired: bool = True,
) -> dict[str, Any]:
    """Pending/dispatched delivery backlog without message bodies."""
    retired = set(_RETIRED_AGENTS)
    with _connect_legacy(db_path) as conn:
        if not _table_exists(conn, "deliveries"):
            return {"total": 0, "by_agent": {}, "by_status": {}, "rows": []}
        cols = _column_names(conn, "deliveries")
        # Schema varies across migrations; only SELECT columns that exist.
        select_cols = [
            c
            for c in (
                "delivery_id",
                "message_id",
                "to_agent",
                "status",
                "attempt_count",
                "dispatched_at",
                "created_at",
            )
            if c in cols
        ]
        if not select_cols:
            return {"total": 0, "by_agent": {}, "by_status": {}, "rows": []}
        order_col = (
            "dispatched_at"
            if "dispatched_at" in cols
            else ("created_at" if "created_at" in cols else select_cols[0])
        )
        status_filter = "('pending', 'dispatched')"
        rows = conn.execute(
            f"""
            SELECT {", ".join(select_cols)}
            FROM deliveries
            WHERE status IN {status_filter}
            ORDER BY COALESCE({order_col}, '') DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        by_agent: dict[str, int] = {}
        by_status: dict[str, int] = {}
        out_rows: list[dict[str, Any]] = []
        for r in rows:
            agent = str(r["to_agent"] if "to_agent" in cols else "") or ""
            if exclude_retired and agent in retired:
                continue
            status = str(r["status"] if "status" in cols else "") or ""
            by_agent[agent] = by_agent.get(agent, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            out_rows.append(
                {
                    "delivery_id": r["delivery_id"] if "delivery_id" in cols else None,
                    "message_id": r["message_id"] if "message_id" in cols else None,
                    "to_agent": agent,
                    "status": status,
                    "attempt_count": r["attempt_count"] if "attempt_count" in cols else 0,
                    "dispatched_at": r["dispatched_at"] if "dispatched_at" in cols else None,
                }
            )
        return {
            "total": len(out_rows),
            "by_agent": by_agent,
            "by_status": by_status,
            "exclude_retired": sorted(retired) if exclude_retired else [],
            "rows": out_rows,
        }


def collect_dead_letters(db_path: Path, *, limit: int = 100) -> dict[str, Any]:
    """Dead-letter counts and metadata rows (no message content)."""
    with _connect_legacy(db_path) as conn:
        if not _table_exists(conn, "dead_letters"):
            return {"total": 0, "by_reason": {}, "rows": []}
        total = conn.execute("SELECT COUNT(*) AS c FROM dead_letters").fetchone()["c"]
        by_reason_rows = conn.execute(
            "SELECT reason, COUNT(*) AS c FROM dead_letters GROUP BY reason ORDER BY c DESC"
        ).fetchall()
        rows = conn.execute(
            """
            SELECT dead_letter_id, request_id, delivery_id, reason, successor,
                   original_expires_at, created_at
            FROM dead_letters
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return {
            "total": int(total),
            "by_reason": {str(r["reason"]): int(r["c"]) for r in by_reason_rows},
            "rows": [dict(r) for r in rows],
        }


def collect_efficiency_metrics(db_path: Path) -> dict[str, Any]:
    """Aggregate ask/reply efficiency from durable timestamps only."""
    with _connect_legacy(db_path) as conn:
        metrics: dict[str, Any] = {
            "content_included": False,
            "deliveries": {},
            "requests": {},
            "messages_legacy": {},
            "dead_letters": 0,
            "latency_seconds": {},
        }

        if _table_exists(conn, "deliveries"):
            for r in conn.execute(
                "SELECT status, COUNT(*) AS c FROM deliveries GROUP BY status"
            ):
                metrics["deliveries"][str(r["status"])] = int(r["c"])
            latency = _delivery_latency(
                conn, table="deliveries", start="dispatched_at", end="delivered_at",
                delivered_only=True,
            )
            if latency:
                metrics["latency_seconds"]["delivery_dispatch_to_done"] = latency

        if _table_exists(conn, "requests"):
            for r in conn.execute(
                "SELECT state, COUNT(*) AS c FROM requests GROUP BY state"
            ):
                metrics["requests"][str(r["state"])] = int(r["c"])

        if _table_exists(conn, "messages"):
            msg_cols = _column_names(conn, "messages")
            # Legacy broker schema uses message_type (+ optional status lifecycle).
            # Never assume status alone — schemas without it must still return metrics.
            if "message_type" in msg_cols:
                by_type: dict[str, int] = {}
                for r in conn.execute(
                    "SELECT message_type, COUNT(*) AS c FROM messages GROUP BY message_type"
                ):
                    by_type[str(r["message_type"] or "")] = int(r["c"])
                metrics["messages_legacy"]["by_message_type"] = by_type
            if "status" in msg_cols:
                by_status: dict[str, int] = {}
                for r in conn.execute(
                    "SELECT status, COUNT(*) AS c FROM messages GROUP BY status"
                ):
                    # Truncate long free-form failure strings (not content, but keep compact).
                    key = str(r["status"] or "")
                    if len(key) > 80:
                        key = key[:77] + "..."
                    by_status[key] = int(r["c"])
                metrics["messages_legacy"]["by_status"] = by_status
            if "task_id" in msg_cols:
                pair = conn.execute(
                    """
                    SELECT COUNT(DISTINCT task_id) AS tasks
                    FROM messages
                    WHERE task_id IS NOT NULL AND task_id != ''
                    """
                ).fetchone()
                metrics["messages_legacy"]["distinct_task_ids"] = int(pair["tasks"] or 0)

        if _table_exists(conn, "dead_letters"):
            metrics["dead_letters"] = int(
                conn.execute("SELECT COUNT(*) AS c FROM dead_letters").fetchone()["c"]
            )

        # retired endpoint backlog should be zero for gemini inserts going forward
        if _table_exists(conn, "deliveries"):
            gemini_pending = conn.execute(
                """
                SELECT COUNT(*) AS c FROM deliveries
                WHERE to_agent = 'gemini' AND status IN ('pending', 'dispatched')
                """
            ).fetchone()["c"]
            metrics["retired_endpoint_pending"] = {
                "gemini": int(gemini_pending),
            }

        return metrics


def _empty_backlog(*, exclude_retired: bool) -> dict[str, Any]:
    return {
        "total": 0,
        "by_agent": {},
        "by_status": {},
        "exclude_retired": sorted(_RETIRED_AGENTS) if exclude_retired else [],
        "rows": [],
    }


def collect_delivery_backlog_authority(
    plane_db: Path,
    *,
    limit: int = 100,
    exclude_retired: bool = True,
) -> dict[str, Any]:
    """Authority-plane backlog from ``authority_deliveries`` (queued/running)."""
    if _authority_file_missing(plane_db):
        return _empty_backlog(exclude_retired=exclude_retired)
    with _connect_ro(plane_db) as conn:
        if not _table_exists(conn, "authority_deliveries"):
            return _empty_backlog(exclude_retired=exclude_retired)
        placeholders = ",".join(_placeholder(conn) for _ in _AUTHORITY_BACKLOG_STATES)
        rows = conn.execute(
            f"""
            SELECT delivery_id, message_id, recipient, state, attempt_count,
                   created_at, updated_at
            FROM authority_deliveries
            WHERE state IN ({placeholders})
            ORDER BY COALESCE(updated_at, created_at, '') DESC
            LIMIT {_placeholder(conn)}
            """,
            (*_AUTHORITY_BACKLOG_STATES, limit),
        ).fetchall()
        by_agent: dict[str, int] = {}
        by_status: dict[str, int] = {}
        out_rows: list[dict[str, Any]] = []
        for r in rows:
            agent = str(r["recipient"] or "")
            if exclude_retired and agent in _RETIRED_AGENTS:
                continue
            status = str(r["state"] or "")
            by_agent[agent] = by_agent.get(agent, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            out_rows.append(
                {
                    "delivery_id": r["delivery_id"],
                    "message_id": r["message_id"],
                    "to_agent": agent,
                    "status": status,
                    "attempt_count": int(r["attempt_count"] or 0),
                    "dispatched_at": r["updated_at"] or r["created_at"],
                }
            )
        return {
            "total": len(out_rows),
            "by_agent": by_agent,
            "by_status": by_status,
            "exclude_retired": sorted(_RETIRED_AGENTS) if exclude_retired else [],
            "rows": out_rows,
        }


def collect_dead_letters_authority(plane_db: Path, *, limit: int = 100) -> dict[str, Any]:
    """Authority-plane dead letters from ``authority_dead_letters`` (metadata only)."""
    empty: dict[str, Any] = {"total": 0, "by_reason": {}, "rows": []}
    if _authority_file_missing(plane_db):
        return empty
    with _connect_ro(plane_db) as conn:
        if not _table_exists(conn, "authority_dead_letters"):
            return empty
        total = conn.execute("SELECT COUNT(*) AS c FROM authority_dead_letters").fetchone()["c"]
        by_reason_rows = conn.execute(
            """
            SELECT reason_code, COUNT(*) AS c
            FROM authority_dead_letters
            GROUP BY reason_code
            ORDER BY c DESC
            """
        ).fetchall()
        rows = conn.execute(
            f"""
            SELECT dead_letter_id, delivery_id, job_id, reason_code, created_at
            FROM authority_dead_letters
            ORDER BY created_at DESC
            LIMIT {_placeholder(conn)}
            """,
            (limit,),
        ).fetchall()
        return {
            "total": int(total),
            "by_reason": {str(r["reason_code"]): int(r["c"]) for r in by_reason_rows},
            "rows": [
                {
                    "dead_letter_id": r["dead_letter_id"],
                    "delivery_id": r["delivery_id"],
                    "job_id": r["job_id"],
                    "reason": r["reason_code"],
                    "reason_code": r["reason_code"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ],
        }


def collect_efficiency_metrics_authority(plane_db: Path) -> dict[str, Any]:
    """Aggregate authority-plane delivery/job efficiency (timestamps only)."""
    metrics: dict[str, Any] = {
        "content_included": False,
        "deliveries": {},
        "jobs": {},
        "dead_letters": 0,
        "latency_seconds": {},
    }
    if _authority_file_missing(plane_db):
        return metrics
    with _connect_ro(plane_db) as conn:
        if _table_exists(conn, "authority_deliveries"):
            for r in conn.execute(
                "SELECT state, COUNT(*) AS c FROM authority_deliveries GROUP BY state"
            ):
                metrics["deliveries"][str(r["state"])] = int(r["c"])
            latency = _delivery_latency(
                conn, table="authority_deliveries", start="created_at", end="completed_at",
            )
            if latency:
                metrics["latency_seconds"]["delivery_created_to_done"] = latency
            gemini_pending = conn.execute(
                f"""
                SELECT COUNT(*) AS c FROM authority_deliveries
                WHERE recipient = 'gemini'
                  AND state IN ({",".join(_placeholder(conn) for _ in _AUTHORITY_BACKLOG_STATES)})
                """,
                _AUTHORITY_BACKLOG_STATES,
            ).fetchone()["c"]
            metrics["retired_endpoint_pending"] = {"gemini": int(gemini_pending)}

        if _table_exists(conn, "authority_jobs"):
            for r in conn.execute(
                "SELECT state, COUNT(*) AS c FROM authority_jobs GROUP BY state"
            ):
                metrics["jobs"][str(r["state"])] = int(r["c"])

        if _table_exists(conn, "authority_dead_letters"):
            metrics["dead_letters"] = int(
                conn.execute("SELECT COUNT(*) AS c FROM authority_dead_letters").fetchone()["c"]
            )

    return metrics


def _parse_timestamp(value: object) -> datetime | None:
    """Parse an ISO-8601 lifecycle timestamp as an aware UTC value."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _identity(record: dict[str, Any]) -> tuple[str | None, str | None]:
    """Read only explicit lifecycle identity fields; never infer from labels."""
    stream_epic = record.get("stream_epic")
    task_family = record.get("task_family")
    stream = str(stream_epic).strip() if stream_epic is not None else ""
    family = str(task_family).strip() if task_family is not None else ""
    return (stream or None, family or None)


def _percentile(samples: list[float], percentile: float) -> float:
    """Linearly interpolate sorted samples at index ``(n - 1) * percentile``."""
    ordered = sorted(samples)
    index = (len(ordered) - 1) * percentile
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def _span_summary(durations: list[float], backlog_ages: list[float]) -> dict[str, Any]:
    """Summarize one span without emitting individual events or content."""
    summary: dict[str, Any] = {
        "n": len(durations),
        "backlog_age_s": round(max(backlog_ages), 3) if backlog_ages else None,
        "raw": {
            "event_count": len(durations) + len(backlog_ages),
            "duration_count": len(durations),
            "unfinished_count": len(backlog_ages),
        },
        "duration_s": {},
    }
    if durations:
        summary["duration_s"] = {
            "min": round(min(durations), 3),
            "max": round(max(durations), 3),
            "avg": round(sum(durations) / len(durations), 3),
        }
        if len(durations) >= 20:
            summary["duration_s"]["p50"] = round(_percentile(durations, 0.50), 3)
            summary["duration_s"]["p95"] = round(_percentile(durations, 0.95), 3)
    return summary


def _new_buckets() -> dict[str, dict[str, list[float]]]:
    return {
        "dispatch": {"durations": [], "backlog_ages": []},
        "formal_cf_publication": {"durations": [], "backlog_ages": []},
        "gate_to_merge": {"durations": [], "backlog_ages": []},
    }


def _add_event(
    buckets: dict[str, dict[str, dict[str, list[float]]]],
    *,
    dimension: str,
    identity: str | None,
    span: str,
    duration: float | None,
    backlog_age: float | None,
) -> None:
    key = identity or "unclassified"
    group = buckets[dimension].setdefault(key, _new_buckets())
    if duration is not None:
        group[span]["durations"].append(duration)
    if backlog_age is not None:
        group[span]["backlog_ages"].append(backlog_age)


def _default_merge_cache_path() -> Path | None:
    """Shared cache on the primary checkout, or ``None`` when it cannot be anchored."""
    override = os.environ.get(_MERGE_CACHE_ENV, "").strip()
    if override:
        return Path(override).expanduser()
    try:
        from scripts.guardrails.worktree_containment import (
            NotAGitRepositoryError,
            resolve_main_root,
        )

        base = resolve_main_root(Path.cwd())
    except NotAGitRepositoryError:
        return None
    return base / _MERGE_CACHE_REL


def _fact_key(repo: str, pr_number: int) -> str:
    return f"{repo}#{pr_number}"


def _load_merge_facts(path: Path | None) -> dict[str, str]:
    """Read cached non-null merge timestamps. Missing or corrupt files are empty."""
    if path is None or not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    facts = raw.get("facts")
    if not isinstance(facts, dict):
        return {}
    loaded: dict[str, str] = {}
    for key, value in facts.items():
        if isinstance(key, str) and isinstance(value, str) and _parse_timestamp(value) is not None:
            loaded[key] = value
    return loaded


def _store_merge_facts(path: Path, facts: dict[str, str]) -> None:
    """Atomically replace the cache. A write failure leaves metrics fail-open."""
    payload = json.dumps(
        {"schema": "pr-merge-facts.v1", "facts": dict(sorted(facts.items()))},
        separators=(",", ":"),
    )
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(payload + "\n", encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            return


def _gql_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _merge_fact_query(batch: list[tuple[str, int]]) -> str:
    """One GraphQL document: repository aliases, each with ≤ the batch's PR aliases."""
    grouped: dict[str, list[int]] = {}
    for repo, number in batch:
        grouped.setdefault(repo, []).append(number)
    selections: list[str] = []
    for index, (repo, numbers) in enumerate(grouped.items()):
        owner, name = repo.split("/", 1)
        fields = " ".join(
            f"p{number}: pullRequest(number: {number}) {{ mergedAt }}" for number in numbers
        )
        selections.append(
            f'r{index}: repository(owner: "{_gql_string(owner)}", name: "{_gql_string(name)}") '
            f"{{ {fields} }}"
        )
    return "query { " + " ".join(selections) + " }"


def _run_gh(
    args: list[str], *, timeout: float = _GH_TIMEOUT_S,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _graphql_failure_message(payload: object) -> str:
    if isinstance(payload, dict):
        errors = payload.get("errors")
        if isinstance(errors, list) and errors and isinstance(errors[0], dict):
            message = errors[0].get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()[:300]
    return "graphql response missing data"


def _parse_merge_fact_payload(
    payload: object,
    batch: list[tuple[str, int]],
) -> dict[tuple[str, int], tuple[datetime | None, str | None, str | None]]:
    """Map each PR to ``(merged_at, error, cacheable_raw)``.

    ``cacheable_raw`` is set only for a parsed non-null ``mergedAt``. A JSON
    null is an open or unmerged PR: no error, and nothing to cache.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        message = _graphql_failure_message(payload)
        return {key: (None, message, None) for key in batch}

    data: dict[str, Any] = payload["data"]
    error_paths: set[tuple[str, str]] = set()
    errors = payload.get("errors")
    if isinstance(errors, list):
        for item in errors:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            if isinstance(path, list) and len(path) >= 2:
                error_paths.add((str(path[0]), str(path[1])))

    grouped: dict[str, list[int]] = {}
    for repo, number in batch:
        grouped.setdefault(repo, []).append(number)

    parsed: dict[tuple[str, int], tuple[datetime | None, str | None, str | None]] = {}
    for index, (repo, numbers) in enumerate(grouped.items()):
        repo_alias = f"r{index}"
        node = data.get(repo_alias)
        if not isinstance(node, dict):
            for number in numbers:
                parsed[(repo, number)] = (None, "graphql repository missing", None)
            continue
        for number in numbers:
            alias = f"p{number}"
            key = (repo, number)
            had_error = (repo_alias, alias) in error_paths
            if had_error or alias not in node:
                parsed[key] = (None, "graphql pull request lookup failed", None)
                continue
            pr = node[alias]
            if pr is None:
                # Explicit null and no field error: still open, or closed without a merge.
                parsed[key] = (None, None, None)
                continue
            if not isinstance(pr, dict):
                parsed[key] = (None, "graphql pull request lookup failed", None)
                continue
            raw = pr.get("mergedAt")
            if raw is None:
                parsed[key] = (None, None, None)
                continue
            if not isinstance(raw, str):
                parsed[key] = (None, "invalid mergedAt timestamp", None)
                continue
            merged_at = _parse_timestamp(raw)
            if merged_at is None:
                parsed[key] = (None, "invalid mergedAt timestamp", None)
                continue
            parsed[key] = (merged_at, None, raw)
    return parsed


def _fetch_merge_facts(
    missing: list[tuple[str, int]],
    *,
    gh_runner: Callable[..., subprocess.CompletedProcess[str]],
    gh_bin: str,
) -> dict[tuple[str, int], tuple[datetime | None, str | None, str | None]]:
    """One ``gh api graphql`` call per ≤50 cache misses.

    ``gh`` exits non-zero when any alias errors, but stdout can still hold
    partial ``data``. Those aliases are parsed. Only a missing or unparseable
    payload fails the whole batch.
    """
    fetched: dict[tuple[str, int], tuple[datetime | None, str | None, str | None]] = {}
    valid: list[tuple[str, int]] = []
    for repo, number in missing:
        if number <= 0 or _REPO_RE.fullmatch(repo) is None:
            fetched[(repo, number)] = (None, "invalid repository or pull request", None)
        else:
            valid.append((repo, number))

    for start in range(0, len(valid), _GRAPHQL_BATCH_SIZE):
        batch = valid[start : start + _GRAPHQL_BATCH_SIZE]
        query = _merge_fact_query(batch)
        try:
            proc = gh_runner([gh_bin, "api", "graphql", "-f", f"query={query}"], timeout=_GH_TIMEOUT_S)
            stdout = proc.stdout or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            stderr = proc.stderr or ""
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            try:
                payload = json.loads(stdout) if stdout.strip() else {}
            except json.JSONDecodeError as exc:
                for key in batch:
                    fetched[key] = (None, f"json_decode: {exc}", None)
                continue
            # Field errors make ``gh`` exit 1 while successful aliases stay in ``data``.
            if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
                fetched.update(_parse_merge_fact_payload(payload, batch))
                continue
            if proc.returncode != 0:
                message = (stderr or stdout or "gh failed").strip()[:300]
                for key in batch:
                    fetched[key] = (None, message, None)
                continue
            fetched.update(_parse_merge_fact_payload(payload, batch))
        except subprocess.TimeoutExpired:
            for key in batch:
                fetched[key] = (None, f"gh api graphql timed out after {_GH_TIMEOUT_S}s", None)
        except Exception as exc:
            message = str(exc)[:300] or "gh failed"
            for key in batch:
                fetched[key] = (None, message, None)
    return fetched


def _resolve_pr_merge_facts(
    keys: list[tuple[str, int]],
    *,
    cache_path: Path | None,
    gh_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    gh_bin: str = "gh",
) -> dict[tuple[str, int], tuple[datetime | None, str | None]]:
    """Return merge timestamps for ``keys``. Cache hits do not call ``gh``."""
    unique: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    for key in keys:
        if key not in seen:
            seen.add(key)
            unique.append(key)

    facts = _load_merge_facts(cache_path)
    resolved: dict[tuple[str, int], tuple[datetime | None, str | None]] = {}
    missing: list[tuple[str, int]] = []
    for repo, number in unique:
        raw = facts.get(_fact_key(repo, number))
        parsed = _parse_timestamp(raw) if raw else None
        if parsed is not None:
            resolved[(repo, number)] = (parsed, None)
        else:
            missing.append((repo, number))
    if not missing:
        return resolved

    fetched = _fetch_merge_facts(missing, gh_runner=gh_runner or _run_gh, gh_bin=gh_bin)
    updates: dict[str, str] = {}
    for key, (merged_at, error, raw) in fetched.items():
        resolved[key] = (merged_at, error)
        if raw:
            updates[_fact_key(*key)] = raw
    if updates and cache_path is not None:
        _store_merge_facts(cache_path, {**_load_merge_facts(cache_path), **updates})
    return resolved


def collect_stream_bottleneck_metrics(
    *,
    tasks_dir: Path,
    plane_db: Path,
    now: datetime | None = None,
    github_lookup: Callable[..., tuple[datetime | None, str | None]] | None = None,
    gh_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    merge_cache_path: Path | None = None,
    gh_bin: str = "gh",
) -> dict[str, Any]:
    """Collect lifecycle-only per-stream bottlenecks from independent sources.

    Percentiles use linear interpolation of the sorted samples at ``(n - 1) * p``
    and are intentionally omitted until a span has at least twenty durations.
    Each source is fail-open: its errors are reported while other sources continue.
    Dispatch history includes records archived into ``tasks_dir/archive/`` (#8625).
    """
    clock = (now or datetime.now(UTC)).astimezone(UTC)
    buckets: dict[str, dict[str, dict[str, list[float]]]] = {
        "by_stream_epic": {},
        "by_task_family": {},
    }
    errors: list[dict[str, Any]] = []
    dispatch_hard_timeouts: list[int] = []
    tasks_store = batch_tasks_store(reachable=tasks_dir.is_dir())
    plane_store = comms_plane_store(reachable=plane_db.is_file())

    def _dispatch_error(error_kind: str) -> dict[str, Any]:
        return {"source": "dispatch", "error_kind": error_kind, "store": tasks_store}

    def _plane_error(error_kind: str, *, source: str = "formal_cf") -> dict[str, Any]:
        return {"source": source, "error_kind": error_kind, "store": plane_store}

    def _github_error(error_kind: str, *, pr_number: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": "github",
            "error_kind": error_kind,
            "store": plane_store,
        }
        if pr_number is not None:
            payload["pr_number"] = pr_number
        return payload

    def add(
        identity: tuple[str | None, str | None],
        span: str,
        duration: float | None,
        backlog_age: float | None,
    ) -> None:
        _add_event(
            buckets,
            dimension="by_stream_epic",
            identity=identity[0],
            span=span,
            duration=duration,
            backlog_age=backlog_age,
        )
        _add_event(
            buckets,
            dimension="by_task_family",
            identity=identity[1],
            span=span,
            duration=duration,
            backlog_age=backlog_age,
        )

    try:
        task_paths = list(iter_task_records(tasks_dir, include_archive=True))
        if not tasks_dir.is_dir():
            raise FileNotFoundError("tasks_dir_missing")
        for path in task_paths:
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                errors.append(_dispatch_error("task_record_unreadable"))
                continue
            if not isinstance(record, dict):
                errors.append(_dispatch_error("task_record_not_object"))
                continue
            hard_timeout = record.get("hard_timeout")
            if isinstance(hard_timeout, int) and hard_timeout >= 0:
                dispatch_hard_timeouts.append(hard_timeout)
            started = _parse_timestamp(record.get("started_at"))
            if started is None:
                errors.append(_dispatch_error("invalid_started_at"))
                continue
            finished_raw = record.get("finished_at")
            finished = _parse_timestamp(finished_raw)
            if finished_raw not in (None, "") and finished is None:
                errors.append(_dispatch_error("invalid_finished_at"))
                continue
            if finished is not None and finished < started:
                errors.append(_dispatch_error("negative_duration"))
                continue
            add(
                _identity(record),
                "dispatch",
                (finished - started).total_seconds() if finished else None,
                max(0.0, (clock - started).total_seconds()) if finished is None else None,
            )
    except FileNotFoundError:
        errors.append(_dispatch_error("tasks_dir_missing"))
    except OSError:
        errors.append(_dispatch_error("tasks_dir_unreadable"))

    lookups: dict[tuple[str, int], tuple[datetime | None, str | None]] = {}
    try:
        if _authority_file_missing(plane_db):
            raise FileNotFoundError("plane_db_missing")
        with _connect_ro(plane_db) as conn:
            plane_store = comms_plane_store(reachable=True)
            if not (_table_exists(conn, "formal_review_jobs") and _table_exists(conn, "github_publications")):
                raise sqlite3.DatabaseError("required formal_review_jobs/github_publications tables missing")
            columns = _column_names(conn, "formal_review_jobs")
            publication_columns = _column_names(conn, "github_publications")
            optional_identity = [name for name in ("stream_epic", "task_family") if name in columns]
            publication_join = "p.review_id = j.review_id"
            if "status_context" in publication_columns:
                publication_join += " AND p.status_context = 'fleet/cross-family-review'"
            rows = conn.execute(
                "SELECT j.review_id, j.repository, j.pr_number, j.created_at, "
                "p.published_at"
                + "".join(f", j.{name}" for name in optional_identity)
                + f" FROM formal_review_jobs j LEFT JOIN github_publications p ON {publication_join}"
            ).fetchall()
            pending_merges: list[tuple[tuple[str | None, str | None], datetime, tuple[str, int]]] = []
            for row in rows:
                record = dict(row)
                identity = _identity(record)
                created = _parse_timestamp(record.get("created_at"))
                if created is None:
                    errors.append(_plane_error("invalid_formal_review_created_at"))
                    continue
                published_raw = record.get("published_at")
                published = _parse_timestamp(published_raw)
                if published_raw not in (None, "") and published is None:
                    errors.append(_plane_error("invalid_github_publication_published_at"))
                    continue
                if published is not None and published < created:
                    errors.append(_plane_error("negative_publication_duration"))
                    continue
                add(
                    identity,
                    "formal_cf_publication",
                    (published - created).total_seconds() if published else None,
                    max(0.0, (clock - created).total_seconds()) if published is None else None,
                )
                if published is None:
                    continue
                repo = str(record.get("repository") or "")
                try:
                    pr_number = int(record["pr_number"])
                except (KeyError, TypeError, ValueError):
                    errors.append(_github_error("invalid_pr_number"))
                    continue
                if not repo:
                    errors.append(_github_error("missing_repository"))
                    continue
                pending_merges.append((identity, published, (repo, pr_number)))

            if github_lookup is None:
                cache_path = merge_cache_path if merge_cache_path is not None else _default_merge_cache_path()
                try:
                    lookups = _resolve_pr_merge_facts(
                        [item[2] for item in pending_merges],
                        cache_path=cache_path,
                        gh_runner=gh_runner,
                        gh_bin=gh_bin,
                    )
                except (OSError, ValueError, TypeError, subprocess.TimeoutExpired) as exc:
                    lookups = {item[2]: (None, str(exc)[:300]) for item in pending_merges}
            else:
                for _row_identity, _published, cache_key in pending_merges:
                    if cache_key in lookups:
                        continue
                    repo, pr_number = cache_key
                    try:
                        lookups[cache_key] = github_lookup(repo=repo, pr_number=pr_number)
                    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired) as exc:
                        lookups[cache_key] = (None, str(exc))

            for identity, published, cache_key in pending_merges:
                merged, lookup_error = lookups.get(cache_key, (None, "pr_lookup_missing"))
                pr_number = cache_key[1]
                if lookup_error:
                    errors.append(_github_error("pr_lookup_failed", pr_number=pr_number))
                    continue
                if merged is not None and merged < published:
                    errors.append(_github_error("negative_merge_duration", pr_number=pr_number))
                    continue
                add(
                    identity,
                    "gate_to_merge",
                    (merged - published).total_seconds() if merged else None,
                    max(0.0, (clock - published).total_seconds()) if merged is None else None,
                )
    except FileNotFoundError:
        errors.append(_plane_error("plane_db_missing"))
    except (OSError, sqlite3.Error, ControlPlaneError):
        errors.append(_plane_error("plane_db_unreadable"))

    def summarize(groups: dict[str, dict[str, dict[str, list[float]]]]) -> dict[str, Any]:
        return {
            name: {span: _span_summary(**samples) for span, samples in spans.items()}
            for name, spans in sorted(groups.items())
        }

    by_stream = summarize(buckets["by_stream_epic"])
    by_family = summarize(buckets["by_task_family"])
    empty_spans = {span: _span_summary(**samples) for span, samples in _new_buckets().items()}
    return {
        "content_included": False,
        "threshold_seconds": {
            "dispatch": max([DISPATCH_BOTTLENECK_THRESHOLD_S, *dispatch_hard_timeouts]),
            "formal_cf_publication": FORMAL_CF_PUBLICATION_THRESHOLD_S,
            "gate_to_merge": GATE_TO_MERGE_THRESHOLD_S,
        },
        "percentile_method": "linear interpolation at sorted index (n - 1) * p; emitted only when n >= 20",
        "by_stream_epic": {key: value for key, value in by_stream.items() if key != "unclassified"},
        "by_task_family": {key: value for key, value in by_family.items() if key != "unclassified"},
        "unclassified": {
            "by_stream_epic": by_stream.get("unclassified", empty_spans),
            "by_task_family": by_family.get("unclassified", empty_spans),
        },
        "source_errors": errors,
    }
