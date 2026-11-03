"""Elevated budget grants read schema-bound recorded verdicts by their run's schema (#12549)."""

from __future__ import annotations

import hashlib
import json

import pytest

from scripts.review import record_cf_verdict as recorder
from scripts.review.budget_grant import finding_is_open, open_blocker_cited
from scripts.review.review_contract import SCHEMA_RELATIVE_PATH, package_repo_root
from scripts.review.review_lineage import ReviewRun

SHA = "a" * 40
LOGIN = "fleet"
STAMP = "2026-11-02T15:23:32Z"
TASK = "review-12534-r3"
STARTED = "2026-11-02T15:19:08.231750+00:00"
LEDGER = "VERDICT: REQUEST_CHANGES\nF4 [P1] still open: retry skips fsync.\nSCORE: 4/10"
SCHEMA = {
    "output_schema_path": f"/repo/{SCHEMA_RELATIVE_PATH}",
    "output_schema_sha256": hashlib.sha256((package_repo_root() / SCHEMA_RELATIVE_PATH).read_bytes()).hexdigest(),
}


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


def _comments(reply: str, *, verdict: str = "CHANGES_REQUESTED", withheld: bool = False) -> list[dict[str, object]]:
    body = recorder.build_comment(
        sha=SHA, task_id=TASK, started=STARTED, verdict=verdict, model="gpt-6.1-sol", family="openai", reply=reply,
        withheld_findings=1 if withheld else None,
    )
    return [{"id": 1, "body": body, "user": {"login": LOGIN}, "author_association": "OWNER",
             "created_at": STAMP, "updated_at": STAMP}]


def _run(reply: str | None, *, task: str = TASK, started: str = STARTED, **record: object) -> ReviewRun:
    return ReviewRun(task, {"task_id": task, "started_at": started, **record}, reply)


def _cited(reply: str, run_reply: str | None = None, **record: object) -> str | None:
    """The cited head when the published and sealed replies are ``reply`` and the run is schema-bound."""
    sealed = reply if run_reply is None else run_reply
    return open_blocker_cited(_comments(reply), LOGIN, "F4", [_run(sealed, **{**SCHEMA, **record})])


def test_schema_bound_open_p1_admits() -> None:
    assert _cited(_reply(_finding())) == SHA
    assert _cited("```json\n" + _reply(_finding()) + "\n```") == SHA


def test_hyphenated_compound_is_not_a_closing_word() -> None:
    """A closing word inside a hyphenated compound must not close a still-open finding."""
    for word in ("resolved", "fixed", "declined", "withdrawn", "closed", "addressed", "superseded"):
        standalone = f"F4 still open: the guarantee is broken; {word}."
        assert not finding_is_open(standalone)
        assert _cited(_reply(_finding(body=standalone))) is None
        for compound in (f"fail-{word}", f"{word}-form", f"fail-{word}-form"):
            entry = f"F4 still open: the {compound} guarantee is broken."
            assert finding_is_open(entry), entry
            assert _cited(_reply(_finding(body=entry))) == SHA


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
        pytest.param(_reply(_finding(confidence=float("nan"))), id="nan-constant"),
        pytest.param(_reply(_finding()) + "\n" + LEDGER, id="json-then-ledger"),
        pytest.param("Review follows.\n```json\n{\"findings\": []}\n```\n" + LEDGER, id="prose-fence-ledger"),
        pytest.param('"find\nings": []\n' + LEDGER, id="fragment-then-ledger"),
        pytest.param(LEDGER, id="ledger-only"),
    ],
)
def test_schema_bound_run_never_falls_back_to_the_ledger(reply: str) -> None:
    assert _cited(reply) is None


def test_the_sealed_reply_decides_not_the_published_text() -> None:
    assert _cited(LEDGER, run_reply=_reply(_finding())) == SHA
    assert _cited(_reply(_finding()), run_reply=_reply(_finding(priority="P2"))) is None
    assert open_blocker_cited(_comments(_reply(_finding())), LOGIN, "F4", [_run(None, **SCHEMA)]) is None


@pytest.mark.parametrize(
    "runs",
    [
        pytest.param([], id="missing-run"),
        pytest.param([_run(_reply(_finding()), **SCHEMA), _run(_reply(_finding()), **SCHEMA)], id="ambiguous-run"),
        pytest.param([_run(_reply(_finding()), task="review-other", **SCHEMA)], id="other-task"),
        pytest.param([_run(_reply(_finding()), started="2026-11-02T15:20:00+00:00", **SCHEMA)], id="other-start"),
        pytest.param([_run(_reply(_finding()), **{**SCHEMA, "output_schema_sha256": "0" * 64})], id="schema-digest"),
        pytest.param([_run(_reply(_finding()), **{**SCHEMA, "output_schema_path": "/repo/schemas/other.json"})],
                     id="other-schema"),
    ],
)
def test_an_unbound_or_foreign_schema_run_refuses(runs: list[ReviewRun]) -> None:
    assert open_blocker_cited(_comments(_reply(_finding())), LOGIN, "F4", runs) is None


def test_withheld_and_untrusted_records_still_refuse() -> None:
    run = [_run(_reply(_finding()), **SCHEMA)]
    assert open_blocker_cited(_comments(_reply(_finding()), withheld=True), LOGIN, "F4", run) is None
    edited = _comments(_reply(_finding()))
    edited[0]["updated_at"] = "2026-11-02T15:30:00Z"
    untrusted = _comments(_reply(_finding()))
    untrusted[0]["author_association"] = "CONTRIBUTOR"
    approved = _comments(_reply(_finding()), verdict="APPROVED")
    for comments in (edited, untrusted, approved):
        assert open_blocker_cited(comments, LOGIN, "F4", run) is None


@pytest.mark.parametrize(
    "defect",
    [None, "closed", "unsealed-digest", "truncated-reply", "other-head", "other-count", "ambiguous-run", "no-schema"],
)
def test_withheld_findings_come_from_the_bound_sealed_run(defect: str | None) -> None:
    """A withheld rejection's open P1 is read from the sealed reply of the run it records, and only then (#12592)."""
    sealed = _reply(_finding(body="F4 still open: in_scope_blocker; a retry skips every ancestor fsync.")
                    if defect != "closed" else _finding(body="F4 is fixed at this head."))
    if defect == "truncated-reply":
        sealed += f"\n\n{recorder.TRUNCATION_FLAG}"
    record = {**({} if defect == "no-schema" else SCHEMA), "status": "done", "model": "gpt-6.1-sol", "agent": "codex",
              "worktree_base_sha": "b" * 40 if defect == "other-head" else SHA,
              "result_sha256": None if defect == "unsealed-digest" else hashlib.sha256(sealed.encode()).hexdigest()}
    runs = [_run(sealed, **record)] * (2 if defect == "ambiguous-run" else 1)
    comments = _comments("", withheld=True)
    if defect == "other-count":
        comments[0]["body"] = str(comments[0]["body"]).replace("Withheld findings: 1\n", "Withheld findings: 2\n")
    assert open_blocker_cited(comments, LOGIN, "F4", runs) == (SHA if defect is None else None)


def test_a_run_without_an_output_schema_keeps_the_markdown_ledger() -> None:
    run = [_run(LEDGER)]
    assert open_blocker_cited(_comments(LEDGER), LOGIN, "F4", run) == SHA
    closed = LEDGER.replace("still open: retry skips fsync.", "resolved at this head.")
    assert open_blocker_cited(_comments(closed), LOGIN, "F4", [_run(closed)]) is None
    assert open_blocker_cited(_comments(_reply(_finding())), LOGIN, "F4", [_run(_reply(_finding()))]) is None
