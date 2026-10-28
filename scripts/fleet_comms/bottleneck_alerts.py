"""Rate-limited, metadata-only stream bottleneck alerts (#5646).

The inbox worker calls :func:`scan_bottlenecks_at_inbox_checkpoint`; this
module deliberately owns no daemon or gate.  Alert delivery uses the existing
channel inbox, while the broker stores only alert lifecycle metadata needed for
dedupe and re-arming.
"""

from __future__ import annotations

import errno
import json
import logging
import re
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from scripts.lib.readonly_sqlite import SQLiteConnection
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    from lib.readonly_sqlite import SQLiteConnection  # type: ignore[no-redef]

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
    if expires_at <= now or holder not in _channels.get_valid_recipient_agents():
        return None
    return holder


def _reserve_scan(conn: SQLiteConnection, *, now: datetime, rate_limit_seconds: int) -> bool:
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


def _state_row(conn: SQLiteConnection, stream_epic: str, span: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM bottleneck_alert_state WHERE stream_epic = ? AND span = ?",
        (stream_epic, span),
    ).fetchone()


def _record_clear(conn: SQLiteConnection, stream_epic: str, span: str) -> bool:
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


def _record_delivery_failures(conn: SQLiteConnection) -> int:
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


# Closed vocabulary for legacy v1 finalization reasons. Keep this reader independent
# of dispatch writers and adapters, including when their legacy modules are retired.
# fmt: off
_PUBLIC_CAUSES = frozenset(
    {
        "ADVISORY_BINDING_MISMATCH", "ADVISORY_ENVELOPE_CHANGED", "ADVISORY_ENVELOPE_INCOMPLETE",
        "ADVISORY_ENVELOPE_MISSING", "ADVISORY_FLAG_CONFLICT", "ADVISORY_OWNED_PATHS_INVALID",
        "ADVISORY_OWNED_PATHS_MISMATCH", "ADVISORY_RESULT_UNREADABLE", "ADVISORY_ROLE_REFUSED",
        "ADVISORY_SEAL_MISMATCH", "ADVISORY_SEAL_MISSING", "ADVISORY_TASK_NOT_DONE", "ADVISORY_TASK_NOT_FOUND",
        "ADVISORY_TASK_WRONG_MODEL", "ADVISORY_TASK_WRONG_ROLE", "BOUNDED_ADMISSION_INVALID",
        "BOUNDED_ADMISSION_MISSING", "BOUNDED_DRIVER_BRIEF_REFUSED", "BOUNDED_ENVELOPE_REQUIRED",
        "BOUNDED_EXECUTION_MISMATCH", "HEAD unavailable", "acp_adapter_incompatible", "acp_adapter_missing",
        "acp_agent_disconnected", "acp_agent_startup", "acp_auth_required", "acp_permission_denied",
        "acp_permission_unavailable", "acp_review_evidence_invalid", "acp_review_evidence_too_large",
        "acp_session_create_timeout", "acp_turn_limit", "activity probe unavailable", "adapter_refused",
        "adapter_rejected", "advisory_ceiling_exceeded", "advisory_ceiling_unmeasured",
        "advisory_exempt_changes_unmeasured", "advisory_exempt_code_change", "agy_background_task_abandoned",
        "agy_background_task_canceled", "agy_background_task_unconfirmed", "agy_headless_permission_denied",
        "agy_model_identity_unverified", "agy_print_timeout_partial", "agy_transcript_unbound",
        "agy_transcript_unreadable", "ahead count unavailable", "already rescued at HEAD",
        "auto_finalize_add_failed", "auto_finalize_changes_remaining", "auto_finalize_changes_unknown",
        "auto_finalize_commit_failed", "auto_finalize_committed_scope_unknown",
        "auto_finalize_committed_scope_unowned", "auto_finalize_copy_timeout", "auto_finalize_dirty_unknown",
        "auto_finalize_failed", "auto_finalize_fsck_failed", "auto_finalize_head_moved",
        "auto_finalize_invalid_tree_path", "auto_finalize_object_hardening_violation",
        "auto_finalize_opsec_blocked", "auto_finalize_pr_failed", "auto_finalize_preparation_refused",
        "auto_finalize_publish_blocked", "auto_finalize_push_failed", "auto_finalize_push_unexpected_ref",
        "auto_finalize_remote_unknown", "auto_finalize_remote_unverified", "auto_finalize_reset_failed",
        "auto_finalize_scope_check_timeout", "auto_finalize_unconfirmed", "auto_finalize_unsafe_branch",
        "auto_finalize_validation_changed", "auto_finalize_validation_unavailable", "background_jobs_alive_at_exit",
        "boundary_install_failed", "boundary_remove_failed", "changed files unavailable", "changes_parse_failed",
        "changes_unreadable", "claude_account_ambient_conflict", "claude_account_api_key_route_unsupported",
        "claude_account_auth_method_conflict",
        "claude_account_auth_status_unavailable", "claude_account_binding_invalid",
        "claude_account_binding_is_default", "claude_account_binding_missing", "claude_account_binding_not_private",
        "claude_account_binding_oversized", "claude_account_binding_unavailable", "claude_account_config_ambiguous",
        "claude_account_config_credential_source", "claude_account_config_dir_missing",
        "claude_account_config_dir_not_private", "claude_account_config_dir_unavailable",
        "claude_account_config_invalid", "claude_account_config_not_private", "claude_account_config_oversized",
        "claude_account_config_unavailable", "claude_account_credentials_expired",
        "claude_account_credentials_invalid", "claude_account_credentials_missing",
        "claude_account_credentials_not_private", "claude_account_credentials_oversized",
        "claude_account_credentials_unavailable", "claude_account_default_file_invalid",
        "claude_account_default_file_not_private", "claude_account_default_file_oversized",
        "claude_account_default_file_unavailable", "claude_account_default_has_no_binding",
        "claude_account_forward_unsupported", "claude_account_identity_unavailable",
        "claude_account_machine_policy_present", "claude_account_machine_policy_unavailable",
        "claude_account_plan_unsupported", "claude_account_plan_unverified", "claude_account_platform_unsupported",
        "claude_account_policy_cache_present", "claude_account_policy_cache_unavailable",
        "claude_account_profile_store_present", "claude_account_record_conflict", "claude_account_route_unsealed",
        "claude_account_seat_unsupported", "claude_account_settings_changed",
        "claude_account_settings_credential_source", "claude_account_settings_invalid",
        "claude_account_settings_not_private", "claude_account_settings_oversized",
        "claude_account_settings_unavailable", "claude_account_status_override", "claude_account_unknown",
        "claude_account_unverified", "clean disposable residue", "clean-tree", "commit_count_unknown",
        "completion_gate_response_unavailable", "could not clean disposable residue", "cwd_unpinned",
        "diff_command_failed", "dispatch_fallback_refused", "dispatch_isolation_failed", "dispatch_not_started",
        "disposable residue removed", "file_unreadable", "files exceed 5 MB", "finalize_delivery_pending",
        "finalize_failed", "finalize_remote_unknown", "finalize_skipped_paths", "finalize_unpushed",
        "forward_configuration_failed", "github_auth_required", "github_secondary_rate_limited",
        "interrupted before the completion gates ran", "interrupted_during_finalize", "invalid finished_at",
        "invalid_delivery_declaration", "junk_only_worktree_changes", "kimi_admission_refused",
        "kimi_content_refused", "kimi_worktree_mismatch", "leftovers_scan_unknown", "mechanical_admission_refused",
        "merge_base_unresolved", "move detection failed; nothing committed", "muse_worker_task_binding_refused",
        "no finished_at", "no provable unpushed work", "no recorded worktree", "no_changes_under_owned_paths",
        "no_commits_no_changes", "no_owned_paths_declared", "not a git worktree",
        "not a registered dispatch worktree", "permission_cancelled", "primary_tree_write", "protocol_output_limit",
        "provider_auth", "provider_error", "provider_overloaded", "provider_policy_refusal",
        "provider_stream_incomplete", "provider_unavailable", "rate_limited", "read_only_checkout_mutation",
        "read_only_checkout_snapshot_failed", "recovery_requires_rerun", "remote_unreachable",
        "rescue remote branch already exists at another head", "rescue_commit_failed", "rescue_embedded_repository",
        "rescue_filtered_path", "rescue_identity_unavailable", "rescue_input_changed", "rescue_input_unreadable",
        "rescue_new_gitlink", "rescue_push_failed", "rescue_push_url_unavailable", "rescue_remote_unverified",
        "rescue_step_failed", "rescue_tree_unavailable", "rescue_worktree_unregistered", "rescued",
        "result_invalid", "review_admission_refused", "review_missing_verdict_line",
        "review_unsupported_verdict_token", "review_worker_nonzero_exit", "review_worker_not_started",
        "review_worker_reported_failure", "review_worker_returncode_missing", "runtime_returncode_missing",
        "task attempt changed after rescue push; recovery ref preserved", "task is not terminal non-success",
        "task lease active", "task process alive", "task state changed", "task_records_snapshot_failed",
        "temp_index_failed", "timeout", "transport_error", "unclassified_error", "unknown",
        "unpushed state unknown - needs rescue", "unpushed work - needs rescue", "unreadable task state",
        "worker_cancelled", "worker_failed", "worker_process_dead", "worker_rate_limited", "worker_runtime_error",
        "worker_spawn_failed", "worker_timed_out", "worker_unexpected_error", "worktree active",
        "worktree already removed", "worktree branch differs from task record", "worktree dirty",
        "worktree group has nonterminal task", "worktree group records disagree on branch",
        "worktree task inventory unavailable", "worktree_missing_at_settle", "worktree_preparation_failed",
    }
)
_PUBLIC_GIT_SUBCOMMANDS = frozenset(
    {
        "add", "am", "apply", "archive", "branch", "cat-file", "check-attr", "check-ignore", "check-ref-format",
        "checkout", "cherry-pick", "clean", "clone", "commit", "commit-tree", "config", "count-objects", "describe",
        "diff", "diff-files", "diff-index", "diff-tree", "fetch", "for-each-ref", "fsck", "gc", "hash-object",
        "init", "log", "ls-files", "ls-remote", "ls-tree", "merge", "merge-base", "mktree", "mv", "notes",
        "pack-refs", "prune", "pull", "push", "read-tree", "rebase", "reflog", "remote", "repack", "reset",
        "restore", "rev-list", "rev-parse", "rm", "show", "show-ref", "sparse-checkout", "stash", "status",
        "submodule", "switch", "symbolic-ref", "tag", "update-index", "update-ref", "var", "verify-commit",
        "worktree", "write-tree",
    }
)
# fmt: on
_PUBLIC_ERROR_CLASS_RE = re.compile(
    r"[A-Z][A-Za-z0-9]{0,63}(?:Error|Exception|Exit|Interrupt|Expired|Refused|Unreadable|Blocked|Iteration|Warning)"
)
_PUBLIC_ERRNO_NAMES = frozenset(errno.errorcode.values())
_PUBLIC_INT_PARAM_RE = re.compile(r"(?:exit -?|count )\d{1,9}")


