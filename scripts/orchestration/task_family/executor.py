"""Fail-closed, resumable executor for task-family cleanup operations."""

from __future__ import annotations

import hashlib
import json
import uuid
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from scripts.orchestration.task_family import codex_state
from scripts.orchestration.task_family import git_safety as safety
from scripts.orchestration.task_family.model import LifecycleState, OperationReceipt, ReceiptAction
from scripts.orchestration.task_family.storage import TaskFamilyStorage, atomic_write_text

CLEANUP_STAGES = (
    "planned",
    "frozen",
    "verified",
    "snapshotted",
    "tasks_archived",
    "worktrees_removed",
    "branches_deleted",
    "runtime_retired",
    "completed",
)

CLEANUP_MODES = {
    "archive_only",
    "finish_and_clean",
}

ResourceStatus = Literal["planned", "actual", "skipped", "failed"]


class ExecutorError(RuntimeError):
    """Cleanup execution blocked by safety guard or data mismatch."""


class ExecutionStateError(ExecutorError):
    """Invalid persisted state or impossible resume shape."""


@dataclass(frozen=True)
class TaskTarget:
    task_id: str
    title: str
    cwd: str
    db_path: Path
    expected_archived: bool = True
    host: str | None = None


@dataclass(frozen=True)
class WorktreeTarget:
    id: str
    worktree: Path
    branch: str
    pr_number: int
    pr_base: str
    explicit_family: str


@dataclass(frozen=True)
class RuntimeTarget:
    id: str
    kind: str
    eligible: bool
    proof: str | None = None


@dataclass(frozen=True)
class CleanupPlan:
    operation_id: str
    family_id: str
    lineage_id: str
    mode: str
    task_targets: tuple[TaskTarget, ...]
    worktree_targets: tuple[WorktreeTarget, ...]
    runtime_targets: tuple[RuntimeTarget, ...]
    selected_task_ids: frozenset[str]
    pin_unknown_confirmed: bool
    persisted_plan_digest: str
    explicit_protected: frozenset[str] = frozenset()


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def state_path(repo_root: Path, plan: CleanupPlan) -> Path:
    return TaskFamilyStorage(
        safety.resolve_main_root(repo_root), plan.family_id, plan.operation_id
    ).state_path


def plan_path(repo_root: Path, plan: CleanupPlan) -> Path:
    return TaskFamilyStorage(
        safety.resolve_main_root(repo_root), plan.family_id, plan.operation_id
    ).plan_path


def receipt_path(repo_root: Path, plan: CleanupPlan) -> Path:
    return TaskFamilyStorage(
        safety.resolve_main_root(repo_root), plan.family_id, plan.operation_id
    ).receipt_path


def manifest_path(repo_root: Path, plan: CleanupPlan) -> Path:
    return TaskFamilyStorage(
        safety.resolve_main_root(repo_root), plan.family_id, plan.operation_id
    ).manifest_path


