"""Fail-closed command line interface for task-family lifecycle operations.

This module only plans, records, and verifies.  It deliberately has no adapter
for Codex's native task tools; archiving and restoring threads stay native-only.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from . import codex_state, executor, git_safety
from .graph import FamilyGraph, discover_task_family
from .model import (
    ArchiveSelection,
    Blocker,
    LifecycleEvent,
    LifecycleState,
    OperationKind,
    OperationReceipt,
    ReceiptAction,
    TaskFamilyManifest,
    utc_now,
)
from .planner import TaskFamilyPlan, build_plan, sha256_digest
from .storage import TaskFamilyStorage

EXIT_OK = 0
EXIT_INVALID = 2
EXIT_BLOCKED = 3
EXIT_ERROR = 4


class CliError(ValueError):
    """A noninteractive input or persisted-state error."""


def _canonical_uuid(value: str, label: str) -> str:
    try:
        parsed = str(uuid.UUID(value))
    except (AttributeError, ValueError) as exc:
        raise CliError(f"{label} must be a UUID: {value!r}") from exc
    if parsed != value:
        raise CliError(f"{label} must use canonical lowercase UUID text: {value!r}")
    return parsed


def _repo_root(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise CliError(f"repo root is not a directory: {path}")
    try:
        return git_safety.resolve_main_root(path)
    except Exception as exc:
        raise CliError(f"repo root is not a Git worktree: {path}: {exc}") from exc


def _load_manifest(path_value: str) -> TaskFamilyManifest:
    path = Path(path_value).expanduser()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CliError(f"manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CliError(f"manifest is invalid JSON: {path}: {exc.msg}") from exc
    try:
        return TaskFamilyManifest.from_dict(payload)
    except ValueError as exc:
        raise CliError(f"invalid manifest: {exc}") from exc


def _blocker_payload(blocker: Blocker) -> dict[str, Any]:
    return blocker.to_dict()


def _graph_payload(graph: FamilyGraph) -> dict[str, Any]:
    nodes = graph.nodes_by_id
    return {
        "family_id": graph.manifest.family_id,
        "seed_task_id": graph.manifest.seed_task_id,
        "included_task_ids": list(graph.included_task_ids),
        "excluded_task_ids": list(graph.excluded_task_ids),
        "counts": {
            "included": len(graph.included_task_ids),
            "excluded": len(graph.excluded_task_ids),
            "relations": len(graph.family_relations),
            "blockers": len(graph.blockers),
        },
        "tasks": [
            {
                "task_id": node.task_id,
                "title": node.title,
                "roles": list(graph.roles_by_task[node.task_id]),
                "resources": {
                    "project_root": node.project_root,
                    "worktree": node.worktree,
                    "branch": node.branch,
                    "pr_id": node.pr_id,
                },
            }
            for node in sorted(nodes.values(), key=lambda item: item.task_id)
        ],
        "excluded": [
            {
                "task_id": node.task_id,
                "title": node.title,
                "reason": "outside exact-ID seed component",
            }
            for node in sorted(graph.manifest.nodes, key=lambda item: item.task_id)
            if node.task_id in graph.excluded_task_ids
        ],
        "blockers": [_blocker_payload(item) for item in graph.blockers],
    }


def _human_inspect(payload: dict[str, Any]) -> str:
    lines = [
        f"Family {payload['family_id']} (seed {payload['seed_task_id']})",
        "Counts: " + ", ".join(f"{key}={value}" for key, value in payload["counts"].items()),
    ]
    for task in payload["tasks"]:
        roles = ", ".join(task["roles"]) or "unclassified"
        lines.append(f"- {task['task_id']}: {roles}; {task['title']}")
    for task in payload["excluded"]:
        lines.append(f"- excluded {task['task_id']}: {task['title']} ({task['reason']})")
    for blocker in payload["blockers"]:
        lines.append(f"BLOCKER {blocker['code']}: {blocker['message']}")
    return "\n".join(lines) + "\n"


def _emit(payload: dict[str, Any], *, json_output: bool, human: str) -> None:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(human, end="")


def _selection_inputs(args: argparse.Namespace) -> tuple[ArchiveSelection, ...]:
    selected = tuple(_canonical_uuid(value, "--select-task") for value in args.select_task)
    confirmed = {_canonical_uuid(value, "--confirm-pin-unknown") for value in args.confirm_pin_unknown}
    if len(selected) != len(set(selected)):
        raise CliError("each --select-task must name a distinct exact UUID")
    unknown_confirmations = confirmed - set(selected)
    if unknown_confirmations:
        joined = ", ".join(sorted(unknown_confirmations))
        raise CliError(f"pin confirmation names an unselected task: {joined}")
    return tuple(
        ArchiveSelection(
            task_id=task_id,
            actor=args.actor,
            pin_state_unknown_confirmed=task_id in confirmed,
        )
        for task_id in selected
    )


def _plan_with_blockers(plan: TaskFamilyPlan, blockers: Sequence[Blocker]) -> TaskFamilyPlan:
    if not blockers:
        return plan
    updated = replace(plan, blockers=tuple(sorted((*plan.blockers, *blockers), key=lambda item: (item.code, item.task_ids, item.message))))
    return replace(updated, digest=sha256_digest(updated.immutable_payload()))


def _plan_with_execution_context(plan: TaskFamilyPlan, execution_context: dict[str, Any]) -> TaskFamilyPlan:
    """Bind all executor adaptation inputs to the planner authorization digest."""
    updated = replace(plan, execution_context=execution_context)
    return replace(updated, digest=sha256_digest(updated.immutable_payload()))


def _preview_receipt(plan: TaskFamilyPlan) -> OperationReceipt:
    planned = [
        ReceiptAction("task", task_id, (task_id,), "verify_native_archive", "native task skill remains the only writer")
        for task_id in plan.selected_task_ids
    ]
    planned.extend(
        ReceiptAction(item.resource_type, item.resource_id, item.selected_task_ids, item.decision, item.reason)
        for item in plan.resource_decisions
    )
    return OperationReceipt(
        operation_id=plan.operation_id,
        family_id=plan.family_id,
        plan_digest=plan.digest,
        final_state=LifecycleState.PLANNED,
        planned=tuple(planned),
    )


def _db_path(value: str) -> Path:
    try:
        return codex_state.discover_state_database(None if value == "auto" else Path(value).expanduser())
    except codex_state.CodexStateError as exc:
        raise CliError(str(exc)) from exc


def _execution_payload(
    graph: FamilyGraph,
    plan: TaskFamilyPlan,
    *,
    lineage_id: str,
    db_path: Path,
    host: str | None,
) -> tuple[dict[str, Any], tuple[Blocker, ...]]:
    """Adapt only explicit manifest resources; absence is a safety blocker."""
    nodes = graph.nodes_by_id
    blockers: list[Blocker] = []
    tasks: list[dict[str, Any]] = []
    worktrees: list[dict[str, Any]] = []
    for task_id in plan.selected_task_ids:
        node = nodes[task_id]
        expected_host = host if host is not None else node.metadata.get("host")
        tasks.append(
            {
                "task_id": task_id,
                "title": node.title,
                "cwd": node.metadata.get("cwd", node.project_root),
                "db_path": str(db_path),
                "host": expected_host,
            }
        )
        resource_values = (node.worktree, node.branch, node.pr_id)
        if not any(resource_values):
            continue
        if not all(resource_values):
            blockers.append(
                Blocker(
                    "incomplete_worktree_resource",
                    f"Task {task_id!r} has partial worktree/branch/PR metadata.",
                    (task_id,),
                    "Supply all explicit resource fields; do not infer links from title or cwd.",
                )
            )
            continue
        pr_base = node.metadata.get("pr_base")
        owner = node.metadata.get("worktree_family")
        if not pr_base or owner != plan.family_id:
            blockers.append(
                Blocker(
                    "unproven_worktree_ownership",
                    f"Task {task_id!r} lacks explicit worktree_family and pr_base evidence.",
                    (task_id,),
                    "Set metadata.worktree_family to the exact family ID and metadata.pr_base explicitly.",
                )
            )
            continue
        try:
            pr_number = int(node.pr_id or "")
        except ValueError:
            blockers.append(Blocker("invalid_pr_id", f"Task {task_id!r} has nonnumeric pr_id.", (task_id,)))
            continue
        if pr_number <= 0:
            blockers.append(Blocker("invalid_pr_id", f"Task {task_id!r} has nonpositive pr_id.", (task_id,)))
            continue
        worktrees.append(
            {
                "id": task_id,
                "worktree": node.worktree,
                "branch": node.branch,
                "pr_number": pr_number,
                "pr_base": pr_base,
                "explicit_family": owner,
            }
        )
    if plan.operation is OperationKind.FINISH_AND_CLEAN and not worktrees:
        blockers.append(
            Blocker(
                "no_explicit_cleanup_resources",
                "finish_and_clean requires at least one explicit, owned worktree target.",
                remediation="Use archive-only or provide explicit worktree, branch, PR, family, and base evidence.",
            )
        )
    payload = {
        "schema_version": 1,
        "operation_id": plan.operation_id,
        "family_id": plan.family_id,
        "lineage_id": lineage_id,
        "mode": plan.operation.value,
        "target_db": str(db_path),
        "task_targets": tasks,
        "worktree_targets": worktrees,
        "runtime_targets": [],
        "pin_unknown_confirmed": all(item.pin_state_unknown_confirmed for item in plan.selections),
    }
    return payload, tuple(blockers)


def _persist_operation(
    root: Path,
    manifest: TaskFamilyManifest,
    plan: TaskFamilyPlan,
    execution_payload: dict[str, Any],
) -> TaskFamilyStorage:
    storage = TaskFamilyStorage(root, plan.family_id, plan.operation_id)
    storage.write_manifest(manifest)
    storage.write_plan(plan)
    storage.write_execution(execution_payload)
    storage.write_state(LifecycleState.PLANNED, details={"preview": True, "plan_digest": plan.digest})
    storage.write_receipt(_preview_receipt(plan))
    return storage


def _preview_payload(graph: FamilyGraph, plan: TaskFamilyPlan, execution_data: dict[str, Any]) -> dict[str, Any]:
    payload = _graph_payload(graph)
    payload.update(
        {
            "operation_id": plan.operation_id,
            "operation": plan.operation.value,
            "plan_digest": plan.digest,
            "selected_task_ids": list(plan.selected_task_ids),
            "base_title": plan.base_title,
            "rename_map": [
                {"task_id": item.task_id, "old_title": item.old_title, "new_title": item.new_title, "roles": list(item.roles)}
                for item in plan.rename_map
            ],
            "planner_blockers": [_blocker_payload(item) for item in plan.blockers],
            "resources": execution_data,
        }
    )
    return payload


def _human_preview(payload: dict[str, Any]) -> str:
    lines = [
        f"Preview {payload['operation']} for family {payload['family_id']}",
        f"Operation: {payload['operation_id']}",
        f"Plan digest: {payload['plan_digest']}",
        f"Counts: included={payload['counts']['included']}, selected={len(payload['selected_task_ids'])}, excluded={payload['counts']['excluded']}",
    ]
    for item in payload["rename_map"]:
        lines.append(f"- {item['task_id']}: {item['old_title']} -> {item['new_title']}")
    for task in payload["excluded"]:
        lines.append(f"- excluded {task['task_id']}: {task['title']}")
    for blocker in payload["planner_blockers"]:
        lines.append(f"BLOCKER {blocker['code']}: {blocker['message']}")
    return "\n".join(lines) + "\n"


def _cmd_inspect(args: argparse.Namespace) -> int:
    graph = discover_task_family(_load_manifest(args.manifest))
    payload = _graph_payload(graph)
    _emit(payload, json_output=args.json, human=_human_inspect(payload))
    return EXIT_OK if graph.is_valid else EXIT_BLOCKED


def _cmd_preview_rename(args: argparse.Namespace) -> int:
    root = _repo_root(args.repo_root)
    manifest = _load_manifest(args.manifest)
    operation_id = _canonical_uuid(args.operation_id, "--operation-id")
    graph = discover_task_family(manifest)
    selections = _selection_inputs(args)
    plan = build_plan(
        graph,
        operation_id=operation_id,
        operation=OperationKind.ARCHIVE_ONLY,
        selections=selections,
        base_title=args.base_title,
    )
    rename_payload = {
        "schema_version": 1,
        "kind": "rename_preview",
        "operation_id": operation_id,
        "family_id": manifest.family_id,
        "base_title": args.base_title,
        "selected_task_ids": list(plan.selected_task_ids),
        "excluded_task_ids": list(plan.excluded_task_ids),
        "rename_map": [
            {"task_id": item.task_id, "old_title": item.old_title, "new_title": item.new_title, "roles": list(item.roles)}
            for item in plan.rename_map
        ],
        "blockers": [_blocker_payload(item) for item in plan.blockers],
    }
    rename_payload["digest"] = sha256_digest(rename_payload)
    storage = TaskFamilyStorage(root, manifest.family_id, operation_id)
    storage.write_manifest(manifest)
    storage.write_immutable_json(storage.rename_plan_path, rename_payload)
    storage.write_state(LifecycleState.PLANNED, details={"preview": "rename", "digest": rename_payload["digest"]})
    storage.write_receipt(_preview_receipt(plan))
    payload = _graph_payload(graph)
    payload.update(rename_payload)
    payload["planner_blockers"] = rename_payload["blockers"]
    _emit(payload, json_output=args.json, human=_human_preview({**payload, "operation": "rename_preview", "plan_digest": rename_payload["digest"]}))
    return EXIT_OK if plan.is_actionable else EXIT_BLOCKED


def _cmd_preview_operation(args: argparse.Namespace, operation: OperationKind) -> int:
    root = _repo_root(args.repo_root)
    manifest = _load_manifest(args.manifest)
    operation_id = _canonical_uuid(args.operation_id, "--operation-id")
    lineage_id = _canonical_uuid(args.lineage_id, "--lineage-id")
    graph = discover_task_family(manifest)
    selections = _selection_inputs(args)
    plan = build_plan(graph, operation_id=operation_id, operation=operation, selections=selections, base_title=args.base_title)
    db_path = _db_path(args.db)
    execution_data, extra_blockers = _execution_payload(graph, plan, lineage_id=lineage_id, db_path=db_path, host=args.host)
    plan = _plan_with_blockers(plan, extra_blockers)
    plan = _plan_with_execution_context(plan, execution_data)
    execution_data = {**execution_data, "plan_digest": plan.digest}
    _persist_operation(root, manifest, plan, execution_data)
    payload = _preview_payload(graph, plan, execution_data)
    _emit(payload, json_output=args.json, human=_human_preview(payload))
    return EXIT_OK if plan.is_actionable else EXIT_BLOCKED


def _thread_result(record: codex_state.ThreadRecord) -> dict[str, Any]:
    return {
        "task_id": record.thread_id,
        "title": record.title,
        "cwd": record.cwd,
        "host": record.host,
        "archived": record.archived,
        "archived_at": record.archived_at,
    }


def _cmd_reconcile_title(args: argparse.Namespace) -> int:
    task_id = _canonical_uuid(args.task_id, "--task-id")
    db_path = _db_path(args.db)
    try:
        record = codex_state.read_thread_record(db_path, task_id=task_id)
        if record.title != args.expected_title or record.cwd != args.cwd or (args.host is not None and record.host != args.host):
            raise codex_state.CodexStateContextError("exact title, cwd, or host context does not match")
    except codex_state.CodexStateError as exc:
        payload = {"ok": False, "action": "reconcile_title", "task_id": task_id, "db_path": str(db_path), "error": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return EXIT_BLOCKED
    payload = {"ok": True, "action": "reconcile_title", "db_path": str(db_path), "thread": _thread_result(record)}
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return EXIT_OK


def _append_reconciliation(
    storage: TaskFamilyStorage,
    *,
    task_id: str,
    action: str,
    result: dict[str, Any],
    verified: bool,
) -> None:
    storage.append_event(
        LifecycleEvent(
            event_id=str(uuid.uuid4()),
            occurred_at=utc_now(),
            state=LifecycleState.TASKS_ARCHIVED,
            kind=f"native_{action}_reconciled",
            details=result,
        )
    )
    plan = storage.load_plan()
    try:
        previous = storage.load_receipt() if storage.receipt_path.exists() else _preview_receipt(plan)
    except ValueError:
        # The cleanup executor owns its state-shaped receipt after apply.  The
        # append-only event remains the exact per-task reconciliation evidence.
        return
    action_record = ReceiptAction(
        "task",
        task_id,
        (task_id,),
        f"native_{action}_{'verified' if verified else 'blocked'}",
        "" if verified else str(result.get("error", "native target was not reached")),
    )
    if verified:
        storage.write_receipt(replace(previous, actual=(*previous.actual, action_record), events=storage.load_events()))
    else:
        storage.write_receipt(replace(previous, failures=(*previous.failures, action_record), events=storage.load_events()))


def _cmd_reconcile_archive(args: argparse.Namespace, *, archived: bool) -> int:
    root = _repo_root(args.repo_root)
    task_id = _canonical_uuid(args.task_id, "--task-id")
    operation_id = _canonical_uuid(args.operation_id, "--operation-id")
    storage = TaskFamilyStorage(root, args.family_id, operation_id)
    try:
        plan = storage.load_plan()
        if task_id not in plan.selected_task_ids:
            raise CliError(f"task {task_id} is not an explicitly selected operation target")
        db_path = _db_path(args.db)
        record = codex_state.await_task_target(
            task_id=task_id,
            expected_title=args.expected_title,
            expected_cwd=args.cwd,
            expected_host=args.host,
            expected_archived=archived,
            db_path=db_path,
        )
        result = {"ok": True, "action": "archive" if archived else "restore", "db_path": str(db_path), "thread": _thread_result(record)}
        _append_reconciliation(storage, task_id=task_id, action=result["action"], result=result, verified=True)
    except (CliError, codex_state.CodexStateError, ValueError) as exc:
        result = {"ok": False, "action": "archive" if archived else "restore", "task_id": task_id, "error": str(exc)}
        if storage.plan_path.exists():
            _append_reconciliation(storage, task_id=task_id, action=result["action"], result=result, verified=False)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return EXIT_BLOCKED
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return EXIT_OK


def _cleanup_plan_from_storage(root: Path, *, family_id: str, operation_id: str, lineage_id: str, digest: str) -> executor.CleanupPlan:
    storage = TaskFamilyStorage(root, family_id, operation_id)
    persisted = storage.assert_plan_digest(digest)
    plan = TaskFamilyPlan.from_dict(persisted)
    if plan.family_id != family_id or plan.operation_id != operation_id:
        raise CliError("persisted plan identity does not match apply request")
    if plan.blockers:
        raise CliError("persisted plan contains blockers; rebuild explicit plan before apply")
    data = storage.load_execution()
    context = dict(data)
    context.pop("plan_digest", None)
    if data.get("plan_digest") != digest or context != (plan.execution_context or {}):
        raise CliError("persisted execution inputs drifted from planner authorization")
    if data.get("lineage_id") != lineage_id:
        raise CliError("persisted execution inputs do not match caller digest or lineage")
    if data.get("mode") != plan.operation.value:
        raise CliError("persisted execution mode does not match planner operation")

    def task_target(item: Any) -> executor.TaskTarget:
        if not isinstance(item, dict):
            raise CliError("persisted task target must be an object")
        return executor.TaskTarget(
            task_id=_canonical_uuid(str(item.get("task_id", "")), "persisted task target"),
            title=str(item.get("title", "")),
            cwd=str(item.get("cwd", "")),
            db_path=Path(str(item.get("db_path", ""))),
            host=item.get("host") if isinstance(item.get("host"), str) else None,
        )

    def worktree_target(item: Any) -> executor.WorktreeTarget:
        if not isinstance(item, dict):
            raise CliError("persisted worktree target must be an object")
        return executor.WorktreeTarget(
            id=_canonical_uuid(str(item.get("id", "")), "persisted worktree target"),
            worktree=Path(str(item.get("worktree", ""))),
            branch=str(item.get("branch", "")),
            pr_number=int(item.get("pr_number", 0)),
            pr_base=str(item.get("pr_base", "")),
            explicit_family=str(item.get("explicit_family", "")),
        )

    def runtime_target(item: Any) -> executor.RuntimeTarget:
        if not isinstance(item, dict):
            raise CliError("persisted runtime target must be an object")
        return executor.RuntimeTarget(
            id=_canonical_uuid(str(item.get("id", "")), "persisted runtime target"),
            kind=str(item.get("kind", "")),
            eligible=item.get("eligible") is True,
            proof=item.get("proof") if isinstance(item.get("proof"), str) else None,
        )

    raw_tasks = data.get("task_targets")
    raw_worktrees = data.get("worktree_targets")
    raw_runtime = data.get("runtime_targets")
    if not all(isinstance(value, list) for value in (raw_tasks, raw_worktrees, raw_runtime)):
        raise CliError("persisted execution target lists are invalid")
    return executor.CleanupPlan(
        operation_id=operation_id,
        family_id=family_id,
        lineage_id=lineage_id,
        mode=plan.operation.value,
        task_targets=tuple(task_target(item) for item in raw_tasks),
        worktree_targets=tuple(worktree_target(item) for item in raw_worktrees),
        runtime_targets=tuple(runtime_target(item) for item in raw_runtime),
        selected_task_ids=frozenset(plan.selected_task_ids),
        pin_unknown_confirmed=data.get("pin_unknown_confirmed") is True,
        persisted_plan_digest=digest,
    )


def _cmd_apply_cleanup(args: argparse.Namespace) -> int:
    root = _repo_root(args.repo_root)
    operation_id = _canonical_uuid(args.operation_id, "--operation-id")
    lineage_id = _canonical_uuid(args.lineage_id, "--lineage-id")
    digest = args.plan_digest.lower()
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise CliError("--plan-digest must be a lowercase SHA-256 hex digest")
    try:
        cleanup_plan = _cleanup_plan_from_storage(root, family_id=args.family_id, operation_id=operation_id, lineage_id=lineage_id, digest=digest)
        result = executor.CleanupExecutor(root, cleanup_plan).run()
    except (CliError, executor.ExecutorError, git_safety.GitSafetyError, ValueError) as exc:
        payload = {"ok": False, "action": "apply_cleanup", "error": str(exc)}
        _emit(payload, json_output=args.json, human=f"BLOCKER: {exc}\n")
        return EXIT_BLOCKED
    payload = {"ok": result.get("state") not in {"blocked"}, "action": "apply_cleanup", "result": result}
    _emit(payload, json_output=args.json, human=f"Cleanup state: {result.get('state')}\n")
    return EXIT_OK if payload["ok"] else EXIT_BLOCKED


def _receipt_human(payload: dict[str, Any]) -> str:
    if "final_state" in payload:
        return OperationReceipt.from_dict(payload).render_human()
    lines = [f"Task-family operation {payload.get('operation_id', 'unknown')}", f"State: {payload.get('state', 'planned')}"]
    resources = payload.get("resources", {})
    if isinstance(resources, dict):
        for kind in ("task", "worktree", "runtime"):
            entries = resources.get(kind, {})
            if not isinstance(entries, dict):
                continue
            for resource_id, entry in sorted(entries.items()):
                status = entry.get("status", "planned") if isinstance(entry, dict) else "unknown"
                lines.append(f"{status}: {kind}:{resource_id}")
    blocked = payload.get("blocked")
    if blocked:
        lines.append(f"BLOCKER: {blocked}")
    return "\n".join(lines) + "\n"


def _cmd_receipt(args: argparse.Namespace) -> int:
    root = _repo_root(args.repo_root)
    operation_id = _canonical_uuid(args.operation_id, "--operation-id")
    storage = TaskFamilyStorage(root, args.family_id, operation_id)
    try:
        payload = storage.read_json(storage.receipt_path)
    except FileNotFoundError as exc:
        raise CliError(f"receipt not found: {storage.receipt_path}") from exc
    _emit(payload, json_output=args.json, human=_receipt_human(payload))
    return EXIT_BLOCKED if payload.get("state") == "blocked" else EXIT_OK


def _add_selection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--select-task", action="append", required=True, default=[])
    parser.add_argument("--actor", required=True)
    parser.add_argument("--confirm-pin-unknown", action="append", required=True, default=[])


def _add_preview_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--operation-id", required=True)
    parser.add_argument("--lineage-id", required=True)
    parser.add_argument("--base-title", required=True)
    parser.add_argument("--db", required=True, help="Codex SQLite path or 'auto'")
    parser.add_argument("--host")
    _add_selection_arguments(parser)
    parser.add_argument("--json", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task-family")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--manifest", required=True)
    inspect.add_argument("--json", action="store_true")

    rename = commands.add_parser("preview-rename")
    rename.add_argument("--repo-root", required=True)
    rename.add_argument("--manifest", required=True)
    rename.add_argument("--operation-id", required=True)
    rename.add_argument("--base-title", required=True)
    _add_selection_arguments(rename)
    rename.add_argument("--json", action="store_true")

    for name in ("preview-archive", "preview-cleanup"):
        command = commands.add_parser(name)
        _add_preview_arguments(command)

    title = commands.add_parser("reconcile-title")
    title.add_argument("--db", required=True)
    title.add_argument("--task-id", required=True)
    title.add_argument("--cwd", required=True)
    title.add_argument("--expected-title", required=True)
    title.add_argument("--host")

    for name in ("reconcile-archive", "reconcile-restore"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", required=True)
        command.add_argument("--family-id", required=True)
        command.add_argument("--operation-id", required=True)
        command.add_argument("--db", required=True)
        command.add_argument("--task-id", required=True)
        command.add_argument("--cwd", required=True)
        command.add_argument("--expected-title", required=True)
        command.add_argument("--host")

    apply_cleanup = commands.add_parser("apply-cleanup")
    apply_cleanup.add_argument("--repo-root", required=True)
    apply_cleanup.add_argument("--family-id", required=True)
    apply_cleanup.add_argument("--operation-id", required=True)
    apply_cleanup.add_argument("--lineage-id", required=True)
    apply_cleanup.add_argument("--plan-digest", required=True)
    apply_cleanup.add_argument("--json", action="store_true")

    receipt = commands.add_parser("receipt")
    receipt.add_argument("--repo-root", required=True)
    receipt.add_argument("--family-id", required=True)
    receipt.add_argument("--operation-id", required=True)
    receipt.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            return _cmd_inspect(args)
        if args.command == "preview-rename":
            return _cmd_preview_rename(args)
        if args.command == "preview-archive":
            return _cmd_preview_operation(args, OperationKind.ARCHIVE_ONLY)
        if args.command == "preview-cleanup":
            return _cmd_preview_operation(args, OperationKind.FINISH_AND_CLEAN)
        if args.command == "reconcile-title":
            return _cmd_reconcile_title(args)
        if args.command == "reconcile-archive":
            return _cmd_reconcile_archive(args, archived=True)
        if args.command == "reconcile-restore":
            return _cmd_reconcile_archive(args, archived=False)
        if args.command == "apply-cleanup":
            return _cmd_apply_cleanup(args)
        if args.command == "receipt":
            return _cmd_receipt(args)
        raise CliError(f"unsupported command: {args.command}")
    except (CliError, ValueError) as exc:
        print(f"task-family: {exc}", file=sys.stderr)
        return EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