def _is_public_error(text: str) -> bool:
    """An exception class, optionally with its errno name: ``OSError EACCES``."""
    error_class, _, errno_name = text.partition(" ")
    return bool(_PUBLIC_ERROR_CLASS_RE.fullmatch(error_class)) and (not errno_name or errno_name in _PUBLIC_ERRNO_NAMES)


def _is_public_param(text: str) -> bool:
    """One fixed parameter: ``git <known subcommand>``, ``exit <n>``, ``count <n>``, or ``<ErrorClass>[ <ERRNO>]``."""
    if text.startswith("git "):
        return text[4:] in _PUBLIC_GIT_SUBCOMMANDS
    return bool(_PUBLIC_INT_PARAM_RE.fullmatch(text)) or _is_public_error(text)


def _is_public_item(text: str) -> bool:
    """A registered cause, alone or followed by fixed parameters (``cause, git push, exit 1``)."""
    if text in _PUBLIC_CAUSES:
        return True
    cause, *params = text.split(", ")
    return cause in _PUBLIC_CAUSES and bool(params) and all(_is_public_param(param) for param in params)


def is_public_cause(value: object) -> bool:
    """Whether ``value`` may be published as it is: registered causes with fixed parameters, joined by ``; ``."""
    if not isinstance(value, str) or not value or len(value) > 512:
        return False
    return value in _PUBLIC_CAUSES or all(_is_public_item(item) for item in value.split("; "))


