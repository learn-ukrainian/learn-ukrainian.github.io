"""Fail-closed candidate selection for #8506, independent of workflow routing.

The former workflow classifier was retired by #9259. Only the requested Python
selection helper is reintroduced here; current CI continues to run its full
suite. A driver must establish rollout proof before wiring this into CI.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path, PurePosixPath

from scripts.ci.test_impact import ROOT, ImportGraph, build_graph, is_test_file

# The current partition/reuse tests supersede the retired shard-partition file.
SAFETY_NET = "tests/test_ci_split.py"
# Leave room for the complete repo_wide safety baseline plus targeted tests.
# Selection still fails closed before it approaches the full repository suite.
SELECTED_CANDIDATE_CEILING = 200


def hits_shared_root_denylist(path: str) -> bool:
    """Preserve the retired selector's shared configuration and code barriers."""
    name = PurePosixPath(path).name
    if path.startswith((".github/", "scripts/ci/", "scripts/config/", "scripts/build/")):
        return True
    if path == "scripts/__init__.py":
        return True
    if path.startswith("scripts/audit/") and path.endswith(".json") and path.count("/") == 2:
        return True
    if name in {"conftest.py", "pytest.ini", "setup.cfg", "tox.ini"}:
        return True
    if path in {"pyproject.toml", "uv.lock", "requirements.lock", ".python-version"}:
        return True
    if name.startswith("requirements") and name.endswith(".txt"):
        return True
    if path.startswith(("packages/", "schemas/", "site/", "curriculum/")):
        return True
    if path.startswith("tests/") and not is_test_file(path):
        return True
    return path.startswith("docs/") and path.endswith(".yaml")


def _stem_map_tests(stem: str, tree: Iterable[str]) -> set[str]:
    variants = {stem, stem.lower()}
    return {
        path for path in tree if is_test_file(path)
        and any(
            PurePosixPath(path).name == f"test_{variant}.py"
            or PurePosixPath(path).name.startswith(f"test_{variant}_")
            for variant in variants if variant
        )
    }


def build_selected_candidates(
    paths: Sequence[str], tree: Iterable[str], *,
    repo_root: Path = ROOT, impact_graph: ImportGraph | None = None,
) -> list[str] | None:
    """Union stem matches, transitive graph tests and safety tests; None is FULL.

    A stem match cannot excuse an unresolved graph or a module without actual
    test dependents. Missing/renamed-away sources, deleted tests, ambiguous
    stems, shared roots, unavailable safety tests and the ceiling stay FULL.
    """
    tree_set = set(tree)
    stems: dict[str, set[str]] = defaultdict(set)
    for path in tree_set:
        if path.startswith("scripts/") and path.endswith(".py"):
            stems[PurePosixPath(path).stem].add(path)
    candidates: set[str] = set()
    changed_scripts: set[str] = set()
    for raw in paths:
        path = raw.replace("\\", "/")
        if hits_shared_root_denylist(path) or path not in tree_set:
            return None
        if is_test_file(path):
            candidates.add(path)
        elif path.startswith("scripts/") and path.endswith(".py"):
            if len(stems[PurePosixPath(path).stem]) > 1:
                return None
            changed_scripts.add(path)
            candidates.update(_stem_map_tests(PurePosixPath(path).stem, tree_set))
        else:
            return None
    if not candidates and not changed_scripts:
        return None
    graph = impact_graph if impact_graph is not None else build_graph(repo_root)
    if graph.reasons:
        return None
    if changed_scripts:
        impact = graph.impacted_tests(changed_scripts)
        if impact["full_suite"]:
            return None
        candidates.update(impact["tests"])
    # Test-only changes may import other test files; include those dependents.
    candidates.update(graph.test_dependents(candidates))
    # Opaque test entry points can load changed code without a visible edge.
    # Select their consumers even for a test-only change.
    candidates.update(graph.uncertain_tests())
    if graph.selection_reasons(paths):
        return None
    candidates.update(graph.safety_tests)
    candidates.add(SAFETY_NET)
    if not candidates <= tree_set or len(candidates) >= SELECTED_CANDIDATE_CEILING:
        return None
    return sorted(candidates)
