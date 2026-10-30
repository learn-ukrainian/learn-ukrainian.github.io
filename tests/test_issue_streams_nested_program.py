"""Closed infra-harness roots stay registered and are not audit roots.

infra-harness still lists #6943, #9737 and #11254 so launcher selectors
resolve, and records them in ``closed_epics``. The audit and the lifecycle
membership reader omit them. When that closed tree is a native descendant of
the live epics root #10453, each descendant resolves to #10453 exactly once.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from scripts.orchestration import task_lifecycle
from scripts.orchestration.issue_stream_audit import (
    _tree_membership,
    classify,
    load_registry,
    make_issue_resolver,
    make_membership_resolver,
)
from scripts.orchestration.task_closeout import GhGitHubAdapter

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "scripts" / "config" / "issue_streams.yaml"
STREAM = "infra-harness"
LIVE = 10453
PARENT, PROGRAM, OVERFLOW = 6943, 9737, 11254
CHILD = 9739
CLOSED = (4215, 5535, 5703, 6943, 7919, 9737, 10844, 11254)


def _page(nodes):
    return {
        "body": "",
        "subIssues": {
            "nodes": [{"number": n} for n in nodes],
            "pageInfo": {"hasNextPage": False, "endCursor": None},
        },
    }


def _audit_report(edges: dict[int, list[int]], open_numbers: list[int]) -> dict:
    """Run the real tree traversal + classifier over the real registry (every epic open)."""
    registry = load_registry(REGISTRY_PATH, audit_only=True)
    roots = {epic for epics in registry.values() for epic in epics}

    def fetch_batch(cursors):
        return {number: _page(edges.get(number, [])) for number in cursors}

    membership = _tree_membership(roots, fetch_batch)
    issues = [{"number": n, "title": f"issue {n}"} for n in sorted(set(open_numbers) | roots)]
    report = classify(issues, registry, membership)
    report["repository"] = "org/repo"
    return report


def test_registry_lists_both_epics_in_one_stream_and_no_epic_in_two_streams():
    registry = load_registry(REGISTRY_PATH)
    assert registry[STREAM] == [PARENT, PROGRAM, OVERFLOW]
    assert registry["docs-knowledge"] == [5535]
    assert registry["devops"] == [5703, 10844]
    assert registry["monitor"] == [7919]
    assert registry["seminars-bio"] == [4431, 4215]
    assert registry["epics"] == [LIVE]
    audit = load_registry(REGISTRY_PATH, audit_only=True)
    assert STREAM not in audit
    assert "docs-knowledge" not in audit
    assert "devops" not in audit
    assert "monitor" not in audit
    assert audit["seminars-bio"] == [4431]
    assert audit["epics"] == [LIVE]
    audit_roots = {epic for epics in audit.values() for epic in epics}
    assert set(CLOSED).isdisjoint(audit_roots)
    all_epics = [epic for epics in registry.values() for epic in epics]
    assert len(all_epics) == len(set(all_epics))


def test_audit_assigns_program_child_to_exactly_one_epic_and_stream():
    edges = {LIVE: [PARENT], PARENT: [PROGRAM, 9000], PROGRAM: [CHILD], 9000: []}
    report = _audit_report(edges, [PARENT, PROGRAM, CHILD, 9000])

    assert report["multi_homed"] == []
    assert report["orphans"] == []
    assert report["ok"] is True
    for number in (PARENT, PROGRAM, CHILD, 9000):
        assert report["effective_membership"][str(number)] == {
            "epics": [LIVE],
            "streams": ["epics"],
            "via": "native",
            "unique_stream": True,
        }


def test_membership_and_issue_resolvers_accept_program_child_only_under_its_epic():
    report = _audit_report({LIVE: [PARENT], PARENT: [PROGRAM], PROGRAM: [CHILD]}, [PARENT, PROGRAM, CHILD])
    report["generated_at"] = int(time.time())

    resolve = make_membership_resolver(report)
    assert resolve(CHILD, LIVE) is True
    assert resolve(CHILD, PARENT) is False
    assert resolve(CHILD, PROGRAM) is False
    assert make_issue_resolver(report)(str(CHILD)) is True


def test_lifecycle_resolves_program_child_to_registered_epic_natively():
    registered = GhGitHubAdapter(ROOT).registered_stream_epics()
    assert LIVE in registered
    assert PARENT not in registered and PROGRAM not in registered
    report = _audit_report({LIVE: [PARENT], PARENT: [CHILD]}, [PARENT, CHILD])
    report["generated_at"] = time.time()

    result = task_lifecycle.resolve_membership(
        issue_number=CHILD,
        stream_epic=LIVE,
        native_parent_epic=PARENT,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=registered,
        membership_report=report,
    )
    assert result["valid"] is True and result["method"] == "native_chain" and result["epic"] == LIVE

    # A closed root is not a membership root, so a claim under it is refused.
    wrong = task_lifecycle.resolve_membership(
        issue_number=CHILD,
        stream_epic=PARENT,
        native_parent_epic=PARENT,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=registered,
        membership_report=report,
    )
    assert wrong["valid"] is False


def test_lifecycle_resolves_program_child_through_audit_body_evidence():
    report = _audit_report({LIVE: [PARENT], PARENT: [PROGRAM]}, [PARENT, PROGRAM, CHILD])
    report["generated_at"] = time.time()
    report["effective_membership"][str(CHILD)] = {
        "epics": [LIVE],
        "streams": ["epics"],
        "via": "body",
        "unique_stream": True,
    }
    registered = GhGitHubAdapter(ROOT).registered_stream_epics()
    other_epic = next(epic for epic in registered if epic != LIVE)

    ok = task_lifecycle.resolve_membership(
        issue_number=CHILD,
        stream_epic=LIVE,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=registered,
        membership_report=report,
    )
    assert ok["valid"] is True and ok["method"] == "body" and ok["epic"] == LIVE

    other = task_lifecycle.resolve_membership(
        issue_number=CHILD,
        stream_epic=other_epic,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=registered,
        membership_report=report,
    )
    assert other["valid"] is False


SUB_EPIC, GRANDCHILD = 8647, 9757  # unregistered sub-epic of #6943 and its child (#9783)


def _registered() -> list[int]:
    return sorted({e for epics in load_registry(REGISTRY_PATH).values() for e in epics})


def test_lifecycle_accepts_native_grandchild_through_unregistered_sub_epic():
    registered = _registered()
    assert SUB_EPIC not in registered
    report = _audit_report(
        {LIVE: [PARENT], PARENT: [SUB_EPIC], SUB_EPIC: [GRANDCHILD]},
        [PARENT, PROGRAM, SUB_EPIC, GRANDCHILD],
    )
    report["generated_at"] = time.time()
    assert report["effective_membership"][str(GRANDCHILD)] == {
        "epics": [LIVE],
        "streams": ["epics"],
        "via": "native",
        "unique_stream": True,
    }

    ok = task_lifecycle.resolve_membership(
        issue_number=GRANDCHILD,
        stream_epic=LIVE,
        native_parent_epic=SUB_EPIC,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=registered,
        membership_report=report,
    )
    assert ok["valid"] is True and ok["method"] == "native_chain" and ok["epic"] == LIVE
    assert ok["generated_at"] == report["generated_at"]
    assert ok["digest"] == task_lifecycle.digest(report["effective_membership"])

    # The chain reaches #10453 only; the closed program epic is a different owner.
    other = task_lifecycle.resolve_membership(
        issue_number=GRANDCHILD,
        stream_epic=PROGRAM,
        native_parent_epic=SUB_EPIC,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=registered,
        membership_report=report,
    )
    assert other["valid"] is False and "different registered epic" in other["reason"]


def test_lifecycle_refuses_native_cycle_that_never_reaches_a_registered_epic():
    report = _audit_report({SUB_EPIC: [GRANDCHILD], GRANDCHILD: [SUB_EPIC]}, [PARENT, SUB_EPIC, GRANDCHILD])
    report["generated_at"] = time.time()
    assert str(GRANDCHILD) not in report["effective_membership"]

    result = task_lifecycle.resolve_membership(
        issue_number=GRANDCHILD,
        stream_epic=PARENT,
        native_parent_epic=SUB_EPIC,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=_registered(),
        membership_report=report,
    )
    assert result["valid"] is False and "native sub-issue chain" in result["reason"]


def test_launcher_shell_anchor_is_first_epic():
    script = f'. "{ROOT}/scripts/lib/handoff_identity.sh" && _launcher_stream_anchor_epic {STREAM}'
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True, timeout=30)
    assert result.stdout.strip() == str(PARENT)
