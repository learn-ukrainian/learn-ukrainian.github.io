from __future__ import annotations

import json

import pytest

from scripts.orchestration.task_family.graph import discover_task_family, rename_mapping
from scripts.orchestration.task_family.model import (
    ArchiveSelection,
    LifecycleState,
    OperationKind,
    RelationType,
    TaskFamilyManifest,
    TaskNode,
    TaskRelation,
)
from scripts.orchestration.task_family.planner import build_plan
from scripts.orchestration.task_family.storage import TaskFamilyStorage, atomic_write_json


def _node(task_id: str, title: str, **resources: str) -> TaskNode:
    return TaskNode(task_id, title, "/repo", **resources)


def _manifest(*, relations: tuple[TaskRelation, ...], nodes: tuple[TaskNode, ...] | None = None) -> TaskFamilyManifest:
    return TaskFamilyManifest(
        "family-5140",
        nodes
        or (
            _node("root", "Planner", worktree="/repo/root", branch="codex/root", pr_id="1"),
            _node("worker", "Implementation", worktree="/repo/worker", branch="codex/worker", pr_id="2"),
            _node("review", "Review"),
            _node("handoff", "Continuation"),
            _node("replacement", "Continuation"),
        ),
        relations,
    )


def _graph():
    return discover_task_family(
        _manifest(
            relations=(
                TaskRelation("worker", "root", RelationType.SUBAGENT_OF, "spawn edge"),
                TaskRelation("review", "worker", RelationType.REVIEWER_FOR, "review assignment"),
                TaskRelation("handoff", "worker", RelationType.HANDOFF_OF, "handoff record"),
                TaskRelation("replacement", "handoff", RelationType.REPLACEMENT_OF, "replacement record"),
                TaskRelation("replacement", "handoff", RelationType.ROLLOVER_GENERATION_OF, "generation record"),
            )
        )
    )


def test_discovers_synthetic_root_worker_reviewer_handoff_and_replacement() -> None:
    graph = _graph()

    assert graph.is_valid
    assert graph.roots == ("root",)
    assert graph.roles_by_task["root"] == ("Lead",)
    assert graph.roles_by_task["worker"] == ("Worker",)
    assert graph.roles_by_task["review"] == ("Reviewer",)
    assert graph.roles_by_task["handoff"] == ("Handoff",)
    assert graph.roles_by_task["replacement"] == ("Replacement", "Generation 1")


def test_similar_titles_do_not_establish_membership() -> None:
    manifest = _manifest(
        nodes=(_node("a", "Same title"), _node("b", "Same title")),
        relations=(),
    )

    graph = discover_task_family(manifest)

    assert not graph.is_valid
    assert any(blocker.code == "multiple_or_missing_roots" for blocker in graph.blockers)


def test_rename_mapping_preserves_multiple_roles_in_stable_order() -> None:
    mapping = {item.task_id: item for item in rename_mapping(_graph())}

    assert mapping["replacement"].new_title == "Continuation [Replacement, Generation 1]"
    assert mapping["replacement"].old_title == "Continuation"


def test_conflicting_membership_fails_closed() -> None:
    graph = discover_task_family(
        _manifest(
            nodes=(_node("root", "Root"), _node("other", "Other"), _node("worker", "Worker")),
            relations=(
                TaskRelation("worker", "root", RelationType.SUBAGENT_OF, "first"),
                TaskRelation("worker", "other", RelationType.SUBAGENT_OF, "conflict"),
            ),
        )
    )

    assert any(blocker.code == "conflicting_membership" for blocker in graph.blockers)


def test_selection_requires_explicit_source_and_pin_confirmation() -> None:
    graph = _graph()
    selection = ArchiveSelection("root", "operator", selected_at="2026-07-14T00:00:00Z")

    plan = build_plan(graph, operation_id="op-1", operation=OperationKind.ARCHIVE_ONLY, selections=(selection,))

    assert any(blocker.code == "pin_state_unconfirmed" for blocker in plan.blockers)
    assert plan.selections[0].selection_source == "explicit"
    with pytest.raises(ValueError, match="selection_source"):
        ArchiveSelection("root", "operator", selection_source="inferred", pin_state_unknown_confirmed=True)


def test_unselected_shared_resource_blocks_planning() -> None:
    manifest = _manifest(
        nodes=(_node("root", "Root", branch="codex/shared"), _node("worker", "Worker", branch="codex/shared")),
        relations=(TaskRelation("worker", "root", RelationType.SUBAGENT_OF, "spawn"),),
    )
    plan = build_plan(
        discover_task_family(manifest),
        operation_id="op-2",
        operation=OperationKind.ARCHIVE_ONLY,
        selections=(ArchiveSelection("root", "operator", selected_at="2026-07-14T00:00:00Z", pin_state_unknown_confirmed=True),),
    )

    assert any(blocker.code == "unselected_shared_resource" for blocker in plan.blockers)
    assert any(blocker.code == "unselected_lineage_endpoint" for blocker in plan.blockers)


def test_plan_digest_is_deterministic() -> None:
    selection = ArchiveSelection("root", "operator", selected_at="2026-07-14T00:00:00Z", pin_state_unknown_confirmed=True)

    first = build_plan(_graph(), operation_id="op-digest", operation=OperationKind.ARCHIVE_ONLY, selections=(selection,))
    second = build_plan(_graph(), operation_id="op-digest", operation=OperationKind.ARCHIVE_ONLY, selections=(selection,))

    assert first.digest == second.digest
    assert first.digest == "0d96804ef4062004a5d4a414285732665c0e5e9c4720b887e962bff523b2456c"


def test_atomic_persistence_and_immutable_digest(tmp_path) -> None:
    path = tmp_path / "record.json"
    atomic_write_json(path, {"b": 2, "a": 1})
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1, "b": 2}

    selection = ArchiveSelection("root", "operator", selected_at="2026-07-14T00:00:00Z", pin_state_unknown_confirmed=True)
    plan = build_plan(_graph(), operation_id="op-store", operation=OperationKind.ARCHIVE_ONLY, selections=(selection,))
    storage = TaskFamilyStorage(tmp_path, plan.family_id, plan.operation_id)
    storage.write_plan(plan)
    assert storage.assert_plan_digest(plan.digest)["digest"] == plan.digest
    storage.write_plan(plan)


def test_completed_cleanup_is_a_model_level_noop() -> None:
    selections = tuple(
        ArchiveSelection(task_id, "operator", selected_at="2026-07-14T00:00:00Z", pin_state_unknown_confirmed=True)
        for task_id in ("root", "worker", "review", "handoff", "replacement")
    )
    plan = build_plan(_graph(), operation_id="op-done", operation=OperationKind.ARCHIVE_ONLY, selections=selections)
    for state in (
        LifecycleState.FROZEN,
        LifecycleState.VERIFIED,
        LifecycleState.SNAPSHOTTED,
        LifecycleState.TASKS_ARCHIVED,
        LifecycleState.WORKTREES_REMOVED,
        LifecycleState.BRANCHES_DELETED,
        LifecycleState.RUNTIME_RETIRED,
        LifecycleState.COMPLETED,
    ):
        plan = plan.with_state(state)

    assert plan.is_completed_cleanup_noop
    assert plan.with_state(LifecycleState.COMPLETED) is plan
