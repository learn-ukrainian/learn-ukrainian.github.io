"""Sol PR-M: efficiency metrics from durable broker timestamps (no content)."""

from __future__ import annotations

import json
import sqlite3
import subprocess
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Alert thresholds are intentionally reported, not enforced here. #5646 owns
# consuming them. Dispatch uses the delegate default floor of 7,200 seconds.
DISPATCH_BOTTLENECK_THRESHOLD_S = 7_200
FORMAL_CF_PUBLICATION_THRESHOLD_S = 3_600
GATE_TO_MERGE_THRESHOLD_S = 3_600


@contextmanager
def _connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Open a read path connection and always close it (sqlite3 `with` only commits)."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def collect_delivery_backlog(
    db_path: Path,
    *,
    limit: int = 100,
    exclude_retired: bool = True,
) -> dict[str, Any]:
    """Pending/dispatched delivery backlog without message bodies."""
    retired = {"gemini"}
    with _connect(db_path) as conn:
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
    with _connect(db_path) as conn:
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
    with _connect(db_path) as conn:
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
            # latency for delivered rows with both timestamps
            lat = conn.execute(
                """
                SELECT
                  COUNT(*) AS n,
                  AVG(
                    (julianday(delivered_at) - julianday(dispatched_at)) * 86400.0
                  ) AS avg_s,
                  MIN(
                    (julianday(delivered_at) - julianday(dispatched_at)) * 86400.0
                  ) AS min_s,
                  MAX(
                    (julianday(delivered_at) - julianday(dispatched_at)) * 86400.0
                  ) AS max_s
                FROM deliveries
                WHERE status = 'delivered'
                  AND delivered_at IS NOT NULL
                  AND dispatched_at IS NOT NULL
                  AND delivered_at != ''
                  AND dispatched_at != ''
                """
            ).fetchone()
            if lat and lat["n"]:
                metrics["latency_seconds"]["delivery_dispatch_to_done"] = {
                    "n": int(lat["n"]),
                    "avg": round(float(lat["avg_s"] or 0.0), 3),
                    "min": round(float(lat["min_s"] or 0.0), 3),
                    "max": round(float(lat["max_s"] or 0.0), 3),
                }

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


def _github_merged_at(
    *,
    repo: str,
    pr_number: int,
    gh_bin: str = "gh",
) -> tuple[datetime | None, str | None]:
    """Fetch a PR merge timestamp only; no body, title, or review text."""
    proc = subprocess.run(
        [gh_bin, "pr", "view", str(pr_number), "--repo", repo, "--json", "mergedAt"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout or "gh failed").strip()[:300]
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return None, f"json_decode: {exc}"
    merged_at = _parse_timestamp(payload.get("mergedAt"))
    if payload.get("mergedAt") and merged_at is None:
        return None, "invalid mergedAt timestamp"
    return merged_at, None


def collect_stream_bottleneck_metrics(
    *,
    tasks_dir: Path,
    plane_db: Path,
    now: datetime | None = None,
    github_lookup: Callable[..., tuple[datetime | None, str | None]] = _github_merged_at,
) -> dict[str, Any]:
    """Collect lifecycle-only per-stream bottlenecks from independent sources.

    Percentiles use linear interpolation of the sorted samples at ``(n - 1) * p``
    and are intentionally omitted until a span has at least twenty durations.
    Each source is fail-open: its errors are reported while other sources continue.
    """
    clock = (now or datetime.now(UTC)).astimezone(UTC)
    buckets: dict[str, dict[str, dict[str, list[float]]]] = {
        "by_stream_epic": {},
        "by_task_family": {},
    }
    errors: list[dict[str, str]] = []
    dispatch_hard_timeouts: list[int] = []

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
        task_paths = sorted(tasks_dir.glob("*.json"))
        if not tasks_dir.is_dir():
            raise FileNotFoundError(tasks_dir)
        for path in task_paths:
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append({"source": "dispatch", "error": f"{path.name}: {exc}"})
                continue
            if not isinstance(record, dict):
                errors.append({"source": "dispatch", "error": f"{path.name}: expected object"})
                continue
            hard_timeout = record.get("hard_timeout")
            if isinstance(hard_timeout, int) and hard_timeout >= 0:
                dispatch_hard_timeouts.append(hard_timeout)
            started = _parse_timestamp(record.get("started_at"))
            if started is None:
                errors.append({"source": "dispatch", "error": f"{path.name}: invalid started_at"})
                continue
            finished_raw = record.get("finished_at")
            finished = _parse_timestamp(finished_raw)
            if finished_raw not in (None, "") and finished is None:
                errors.append({"source": "dispatch", "error": f"{path.name}: invalid finished_at"})
                continue
            if finished is not None and finished < started:
                errors.append({"source": "dispatch", "error": f"{path.name}: negative duration"})
                continue
            add(
                _identity(record),
                "dispatch",
                (finished - started).total_seconds() if finished else None,
                max(0.0, (clock - started).total_seconds()) if finished is None else None,
            )
    except OSError as exc:
        errors.append({"source": "dispatch", "error": str(exc)})

    merged_cache: dict[tuple[str, int], tuple[datetime | None, str | None]] = {}
    try:
        with _connect(plane_db) as conn:
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
            for row in rows:
                record = dict(row)
                identity = _identity(record)
                created = _parse_timestamp(record.get("created_at"))
                if created is None:
                    errors.append({"source": "formal_cf", "error": "invalid formal_review_jobs.created_at"})
                    continue
                published_raw = record.get("published_at")
                published = _parse_timestamp(published_raw)
                if published_raw not in (None, "") and published is None:
                    errors.append({"source": "formal_cf", "error": "invalid github_publications.published_at"})
                    continue
                if published is not None and published < created:
                    errors.append({"source": "formal_cf", "error": "negative publication duration"})
                    continue
                add(
                    identity,
                    "formal_cf_publication",
                    (published - created).total_seconds() if published else None,
                    max(0.0, (clock - created).total_seconds()) if published is None else None,
                )
                if published is None:
                    continue
                repo, pr_number = str(record["repository"]), int(record["pr_number"])
                cache_key = (repo, pr_number)
                if cache_key not in merged_cache:
                    try:
                        merged_cache[cache_key] = github_lookup(repo=repo, pr_number=pr_number)
                    except (OSError, ValueError, TypeError) as exc:
                        merged_cache[cache_key] = (None, str(exc))
                merged, lookup_error = merged_cache[cache_key]
                if lookup_error:
                    errors.append({"source": "github", "error": f"PR {pr_number}: {lookup_error}"})
                    continue
                if merged is not None and merged < published:
                    errors.append({"source": "github", "error": f"PR {pr_number}: negative merge duration"})
                    continue
                add(
                    identity,
                    "gate_to_merge",
                    (merged - published).total_seconds() if merged else None,
                    max(0.0, (clock - published).total_seconds()) if merged is None else None,
                )
    except (OSError, sqlite3.Error) as exc:
        errors.append({"source": "formal_cf", "error": str(exc)})

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
