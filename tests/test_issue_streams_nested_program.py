"""Nested program epic #9737 inside the infra-harness stream (#9776).

infra-harness registers two epics, #6943 (the stream epic) and #9737 (a nested
program whose native parent is #6943). Every registry consumer must accept two
epics in one stream, and a #9737 child must resolve to exactly one effective
epic (9737) — never to both, which would be double membership.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from agents_extensions.shared.session_streams.inventory import stream_anchor_id, stream_map
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
PARENT, PROGRAM = 6943, 9737
CHILD = 9739


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
    assert registry[STREAM] == [PARENT, PROGRAM]
    assert load_registry(REGISTRY_PATH, audit_only=True)[STREAM] == [PARENT, PROGRAM]
    all_epics = [epic for epics in registry.values() for epic in epics]
    assert len(all_epics) == len(set(all_epics))


def test_workstreams_mirror_lists_both_epics():
    rows = [
        line
        for line in (ROOT / "docs" / "WORKSTREAMS.md").read_text(encoding="utf-8").splitlines()
        if line.startswith(f"| {STREAM} |") and "Infra & fleet reliability" in line
    ]
    assert len(rows) == 1
    assert f"#{PARENT}" in rows[0] and f"#{PROGRAM}" in rows[0]


def test_audit_assigns_program_child_to_exactly_one_epic_and_stream():
    edges = {PARENT: [PROGRAM, 9000], PROGRAM: [CHILD], 9000: []}
    report = _audit_report(edges, [PARENT, PROGRAM, CHILD, 9000])

    assert report["multi_homed"] == []
    assert report["orphans"] == []
    assert report["ok"] is True
    # Registered epics are exempt from membership; only children are indexed.
    assert str(PROGRAM) not in report["effective_membership"]
    assert report["effective_membership"][str(CHILD)] == {
        "epics": [PROGRAM],
        "streams": [STREAM],
        "via": "native",
        "unique_stream": True,
    }
    assert report["effective_membership"]["9000"]["epics"] == [PARENT]


def test_membership_and_issue_resolvers_accept_program_child_only_under_its_epic():
    report = _audit_report({PARENT: [PROGRAM], PROGRAM: [CHILD]}, [PARENT, PROGRAM, CHILD])
    report["generated_at"] = int(time.time())

    resolve = make_membership_resolver(report)
    assert resolve(CHILD, PROGRAM) is True
    assert resolve(CHILD, PARENT) is False
    assert make_issue_resolver(report)(str(CHILD)) is True


def test_lifecycle_resolves_program_child_to_registered_epic_natively():
    registered = GhGitHubAdapter(ROOT).registered_stream_epics()
    assert PARENT in registered and PROGRAM in registered

    result = task_lifecycle.resolve_membership(
        issue_number=CHILD,
        stream_epic=PROGRAM,
        native_parent_epic=PROGRAM,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=registered,
        membership_report=None,
    )
    assert result["valid"] is True and result["method"] == "native" and result["epic"] == PROGRAM

    # The native parent is authoritative: the same child is not also a #6943 member.
    wrong = task_lifecycle.resolve_membership(
        issue_number=CHILD,
        stream_epic=PARENT,
        native_parent_epic=PROGRAM,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=registered,
        membership_report=None,
    )
    assert wrong["valid"] is False


def test_lifecycle_resolves_program_child_through_audit_body_evidence():
    report = _audit_report({PARENT: [PROGRAM], PROGRAM: []}, [PARENT, PROGRAM, CHILD])
    report["generated_at"] = time.time()
    report["effective_membership"][str(CHILD)] = {
        "epics": [PROGRAM],
        "streams": [STREAM],
        "via": "body",
        "unique_stream": True,
    }
    registered = sorted({e for epics in load_registry(REGISTRY_PATH).values() for e in epics})

    ok = task_lifecycle.resolve_membership(
        issue_number=CHILD,
        stream_epic=PROGRAM,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=registered,
        membership_report=report,
    )
    assert ok["valid"] is True and ok["method"] == "body" and ok["epic"] == PROGRAM

    other = task_lifecycle.resolve_membership(
        issue_number=CHILD,
        stream_epic=PARENT,
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
    report = _audit_report({PARENT: [SUB_EPIC], SUB_EPIC: [GRANDCHILD]}, [PARENT, PROGRAM, SUB_EPIC, GRANDCHILD])
    report["generated_at"] = time.time()
    assert report["effective_membership"][str(GRANDCHILD)]["via"] == "native"

    ok = task_lifecycle.resolve_membership(
        issue_number=GRANDCHILD,
        stream_epic=PARENT,
        native_parent_epic=SUB_EPIC,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=registered,
        membership_report=report,
    )
    assert ok["valid"] is True and ok["method"] == "native_chain" and ok["epic"] == PARENT
    assert ok["generated_at"] == report["generated_at"]
    assert ok["digest"] == task_lifecycle.digest(report["effective_membership"])

    # The chain reaches #6943 only; the nested program epic is a different owner.
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


def test_lifecycle_refuses_chain_that_reaches_a_different_registered_epic():
    """A sub-epic under the nested program #9737 belongs to #9737, never to #6943."""
    report = _audit_report(
        {PARENT: [PROGRAM], PROGRAM: [SUB_EPIC], SUB_EPIC: [GRANDCHILD]},
        [PARENT, PROGRAM, SUB_EPIC, GRANDCHILD],
    )
    report["generated_at"] = time.time()
    assert report["effective_membership"][str(GRANDCHILD)]["epics"] == [PROGRAM]

    wrong = task_lifecycle.resolve_membership(
        issue_number=GRANDCHILD,
        stream_epic=PARENT,
        native_parent_epic=SUB_EPIC,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=_registered(),
        membership_report=report,
    )
    assert wrong["valid"] is False and "different registered epic" in wrong["reason"]


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


def test_session_stream_readers_keep_stream_epic_as_anchor():
    assert stream_map(ROOT)[STREAM] == [PARENT, PROGRAM]
    # The first listed epic stays the launcher/handoff anchor.
    assert stream_anchor_id(STREAM, ROOT).split(":", 1)[1] == str(load_registry(REGISTRY_PATH)[STREAM][0])


def test_launcher_shell_anchor_is_first_epic():
    script = f'. "{ROOT}/scripts/lib/handoff_identity.sh" && _launcher_stream_anchor_epic {STREAM}'
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True, timeout=30)
    assert result.stdout.strip() == str(PARENT)
