"""Durable, fail-closed task-family planning primitives.

This package deliberately plans and records lifecycle operations; executors for
application or Git mutations live in separate lanes.
"""

from .graph import FamilyGraph, discover_task_family, rename_mapping
from .model import (
    ArchiveSelection,
    Blocker,
    LifecycleState,
    OperationKind,
    RelationType,
    TaskFamilyManifest,
    TaskNode,
    TaskRelation,
)
from .planner import TaskFamilyPlan, build_plan
from .storage import TaskFamilyStorage

__all__ = [
    "ArchiveSelection",
    "Blocker",
    "FamilyGraph",
    "LifecycleState",
    "OperationKind",
    "RelationType",
    "TaskFamilyManifest",
    "TaskFamilyPlan",
    "TaskFamilyStorage",
    "TaskNode",
    "TaskRelation",
    "build_plan",
    "discover_task_family",
    "rename_mapping",
]
