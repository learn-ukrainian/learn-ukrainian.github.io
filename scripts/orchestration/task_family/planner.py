"""Deterministic, fail-closed lifecycle planning for a task-family graph."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any

from .graph import FamilyGraph, TitleRename, rename_mapping
from .model import (
    PARENT_LIKE_RELATIONS,
    SCHEMA_VERSION,
    STATE_SEQUENCE,
    ArchiveSelection,
    Blocker,
    LifecycleState,
    OperationKind,
    PlanStage,
    ResourceDecision,
)

STAGE_DESCRIPTIONS = {
    LifecycleState.PLANNED: "Immutable plan recorded; no mutation is authorized.",
    LifecycleState.FROZEN: "Operation lock acquired and current resources re-discovered.",
    LifecycleState.VERIFIED: "Selection, pins, and resource preconditions verified.",
    LifecycleState.SNAPSHOTTED: "Required recoverability snapshot verified before cleanup.",
    LifecycleState.TASKS_ARCHIVED: "Selected tasks reconciled at archive target.",
    LifecycleState.WORKTREES_REMOVED: "Selected, exclusive worktrees reconciled as absent.",
    LifecycleState.BRANCHES_DELETED: "Selected, proof-gated branches reconciled as absent.",
    LifecycleState.RUNTIME_RETIRED: "Family runtime record retired without purge.",
    LifecycleState.COMPLETED: "Operation reached its requested terminal target.",
    LifecycleState.BLOCKED: "A fail-closed blocker prevented further progression.",
}


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TaskFamilyPlan:
    family_id: str
    operation_id: str
    operation: OperationKind
    selected_task_ids: tuple[str, ...]
    excluded_task_ids: tuple[str, ...]
    base_title: str
    selections: tuple[ArchiveSelection, ...]
    rename_map: tuple[TitleRename, ...]
    resource_decisions: tuple[ResourceDecision, ...]
    stages: tuple[PlanStage, ...]
    blockers: tuple[Blocker, ...]
    state: LifecycleState = LifecycleState.PLANNED
    schema_version: int = SCHEMA_VERSION
    digest: str = ""

    @property
    def is_actionable(self) -> bool:
        return not self.blockers and self.state is not LifecycleState.BLOCKED

    @property
    def is_completed_cleanup_noop(self) -> bool:
        """A completed operation is immutable and never schedules a second cleanup."""
        return self.state is self.terminal_state

    @property
    def terminal_state(self) -> LifecycleState:
        return LifecycleState.TASKS_ARCHIVED if self.operation is OperationKind.ARCHIVE_ONLY else LifecycleState.COMPLETED

    def immutable_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "family_id": self.family_id,
            "operation_id": self.operation_id,
            "operation": self.operation.value,
            "selected_task_ids": list(self.selected_task_ids),
            "excluded_task_ids": list(self.excluded_task_ids),
            "base_title": self.base_title,
            "selections": [
                {
                    "task_id": item.task_id,
                    "actor": item.actor,
                    "selected_at": item.selected_at,
                    "selection_source": item.selection_source,
                    "pin_state_unknown_confirmed": item.pin_state_unknown_confirmed,
                }
                for item in self.selections
            ],
            "rename_map": [
                {"task_id": item.task_id, "old_title": item.old_title, "new_title": item.new_title, "roles": list(item.roles)}
                for item in self.rename_map
            ],
            "resource_decisions": [item.to_dict() for item in self.resource_decisions],
            "stages": [item.to_dict() for item in self.stages],
            "blockers": [item.to_dict() for item in self.blockers],
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.immutable_payload()
        payload["state"] = self.state.value
        payload["digest"] = self.digest
        return payload

    def with_state(self, state: LifecycleState) -> TaskFamilyPlan:
        if self.state is self.terminal_state:
            if state is self.state:
                return self
            raise ValueError(f"operation {self.operation.value} reached terminal state {self.state.value}")
        if state is LifecycleState.BLOCKED:
            return replace(self, state=state)
        state_sequence = tuple(stage.state for stage in self.stages)
        current_index = state_sequence.index(self.state)
        requested_index = state_sequence.index(state)
        if requested_index != current_index + 1:
            raise ValueError(f"invalid lifecycle transition: {self.state.value} -> {state.value}")
        if self.blockers:
            return replace(self, state=LifecycleState.BLOCKED)
        return replace(self, state=state)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TaskFamilyPlan:
        if not isinstance(payload, dict):
            raise ValueError("task-family plan must be an object")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"unsupported task-family plan schema_version: {payload.get('schema_version')!r}")
        try:
            operation = OperationKind(payload.get("operation"))
            state = LifecycleState(payload.get("state"))
        except (TypeError, ValueError) as exc:
            raise ValueError("task-family plan contains an unknown operation or lifecycle state") from exc

        def string_list(key: str) -> tuple[str, ...]:
            value = payload.get(key, [])
            if not isinstance(value, list):
                raise ValueError(f"task-family plan {key} must be a list")
            return tuple(item for item in value if isinstance(item, str))

        def record_list(key: str) -> list[dict[str, Any]]:
            value = payload.get(key, [])
            if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
                raise ValueError(f"task-family plan {key} must be a list of objects")
            return value

        def title_rename(item: dict[str, Any]) -> TitleRename:
            roles = item.get("roles")
            if not all(isinstance(item.get(key), str) for key in ("task_id", "old_title", "new_title")) or not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
                raise ValueError("task-family plan rename_map must contain title rename objects")
            return TitleRename(item["task_id"], item["old_title"], item["new_title"], tuple(roles))

        if len(string_list("selected_task_ids")) != len(payload.get("selected_task_ids", [])):
            raise ValueError("task-family plan selected_task_ids must be strings")
        plan = cls(
            family_id=payload.get("family_id") if isinstance(payload.get("family_id"), str) else "",
            operation_id=payload.get("operation_id") if isinstance(payload.get("operation_id"), str) else "",
            operation=operation,
            selected_task_ids=string_list("selected_task_ids"),
            excluded_task_ids=string_list("excluded_task_ids"),
            base_title=payload.get("base_title") if isinstance(payload.get("base_title"), str) else "",
            selections=tuple(ArchiveSelection.from_dict(item) for item in record_list("selections")),
            rename_map=tuple(title_rename(item) for item in record_list("rename_map")),
            resource_decisions=tuple(ResourceDecision.from_dict(item) for item in record_list("resource_decisions")),
            stages=tuple(PlanStage.from_dict(item) for item in record_list("stages")),
            blockers=tuple(Blocker.from_dict(item) for item in record_list("blockers")),
            state=state,
            schema_version=payload["schema_version"],
            digest=payload.get("digest") if isinstance(payload.get("digest"), str) else "",
        )
        if not plan.family_id or not plan.operation_id or not plan.base_title or not plan.digest:
            raise ValueError("task-family plan requires family_id, operation_id, base_title, and digest")
        if sha256_digest(plan.immutable_payload()) != plan.digest:
            raise ValueError("immutable plan digest does not match persisted plan")
        if plan.state is not LifecycleState.BLOCKED and plan.state not in {stage.state for stage in plan.stages}:
            raise ValueError("task-family plan state is absent from operation stages")
        return plan


def _shared_resource_blockers(graph: FamilyGraph, selected: set[str]) -> list[Blocker]:
    blockers: list[Blocker] = []
    nodes = graph.nodes_by_id
    resource_fields = (("worktree", "worktree"), ("branch", "branch"), ("pr_id", "PR"))
    for field, label in resource_fields:
        owners: dict[str, set[str]] = {}
        for node in nodes.values():
            value = getattr(node, field)
            if value:
                owners.setdefault(value, set()).add(node.task_id)
        for value, task_ids in owners.items():
            if task_ids & selected and task_ids - selected:
                blockers.append(
                    Blocker(
                        "unselected_shared_resource",
                        f"Unselected task(s) share {label} {value!r} with selected task(s).",
                        tuple(sorted(task_ids)),
                        "Select every affected exact ID or separate the shared resource before retrying.",
                    )
                )
    adjacency: dict[str, set[str]] = {task_id: set() for task_id in nodes}
    for relation in graph.family_relations:
        if relation.relation_type in PARENT_LIKE_RELATIONS:
            adjacency[relation.source_id].add(relation.target_id)
            adjacency[relation.target_id].add(relation.source_id)
    for task_id in selected:
        stack = list(adjacency[task_id])
        seen = {task_id}
        while stack:
            candidate = stack.pop()
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate not in selected:
                blockers.append(
                    Blocker(
                        "unselected_lineage_endpoint",
                        f"Unselected task {candidate!r} is a predecessor/successor lineage endpoint of selected task {task_id!r}.",
                        tuple(sorted((task_id, candidate))),
                        "Explicitly select the lineage endpoint or use archive-only after separating the family.",
                    )
                )
            stack.extend(adjacency[candidate] - seen)
    return blockers


def _resource_decisions(graph: FamilyGraph, selected: tuple[str, ...]) -> tuple[ResourceDecision, ...]:
    nodes = graph.nodes_by_id
    decisions: list[ResourceDecision] = []
    for task_id in selected:
        node = nodes[task_id]
        for resource_type, value in (("worktree", node.worktree), ("branch", node.branch), ("pr", node.pr_id)):
            if value:
                decisions.append(ResourceDecision(resource_type, value, (task_id,), "preserve_until_verified", "Planning lane performs no mutation."))
    return tuple(sorted(decisions, key=lambda item: (item.resource_type, item.resource_id, item.selected_task_ids)))


def _stages(operation: OperationKind) -> tuple[PlanStage, ...]:
    states = (
        (LifecycleState.PLANNED, LifecycleState.FROZEN, LifecycleState.VERIFIED, LifecycleState.TASKS_ARCHIVED)
        if operation is OperationKind.ARCHIVE_ONLY
        else STATE_SEQUENCE
    )
    return tuple(PlanStage(state, True, STAGE_DESCRIPTIONS[state]) for state in states)


def build_plan(
    graph: FamilyGraph,
    *,
    operation_id: str,
    operation: OperationKind,
    selections: tuple[ArchiveSelection, ...],
    base_title: str,
) -> TaskFamilyPlan:
    """Build a deterministic plan, recording blockers instead of guessing intent."""
    blockers = list(graph.blockers)
    if not base_title.strip():
        blockers.append(Blocker("missing_base_title", "A caller-supplied base title is required; titles are never identity inputs."))
    node_ids = set(graph.nodes_by_id)
    selected_ids = tuple(sorted(selection.task_id for selection in selections))
    if not selections:
        blockers.append(Blocker("no_explicit_selection", "No tasks were selected; archive selection is never inferred.", remediation="Provide one explicit selection per exact task ID."))
    if len(selected_ids) != len(set(selected_ids)):
        blockers.append(Blocker("duplicate_selection", "An exact task ID was selected more than once.", selected_ids))
    for selection in selections:
        if selection.task_id not in node_ids:
            blockers.append(Blocker("unknown_selected_task", f"Selected task ID {selection.task_id!r} is not in the manifest.", (selection.task_id,)))
        if not selection.pin_state_unknown_confirmed:
            blockers.append(Blocker("pin_state_unconfirmed", f"Selected task {selection.task_id!r} has unknown pin state without affirmative confirmation.", (selection.task_id,), "Confirm pin_state_unknown for this exact task ID."))
    selected_set = set(selected_ids) & node_ids
    blockers.extend(_shared_resource_blockers(graph, selected_set))
    plan = TaskFamilyPlan(
        family_id=graph.manifest.family_id,
        operation_id=operation_id,
        operation=operation,
        selected_task_ids=selected_ids,
        excluded_task_ids=graph.excluded_task_ids,
        base_title=base_title,
        selections=tuple(sorted(selections, key=lambda item: item.task_id)),
        rename_map=rename_mapping(graph, base_title) if base_title.strip() else (),
        resource_decisions=_resource_decisions(graph, tuple(sorted(selected_set))),
        stages=_stages(operation),
        blockers=tuple(sorted(blockers, key=lambda item: (item.code, item.task_ids, item.message))),
    )
    return replace(plan, digest=sha256_digest(plan.immutable_payload()))