def _as_text(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, frozenset):
        return sorted(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return {str(k): _as_text(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_as_text(item) for item in value]
    if isinstance(value, set):
        return sorted(value)
    return value


def _serialize_target(target: Any) -> dict[str, Any]:
    if isinstance(target, TaskTarget):
        return {
            "task_id": target.task_id,
            "title": target.title,
            "cwd": target.cwd,
            "db_path": str(target.db_path),
            "expected_archived": target.expected_archived,
            "host": target.host,
        }
    if isinstance(target, WorktreeTarget):
        return {
            "id": target.id,
            "worktree": str(target.worktree),
            "branch": target.branch,
            "pr_number": target.pr_number,
            "pr_base": target.pr_base,
            "explicit_family": target.explicit_family,
        }
    if isinstance(target, RuntimeTarget):
        return {
            "id": target.id,
            "kind": target.kind,
            "eligible": target.eligible,
            "proof": target.proof,
        }
    raise TypeError(f"unsupported target payload type: {type(target)!r}")


def _canonical_plan_digest(payload: dict[str, Any]) -> str:
    """Match the planner's immutable digest without accepting mutable state."""
    immutable = dict(payload)
    immutable.pop("digest", None)
    immutable.pop("state", None)
    body = json.dumps(immutable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _load_persisted_plan(repo_root: Path, plan: CleanupPlan) -> dict[str, Any]:
    """Read the planner-owned immutable plan; executor never creates or rewrites it."""
    path = plan_path(repo_root, plan)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ExecutorError(f"persisted immutable plan missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ExecutorError(f"persisted immutable plan is invalid JSON: {path}") from exc
    if not isinstance(raw, dict):
        raise ExecutorError("persisted immutable plan must be an object")
    persisted_digest = raw.get("digest")
    canonical_digest = _canonical_plan_digest(raw)
    if persisted_digest != canonical_digest or plan.persisted_plan_digest != canonical_digest:
        raise ExecutorError("caller digest does not authorize the canonical persisted plan")
    if raw.get("operation_id") != plan.operation_id or raw.get("family_id") != plan.family_id:
        raise ExecutorError("persisted immutable plan identity does not match execution request")
    planned_ids = raw.get("selected_task_ids")
    if not isinstance(planned_ids, list) or not all(isinstance(item, str) for item in planned_ids):
        raise ExecutorError("persisted immutable plan selected_task_ids must be string UUIDs")
    try:
        normalized_ids = {str(uuid.UUID(item)) for item in planned_ids}
    except ValueError as exc:
        raise ExecutorError("persisted immutable plan has an invalid task UUID") from exc
    if len(normalized_ids) != len(planned_ids):
        raise ExecutorError("persisted immutable plan repeats a selected task UUID")
    if normalized_ids != set(plan.selected_task_ids):
        raise ExecutorError("persisted plan selection drifted from execution request")
    _assert_manifest_task_ids(repo_root, plan, normalized_ids)
    return raw


def _assert_manifest_task_ids(repo_root: Path, plan: CleanupPlan, selected_ids: set[str]) -> None:
    path = manifest_path(repo_root, plan)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ExecutorError(f"persisted manifest missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ExecutorError(f"persisted manifest is invalid JSON: {path}") from exc
    if not isinstance(payload, dict) or payload.get("family_id") != plan.family_id:
        raise ExecutorError("persisted manifest identity does not match execution request")
    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not all(isinstance(node, dict) for node in nodes):
        raise ExecutorError("persisted manifest nodes must be an object list")
    try:
        manifest_ids = {str(uuid.UUID(str(node.get("task_id", "")))) for node in nodes}
    except ValueError as exc:
        raise ExecutorError("persisted manifest has an invalid task UUID") from exc
    if len(manifest_ids) != len(nodes) or not selected_ids.issubset(manifest_ids):
        raise ExecutorError("manifest task IDs do not exactly cover selected task UUIDs")


def _resource_block_for_targets(name: str, *, targets: tuple[Any, ...], selected_only: bool = False) -> dict[str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    for target in targets:
        item = {
            "type": name,
            "status": "planned",
            "planned": _serialize_target(target),
            "actual": None,
            "selected": True,
        }
        if selected_only and hasattr(target, "id"):
            item["selected"] = False
        resource_id = target.task_id if isinstance(target, TaskTarget) else str(target.id)
        items[resource_id] = item
    return items


def _bundle_path_to_record(bundle: safety.BundleReceipt | None) -> dict[str, Any] | None:
    if bundle is None:
        return None
    return {
        "path": str(bundle.path),
        "sha256": bundle.sha256,
        "branch": bundle.branch,
        "created_at": bundle.created_at,
    }


def _load_bundle(record: Any) -> safety.BundleReceipt:
    if not isinstance(record, dict):
        raise ExecutorError("invalid bundle record")
    return safety.BundleReceipt(
        path=Path(str(record.get("path", ""))),
        sha256=str(record.get("sha256", "")),
        branch=str(record.get("branch", "")),
        created_at=str(record.get("created_at", "")),
    )


def _ensure_ids(payload: dict[str, Any], plan: CleanupPlan) -> dict[str, Any]:
    payload.setdefault("resources", {})
    resources = payload["resources"]
    resources.setdefault(
        "task",
        _resource_block_for_targets("task", targets=plan.task_targets, selected_only=False),
    )
    resources.setdefault(
        "worktree",
        _resource_block_for_targets("worktree", targets=plan.worktree_targets, selected_only=False),
    )
    resources.setdefault(
        "runtime",
        _resource_block_for_targets("runtime", targets=plan.runtime_targets),
    )

    for target in plan.task_targets:
        entry = resources["task"].setdefault(
            target.task_id,
            _resource_block_for_targets("task", targets=(target,))[target.task_id],
        )
        entry["selected"] = target.task_id in plan.selected_task_ids
    return payload


def _default_state(plan: CleanupPlan) -> dict[str, Any]:
    return {
        "operation_id": plan.operation_id,
        "family_id": plan.family_id,
        "lineage_id": plan.lineage_id,
        "mode": plan.mode,
        "plan_digest": plan.persisted_plan_digest,
        "state": "planned",
        "resume_stage": None,
        "updated_at": _iso_now(),
        "blocked": None,
        "resources": {
            "task": _resource_block_for_targets("task", targets=plan.task_targets),
            "worktree": _resource_block_for_targets("worktree", targets=plan.worktree_targets),
            "runtime": _resource_block_for_targets("runtime", targets=plan.runtime_targets),
        },
        "stages": {},
        "history": ["planned"],
    }


def _serializable_receipt(payload: Any) -> Any:
    if isinstance(payload, safety.BundleReceipt):
        return _bundle_path_to_record(payload)
    return payload


def _record(payload: dict[str, Any], stage: str, key: str, value: Any) -> None:
    recorded = dict(payload.setdefault("stages", {}).get(stage, {}))
    recorded[key] = _serializable_receipt(value)
    payload.setdefault("stages", {})[stage] = recorded


def _record_resource(payload: dict[str, Any], kind: str, resource_id: str, status: ResourceStatus, *, evidence: Any | None = None, reason: str | None = None) -> None:
    resources = payload.setdefault("resources", {}).setdefault(kind, {})
    entry = resources.setdefault(resource_id, {"status": "planned"})
    entry["status"] = status
    if reason is not None:
        entry["reason"] = reason
    if evidence is not None:
        entry["actual"] = _as_text(evidence)
    else:
        entry.pop("actual", None)


def load_state(repo_root: Path, plan: CleanupPlan) -> dict[str, Any]:
    path = state_path(repo_root, plan)
    if not path.exists():
        return _ensure_ids(_default_state(plan), plan)

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExecutionStateError(f"state file {path} is invalid JSON") from exc
    if not isinstance(raw, dict):
        raise ExecutionStateError(f"state file {path} must be an object")
    # ``TaskFamilyStorage`` writes a preview seed before execution.  It is not
    # executor state and must never be treated as a partially completed run.
    if "operation_id" not in raw and raw.get("schema_version") == 1 and isinstance(raw.get("details"), dict):
        if raw.get("state") != "planned":
            raise ExecutionStateError("task-family preview state is not planned")
        return _ensure_ids(_default_state(plan), plan)
    return _ensure_ids(raw, plan)


def _set_blocked(
    path: Path,
    payload: dict[str, Any],
    *,
    stage: str,
    error: str,
) -> dict[str, Any]:
    payload["state"] = "blocked"
    payload["resume_stage"] = stage
    payload["blocked"] = {
        "stage": stage,
        "reason": error,
        "updated_at": _iso_now(),
    }
    payload["updated_at"] = _iso_now()
    payload.setdefault("history", [])
    if not payload["history"] or payload["history"][-1] != "blocked":
        payload["history"].append("blocked")
    return persist_state(path, payload)


def _dedupe_actions(actions: tuple[ReceiptAction, ...]) -> tuple[ReceiptAction, ...]:
    seen: set[tuple[str, str, str]] = set()
    result: list[ReceiptAction] = []
    for action in actions:
        key = (action.resource_type, action.resource_id, action.action)
        if key in seen:
            continue
        seen.add(key)
        result.append(action)
    return tuple(result)


def _initial_receipt(payload: dict[str, Any]) -> OperationReceipt:
    raw = payload.get("initial_receipt")
    if isinstance(raw, dict):
        try:
            return OperationReceipt.from_dict(raw)
        except ValueError:
            pass
    return OperationReceipt(
        operation_id=str(payload["operation_id"]),
        family_id=str(payload["family_id"]),
        plan_digest=str(payload["plan_digest"]),
        final_state=LifecycleState.PLANNED,
    )


def _resource_actions(payload: dict[str, Any]) -> tuple[tuple[ReceiptAction, ...], tuple[ReceiptAction, ...], tuple[ReceiptAction, ...]]:
    """Return exact actual, skipped, and failed resource outcomes."""
    actual: list[ReceiptAction] = []
    skipped: list[ReceiptAction] = []
    failures: list[ReceiptAction] = []
    resources = payload.get("resources", {})
    if not isinstance(resources, dict):
        return (), (), ()
    branch_results = payload.get("stages", {}).get("branches_deleted", {}).get("results", {})
    if not isinstance(branch_results, dict):
        branch_results = {}
    action_by_kind = {
        "task": "archive",
        "worktree": "retire_local_worktree_and_branch",
        "runtime": "retire_runtime",
    }
    for kind in ("task", "worktree", "runtime"):
        entries = resources.get(kind, {})
        if not isinstance(entries, dict):
            continue
        for resource_id, entry in sorted(entries.items()):
            if not isinstance(entry, dict):
                continue
            status = entry.get("status")
            if kind == "worktree":
                branch_status = branch_results.get(resource_id, {})
                if not isinstance(branch_status, dict):
                    branch_status = {}
                if branch_status.get("status") == "deleted":
                    status = "actual"
                elif branch_status.get("status") == "already_absent":
                    status = "skipped"
                elif status == "actual":
                    continue
            reason = str(entry.get("reason") or f"executor resource status: {status or 'unknown'}")
            action = ReceiptAction(
                kind,
                str(resource_id),
                (str(resource_id),),
                action_by_kind[kind],
                reason,
                reason if status == "failed" else "",
                "Inspect state.json and retained snapshots before retrying." if status == "failed" else "",
            )
            if status == "actual":
                actual.append(action)
            elif status == "skipped":
                skipped.append(action)
            elif status == "failed":
                failures.append(action)
    return tuple(actual), tuple(skipped), tuple(failures)


def _final_resource_actions(payload: dict[str, Any]) -> tuple[ReceiptAction, ...]:
    resources = payload.get("resources", {})
    if not isinstance(resources, dict):
        return ()
    branch_results = payload.get("stages", {}).get("branches_deleted", {}).get("results", {})
    if not isinstance(branch_results, dict):
        branch_results = {}
    actions: list[ReceiptAction] = []
    for kind in ("task", "worktree", "runtime"):
        entries = resources.get(kind, {})
        if not isinstance(entries, dict):
            continue
        for resource_id, entry in sorted(entries.items()):
            status = entry.get("status") if isinstance(entry, dict) else "unknown"
            branch_status = branch_results.get(resource_id, {}) if kind == "worktree" else {}
            if isinstance(branch_status, dict) and branch_status.get("status") == "deleted":
                status = "retired"
            elif isinstance(branch_status, dict) and branch_status.get("status") == "already_absent":
                status = "already_absent"
            action = {
                ("task", "actual"): "archived",
                ("worktree", "retired"): "retired",
                ("worktree", "already_absent"): "retired_before_resume",
                ("runtime", "actual"): "retired",
            }.get((kind, status), "retained")
            actions.append(
                ReceiptAction(
                    kind,
                    str(resource_id),
                    (str(resource_id),),
                    action,
                    f"final executor resource status: {status}",
                )
            )
    return tuple(actions)


def _receipt_payload(payload: dict[str, Any]) -> OperationReceipt:
    """Build one durable receipt without discarding native reconciliation."""
    initial = _initial_receipt(payload)
    resource_actual, resource_skipped, resource_failures = _resource_actions(payload)
    try:
        final_state = LifecycleState(str(payload["state"]))
    except ValueError as exc:
        raise ExecutionStateError(f"invalid receipt lifecycle state: {payload.get('state')!r}") from exc
    return OperationReceipt(
        operation_id=initial.operation_id,
        family_id=initial.family_id,
        plan_digest=initial.plan_digest,
        final_state=final_state,
        planned=initial.planned,
        actual=_dedupe_actions((*initial.actual, *resource_actual)),
        skipped=_dedupe_actions((*initial.skipped, *resource_skipped)),
        failures=_dedupe_actions((*initial.failures, *resource_failures)),
        restoration=initial.restoration,
        final_resources=_final_resource_actions(payload),
        events=initial.events,
    )


def _capture_initial_receipt(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("initial_receipt"), dict):
        return payload
    receipt_file = path.with_name("receipt.json")
    try:
        raw = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt = OperationReceipt.from_dict(raw)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        receipt = _initial_receipt(payload)
    payload["initial_receipt"] = receipt.to_dict()
    return payload


def persist_state(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["updated_at"] = _iso_now()
    safety.write_json_atomic(path, payload)
    receipt = _receipt_payload(payload)
    safety.write_json_atomic(path.with_name("receipt.json"), receipt.to_dict())
    atomic_write_text(path.with_name("receipt.txt"), receipt.render_human())
    return payload


def _validate_stage(stage: str) -> None:
    if stage not in CLEANUP_STAGES:
        raise ExecutionStateError(f"unknown stage: {stage!r}")


def _starting_stage(payload: dict[str, Any]) -> str:
    state = payload.get("state", "planned")
    if state == "blocked":
        resume = str(payload.get("resume_stage") or "planned")
        _validate_stage(resume)
        return resume
    if state == "completed":
        return "completed"
    if state in CLEANUP_STAGES:
        return str(state)
    raise ExecutionStateError(f"unknown state: {state!r}")


def _extract_simulated_crash_stage(error: str) -> str | None:
    marker = "simulated crash after "
    if not error.startswith(marker):
        return None
    return error[len(marker) :].strip() or None


def _failure_block_stage(stage: str, *, mode: str) -> str:
    if stage == "tasks_archived" and mode == "archive_only":
        return "tasks_archived"
    if stage == "branches_deleted":
        return "runtime_retired"
    return stage


def _validate_uuid(value: str) -> None:
    if str(uuid.UUID(value)) != value:
        raise ExecutorError(f"UUID must use canonical lowercase text: {value!r}")


def _validate_plan(plan: CleanupPlan) -> None:
    if plan.mode not in CLEANUP_MODES:
        raise ExecutorError(f"invalid cleanup mode: {plan.mode!r}")
    _validate_uuid(str(plan.operation_id))
    if not plan.family_id:
        raise ExecutorError("family_id is required")
    _validate_uuid(str(plan.lineage_id))
    if not plan.task_targets and not plan.pin_unknown_confirmed:
        raise ExecutorError("selected_task_ids must be pinned when no task targets are explicit")
    if not plan.pin_unknown_confirmed:
        raise ExecutorError("pin_unknown_confirmed is required")
    if not isinstance(plan.persisted_plan_digest, str) or len(plan.persisted_plan_digest) != 64:
        raise ExecutorError("caller-supplied persisted_plan_digest is required")

    task_ids = {target.task_id for target in plan.task_targets}
    if len(task_ids) != len(plan.task_targets) or set(plan.selected_task_ids) != task_ids:
        raise ExecutorError("selected_task_ids, resource keys, and task thread IDs must be identical UUIDs")

    for target in plan.task_targets:
        _validate_uuid(target.task_id)
        if not target.title:
            raise ExecutorError("TaskTarget.title is required")
        if not target.cwd:
            raise ExecutorError("TaskTarget.cwd is required")
        if target.expected_archived is not True:
            raise ExecutorError("Task cleanup currently only supports expected_archived=True")

    for target in plan.worktree_targets:
        _validate_uuid(target.id)
        if not target.branch:
            raise ExecutorError("WorktreeTarget.branch is required")
        if not target.pr_base:
            raise ExecutorError("WorktreeTarget.pr_base is required")
        if not target.pr_number:
            raise ExecutorError("WorktreeTarget.pr_number is required")
        if target.explicit_family and target.explicit_family != plan.family_id:
            raise ExecutorError(
                f"worktree target {target.id!r} explicit_family {target.explicit_family!r} does not match family {plan.family_id!r}"
            )

    for target in plan.runtime_targets:
        _validate_uuid(target.id)
        if not target.kind:
            raise ExecutorError("RuntimeTarget.kind is required")


def _status_ok(state: dict[str, Any] | None) -> bool:
    if not isinstance(state, dict):
        return False
    return state.get("status") in {"actual", "skipped"}


def _extract_task_targets(plan: CleanupPlan) -> dict[str, TaskTarget]:
    return {target.task_id: target for target in plan.task_targets}


def _extract_worktree_targets(plan: CleanupPlan) -> dict[str, WorktreeTarget]:
    return {target.id: target for target in plan.worktree_targets}


class CleanupExecutor:
    """Run and persist one cleanup sequence for a task family."""

    def __init__(
        self,
        repo_root: Path,
        plan: CleanupPlan,
        *,
        crash_after_stage: str | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.plan = plan
        self.crash_after_stage = crash_after_stage

    @property
    def state_file(self) -> Path:
        return state_path(self.repo_root, self.plan)

    def _maybe_crash(self, stage: str) -> None:
        if self.crash_after_stage == stage:
            raise RuntimeError(f"simulated crash after {stage}")

    def run(self) -> dict[str, Any]:
        _validate_plan(self.plan)
        with ExitStack() as locks:
            locks.enter_context(safety.operation_lock(self.repo_root, operation_id=self.plan.operation_id))
            locks.enter_context(safety.lineage_lock(self.repo_root, self.plan.lineage_id))
            locks.enter_context(safety.family_lock(self.repo_root, self.plan.family_id))
            for target in sorted(self.plan.worktree_targets, key=lambda item: str(item.worktree.resolve())):
                locks.enter_context(safety.worktree_lock(self.repo_root, target.worktree))
            return self._run_locked()

    def _run_locked(self) -> dict[str, Any]:
        payload = load_state(self.repo_root, self.plan)
        payload = _capture_initial_receipt(self.state_file, payload)
        try:
            _load_persisted_plan(self.repo_root, self.plan)
        except ExecutorError as exc:
            return _set_blocked(self.state_file, payload, stage="frozen", error=str(exc))
        if payload.get("plan_digest") != self.plan.persisted_plan_digest:
            return _set_blocked(
                self.state_file,
                payload,
                stage="frozen",
                error="plan digest changed; rebuild explicit plan before resume",
            )

        if payload.get("operation_id") != self.plan.operation_id:
            raise ExecutionStateError("operation_id changed for same state file")
        if payload.get("family_id") != self.plan.family_id:
            raise ExecutionStateError("family_id changed for same state file")

        stage = _starting_stage(payload)
        if stage == "completed" or (self.plan.mode == "archive_only" and stage == "tasks_archived"):
            return payload

        blocked_payload = payload.get("blocked")
        blocked_stage = None
        if payload.get("state") == "blocked" and isinstance(blocked_payload, dict):
            blocked_stage = blocked_payload.get("stage")
            if not isinstance(blocked_stage, str):
                blocked_stage = None
        if blocked_stage is None and isinstance(blocked_payload, dict):
            blocked_stage = _extract_simulated_crash_stage(str(blocked_payload.get("reason", "")))

        try:
            while stage != "completed":
                _validate_stage(stage)
                next_stage = self._advance_once(payload, stage)
                if next_stage == stage:
                    raise ExecutorError(f"transition for {stage!r} did not advance")
                payload = _update_state(self.state_file, payload, next_state=next_stage)
                _record(payload, next_stage, "stage_transition_ok", True)
                payload = persist_state(self.state_file, payload)
                stage = next_stage
                if self.plan.mode == "archive_only" and stage == "tasks_archived":
                    return payload
            return payload
        except (ExecutorError, RuntimeError) as exc:
            if blocked_stage is None:
                blocked_stage = _failure_block_stage(stage, mode=self.plan.mode)
            return _set_blocked(self.state_file, payload, stage=blocked_stage, error=str(exc))

    def _verify_frozen_gate_once(self) -> None:
        for target in self.plan.worktree_targets:
            safety.verify_frozen_preconditions(
                self.repo_root,
                operation_id=self.plan.operation_id,
                lineage_id=self.plan.lineage_id,
                family=self.plan.family_id,
                worktree=target.worktree,
            )

    def _advance_once(self, payload: dict[str, Any], stage: str) -> str:
        if stage == "planned":
            return self._to_frozen(payload)
        if stage == "frozen":
            return self._to_verified(payload)
        if stage == "verified":
            return self._to_snapshotted(payload)
        if stage == "snapshotted":
            return self._to_tasks_archived(payload)
        if stage == "tasks_archived":
            return self._to_worktrees_or_complete(payload)
        if stage == "worktrees_removed":
            return self._to_branches_deleted(payload)
        if stage == "branches_deleted":
            return self._to_runtime_retired(payload)
        if stage == "runtime_retired":
            return self._to_completed(payload)
        if stage == "completed":
            return "completed"
        raise ExecutionStateError(f"invalid stage transition request: {stage!r}")

    def _to_frozen(self, payload: dict[str, Any]) -> str:
        if self.plan.mode == "archive_only":
            _record(payload, "frozen", "git_mutations", False)
            _record(payload, "frozen", "ok", True)
            self._maybe_crash("frozen")
            return "frozen"
        self._verify_frozen_gate_once()
        frozen_stage = payload.get("stages", {}).get("frozen", {})
        if isinstance(frozen_stage, dict) and frozen_stage.get("ok"):
            self._maybe_crash("frozen")
            return "frozen"

        if not self.plan.worktree_targets and self.plan.mode == "finish_and_clean":
            raise ExecutorError("no worktrees supplied for finish_and_clean mode")

        for worktree in self.plan.worktree_targets:
            safety.verify_worktree_candidate(
                self.repo_root,
                worktree=worktree.worktree,
                branch=worktree.branch,
                explicit_family=worktree.explicit_family,
                planned_family=self.plan.family_id,
            )
            _record_resource(payload, "worktree", worktree.id, "actual", evidence={"worktree": str(worktree.worktree)})

        _record(payload, "frozen", "operation_id", self.plan.operation_id)
        _record(payload, "frozen", "family_id", self.plan.family_id)
        _record(payload, "frozen", "ok", True)
        self._maybe_crash("frozen")
        return "frozen"

    def _to_verified(self, payload: dict[str, Any]) -> str:
        if self.plan.mode == "archive_only":
            _record(payload, "verified", "git_mutations", False)
            _record(payload, "verified", "ok", True)
            self._maybe_crash("verified")
            return "verified"
        self._verify_frozen_gate_once()
        if not self.plan.worktree_targets:
            _record(payload, "verified", "ok", True)
            self._maybe_crash("verified")
            return "verified"

        verified = payload.get("stages", {}).get("verified", {})
        if isinstance(verified, dict) and verified.get("ok"):
            self._maybe_crash("verified")
            return "verified"

        for target in self.plan.worktree_targets:
            if not target.worktree.exists():
                raise ExecutorError(f"worktree missing: {target.worktree}")

            safety.assert_no_unknown_branch_mutation(
                self.repo_root,
                target.branch,
                explicit_protected=self.plan.explicit_protected,
            )
            safety.assert_primary_checkout(self.repo_root)
            base_branch = safety.repo_default_branch(self.repo_root)
            if base_branch != target.pr_base:
                raise ExecutorError(
                    f"branch base mismatch for {target.branch}: plan {target.pr_base!r}, repo {base_branch!r}"
                )
            safety.ensure_clean_base(self.repo_root, base_branch)
            safety.verify_worktree_candidate(
                self.repo_root,
                worktree=target.worktree,
                branch=target.branch,
                explicit_family=target.explicit_family,
                planned_family=self.plan.family_id,
            )
            head = safety.worktree_head(self.repo_root, target.worktree)
            if not head:
                raise ExecutorError(f"worktree has no HEAD: {target.worktree}")
            pr = safety.query_pr_by_head(
                self.repo_root,
                branch=target.branch,
                pr_number=target.pr_number,
            )
            safety.assert_pr_is_merged(
                pr,
                expected_branch=target.branch,
                expected_number=target.pr_number,
                expected_base=target.pr_base,
            )
            _record_resource(payload, "worktree", target.id, "actual", evidence={"pr": pr, "head": head})
            _record(payload, f"verified:{target.id}", "base_branch", base_branch)
            _record(payload, f"verified:{target.id}", "pr", pr)

        _record(payload, "verified", "ok", True)
        _record(payload, "verified", "base_branch", safety.repo_default_branch(self.repo_root))
        _record(payload, "verified", "runtime_targets", len(self.plan.runtime_targets))
        self._maybe_crash("verified")
        return "verified"

    def _to_snapshotted(self, payload: dict[str, Any]) -> str:
        if self.plan.mode == "archive_only":
            _record(payload, "snapshotted", "git_mutations", False)
            _record(payload, "snapshotted", "ok", True)
            self._maybe_crash("snapshotted")
            return "snapshotted"
        self._verify_frozen_gate_once()
        snap = payload.get("stages", {}).get("snapshotted", {})
        if isinstance(snap, dict) and snap.get("ok"):
            self._maybe_crash("snapshotted")
            return "snapshotted"

        recorded = snap.get("bundles", {}) if isinstance(snap, dict) else {}
        if not isinstance(recorded, dict):
            recorded = {}

        for target in self.plan.worktree_targets:
            current = recorded.get(target.id)
            if current is not None:
                bundle = _load_bundle(current)
                safety.assert_bundle_matches_receipt(bundle, target.branch)
                safety.verify_bundle(bundle.path, branch=target.branch, repo_root=self.repo_root)
                _record(payload, "snapshotted", "bundles", recorded)
                _record_resource(payload, "worktree", target.id, "actual", evidence=current)
                continue

            bundle = safety.build_bundle(
                self.repo_root,
                branch=target.branch,
                bundle_dir=self.state_file.parent / "snapshots",
            )
            recorded[target.id] = _bundle_path_to_record(bundle)
            _record(payload, "snapshotted", "bundles", recorded)
            _record_resource(payload, "worktree", target.id, "actual", evidence=_bundle_path_to_record(bundle))

        self._maybe_crash("snapshotted")
        _record(payload, "snapshotted", "ok", True)
        return "snapshotted"

    def _to_tasks_archived(self, payload: dict[str, Any]) -> str:
        if self.plan.mode != "archive_only":
            self._verify_frozen_gate_once()
        selected = set(self.plan.selected_task_ids)
        task_by_id = _extract_task_targets(self.plan)
        stage_receipts = {}
        failed = False

        for target_id in selected:
            target = task_by_id[target_id]
            entry = payload.setdefault("resources", {}).setdefault("task", {}).setdefault(target.task_id, {})
            if _status_ok(entry):
                continue

            try:
                before = codex_state.await_task_target(
                    task_id=target.task_id,
                    expected_title=target.title,
                    expected_cwd=target.cwd,
                    expected_host=target.host,
                    expected_archived=target.expected_archived,
                    db_path=target.db_path,
                    timeout_seconds=5.0,
                )
            except Exception as exc:  # includes codex context or conflict
                _record_resource(
                    payload,
                    "task",
                    target.task_id,
                    "failed",
                    reason=(
                        f"task {target.task_id!r} not at archive target; call native task tool and retry: {exc}"
                    ),
                )
                failed = True
                stage_receipts[target.task_id] = {
                    "task_id": target.task_id,
                    "thread_id": target.task_id,
                    "reason": str(exc),
                }
                continue

            payload_task = {
                "thread_id": before.thread_id,
                "title": before.title,
                "cwd": before.cwd,
                "archived": before.archived,
                "archived_at": before.archived_at,
            }
            stage_receipts[target.task_id] = payload_task
            _record_resource(payload, "task", target.task_id, "actual", evidence=payload_task)

        for target in self.plan.task_targets:
            if target.task_id not in selected:
                _record_resource(payload, "task", target.task_id, "skipped")

        if stage_receipts:
            _record(payload, "tasks_archived", "reconcile", stage_receipts)

        if failed:
            raise ExecutorError("task archive incomplete; invoke native task API and retry")

        self._maybe_crash("tasks_archived")
        return "tasks_archived"

    def _to_worktrees_or_complete(self, payload: dict[str, Any]) -> str:
        if self.plan.mode == "archive_only":
            _record(payload, "completed", "mode", "archive_only")
            return "completed"
        return self._to_worktrees_removed(payload)

    @staticmethod
    def _is_bundle_ready_for_target(payload: dict[str, Any], target: WorktreeTarget) -> safety.BundleReceipt | None:
        snap = payload.get("stages", {}).get("snapshotted", {}).get("bundles", {})
        if not isinstance(snap, dict):
            return None
        raw = snap.get(target.id)
        if not isinstance(raw, dict):
            return None
        try:
            return _load_bundle(raw)
        except Exception:
            return None

    def _to_worktrees_removed(self, payload: dict[str, Any]) -> str:
        self._verify_frozen_gate_once()
        recorded = payload.get("stages", {}).get("worktrees_removed", {})
        if not isinstance(recorded, dict):
            recorded = {}

        for target in self.plan.worktree_targets:
            bundle = self._is_bundle_ready_for_target(payload, target)
            if bundle is None:
                raise ExecutorError(f"missing validated bundle for branch {target.branch}")
            safety.assert_bundle_matches_receipt(bundle, branch=target.branch)
            safety.verify_bundle(bundle.path, branch=target.branch, repo_root=self.repo_root)
            if safety.is_worktree_registered(self.repo_root, target.worktree):
                head = safety.worktree_head(self.repo_root, target.worktree)
                if not head:
                    raise ExecutorError(f"worktree has no HEAD immediately before removal: {target.worktree}")
                safety.verify_worktree_candidate(
                    self.repo_root,
                    worktree=target.worktree,
                    branch=target.branch,
                    explicit_family=target.explicit_family,
                    planned_family=self.plan.family_id,
                )
                # This authoritative lookup and all mutable-resource checks are
                # deliberately repeated immediately before the mutation.
                pr = safety.query_pr_by_head(self.repo_root, branch=target.branch, pr_number=target.pr_number)
                safety.assert_pr_is_merged(
                    pr,
                    expected_branch=target.branch,
                    expected_number=target.pr_number,
                    expected_base=target.pr_base,
                    expected_head=head,
                )
                safety.assert_bundle_matches_receipt(bundle, branch=target.branch)
                safety.verify_bundle(bundle.path, branch=target.branch, repo_root=self.repo_root)
                safety.verify_worktree_candidate(
                    self.repo_root,
                    worktree=target.worktree,
                    branch=target.branch,
                    explicit_family=target.explicit_family,
                    planned_family=self.plan.family_id,
                )
                safety.remove_worktree(self.repo_root, target.worktree)
                _record_resource(payload, "worktree", target.id, "actual", evidence={"removed": True})
                recorded[target.id] = {"status": "removed"}
            else:
                _record_resource(payload, "worktree", target.id, "skipped", evidence={"reason": "absent"})
                recorded[target.id] = {"status": "skipped"}

            _record(payload, "worktrees_removed", "results", recorded)

        self._maybe_crash("worktrees_removed")
        return "worktrees_removed"

    def _to_branches_deleted(self, payload: dict[str, Any]) -> str:
        self._verify_frozen_gate_once()
        recorded = payload.get("stages", {}).get("branches_deleted", {}).get("results", {})
        if not isinstance(recorded, dict):
            recorded = {}
        for target in self.plan.worktree_targets:
            bundle = self._is_bundle_ready_for_target(payload, target)
            if bundle is None:
                raise ExecutorError(f"missing validated bundle for branch {target.branch}")
            safety.assert_bundle_matches_receipt(bundle, branch=target.branch)
            safety.verify_bundle(bundle.path, branch=target.branch, repo_root=self.repo_root)
            safety.assert_primary_checkout(self.repo_root)
            base_branch = safety.repo_default_branch(self.repo_root)
            if base_branch != target.pr_base:
                raise ExecutorError(f"base branch drift for {target.branch}: expected {target.pr_base!r}, got {base_branch!r}")
            safety.ensure_clean_base(self.repo_root, base_branch)

            if not safety.local_branch_exists(self.repo_root, target.branch):
                if safety.is_worktree_registered(self.repo_root, target.worktree):
                    raise ExecutorError(f"branch is absent but its worktree remains registered: {target.branch}")
                if safety.remote_branch_present(self.repo_root, target.branch):
                    raise ExecutorError(f"remote branch still present while local branch is absent: {target.branch}")
                bundle_head = safety.bundle_branch_head(
                    bundle.path,
                    branch=target.branch,
                    repo_root=self.repo_root,
                )
                current_pr = safety.query_pr_by_head(
                    self.repo_root,
                    branch=target.branch,
                    pr_number=target.pr_number,
                )
                safety.assert_pr_is_merged(
                    current_pr,
                    expected_branch=target.branch,
                    expected_number=target.pr_number,
                    expected_base=target.pr_base,
                    expected_head=bundle_head,
                )
                prior = recorded.get(target.id, {})
                if isinstance(prior, dict) and prior.get("status") == "deleted":
                    _record_resource(
                        payload,
                        "worktree",
                        target.id,
                        "actual",
                        evidence=prior,
                        reason="persisted deletion receipt reverified on safe resume",
                    )
                    _record(payload, "branches_deleted", "results", recorded)
                    continue
                recorded[target.id] = {"status": "already_absent", "branch": target.branch, "head": bundle_head}
                _record_resource(
                    payload,
                    "worktree",
                    target.id,
                    "skipped",
                    evidence=recorded[target.id],
                    reason="exact local branch was already absent on safe resume",
                )
                _record(payload, "branches_deleted", "results", recorded)
                continue

            local_head = safety.local_branch_head(self.repo_root, target.branch)
            pr = safety.query_pr_by_head(self.repo_root, branch=target.branch, pr_number=target.pr_number)
            safety.assert_pr_is_merged(
                pr,
                expected_branch=target.branch,
                expected_number=target.pr_number,
                expected_base=target.pr_base,
                expected_head=local_head,
            )
            if local_head != pr["head_ref_oid"]:
                raise ExecutorError(
                    f"local branch head changed before delete for {target.branch}: {local_head!r} != {pr['head_ref_oid']!r}"
                )

            safety.assert_branch_deletion_preconditions(
                repo_root=self.repo_root,
                branch=target.branch,
                pr_data=pr,
                bundle=bundle,
                explicit_protected=self.plan.explicit_protected,
                require_remote_gone=True,
                worktree_registered=safety.is_worktree_registered(self.repo_root, target.worktree),
                expected_head=pr["head_ref_oid"],
            )

            # Re-query exact PR and re-check the complete mutation fence at the
            # last possible point; unknown remote state is a blocker.
            current_head = safety.local_branch_head(self.repo_root, target.branch)
            current_pr = safety.query_pr_by_head(self.repo_root, branch=target.branch, pr_number=target.pr_number)
            if safety.worktree_index_locked(self.repo_root):
                raise ExecutorError("primary checkout index.lock blocks branch deletion")
            safety.assert_pr_is_merged(
                current_pr,
                expected_branch=target.branch,
                expected_number=target.pr_number,
                expected_base=target.pr_base,
                expected_head=current_head,
            )
            safety.assert_branch_deletion_preconditions(
                repo_root=self.repo_root,
                branch=target.branch,
                pr_data=current_pr,
                bundle=bundle,
                explicit_protected=self.plan.explicit_protected,
                require_remote_gone=True,
                worktree_registered=safety.is_worktree_registered(self.repo_root, target.worktree),
                expected_head=current_head,
            )
            safety.delete_branch(self.repo_root, branch=target.branch)
            if safety.local_branch_exists(self.repo_root, target.branch):
                raise ExecutorError(f"branch still present after delete attempt: {target.branch}")
            if safety.remote_branch_present(self.repo_root, target.branch):
                raise ExecutorError(f"remote branch still present after delete: {target.branch}")

            recorded[target.id] = {"status": "deleted", "branch": target.branch, "head": current_head}
            _record(payload, "branches_deleted", "results", recorded)

        self._maybe_crash("branches_deleted")
        return "branches_deleted"

    def _to_runtime_retired(self, payload: dict[str, Any]) -> str:
        if not self.plan.runtime_targets:
            _record(payload, "runtime_retired", "status", "no_op")
            return "runtime_retired"

        blocked = False
        for target in self.plan.runtime_targets:
            if not target.eligible or not (target.proof and target.proof.strip()):
                _record_resource(
                    payload,
                    "runtime",
                    target.id,
                    "failed",
                    reason="runtime retirement blocked: explicit eligibility and proof required; evidence preserved",
                )
                blocked = True
                continue
            _record_resource(
                payload,
                "runtime",
                target.id,
                "skipped",
                evidence={"retired": False, "preserved": True, "proof": target.proof},
                reason="native runtime retirement is unavailable; evidence preserved and retirement deferred",
            )

        if blocked:
            raise ExecutorError("runtime retirement blocked: explicit eligibility and proof required")
        _record(payload, "runtime_retired", "proof_verified", True)
        _record(payload, "runtime_retired", "mutation", "deferred_to_native")
        self._maybe_crash("runtime_retired")
        return "runtime_retired"

    def _to_completed(self, payload: dict[str, Any]) -> str:
        _record(payload, "completed", "ok", True)
        _record(payload, "completed", "mode", self.plan.mode)
        return "completed"

    def restore_archive(self) -> dict[str, Any]:
        """Reject mutation requests: the native task skill owns archive and restore."""
        raise ExecutorError("executor observes Codex DB state only; invoke the native task skill to restore")


def _update_state(path: Path, payload: dict[str, Any], *, next_state: str) -> dict[str, Any]:
    payload["state"] = next_state
    payload["resume_stage"] = None
    payload["blocked"] = None
    history = payload.get("history")
    if not isinstance(history, list):
        history = []
        payload["history"] = history
    if not history or history[-1] != next_state:
        history.append(next_state)
    return persist_state(path, payload)
