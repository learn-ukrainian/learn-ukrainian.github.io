"""Post-merge issue handling through typed publishing and Fleet authority."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.orchestration import postmerge_criteria as pc

pytestmark = pytest.mark.usefixtures("github_command_boundary")

OWNED = "- [ ] AC-01: After merge, review receipts; owner: codex-devops; due: 2026-11-20"
UNOWNED = "- [ ] AC-02: Unit tests pass"


@pytest.mark.parametrize("field,owner", [
    ("owner: `codex-devops`", "codex-devops"),
    ("**owner:** codex-devops", "codex-devops"),
    ("owner: codex-devops.", "codex-devops"),
    ("co-owner: codex-devops", None),
])
def test_owner_markdown_and_label_boundary(field, owner):
    assert pc.item_assignment(f"{field}; due: 2026-11-20") == (owner, "2026-11-20")


@pytest.fixture
def transport(monkeypatch):
    pr = {"state": "MERGED", "url": "https://github.com/unit/public/pull/3", "body": "Closes #7",
          "closingIssuesReferences": [{"url": "https://github.com/unit/public/issues/7"}]}
    issue = {"state": "closed", "body": OWNED + "\n" + UNOWNED}
    comments = []
    mutations = []
    requests = {}
    authority = Mock()
    authority.__enter__ = Mock(return_value=authority)
    authority.__exit__ = Mock(return_value=False)

    def enqueue(**fields):
        key = fields["idempotency_key"]
        assert key not in requests or requests[key] == fields
        requests[key] = fields

    authority.enqueue_supervisory_request.side_effect = enqueue
    factory = Mock(return_value=authority)

    def read(operation, **fields):
        data = issue if operation == "issue" else [comments[:1], comments[1:]]
        if operation == "comments":
            assert fields["paginate"] and fields["slurp"]
        return SimpleNamespace(stdout=json.dumps(data))

    def publish(verb, **fields):
        mutations.append((verb, fields))
        if verb == "issue-reopen":
            issue["state"] = "open"
        elif verb == "issue-comment":
            comments.append({"body": fields["body"]})
        else:
            pytest.fail(f"unexpected mutation {verb}")

    monkeypatch.setattr(pc.github_client, "check_output", lambda *a, **k: json.dumps(pr))
    monkeypatch.setattr(pc, "read", read)
    monkeypatch.setattr(pc, "publish", publish)
    monkeypatch.setattr(pc, "AuthorityService", factory)
    return SimpleNamespace(pr=pr, issue=issue, comments=comments, mutations=mutations,
                           requests=requests, factory=factory, authority=authority)


def test_reopen_list_and_escalate(transport):
    result = pc.run_postmerge_criteria(3, apply=True)
    assert result["ok"] is False
    assert len(result["issues"]) == 1
    assert [verb for verb, _ in transport.mutations] == ["issue-reopen", "issue-comment"]
    assert transport.issue["state"] == "open"
    comment = transport.comments[0]["body"]
    assert OWNED in comment
    assert "AC-02: Unit tests pass | owner: MISSING | due: MISSING" in comment
    request = next(iter(transport.requests.values()))
    assert request["recipient"] == "claude-cto"
    assert "AC-02" in request["body"] and "AC-01" not in request["body"]
    transport.factory.assert_called_once_with(root=None)


def test_repeat_is_idempotent(transport):
    pc.run_postmerge_criteria(3, apply=True)
    pc.run_postmerge_criteria(3, apply=True)
    assert len(transport.comments) == 1
    assert len(transport.requests) == 1
    assert transport.authority.enqueue_supervisory_request.call_count == 2
    transport.issue["body"] += "\n- [ ] AC-03: More proof"
    pc.run_postmerge_criteria(3, apply=True)
    assert len(transport.requests) == 2


def test_real_authority_deduplicates_across_retries(transport, monkeypatch, tmp_path):
    from scripts.fleet_comms.authority import AuthorityService

    root = tmp_path / "plane"
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))
    monkeypatch.setattr(pc, "AuthorityService", AuthorityService)
    pc.run_postmerge_criteria(3, apply=True)
    transport.issue["body"] = UNOWNED + "\n" + OWNED
    transport.pr["url"] = "https://github.com/unit/public/pull/4"
    pc.run_postmerge_criteria(4, apply=True)
    with AuthorityService(root=root) as authority:
        delivery = authority.claim_next_delivery("claude-cto", "test-owner")
        assert delivery is not None
        message = authority.get_message(delivery.delivery.message_id)
        assert message.kind == "supervisory-request"
        assert message.sender == "codex-devops"
        assert authority.claim_next_delivery("claude-cto", "test-owner") is None


def test_dry_run_has_no_side_effects(transport):
    result = pc.run_postmerge_criteria(3)
    assert result["ok"] is False
    assert result["issues"][0]["missing_assignment"] == ["AC-02"]
    assert not transport.mutations
    transport.factory.assert_not_called()


@pytest.mark.parametrize("body", [OWNED.replace("[ ]", "[x]"), "No acceptance items"])
def test_no_unchecked_items_leave_closed_issue_alone(transport, body):
    transport.issue["body"] = body
    assert pc.run_postmerge_criteria(3, apply=True)["ok"] is True
    assert not transport.mutations
    transport.factory.assert_not_called()


def test_owned_open_item_needs_no_escalation(transport):
    transport.issue.update(body=OWNED, state="open")
    result = pc.run_postmerge_criteria(3, apply=True)
    assert result["ok"] is False
    assert [verb for verb, _ in transport.mutations] == ["issue-comment"]
    transport.factory.assert_not_called()


def test_invalid_date_escalates(transport):
    transport.issue["body"] = OWNED.replace("2026-11-20", "2026-02-30")
    pc.run_postmerge_criteria(3, apply=True)
    assert len(transport.requests) == 1
    assert "due: MISSING" in transport.comments[0]["body"]


def test_examples_not_outstanding(transport):
    transport.issue["body"] = OWNED.replace("[ ]", "[X]") + "\n```\n" + UNOWNED + "\n```\n> " + UNOWNED
    assert pc.run_postmerge_criteria(3, apply=True)["ok"] is True
    assert not transport.mutations


def test_item_set_order_does_not_change_escalation(transport):
    transport.issue["body"] = UNOWNED + "\n- [ ] AC-03: More evidence"
    pc.run_postmerge_criteria(3, apply=True)
    transport.issue["body"] = "- [ ] AC-03: More evidence\n" + UNOWNED
    pc.run_postmerge_criteria(3, apply=True)
    assert len(transport.requests) == 1
    assert len(transport.comments) == 1


def test_closing_references_and_body():
    pr = {"body": "Closes #7\nFixes other/repo#9\nMentions #10\n> Closes #11\n```\nCloses #12\n```",
          "closingIssuesReferences": [{"url": "https://github.com/unit/public/issues/8"}]}
    assert pc.closing_issues(pr, "unit/public") == [("other/repo", 9), ("unit/public", 7), ("unit/public", 8)]


@pytest.mark.parametrize("body,expected", [
    ("Closes #7, #8", [("unit/public", 7), ("unit/public", 8)]),
    ("Fixes #7,#8 and #9", [("unit/public", 7), ("unit/public", 8), ("unit/public", 9)]),
    ("Resolves #7, other/repo#9, and #8", [("other/repo", 9), ("unit/public", 7), ("unit/public", 8)]),
    ("Closes #7 & #8; related #10\nMentions #11", [("unit/public", 7), ("unit/public", 8)]),
])
def test_multiple_closing_references(body, expected):
    pr = {"body": body, "closingIssuesReferences": [{"url": "https://github.com/unit/public/issues/8"}]}
    assert pc.closing_issues(pr, "unit/public") == expected


@pytest.mark.parametrize("state", ["OPEN", "CLOSED"])
def test_unmerged_pr_rejected(transport, state):
    transport.pr["state"] = state
    with pytest.raises(ValueError, match="MERGED"):
        pc.run_postmerge_criteria(3, apply=True)
    assert not transport.mutations


@pytest.mark.parametrize("state", ["missing", None])
def test_unread_issue_state_rejected(transport, state):
    transport.issue["state"] = state
    with pytest.raises(ValueError, match="state unavailable"):
        pc.run_postmerge_criteria(3, apply=True)
    assert not transport.mutations


def test_malformed_criteria_fail_closed(transport):
    transport.issue["body"] = OWNED + "\n" + OWNED
    with pytest.raises(ValueError, match="duplicate"):
        pc.run_postmerge_criteria(3, apply=True)
    assert not transport.mutations


def test_write_failure_reported(transport, monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise RuntimeError("write refused")
    monkeypatch.setattr(pc, "publish", fail)
    assert pc.main(["--pr", "3", "--apply"]) == 2
    assert json.loads(capsys.readouterr().out) == {"ok": False, "error": "write refused"}


def test_cli_status(transport, capsys):
    assert pc.main(["--pr", "3"]) == 1
    assert json.loads(capsys.readouterr().out)["apply"] is False
    transport.issue["body"] = OWNED.replace("[ ]", "[x]")
    assert pc.main(["--pr", "3", "--apply"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        pc.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert all(value in help_text for value in ["--pr", "--apply", "Outputs:", "Exit codes:", "Related:"])
