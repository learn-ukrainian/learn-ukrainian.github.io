"""Fleet-wide, exact-ID registry for durable thread rollover packets.

The registry projects the existing task-family identity envelope; it does not
create another task identity.  Its key is exactly ``(agent, lineage_id,
rollover_id)`` and task titles remain display-only metadata.  Native app facts
enter only through explicit snapshots or existing immutable receipts.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .. import task_identity
from .planner import canonical_json, sha256_digest
from .storage import advisory_lock, atomic_write_json

REGISTRY_SCHEMA_VERSION = 1
REGISTRY_RELATIVE_ROOT = Path(".agent/thread-rollover-registry/v1")
DEFAULT_STALE_HOURS = 24.0
LINEAGE_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
ROLLOVER_ID_RE = re.compile(r"^rollover-[a-z0-9]+(?:-[a-z0-9]+)*$")

_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_SCHEMA_PATH = _ROOT / "agents_extensions" / "shared" / "schemas" / "rollover-registry.v1.schema.json"
_TASK_IDENTITY_SCHEMA_PATH = _ROOT / "agents_extensions" / "shared" / "schemas" / "task-identity.v1.schema.json"
_REGISTRY_SCHEMA = json.loads(_REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))
_TASK_IDENTITY_SCHEMA = json.loads(_TASK_IDENTITY_SCHEMA_PATH.read_text(encoding="utf-8"))
_SCHEMA_REGISTRY = Registry().with_resource(
    task_identity.IDENTITY_SCHEMA_VERSION,
    Resource.from_contents(_TASK_IDENTITY_SCHEMA),
)
_REGISTRY_VALIDATOR = Draft202012Validator(
    _REGISTRY_SCHEMA,
    registry=_SCHEMA_REGISTRY,
    format_checker=FormatChecker(),
)


class RolloverState(StrEnum):
    PREPARED = "PREPARED"
    AWAITING_NATIVE_CREATE = "AWAITING_NATIVE_CREATE"
    REPLACEMENT_CREATED = "REPLACEMENT_CREATED"
    RESUMED = "RESUMED"
    STRICT_RECALL_PASSED = "STRICT_RECALL_PASSED"
    CANARY_PASSED = "CANARY_PASSED"
    CONFIRMED = "CONFIRMED"
    PREDECESSOR_ARCHIVED = "PREDECESSOR_ARCHIVED"
    HEARTBEAT_RETIRED = "HEARTBEAT_RETIRED"
    SUPERSEDED = "SUPERSEDED"
    ABANDONED_WITH_PROOF = "ABANDONED_WITH_PROOF"
    BLOCKED = "BLOCKED"


class AuditClassification(StrEnum):
    ACTIVE_RESUMABLE = "active and resumable"
    AWAITING_NATIVE_ACTION = "awaiting native action"
    CONFIRMED_INCOMPLETE_CLEANUP = "confirmed but incompletely cleaned"
    CONFIRMED_FULLY_CLEANED = "confirmed and fully cleaned"
    SUPERSEDED = "superseded"
    STALE_ADJUDICATION = "stale and requiring operator adjudication"
    INCONSISTENT_CORRUPT = "inconsistent or corrupt"


class MaintenanceAction(StrEnum):
    FINISH_CLEANUP = "finish-cleanup"
    SUPERSEDE = "supersede"
    ABANDON = "abandon"


TERMINAL_STATES = frozenset(
    {
        RolloverState.SUPERSEDED,
        RolloverState.ABANDONED_WITH_PROOF,
    }
)
LIVE_PENDING_STATES = frozenset(
    {
        RolloverState.PREPARED,
        RolloverState.AWAITING_NATIVE_CREATE,
        RolloverState.REPLACEMENT_CREATED,
        RolloverState.RESUMED,
        RolloverState.STRICT_RECALL_PASSED,
        RolloverState.CANARY_PASSED,
        RolloverState.BLOCKED,
    }
)
SUCCESS_SEQUENCE = (
    RolloverState.PREPARED,
    RolloverState.AWAITING_NATIVE_CREATE,
    RolloverState.REPLACEMENT_CREATED,
    RolloverState.RESUMED,
    RolloverState.STRICT_RECALL_PASSED,
    RolloverState.CANARY_PASSED,
    RolloverState.CONFIRMED,
    RolloverState.PREDECESSOR_ARCHIVED,
    RolloverState.HEARTBEAT_RETIRED,
)
SUCCESS_RANK = {state: index for index, state in enumerate(SUCCESS_SEQUENCE)}


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _clean_agent(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("registry agent must be a string")
    agent = value.strip().lower()
    if agent != value or not agent or not agent[0].isalpha() or not all(c.isalnum() or c == "-" for c in agent):
        raise ValueError("registry agent must be a lowercase path-safe identifier")
    return agent


def normalize_agent(value: str) -> str:
    return _clean_agent(value)


def normalize_lineage_id(value: str) -> str:
    lineage_id = value.strip().lower()
    if lineage_id != value or not LINEAGE_ID_RE.fullmatch(lineage_id):
        raise ValueError("lineage ids must match [a-z][a-z0-9-]{0,63}")
    return lineage_id


def normalize_rollover_id(value: str) -> str:
    rollover_id = value.strip().lower()
    if rollover_id != value or not ROLLOVER_ID_RE.fullmatch(rollover_id):
        raise ValueError("rollover ids must match rollover-[a-z0-9]+(-[a-z0-9]+)*")
    return rollover_id


def _assert_within_state_root(state_root: Path, path: Path, *, label: str) -> Path:
    root = state_root.resolve()
    try:
        path.resolve().relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} must remain inside the repository state root") from exc
    return path


def registry_root(state_root: Path) -> Path:
    return _assert_within_state_root(
        state_root,
        state_root.resolve() / REGISTRY_RELATIVE_ROOT,
        label="rollover registry root",
    )


def record_path(state_root: Path, *, agent: str, lineage_id: str, rollover_id: str) -> Path:
    return _assert_within_state_root(
        state_root,
        registry_root(state_root)
        / _clean_agent(agent)
        / normalize_lineage_id(lineage_id)
        / normalize_rollover_id(rollover_id)
        / "record.json",
        label="rollover registry record",
    )


def lineage_lock_path(state_root: Path, *, agent: str, lineage_id: str) -> Path:
    return _assert_within_state_root(
        state_root,
        state_root.resolve()
        / ".agent"
        / "thread-rollovers"
        / _clean_agent(agent)
        / normalize_lineage_id(lineage_id)
        / ".native-intent.lock",
        label="rollover lineage lock",
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read durable JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"durable JSON must be an object: {path}")
    return value


def _validate_existing_json_sources(state_root: Path, values: Iterable[object]) -> None:
    root = state_root.resolve()
    for value in values:
        if not isinstance(value, (str, Path)) or not str(value):
            continue
        candidate = Path(value)
        candidate = candidate if candidate.is_absolute() else root / candidate
        _assert_within_state_root(state_root, candidate, label="rollover JSON source")
        if candidate.is_file() and candidate.suffix == ".json":
            _load_json(candidate)


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _dedupe_strings(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip() and value not in result:
            result.append(value)
    return result


def _require_durable_paths(state_root: Path, values: Iterable[object], *, label: str) -> list[str]:
    root = state_root.resolve()
    durable = _dedupe_strings(values)
    for value in durable:
        candidate = Path(value)
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"{label} must remain inside the repository state root: {value}") from exc
        if not resolved.is_file():
            raise ValueError(f"{label} does not exist as durable evidence: {value}")
    return durable


def _key(record: Mapping[str, Any]) -> tuple[str, str, str]:
    key = record.get("key")
    if not isinstance(key, Mapping):
        raise ValueError("registry record key is missing")
    return (
        _clean_agent(key.get("agent")),
        normalize_lineage_id(str(key.get("lineage_id") or "")),
        normalize_rollover_id(str(key.get("rollover_id") or "")),
    )


def _identity(record: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    identity = task_identity.validate_identity(record.get("task_identity") or {})
    transition = task_identity.validate_title_transition(
        record.get("title_transition") or {},
        identity,
    )
    return identity, transition


def validate_record(record: Mapping[str, Any], *, path: Path | None = None) -> dict[str, Any]:
    errors = sorted(_REGISTRY_VALIDATOR.iter_errors(record), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise ValueError(f"rollover registry schema violation at {location}: {first.message}")
    if record.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ValueError(f"unsupported rollover registry schema_version: {record.get('schema_version')!r}")
    agent, lineage_id, rollover_id = _key(record)
    identity, _ = _identity(record)
    if identity["lineage_id"] != lineage_id:
        raise ValueError("task identity lineage does not match the registry key")
    try:
        state = RolloverState(str(record.get("state")))
        last_successful_boundary = RolloverState(str(record.get("last_successful_boundary")))
    except ValueError as exc:
        raise ValueError("registry record has an unknown lifecycle state") from exc
    if last_successful_boundary not in SUCCESS_RANK:
        raise ValueError("last_successful_boundary must be an ordered successful lifecycle boundary")
    if state is RolloverState.BLOCKED and not str(record.get("blocking_reason") or "").strip():
        raise ValueError("blocked registry state requires a blocking reason")
    if state in TERMINAL_STATES and not str(record.get("terminal_reason") or "").strip():
        raise ValueError("terminal registry state requires a terminal reason")
    effective_boundary = last_successful_boundary if state in TERMINAL_STATES or state is RolloverState.BLOCKED else state
    if (
        SUCCESS_RANK.get(effective_boundary, -1) >= SUCCESS_RANK[RolloverState.REPLACEMENT_CREATED]
        and not identity.get("replacement_task_id")
    ):
        raise ValueError("replacement-created registry state requires the canonical replacement task identity")
    if (
        SUCCESS_RANK.get(effective_boundary, -1) >= SUCCESS_RANK[RolloverState.RESUMED]
        and identity["lifecycle_state"] not in {"resumed", "confirmed"}
    ):
        raise ValueError("resumed registry state requires a resumed canonical task identity")
    if (
        SUCCESS_RANK.get(effective_boundary, -1) >= SUCCESS_RANK[RolloverState.CONFIRMED]
        and identity["lifecycle_state"] != "confirmed"
    ):
        raise ValueError("confirmed registry state requires a confirmed canonical task identity")
    if not isinstance(record.get("timestamps"), Mapping):
        raise ValueError("registry record requires timestamps")
    if not isinstance(record.get("history"), list):
        raise ValueError("registry record history must be a list")
    packet_paths = record.get("packet_paths")
    receipts = record.get("receipts")
    evidence_paths = record.get("evidence_paths")
    if not isinstance(packet_paths, Mapping) or not isinstance(receipts, list) or not isinstance(evidence_paths, list):
        raise ValueError("registry packet paths, receipts, and evidence paths are malformed")
    durable_paths: list[object] = [
        record.get("lease_path"),
        *receipts,
        *evidence_paths,
        *packet_paths.values(),
    ]
    for value in durable_paths:
        if value is None:
            continue
        candidate = Path(str(value))
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("registry durable paths must be repository-relative and non-traversing")
    if path is not None:
        expected = record_path(path.parents[6], agent=agent, lineage_id=lineage_id, rollover_id=rollover_id)
        if path.resolve() != expected.resolve():
            raise ValueError("registry record key does not match its canonical path")
    return dict(record)


def load_record(state_root: Path, *, agent: str, lineage_id: str, rollover_id: str) -> dict[str, Any]:
    path = record_path(state_root, agent=agent, lineage_id=lineage_id, rollover_id=rollover_id)
    return validate_record(_load_json(path), path=path)


def _event(
    state: RolloverState,
    *,
    at: str,
    reason: str,
    evidence_paths: Iterable[str] = (),
    operation_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "state": state.value,
        "at": at,
        "reason": reason,
        "evidence_paths": _dedupe_strings(evidence_paths),
    }
    if operation_id:
        payload["operation_id"] = operation_id
    return payload


def _append_history(record: dict[str, Any], event: dict[str, Any]) -> None:
    history = list(record.get("history") or [])
    identity = (event.get("state"), event.get("operation_id"), event.get("reason"))
    if not any((item.get("state"), item.get("operation_id"), item.get("reason")) == identity for item in history):
        history.append(event)
    record["history"] = history


def _task_family_paths(state_root: Path, native: Mapping[str, Any]) -> dict[str, Path]:
    family = native.get("family_id")
    operation = native.get("operation_id")
    if not isinstance(family, str) or not family or not isinstance(operation, str) or not operation:
        return {}
    for label, value in (("family_id", family), ("operation_id", operation)):
        if value in {".", ".."} or "/" in value or "\\" in value or "\x00" in value:
            raise ValueError(f"native {label} must be a path-safe component")
    root = _assert_within_state_root(
        state_root,
        state_root / ".agent" / "task-families" / family / "operations" / operation,
        label="native task-family operation",
    )
    return {
        "root": root,
        "plan": root / "rollover-plan.json",
        "binding": root / "rollover-binding.json",
        "state": root / "state.json",
        "receipt": root / "receipt.json",
        "archive_authorization": root / "rollover-archive-authorization.json",
    }


def _effective_state_from_lease(state_root: Path, lease: Mapping[str, Any]) -> tuple[RolloverState, str | None]:
    replacement = lease.get("replacement")
    if not isinstance(replacement, Mapping):
        raise ValueError("lease replacement is missing")
    native = replacement.get("native_lifecycle")
    native = native if isinstance(native, Mapping) else {}
    family_paths = _task_family_paths(state_root, native)
    task_state: dict[str, Any] = {}
    if (path := family_paths.get("state")) is not None and path.is_file():
        task_state = _load_json(path)
    task_status = (
        (task_state.get("details") or {}).get("status") if isinstance(task_state.get("details"), Mapping) else None
    )
    native_status = native.get("status")
    blocked_statuses = (task_status, native_status)
    is_blocked = task_state.get("state") == "blocked" or any(
        isinstance(value, str) and ("blocked" in value or "failed" in value) for value in blocked_statuses
    )
    blocking_reason: str | None = None
    if is_blocked:
        task_details = task_state.get("details") if isinstance(task_state.get("details"), Mapping) else {}
        recorded_status = task_details.get("status") or native_status or "unknown native boundary"
        recorded_error = task_details.get("error")
        blocking_reason = f"native rollover boundary blocked: {recorded_status}"
        if isinstance(recorded_error, str) and recorded_error.strip():
            blocking_reason += f" ({recorded_error.strip()})"
    if task_status == "superseded_before_native_create":
        if (
            replacement.get("status") in {"resumed", "started"}
            or (
                isinstance(native.get("replacement_thread_id"), str)
                and native["replacement_thread_id"].strip()
            )
        ):
            raise ValueError("superseded-before-create receipt conflicts with an exact native replacement")
        return RolloverState.SUPERSEDED, blocking_reason
    if task_status == "archive_reconciled":
        if is_blocked:
            raise ValueError("native task-family state cannot be both archived and blocked")
        return RolloverState.PREDECESSOR_ARCHIVED, None
    if replacement.get("status") == "started":
        return RolloverState.CONFIRMED, blocking_reason
    if is_blocked:
        return RolloverState.BLOCKED, blocking_reason
    if replacement.get("status") == "resumed":
        return RolloverState.RESUMED, None
    if isinstance(native.get("replacement_thread_id"), str) and native["replacement_thread_id"].strip():
        return RolloverState.REPLACEMENT_CREATED, None
    return RolloverState.AWAITING_NATIVE_CREATE, None


def _state_prefix(state: RolloverState) -> tuple[RolloverState, ...]:
    if state in TERMINAL_STATES or state is RolloverState.BLOCKED:
        return (RolloverState.PREPARED, state)
    return SUCCESS_SEQUENCE[: SUCCESS_RANK[state] + 1]


def record_from_lease(
    state_root: Path,
    lease_path: Path,
    lease: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or utc_now()
    _assert_within_state_root(state_root, lease_path, label="rollover lease")
    agent = _clean_agent(lease.get("agent"))
    normalized_lease, migrated = task_identity.backfill_legacy_identity(
        lease,
        agent=agent,
        repository=task_identity.DEFAULT_REPOSITORY,
        now=isoformat_z(now),
    )
    lease = normalized_lease
    lineage_id = normalize_lineage_id(str(lease.get("lineage_id") or ""))
    replacement = lease.get("replacement")
    active = lease.get("active")
    if not isinstance(replacement, Mapping) or not isinstance(active, Mapping):
        raise ValueError("lease requires active and replacement objects")
    rollover_id = normalize_rollover_id(str(replacement.get("rollover_id") or ""))
    if replacement.get("lineage_id") != lineage_id or lease.get("rollover_id") != rollover_id:
        raise ValueError("lease exact identity fields disagree")
    source_thread_id = active.get("thread_id")
    if not isinstance(source_thread_id, str) or not source_thread_id.strip():
        raise ValueError("lease source thread identity is missing")
    identity = task_identity.validate_identity(replacement.get("identity") or {})
    title_transition = task_identity.validate_title_transition(
        replacement.get("title_transition") or {},
        identity,
    )
    if identity["lineage_id"] != lineage_id:
        raise ValueError("lease task identity lineage does not match the rollover")
    if identity["predecessor_task_id"] != source_thread_id:
        raise ValueError("lease task identity predecessor does not match the active task")
    native = replacement.get("native_lifecycle")
    native = native if isinstance(native, Mapping) else {}
    replacement_thread_id = (
        native.get("replacement_thread_id") or replacement.get("thread_id") or replacement.get("resumed_thread_id")
    )
    if replacement_thread_id and identity.get("replacement_task_id") != replacement_thread_id:
        raise ValueError("lease task identity replacement does not match the exact native binding")
    if migrated and isinstance(replacement_thread_id, str):
        if replacement.get("status") == "resumed":
            identity = task_identity.mark_resumed(
                identity,
                title_transition,
                replacement_task_id=replacement_thread_id,
            )
        elif replacement.get("status") == "started":
            identity = task_identity.mark_confirmed(
                identity,
                title_transition,
                replacement_task_id=replacement_thread_id,
            )
    family_paths = _task_family_paths(state_root, native)
    packet_path_keys = (
        "runtime_path",
        "handoff_path",
        "bootstrap_prompt_path",
        "semantic_snapshot_path",
        "strict_probe_path",
        "strict_questions_path",
        "strict_answers_path",
        "strict_verdict_path",
        "canary_proof_path",
    )
    _validate_existing_json_sources(
        state_root,
        [*family_paths.values(), *(replacement.get(key) for key in packet_path_keys)],
    )
    state, blocking_reason = _effective_state_from_lease(state_root, lease)
    strict = replacement.get("strict_verdict")
    strict = strict if isinstance(strict, Mapping) else {}
    strict_result = strict.get("verdict") or strict.get("status")
    strict_state = (
        "passed" if strict_result == "PASS" else "failed" if isinstance(strict_result, str) else "pending"
    )
    strict_score = strict.get("score")
    if strict_score is None:
        strict_score = strict.get("correct")
    canary = replacement.get("canary_proof")
    canary = canary if isinstance(canary, Mapping) else {}
    cleanup = lease.get("cleanup")
    cleanup = cleanup if isinstance(cleanup, Mapping) else {}
    prepared_at = str(replacement.get("prepared_at") or lease.get("updated_at") or isoformat_z(now))
    updated_at = str(lease.get("updated_at") or replacement.get("confirmed_at") or prepared_at)
    evidence = [
        _relative(lease_path, state_root),
        *(replacement.get(key) for key in ("handoff_path", "canary_proof_path", "strict_verdict_path")),
        *(_relative(path, state_root) for path in family_paths.values() if path.is_file()),
    ]
    last_success = state
    if state in TERMINAL_STATES or state is RolloverState.BLOCKED:
        last_success = RolloverState.AWAITING_NATIVE_CREATE
        if isinstance(replacement_thread_id, str) and replacement_thread_id.strip():
            last_success = RolloverState.REPLACEMENT_CREATED
        if replacement.get("status") in {"resumed", "started"}:
            last_success = RolloverState.RESUMED
        if strict_state == "passed":
            last_success = RolloverState.STRICT_RECALL_PASSED
        if canary.get("status") == "PASS":
            last_success = RolloverState.CANARY_PASSED
        if replacement.get("status") == "started":
            last_success = RolloverState.CONFIRMED
        if state in TERMINAL_STATES and SUCCESS_RANK[last_success] >= SUCCESS_RANK[RolloverState.REPLACEMENT_CREATED]:
            raise ValueError("terminal legacy rollover conflicts with an exact native replacement")
    history_states = _state_prefix(state)
    if state in TERMINAL_STATES or state is RolloverState.BLOCKED:
        history_states = (*SUCCESS_SEQUENCE[: SUCCESS_RANK[last_success] + 1], state)
    history = [
        _event(
            boundary, at=prepared_at if boundary is RolloverState.PREPARED else updated_at, reason="lease projection"
        )
        for boundary in history_states
    ]
    record = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "key": {"agent": agent, "lineage_id": lineage_id, "rollover_id": rollover_id},
        "task_identity": identity,
        "title_transition": title_transition,
        "state": state.value,
        "last_successful_boundary": last_success.value,
        "native_creation": {
            "state": native.get("status") or "legacy_or_unrecorded",
            "family_id": native.get("family_id"),
            "operation_id": native.get("operation_id"),
        },
        "strict_recall": {
            "state": strict_state,
            "score": strict_score,
            "verdict_path": replacement.get("strict_verdict_path"),
        },
        "canary": {
            "state": "passed" if canary.get("status") == "PASS" else "pending",
            "proof_path": replacement.get("canary_proof_path"),
        },
        "confirmation": {
            "state": "confirmed" if replacement.get("status") == "started" else "pending",
            "confirmed_at": replacement.get("confirmed_at"),
            "confirmed_by": cleanup.get("confirmed_by"),
        },
        "predecessor_archival": {
            "state": "archived"
            if state in {RolloverState.PREDECESSOR_ARCHIVED, RolloverState.HEARTBEAT_RETIRED}
            else "pending",
        },
        "heartbeat": {
            "automation_id": active.get("automation_id"),
            "state": "cleanup_authorized" if cleanup.get("old_automation_ready_to_delete") else "active_or_unknown",
            "cleanup_authorized": bool(cleanup.get("old_automation_ready_to_delete")),
        },
        "timestamps": {"prepared_at": prepared_at, "updated_at": updated_at},
        "lease_path": _relative(lease_path, state_root),
        "packet_paths": {
            key: replacement.get(key) for key in packet_path_keys
        },
        "receipts": _dedupe_strings(_relative(path, state_root) for path in family_paths.values() if path.is_file()),
        "evidence_paths": _dedupe_strings(evidence),
        "terminal_reason": "superseded by exact task-family receipt" if state is RolloverState.SUPERSEDED else None,
        "blocking_reason": blocking_reason,
        "last_reconciliation": None,
        "history": history,
    }
    return validate_record(record)


def _merge_projection(existing: dict[str, Any], projected: dict[str, Any]) -> dict[str, Any]:
    current = RolloverState(existing["state"])
    candidate = RolloverState(projected["state"])
    last_success = RolloverState(existing["last_successful_boundary"])
    projected_last_success = RolloverState(projected["last_successful_boundary"])
    projected_boundary = (
        projected_last_success if candidate in TERMINAL_STATES or candidate is RolloverState.BLOCKED else candidate
    )
    projection_not_behind = SUCCESS_RANK[projected_boundary] >= SUCCESS_RANK[last_success]
    projection_advances = SUCCESS_RANK[projected_boundary] > SUCCESS_RANK[last_success]
    merged = dict(existing)
    durable_identity, _ = _identity(existing)
    projected_identity, _ = _identity(projected)
    immutable_identity_fields = set(durable_identity) - {"replacement_task_id", "lifecycle_state"}
    for field in immutable_identity_fields:
        if durable_identity.get(field) != projected_identity.get(field):
            raise ValueError(f"projected task identity {field} conflicts with the durable registry")
    durable_replacement = durable_identity.get("replacement_task_id")
    projected_replacement = projected_identity.get("replacement_task_id")
    if durable_replacement and projected_replacement and durable_replacement != projected_replacement:
        raise ValueError("projected replacement_task_id conflicts with the durable registry")
    if projection_not_behind and (projected_replacement or not durable_replacement):
        merged["task_identity"] = projected["task_identity"]
        merged["title_transition"] = projected["title_transition"]
    for key in ("lease_path", "packet_paths"):
        value = projected.get(key)
        if value is not None:
            merged[key] = value
    if projection_not_behind:
        for key in (
            "native_creation",
            "strict_recall",
            "canary",
            "confirmation",
            "predecessor_archival",
            "heartbeat",
        ):
            value = projected.get(key)
            if value is not None:
                merged[key] = value
        if current is not RolloverState.BLOCKED or candidate is RolloverState.BLOCKED or projection_advances:
            merged["blocking_reason"] = projected.get("blocking_reason")
    merged["receipts"] = _dedupe_strings([*existing.get("receipts", []), *projected.get("receipts", [])])
    merged["evidence_paths"] = _dedupe_strings(
        [*existing.get("evidence_paths", []), *projected.get("evidence_paths", [])]
    )
    if current not in TERMINAL_STATES:
        if candidate in TERMINAL_STATES and projection_not_behind:
            if SUCCESS_RANK.get(last_success, 0) >= SUCCESS_RANK[RolloverState.CONFIRMED]:
                raise ValueError("confirmed active rollover cannot be superseded by a projected legacy state")
            merged["state"] = candidate.value
            merged["last_successful_boundary"] = projected_last_success.value
            merged["terminal_reason"] = projected.get("terminal_reason")
        elif candidate is RolloverState.BLOCKED and projection_not_behind:
            merged["state"] = candidate.value
            merged["last_successful_boundary"] = projected_last_success.value
            merged["blocking_reason"] = projected.get("blocking_reason")
        elif projection_advances:
            merged["state"] = candidate.value
            merged["last_successful_boundary"] = candidate.value
            merged["blocking_reason"] = projected.get("blocking_reason")
    for event in projected.get("history", []):
        if (
            candidate in TERMINAL_STATES or candidate is RolloverState.BLOCKED
        ) and not projection_not_behind and event.get("state") == candidate.value:
            continue
        _append_history(merged, event)
    timestamps = dict(existing.get("timestamps") or {})
    timestamps.update({key: value for key, value in projected.get("timestamps", {}).items() if value})
    merged["timestamps"] = timestamps
    return validate_record(merged)


def sync_from_lease(
    state_root: Path,
    lease_path: Path,
    lease: Mapping[str, Any],
    *,
    already_locked: bool = False,
) -> dict[str, Any]:
    projected = record_from_lease(state_root, lease_path, lease)
    agent, lineage_id, rollover_id = _key(projected)
    path = record_path(state_root, agent=agent, lineage_id=lineage_id, rollover_id=rollover_id)

    def write() -> None:
        nonlocal projected
        if path.is_file():
            projected = _merge_projection(validate_record(_load_json(path), path=path), projected)
        atomic_write_json(path, projected)

    if already_locked:
        write()
    else:
        with advisory_lock(lineage_lock_path(state_root, agent=agent, lineage_id=lineage_id)):
            write()
    return projected


def transition(
    state_root: Path,
    *,
    agent: str,
    lineage_id: str,
    rollover_id: str,
    state: RolloverState,
    reason: str,
    evidence_paths: Iterable[str] = (),
    operation_id: str | None = None,
    updates: Mapping[str, Any] | None = None,
    already_locked: bool = False,
) -> dict[str, Any]:
    path = record_path(state_root, agent=agent, lineage_id=lineage_id, rollover_id=rollover_id)

    def apply() -> dict[str, Any]:
        record = validate_record(_load_json(path), path=path)
        if operation_id and any(
            event.get("operation_id") == operation_id and event.get("state") == state.value
            for event in record.get("history", [])
        ):
            return record
        current = RolloverState(record["state"])
        if current in TERMINAL_STATES and current is not state:
            raise ValueError(f"terminal rollover {current.value} cannot transition to {state.value}")
        if (
            state in TERMINAL_STATES
            and SUCCESS_RANK.get(RolloverState(record["last_successful_boundary"]), 0)
            >= SUCCESS_RANK[RolloverState.CONFIRMED]
        ):
            raise ValueError("confirmed active rollover cannot be superseded or abandoned")
        if state not in TERMINAL_STATES and state is not RolloverState.BLOCKED:
            last = RolloverState(record["last_successful_boundary"])
            if current is RolloverState.BLOCKED and SUCCESS_RANK[state] <= SUCCESS_RANK[last]:
                raise ValueError("blocked rollover requires authoritative proof beyond its last successful boundary")
            if SUCCESS_RANK[state] < SUCCESS_RANK.get(last, 0):
                return record
            if SUCCESS_RANK[state] > SUCCESS_RANK.get(last, 0) + 1:
                raise ValueError(
                    f"rollover boundary {state.value} cannot skip past {last.value}; "
                    "reconcile and persist each prerequisite boundary"
                )
            record["last_successful_boundary"] = state.value
            record["blocking_reason"] = None
        record["state"] = state.value
        at = isoformat_z(utc_now())
        _append_history(
            record,
            _event(state, at=at, reason=reason, evidence_paths=evidence_paths, operation_id=operation_id),
        )
        record["timestamps"] = {**record.get("timestamps", {}), "updated_at": at}
        record["evidence_paths"] = _dedupe_strings([*record.get("evidence_paths", []), *evidence_paths])
        if state is RolloverState.BLOCKED:
            record["blocking_reason"] = reason
        if state in TERMINAL_STATES:
            record["terminal_reason"] = reason
        if state is RolloverState.REPLACEMENT_CREATED:
            record["native_creation"] = {**record["native_creation"], "state": "replacement_created"}
        elif state is RolloverState.STRICT_RECALL_PASSED:
            record["strict_recall"] = {**record["strict_recall"], "state": "passed"}
        elif state is RolloverState.CANARY_PASSED:
            record["canary"] = {**record["canary"], "state": "passed"}
        elif state is RolloverState.CONFIRMED:
            record["confirmation"] = {**record["confirmation"], "state": "confirmed", "confirmed_at": at}
        elif state is RolloverState.PREDECESSOR_ARCHIVED:
            record["predecessor_archival"] = {**record["predecessor_archival"], "state": "archived"}
        elif state is RolloverState.HEARTBEAT_RETIRED:
            record["heartbeat"] = {**record["heartbeat"], "state": "retired"}
        if updates:
            allowed_updates = {
                "native_creation",
                "task_identity",
                "title_transition",
                "strict_recall",
                "canary",
                "confirmation",
                "predecessor_archival",
                "heartbeat",
            }
            for key, value in updates.items():
                if key not in allowed_updates:
                    raise ValueError(f"registry transition update is not allowed for {key}")
                record[key] = value
        if state is RolloverState.RESUMED:
            identity, title_transition = _identity(record)
            replacement_task_id = identity.get("replacement_task_id")
            if not isinstance(replacement_task_id, str):
                raise ValueError("resume requires the canonical replacement task identity")
            record["task_identity"] = task_identity.mark_resumed(
                identity,
                title_transition,
                replacement_task_id=replacement_task_id,
            )
        elif state is RolloverState.CONFIRMED:
            identity, title_transition = _identity(record)
            replacement_task_id = identity.get("replacement_task_id")
            if not isinstance(replacement_task_id, str):
                raise ValueError("confirmation requires the canonical replacement task identity")
            record["task_identity"] = task_identity.mark_confirmed(
                identity,
                title_transition,
                replacement_task_id=replacement_task_id,
            )
        validate_record(record, path=path)
        atomic_write_json(path, record)
        return record

    if already_locked:
        return apply()
    with advisory_lock(lineage_lock_path(state_root, agent=agent, lineage_id=lineage_id)):
        return apply()


def _minimal_record_from_plan(state_root: Path, plan_path: Path, plan: Mapping[str, Any]) -> dict[str, Any]:
    _assert_within_state_root(state_root, plan_path, label="task-family rollover plan")
    agent = _clean_agent(plan.get("agent"))
    lineage_id = normalize_lineage_id(str(plan.get("lineage_id") or ""))
    rollover_id = normalize_rollover_id(str(plan.get("rollover_id") or ""))
    operation_root = plan_path.parent
    task_state = _load_json(operation_root / "state.json") if (operation_root / "state.json").is_file() else {}
    details = task_state.get("details") if isinstance(task_state.get("details"), Mapping) else {}
    status = details.get("status")
    state = RolloverState.AWAITING_NATIVE_CREATE
    if status == "superseded_before_native_create":
        state = RolloverState.SUPERSEDED
    elif task_state.get("state") == "blocked" or (
        isinstance(status, str) and ("blocked" in status or "failed" in status)
    ):
        state = RolloverState.BLOCKED
    binding = (
        _load_json(operation_root / "rollover-binding.json")
        if (operation_root / "rollover-binding.json").is_file()
        else {}
    )
    created_at = datetime.fromtimestamp(plan_path.stat().st_mtime, tz=UTC).replace(microsecond=0)
    source_thread_id = str(plan.get("source_thread_id") or "")
    if not source_thread_id:
        raise ValueError("legacy rollover plan has no source thread identity")
    generation = plan.get("generation")
    if not isinstance(generation, int) or generation < 1:
        raise ValueError("legacy rollover plan has no valid generation")
    plan_identity = plan.get("task_identity")
    if isinstance(plan_identity, Mapping):
        identity = task_identity.validate_identity(plan_identity)
        harness = task_identity.default_harness(agent)
    else:
        intended_title = str(plan.get("intended_title") or "").strip()
        semantic_title = intended_title.split(" — ", 1)[-1].strip()
        try:
            task_identity.validate_semantic_title(semantic_title)
        except ValueError:
            semantic_title = "Recover predecessor task context"
        identity = task_identity.build_identity(
            repository=task_identity.DEFAULT_REPOSITORY,
            stream_epic=None,
            stream_epic_url=None,
            github_issue_number=None,
            github_issue_url=None,
            semantic_title=semantic_title,
            task_family="thread-rollover",
            role=agent,
            predecessor_task_id=source_thread_id,
            replacement_task_id=None,
            lineage_id=lineage_id,
            generation=generation,
            terminal_goal=task_identity.LEGACY_TERMINAL_GOAL,
            migration_source="legacy-task-family-plan",
            legacy_fallback=True,
        )
        harness = f"{task_identity.default_harness(agent)}-legacy"
    if identity["lineage_id"] != lineage_id or identity["generation"] != generation:
        raise ValueError("task-family plan identity does not match its exact lineage and generation")
    if identity["predecessor_task_id"] != source_thread_id:
        raise ValueError("task-family plan identity does not match its exact predecessor")
    title_transition = task_identity.new_title_transition(
        harness=harness,
        visible_title_value=identity["visible_title"],
        prepared_at=isoformat_z(created_at),
    )
    bound_replacement = binding.get("replacement_thread_id")
    if isinstance(bound_replacement, str) and bound_replacement:
        if state in TERMINAL_STATES:
            raise ValueError("terminal task-family receipt conflicts with an exact native replacement")
        identity, title_transition = task_identity.bind_replacement(
            identity,
            title_transition,
            replacement_task_id=bound_replacement,
            evidence=f"Exact task-family binding at {_relative(operation_root / 'rollover-binding.json', state_root)}.",
            now=isoformat_z(created_at),
        )
        if state is not RolloverState.BLOCKED:
            state = RolloverState.REPLACEMENT_CREATED
    last_success = state
    if state in TERMINAL_STATES or state is RolloverState.BLOCKED:
        last_success = (
            RolloverState.REPLACEMENT_CREATED
            if isinstance(bound_replacement, str) and bound_replacement
            else RolloverState.AWAITING_NATIVE_CREATE
        )
    history_states = _state_prefix(state)
    if state in TERMINAL_STATES or state is RolloverState.BLOCKED:
        history_states = (*SUCCESS_SEQUENCE[: SUCCESS_RANK[last_success] + 1], state)
    operation_json_paths = sorted(
        path for path in operation_root.iterdir() if path.is_file() and path.name.endswith(".json")
    )
    _validate_existing_json_sources(state_root, operation_json_paths)
    record = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "key": {"agent": agent, "lineage_id": lineage_id, "rollover_id": rollover_id},
        "task_identity": identity,
        "title_transition": title_transition,
        "state": state.value,
        "last_successful_boundary": last_success.value,
        "native_creation": {
            "state": status or "awaiting_native_create",
            "family_id": plan.get("family_id"),
            "operation_id": plan.get("operation_id"),
        },
        "strict_recall": {"state": "pending", "score": None, "verdict_path": None},
        "canary": {"state": "pending", "proof_path": None},
        "confirmation": {"state": "pending", "confirmed_at": None, "confirmed_by": None},
        "predecessor_archival": {"state": "pending"},
        "heartbeat": {"automation_id": None, "state": "unknown", "cleanup_authorized": False},
        "timestamps": {"prepared_at": isoformat_z(created_at), "updated_at": isoformat_z(created_at)},
        "lease_path": None,
        "packet_paths": {"bootstrap_prompt_path": plan.get("bootstrap_prompt_path")},
        "receipts": _dedupe_strings(_relative(path, state_root) for path in operation_json_paths),
        "evidence_paths": [_relative(plan_path, state_root)],
        "terminal_reason": "superseded by exact task-family receipt" if state is RolloverState.SUPERSEDED else None,
        "blocking_reason": (
            f"native task-family boundary blocked: {status or task_state.get('state')}"
            if state is RolloverState.BLOCKED
            else None
        ),
        "last_reconciliation": None,
        "history": [
            _event(boundary, at=isoformat_z(created_at), reason="legacy task-family migration projection")
            for boundary in history_states
        ],
    }
    return validate_record(record)


def discover_legacy_records(
    state_root: Path,
) -> tuple[dict[tuple[str, str, str], dict[str, Any]], list[dict[str, Any]]]:
    records: dict[tuple[str, str, str], dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    rollover_root = state_root / ".agent" / "thread-rollovers"
    if rollover_root.is_dir():
        for lease_path in sorted(rollover_root.glob("*/*/lease.json")):
            try:
                record = record_from_lease(state_root, lease_path, _load_json(lease_path))
                records[_key(record)] = record
            except (OSError, ValueError) as exc:
                errors.append({"path": _relative(lease_path, state_root), "error": str(exc)})
    families_root = state_root / ".agent" / "task-families"
    if families_root.is_dir():
        for plan_path in sorted(families_root.glob("rollover-*/operations/*/rollover-plan.json")):
            try:
                record = _minimal_record_from_plan(state_root, plan_path, _load_json(plan_path))
                records.setdefault(_key(record), record)
            except (OSError, ValueError) as exc:
                errors.append({"path": _relative(plan_path, state_root), "error": str(exc)})
    return records, errors


def scan_records(
    state_root: Path,
    *,
    include_legacy: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: dict[tuple[str, str, str], dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    root = registry_root(state_root)
    if root.is_dir():
        for path in sorted(root.glob("*/*/*/record.json")):
            try:
                record = validate_record(_load_json(path), path=path)
                key = _key(record)
                if key in records:
                    raise ValueError(f"duplicate registry key {key}")
                records[key] = record
            except (OSError, ValueError) as exc:
                errors.append({"path": _relative(path, state_root), "error": str(exc)})
    if include_legacy:
        legacy, legacy_errors = discover_legacy_records(state_root)
        errors.extend(legacy_errors)
        for key, projection in legacy.items():
            if key in records:
                try:
                    records[key] = _merge_projection(records[key], projection)
                except ValueError as exc:
                    errors.append({"path": records[key].get("lease_path") or str(key), "error": str(exc)})
            else:
                records[key] = projection
    return [records[key] for key in sorted(records)], errors


def select_exact(
    records: Iterable[Mapping[str, Any]],
    *,
    agent: str | None = None,
    source_thread_id: str | None = None,
    replacement_thread_id: str | None = None,
    lineage_id: str | None = None,
    rollover_id: str | None = None,
) -> list[dict[str, Any]]:
    selectors = {
        "source_thread_id": source_thread_id,
        "replacement_thread_id": replacement_thread_id,
        "lineage_id": lineage_id,
        "rollover_id": rollover_id,
    }
    if not any(value for value in selectors.values()):
        raise ValueError("at least one exact rollover selector is required")
    if agent is not None:
        agent = _clean_agent(agent)
    if lineage_id is not None:
        lineage_id = normalize_lineage_id(lineage_id)
    if rollover_id is not None:
        rollover_id = normalize_rollover_id(rollover_id)
    selected: list[dict[str, Any]] = []
    for item in records:
        record = dict(item)
        key_agent, key_lineage, key_rollover = _key(record)
        identity, _ = _identity(record)
        if agent is not None and key_agent != agent:
            continue
        if source_thread_id is not None and identity["predecessor_task_id"] != source_thread_id:
            continue
        if replacement_thread_id is not None and identity.get("replacement_task_id") != replacement_thread_id:
            continue
        if lineage_id is not None and key_lineage != lineage_id:
            continue
        if rollover_id is not None and key_rollover != rollover_id:
            continue
        selected.append(record)
    return selected


def record_source_errors(
    state_root: Path,
    record: Mapping[str, Any],
    errors: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return scan errors that affect one selected record's durable sources."""
    agent, lineage_id, rollover_id = _key(record)
    canonical = _relative(
        record_path(state_root, agent=agent, lineage_id=lineage_id, rollover_id=rollover_id),
        state_root,
    )
    packet_paths = record.get("packet_paths") if isinstance(record.get("packet_paths"), Mapping) else {}
    selected_paths = {
        canonical,
        record.get("lease_path"),
        *record.get("receipts", []),
        *record.get("evidence_paths", []),
        *packet_paths.values(),
    }
    return [dict(error) for error in errors if error.get("path") in selected_paths]


