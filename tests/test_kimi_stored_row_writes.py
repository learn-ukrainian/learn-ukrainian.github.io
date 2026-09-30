"""Every write to a stored job, delivery, request or message row has a recorded Kimi disposition.

Kimi is not a bridge recipient and nothing new can be addressed to it, but
legacy Kimi rows may remain. No generic path (a drain, sweep, reclaim,
expiry, requeue, dead-letter, bulk acknowledgement or retention cleanup) may
write to one; reading is allowed. This test scans ``scripts/fleet_comms`` and
``scripts/ai_agent_bridge`` for every SQL ``INSERT``, ``UPDATE`` or ``DELETE``
on the stored-row tables below and requires each enclosing function to be in
``WRITERS`` with one disposition:

- ``SKIP``: a generic selection; the function itself excludes stored Kimi
  rows before it writes (a skip marker appears in its source).
- ``ADMITTED``: a fresh row whose target ``resolve_and_admit`` admitted (an
  admission marker appears in its source).
- ``KEYED``: every write names one row (or the ids a caller already
  selected) by its key; the caller that picks the key is a drain covered by
  the behavioural tests in ``tests/test_kimi_coding_only_admission.py``.
- ``NO_TARGET``: the row names no recipient or model.
- ``HELPER``: a side-row writer (event, dead letter, wake receipt, reply,
  job insert, telemetry); every call site in the two packages must be a
  declared caller, and SKIP or ADMITTED callers carry their marker.

A new write site, a new caller of a helper, or a stale entry fails the test.
Bounds: it reads SQL string literals (including f-string text) and named
calls; SQL built at run time from other variables, writes through another
module's API, and callbacks are not seen, and a marker's presence is not
proof that it guards every statement. The behavioural tests are the proof of
each disposition; this scan makes a new path impossible to add unclassified.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
_PACKAGES = ("fleet_comms", "ai_agent_bridge")

# Tables whose rows are a stored job, delivery, request or message, or a row recorded about one.
STORED_ROW_TABLES = frozenset(
    {
        "authority_jobs",
        "authority_job_events",
        "authority_dead_letters",
        "authority_deliveries",
        "authority_delivery_attempts",
        "authority_wake_receipts",
        "acp_conversations",
        "acp_conversation_events",
        "requests",
        "comms_messages",
        "messages",
        "deliveries",
        "channel_messages",
        "channel_events",
    }
)

SKIP, ADMITTED, KEYED, NO_TARGET, HELPER = "skip", "admitted", "keyed", "no-target", "helper"

_SKIP_MARKERS = (
    "kimi_row(",
    "kimi_message(",
    "stored_kimi_row(",
    "stored_kimi_request(",
    "_stored_kimi_job(",
    "_stored_kimi_delivery(",
    "skip_stored_kimi_row(",
)
_ADMIT_MARKERS = ("resolve_and_admit(", "_admit_recipients(", "require_admitted(", "_admitted_subscribers(")
_WRITE = re.compile(r"\b(UPDATE|INSERT(?:\s+OR\s+\w+)?\s+INTO|DELETE\s+FROM)\s+([A-Za-z_]\w*)", re.IGNORECASE)
_KEY_PREDICATE = re.compile(
    r"\bWHERE\s+(?:\w+\.)?(?:id|job_id|delivery_id|request_id|wake_id)\s*(?:=|IN\s*\()", re.IGNORECASE
)


@dataclass(frozen=True)
class Writer:
    disposition: str
    reason: str
    callers: dict[str, str] = field(default_factory=dict)  # "file::qualname" -> disposition (HELPER only)


def _fc(name: str) -> str:
    return f"fleet_comms/{name}"


def _br(name: str) -> str:
    return f"ai_agent_bridge/{name}"


_AUTH = _fc("authority.py")

# Channel telemetry emitters and the inbox functions that call them, each with a claimed thread.
_EMITTERS: dict[str, tuple[str, ...]] = {
    "emit_delivery_delivered": ("run_inbox", "_mark_claimed_delivered"),
    "emit_delivery_failed": ("run_inbox",),
    "emit_reply_started": ("_invoke_thread",),
    "emit_reply_complete": ("_mark_claimed_delivered",),
    "emit_heartbeat": ("_invoke_thread._heartbeat_loop",),
    "emit_model_cascade": (),
}

WRITERS: dict[str, Writer] = {
    # --- fleet_comms/authority.py: durable jobs and deliveries ---------------------------------------
    f"{_AUTH}::AuthorityService.claim_next_job": Writer(SKIP, "oldest queued job; stored Kimi jobs passed over"),
    f"{_AUTH}::AuthorityService.claim_job": Writer(SKIP, "named job; refused when Kimi, then the generic reclaim"),
    f"{_AUTH}::AuthorityService._requeue_terminal_job": Writer(SKIP, "retry/redrive by id; a Kimi job is refused"),
    f"{_AUTH}::AuthorityService._reclaim_expired_jobs_tx": Writer(SKIP, "deadline expiry and stale-lease requeue"),
    f"{_AUTH}::AuthorityService.claim_next_delivery": Writer(SKIP, "admitted recipient; Kimi-model request passed over"),
    f"{_AUTH}::AuthorityService._reclaim_expired_deliveries_tx": Writer(SKIP, "delivery expiry and requeue"),
    f"{_AUTH}::AuthorityService.finish_job": Writer(KEYED, "the fenced lease holder terminalizes its own job"),
    f"{_AUTH}::AuthorityService.finish_delivery": Writer(KEYED, "the fenced lease holder terminalizes its delivery"),
    f"{_AUTH}::AuthorityService.authorize_formal_review_substitution": Writer(
        KEYED, "one formal-review job; a formal review names no recipient"
    ),
    f"{_AUTH}::AuthorityService.enqueue_discussion": Writer(ADMITTED, "participants admitted before any insert"),
    f"{_AUTH}::AuthorityService._publish_message_tx": Writer(
        ADMITTED, "admitted targets or subscribers; a historical import records terminal history rows"
    ),
    f"{_AUTH}::AuthorityService._enqueue_job_tx": Writer(
        HELPER,
        "inserts one job for a message or conversation its caller admitted",
        {
            f"{_AUTH}::AuthorityService.enqueue_request": ADMITTED,
            f"{_AUTH}::AuthorityService.enqueue_discussion": ADMITTED,
            f"{_AUTH}::AuthorityService.enqueue_formal_review": NO_TARGET,
        },
    ),
    f"{_AUTH}::AuthorityService._append_job_event_tx": Writer(
        HELPER,
        "job event",
        {
            f"{_AUTH}::AuthorityService.claim_next_job": SKIP,
            f"{_AUTH}::AuthorityService.claim_job": SKIP,
            f"{_AUTH}::AuthorityService.finish_job": KEYED,
            f"{_AUTH}::AuthorityService.authorize_formal_review_substitution": KEYED,
            f"{_AUTH}::AuthorityService._requeue_terminal_job": SKIP,
            f"{_AUTH}::AuthorityService._reclaim_expired_jobs_tx": SKIP,
            f"{_AUTH}::AuthorityService._enqueue_job_tx": HELPER,
        },
    ),
    f"{_AUTH}::AuthorityService._dead_letter_job_tx": Writer(
        HELPER, "job dead letter", {f"{_AUTH}::AuthorityService._reclaim_expired_jobs_tx": SKIP}
    ),
    f"{_AUTH}::AuthorityService._dead_letter_delivery_tx": Writer(
        HELPER,
        "delivery dead letter",
        {
            f"{_AUTH}::AuthorityService.finish_delivery": KEYED,
            f"{_AUTH}::AuthorityService._reclaim_expired_deliveries_tx": SKIP,
        },
    ),
    f"{_AUTH}::AuthorityService._record_wake_receipt_tx": Writer(
        HELPER,
        "wake receipt",
        {
            f"{_AUTH}::AuthorityService.claim_next_delivery": SKIP,
            f"{_AUTH}::AuthorityService.record_supervisory_consumption": KEYED,
            f"{_AUTH}::AuthorityService.finish_delivery": KEYED,
            f"{_AUTH}::AuthorityService.record_wake_receipt": KEYED,
            f"{_AUTH}::AuthorityService._publish_message_tx": ADMITTED,
        },
    ),
    # --- fleet_comms: request executor, message plane, artifacts --------------------------------------
    f"{_fc('request_executor.py')}::RequestExecutor.create_request": Writer(
        ADMITTED, "recipient, endpoint successor and metadata model admitted before any insert"
    ),
    f"{_fc('request_executor.py')}::RequestExecutor.requeue_stale_running": Writer(
        SKIP, "stale running requests; recipient and message-metadata model read"
    ),
    f"{_fc('request_executor.py')}::RequestExecutor.execute_capture": Writer(KEYED, "claims the named request"),
    f"{_fc('request_executor.py')}::RequestExecutor._finalize_capture": Writer(
        HELPER,
        "terminal state and reply message of the request being executed",
        {f"{_fc('request_executor.py')}::RequestExecutor.execute_capture": KEYED},
    ),
    f"{_fc('request_executor.py')}::RequestExecutor.touch_claim": Writer(KEYED, "heartbeat of the claimant's request"),
    f"{_fc('request_executor.py')}::RequestExecutor._set_state": Writer(KEYED, "one request by id"),
    f"{_fc('request_executor.py')}::RequestExecutor.claim_v4_runner_execution": Writer(KEYED, "one request by id"),
    f"{_fc('message_plane.py')}::MessagePlane._bump_continuation": Writer(KEYED, "one request by id"),
    f"{_fc('artifacts.py')}::ArtifactStore._ensure_message_stub": Writer(NO_TARGET, "a note stub with no recipient"),
    # --- ai_agent_bridge: legacy messages ---------------------------------------------------------------
    f"{_br('_messaging.py')}::_insert_message": Writer(ADMITTED, "send_message's admitted target"),
    f"{_br('_messaging.py')}::acknowledge": Writer(KEYED, "named ids; drains skip stored Kimi rows first"),
    f"{_br('_messaging.py')}::acknowledge_all": Writer(SKIP, "a seat's unread messages"),
    f"{_br('_ask_lifecycle.py')}::record_ask_reply": Writer(KEYED, "the ask being answered"),
    f"{_br('_ask_lifecycle.py')}::mark_timeout_notices_shown": Writer(SKIP, "timed-out asks shown by the notice"),
    f"{_br('_ask_lifecycle.py')}::_re_fire_ask": Writer(SKIP, "watchdog retry of a dead ask"),
    f"{_br('_ask_lifecycle.py')}::_set_ask_status": Writer(KEYED, "one ask by id"),
    f"{_br('_ask_lifecycle.py')}::_store_fleet_request_id": Writer(KEYED, "the ask just registered"),
    f"{_br('_grok_build.py')}::_attempt_cancel_and_retell_retry": Writer(KEYED, "the ask being processed"),
    f"{_br('_broker.py')}::_cleanup_ancient_messages": Writer(SKIP, "force-acknowledge ancient messages"),
    f"{_br('_broker.py')}::broker_retention_cleanup": Writer(SKIP, "retention deletes of old terminal rows"),
    f"{_br('_db.py')}::get_db": Writer(SKIP, "one-time consumed_by_live_driver backfill"),
    # --- ai_agent_bridge: channel deliveries --------------------------------------------------------------
    f"{_br('_channels.py')}::_insert_delivery": Writer(ADMITTED, "post's admitted targets"),
    f"{_br('_channels.py')}::post": Writer(ADMITTED, "recipients admitted before any insert"),
    f"{_br('_channels.py')}::mark_delivery": Writer(KEYED, "one delivery by id"),
    f"{_br('_channels.py')}::mark_delivery_delivered": Writer(KEYED, "the claimant's delivery and attempt"),
    f"{_br('_channels.py')}::mark_delivery_failed": Writer(KEYED, "the claimant's delivery and attempt"),
    f"{_br('_channels.py')}::claim_next_delivery": Writer(SKIP, "oldest pending delivery"),
    f"{_br('_channels.py')}::release_expired_leases": Writer(SKIP, "expired processing leases"),
    f"{_br('_channels.py')}::expire_stale_deliveries": Writer(SKIP, "deliveries past their channel TTL"),
    f"{_br('_channels.py')}::bulk_expire_dead_lanes": Writer(SKIP, "pending deliveries of dead lanes"),
    f"{_br('_reconcile.py')}::reconcile_deliveries": Writer(SKIP, "deliveries whose reply already exists"),
    f"{_br('_inbox.py')}::_claim_next_thread": Writer(SKIP, "the inbox drain's thread claim"),
    f"{_br('_inbox.py')}::_update_claimed_status": Writer(KEYED, "the ids the filtered claim returned"),
    f"{_br('_channels_watch.py')}::append_channel_event": Writer(
        HELPER,
        "delivery telemetry",
        {f"{_br('_channels_watch.py')}::{name}": HELPER for name in _EMITTERS},
    ),
    # Each emitter reports on a thread the filtered inbox claim (``_claim_next_thread``) returned.
    **{
        f"{_br('_channels_watch.py')}::{name}": Writer(
            HELPER, "delivery telemetry", {f"{_br('_inbox.py')}::{caller}": KEYED for caller in callers}
        )
        for name, callers in _EMITTERS.items()
    },
}


def _docstring_ids(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                ids.add(id(first.value))
    return ids


def _sql_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            part.value if isinstance(part, ast.Constant) and isinstance(part.value, str) else "{}"
            for part in node.values
        )
    return None


@dataclass
class _Scan:
    writes: dict[str, list[tuple[int, str, str]]]  # function -> [(line, table, statement)]
    calls: dict[str, set[str]]  # callee name -> {calling function}
    sources: dict[str, str]  # function -> source


def _scan() -> _Scan:
    scan = _Scan({}, {}, {})
    for package in _PACKAGES:
        for path in sorted((_SCRIPTS / package).rglob("*.py")):
            rel = path.relative_to(_SCRIPTS).as_posix()
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
            docstrings = _docstring_ids(tree)

            def visit(node: ast.AST, qual: str, rel: str = rel, text: str = text, docstrings: set = docstrings) -> None:
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        name = f"{qual}.{child.name}" if qual else child.name
                        if not isinstance(child, ast.ClassDef):
                            scan.sources[f"{rel}::{name}"] = ast.get_source_segment(text, child) or ""
                        visit(child, name)
                        continue
                    key = f"{rel}::{qual}"
                    if isinstance(child, ast.Call):
                        func = child.func
                        callee = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
                        if callee:
                            scan.calls.setdefault(callee, set()).add(key)
                    statement = None if id(child) in docstrings else _sql_text(child)
                    if statement is not None:
                        for match in _WRITE.finditer(statement):
                            if match.group(2) in STORED_ROW_TABLES:
                                scan.writes.setdefault(key, []).append(
                                    (child.lineno, match.group(2), statement[match.start() :])
                                )
                        if isinstance(child, ast.JoinedStr):
                            continue
                    visit(child, qual)

            visit(tree, "")
    return scan


_SCANNED = _scan()


def test_the_scan_sees_the_known_writers():
    """Guards against a scanner that silently sees nothing."""
    assert len(_SCANNED.writes) >= 40
    assert f"{_AUTH}::AuthorityService._reclaim_expired_jobs_tx" in _SCANNED.writes


def test_every_stored_row_write_has_a_recorded_kimi_disposition():
    """A new write site on a stored-row table must be classified in ``WRITERS``; a stale entry fails too."""
    unclassified = sorted(
        f"{site} (line {writes[0][0]}, {writes[0][1]})"
        for site, writes in _SCANNED.writes.items()
        if site not in WRITERS
    )
    assert unclassified == [], "classify each new write path's Kimi disposition in WRITERS"
    stale = sorted(site for site, writer in WRITERS.items() if writer.disposition != HELPER and site not in _SCANNED.writes)
    assert stale == []


def test_generic_writers_skip_stored_kimi_rows_and_fresh_writers_are_admitted():
    missing = []
    for site, writer in WRITERS.items():
        source = _SCANNED.sources.get(site, "")
        if writer.disposition == SKIP and not any(marker in source for marker in _SKIP_MARKERS):
            missing.append(f"{site}: SKIP without a Kimi skip")
        if writer.disposition == ADMITTED and not any(marker in source for marker in _ADMIT_MARKERS):
            missing.append(f"{site}: ADMITTED without admission")
    assert missing == []


def test_keyed_writers_name_one_row_by_its_key():
    """A KEYED writer never selects rows generically: every stored-row write names its key."""
    unkeyed = [
        f"{site} line {line} ({table})"
        for site, writer in WRITERS.items()
        if writer.disposition == KEYED
        for line, table, statement in _SCANNED.writes.get(site, [])
        if not _KEY_PREDICATE.search(statement)
    ]
    assert unkeyed == []


def test_helpers_are_called_only_from_declared_callers():
    """Every call of a side-row writer is declared; SKIP and ADMITTED callers carry their marker."""
    problems = []
    for site, writer in WRITERS.items():
        if writer.disposition != HELPER:
            continue
        name = site.rsplit("::", 1)[1].rsplit(".", 1)[-1]
        actual = _SCANNED.calls.get(name, set())
        if actual != set(writer.callers):
            problems.append(f"{site}: callers {sorted(actual)} != declared {sorted(writer.callers)}")
        for caller, disposition in writer.callers.items():
            source = _SCANNED.sources.get(caller, "")
            markers = {SKIP: _SKIP_MARKERS, ADMITTED: _ADMIT_MARKERS}.get(disposition)
            if markers and not any(marker in source for marker in markers):
                problems.append(f"{caller}: declared {disposition} without its marker")
            if disposition == HELPER and caller not in WRITERS and not _SCANNED.calls.get(caller.rsplit(".", 1)[-1].rsplit("::", 1)[-1]):
                problems.append(f"{caller}: declared HELPER but is neither registered nor called")
    assert problems == []
