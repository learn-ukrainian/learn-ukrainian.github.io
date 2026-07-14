from __future__ import annotations

import json

import pytest

from scripts.orchestration.task_family.graph import discover_task_family, rename_mapping
from scripts.orchestration.task_family.model import (
    ArchiveSelection,
    LifecycleEvent,
    LifecycleState,
    OperationKind,
    OperationReceipt,
    ReceiptAction,
    RelationType,
    TaskFamilyManifest,
    TaskNode,
    TaskRelation,
)
from scripts.orchestration.task_family.planner import TaskFamilyPlan, build_plan
from scripts.orchestration.task_family.storage import TaskFamilyStorage, atomic_write_json


def _node(task_id: str, title: str, **resources: str) -> TaskNode:
    return TaskNode(task_id, title, "/repo", **resources)


def _manifest(
    *,
    relations: tuple[TaskRelation, ...],
    nodes: tuple[TaskNode, ...] | None = None,
    seed_task_id: str = "root",
) -> TaskFamilyManifest:
    return TaskFamilyManifest(
        "family-5140",
        seed_task_id,
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


def _selection(task_id: str) -> ArchiveSelection:
    return ArchiveSelection(task_id, "operator", selected_at="2026-07-14T00:00:00Z", pin_state_unknown_confirmed=True)


def test_discovers_synthetic_root_worker_reviewer_handoff_and_replacement() -> None:
    graph = _graph()

    assert graph.is_valid
    assert graph.roots == ("root",)
    assert graph.roles_by_task["root"] == ("Lead",)
    assert graph.roles_by_task["worker"] == ("Worker",)
    assert graph.roles_by_task["review"] == ("Reviewer",)
    assert graph.roles_by_task["handoff"] == ("Handoff",)
    assert graph.roles_by_task["replacement"] == ("Replacement", "Generation 1")


def test_exact_id_component_excludes_similar_title_and_display_only_members() -> None:
    manifest = _manifest(
        nodes=(
            _node("root", "Same title"),
            _node("worker", "Worker"),
            _node("unrelated", "Same title"),
            _node("display", "Same title"),
        ),
        relations=(
            TaskRelation("worker", "root", RelationType.SUBAGENT_OF, "spawn"),
            TaskRelation("display", "root", RelationType.ISSUE_OR_PR_MEMBER, "issue annotation", family_defining=False),
        ),
    )

    graph = discover_task_family(manifest)

    assert graph.is_valid
    assert graph.included_task_ids == ("root", "worker")
    assert graph.excluded_task_ids == ("display", "unrelated")
    plan = build_plan(graph, operation_id="component-preview", operation=OperationKind.ARCHIVE_ONLY, selections=(_selection("root"), _selection("worker")), base_title="Lifecycle repair")
    assert plan.excluded_task_ids == ("display", "unrelated")


def test_unknown_relation_endpoint_blocks_without_entering_component() -> None:
    graph = discover_task_family(
        _manifest(
            nodes=(_node("root", "Root"),),
            relations=(TaskRelation("unknown-worker", "root", RelationType.SUBAGENT_OF, "invalid endpoint"),),
        )
    )

    assert graph.included_task_ids == ("root",)
    assert graph.roles_by_task == {"root": ("Lead",)}
    assert any(blocker.code == "unknown_endpoint" for blocker in graph.blockers)


def test_rename_mapping_uses_one_caller_supplied_base_and_stable_separator() -> None:
    mapping = {item.task_id: item for item in rename_mapping(_graph(), "Lifecycle repair")}

    assert mapping["root"].new_title == "Lifecycle repair [Lead]"
    assert mapping["replacement"].new_title == "Lifecycle repair [Repl. · Gen. 1]"
    assert mapping["replacement"].old_title == "Continuation"


def test_rename_mapping_respects_native_codex_title_limit_without_losing_roles() -> None:
    mapping = {item.task_id: item for item in rename_mapping(_graph(), "A deliberately oversized lifecycle repair title")}

    replacement = mapping["replacement"]
    assert len(replacement.new_title) <= 60
    assert "… [" in replacement.new_title
    assert replacement.new_title.endswith("[Repl. · Gen. 1]")
    assert replacement.roles == ("Replacement", "Generation 1")

    ukrainian = {item.task_id: item for item in rename_mapping(_graph(), "Завершення надзвичайно довгого життєвого циклу завдання")}
    assert len(ukrainian["replacement"].new_title) <= 60
    assert ukrainian["replacement"].new_title.endswith("[Repl. · Gen. 1]")


def test_generation_is_transitive_and_relation_order_independent() -> None:
    nodes = (_node("root", "Root"), _node("generation-1", "One"), _node("generation-2", "Two"))
    relations = (
        TaskRelation("generation-1", "root", RelationType.ROLLOVER_GENERATION_OF, "first rollover"),
        TaskRelation("generation-2", "generation-1", RelationType.ROLLOVER_GENERATION_OF, "second rollover"),
    )
    first = discover_task_family(_manifest(nodes=nodes, relations=relations))
    second = discover_task_family(_manifest(nodes=nodes, relations=tuple(reversed(relations))))

    assert first.roles_by_task == second.roles_by_task
    assert first.roles_by_task["generation-2"] == ("Generation 2",)


def test_rollover_cycle_and_conflict_fail_closed() -> None:
    cycle = discover_task_family(
        _manifest(
            nodes=(_node("root", "Root"), _node("next", "Next")),
            relations=(
                TaskRelation("root", "next", RelationType.ROLLOVER_GENERATION_OF, "a"),
                TaskRelation("next", "root", RelationType.ROLLOVER_GENERATION_OF, "b"),
            ),
        )
    )
    conflict = discover_task_family(
        _manifest(
            nodes=(_node("root", "Root"), _node("one", "One"), _node("two", "Two")),
            relations=(
                TaskRelation("root", "one", RelationType.ROLLOVER_GENERATION_OF, "a"),
                TaskRelation("root", "two", RelationType.ROLLOVER_GENERATION_OF, "b"),
            ),
        )
    )

    assert any(blocker.code == "parent_relation_cycle" for blocker in cycle.blockers)
    assert any(blocker.code == "conflicting_membership" for blocker in conflict.blockers)


def test_selection_requires_explicit_source_and_pin_confirmation() -> None:
    graph = _graph()
    selection = ArchiveSelection("root", "operator", selected_at="2026-07-14T00:00:00Z")

    plan = build_plan(graph, operation_id="op-1", operation=OperationKind.ARCHIVE_ONLY, selections=(selection,), base_title="Lifecycle repair")

    assert any(blocker.code == "pin_state_unconfirmed" for blocker in plan.blockers)
    assert plan.selections[0].selection_source == "explicit"
    with pytest.raises(ValueError, match="selection_source"):
        ArchiveSelection("root", "operator", selection_source="inferred", pin_state_unknown_confirmed=True)


def test_unselected_shared_resource_blocks_planning() -> None:
    manifest = _manifest(
        nodes=(_node("root", "Root", branch="codex/shared"), _node("worker", "Worker", branch="codex/shared")),
        relations=(TaskRelation("worker", "root", RelationType.SUBAGENT_OF, "spawn"),),
    )
    plan = build_plan(discover_task_family(manifest), operation_id="op-2", operation=OperationKind.ARCHIVE_ONLY, selections=(_selection("root"),), base_title="Lifecycle repair")

    assert any(blocker.code == "unselected_shared_resource" for blocker in plan.blockers)
    assert any(blocker.code == "unselected_lineage_endpoint" for blocker in plan.blockers)


def test_plan_digest_is_stable_across_relation_order_and_changes_on_mutation() -> None:
    selection = _selection("root")
    first = build_plan(_graph(), operation_id="op-digest", operation=OperationKind.ARCHIVE_ONLY, selections=(selection,), base_title="Lifecycle repair")
    reordered = discover_task_family(_manifest(relations=tuple(reversed(_graph().manifest.relations))))
    second = build_plan(reordered, operation_id="op-digest", operation=OperationKind.ARCHIVE_ONLY, selections=(selection,), base_title="Lifecycle repair")
    mutated = build_plan(_graph(), operation_id="op-digest", operation=OperationKind.ARCHIVE_ONLY, selections=(selection,), base_title="Different lifecycle")

    assert first.digest == second.digest
    assert first.digest != mutated.digest


def test_archive_only_stops_at_independently_reconciled_tasks_archived() -> None:
    selections = tuple(_selection(task_id) for task_id in ("root", "worker", "review", "handoff", "replacement"))
    plan = build_plan(_graph(), operation_id="op-archive", operation=OperationKind.ARCHIVE_ONLY, selections=selections, base_title="Lifecycle repair")
    assert tuple(stage.state for stage in plan.stages) == (
        LifecycleState.PLANNED,
        LifecycleState.FROZEN,
        LifecycleState.VERIFIED,
        LifecycleState.TASKS_ARCHIVED,
    )
    for state in (LifecycleState.FROZEN, LifecycleState.VERIFIED, LifecycleState.TASKS_ARCHIVED):
        plan = plan.with_state(state)

    assert plan.is_completed_cleanup_noop
    assert plan.with_state(LifecycleState.TASKS_ARCHIVED) is plan
    with pytest.raises(ValueError, match="terminal state"):
        plan.with_state(LifecycleState.COMPLETED)


def test_finish_and_clean_retains_full_ordered_path() -> None:
    plan = build_plan(_graph(), operation_id="op-clean", operation=OperationKind.FINISH_AND_CLEAN, selections=tuple(_selection(task_id) for task_id in ("root", "worker", "review", "handoff", "replacement")), base_title="Lifecycle repair")

    assert tuple(stage.state for stage in plan.stages) == (
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


def test_storage_exposes_all_runtime_evidence_and_validated_loaders(tmp_path) -> None:
    selection = _selection("root")
    plan = build_plan(_graph(), operation_id="op-store", operation=OperationKind.ARCHIVE_ONLY, selections=(selection,), base_title="Lifecycle repair")
    storage = TaskFamilyStorage(tmp_path, plan.family_id, plan.operation_id)
    storage.write_manifest(_graph().manifest)
    storage.write_plan(plan)
    storage.write_state(LifecycleState.FROZEN, details={"lock": "held"})
    storage.write_snapshot("before-archive.json", {"task_ids": ["root"]})
    event = LifecycleEvent("event-1", "2026-07-14T00:00:00Z", LifecycleState.FROZEN, "verified", {"task_id": "root"})
    storage.append_event(event)
    action = ReceiptAction("task", "root", ("root",), "archive", "selected explicitly")
    final = ReceiptAction("runtime", plan.operation_id, ("root",), "retained", "archive-only target reached")
    receipt = OperationReceipt(plan.operation_id, plan.family_id, plan.digest, LifecycleState.TASKS_ARCHIVED, planned=(action,), actual=(action,), skipped=(ReceiptAction("worktree", "/repo/root", ("root",), "not-run", "archive-only"),), restoration=(ReceiptAction("task", "root", ("root",), "restore", "unarchive via task system"),), final_resources=(final,), events=(event,))
    storage.write_receipt(receipt)

    assert storage.manifest_path.is_file()
    assert storage.plan_path.is_file()
    assert storage.state_path.is_file()
    assert storage.receipt_path.is_file() and storage.receipt_text_path.is_file()
    assert (storage.snapshots_dir / "before-archive.json").is_file()
    assert storage.load_manifest() == _graph().manifest
    assert storage.load_plan() == plan
    assert storage.load_state()["state"] == "frozen"
    assert storage.load_events() == (event,)
    assert storage.load_receipt() == receipt
    assert "task:root archive" in storage.receipt_text_path.read_text(encoding="utf-8")


def test_atomic_persistence_and_schema_validation_reject_drift_and_unknown_enums(tmp_path) -> None:
    path = tmp_path / "record.json"
    atomic_write_json(path, {"b": 2, "a": 1})
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1, "b": 2}
    manifest_data = _graph().manifest.to_dict()
    manifest_data["schema_version"] = 99
    with pytest.raises(ValueError, match="schema_version"):
        TaskFamilyManifest.from_dict(manifest_data)
    manifest_data = _graph().manifest.to_dict()
    manifest_data["relations"][0]["relation_type"] = "unknown"
    with pytest.raises(ValueError, match="unknown task relation type"):
        TaskFamilyManifest.from_dict(manifest_data)
    plan = build_plan(_graph(), operation_id="op-parse", operation=OperationKind.ARCHIVE_ONLY, selections=(_selection("root"),), base_title="Lifecycle repair")
    payload = plan.to_dict()
    payload["state"] = "unknown"
    with pytest.raises(ValueError, match="unknown operation or lifecycle state"):
        TaskFamilyPlan.from_dict(payload)
