"""Task Family Manager adapter for Codex rollover-native actions.

Repo-local Python cannot invoke Codex app tools. This module owns the durable
exact-ID plan, typed family binding, native acknowledgements, read-back
reconciliation, and retry decisions used by the app-capable rollover skill.
It never writes Codex state directly.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal

from . import codex_state
from .graph import bounded_title, discover_task_family
from .model import (
    LifecycleEvent,
    LifecycleState,
    OperationReceipt,
    ReceiptAction,
    RelationType,
    TaskFamilyManifest,
    TaskNode,
    TaskRelation,
    utc_now,
)
from .planner import sha256_digest
from .storage import TaskFamilyStorage

PLAN_SCHEMA_VERSION = 1
NATIVE_ACTIONS = frozenset({"create", "title", "archive"})
PinState = Literal["unpinned", "pinned", "unknown"]


def _clean_display(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValueError(f"{label} must be non-empty when supplied")
    if any(ord(character) < 32 for character in cleaned):
        raise ValueError(f"{label} contains control characters")
    return cleaned


def rollover_title(
    *,
    agent: str,
    lineage_id: str,
    generation: int,
    epic_title: str | None,
    goal: str | None,
    phase: str | None,
    next_phase: str | None = None,
) -> tuple[str, str, dict[str, str | None]]:
    """Return a bounded human title or a unique lineage/generation fallback."""
    fields = {
        "epic_title": _clean_display(epic_title, "epic title"),
        "goal": _clean_display(goal, "goal"),
        "phase": _clean_display(phase, "phase"),
        "next_phase": _clean_display(next_phase, "next phase"),
    }
    required = (fields["epic_title"], fields["goal"], fields["phase"])
    if any(required) and not all(required):
        raise ValueError("epic title, goal, and phase must be supplied together")
    if all(required):
        base = f"{fields['epic_title']} — {fields['phase']} {fields['goal']}"
        if fields["next_phase"]:
            base += f" → {fields['next_phase']}"
        source = "durable_metadata"
    else:
        if generation < 1:
            raise ValueError("rollover generation must be positive")
        agent_label = _clean_display(agent, "agent")
        assert agent_label is not None
        base = f"{agent_label[:6].title()} continuity — {lineage_id} · g{generation:04d}"
        source = "lineage_generation_fallback"
    title = bounded_title(base)
    if title.casefold() in {"resume codex rollover", "rollover"}:
        raise ValueError("generic rollover titles are forbidden")
    return title, source, fields


def legacy_transition_identity(*, lineage_id: str, generation: int) -> tuple[str, str]:
    """Return the pre-supersession operation identity for exact repair only."""
    family_id = f"rollover-{lineage_id}-g{generation:04d}"
    operation_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"learn-ukrainian:{family_id}:native-transition"))
    return family_id, operation_id


def transition_identity(*, lineage_id: str, generation: int, rollover_id: str) -> tuple[str, str]:
    """Return a stable family ID and packet-specific operation ID."""
    if not rollover_id.strip():
        raise ValueError("rollover_id must be non-empty")
    family_id = f"rollover-{lineage_id}-g{generation:04d}"
    operation_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"learn-ukrainian:{family_id}:native-transition:{rollover_id}",
        )
    )
    return family_id, operation_id


def _plan_digest(payload: dict[str, Any]) -> str:
    immutable = dict(payload)
    immutable.pop("digest", None)
    return sha256_digest(immutable)


def _load_plan(storage: TaskFamilyStorage) -> dict[str, Any]:
    plan = storage.read_json(storage.rollover_plan_path)
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION or plan.get("kind") != "rollover_native_transition":
        raise ValueError("persisted rollover transition plan is malformed")
    digest = plan.get("digest")
    if not isinstance(digest, str) or digest != _plan_digest(plan):
        raise ValueError("persisted rollover transition plan digest mismatch")
    return plan


def _load_binding(storage: TaskFamilyStorage) -> dict[str, Any]:
    binding = storage.read_json(storage.rollover_binding_path)
    if binding.get("schema_version") != PLAN_SCHEMA_VERSION or binding.get("kind") != "rollover_native_binding":
        raise ValueError("persisted rollover binding is malformed")
    if binding.get("plan_digest") != _load_plan(storage)["digest"]:
        raise ValueError("persisted rollover binding does not match the immutable plan")
    return binding


def assert_transition_context(
    *,
    repo_root: Path,
    family_id: str,
    operation_id: str,
    lineage_id: str,
    rollover_id: str,
    generation: int,
    source_thread_id: str,
) -> dict[str, Any]:
    """Match one native command to the exact immutable packet plan."""
    expected_family_id, expected_operation_id = transition_identity(
        lineage_id=lineage_id,
        generation=generation,
        rollover_id=rollover_id,
    )
    if family_id != expected_family_id or operation_id != expected_operation_id:
        raise ValueError("native lifecycle operation does not match the packet-specific transition identity")
    plan = _load_plan(TaskFamilyStorage(repo_root, family_id, operation_id))
    expected = {
        "family_id": family_id,
        "operation_id": operation_id,
        "lineage_id": lineage_id,
        "rollover_id": rollover_id,
        "generation": generation,
        "source_thread_id": source_thread_id,
    }
    for key, value in expected.items():
        if plan.get(key) != value:
            raise ValueError(f"immutable native transition plan does not match lease {key}")
    return plan


def _event(
    storage: TaskFamilyStorage,
    *,
    state: LifecycleState,
    kind: str,
    details: dict[str, Any],
) -> None:
    storage.append_event(
        LifecycleEvent(
            event_id=str(uuid.uuid4()),
            occurred_at=utc_now(),
            state=state,
            kind=kind,
            details=details,
        )
    )


def _action_key(action: ReceiptAction) -> tuple[str, str, str]:
    return action.resource_type, action.resource_id, action.action


def _append_receipt(
    storage: TaskFamilyStorage,
    *,
    final_state: LifecycleState | None = None,
    actual: ReceiptAction | None = None,
    skipped: ReceiptAction | None = None,
    failure: ReceiptAction | None = None,
) -> OperationReceipt:
    receipt = storage.load_receipt()

    def add_unique(items: tuple[ReceiptAction, ...], item: ReceiptAction | None) -> tuple[ReceiptAction, ...]:
        if item is None or _action_key(item) in {_action_key(existing) for existing in items}:
            return items
        return (*items, item)

    updated = replace(
        receipt,
        final_state=final_state or receipt.final_state,
        actual=add_unique(receipt.actual, actual),
        skipped=add_unique(receipt.skipped, skipped),
        failures=(*receipt.failures, failure) if failure is not None else receipt.failures,
        events=storage.load_events(),
    )
    storage.write_receipt(updated)
    return updated


def prepare_transition(
    *,
    repo_root: Path,
    agent: str,
    lineage_id: str,
    rollover_id: str,
    generation: int,
    source_thread_id: str,
    intended_title: str,
    title_source: str,
    bootstrap_prompt_path: str,
    supersedes: dict[str, str] | None = None,
) -> dict[str, Any]:
    family_id, operation_id = transition_identity(
        lineage_id=lineage_id,
        generation=generation,
        rollover_id=rollover_id,
    )
    if supersedes is not None:
        required = {"family_id", "operation_id", "rollover_id"}
        if set(supersedes) != required or any(not supersedes[key].strip() for key in required):
            raise ValueError("supersedes must contain exact non-empty family_id, operation_id, and rollover_id")
        if supersedes["operation_id"] == operation_id or supersedes["rollover_id"] == rollover_id:
            raise ValueError("a rollover transition cannot supersede itself")
    storage = TaskFamilyStorage(repo_root, family_id, operation_id)
    payload: dict[str, Any] = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "kind": "rollover_native_transition",
        "family_id": family_id,
        "operation_id": operation_id,
        "agent": agent,
        "lineage_id": lineage_id,
        "rollover_id": rollover_id,
        "generation": generation,
        "project_root": str(repo_root.resolve()),
        "source_thread_id": source_thread_id,
        "intended_title": intended_title,
        "title_source": title_source,
        "bootstrap_prompt_path": bootstrap_prompt_path,
        "relation_types": [RelationType.REPLACEMENT_OF.value, RelationType.ROLLOVER_GENERATION_OF.value],
    }
    if supersedes is not None:
        payload["supersedes"] = dict(supersedes)
    payload["digest"] = _plan_digest(payload)
    storage.write_immutable_json(storage.rollover_plan_path, payload)
    if not storage.receipt_path.exists():
        planned = (
            ReceiptAction(
                "rollover", rollover_id, (source_thread_id,), "create_replacement", "Use native create_thread once."
            ),
            ReceiptAction("rollover", rollover_id, (source_thread_id,), "title_replacement", intended_title),
            ReceiptAction(
                "task",
                source_thread_id,
                (source_thread_id,),
                "archive_confirmed_predecessor",
                "Proof and app-state gated.",
            ),
        )
        _event(
            storage,
            state=LifecycleState.PLANNED,
            kind="rollover_native_intent_prepared",
            details={"plan_digest": payload["digest"]},
        )
        storage.write_receipt(
            OperationReceipt(
                operation_id,
                family_id,
                payload["digest"],
                LifecycleState.PLANNED,
                planned=planned,
                events=storage.load_events(),
            )
        )
        storage.write_state(
            LifecycleState.PLANNED,
            details={
                "status": "supersession_pending" if supersedes is not None else "awaiting_native_create",
                "plan_digest": payload["digest"],
                **({"supersedes": dict(supersedes)} if supersedes is not None else {}),
            },
        )
    else:
        receipt = storage.load_receipt()
        if receipt.plan_digest != payload["digest"]:
            raise ValueError("existing rollover receipt does not match the immutable transition plan")
    return {
        "family_id": family_id,
        "operation_id": operation_id,
        "plan_digest": payload["digest"],
        "receipt_path": str(storage.receipt_path),
        "status": storage.load_state()["details"].get("status"),
    }


def assert_transition_supersedable(
    *,
    repo_root: Path,
    family_id: str,
    operation_id: str,
    lineage_id: str,
    generation: int,
    source_thread_id: str,
    successor_rollover_id: str,
    successor_operation_id: str,
    expected_rollover_id: str | None = None,
) -> dict[str, Any]:
    """Prove an exact native intent has never reached or authorized a native call."""
    storage = TaskFamilyStorage(repo_root, family_id, operation_id)
    plan = _load_plan(storage)
    expected = {
        "family_id": family_id,
        "operation_id": operation_id,
        "lineage_id": lineage_id,
        "generation": generation,
        "source_thread_id": source_thread_id,
    }
    for key, value in expected.items():
        if plan.get(key) != value:
            raise ValueError(f"superseded transition {key} does not match the exact predecessor intent")
    if expected_rollover_id is not None and plan.get("rollover_id") != expected_rollover_id:
        raise ValueError("superseded transition rollover_id does not match the exact predecessor intent")
    if plan.get("rollover_id") == successor_rollover_id or operation_id == successor_operation_id:
        raise ValueError("successor identity must differ from the superseded transition")

    state = storage.load_state()
    details = state["details"]
    already_superseded = details.get("status") == "superseded_before_native_create"
    if already_superseded and (
        details.get("superseded_by_rollover_id") != successor_rollover_id
        or details.get("superseded_by_operation_id") != successor_operation_id
    ):
        raise ValueError("transition was already superseded by a different exact successor")

    supersession: dict[str, Any] | None = None
    if storage.rollover_supersession_path.exists():
        supersession = storage.read_json(storage.rollover_supersession_path)
        if (
            supersession.get("schema_version") != PLAN_SCHEMA_VERSION
            or supersession.get("kind") != "rollover_native_intent_supersession"
            or supersession.get("plan_digest") != plan["digest"]
            or supersession.get("family_id") != family_id
            or supersession.get("rollover_id") != plan["rollover_id"]
            or supersession.get("superseded_by_rollover_id") != successor_rollover_id
            or supersession.get("superseded_by_operation_id") != successor_operation_id
        ):
            raise ValueError("immutable transition supersession does not match the exact successor")
    if already_superseded and supersession is None:
        raise ValueError("superseded transition is missing its immutable exact-successor document")

    receipt = storage.load_receipt()
    if receipt.family_id != family_id or receipt.operation_id != operation_id or receipt.plan_digest != plan["digest"]:
        raise ValueError("superseded transition receipt identity or digest is inconsistent")
    if storage.rollover_binding_path.exists():
        raise ValueError("transition has an exact replacement binding and cannot be superseded")
    if receipt.actual:
        raise ValueError("transition has recorded native or reconciled actions and cannot be superseded")
    if receipt.failures:
        raise ValueError("transition has partial or ambiguous failures and cannot be superseded")
    if already_superseded:
        event_kinds = [event.kind for event in storage.load_events()]
        if (
            state.get("state") != LifecycleState.BLOCKED.value
            or receipt.final_state is not LifecycleState.BLOCKED
            or "rollover_native_intent_superseded" not in event_kinds
        ):
            raise ValueError("superseded transition receipt, event, or state is incomplete")
        return {"already_superseded": True, "plan": plan, "supersession_started": True}
    if state.get("state") != LifecycleState.PLANNED.value or details.get("status") != "awaiting_native_create":
        raise ValueError("transition is not an untouched native-create intent")
    permitted_events = {"rollover_native_intent_prepared"}
    if supersession is not None:
        permitted_events.add("rollover_native_intent_superseded")
    unsafe_events = [event.kind for event in storage.load_events() if event.kind not in permitted_events]
    if unsafe_events:
        raise ValueError("transition has native-action or ambiguous lifecycle events and cannot be superseded")
    return {"already_superseded": False, "plan": plan, "supersession_started": supersession is not None}


def supersede_unexecuted_transition(
    *,
    repo_root: Path,
    family_id: str,
    operation_id: str,
    lineage_id: str,
    generation: int,
    source_thread_id: str,
    successor_rollover_id: str,
    successor_operation_id: str,
    evidence: str,
    expected_rollover_id: str | None = None,
) -> dict[str, Any]:
    """Close an untouched native intent while preserving its immutable evidence."""
    if not evidence.strip():
        raise ValueError("native-intent supersession evidence is required")
    proof = assert_transition_supersedable(
        repo_root=repo_root,
        family_id=family_id,
        operation_id=operation_id,
        lineage_id=lineage_id,
        generation=generation,
        source_thread_id=source_thread_id,
        successor_rollover_id=successor_rollover_id,
        successor_operation_id=successor_operation_id,
        expected_rollover_id=expected_rollover_id,
    )
    storage = TaskFamilyStorage(repo_root, family_id, operation_id)
    plan = proof["plan"]
    if proof["already_superseded"]:
        return {
            "status": "already_superseded",
            "rollover_id": plan["rollover_id"],
            "superseded_by_rollover_id": successor_rollover_id,
            "superseded_by_operation_id": successor_operation_id,
            "receipt_path": str(storage.receipt_path),
        }

    supersession = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "kind": "rollover_native_intent_supersession",
        "plan_digest": plan["digest"],
        "family_id": family_id,
        "rollover_id": plan["rollover_id"],
        "operation_id": operation_id,
        "superseded_by_rollover_id": successor_rollover_id,
        "superseded_by_operation_id": successor_operation_id,
        "evidence": evidence.strip(),
    }
    storage.write_immutable_json(storage.rollover_supersession_path, supersession)
    if not any(event.kind == "rollover_native_intent_superseded" for event in storage.load_events()):
        _event(
            storage,
            state=LifecycleState.BLOCKED,
            kind="rollover_native_intent_superseded",
            details={
                "rollover_id": plan["rollover_id"],
                "superseded_by_rollover_id": successor_rollover_id,
                "superseded_by_operation_id": successor_operation_id,
                "evidence": evidence.strip(),
            },
        )
    receipt = storage.load_receipt()
    skipped_keys = {_action_key(item) for item in receipt.skipped}
    skipped = tuple(
        item
        for item in (
            ReceiptAction(
                planned.resource_type,
                planned.resource_id,
                planned.task_ids,
                planned.action,
                f"Superseded before native creation by {successor_rollover_id}; no native mutation was authorized.",
            )
            for planned in receipt.planned
        )
        if _action_key(item) not in skipped_keys
    )
    storage.write_receipt(
        replace(
            receipt,
            final_state=LifecycleState.BLOCKED,
            skipped=(*receipt.skipped, *skipped),
            events=storage.load_events(),
        )
    )
    storage.write_state(
        LifecycleState.BLOCKED,
        details={
            "status": "superseded_before_native_create",
            "rollover_id": plan["rollover_id"],
            "superseded_by_rollover_id": successor_rollover_id,
            "superseded_by_operation_id": successor_operation_id,
        },
    )
    return {
        "status": "superseded",
        "rollover_id": plan["rollover_id"],
        "superseded_by_rollover_id": successor_rollover_id,
        "superseded_by_operation_id": successor_operation_id,
        "receipt_path": str(storage.receipt_path),
    }


def activate_superseding_transition(
    *,
    repo_root: Path,
    family_id: str,
    operation_id: str,
) -> dict[str, Any]:
    """Unlock create only after the immutable predecessor intent is superseded."""
    storage = TaskFamilyStorage(repo_root, family_id, operation_id)
    plan = _load_plan(storage)
    supersedes = plan.get("supersedes")
    if not isinstance(supersedes, dict):
        raise ValueError("transition is not an explicit superseding intent")
    old_storage = TaskFamilyStorage(repo_root, supersedes["family_id"], supersedes["operation_id"])
    old_state = old_storage.load_state()
    old_details = old_state["details"]
    if (
        old_details.get("status") != "superseded_before_native_create"
        or old_details.get("superseded_by_rollover_id") != plan["rollover_id"]
        or old_details.get("superseded_by_operation_id") != operation_id
    ):
        raise ValueError("exact predecessor intent has not been durably superseded by this transition")
    state = storage.load_state()
    if state["details"].get("status") == "awaiting_native_create":
        return {"status": "already_active", "receipt_path": str(storage.receipt_path)}
    if state["details"].get("status") != "supersession_pending":
        raise ValueError("superseding transition is not awaiting exact predecessor reconciliation")
    if not any(event.kind == "rollover_native_intent_activated" for event in storage.load_events()):
        _event(
            storage,
            state=LifecycleState.PLANNED,
            kind="rollover_native_intent_activated",
            details={"superseded_operation_id": supersedes["operation_id"]},
        )
        _append_receipt(storage)
    storage.write_state(
        LifecycleState.PLANNED,
        details={"status": "awaiting_native_create", "plan_digest": plan["digest"]},
    )
    return {"status": "awaiting_native_create", "receipt_path": str(storage.receipt_path)}


def bind_replacement(
    *,
    repo_root: Path,
    family_id: str,
    operation_id: str,
    source: codex_state.ThreadRecord,
    replacement: codex_state.ThreadRecord,
    db_path: Path,
    evidence: str,
) -> dict[str, Any]:
    storage = TaskFamilyStorage(repo_root, family_id, operation_id)
    plan = _load_plan(storage)
    source_id = plan["source_thread_id"]
    if source.thread_id != source_id:
        raise ValueError("native binding source does not match the persisted predecessor")
    if replacement.thread_id == source_id:
        raise ValueError("replacement thread must differ from the predecessor")
    if not evidence.strip():
        raise ValueError("native create evidence is required")
    project_root = plan["project_root"]
    source_metadata = {"cwd": source.cwd, **({"host": source.host} if source.host else {})}
    replacement_metadata = {"cwd": replacement.cwd, **({"host": replacement.host} if replacement.host else {})}
    manifest = TaskFamilyManifest(
        family_id=family_id,
        seed_task_id=source_id,
        nodes=(
            TaskNode(source_id, source.title, project_root, metadata=source_metadata),
            TaskNode(replacement.thread_id, replacement.title, project_root, metadata=replacement_metadata),
        ),
        relations=(
            TaskRelation(replacement.thread_id, source_id, RelationType.REPLACEMENT_OF, evidence),
            TaskRelation(replacement.thread_id, source_id, RelationType.ROLLOVER_GENERATION_OF, evidence),
        ),
    )
    graph = discover_task_family(manifest)
    if not graph.is_valid:
        raise ValueError("invalid rollover task family: " + "; ".join(blocker.message for blocker in graph.blockers))
    storage.write_manifest(manifest)
    binding = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "kind": "rollover_native_binding",
        "plan_digest": plan["digest"],
        "source_thread_id": source_id,
        "replacement_thread_id": replacement.thread_id,
        "source_title": source.title,
        "replacement_initial_title": replacement.title,
        "intended_title": plan["intended_title"],
        "source_cwd": source.cwd,
        "replacement_cwd": replacement.cwd,
        "source_host": source.host,
        "replacement_host": replacement.host,
        "db_path": str(db_path),
        "relations": [relation.to_dict() for relation in manifest.relations],
        "evidence": evidence,
    }
    storage.write_immutable_json(storage.rollover_binding_path, binding)
    actual = ReceiptAction(
        "task",
        replacement.thread_id,
        (replacement.thread_id, source_id),
        "create_replacement",
        evidence,
    )
    if _action_key(actual) in {_action_key(item) for item in storage.load_receipt().actual}:
        skipped = ReceiptAction(
            "task",
            replacement.thread_id,
            (replacement.thread_id, source_id),
            "create_retry_readback",
            "Exact binding already persisted; no second create call.",
        )
        _event(
            storage,
            state=LifecycleState.VERIFIED,
            kind="native_create_retry_reconciled",
            details={"replacement_thread_id": replacement.thread_id},
        )
        _append_receipt(storage, skipped=skipped)
    else:
        _event(
            storage,
            state=LifecycleState.VERIFIED,
            kind="native_create_bound",
            details={"replacement_thread_id": replacement.thread_id, "evidence": evidence},
        )
        _append_receipt(storage, actual=actual)
    storage.write_state(
        LifecycleState.VERIFIED,
        details={"status": "awaiting_native_title", "replacement_thread_id": replacement.thread_id},
    )
    return binding


def _has_actual(storage: TaskFamilyStorage, action: str) -> bool:
    return any(item.action == action for item in storage.load_receipt().actual)


def _last_ack(storage: TaskFamilyStorage, action: str) -> bool | None:
    prefix = f"native_{action}_ack_"
    matches = [event for event in storage.load_events() if event.kind.startswith(prefix)]
    if not matches:
        return None
    return matches[-1].kind == f"native_{action}_ack_succeeded"


def record_native_result(
    *,
    repo_root: Path,
    family_id: str,
    operation_id: str,
    action: str,
    succeeded: bool,
    evidence: str,
    error: str = "",
) -> dict[str, Any]:
    if action not in NATIVE_ACTIONS:
        raise ValueError(f"unsupported native rollover action: {action}")
    storage = TaskFamilyStorage(repo_root, family_id, operation_id)
    plan = _load_plan(storage)
    binding = _load_binding(storage) if action != "create" and storage.rollover_binding_path.exists() else None
    endpoint = "replacement" if action == "title" else "source"
    resource_id = plan["rollover_id"] if binding is None else binding[f"{endpoint}_thread_id"]
    if not evidence.strip():
        raise ValueError("native action evidence is required")
    if succeeded:
        _event(
            storage,
            state=LifecycleState.VERIFIED,
            kind=f"native_{action}_ack_succeeded",
            details={"resource_id": resource_id, "evidence": evidence},
        )
        actual = ReceiptAction(
            "task" if binding else "rollover",
            resource_id,
            (resource_id,),
            f"native_{action}_ack",
            evidence,
        )
        _append_receipt(storage, actual=actual)
        status = f"native_{action}_acknowledged"
    else:
        message = error.strip() or "native action failed without an error detail"
        recovery = f"Retry the exact {action} action after checking the receipt; never choose a new task by title."
        _event(
            storage,
            state=LifecycleState.BLOCKED,
            kind=f"native_{action}_ack_failed",
            details={"resource_id": resource_id, "evidence": evidence, "error": message},
        )
        failure = ReceiptAction(
            "task" if binding else "rollover",
            resource_id,
            (resource_id,),
            f"native_{action}_failed",
            evidence,
            message,
            recovery,
        )
        _append_receipt(storage, failure=failure)
        storage.write_state(
            LifecycleState.BLOCKED,
            details={"status": f"native_{action}_failed", "recovery": recovery},
        )
        status = f"native_{action}_failed"
    return {
        "ok": succeeded,
        "action": action,
        "resource_id": resource_id,
        "status": status,
        "receipt_path": str(storage.receipt_path),
    }


def record_blocker(
    *,
    repo_root: Path,
    family_id: str,
    operation_id: str,
    action: str,
    error: str,
    evidence: str,
) -> dict[str, Any]:
    """Persist a pre-mutation failure without misreporting a native call."""
    storage = TaskFamilyStorage(repo_root, family_id, operation_id)
    plan = _load_plan(storage)
    binding = _load_binding(storage) if storage.rollover_binding_path.exists() else None
    endpoint = "replacement" if action == "title" else "source"
    resource_id = plan["rollover_id"] if binding is None else binding[f"{endpoint}_thread_id"]
    recovery = "Repair the exact precondition, then ask for the same persisted action again."
    failure = ReceiptAction(
        "task" if binding else "rollover",
        resource_id,
        (resource_id,),
        f"{action}_preflight_blocked",
        evidence,
        error,
        recovery,
    )
    _event(
        storage,
        state=LifecycleState.BLOCKED,
        kind=f"rollover_{action}_preflight_blocked",
        details={"resource_id": resource_id, "error": error, "evidence": evidence},
    )
    _append_receipt(storage, failure=failure)
    storage.write_state(
        LifecycleState.BLOCKED,
        details={"status": f"{action}_preflight_blocked", "error": error, "recovery": recovery},
    )
    return {
        "ok": False,
        "action": action,
        "status": "blocked",
        "task_id": resource_id,
        "error": error,
        "receipt_path": str(storage.receipt_path),
    }


def request_create_action(
    *,
    repo_root: Path,
    family_id: str,
    operation_id: str,
) -> dict[str, Any]:
    """Return one retry-safe native create decision before exact-ID binding."""
    storage = TaskFamilyStorage(repo_root, family_id, operation_id)
    plan = _load_plan(storage)
    operation_state = storage.load_state()
    operation_status = operation_state["details"].get("status")
    if operation_status in {"supersession_pending", "superseded_before_native_create"}:
        return {
            "ok": False,
            "action": "create",
            "status": operation_status,
            "needs_native_action": False,
            "recovery": (
                "Finish exact predecessor-intent reconciliation. Never create from a pending or superseded receipt."
            ),
            "receipt_path": str(storage.receipt_path),
        }
    if storage.rollover_binding_path.exists():
        binding = _load_binding(storage)
        skipped = ReceiptAction(
            "task",
            binding["replacement_thread_id"],
            (binding["replacement_thread_id"], plan["source_thread_id"]),
            "create_retry_readback",
            "Exact replacement binding already exists; no second native create is authorized.",
        )
        _event(
            storage,
            state=LifecycleState.VERIFIED,
            kind="native_create_retry_reconciled",
            details={"replacement_thread_id": binding["replacement_thread_id"]},
        )
        _append_receipt(storage, skipped=skipped)
        return {
            "ok": True,
            "action": "create",
            "status": "already_bound",
            "needs_native_action": False,
            "replacement_thread_id": binding["replacement_thread_id"],
            "receipt_path": str(storage.receipt_path),
        }
    if _last_ack(storage, "create") is True:
        recovery = "Recover the exact threadId from the acknowledged create result, then run register-created."
        if not any(item.action == "create_binding_missing_after_ack" for item in storage.load_receipt().failures):
            failure = ReceiptAction(
                "rollover",
                plan["rollover_id"],
                (plan["source_thread_id"],),
                "create_binding_missing_after_ack",
                "Native create succeeded, but exact replacement binding is incomplete.",
                "A second create is forbidden after a successful native acknowledgement.",
                recovery,
            )
            _event(
                storage,
                state=LifecycleState.BLOCKED,
                kind="native_create_binding_missing_after_ack",
                details={"rollover_id": plan["rollover_id"]},
            )
            _append_receipt(storage, failure=failure)
        storage.write_state(
            LifecycleState.BLOCKED,
            details={"status": "awaiting_create_binding", "recovery": recovery},
        )
        return {
            "ok": False,
            "action": "create",
            "status": "awaiting_create_binding",
            "needs_native_action": False,
            "recovery": recovery,
            "receipt_path": str(storage.receipt_path),
        }
    storage.write_state(
        LifecycleState.PLANNED,
        details={"status": "native_create_authorized", "source_thread_id": plan["source_thread_id"]},
    )
    if not any(event.kind == "native_create_authorized" for event in storage.load_events()):
        _event(
            storage,
            state=LifecycleState.PLANNED,
            kind="native_create_authorized",
            details={"rollover_id": plan["rollover_id"], "source_thread_id": plan["source_thread_id"]},
        )
        _append_receipt(storage)
    return {
        "ok": True,
        "action": "create",
        "status": "needs_native_action",
        "needs_native_action": True,
        "tool": "create_thread",
        "bootstrap_prompt_path": plan["bootstrap_prompt_path"],
        "intended_title": plan["intended_title"],
        "source_thread_id": plan["source_thread_id"],
        "receipt_path": str(storage.receipt_path),
    }


def _exact_record(binding: dict[str, Any], *, action: str, db_path: Path) -> codex_state.ThreadRecord:
    endpoint = "replacement" if action == "title" else "source"
    task_id = binding[f"{endpoint}_thread_id"]
    record = codex_state.read_thread_record(db_path, task_id=task_id)
    expected_cwd = binding[f"{endpoint}_cwd"]
    expected_host = binding[f"{endpoint}_host"]
    if record.cwd != expected_cwd or (expected_host is not None and record.host != expected_host):
        raise codex_state.CodexStateContextError("exact rollover task cwd or host no longer matches the native binding")
    return record


def reconcile_action(
    *,
    repo_root: Path,
    family_id: str,
    operation_id: str,
    action: Literal["title", "archive"],
    db_path: Path,
) -> dict[str, Any]:
    storage = TaskFamilyStorage(repo_root, family_id, operation_id)
    binding = _load_binding(storage)
    endpoint = "replacement" if action == "title" else "source"
    reconciled_action = f"{action}_reconciled"
    if _has_actual(storage, reconciled_action):
        skipped = ReceiptAction(
            "task",
            binding[f"{endpoint}_thread_id"],
            (),
            f"{action}_retry_readback",
            "Already reconciled; no second native mutation was performed.",
        )
        final_state = LifecycleState.VERIFIED if action == "title" else LifecycleState.TASKS_ARCHIVED
        _event(
            storage,
            state=final_state,
            kind=f"native_{action}_retry_reconciled",
            details={"readback_only": True},
        )
        _append_receipt(storage, skipped=skipped)
        return {"ok": True, "action": action, "status": "already_reconciled", "readback_only": True}
    try:
        if action == "title":
            record = _exact_record(binding, action=action, db_path=db_path)
            if record.title != binding["intended_title"]:
                raise codex_state.CodexStateContextError(
                    "replacement title has not reached the persisted intended title"
                )
            final_state = LifecycleState.VERIFIED
        else:
            record = codex_state.await_task_target(
                task_id=binding["source_thread_id"],
                expected_title=binding["source_title"],
                expected_cwd=binding["source_cwd"],
                expected_host=binding["source_host"],
                expected_archived=True,
                db_path=db_path,
            )
            final_state = LifecycleState.TASKS_ARCHIVED
    except (codex_state.CodexStateError, ValueError) as exc:
        task_id = binding[f"{endpoint}_thread_id"]
        recovery = "Do not repeat a successful native acknowledgement; retry read-back first."
        failure = ReceiptAction(
            "task",
            task_id,
            (task_id,),
            f"{action}_reconciliation_failed",
            "Native read-back did not reach the exact persisted target.",
            str(exc),
            recovery,
        )
        _event(
            storage,
            state=LifecycleState.BLOCKED,
            kind=f"native_{action}_reconciliation_failed",
            details={"task_id": task_id, "error": str(exc), "native_ack": _last_ack(storage, action)},
        )
        _append_receipt(storage, failure=failure)
        storage.write_state(
            LifecycleState.BLOCKED,
            details={"status": f"{action}_reconciliation_failed", "native_ack": _last_ack(storage, action)},
        )
        return {
            "ok": False,
            "action": action,
            "status": "reconciliation_failed",
            "error": str(exc),
            "native_ack": _last_ack(storage, action),
        }
    task_id = record.thread_id
    actual = ReceiptAction(
        "task",
        task_id,
        (task_id,),
        reconciled_action,
        "Native DB read-back verified the exact persisted target.",
    )
    readback_only = _last_ack(storage, action) is not True
    _event(
        storage,
        state=final_state,
        kind=f"native_{action}_reconciled",
        details={"task_id": task_id, "readback_only": readback_only},
    )
    _append_receipt(storage, final_state=final_state, actual=actual)
    storage.write_state(final_state, details={"status": reconciled_action, "task_id": task_id})
    return {
        "ok": True,
        "action": action,
        "status": reconciled_action,
        "task_id": task_id,
        "readback_only": readback_only,
    }


def _confirmation_blockers(state: dict[str, Any], binding: dict[str, Any]) -> list[str]:
    replacement = state.get("replacement") or {}
    cleanup = state.get("cleanup") or {}
    blockers: list[str] = []
    if replacement.get("status") != "started":
        blockers.append("replacement is not confirmed started")
    if replacement.get("thread_id") != binding["replacement_thread_id"]:
        blockers.append("confirmed replacement identity does not match the native binding")
    if replacement.get("resumed_thread_id") != binding["replacement_thread_id"]:
        blockers.append("resumed replacement identity does not match the native binding")
    if (state.get("active") or {}).get("thread_id") != binding["source_thread_id"]:
        blockers.append("persisted predecessor identity does not match the native binding")
    if cleanup.get("old_automation_ready_to_delete") is not True:
        blockers.append("existing confirmation cleanup proof gate is still locked")
    proof = replacement.get("canary_proof") or {}
    verdict = replacement.get("strict_verdict") or {}
    if proof.get("verdict") != "PASS":
        blockers.append("script canary proof is not PASS")
    if verdict.get("verdict") != "PASS" or verdict.get("correct") != 10 or verdict.get("k") != 10:
        blockers.append("strict recall verdict is not PASS 10/10")
    return blockers


def authorize_archive(
    *,
    repo_root: Path,
    family_id: str,
    operation_id: str,
    state: dict[str, Any],
    source_status: str,
    pin_state: PinState,
    evidence: str,
) -> dict[str, Any]:
    storage = TaskFamilyStorage(repo_root, family_id, operation_id)
    binding = _load_binding(storage)
    blockers = _confirmation_blockers(state, binding)
    if not _has_actual(storage, "title_reconciled"):
        blockers.append("replacement title has not been reconciled")
    if source_status.strip().lower() != "idle":
        blockers.append(f"predecessor status is not authoritatively idle: {source_status or 'unknown'}")
    if pin_state != "unpinned":
        blockers.append(f"predecessor pin state is not authoritatively unpinned: {pin_state}")
    if not evidence.strip():
        blockers.append("app task-state evidence is missing")
    if blockers:
        message = "; ".join(blockers)
        recovery = (
            "Retry only after exact idle and unpinned app evidence is available for the persisted predecessor UUID."
        )
        failure = ReceiptAction(
            "task",
            binding["source_thread_id"],
            (binding["source_thread_id"],),
            "archive_authorization_blocked",
            f"Predecessor preserved. App evidence: {evidence or 'missing'}",
            message,
            recovery,
        )
        _event(
            storage,
            state=LifecycleState.BLOCKED,
            kind="rollover_archive_authorization_blocked",
            details={"task_id": binding["source_thread_id"], "blockers": blockers, "evidence": evidence},
        )
        _append_receipt(storage, failure=failure)
        storage.write_state(
            LifecycleState.BLOCKED,
            details={"status": "archive_authorization_blocked", "blockers": blockers},
        )
        return {
            "ok": False,
            "status": "blocked",
            "task_id": binding["source_thread_id"],
            "blockers": blockers,
            "receipt_path": str(storage.receipt_path),
        }
    replacement = state["replacement"]
    authorization = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "kind": "rollover_predecessor_archive_authorization",
        "plan_digest": _load_plan(storage)["digest"],
        "source_thread_id": binding["source_thread_id"],
        "replacement_thread_id": binding["replacement_thread_id"],
        "source_status": "idle",
        "pin_state": "unpinned",
        "evidence": evidence,
        "canary_proof_sha256": sha256_digest(replacement["canary_proof"]),
        "strict_verdict_sha256": sha256_digest(replacement["strict_verdict"]),
        "confirmed_at": replacement["confirmed_at"],
    }
    if storage.rollover_archive_authorization_path.exists():
        existing_authorization = storage.read_json(storage.rollover_archive_authorization_path)
        stable_existing = dict(existing_authorization)
        stable_existing.pop("evidence", None)
        stable_retry = dict(authorization)
        stable_retry.pop("evidence", None)
        if stable_existing != stable_retry:
            raise ValueError("persisted predecessor archive authorization no longer matches the proof state")
    else:
        storage.write_immutable_json(storage.rollover_archive_authorization_path, authorization)
    _event(
        storage,
        state=LifecycleState.VERIFIED,
        kind="rollover_archive_authorized",
        details={"task_id": binding["source_thread_id"], "evidence": evidence},
    )
    storage.write_state(
        LifecycleState.VERIFIED,
        details={"status": "awaiting_native_archive", "task_id": binding["source_thread_id"]},
    )
    return {
        "ok": True,
        "status": "actionable",
        "task_id": binding["source_thread_id"],
        "tool": "set_thread_archived",
        "arguments": {"threadId": binding["source_thread_id"], "archived": True},
        "receipt_path": str(storage.receipt_path),
    }


def request_action(
    *,
    repo_root: Path,
    family_id: str,
    operation_id: str,
    action: Literal["title", "archive"],
    db_path: Path,
    state: dict[str, Any] | None = None,
    source_status: str = "unknown",
    pin_state: PinState = "unknown",
    evidence: str = "",
) -> dict[str, Any]:
    storage = TaskFamilyStorage(repo_root, family_id, operation_id)
    binding = _load_binding(storage)
    if action == "archive":
        if state is None:
            raise ValueError("rollover lease state is required for archive authorization")
        authorization = authorize_archive(
            repo_root=repo_root,
            family_id=family_id,
            operation_id=operation_id,
            state=state,
            source_status=source_status,
            pin_state=pin_state,
            evidence=evidence,
        )
        if not authorization["ok"]:
            return authorization
    try:
        current = _exact_record(binding, action=action, db_path=db_path)
    except (codex_state.CodexStateError, ValueError) as exc:
        return record_blocker(
            repo_root=repo_root,
            family_id=family_id,
            operation_id=operation_id,
            action=action,
            error=str(exc),
            evidence="native read-back preflight",
        )
    target_satisfied = current.title == binding["intended_title"] if action == "title" else current.archived
    if target_satisfied:
        reconciled = reconcile_action(
            repo_root=repo_root,
            family_id=family_id,
            operation_id=operation_id,
            action=action,
            db_path=db_path,
        )
        return {**reconciled, "needs_native_action": False}
    if _last_ack(storage, action) is True:
        reconciled = reconcile_action(
            repo_root=repo_root,
            family_id=family_id,
            operation_id=operation_id,
            action=action,
            db_path=db_path,
        )
        return {
            **reconciled,
            "needs_native_action": False,
            "status": "awaiting_readback",
            "recovery": "Retry reconciliation only; the native action already acknowledged success.",
        }
    endpoint = "replacement" if action == "title" else "source"
    task_id = binding[f"{endpoint}_thread_id"]
    if action == "title":
        tool = "set_thread_title"
        arguments = {"threadId": task_id, "title": binding["intended_title"]}
    else:
        tool = "set_thread_archived"
        arguments = {"threadId": task_id, "archived": True}
    storage.write_state(
        LifecycleState.VERIFIED,
        details={"status": f"awaiting_native_{action}", "task_id": task_id},
    )
    return {
        "ok": True,
        "action": action,
        "status": "needs_native_action",
        "needs_native_action": True,
        "task_id": task_id,
        "tool": tool,
        "arguments": arguments,
        "receipt_path": str(storage.receipt_path),
    }


def resolve_db(value: str | Path) -> Path:
    """Resolve ``auto`` with the same fail-closed discovery as the TFM CLI."""
    return codex_state.discover_state_database(None if str(value) == "auto" else Path(value))
