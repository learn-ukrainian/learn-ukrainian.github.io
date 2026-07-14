"""Versioned data model for task-family lifecycle planning.

Task IDs are the sole identity keys.  Titles are retained only for rendering.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

SCHEMA_VERSION = 1


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
class TaskNode:
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


@dataclass(frozen=True, slots=True)
class TaskRelation:
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

    @property
    def is_display_only(self) -> bool:
        return self.relation_type is RelationType.ISSUE_OR_PR_MEMBER and not self.family_defining


@dataclass(frozen=True, slots=True)
class TaskFamilyManifest:
    family_id: str
    nodes: tuple[TaskNode, ...]
    relations: tuple[TaskRelation, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported manifest schema_version: {self.schema_version}")
        if not self.family_id.strip():
            raise ValueError("family_id must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ArchiveSelection:
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


@dataclass(frozen=True, slots=True)
class Blocker:
    code: str
    message: str
    task_ids: tuple[str, ...] = ()
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResourceDecision:
    resource_type: str
    resource_id: str
    selected_task_ids: tuple[str, ...]
    decision: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PlanStage:
    state: LifecycleState
    required: bool
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state.value, "required": self.required, "description": self.description}


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    event_id: str
    occurred_at: str
    state: LifecycleState
    kind: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"event_id": self.event_id, "occurred_at": self.occurred_at, "state": self.state.value, "kind": self.kind, "details": self.details}


@dataclass(frozen=True, slots=True)
class OperationReceipt:
    operation_id: str
    family_id: str
    plan_digest: str
    final_state: LifecycleState
    planned: tuple[str, ...] = ()
    actual: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()
    restoration: tuple[str, ...] = ()
    events: tuple[LifecycleEvent, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation_id": self.operation_id,
            "family_id": self.family_id,
            "plan_digest": self.plan_digest,
            "final_state": self.final_state.value,
            "planned": list(self.planned),
            "actual": list(self.actual),
            "skipped": list(self.skipped),
            "failures": list(self.failures),
            "restoration": list(self.restoration),
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
        ):
            lines.append(f"{label}: " + ("; ".join(values) if values else "none"))
        return "\n".join(lines) + "\n"
