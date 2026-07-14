"""Exact-ID task-family graph discovery and role-preserving title rendering."""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import PurePath

from .model import PARENT_LIKE_RELATIONS, Blocker, RelationType, TaskFamilyManifest, TaskNode, TaskRelation

ROLE_ORDER = ("Lead", "Worker", "Reviewer", "Handoff", "Replacement")
CODEX_TITLE_MAX_CHARS = 60


def _display_role(role: str) -> str:
    """Keep role semantics readable inside Codex's persisted title limit."""
    if role == "Replacement":
        return "Repl."
    if role.startswith("Generation "):
        return f"Gen. {role.removeprefix('Generation ')}"
    return role


def _bounded_title(base_title: str, roles: tuple[str, ...]) -> str:
    base = base_title.strip()
    suffix = " · ".join(_display_role(role) for role in roles)
    if not suffix:
        available = CODEX_TITLE_MAX_CHARS
    else:
        available = CODEX_TITLE_MAX_CHARS - len(suffix) - len(" []")
        if available < 1:
            raise ValueError("role suffix exceeds the Codex title limit")
    if len(base) > available:
        base = f"{base[: max(available - 1, 0)].rstrip()}…"
    return f"{base} [{suffix}]" if suffix else base


@dataclass(frozen=True, slots=True)
class TitleRename:
    task_id: str
    old_title: str
    new_title: str
    roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FamilyGraph:
    manifest: TaskFamilyManifest
    included_task_ids: tuple[str, ...]
    excluded_task_ids: tuple[str, ...]
    roots: tuple[str, ...]
    roles_by_task: dict[str, tuple[str, ...]]
    blockers: tuple[Blocker, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.blockers

    @property
    def nodes_by_id(self) -> dict[str, TaskNode]:
        included = set(self.included_task_ids)
        return {node.task_id: node for node in self.manifest.nodes if node.task_id in included}

    @property
    def family_relations(self) -> tuple[TaskRelation, ...]:
        included = set(self.included_task_ids)
        return tuple(
            relation
            for relation in self.manifest.relations
            if not relation.is_display_only and relation.source_id in included and relation.target_id in included
        )


def _normal_root(path: str) -> str:
    return os.path.normpath(str(PurePath(path)))


def _cycle_nodes(relations: tuple[TaskRelation, ...]) -> tuple[str, ...]:
    adjacency: dict[str, list[str]] = defaultdict(list)
    for relation in relations:
        if relation.relation_type in PARENT_LIKE_RELATIONS:
            adjacency[relation.source_id].append(relation.target_id)
    visiting: list[str] = []
    visited: set[str] = set()
    cycle_members: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            cycle_members.update(visiting[visiting.index(node) :])
            return True
        if node in visited:
            return False
        visiting.append(node)
        found = any(visit(neighbor) for neighbor in adjacency.get(node, ()))
        visiting.pop()
        visited.add(node)
        return found

    for node in tuple(adjacency):
        visit(node)
    return tuple(sorted(cycle_members))


def _roots(nodes: tuple[TaskNode, ...], relations: tuple[TaskRelation, ...]) -> tuple[str, ...]:
    explicit = {relation.target_id for relation in relations if relation.relation_type is RelationType.ROOT}
    if explicit:
        return tuple(sorted(explicit))
    child_ids = {relation.source_id for relation in relations if relation.relation_type in PARENT_LIKE_RELATIONS}
    inferred = {node.task_id for node in nodes} - child_ids
    return tuple(sorted(inferred))


def _generation_numbers(nodes: tuple[TaskNode, ...], relations: tuple[TaskRelation, ...]) -> dict[str, int]:
    """Resolve rollover generations by dependency, never relation input order."""
    parents: dict[str, tuple[str, ...]] = defaultdict(tuple)
    grouped: dict[str, list[str]] = defaultdict(list)
    for relation in relations:
        if relation.relation_type is RelationType.ROLLOVER_GENERATION_OF:
            grouped[relation.source_id].append(relation.target_id)
    for source, targets in grouped.items():
        parents[source] = tuple(sorted(set(targets)))
    resolved: dict[str, int] = {}
    visiting: set[str] = set()

    def resolve(task_id: str) -> int:
        if task_id in resolved:
            return resolved[task_id]
        if task_id in visiting:
            return 0
        visiting.add(task_id)
        targets = parents.get(task_id, ())
        value = 0 if not targets else max(resolve(target_id) + 1 for target_id in targets)
        visiting.remove(task_id)
        resolved[task_id] = value
        return value

    for node in sorted(nodes, key=lambda item: item.task_id):
        resolve(node.task_id)
    return resolved


def _roles(nodes: tuple[TaskNode, ...], relations: tuple[TaskRelation, ...], roots: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    values: dict[str, set[str]] = {node.task_id: set() for node in nodes}
    for root in roots:
        values[root].add("Lead")
    generation = _generation_numbers(nodes, relations)
    for relation in relations:
        if relation.is_display_only:
            continue
        role = {
            RelationType.SUBAGENT_OF: "Worker",
            RelationType.REVIEWER_FOR: "Reviewer",
            RelationType.HANDOFF_OF: "Handoff",
            RelationType.REPLACEMENT_OF: "Replacement",
        }.get(relation.relation_type)
        if role:
            values[relation.source_id].add(role)
    for task_id, number in generation.items():
        if number:
            values[task_id].add(f"Generation {number}")

    def sort_key(role: str) -> tuple[int, int | str]:
        if role in ROLE_ORDER:
            return (0, ROLE_ORDER.index(role))
        return (1, int(role.removeprefix("Generation ")))

    return {task_id: tuple(sorted(roles, key=sort_key)) for task_id, roles in values.items()}


def _component(seed_task_id: str, relations: tuple[TaskRelation, ...]) -> set[str]:
    """Return the exact-ID component, ignoring display-only membership annotations."""
    adjacency: dict[str, set[str]] = defaultdict(set)
    for relation in relations:
        if relation.is_display_only:
            continue
        adjacency[relation.source_id].add(relation.target_id)
        adjacency[relation.target_id].add(relation.source_id)
    discovered = {seed_task_id}
    pending = [seed_task_id]
    while pending:
        current = pending.pop()
        for neighbor in sorted(adjacency[current] - discovered):
            discovered.add(neighbor)
            pending.append(neighbor)
    return discovered


def discover_task_family(manifest: TaskFamilyManifest) -> FamilyGraph:
    blockers: list[Blocker] = []
    nodes_by_id: dict[str, TaskNode] = {}
    for node in manifest.nodes:
        if node.task_id in nodes_by_id:
            blockers.append(Blocker("duplicate_task_id", f"Task ID {node.task_id!r} appears more than once.", (node.task_id,)))
        nodes_by_id[node.task_id] = node
    for relation in manifest.relations:
        missing = tuple(task_id for task_id in (relation.source_id, relation.target_id) if task_id not in nodes_by_id)
        if missing:
            blockers.append(Blocker("unknown_endpoint", f"Relation {relation.relation_type.value} names unknown exact task ID(s): {', '.join(missing)}.", missing, "Correct the manifest endpoints; titles cannot establish membership."))
    known_relations = tuple(
        relation
        for relation in manifest.relations
        if relation.source_id in nodes_by_id and relation.target_id in nodes_by_id
    )
    if manifest.seed_task_id not in nodes_by_id:
        blockers.append(Blocker("unknown_seed_task", f"Seed task ID {manifest.seed_task_id!r} is not in the manifest.", (manifest.seed_task_id,), "Supply one existing exact task ID as the family seed."))
    included_set = _component(manifest.seed_task_id, known_relations) if manifest.seed_task_id in nodes_by_id else set()
    included_nodes = tuple(node for node in manifest.nodes if node.task_id in included_set)
    excluded_task_ids = tuple(sorted(set(nodes_by_id) - included_set))
    included_relations = tuple(
        relation
        for relation in known_relations
        if not relation.is_display_only and relation.source_id in included_set and relation.target_id in included_set
    )
    roots = _roots(included_nodes, included_relations)
    if len(roots) != 1:
        blockers.append(Blocker("multiple_or_missing_roots", f"Family must resolve to exactly one root; found {len(roots)}: {', '.join(roots) or 'none'}.", roots, "Supply unambiguous family-defining exact-ID relations."))
    project_roots = {_normal_root(node.project_root) for node in included_nodes}
    if len(project_roots) > 1:
        blockers.append(Blocker("incompatible_project_roots", "Family nodes use incompatible project roots.", tuple(sorted(included_set)), "Split the family or supply evidence for a single compatible project root."))
    conflicts: dict[tuple[str, RelationType], set[str]] = defaultdict(set)
    for relation in included_relations:
        if relation.relation_type in PARENT_LIKE_RELATIONS and not relation.is_display_only:
            conflicts[(relation.source_id, relation.relation_type)].add(relation.target_id)
    for (source, relation_type), targets in conflicts.items():
        if len(targets) > 1:
            blockers.append(Blocker("conflicting_membership", f"Task {source} has conflicting {relation_type.value} parents: {', '.join(sorted(targets))}.", (source, *sorted(targets))))
    cycles = _cycle_nodes(included_relations)
    if cycles:
        blockers.append(Blocker("parent_relation_cycle", f"Parent-like task relations contain a cycle at: {', '.join(cycles)}.", cycles))
    return FamilyGraph(manifest, tuple(sorted(included_set)), excluded_task_ids, roots, _roles(included_nodes, included_relations, roots), tuple(blockers))


def rename_mapping(graph: FamilyGraph, base_title: str) -> tuple[TitleRename, ...]:
    """Return stable title display changes; source titles are never identity keys."""
    if not base_title.strip():
        raise ValueError("base_title must be a non-empty caller-supplied value")
    changes: list[TitleRename] = []
    for node in sorted(graph.nodes_by_id.values(), key=lambda item: item.task_id):
        roles = graph.roles_by_task[node.task_id]
        new_title = _bounded_title(base_title, roles)
        changes.append(TitleRename(node.task_id, node.title, new_title, roles))
    return tuple(changes)