def is_live_pending(record: Mapping[str, Any]) -> bool:
    return RolloverState(str(record.get("state"))) in LIVE_PENDING_STATES


def allows_exact_progress(record: Mapping[str, Any]) -> bool:
    """Return whether ordinary exact progress is safe without blocker adjudication."""
    state = RolloverState(str(record.get("state")))
    return state in LIVE_PENDING_STATES and state is not RolloverState.BLOCKED


def _age_seconds(record: Mapping[str, Any], *, now: datetime) -> int | None:
    timestamps = record.get("timestamps")
    if not isinstance(timestamps, Mapping):
        return None
    changed = parse_timestamp(timestamps.get("updated_at") or timestamps.get("prepared_at"))
    if changed is None:
        return None
    return max(0, int((now - changed).total_seconds()))


def next_safe_action(record: Mapping[str, Any]) -> str:
    state = RolloverState(str(record.get("state")))
    if state is RolloverState.PREPARED:
        return "reconcile the exact packet, then request its native create action"
    if state is RolloverState.AWAITING_NATIVE_CREATE:
        return "run native-action --action create for this exact lineage and rollover"
    if state is RolloverState.REPLACEMENT_CREATED:
        return "resume-exact with the authoritative replacement task ID"
    if state in {RolloverState.RESUMED, RolloverState.STRICT_RECALL_PASSED, RolloverState.CANARY_PASSED}:
        return "complete strict recall and canary proof, then confirm this exact successor"
    if state is RolloverState.CONFIRMED:
        return "reconcile and archive only the exact confirmed predecessor"
    if state is RolloverState.PREDECESSOR_ARCHIVED:
        return "finish-cleanup exact after explicit heartbeat retirement authorization"
    if state is RolloverState.HEARTBEAT_RETIRED:
        return "none; confirmed successor owns the active lineage"
    if state in TERMINAL_STATES:
        return "none; terminal packet is excluded from live pending detection"
    return "resolve the recorded blocker using exact reconciliation evidence"


