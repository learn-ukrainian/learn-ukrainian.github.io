"""Versioned data model for task-family lifecycle planning.

Task IDs are the sole identity keys.  Titles are retained only for rendering.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar

SCHEMA_VERSION = 1
def _object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object")
    return value


def _list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{context} must be a list")
    return value


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{context} must be a string")
    return value


def _schema_version(payload: dict[str, Any], context: str) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported {context} schema_version: {payload.get('schema_version')!r}")


class SchemaModel:
    """Marker for immutable JSON records read by the future CLI."""

    schema_version: ClassVar[int]


class RelationType(StrEnum):
    ROOT = "root"
    SUBAGENT_OF = "subagent_of"
    REVIEWER_FOR = "reviewer_for"
    REPLACEMENT_OF = "replacement_of"
    HANDOFF_OF = "handoff_of"
    ROLLOVER_GENERATION_OF = "rollover_generation_of"
    ISSUE_OR_PR_MEMBER = "issue_or_pr_member"


class OperationKind(StrEnum):
    ARCHIVE_ONLY = "archive_only"
    FINISH_AND_CLEAN = "finish_and_clean"


class LifecycleState(StrEnum):
    PLANNED = "planned"
    FROZEN = "frozen"
    VERIFIED = "verified"
    SNAPSHOTTED = "snapshotted"
    TASKS_ARCHIVED = "tasks_archived"
    WORKTREES_REMOVED = "worktrees_removed"
    BRANCHES_DELETED = "branches_deleted"
    RUNTIME_RETIRED = "runtime_retired"
    COMPLETED = "completed"
    BLOCKED = "blocked"


STATE_SEQUENCE = (
    LifecycleState.PLANNED,
    LifecycleState.FROZEN,
    LifecycleState.VERIFIED,
    LifecycleState.SNAPSHOTTED,
    LifecycleState.TASKS_ARCHIVED,
    LifecycleState.WORKTREES_REMOVED,
    LifecycleState.BRANCHES_DELETED,
    LifecycleState.RUNTIME_RETIRED,
    LifecycleState.COMPLETED,
)
PARENT_LIKE_RELATIONS = frozenset(
    {
        RelationType.SUBAGENT_OF,
        RelationType.REVIEWER_FOR,
        RelationType.REPLACEMENT_OF,
        RelationType.HANDOFF_OF,
        RelationType.ROLLOVER_GENERATION_OF,
    }
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class TaskNode(SchemaModel):
    task_id: str
    title: str
    project_root: str
    worktree: str | None = None
    branch: str | None = None
    pr_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must be non-empty")
        if not self.project_root.strip():
            raise ValueError(f"task {self.task_id}: project_root must be non-empty")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TaskNode:
        data = _object(payload, "task node")
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in metadata.items()):
            raise ValueError("task node metadata must be a string map")
        def optional(key: str) -> str | None:
            return None if data.get(key) is None else _string(data[key], f"task node {key}")

        return cls(_string(data.get("task_id"), "task node task_id"), _string(data.get("title"), "task node title"), _string(data.get("project_root"), "task node project_root"), optional("worktree"), optional("branch"), optional("pr_id"), metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TaskRelation(SchemaModel):
    source_id: str
    target_id: str
    relation_type: RelationType
    evidence: str
    family_defining: bool = True

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.target_id.strip():
            raise ValueError("relation endpoints must be non-empty exact task IDs")
        if not self.evidence.strip():
            raise ValueError("relation evidence must be non-empty")
        if not self.family_defining and self.relation_type is not RelationType.ISSUE_OR_PR_MEMBER:
            raise ValueError("only issue_or_pr_member relations may be display-only")

    @property
    def is_display_only(self) -> bool:
        return self.relation_type is RelationType.ISSUE_OR_PR_MEMBER and not self.family_defining

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TaskRelation:
        data = _object(payload, "task relation")
        try:
            relation_type = RelationType(_string(data.get("relation_type"), "task relation relation_type"))
        except ValueError as exc:
            raise ValueError(f"unknown task relation type: {data.get('relation_type')!r}") from exc
        family_defining = data.get("family_defining", True)
        if not isinstance(family_defining, bool):
            raise ValueError("task relation family_defining must be boolean")
        return cls(_string(data.get("source_id"), "task relation source_id"), _string(data.get("target_id"), "task relation target_id"), relation_type, _string(data.get("evidence"), "task relation evidence"), family_defining)

    def to_dict(self) -> dict[str, Any]:
        return {"source_id": self.source_id, "target_id": self.target_id, "relation_type": self.relation_type.value, "evidence": self.evidence, "family_defining": self.family_defining}


@dataclass(frozen=True, slots=True)
class TaskFamilyManifest(SchemaModel):
    family_id: str
    seed_task_id: str
    nodes: tuple[TaskNode, ...]
    relations: tuple[TaskRelation, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported manifest schema_version: {self.schema_version}")
        if not self.family_id.strip():
            raise ValueError("family_id must be non-empty")
        if not self.seed_task_id.strip():
            raise ValueError("seed_task_id must be a non-empty exact task ID")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "family_id": self.family_id,
            "seed_task_id": self.seed_task_id,
            "nodes": [node.to_dict() for node in self.nodes],
            "relations": [relation.to_dict() for relation in self.relations],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TaskFamilyManifest:
        data = _object(payload, "task-family manifest")
        _schema_version(data, "task-family manifest")
        return cls(
            _string(data.get("family_id"), "task-family manifest family_id"),
            _string(data.get("seed_task_id"), "task-family manifest seed_task_id"),
            tuple(TaskNode.from_dict(_object(item, "task-family manifest node")) for item in _list(data.get("nodes"), "task-family manifest nodes")),
            tuple(TaskRelation.from_dict(_object(item, "task-family manifest relation")) for item in _list(data.get("relations"), "task-family manifest relations")),
            data["schema_version"],
        )


@dataclass(frozen=True, slots=True)
class ArchiveSelection(SchemaModel):
    task_id: str
    actor: str
    selected_at: str = field(default_factory=utc_now)
    selection_source: str = "explicit"
    pin_state_unknown_confirmed: bool = False

    def __post_init__(self) -> None:
        if self.selection_source != "explicit":
            raise ValueError("archive selection_source must be explicit")
        if not self.actor.strip():
            raise ValueError("archive selection actor must be non-empty")
        if not self.selected_at.strip():
            raise ValueError("archive selection selected_at must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ArchiveSelection:
        data = _object(payload, "archive selection")
        confirmed = data.get("pin_state_unknown_confirmed", False)
        if not isinstance(confirmed, bool):
            raise ValueError("archive selection pin_state_unknown_confirmed must be boolean")
        return cls(_string(data.get("task_id"), "archive selection task_id"), _string(data.get("actor"), "archive selection actor"), _string(data.get("selected_at"), "archive selection selected_at"), _string(data.get("selection_source", "explicit"), "archive selection selection_source"), confirmed)


@dataclass(frozen=True, slots=True)
class Blocker(SchemaModel):
    code: str
    message: str
    task_ids: tuple[str, ...] = ()
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Blocker:
        data = _object(payload, "blocker")
        return cls(_string(data.get("code"), "blocker code"), _string(data.get("message"), "blocker message"), tuple(_string(item, "blocker task_id") for item in _list(data.get("task_ids", []), "blocker task_ids")), _string(data.get("remediation", ""), "blocker remediation"))


@dataclass(frozen=True, slots=True)
class ResourceDecision(SchemaModel):
    resource_type: str
    resource_id: str
    selected_task_ids: tuple[str, ...]
    decision: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResourceDecision:
        data = _object(payload, "resource decision")
        return cls(_string(data.get("resource_type"), "resource decision resource_type"), _string(data.get("resource_id"), "resource decision resource_id"), tuple(_string(item, "resource decision selected_task_id") for item in _list(data.get("selected_task_ids"), "resource decision selected_task_ids")), _string(data.get("decision"), "resource decision decision"), _string(data.get("reason"), "resource decision reason"))


@dataclass(frozen=True, slots=True)
class PlanStage(SchemaModel):
    state: LifecycleState
    required: bool
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state.value, "required": self.required, "description": self.description}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PlanStage:
        data = _object(payload, "plan stage")
        try:
            state = LifecycleState(_string(data.get("state"), "plan stage state"))
        except ValueError as exc:
            raise ValueError(f"unknown lifecycle state: {data.get('state')!r}") from exc
        required = data.get("required")
        if not isinstance(required, bool):
            raise ValueError("plan stage required must be boolean")
        return cls(state, required, _string(data.get("description"), "plan stage description"))


@dataclass(frozen=True, slots=True)
class LifecycleEvent(SchemaModel):
    event_id: str
    occurred_at: str
    state: LifecycleState
    kind: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"event_id": self.event_id, "occurred_at": self.occurred_at, "state": self.state.value, "kind": self.kind, "details": self.details}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> LifecycleEvent:
        data = _object(payload, "lifecycle event")
        try:
            state = LifecycleState(_string(data.get("state"), "lifecycle event state"))
        except ValueError as exc:
            raise ValueError(f"unknown lifecycle state: {data.get('state')!r}") from exc
        details = data.get("details", {})
        if not isinstance(details, dict):
            raise ValueError("lifecycle event details must be an object")
        return cls(_string(data.get("event_id"), "lifecycle event event_id"), _string(data.get("occurred_at"), "lifecycle event occurred_at"), state, _string(data.get("kind"), "lifecycle event kind"), details)


@dataclass(frozen=True, slots=True)
class ReceiptAction(SchemaModel):
    resource_type: str
    resource_id: str
    task_ids: tuple[str, ...]
    action: str
    reason: str = ""
    error: str = ""
    recovery: str = ""

    def __post_init__(self) -> None:
        if not self.resource_type.strip() or not self.resource_id.strip() or not self.action.strip():
            raise ValueError("receipt actions require resource_type, resource_id, and action")

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "task_ids": list(self.task_ids),
            "action": self.action,
            "reason": self.reason,
            "error": self.error,
            "recovery": self.recovery,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ReceiptAction:
        data = _object(payload, "receipt action")
        return cls(
            _string(data.get("resource_type"), "receipt action resource_type"),
            _string(data.get("resource_id"), "receipt action resource_id"),
            tuple(_string(item, "receipt action task_id") for item in _list(data.get("task_ids", []), "receipt action task_ids")),
            _string(data.get("action"), "receipt action action"),
            _string(data.get("reason", ""), "receipt action reason"),
            _string(data.get("error", ""), "receipt action error"),
            _string(data.get("recovery", ""), "receipt action recovery"),
        )


@dataclass(frozen=True, slots=True)
class OperationReceipt(SchemaModel):
    operation_id: str
    family_id: str
    plan_digest: str
    final_state: LifecycleState
    planned: tuple[ReceiptAction, ...] = ()
    actual: tuple[ReceiptAction, ...] = ()
    skipped: tuple[ReceiptAction, ...] = ()
    failures: tuple[ReceiptAction, ...] = ()
    restoration: tuple[ReceiptAction, ...] = ()
    final_resources: tuple[ReceiptAction, ...] = ()
    events: tuple[LifecycleEvent, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation_id": self.operation_id,
            "family_id": self.family_id,
            "plan_digest": self.plan_digest,
            "final_state": self.final_state.value,
            "planned": [item.to_dict() for item in self.planned],
            "actual": [item.to_dict() for item in self.actual],
            "skipped": [item.to_dict() for item in self.skipped],
            "failures": [item.to_dict() for item in self.failures],
            "restoration": [item.to_dict() for item in self.restoration],
            "final_resources": [item.to_dict() for item in self.final_resources],
            "events": [event.to_dict() for event in self.events],
        }

    def render_human(self) -> str:
        lines = [
            f"Task-family operation {self.operation_id}",
            f"Family: {self.family_id}",
            f"Plan digest: {self.plan_digest}",
            f"Final state: {self.final_state.value}",
        ]
        for label, values in (
            ("Planned", self.planned),
            ("Actual", self.actual),
            ("Skipped", self.skipped),
            ("Failures", self.failures),
            ("Restoration", self.restoration),
            ("Final resources", self.final_resources),
        ):
            rendered = (f"{item.resource_type}:{item.resource_id} {item.action}" + (f" ({item.reason})" if item.reason else "") for item in values)
            lines.append(f"{label}: " + ("; ".join(rendered) if values else "none"))
        return "\n".join(lines) + "\n"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> OperationReceipt:
        data = _object(payload, "operation receipt")
        _schema_version(data, "operation receipt")
        try:
            final_state = LifecycleState(_string(data.get("final_state"), "operation receipt final_state"))
        except ValueError as exc:
            raise ValueError(f"unknown lifecycle state: {data.get('final_state')!r}") from exc
        def actions(key: str) -> tuple[ReceiptAction, ...]:
            return tuple(
                ReceiptAction.from_dict(_object(item, f"operation receipt {key} item"))
                for item in _list(data.get(key, []), f"operation receipt {key}")
            )

        return cls(_string(data.get("operation_id"), "operation receipt operation_id"), _string(data.get("family_id"), "operation receipt family_id"), _string(data.get("plan_digest"), "operation receipt plan_digest"), final_state, actions("planned"), actions("actual"), actions("skipped"), actions("failures"), actions("restoration"), actions("final_resources"), tuple(LifecycleEvent.from_dict(_object(item, "operation receipt event")) for item in _list(data.get("events", []), "operation receipt events")), data["schema_version"])