def _scan_finalization_attention(*, task_root: Path, now: datetime) -> tuple[int, tuple[dict[str, str], ...]]:
    """Post once per aged task/run through the checkpoint's durable broker."""
    from scripts.driver_blockers import finalization_age

    if not task_root.is_dir():
        return 0, ({"source": "needs_finalize", "error": "task_store_unavailable"},)
    posted, errors = 0, []
    conn = get_db()
    try:
        for path in sorted(task_root.glob("*.json")):
            try:
                task = json.loads(path.read_text())
                if not isinstance(task, dict):
                    raise ValueError("invalid_task_record")
                if task.get("status") != "needs_finalize":
                    continue
                task_id, nonce = task.get("task_id"), task.get("run_nonce")
                if not all(
                    isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", value)
                    for value in (task_id, nonce)
                ):
                    raise ValueError("task_identity_unknown")
                age = finalization_age(task, now=now)
                if not age["attention"]:
                    continue
                identity = f"task:{task_id}:{nonce}"
                prior = _state_row(conn, identity, "needs_finalize")
                if prior is not None and prior["message_id"]:
                    continue
                reason = task.get("finalize_error") or task.get("last_error")
                if not is_public_cause(reason):
                    reason = "finalize_delivery_pending"
                owner = task.get("initiator")
                if owner not in _channels.get_valid_recipient_agents():
                    owner = "unknown"
                _channels.create_channel("cto", description="CTO attention")
                correlation = f"needs-finalize:{task_id}:{nonce}"
                delivered = conn.execute(
                    "SELECT message_id FROM channel_messages WHERE channel='cto' AND correlation_id=? LIMIT 1",
                    (correlation,),
                ).fetchone()
                if delivered is not None:
                    post = {"message_id": delivered["message_id"]}
                else:
                    post = _channels.post(
                        "cto",
                        "user",
                        f"ACTION REQUIRED: needs_finalize task={task_id}; age_minutes={age['age_minutes']}; "
                        f"age_state={age['age_state']}; threshold_minutes={age['threshold_minutes']}; "
                        f"configuration={age['configuration']}; reason={reason}; owner={owner}; "
                        "action=inspect retained task/head, repair the named gate and retry normal publication.",
                        correlation_id=f"needs-finalize:{task_id}:{nonce}",
                        kind="system",
                        priority=_channels.PRIORITY_ACTION_REQUIRED,
                        auto_snapshot=False,
                        verify_citations=False,
                    )
                conn.execute(
                    """INSERT INTO bottleneck_alert_state(
                        stream_epic, span, active, rearm_level, last_alert_age_s, last_alert_at, message_id
                    ) VALUES (?, 'needs_finalize', 1, 1, ?, ?, ?)
                    ON CONFLICT(stream_epic, span) DO UPDATE SET
                        active=1, last_alert_age_s=excluded.last_alert_age_s,
                        last_alert_at=excluded.last_alert_at, message_id=excluded.message_id""",
                    (
                        identity,
                        None if age["age_minutes"] is None else age["age_minutes"] * 60,
                        _iso(now),
                        post["message_id"],
                    ),
                )
                conn.commit()
                posted += int(delivered is None)
            except Exception as exc:
                errors.append({"source": "needs_finalize", "error": type(exc).__name__})
                logger.exception("finalization alert could not be evaluated or posted")
    finally:
        conn.close()
    return posted, tuple(errors)


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

    finalization_posted, finalization_errors = _scan_finalization_attention(task_root=task_path, now=clock)
    try:
        metrics = metrics_collector(tasks_dir=task_path, plane_db=plane_path, now=clock)
    except Exception as exc:  # A diagnostics failure must never break inbox delivery.
        logger.exception("bottleneck alerts: metrics collection failed: %s", exc)
        return AlertScanResult(
            True,
            finalization_posted,
            0,
            delivery_failures,
            (*finalization_errors, {"source": "alerts", "error": str(exc)}),
        )

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
    alerts_posted = finalization_posted
    cleared = 0
    try:
        prior_active = conn.execute(
            "SELECT stream_epic, span FROM bottleneck_alert_state WHERE active = 1 AND span != 'needs_finalize'"
        ).fetchall()
        error_sources = {
            str(error.get("source")) for error in metrics.get("source_errors", []) if isinstance(error, dict)
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
            recipients = list(dict.fromkeys([*([holder] if holder else []), ESCALATION_RECIPIENT]))
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

    errors = (*finalization_errors, *(error for error in metrics.get("source_errors", []) if isinstance(error, dict)))
    return AlertScanResult(True, alerts_posted, cleared, delivery_failures, errors)
