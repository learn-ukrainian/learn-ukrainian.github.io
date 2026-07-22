"""Rate-limited, metadata-only stream bottleneck alerts (#5646).

The inbox worker calls :func:`scan_bottlenecks_at_inbox_checkpoint`; this
module deliberately owns no daemon or gate.  Alert delivery uses the existing
channel inbox, while the broker stores only alert lifecycle metadata needed for
dedupe and re-arming.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agents_extensions.shared.session_streams.db import SessionStreamDatabase, default_database_path
from agents_extensions.shared.session_streams.model import parse_timestamp
from scripts.ai_agent_bridge import _channels
from scripts.ai_agent_bridge._db import get_db
from scripts.fleet_comms.efficiency_metrics import collect_stream_bottleneck_metrics
from scripts.fleet_comms.message_plane import default_plane_root

logger = logging.getLogger(__name__)

ALERT_CHANNEL = "fleet-comms"
ESCALATION_RECIPIENT = "claude-infra"
SCAN_RATE_LIMIT_SECONDS = 300
REARM_MULTIPLIER = 2
_CONTROL_KEY = "bottleneck-alerts"


@dataclass(frozen=True, slots=True)
class AlertScanResult:
    """Metadata-only outcome for one checkpoint invocation."""

    scanned: bool
    alerts_posted: int
    cleared: int
    delivery_failures: int
    source_errors: tuple[dict[str, str], ...]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _active_lease_holder(stream_epic: str, *, session_db: Path, now: datetime) -> str | None:
    """Return the non-expired stream holder, without creating a session DB."""
    if not session_db.is_file():
        return None
    try:
        database = SessionStreamDatabase(session_db)
        with database.connect(read_only=True) as conn:
            row = conn.execute(
                """
                SELECT l.holder_agent, l.expires_at
                FROM stream_leases AS l
                JOIN sessions AS s ON s.stream_id = l.stream_id
                    AND s.session_id = l.session_id
                WHERE l.stream_id = ?
                  AND l.state = 'active'
                  AND s.state IN ('open', 'rolling')
                """,
                (f"epic:{stream_epic}",),
            ).fetchone()
    except (OSError, sqlite3.Error, ValueError) as exc:
        logger.error("bottleneck alerts: lease lookup failed for epic %s: %s", stream_epic, exc)
        return None
    if row is None:
        return None
    try:
        expires_at = parse_timestamp(str(row["expires_at"]))
    except ValueError:
        logger.error("bottleneck alerts: invalid lease expiry for epic %s", stream_epic)
        return None
    holder = str(row["holder_agent"] or "")
    if expires_at <= now or holder not in _channels.VALID_RECIPIENT_AGENTS:
        return None
    return holder


def _reserve_scan(conn: sqlite3.Connection, *, now: datetime, rate_limit_seconds: int) -> bool:
    """Persistently rate-limit the scanner across independent inbox workers."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT last_scanned_at FROM bottleneck_alert_scan_control WHERE control_key = ?",
            (_CONTROL_KEY,),
        ).fetchone()
        if row is not None:
            try:
                last = parse_timestamp(str(row["last_scanned_at"]))
            except ValueError:
                last = None
            if last is not None and (now - last).total_seconds() < rate_limit_seconds:
                conn.commit()
                return False
        conn.execute(
            """
            INSERT INTO bottleneck_alert_scan_control(control_key, last_scanned_at)
            VALUES (?, ?)
            ON CONFLICT(control_key) DO UPDATE SET last_scanned_at = excluded.last_scanned_at
            """,
            (_CONTROL_KEY, _iso(now)),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise


def _state_row(conn: sqlite3.Connection, stream_epic: str, span: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM bottleneck_alert_state WHERE stream_epic = ? AND span = ?",
        (stream_epic, span),
    ).fetchone()


def _record_clear(conn: sqlite3.Connection, stream_epic: str, span: str) -> bool:
    row = _state_row(conn, stream_epic, span)
    if row is None or not bool(row["active"]):
        return False
    conn.execute(
        """
        UPDATE bottleneck_alert_state
        SET active = 0, rearm_level = 1, last_alert_age_s = NULL,
            message_id = NULL, last_delivery_error = NULL, delivery_failure_reported = 0
        WHERE stream_epic = ? AND span = ?
        """,
        (stream_epic, span),
    )
    conn.commit()
    return True


def _requires_alert(row: sqlite3.Row | None, *, age_s: float, threshold_s: int) -> tuple[bool, int]:
    if row is None or not bool(row["active"]):
        return True, 1
    level = max(1, int(row["rearm_level"]))
    # A failed post has no durable channel message to deduplicate against;
    # retry it at the next rate-limited checkpoint instead of waiting for 2x.
    if not row["message_id"]:
        return True, level
    if age_s >= threshold_s * (REARM_MULTIPLIER**level):
        return True, level + 1
    return False, level


def _record_delivery_failures(conn: sqlite3.Connection) -> int:
    """Make failed alert deliveries loud once; the channel remains the record."""
    rows = conn.execute(
        """
        SELECT s.stream_epic, s.span, MIN(COALESCE(d.error, 'delivery failed')) AS error
        FROM bottleneck_alert_state AS s
        JOIN deliveries AS d ON d.message_id = s.message_id
        WHERE s.active = 1 AND s.delivery_failure_reported = 0
          AND d.status IN ('failed', 'expired')
        GROUP BY s.stream_epic, s.span
        """
    ).fetchall()
    for row in rows:
        error = str(row["error"] or "delivery failed")[:300]
        logger.error(
            "bottleneck alert delivery failed for epic %s %s: %s",
            row["stream_epic"],
            row["span"],
            error,
        )
        conn.execute(
            """
            UPDATE bottleneck_alert_state
            SET last_delivery_error = ?, delivery_failure_reported = 1
            WHERE stream_epic = ? AND span = ?
            """,
            (error, row["stream_epic"], row["span"]),
        )
    conn.commit()
    return len(rows)


def _alert_body(*, stream_epic: str, span: str, age_s: float, threshold_s: int) -> str:
    return (
        "ACTION REQUIRED: stream bottleneck detected. "
        f"epic={stream_epic}; span={span}; backlog_age_s={round(age_s, 3)}; "
        f"threshold_s={threshold_s}. Inspect lifecycle metadata and unblock or hand off."
    )


def scan_bottlenecks_at_inbox_checkpoint(
    *,
    repo_root: Path,
    now: datetime | None = None,
    tasks_dir: Path | None = None,
    plane_db: Path | None = None,
    session_db: Path | None = None,
    rate_limit_seconds: int = SCAN_RATE_LIMIT_SECONDS,
    metrics_collector: Callable[..., dict[str, Any]] = collect_stream_bottleneck_metrics,
) -> AlertScanResult:
    """Scan and post deduplicated action-required alerts without blocking a drain.

    A persistent breach re-arms at 2x, 4x, and subsequent powers of its
    threshold.  A clear resets the level, so a later breach is immediately
    eligible again.  Neither alerts nor their state include task prompts or
    message bodies.
    """
    if rate_limit_seconds < 0:
        raise ValueError("rate_limit_seconds must be non-negative")
    clock = (now or _utc_now()).astimezone(UTC)
    task_path = tasks_dir or repo_root / "batch_state" / "tasks"
    plane_path = plane_db or default_plane_root(repo_root=repo_root) / "comms.sqlite3"
    if session_db is not None:
        lease_path = session_db
    else:
        try:
            lease_path = default_database_path(repo_root)
        except Exception as exc:
            # A missing canonical checkout is equivalent to no live lease for
            # this best-effort diagnostic; escalation must still proceed.
            logger.error("bottleneck alerts: cannot resolve session-stream DB: %s", exc)
            lease_path = repo_root / ".agent" / "session-streams" / "missing.sqlite3"

    conn = get_db()
    try:
        if not _reserve_scan(conn, now=clock, rate_limit_seconds=rate_limit_seconds):
            return AlertScanResult(False, 0, 0, _record_delivery_failures(conn), ())
        delivery_failures = _record_delivery_failures(conn)
    finally:
        conn.close()

    try:
        metrics = metrics_collector(tasks_dir=task_path, plane_db=plane_path, now=clock)
    except Exception as exc:  # A diagnostics failure must never break inbox delivery.
        logger.exception("bottleneck alerts: metrics collection failed: %s", exc)
        return AlertScanResult(True, 0, 0, delivery_failures, ({"source": "alerts", "error": str(exc)},))

    thresholds = metrics.get("threshold_seconds", {})
    breaches: dict[tuple[str, str], tuple[float, int]] = {}
    by_stream = metrics.get("by_stream_epic", {})
    if isinstance(by_stream, dict):
        for stream_epic, spans in by_stream.items():
            if not isinstance(spans, dict):
                continue
            for span, summary in spans.items():
                if not isinstance(summary, dict):
                    continue
                age_s = summary.get("backlog_age_s")
                threshold_s = thresholds.get(span)
                if isinstance(age_s, (int, float)) and isinstance(threshold_s, int) and age_s >= threshold_s:
                    breaches[(str(stream_epic), str(span))] = (float(age_s), threshold_s)

    conn = get_db()
    alerts_posted = 0
    cleared = 0
    try:
        prior_active = conn.execute(
            "SELECT stream_epic, span FROM bottleneck_alert_state WHERE active = 1"
        ).fetchall()
        error_sources = {
            str(error.get("source"))
            for error in metrics.get("source_errors", [])
            if isinstance(error, dict)
        }
        span_sources = {
            "dispatch": {"dispatch"},
            "formal_cf_publication": {"formal_cf"},
            "gate_to_merge": {"formal_cf", "github"},
        }
        for row in prior_active:
            identity = (str(row["stream_epic"]), str(row["span"]))
            # A source outage is unknown, not clear.  Retain its alert state
            # until the relevant lifecycle source reports a genuine clear.
            if identity not in breaches and not (span_sources.get(identity[1], set()) & error_sources):
                cleared += int(_record_clear(conn, *identity))

        for (stream_epic, span), (age_s, threshold_s) in sorted(breaches.items()):
            row = _state_row(conn, stream_epic, span)
            should_alert, new_level = _requires_alert(row, age_s=age_s, threshold_s=threshold_s)
            if not should_alert:
                continue
            holder = _active_lease_holder(stream_epic, session_db=lease_path, now=clock)
            recipients = list(dict.fromkeys([*( [holder] if holder else []), ESCALATION_RECIPIENT]))
            try:
                _channels.create_channel(ALERT_CHANNEL, description="Fleet lifecycle alerts")
                post = _channels.post(
                    ALERT_CHANNEL,
                    "user",
                    _alert_body(
                        stream_epic=stream_epic,
                        span=span,
                        age_s=age_s,
                        threshold_s=threshold_s,
                    ),
                    to_agents=recipients,
                    correlation_id=f"bottleneck:{stream_epic}:{span}:{new_level}",
                    kind="system",
                    priority=_channels.PRIORITY_ACTION_REQUIRED,
                    auto_snapshot=False,
                    verify_citations=False,
                )
            except Exception as exc:
                logger.exception("bottleneck alert post failed for epic %s %s: %s", stream_epic, span, exc)
                conn.execute(
                    """
                    INSERT INTO bottleneck_alert_state(
                        stream_epic, span, active, rearm_level, last_delivery_error
                    ) VALUES (?, ?, 1, ?, ?)
                    ON CONFLICT(stream_epic, span) DO UPDATE SET
                        active = 1, rearm_level = excluded.rearm_level,
                        last_delivery_error = excluded.last_delivery_error
                    """,
                    (stream_epic, span, new_level, str(exc)[:300]),
                )
                conn.commit()
                continue
            conn.execute(
                """
                INSERT INTO bottleneck_alert_state(
                    stream_epic, span, active, rearm_level, last_alert_age_s,
                    last_alert_at, message_id, last_delivery_error, delivery_failure_reported
                ) VALUES (?, ?, 1, ?, ?, ?, ?, NULL, 0)
                ON CONFLICT(stream_epic, span) DO UPDATE SET
                    active = 1, rearm_level = excluded.rearm_level,
                    last_alert_age_s = excluded.last_alert_age_s,
                    last_alert_at = excluded.last_alert_at, message_id = excluded.message_id,
                    last_delivery_error = NULL, delivery_failure_reported = 0
                """,
                (stream_epic, span, new_level, age_s, _iso(clock), post["message_id"]),
            )
            conn.commit()
            alerts_posted += 1
    finally:
        conn.close()

    errors = tuple(error for error in metrics.get("source_errors", []) if isinstance(error, dict))
    return AlertScanResult(True, alerts_posted, cleared, delivery_failures, errors)
