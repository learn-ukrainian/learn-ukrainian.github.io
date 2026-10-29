"""pr-merge scans the squash subject and body GitHub will publish (#9339); synthetic data, no network."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.opsec import prepublish as gate
from scripts.publish import github as pub
from tests.opsec_fixtures import CATALOG, TOKEN

HEAD = "a" * 40


@pytest.fixture(autouse=True)
def catalog(monkeypatch):
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)


def transport(calls, *, subject="clean (#1)", body="* clean", queue=False, head=HEAD):
    """Answer readiness and squash-text reads; record only the merge write."""

    queued = False

    def send(args, **kwargs):
        nonlocal queued
        if args[:3] == ["gh", "pr", "view"]:
            assert "isInMergeQueue" not in args[args.index("--json") + 1].split(",")
            return subprocess.CompletedProcess(
                args, 0, json.dumps({"number": 1, "isDraft": False, "headRefOid": HEAD, "state": "OPEN",
                                    "baseRefName": "main", "isCrossRepository": False, "headRefName": "codex/fixture"}), ""
            )
        if args[:3] == ["gh", "pr", "checks"]:
            return subprocess.CompletedProcess(args, 0, "[]", "")
        if args[:5] == ["gh", "api", "--method", "POST", "graphql"]:
            if "mergeQueueEntry" in Path(args[6]).read_text():
                pull = {"number": 1, "state": "OPEN", "headRefOid": HEAD,
                        "headRefName": "codex/fixture", "isInMergeQueue": queued}
                return subprocess.CompletedProcess(args, 0, json.dumps({"data": {"repository": {"pullRequest": pull}}}), "")
            assert "viewerMergeBodyText(mergeType:SQUASH)" in Path(args[6]).read_text()
            pull = {
                "headRefOid": head,
                "isMergeQueueEnabled": queue,
                "viewerMergeHeadlineText": subject,
                "viewerMergeBodyText": body,
            }
            return subprocess.CompletedProcess(args, 0, json.dumps({"data": {"repository": {"pullRequest": pull}}}), "")
        assert args[:3] == ["gh", "pr", "merge"]
        queued = True
        calls.append({"argv": args, "body": Path(args[args.index("--body-file") + 1]).read_text()})
        return subprocess.CompletedProcess(args, 0, "", "")

    return send


@pytest.mark.parametrize(
    "field,defaults", [("subject", {"subject": TOKEN + " (#1)"}), ("body", {"body": "* " + TOKEN})]
)
def test_default_squash_text_hit_is_refused_before_merge(synthetic_opsec, field, defaults):
    calls = []
    with pytest.raises(gate.PublishBlocked) as error:
        pub.publish("pr-merge", repo="unit/public", number=1, runner=transport(calls, **defaults))
    assert not calls and TOKEN not in str(error.value)
    assert f"rule=synthetic-rule class=1 field={field} line=1" in str(error.value)


@pytest.mark.parametrize("field", ["subject", "body"])
def test_explicit_squash_text_hit_is_refused_before_merge(synthetic_opsec, field):
    calls = []
    with pytest.raises(gate.PublishBlocked, match=f"field={field} "):
        pub.publish("pr-merge", repo="unit/public", number=1, runner=transport(calls), **{field: "x " + TOKEN})
    assert not calls


def test_clean_defaults_are_sent_explicitly_as_scanned(synthetic_opsec):
    calls = []
    pub.publish("pr-merge", repo="unit/public", number=1, runner=transport(calls, body="* clean\n* also clean"))
    assert len(calls) == 1
    argv = calls[0]["argv"]
    assert "--squash" in argv and "--subject=clean (#1)" in argv and f"--match-head-commit={HEAD}" in argv
    assert calls[0]["body"] == "* clean\n* also clean"


def test_merge_queue_defaults_are_scanned_even_with_explicit_text(synthetic_opsec):
    calls = []
    with pytest.raises(gate.PublishBlocked, match="field=default_body "):
        pub.publish(
            "pr-merge",
            repo="unit/public",
            number=1,
            subject="clean",
            body="clean",
            runner=transport(calls, body="* " + TOKEN, queue=True),
        )
    assert not calls


def test_direct_merge_sends_explicit_text_instead_of_defaults(synthetic_opsec):
    calls = []
    pub.publish(
        "pr-merge",
        repo="unit/public",
        number=1,
        subject="clean",
        body="clean",
        runner=transport(calls, body="* " + TOKEN, queue=False),
    )
    assert len(calls) == 1 and "--subject=clean" in calls[0]["argv"] and calls[0]["body"] == "clean"


@pytest.mark.parametrize(
    "overrides",
    [{"head": "b" * 40}, {"subject": None}, {"body": 7}, {"queue": "yes"}],
)
def test_unverifiable_squash_text_is_refused(synthetic_opsec, overrides):
    calls = []
    with pytest.raises(gate.PublishBlocked, match="squash text unverifiable"):
        pub.publish("pr-merge", repo="unit/public", number=1, runner=transport(calls, **overrides))
    assert not calls


def test_missing_matcher_fails_closed_for_default_text(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "private_tooling", lambda: tmp_path / "absent")
    calls = []
    with pytest.raises(gate.PublishBlocked, match="unavailable"):
        pub.publish("pr-merge", repo="unit/public", number=1, runner=transport(calls))
    assert not calls


def test_override_is_logged_and_single_use(synthetic_opsec, tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "primary_root", lambda cwd=None: tmp_path)
    calls = []
    env = {"LU_OPSEC_OVERRIDE": "synthetic false positive"}
    pub.publish(
        "pr-merge", repo="unit/public", number=1, env=dict(env), runner=transport(calls, subject=TOKEN + " (#1)")
    )
    assert len(calls) == 1
    log = tmp_path / "batch_state/opsec/overrides.jsonl"
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["rule_ids"] == ["synthetic-rule"] and TOKEN not in log.read_text()
    with pytest.raises(gate.PublishBlocked, match="override already consumed"):
        pub.publish(
            "pr-merge", repo="unit/public", number=1, env=dict(env), runner=transport(calls, subject=TOKEN + " (#1)")
        )
    assert len(calls) == 1


def priority_transport(calls, *, labels, timeline):
    """A queue repository with one recorded approval of HEAD; records either enqueue write."""
    base = transport(calls, queue=True)
    marker = (
        f"### Cross-family review\nhead: {HEAD}\nReviewer family: openai\nVERDICT: APPROVED\n"
        "Reviewer model: gpt-6.1-sol\nTask id: review-one\n\n"
        f"<!-- cf-verdict v1 sha={HEAD} task=review-one started=2026-10-29T10:00:00.000001+00:00 "
        "verdict=APPROVED model=gpt-6.1-sol family=openai -->"
    )
    approval = {"id": 1, "body": marker, "user": {"login": "fleet"}, "author_association": "OWNER",
                "created_at": "2026-10-29T10:05:00Z", "updated_at": "2026-10-29T10:05:00Z"}
    pages = {"/comments": [[approval]], "/timeline": [timeline]}

    def send(args, **kwargs):
        if args[:3] == ["gh", "pr", "view"] and "labels" in args[args.index("--json") + 1]:
            return subprocess.CompletedProcess(args, 0, json.dumps({
                "id": "PR_node", "headRefOid": HEAD, "isCrossRepository": False, "baseRefName": "main",
                "labels": [{"name": name} for name in labels],
            }), "")
        if args[:4] == ["gh", "api", "--method", "GET"]:
            if args[4].startswith("user"):
                return subprocess.CompletedProcess(args, 0, json.dumps({"login": "fleet"}), "")
            page = next(value for key, value in pages.items() if key + "?" in args[4])
            return subprocess.CompletedProcess(args, 0, json.dumps(page), "")
        if args[:5] == ["gh", "api", "--method", "POST", "graphql"]:
            document = json.loads(Path(args[6]).read_text())
            if "enqueuePullRequest" in document["query"]:
                calls.append({"argv": args, "jump": "jump:true" in document["query"], "variables": document["variables"]})
                return subprocess.CompletedProcess(args, 0, "{}", "")
        return base(args, **kwargs)

    return send


def labeled(at):
    return {"event": "labeled", "label": {"name": "merge-priority"}, "actor": {"login": "fleet"}, "created_at": at}


def test_labelled_approved_pr_is_enqueued_with_jump(synthetic_opsec):
    calls = []
    result = pub.publish("pr-merge", repo="unit/public", number=1, match_head=HEAD,
                         runner=priority_transport(calls, labels=["merge-priority"],
                                                   timeline=[labeled("2026-10-29T10:10:00Z")]))
    assert calls == [{"argv": calls[0]["argv"], "jump": True, "variables": {"id": "PR_node", "head": HEAD}}]
    assert result.queue_jump is True


def test_unlabelled_pr_is_enqueued_without_jump(synthetic_opsec):
    calls = []
    result = pub.publish("pr-merge", repo="unit/public", number=1, match_head=HEAD,
                         runner=priority_transport(calls, labels=[], timeline=[]))
    assert len(calls) == 1 and calls[0]["argv"][:3] == ["gh", "pr", "merge"]
    assert not getattr(result, "queue_jump", False)


def test_label_applied_after_an_earlier_heads_approval_does_not_jump(synthetic_opsec):
    """Labelled after approving an old head; this head's approval came later, so the label predates it."""
    calls = []
    old_head_label = labeled("2026-10-29T10:03:00Z")
    result = pub.publish("pr-merge", repo="unit/public", number=1, match_head=HEAD,
                         runner=priority_transport(calls, labels=["merge-priority"], timeline=[old_head_label]))
    assert len(calls) == 1 and calls[0]["argv"][:3] == ["gh", "pr", "merge"]
    assert not getattr(result, "queue_jump", False)