def candidate_summary(record: Mapping[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    now = now or utc_now()
    agent, lineage_id, rollover_id = _key(record)
    identity, transition = _identity(record)
    return {
        "agent": agent,
        "title": identity["visible_title"],
        "semantic_title": identity["semantic_title"],
        "visible_title": identity["visible_title"],
        "issue": {
            "number": identity["github_issue_number"],
            "url": identity["github_issue_url"],
        },
        "epic": {
            "number": identity["stream_epic"],
            "url": identity["stream_epic_url"],
        },
        "lineage_id": lineage_id,
        "rollover_id": rollover_id,
        "source_thread_id": identity["predecessor_task_id"],
        "replacement_thread_id": identity["replacement_task_id"],
        "state": record.get("state"),
        "identity_lifecycle_state": identity["lifecycle_state"],
        "title_confirmation_state": transition["state"],
        "identity_source": identity["migration"]["source"],
        "age_seconds": _age_seconds(record, now=now),
        "last_successful_boundary": record.get("last_successful_boundary"),
        "blocking_reason": record.get("blocking_reason"),
        "terminal_reason": record.get("terminal_reason"),
        "next_safe_action": next_safe_action(record),
    }


def classify(record: Mapping[str, Any], *, now: datetime, stale_after: timedelta) -> AuditClassification:
    state = RolloverState(str(record.get("state")))
    age = _age_seconds(record, now=now)
    if state in TERMINAL_STATES:
        return AuditClassification.SUPERSEDED
    if state is RolloverState.BLOCKED:
        return AuditClassification.STALE_ADJUDICATION
    if age is not None and age > int(stale_after.total_seconds()) and state in LIVE_PENDING_STATES:
        return AuditClassification.STALE_ADJUDICATION
    if state in {RolloverState.PREPARED, RolloverState.AWAITING_NATIVE_CREATE}:
        return AuditClassification.AWAITING_NATIVE_ACTION
    if state in {RolloverState.CONFIRMED, RolloverState.PREDECESSOR_ARCHIVED}:
        return AuditClassification.CONFIRMED_INCOMPLETE_CLEANUP
    if state is RolloverState.HEARTBEAT_RETIRED:
        return AuditClassification.CONFIRMED_FULLY_CLEANED
    return AuditClassification.ACTIVE_RESUMABLE


def audit_fleet(
    state_root: Path,
    *,
    stale_hours: float = DEFAULT_STALE_HOURS,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or utc_now()
    records, errors = scan_records(state_root)
    entries: list[dict[str, Any]] = []
    matched_error_keys: set[tuple[object, object]] = set()
    for record in records:
        item = candidate_summary(record, now=now)
        source_errors = record_source_errors(state_root, record, errors)
        matched_error_keys.update((error.get("path"), error.get("error")) for error in source_errors)
        item["classification"] = (
            AuditClassification.INCONSISTENT_CORRUPT.value
            if source_errors
            else classify(record, now=now, stale_after=timedelta(hours=stale_hours)).value
        )
        item["live_pending"] = is_live_pending(record) and not source_errors
        item["reconciliation"] = record.get("last_reconciliation")
        item["source_errors"] = source_errors
        entries.append(item)
    unmatched_errors = [
        error for error in errors if (error.get("path"), error.get("error")) not in matched_error_keys
    ]
    entries.extend(
        {
            "agent": None,
            "title": None,
            "issue": None,
            "epic": None,
            "lineage_id": None,
            "rollover_id": None,
            "source_thread_id": None,
            "replacement_thread_id": None,
            "state": None,
            "age_seconds": None,
            "last_successful_boundary": None,
            "next_safe_action": "repair or adjudicate the corrupt packet; no mutation is authorized",
            "classification": AuditClassification.INCONSISTENT_CORRUPT.value,
            "live_pending": False,
            "reconciliation": None,
            "path": error.get("path"),
            "error": error.get("error"),
            "source_errors": [error],
        }
        for error in unmatched_errors
    )
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "generated_at": isoformat_z(now),
        "mutation_allowed": False,
        "entries": entries,
        "errors": errors,
        "counts": {
            "total": len(entries),
            "live_pending": sum(bool(item["live_pending"]) for item in entries),
            "corrupt": sum(
                item["classification"] == AuditClassification.INCONSISTENT_CORRUPT.value for item in entries
            ),
        },
    }


def migrate_existing(state_root: Path, *, apply: bool, evidence: str) -> dict[str, Any]:
    legacy, errors = discover_legacy_records(state_root)
    planned: list[dict[str, Any]] = []
    for key, _record in sorted(legacy.items()):
        path = record_path(state_root, agent=key[0], lineage_id=key[1], rollover_id=key[2])
        planned.append({"key": list(key), "record_path": _relative(path, state_root), "exists": path.is_file()})
    result = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "mode": "apply" if apply else "plan",
        "mutation_allowed": apply,
        "planned": planned,
        "errors": errors,
    }
    if not apply:
        return result
    if errors:
        raise ValueError("migration refuses to apply while legacy packets are inconsistent or corrupt")
    if not evidence.strip():
        raise ValueError("migration apply requires durable evidence")
    written = 0
    for key, record in sorted(legacy.items()):
        path = record_path(state_root, agent=key[0], lineage_id=key[1], rollover_id=key[2])
        with advisory_lock(lineage_lock_path(state_root, agent=key[0], lineage_id=key[1])):
            if path.is_file():
                current = validate_record(_load_json(path), path=path)
                record = _merge_projection(current, record)
            _append_history(
                record,
                _event(
                    RolloverState(record["state"]),
                    at=isoformat_z(utc_now()),
                    reason=f"non-destructive registry migration: {evidence.strip()}",
                    evidence_paths=record.get("evidence_paths", []),
                ),
            )
            atomic_write_json(path, record)
            written += 1
    receipt_payload = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "kind": "rollover_registry_migration_receipt",
        "evidence": evidence.strip(),
        "written": written,
        "keys": [list(key) for key in sorted(legacy)],
    }
    digest = sha256_digest(receipt_payload)
    receipt_payload["digest"] = digest
    atomic_write_json(registry_root(state_root) / "migrations" / digest[:24] / "receipt.json", receipt_payload)
    return {**result, "written": written, "receipt_digest": digest}


