"""Exact-ID task-family graph discovery and role-preserving title rendering."""

from __future__ import annotations

import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import PurePath

from .model import PARENT_LIKE_RELATIONS, Blocker, RelationType, TaskFamilyManifest, TaskNode, TaskRelation

ROLE_ORDER = ("Lead", "Worker", "Reviewer", "Handoff", "Replacement")


@dataclass(frozen=True, slots=True)
class TitleRename:
    task_id: str
    old_title: str
    new_title: str
    roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FamilyGraph:
    manifest: TaskFamilyManifest
    roots: tuple[str, ...]
    roles_by_task: dict[str, tuple[str, ...]]
    blockers: tuple[Blocker, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.blockers

    @property
    def nodes_by_id(self) -> dict[str, TaskNode]:
        return {node.task_id: node for node in self.manifest.nodes}

    @property
    def family_relations(self) -> tuple[TaskRelation, ...]:
        return tuple(relation for relation in self.manifest.relations if not relation.is_display_only)


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


def _roles(nodes: tuple[TaskNode, ...], relations: tuple[TaskRelation, ...], roots: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    values: dict[str, set[str]] = {node.task_id: set() for node in nodes}
    for root in roots:
        values[root].add("Lead")
    generation: dict[str, int] = defaultdict(int)
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
        if relation.relation_type is RelationType.ROLLOVER_GENERATION_OF:
            generation[relation.source_id] = max(generation[relation.source_id], generation[relation.target_id] + 1)
    for task_id, number in generation.items():
        if number:
            values[task_id].add(f"Generation {number}")

    def sort_key(role: str) -> tuple[int, int | str]:
        if role in ROLE_ORDER:
            return (0, ROLE_ORDER.index(role))
        return (1, int(role.removeprefix("Generation ")))

    return {task_id: tuple(sorted(roles, key=sort_key)) for task_id, roles in values.items()}


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
    roots = _roots(manifest.nodes, manifest.relations)
    if len(roots) != 1:
        blockers.append(Blocker("multiple_or_missing_roots", f"Family must resolve to exactly one root; found {len(roots)}: {', '.join(roots) or 'none'}.", roots, "Supply unambiguous family-defining exact-ID relations."))
    project_roots = {_normal_root(node.project_root) for node in manifest.nodes}
    if len(project_roots) > 1:
        blockers.append(Blocker("incompatible_project_roots", "Family nodes use incompatible project roots.", tuple(sorted(nodes_by_id)), "Split the family or supply evidence for a single compatible project root."))
    conflicts: dict[tuple[str, RelationType], set[str]] = defaultdict(set)
    for relation in manifest.relations:
        if relation.relation_type in PARENT_LIKE_RELATIONS and not relation.is_display_only:
            conflicts[(relation.source_id, relation.relation_type)].add(relation.target_id)
    for (source, relation_type), targets in conflicts.items():
        if len(targets) > 1:
            blockers.append(Blocker("conflicting_membership", f"Task {source} has conflicting {relation_type.value} parents: {', '.join(sorted(targets))}.", (source, *sorted(targets))))
    cycles = _cycle_nodes(manifest.relations)
    if cycles:
        blockers.append(Blocker("parent_relation_cycle", f"Parent-like task relations contain a cycle at: {', '.join(cycles)}.", cycles))
    return FamilyGraph(manifest, roots, _roles(manifest.nodes, manifest.relations, roots), tuple(blockers))


def rename_mapping(graph: FamilyGraph) -> tuple[TitleRename, ...]:
    """Return stable title display changes; source titles are never identity keys."""
    changes: list[TitleRename] = []
    for node in sorted(graph.manifest.nodes, key=lambda item: item.task_id):
        roles = graph.roles_by_task[node.task_id]
        suffix = ", ".join(roles)
        managed_suffix = re.compile(r" \[(?:Lead|Worker|Reviewer|Handoff|Replacement|Generation \d+)(?:, (?:Lead|Worker|Reviewer|Handoff|Replacement|Generation \d+))*\]$")
        base_title = managed_suffix.sub("", node.title)
        new_title = f"{base_title} [{suffix}]" if suffix else base_title
        changes.append(TitleRename(node.task_id, node.title, new_title, roles))
    return tuple(changes)
