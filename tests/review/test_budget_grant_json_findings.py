"""Elevated budget grants read schema-bound ``code-review-findings.v1`` recorded verdicts (#12549)."""

from __future__ import annotations

import copy
import json

import pytest

from scripts.review import record_cf_verdict as recorder
from scripts.review.budget_grant import open_blocker_cited, recorded_reply
from scripts.review.verdict_parser import finding_entries

SHA = "a" * 40
LOGIN = "fleet"
STAMP = "2026-11-02T15:23:32Z"


def _finding(**changes: object) -> dict[str, object]:
    finding = {
        "id": "F4",
        "title": "[P1] Persist backup ancestry when retrying failed setup",
        "body": "F4 remains an in_scope_blocker: a retry skips every ancestor fsync.",
        "priority": "P1",
        "confidence": 0.97,
        "category": "security",
        "location": {"path": "scripts/fleet_comms/artifacts.py", "start_line": 991, "end_line": 994,
                     "claim_type": "present"},
        "verbatim": "created = backup_dir",
        "why_wrong": "Directory existence does not prove its parent entry was persisted.",
        "smallest_fix": "Sync the backup parent chain on every apply.",
        "sources": ["scripts/fleet_comms/artifacts.py:985-994"],
    }
    finding.update(changes)
    return finding


def _reply(*findings: dict[str, object]) -> str:
    return json.dumps({
        "schema_version": "code-review-findings.v1",
        "overall": {"correctness": "incorrect", "explanation": "F4 remains open.", "confidence": 0.97},
        "findings": list(findings),
    })


def _comments(reply: str, *, verdict: str = "CHANGES_REQUESTED") -> list[dict[str, object]]:
    body = recorder.build_comment(
        sha=SHA, task_id="review-12534-r3", started="2026-11-02T15:19:08.231750+00:00", verdict=verdict,
        model="gpt-6.1-sol", family="openai", reply=reply,
    )
    return [{"id": 1, "body": body, "user": {"login": LOGIN}, "author_association": "OWNER",
             "created_at": STAMP, "updated_at": STAMP}]


def test_open_p1_json_finding_admits() -> None:
    comments = _comments(_reply(_finding()))
    assert finding_entries(recorded_reply(comments[0]["body"]), "F4") == [
        ("P1", "[P1] Persist backup ancestry when retrying failed setup\n"
               "F4 remains an in_scope_blocker: a retry skips every ancestor fsync.")
    ]
    assert open_blocker_cited(comments, LOGIN, "F4") == SHA


def test_whole_fenced_json_reply_admits() -> None:
    comments = _comments("```json\n" + _reply(_finding()) + "\n```")
    assert open_blocker_cited(comments, LOGIN, "F4") == SHA


@pytest.mark.parametrize(
    "reply",
    [
        pytest.param(_reply(_finding(priority="P2")), id="p2"),
        pytest.param(_reply(_finding(id="F5")), id="absent"),
        pytest.param(_reply(), id="no-findings"),
        pytest.param(_reply(_finding(body="F4 is fixed at this head; only the retry note remains.")), id="closed"),
        pytest.param(_reply(_finding())[:-2], id="truncated-json"),
        pytest.param(_reply(_finding()).replace('"priority": "P1"', '"priority": "P1", "priority": "P1"'),
                     id="duplicate-key"),
        pytest.param(_reply(_finding(priority="high")), id="schema-invalid"),
        pytest.param(_reply(_finding()).replace("code-review-findings.v1", "code-review-findings.v0"),
                     id="wrong-schema"),
        pytest.param(_reply(_finding()) + "\nF4 [P1] still open: retry skips fsync.", id="ledger-after-json"),
    ],
)
def test_json_reply_refuses_without_an_open_p1(reply: str) -> None:
    assert open_blocker_cited(_comments(reply), LOGIN, "F4") is None


def test_trust_rules_still_refuse_a_json_reply() -> None:
    reply = _reply(_finding())
    edited = _comments(reply)
    edited[0]["updated_at"] = "2026-11-02T15:30:00Z"
    untrusted = _comments(reply)
    untrusted[0]["author_association"] = "CONTRIBUTOR"
    approved = _comments(reply, verdict="APPROVED")
    for comments in (edited, untrusted, approved):
        assert open_blocker_cited(comments, LOGIN, "F4") is None


def test_markdown_ledger_reply_still_admits() -> None:
    comments = _comments("VERDICT: REQUEST_CHANGES\nF4 [P1] still open: retry skips fsync.\nSCORE: 4/10")
    assert open_blocker_cited(comments, LOGIN, "F4") == SHA
    closed = copy.deepcopy(comments)
    closed[0]["body"] = closed[0]["body"].replace("still open: retry skips fsync.", "resolved at this head.")
    assert open_blocker_cited(closed, LOGIN, "F4") is None