def _snapshot_key(snapshot: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        _clean_agent(snapshot.get("agent")),
        normalize_lineage_id(str(snapshot.get("lineage_id") or "")),
        normalize_rollover_id(str(snapshot.get("rollover_id") or "")),
    )


def reconcile_snapshot(record: Mapping[str, Any], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    if _snapshot_key(snapshot) != _key(record):
        raise ValueError("native reconciliation snapshot exact IDs do not match the selected registry record")
    identity, title_transition = _identity(record)
    evidence_paths = snapshot.get("evidence_paths")
    if not isinstance(evidence_paths, list) or not _dedupe_strings(evidence_paths):
        raise ValueError("native reconciliation snapshot requires evidence_paths")
    captured_at = parse_timestamp(snapshot.get("captured_at"))
    if captured_at is None:
        raise ValueError("native reconciliation snapshot requires an authoritative UTC captured_at")
    source = snapshot.get("source")
    replacement = snapshot.get("replacement")
    title_receipt = snapshot.get("title_receipt")
    confirmation = snapshot.get("confirmation")
    heartbeat = snapshot.get("heartbeat")
    if not all(isinstance(item, Mapping) for item in (source, replacement, title_receipt, confirmation, heartbeat)):
        raise ValueError(
            "native reconciliation snapshot requires source, replacement, title_receipt, "
            "confirmation, and heartbeat objects"
        )
    discrepancies: list[str] = []
    transitions: list[str] = []
    proposed_updates: dict[str, dict[str, Any]] = {}
    receipt_paths: list[str] = []
    if source.get("thread_id") != identity["predecessor_task_id"]:
        discrepancies.append("source thread ID does not match the selected predecessor")
    native_replacement_id = replacement.get("thread_id")
    recorded_replacement_id = identity.get("replacement_task_id")
    replacement_created = replacement.get("created")
    if replacement_created is True:
        if not isinstance(native_replacement_id, str) or not native_replacement_id:
            discrepancies.append("snapshot says replacement exists but supplies no exact replacement thread ID")
        elif recorded_replacement_id and native_replacement_id != recorded_replacement_id:
            discrepancies.append("native replacement ID conflicts with the durable registry")
        elif not recorded_replacement_id:
            transitions.append(RolloverState.REPLACEMENT_CREATED.value)
            try:
                identity, title_transition = task_identity.bind_replacement(
                    identity,
                    title_transition,
                    replacement_task_id=native_replacement_id,
                    evidence=f"Authoritative exact native snapshot captured at {isoformat_z(captured_at)}.",
                    now=isoformat_z(captured_at),
                )
            except ValueError as exc:
                discrepancies.append(str(exc))
    elif replacement_created is False:
        if native_replacement_id is not None:
            discrepancies.append("snapshot says replacement is absent but supplies a replacement thread ID")
        if recorded_replacement_id:
            discrepancies.append("authoritative native state cannot find the durable replacement task")
    else:
        discrepancies.append("native replacement creation state is unknown")
    intended_title = identity["visible_title"]
    title_replacement_id = title_receipt.get("replacement_thread_id")
    if not isinstance(title_replacement_id, str) or title_replacement_id != native_replacement_id:
        discrepancies.append("title receipt does not identify the exact native replacement")
    if title_receipt.get("supported") is True:
        if title_transition["native_title_supported"] is not True:
            discrepancies.append("title snapshot overclaims support for the persisted harness")
        if replacement_created is not True:
            discrepancies.append("native title receipt cannot exist without an exact replacement task")
        if replacement.get("title") != intended_title:
            discrepancies.append("authoritative replacement title differs from the intended display title")
        if title_receipt.get("readback_confirmed") is not True:
            discrepancies.append("native title mutation lacks exact readback confirmation")
        if title_receipt.get("intended_title") != intended_title:
            discrepancies.append("title receipt intended title differs from the durable identity")
        if title_receipt.get("readback_title") != intended_title:
            discrepancies.append("title receipt readback differs from the durable identity")
        if not isinstance(title_receipt.get("receipt_path"), str):
            discrepancies.append("native title reconciliation receipt path is missing")
        else:
            receipt_paths.append(title_receipt["receipt_path"])
            if isinstance(native_replacement_id, str) and title_transition["native_title_supported"] is True:
                try:
                    identity, title_transition = task_identity.record_title_acknowledgement(
                        identity,
                        title_transition,
                        replacement_task_id=native_replacement_id,
                        succeeded=True,
                        evidence=title_receipt["receipt_path"],
                        error="",
                        now=isoformat_z(captured_at),
                    )
                    identity, title_transition = task_identity.record_title_readback(
                        identity,
                        title_transition,
                        replacement_task_id=native_replacement_id,
                        observed_title=str(title_receipt.get("readback_title") or ""),
                        succeeded=title_receipt.get("readback_confirmed") is True,
                        evidence=title_receipt["receipt_path"],
                        error="exact native title readback failed",
                        now=isoformat_z(captured_at),
                    )
                except ValueError as exc:
                    discrepancies.append(str(exc))
    elif title_receipt.get("supported") is False:
        if title_transition["native_title_supported"] is not False:
            discrepancies.append("title snapshot denies support for a harness with a native title adapter")
        if replacement_created is not True:
            discrepancies.append("title fallback receipt cannot exist without an exact replacement task")
        if not isinstance(title_receipt.get("fallback_receipt_path"), str):
            discrepancies.append("unsupported title adapter lacks an honest fallback receipt")
        else:
            receipt_paths.append(title_receipt["fallback_receipt_path"])
    else:
        discrepancies.append("title adapter support state is unknown")
    last_boundary = RolloverState(str(record.get("last_successful_boundary")))
    confirmation_active = confirmation.get("confirmed") is True
    confirmation_replacement_id = confirmation.get("replacement_thread_id")
    if confirmation_active:
        if not isinstance(confirmation.get("proof_path"), str):
            discrepancies.append("native confirmation lacks a durable proof path")
        else:
            receipt_paths.append(confirmation["proof_path"])
        if not native_replacement_id or confirmation_replacement_id != native_replacement_id:
            discrepancies.append("native confirmation does not identify the exact replacement")
        if recorded_replacement_id and confirmation_replacement_id != recorded_replacement_id:
            discrepancies.append("native confirmation conflicts with the durable replacement ID")
        if SUCCESS_RANK.get(last_boundary, -1) < SUCCESS_RANK[RolloverState.CONFIRMED]:
            if last_boundary is RolloverState.CANARY_PASSED:
                transitions.append(RolloverState.CONFIRMED.value)
            else:
                discrepancies.append("native confirmation cannot skip strict-recall or canary boundaries")
        if isinstance(confirmation_replacement_id, str):
            try:
                identity = task_identity.mark_confirmed(
                    identity,
                    title_transition,
                    replacement_task_id=confirmation_replacement_id,
                )
            except ValueError as exc:
                discrepancies.append(str(exc))
    elif confirmation.get("confirmed") is False:
        if SUCCESS_RANK.get(last_boundary, -1) >= SUCCESS_RANK[RolloverState.CONFIRMED]:
            discrepancies.append("durable registry says confirmed but authoritative confirmation proof is absent")
    else:
        discrepancies.append("native confirmation state is unknown")
    recorded_automation_id = (record.get("heartbeat") or {}).get("automation_id")
    snapshot_automation_id = heartbeat.get("automation_id")
    if recorded_automation_id and snapshot_automation_id != recorded_automation_id:
        discrepancies.append("heartbeat automation ID does not match the durable registry")
    elif not recorded_automation_id and isinstance(snapshot_automation_id, str) and snapshot_automation_id:
        proposed_updates["heartbeat"] = {"automation_id": snapshot_automation_id}
    confirmed_locally = SUCCESS_RANK.get(last_boundary, -1) >= SUCCESS_RANK[RolloverState.CONFIRMED]
    confirmed_by_snapshot = confirmation_active and RolloverState.CONFIRMED.value in transitions
    source_archived = source.get("archived")
    if source_archived is True:
        if not (confirmed_locally or confirmed_by_snapshot) or not confirmation_active:
            discrepancies.append("predecessor archival lacks exact confirmed-successor proof")
        elif not isinstance(source.get("archive_receipt_path"), str):
            discrepancies.append("predecessor archival lacks a durable native receipt")
        else:
            receipt_paths.append(source["archive_receipt_path"])
            if SUCCESS_RANK.get(last_boundary, -1) < SUCCESS_RANK[RolloverState.PREDECESSOR_ARCHIVED]:
                transitions.append(RolloverState.PREDECESSOR_ARCHIVED.value)
    elif source_archived is False:
        if SUCCESS_RANK.get(last_boundary, -1) >= SUCCESS_RANK[RolloverState.PREDECESSOR_ARCHIVED]:
            discrepancies.append("durable registry says predecessor archived but native state says active")
    else:
        discrepancies.append("native predecessor archival state is unknown")
    heartbeat_retired = heartbeat.get("retired")
    if heartbeat_retired is True:
        if heartbeat.get("cleanup_authorized") is not True:
            discrepancies.append("heartbeat retirement lacks explicit cleanup authorization")
        elif not (confirmed_locally or confirmed_by_snapshot) or source_archived is not True:
            discrepancies.append("heartbeat retirement requires an exact confirmed and archived predecessor")
        elif not isinstance(heartbeat.get("retirement_receipt_path"), str):
            discrepancies.append("heartbeat retirement lacks a durable native receipt")
        else:
            receipt_paths.append(heartbeat["retirement_receipt_path"])
            if SUCCESS_RANK.get(last_boundary, -1) < SUCCESS_RANK[RolloverState.HEARTBEAT_RETIRED]:
                transitions.append(RolloverState.HEARTBEAT_RETIRED.value)
    elif heartbeat_retired is False:
        if SUCCESS_RANK.get(last_boundary, -1) >= SUCCESS_RANK[RolloverState.HEARTBEAT_RETIRED]:
            discrepancies.append("durable registry says heartbeat retired but authoritative automation is active")
    else:
        discrepancies.append("heartbeat retirement state is unknown")
    if heartbeat.get("cleanup_authorized") is True:
        if not (confirmed_locally or confirmed_by_snapshot):
            discrepancies.append("heartbeat cleanup authorization precedes exact successor confirmation")
        else:
            proposed_updates.setdefault("heartbeat", {})["cleanup_authorized"] = True
    proposed_updates["task_identity"] = identity
    proposed_updates["title_transition"] = title_transition
    return {
        "consistent": not discrepancies,
        "discrepancies": discrepancies,
        "proposed_transitions": list(dict.fromkeys(transitions)),
        "captured_at": isoformat_z(captured_at),
        "evidence_paths": _dedupe_strings(evidence_paths),
        "receipt_paths": _dedupe_strings(receipt_paths),
        "proposed_updates": proposed_updates,
        "snapshot_digest": hashlib.sha256(canonical_json(dict(snapshot)).encode()).hexdigest(),
        "next_safe_action": "apply exact reconciliation"
        if (transitions or proposed_updates) and not discrepancies
        else next_safe_action(record),
    }


def apply_reconciliation(
    state_root: Path,
    *,
    record: Mapping[str, Any],
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    reconciliation = reconcile_snapshot(record, snapshot)
    if not reconciliation["consistent"]:
        raise ValueError("reconciliation is inconsistent; no durable state was changed")
    _require_durable_paths(
        state_root,
        [*reconciliation["evidence_paths"], *reconciliation["receipt_paths"]],
        label="reconciliation evidence path",
    )
    agent, lineage_id, rollover_id = _key(record)
    operation_id = reconciliation["snapshot_digest"]
    receipt_path = (
        record_path(state_root, agent=agent, lineage_id=lineage_id, rollover_id=rollover_id).parent
        / "reconciliation"
        / operation_id[:24]
        / "receipt.json"
    )

    def existing_receipt() -> dict[str, Any] | None:
        if not receipt_path.is_file():
            return None
        durable = _load_json(receipt_path)
        if (
            durable.get("kind") != "rollover_reconciliation_receipt"
            or durable.get("key") != record.get("key")
            or durable.get("snapshot_digest") != operation_id
        ):
            raise ValueError("durable reconciliation receipt conflicts with the exact snapshot")
        return durable

    if durable := existing_receipt():
        return durable
    with advisory_lock(lineage_lock_path(state_root, agent=agent, lineage_id=lineage_id)):
        if durable := existing_receipt():
            return durable
        _require_durable_paths(
            state_root,
            [*reconciliation["evidence_paths"], *reconciliation["receipt_paths"]],
            label="reconciliation evidence path",
        )
        current = load_record(state_root, agent=agent, lineage_id=lineage_id, rollover_id=rollover_id)
        reconciliation = reconcile_snapshot(current, snapshot)
        if not reconciliation["consistent"]:
            raise ValueError("registry changed before reconciliation apply; no durable state was changed")
        replacement = snapshot["replacement"]
        native_id = replacement.get("thread_id")
        for target_value in reconciliation["proposed_transitions"]:
            target = RolloverState(target_value)
            updates: dict[str, Any] = {
                "task_identity": reconciliation["proposed_updates"]["task_identity"],
                "title_transition": reconciliation["proposed_updates"]["title_transition"],
            }
            if target is RolloverState.REPLACEMENT_CREATED and isinstance(native_id, str):
                updates["native_creation"] = {
                    **current["native_creation"],
                    "state": "authoritatively_reconciled",
                    "snapshot_digest": operation_id,
                }
            current = transition(
                state_root,
                agent=agent,
                lineage_id=lineage_id,
                rollover_id=rollover_id,
                state=target,
                reason="authoritative exact native reconciliation",
                evidence_paths=reconciliation["evidence_paths"],
                operation_id=operation_id,
                updates=updates,
                already_locked=True,
            )
        for section, updates in reconciliation["proposed_updates"].items():
            if section in {"task_identity", "title_transition"}:
                current[section] = dict(updates)
            else:
                current[section] = {**(current.get(section) or {}), **updates}
        current["receipts"] = _dedupe_strings([*current.get("receipts", []), *reconciliation["receipt_paths"]])
        current["evidence_paths"] = _dedupe_strings(
            [*current.get("evidence_paths", []), *reconciliation["evidence_paths"]]
        )
        current["last_reconciliation"] = reconciliation
        path = record_path(state_root, agent=agent, lineage_id=lineage_id, rollover_id=rollover_id)
        validate_record(current, path=path)
        atomic_write_json(path, current)
        receipt = {
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "kind": "rollover_reconciliation_receipt",
            "key": current["key"],
            "snapshot_digest": operation_id,
            "applied_transitions": reconciliation["proposed_transitions"],
            "evidence_paths": _dedupe_strings([*reconciliation["evidence_paths"], *reconciliation["receipt_paths"]]),
            "applied_at": isoformat_z(utc_now()),
        }
        atomic_write_json(receipt_path, receipt)
    return receipt


_DISPOSITION_ASSERTIONS = frozenset(
    {
        "not_confirmed_active",
        "no_valid_replacement_owns_lineage",
        "no_unrecorded_native_create",
        "no_active_heartbeat_dependency",
        "selected_exact_ids_match",
    }
)
_CLEANUP_ASSERTIONS = frozenset(
    {
        "confirmed_successor_exact",
        "predecessor_archived_exact",
        "heartbeat_retirement_authorized",
        "heartbeat_retired_exact",
        "selected_exact_ids_match",
    }
)


def _maintenance_target_states(action: MaintenanceAction) -> list[str]:
    if action is MaintenanceAction.FINISH_CLEANUP:
        return [
            RolloverState.PREDECESSOR_ARCHIVED.value,
            RolloverState.HEARTBEAT_RETIRED.value,
        ]
    return [
        RolloverState.SUPERSEDED.value
        if action is MaintenanceAction.SUPERSEDE
        else RolloverState.ABANDONED_WITH_PROOF.value
    ]


def validate_maintenance_proof(
    record: Mapping[str, Any],
    *,
    action: MaintenanceAction,
    proof: Mapping[str, Any],
) -> dict[str, Any]:
    if _snapshot_key(proof) != _key(record):
        raise ValueError("maintenance proof exact IDs do not match the selected registry record")
    assertions = proof.get("assertions")
    if not isinstance(assertions, Mapping):
        raise ValueError("maintenance proof requires assertions")
    required = _CLEANUP_ASSERTIONS if action is MaintenanceAction.FINISH_CLEANUP else _DISPOSITION_ASSERTIONS
    missing = sorted(name for name in required if assertions.get(name) is not True)
    if missing:
        raise ValueError(f"maintenance proof lacks required true assertions: {', '.join(missing)}")
    evidence_paths = proof.get("evidence_paths")
    if not isinstance(evidence_paths, list) or not _dedupe_strings(evidence_paths):
        raise ValueError("maintenance proof requires durable evidence_paths")
    if parse_timestamp(proof.get("captured_at")) is None:
        raise ValueError("maintenance proof requires an authoritative UTC captured_at")
    state = RolloverState(str(record.get("state")))
    if (
        action in {MaintenanceAction.SUPERSEDE, MaintenanceAction.ABANDON}
        and SUCCESS_RANK.get(RolloverState(str(record.get("last_successful_boundary"))), 0)
        >= SUCCESS_RANK[RolloverState.CONFIRMED]
    ):
        raise ValueError("confirmed active rollover cannot be superseded or abandoned")
    if action is MaintenanceAction.FINISH_CLEANUP and state not in {
        RolloverState.CONFIRMED,
        RolloverState.PREDECESSOR_ARCHIVED,
        RolloverState.HEARTBEAT_RETIRED,
    }:
        raise ValueError("finish-cleanup requires an exact confirmed successor")
    return {
        "assertions": {name: True for name in sorted(required)},
        "evidence_paths": _dedupe_strings(evidence_paths),
        "captured_at": str(proof["captured_at"]),
        "reason": str(proof.get("reason") or action.value),
        "proof_digest": hashlib.sha256(canonical_json(dict(proof)).encode()).hexdigest(),
    }


def create_maintenance_plan(
    state_root: Path,
    *,
    record: Mapping[str, Any],
    action: MaintenanceAction,
    proof: Mapping[str, Any],
) -> dict[str, Any]:
    validated = validate_maintenance_proof(record, action=action, proof=proof)
    _require_durable_paths(
        state_root,
        validated["evidence_paths"],
        label="maintenance evidence path",
    )
    agent, lineage_id, rollover_id = _key(record)
    payload = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "kind": "rollover_maintenance_plan",
        "key": {"agent": agent, "lineage_id": lineage_id, "rollover_id": rollover_id},
        "action": action.value,
        "record_digest": sha256_digest(dict(record)),
        "proof": validated,
        "target_states": _maintenance_target_states(action),
    }
    digest = sha256_digest(payload)
    payload["digest"] = digest
    plan_path = (
        record_path(state_root, agent=agent, lineage_id=lineage_id, rollover_id=rollover_id).parent
        / "maintenance"
        / action.value
        / digest[:24]
        / "plan.json"
    )
    with advisory_lock(lineage_lock_path(state_root, agent=agent, lineage_id=lineage_id)):
        if plan_path.is_file() and _load_json(plan_path) != payload:
            raise ValueError("immutable maintenance plan digest collision")
        atomic_write_json(plan_path, payload)
    return {**payload, "plan_path": _relative(plan_path, state_root)}


def load_maintenance_plan(state_root: Path, *, plan_path: Path) -> tuple[Path, dict[str, Any]]:
    """Load and validate an immutable plan without changing registry state."""
    resolved = (state_root / plan_path).resolve() if not plan_path.is_absolute() else plan_path.resolve()
    try:
        resolved.relative_to(registry_root(state_root))
    except ValueError as exc:
        raise ValueError("maintenance plan must remain inside the canonical rollover registry") from exc
    plan = _load_json(resolved)
    if plan.get("schema_version") != REGISTRY_SCHEMA_VERSION or plan.get("kind") != "rollover_maintenance_plan":
        raise ValueError("maintenance plan is malformed")
    expected_plan_fields = {
        "schema_version",
        "kind",
        "key",
        "action",
        "record_digest",
        "proof",
        "target_states",
        "digest",
    }
    if set(plan) != expected_plan_fields:
        raise ValueError("maintenance plan has missing or unexpected fields")
    immutable = dict(plan)
    digest = immutable.pop("digest", None)
    if not isinstance(digest, str) or sha256_digest(immutable) != digest:
        raise ValueError("maintenance plan digest mismatch")
    key = plan.get("key")
    if not isinstance(key, Mapping):
        raise ValueError("maintenance plan key is missing")
    agent, lineage_id, rollover_id = _snapshot_key(key)
    try:
        action = MaintenanceAction(str(plan.get("action")))
    except ValueError as exc:
        raise ValueError("maintenance plan action is malformed") from exc
    if plan.get("target_states") != _maintenance_target_states(action):
        raise ValueError("maintenance plan target states do not match its exact action")
    record_digest = plan.get("record_digest")
    if not isinstance(record_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", record_digest):
        raise ValueError("maintenance plan record digest is malformed")
    proof = plan.get("proof")
    if not isinstance(proof, Mapping):
        raise ValueError("maintenance plan proof is missing")
    if set(proof) != {"assertions", "evidence_paths", "captured_at", "reason", "proof_digest"}:
        raise ValueError("maintenance plan proof has missing or unexpected fields")
    assertions = proof.get("assertions")
    required = _CLEANUP_ASSERTIONS if action is MaintenanceAction.FINISH_CLEANUP else _DISPOSITION_ASSERTIONS
    if (
        not isinstance(assertions, Mapping)
        or set(assertions) != required
        or not all(assertions.get(name) is True for name in required)
    ):
        raise ValueError("maintenance plan proof assertions do not match its exact action")
    if not isinstance(proof.get("evidence_paths"), list) or not _dedupe_strings(proof["evidence_paths"]):
        raise ValueError("maintenance plan proof has no durable evidence paths")
    if parse_timestamp(proof.get("captured_at")) is None or not str(proof.get("reason") or "").strip():
        raise ValueError("maintenance plan proof timestamp or reason is malformed")
    proof_digest = proof.get("proof_digest")
    if not isinstance(proof_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", proof_digest):
        raise ValueError("maintenance plan proof digest is malformed")
    expected_path = (
        record_path(
            state_root,
            agent=agent,
            lineage_id=lineage_id,
            rollover_id=rollover_id,
        ).parent
        / "maintenance"
        / action.value
        / digest[:24]
        / "plan.json"
    )
    if resolved != expected_path:
        raise ValueError("maintenance plan path does not match its exact key, action, and digest")
    return resolved, plan


def apply_maintenance_plan(state_root: Path, *, plan_path: Path) -> dict[str, Any]:
    resolved, plan = load_maintenance_plan(state_root, plan_path=plan_path)
    key = plan["key"]
    agent, lineage_id, rollover_id = _snapshot_key(key)
    receipt_path = resolved.parent / "receipt.json"
    intent_path = resolved.parent / "apply-intent.json"

    def existing_receipt() -> dict[str, Any] | None:
        if not receipt_path.is_file():
            return None
        durable = _load_json(receipt_path)
        if (
            durable.get("kind") != "rollover_maintenance_receipt"
            or durable.get("plan_digest") != plan.get("digest")
            or durable.get("key") != key
            or durable.get("action") != plan.get("action")
        ):
            raise ValueError("durable maintenance receipt conflicts with the exact plan")
        return durable

    if durable := existing_receipt():
        return durable
    with advisory_lock(lineage_lock_path(state_root, agent=agent, lineage_id=lineage_id)):
        if durable := existing_receipt():
            return durable
        _, durable_plan = load_maintenance_plan(state_root, plan_path=resolved)
        if durable_plan != plan:
            raise ValueError("immutable maintenance plan changed before apply")
        _require_durable_paths(
            state_root,
            plan["proof"]["evidence_paths"],
            label="maintenance evidence path",
        )
        record = load_record(state_root, agent=agent, lineage_id=lineage_id, rollover_id=rollover_id)
        operation_id = str(plan["digest"])
        already_applied = any(event.get("operation_id") == operation_id for event in record.get("history", []))
        if not already_applied and sha256_digest(record) != plan.get("record_digest"):
            raise ValueError("registry record changed after maintenance planning; create a fresh exact plan")
        intent = {
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "kind": "rollover_maintenance_apply_intent",
            "plan_digest": operation_id,
            "key": dict(key),
        }
        if intent_path.is_file() and _load_json(intent_path) != intent:
            raise ValueError("durable maintenance apply intent conflicts with the exact plan")
        atomic_write_json(intent_path, intent)
        for target_value in plan.get("target_states", []):
            record = transition(
                state_root,
                agent=agent,
                lineage_id=lineage_id,
                rollover_id=rollover_id,
                state=RolloverState(target_value),
                reason=str(plan["proof"]["reason"]),
                evidence_paths=plan["proof"]["evidence_paths"],
                operation_id=operation_id,
                already_locked=True,
            )
        receipt = {
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "kind": "rollover_maintenance_receipt",
            "plan_digest": operation_id,
            "key": dict(key),
            "action": plan["action"],
            "final_state": record["state"],
            "applied_at": isoformat_z(utc_now()),
            "evidence_paths": plan["proof"]["evidence_paths"],
        }
        atomic_write_json(receipt_path, receipt)
    return receipt


def monitor_snapshot(state_root: Path) -> dict[str, Any]:
    audit = audit_fleet(state_root)
    return {
        "schema_version": audit["schema_version"],
        "generated_at": audit["generated_at"],
        "counts": audit["counts"],
        "entries": audit["entries"],
        "errors": audit["errors"],
    }
