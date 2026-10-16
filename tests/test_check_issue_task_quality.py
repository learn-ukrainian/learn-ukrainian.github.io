"""Tests for scripts/ci/check_issue_task_quality.py (#7854)."""

from __future__ import annotations

import json
import time
from unittest.mock import Mock

import pytest

pytestmark = pytest.mark.usefixtures("github_command_boundary")

from scripts.ci.check_issue_task_quality import main, score_body
from scripts.ci.comment_issue_task_quality import MARKER, reconcile_comments, render_comment

COMPLETE = """
## User-visible outcome
Ship the advisory checker.

## Why / evidence
#7854 audit showed empty DoD cards.

## In scope
`scripts/ci/check_issue_task_quality.py` and issue templates.

## Non-goals
No blocking CI gate.

## Denominator
All templates under .github/ISSUE_TEMPLATE/.

## Verify
```bash
.venv/bin/python scripts/ci/check_issue_task_quality.py --help
```

## Dependencies
none

## Accountable driver
cursor-infra

## Stop policy
If CF CHANGES_REQUESTED: fix on tip and re-CF; owner cursor-infra.

## Residual policy
none

## Review plan
Author family Cursor; CF Claude; backup AGY. Discussion ≠ CF.

## Acceptance Criteria / Definition of Done
- [ ] AC-01: checker WARN when new DoR fields missing
- [ ] AC-02: PR merged with CF + green CI

## Terminal goal
merge

## Residual
none — owner: n/a
"""

HEADINGS_ONLY = """
## User-visible outcome
## Why / evidence
## In scope
## Non-goals
## Denominator
## Verify
## Dependencies
## Accountable driver
## Stop policy
## Residual policy
## Review plan
## Definition of Done
## Terminal goal
## Residual
"""


def test_complete_card_passes() -> None:
    result = score_body(COMPLETE)
    assert result["verdict"] == "PASS"
    assert result["missing"] == []


def test_missing_fields_warn() -> None:
    result = score_body("## Overview\nDo a thing somehow.\n")
    assert result["verdict"] == "WARN"
    assert "non_goals" in result["missing"]
    assert "why" in result["missing"]


def test_headings_only_warns() -> None:
    result = score_body(HEADINGS_ONLY)
    assert result["verdict"] == "WARN"
    assert "outcome" in result["missing"]
    assert "terminal_goal" in result["missing"]


def test_empty_body_warns() -> None:
    result = score_body("")
    assert result["verdict"] == "WARN"
    assert len(result["missing"]) >= 8


def test_trivial_exemption() -> None:
    result = score_body("trivial: yes\nFix typo in README\n", trivial=False)
    assert result["verdict"] == "PASS"
    assert result["trivial"] is True


@pytest.mark.parametrize("first_line", ["trivial:", "trivial: yes", "Trivial: TRUE", "trivial: exempt"])
def test_first_line_trivial_exemption(first_line: str) -> None:
    assert score_body(f"{first_line}\nFix typo in README")["trivial"] is True
    assert main(["--body", f"{first_line}\nFix typo in README", "--strict"]) == 0


@pytest.mark.parametrize("label", ["trivial", "TrIvIaL"])
def test_issue_trivial_label_exemption(label: str, monkeypatch, capsys) -> None:
    payload = {"title": "Fix typo", "body": "Correct spelling", "labels": [{"name": label}]}
    monkeypatch.setattr(
        "scripts.ci.check_issue_task_quality.github_client.check_output",
        lambda *_args, **_kwargs: json.dumps(payload),
    )
    assert (
        main(["--issue", "123", "--repo", "learn-ukrainian/learn-ukrainian-infra-private", "--strict", "--json"]) == 0
    )
    assert json.loads(capsys.readouterr().out)["trivial"] is True
    assert "PASS (trivial exemption)" in render_comment(payload)


def test_issue_first_line_trivial_exemption(monkeypatch, capsys) -> None:
    payload = {"title": "Fix typo", "body": "trivial:\nCorrect spelling", "labels": []}
    monkeypatch.setattr(
        "scripts.ci.check_issue_task_quality.github_client.check_output",
        lambda *_args, **_kwargs: json.dumps(payload),
    )
    assert (
        main(["--issue", "123", "--repo", "learn-ukrainian/learn-ukrainian-infra-private", "--strict", "--json"]) == 0
    )
    assert json.loads(capsys.readouterr().out)["trivial"] is True
    assert "PASS (trivial exemption)" in render_comment(payload)


def test_nontrivial_issue_warns(monkeypatch, capsys) -> None:
    payload = {"title": "trivial:", "body": "Correct spelling", "labels": [{"name": "task"}]}
    monkeypatch.setattr(
        "scripts.ci.check_issue_task_quality.github_client.check_output",
        lambda *_args, **_kwargs: json.dumps(payload),
    )
    assert (
        main(["--issue", "123", "--repo", "learn-ukrainian/learn-ukrainian-infra-private", "--strict", "--json"]) == 1
    )
    assert json.loads(capsys.readouterr().out)["verdict"] == "WARN"
    assert "DoR card check: WARN" in render_comment(payload)


def test_prose_mentioning_trivial_is_not_exempt() -> None:
    result = score_body(
        "## Overview\nDiscusses trivial exempt cases but is not itself trivial.\n",
        trivial=False,
    )
    assert result["trivial"] is False
    assert result["verdict"] == "WARN"


def test_missing_body_file_is_fail_open(tmp_path) -> None:
    missing = tmp_path / "does-not-exist.md"
    code = main(["--body-file", str(missing), "--json"])
    assert code == 0


def test_missing_body_file_strict_fails(tmp_path) -> None:
    missing = tmp_path / "does-not-exist.md"
    code = main(["--body-file", str(missing), "--strict"])
    assert code == 1


def test_empty_tilde_verify_fence_warns() -> None:
    body = COMPLETE.replace(
        "## Verify\n```bash\n.venv/bin/python scripts/ci/check_issue_task_quality.py --help\n```",
        "## Verify\n~~~bash\n~~~\n",
    )
    result = score_body(body)
    assert result["verdict"] == "WARN"
    assert "verify" in result["missing"]


def test_cli_help(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    assert "Advisory" in out or "task-quality" in out or "--issue" in out


def test_dor_workflow_comment_lists_missing_fields_and_updates_one() -> None:
    issue = {"title": "Sparse issue", "body": "x", "labels": []}
    comment = render_comment(issue)
    assert MARKER in comment
    assert "DoR card check: WARN. Missing fields:" in comment
    assert "user-visible outcome / what" in comment
    calls: list[tuple[str, str, object]] = []

    def api(method: str, path: str, data: object = None) -> None:
        calls.append((method, path, data))

    comments = [
        {"id": 1, "body": MARKER + "\nold", "user": {"login": "github-actions[bot]"}},
        {"id": 2, "body": MARKER + "\nduplicate", "user": {"login": "github-actions[bot]"}},
    ]
    reconcile_comments(issue, comments, api, "/issues/123")
    assert calls == [
        ("PATCH", "/issues/123/comments/1", {"body": comment}),
        ("DELETE", "/issues/123/comments/2", None),
    ]
    calls.clear()
    reconcile_comments(issue, [{**comments[0], "body": comment}], api, "/issues/123")
    assert calls == []


def test_dor_workflow_comment_creates_once_for_empty_comments() -> None:
    calls: list[tuple[str, str, object]] = []

    def api(method: str, path: str, data: object = None) -> None:
        calls.append((method, path, data))

    reconcile_comments({"title": "Sparse issue", "body": "x"}, [], api, "/issues/123")
    assert len(calls) == 1
    assert calls[0][0:2] == ("POST", "/issues/123/comments")
    assert "Missing fields:" in calls[0][2]["body"]


def test_intake_accepted_plain_colon_criteria_initialize_lifecycle():
    from scripts.orchestration import task_lifecycle

    assert score_body(COMPLETE)["verdict"] == "PASS"
    policy = {key: {"due_state": "IMPLEMENTATION_READY", "required_evidence": ["test"]} for key in ("AC-01", "AC-02")}
    snapshot = task_lifecycle.build_ac_snapshot(COMPLETE, policy, finalized_at="2026-10-05T12:36:05Z")
    assert [(item["id"], item["text"]) for item in snapshot["criteria"]] == [
        ("AC-01", "checker WARN when new DoR fields missing"),
        ("AC-02", "PR merged with CF + green CI"),
    ]


# #10565: supplied observations exercise the real lifecycle ancestry validator.
from scripts.ci import check_issue_task_quality as checker
from scripts.ci import comment_issue_task_quality as commenter
from scripts.orchestration import issue_stream_audit as audit

REPO = "learn-ukrainian/learn-ukrainian.github.io"
REGISTRY = {"devops": [5703], "harness": [6943]}


def audit_report(*, native=(), body=()):
    result = audit.classify(
        [{"number": 123, "title": "target"}], REGISTRY, {5703: (set(native), set(body)), 6943: (set(), set())}
    )
    result.update(repository=REPO, warnings=[])
    return result


def test_dod_structure_uses_canonical_grammar():
    from scripts.orchestration.task_lifecycle import parse_issue_acceptance_criteria

    for body in [COMPLETE, COMPLETE.replace("[ ]", "[x]")]:
        assert parse_issue_acceptance_criteria(body)
        assert checker.score_body(body)["dod"]["status"] == "PASS"
    absent = checker.score_body("## Definition of Done\nShip it")
    assert "dod_structure_absent" in absent["missing"]
    for suffix in ["\n- [ ] AC-01: duplicate", "\n- [yes] AC-03: broken"]:
        result = checker.score_body(COMPLETE + suffix)
        assert "dod_structure_malformed" in result["missing"]
        assert result["dod"]["errors"][0]["message"]
        assert set(result["dod"]["errors"][0]) == {"section", "field", "code", "message"}


@pytest.mark.parametrize(
    "parents,claim,expected",
    [
        ({123: {"number": 5703, "repository": REPO}}, "[5703]", "PASS"),
        ({123: {"number": 456, "repository": REPO}, 456: {"number": 5703, "repository": REPO}}, "[5703]", "PASS"),
        ({123: None}, "", "membership_missing_parent"),
        ({123: {"number": 5703, "repository": "other/repository"}}, "[5703]", "membership_conflicting_ancestry"),
        ({123: {"number": 6943, "repository": REPO}}, "[5703]", "membership_conflicting_ancestry"),
        (
            {123: {"number": 456, "repository": REPO}, 456: {"number": 123, "repository": REPO}},
            "",
            "membership_conflicting_ancestry",
        ),
        ({n: {"number": n + 1, "repository": REPO} for n in range(123, 131)}, "", "membership_unknown"),
    ],
)
def test_membership_real_validator(parents, claim, expected):
    result = checker.evaluate_membership({"title": claim}, REPO, 123, REGISTRY, parents)
    assert result["status"] == "PASS" if expected == "PASS" else result["errors"][0]["code"] == expected


def test_membership_body_requires_fresh_unique_audit():
    report = audit_report(body=[123])
    result = checker.evaluate_membership({"title": "[5703]"}, REPO, 123, REGISTRY, {123: None}, report)
    assert result == {"status": "PASS", "errors": [], "pending_native_link": True}
    report["generated_at"] = 0
    assert (
        checker.evaluate_membership({}, REPO, 123, REGISTRY, {123: None}, report)["errors"][0]["code"]
        == "membership_audit_stale"
    )
    report = audit_report(body=[123])
    report["membership_complete"] = False
    assert (
        checker.evaluate_membership({}, REPO, 123, REGISTRY, {123: None}, report)["errors"][0]["code"]
        == "membership_audit_incomplete"
    )


def test_multihome_is_conflicting_even_in_one_stream():
    report = audit_report(body=[123])
    report["effective_membership"]["123"].update(epics=[5703, 6943], streams=["devops", "harness"], unique_stream=False)
    result = checker.evaluate_membership({}, REPO, 123, REGISTRY, {123: None}, report)
    assert result["errors"][0]["code"] == "membership_conflicting_ancestry"


def test_registered_root_has_only_membership_exemption():
    result = checker.evaluate_issue({"body": ""}, checker.evaluate_membership({}, REPO, 5703, REGISTRY, {}))
    assert result["membership"]["status"] == "root_exempt"
    assert result["dod"]["status"] == "WARN"


@pytest.mark.parametrize(
    "failure,code",
    [
        (RuntimeError("private detail"), "membership_unknown"),
        (TimeoutError(), "membership_timeout"),
        (checker.subprocess.TimeoutExpired("reader", 30), "membership_timeout"),
        (checker.github_client.GitHubRateLimited(2000), "membership_rate_limited"),
    ],
)
def test_read_failures_are_unknown(monkeypatch, failure, code):
    monkeypatch.setattr(checker, "registry_for", lambda r: REGISTRY)

    def fail(*a):
        raise failure

    monkeypatch.setattr(checker, "read_parent", fail)
    result = checker.observe_membership({}, REPO, 123)
    assert result["errors"][0]["code"] == code
    assert "private detail" not in json.dumps(result)


def test_observation_audits_only_target_null_and_publishes_complete_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    monkeypatch.setattr(checker, "registry_for", lambda r: REGISTRY)
    monkeypatch.setattr(checker, "read_parent", lambda r, n: {"number": 5703, "repository": REPO})
    monkeypatch.setattr(checker, "live_audit", lambda *a: pytest.fail("native parent must not audit"))
    assert checker.observe_membership({}, REPO, 123)["status"] == "PASS"
    path = tmp_path / "batch_state/issue_stream_audit.json"
    assert not path.exists()
    monkeypatch.setattr(checker, "read_parent", lambda r, n: None)
    monkeypatch.setattr(checker, "live_audit", lambda *a, **k: audit_report(body=[123]))
    assert checker.observe_membership({}, REPO, 123)["pending_native_link"] is True
    assert json.loads(path.read_text())["schema_version"] == 1


def test_in_memory_audit(monkeypatch):
    monkeypatch.setattr(audit, "_repo_owner_name", lambda *a: tuple(REPO.split("/")))
    monkeypatch.setattr(audit, "run_audit", lambda *a: pytest.fail("cache writer forbidden"))
    monkeypatch.setattr(audit, "fetch_open_issues", lambda *a: [{"number": 123, "title": "target"}])
    def fetch(cursors, *args):
        return {n: {"body": "#123" if n == 5703 else "", "subIssues": {"nodes": []}} for n in cursors}

    monkeypatch.setattr(audit, "_fetch_subissue_batch", fetch)
    report = checker.live_audit(REPO, REGISTRY)
    assert report["effective_membership"]["123"]["via"] == "body"
    assert report["repository"] == REPO


def test_live_audit_retains_forest_ownership_and_incomplete_refusal(monkeypatch):
    monkeypatch.setattr(audit, "_repo_owner_name", lambda *a: tuple(REPO.split("/")))
    monkeypatch.setattr(audit, "fetch_open_issues", lambda *a: [{"number": 123, "title": "target"}])
    tree = {5703: [6943, 321], 6943: [456, 321], 456: [123]}
    unread = set()

    def fetch(cursors, *args):
        pages = {}
        for number in cursors:
            nodes = [{"number": n, "repository": {"nameWithOwner": REPO},
                      "subIssuesSummary": {"total": len(tree.get(n, []))}} for n in tree.get(number, [])]
            pages[number] = audit.INCOMPLETE_NODE if number in unread else {
                "body": "#123 #777" if number == 5703 else "", "subIssues": {"nodes": nodes}}
        return pages

    monkeypatch.setattr(audit, "_fetch_subissue_batch", fetch)
    report = checker.live_audit(REPO, REGISTRY)
    assert report["membership_complete"] is True
    assert report["effective_membership"] == {
        "123": {"epics": [6943], "streams": ["harness"], "via": "native", "unique_stream": True},
        "456": {"epics": [6943], "streams": ["harness"], "via": "native", "unique_stream": True},
        "321": {"epics": [5703, 6943], "streams": ["devops", "harness"], "via": "native", "unique_stream": False},
        "777": {"epics": [5703], "streams": ["devops"], "via": "body", "unique_stream": True},
    }
    unread.add(6943)
    report = checker.live_audit(REPO, REGISTRY)
    assert report["membership_complete"] is False
    result = checker.evaluate_membership({}, REPO, 123, REGISTRY, {123: None}, report)
    assert result["errors"][0]["code"] == "membership_audit_incomplete"


@pytest.fixture
def membership_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    path = tmp_path / "batch_state/issue_stream_audit.json"
    path.parent.mkdir()
    monkeypatch.setattr(checker, "registry_for", lambda r: REGISTRY)
    monkeypatch.setattr(checker, "fetch_issue", lambda *a: {"body": COMPLETE, "title": "[5703] target"})
    monkeypatch.setattr(checker, "read_parent", lambda *a: None)
    return path


def test_fresh_cached_membership_skips_slow_live_audit(monkeypatch, membership_cache, capsys):
    report = audit_report(body=[123])
    assert checker.write_membership_cache(report, REPO, REGISTRY)
    payload = json.loads(membership_cache.read_text())
    assert payload == {
        **report, "schema_version": 1,
        "root_results": {"5703": {"native": [], "body": [123]}, "6943": {"native": [], "body": []}},
    }
    live = Mock(side_effect=lambda *a, **k: time.sleep(6))
    parent = Mock(return_value=None)
    monkeypatch.setattr(checker, "live_audit", live)
    monkeypatch.setattr(checker, "read_parent", parent)
    started = time.monotonic()
    assert checker.main(["--issue", "123", "--strict", "--json"]) == 0
    assert time.monotonic() - started < 5
    result = json.loads(capsys.readouterr().out)
    assert result["verdict"] == "PASS"
    assert result["membership"] == {"status": "PASS", "errors": [], "pending_native_link": True}
    parent.assert_called_once_with(REPO, 123)
    live.assert_not_called()


@pytest.mark.parametrize(
    "cache,reason",
    [
        ("stale", "membership_audit_stale"),
        ("incomplete", "membership_audit_incomplete"),
        ("conflicting", "membership_conflicting_ancestry"),
        ("missing", "membership_audit_cache_missing"),
        ("repository", "membership_audit_repository_mismatch"),
        ("issue", "membership_missing_parent"),
        ("registry", "membership_audit_registry_mismatch"),
        ("malformed", "membership_audit_cache_unreadable"),
        ("invalid_index", "membership_audit_stale"),
        ("native_entry", "membership_unknown"),
        ("unread_root", "membership_unknown"),
    ],
)
@pytest.mark.parametrize("live_valid", [False, True])
def test_rejected_cache_never_admits_without_live_proof(
    monkeypatch, membership_cache, capsys, cache, reason, live_valid
):
    report = audit_report(body=[123])
    if cache == "stale":
        report["generated_at"] = 0
    elif cache == "incomplete":
        report["membership_complete"] = False
    elif cache == "conflicting":
        report["effective_membership"]["123"].update(epics=[5703, 6943], streams=["devops", "harness"], unique_stream=False)
    elif cache == "repository":
        report["repository"] = "other/repository"
    elif cache == "issue":
        report["effective_membership"]["124"] = report["effective_membership"].pop("123")
        report["open_issue_numbers"] = [124]  # Target was not observed by this snapshot.
    elif cache == "registry":
        report["streams"] = {"devops": [5703]}
    elif cache == "invalid_index":
        report["effective_membership"]["123"]["unique_stream"] = "true"
    elif cache == "native_entry":
        report["effective_membership"]["123"]["via"] = "native"
    elif cache == "unread_root":
        report["warnings"] = [{"code": "unresolved_subissue", "issue": 6943}]
    if cache != "missing":
        membership_cache.write_text("{" if cache == "malformed" else json.dumps(report))
    live_report = audit_report(body=[123])
    if not live_valid:
        live_report["membership_complete"] = False
    live = Mock(return_value=live_report)
    monkeypatch.setattr(checker, "live_audit", live)
    assert checker.main(["--issue", "123", "--strict", "--json"]) == (0 if live_valid else 1)
    live.assert_called_once()
    result = json.loads(capsys.readouterr().out)
    if live_valid:
        assert result["membership"] == {"status": "PASS", "errors": [], "pending_native_link": True}
    else:
        assert result["membership"]["status"] == "WARN"
        assert result["membership"]["errors"][0]["code"] == "membership_audit_incomplete"
        assert result["membership"]["cache_rejection"] == reason


def test_canonical_validator_must_accept_cache(monkeypatch, membership_cache, capsys):
    membership_cache.write_text(json.dumps(audit_report(body=[123])))
    validator = Mock(return_value=None)
    monkeypatch.setattr(audit, "validate_membership_report", validator)
    monkeypatch.setattr(checker, "live_audit", lambda *a, **k: audit_report())
    assert checker.main(["--issue", "123", "--strict", "--json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["membership"]["cache_rejection"] == "membership_audit_stale"
    assert validator.call_count == 2
    assert validator.call_args.args[1] == 3600


@pytest.mark.parametrize("stage", ["target_fetch", "cached_audit_validation", "live_audit_open_issues",
                                      "live_audit_root_2_of_2_issue_6943", "live_audit_root_1_of_2_issue_999",
                                      "live_audit_cache_write"])
def test_slow_stage_times_out_inside_dispatch_deadline(monkeypatch, membership_cache, capsys, stage):
    budget = checker.time_budget
    monkeypatch.setattr(checker, "time_budget", lambda: budget(0.05))
    monkeypatch.setattr(audit, "_repo_owner_name", lambda *a: tuple(REPO.split("/")))
    membership_cache.write_text(json.dumps(audit_report(body=[123])))

    def slow(*a, **k):
        time.sleep(10)

    if stage == "target_fetch":
        monkeypatch.setattr(checker, "fetch_issue", slow)
    elif stage == "cached_audit_validation":
        monkeypatch.setattr(audit, "validate_membership_report", slow)
    elif stage == "live_audit_cache_write":
        membership_cache.write_text(json.dumps({**audit_report(), "generated_at": 0}))
        monkeypatch.setattr(checker, "live_audit", lambda *a, **k: audit_report(body=[123]))
        monkeypatch.setattr(checker, "write_membership_cache", slow)
    else:
        membership_cache.write_text(json.dumps({**audit_report(), "generated_at": 0}))
        monkeypatch.setattr(audit, "fetch_open_issues", slow if stage == "live_audit_open_issues" else lambda *a: [])

        def fetch(cursors, *args):
            number = next(iter(cursors))
            if stage.endswith(f"issue_{number}"):
                slow()
            nodes = [{"number": 999, "repository": {"nameWithOwner": REPO}}] if number == 5703 else []
            return {number: {"body": "#123", "subIssues": {"nodes": nodes}}}

        monkeypatch.setattr(audit, "_fetch_subissue_batch", fetch)
    started = time.monotonic()
    assert checker.main(["--issue", "123", "--strict", "--json"]) == 1
    assert time.monotonic() - started < 1  # Far inside delegate.py's 135s outer deadline.
    result = json.loads(capsys.readouterr().out)
    assert result["membership"]["errors"][0]["code"] == f"membership_timeout_{stage}"
    if stage != "target_fetch":
        assert result["dor"]["status"] == "PASS"
        assert result["dod"]["status"] == "PASS"


@pytest.mark.parametrize("parents,expected", [
    ({123: {"number": 5703, "repository": REPO}}, "PASS"),
    ({123: {"number": 456, "repository": REPO}, 456: {"number": 5703, "repository": REPO}}, "PASS"),
    ({123: {"number": 6943, "repository": REPO}}, "membership_conflicting_ancestry"),
    ({123: {"number": 5703, "repository": "other/repository"}}, "membership_conflicting_ancestry"),
    ({123: {"number": 456, "repository": REPO}, 456: None}, "membership_unknown"),
    ({123: {"number": 456, "repository": REPO}, 456: {"number": 123, "repository": REPO}}, "membership_conflicting_ancestry"),
])
def test_native_observation_never_uses_cached_or_live_audit(monkeypatch, membership_cache, parents, expected):
    monkeypatch.setattr(checker, "read_parent", lambda r, n: parents[n])
    cached = Mock(side_effect=AssertionError("native ancestry must not read the cache"))
    live = Mock(side_effect=AssertionError("native ancestry must not audit"))
    monkeypatch.setattr(checker, "cached_membership", cached)
    monkeypatch.setattr(checker, "live_audit", live)
    result = checker.observe_membership({"title": "[5703]"}, REPO, 123)
    assert result["status"] == "PASS" if expected == "PASS" else result["errors"][0]["code"] == expected
    cached.assert_not_called()
    live.assert_not_called()


@pytest.mark.parametrize("claim", ["", "[5703]", "Parent: #5703"])
def test_writer_round_trip_resolves_parentless_checklist_member(monkeypatch, membership_cache, claim):
    assert checker.write_membership_cache(audit_report(body=[123]), REPO, REGISTRY)
    monkeypatch.setattr(checker, "live_audit", lambda *a, **k: pytest.fail("fresh cache must resolve"))
    assert checker.observe_membership({"title": claim}, REPO, 123) == {
        "status": "PASS", "errors": [], "pending_native_link": True,
    }


@pytest.mark.parametrize("source", ["cache", "live"])
def test_unregistered_parentless_target_fails_closed_without_repeated_audit(
    monkeypatch, membership_cache, capsys, source
):
    report = audit_report()
    if source == "cache":
        assert checker.write_membership_cache(report, REPO, REGISTRY)
    live = Mock(return_value=report)
    monkeypatch.setattr(checker, "live_audit", live)
    assert checker.main(["--issue", "123", "--strict", "--json"]) == 1
    membership = json.loads(capsys.readouterr().out)["membership"]
    assert membership["errors"] == [{
        "section": "membership", "field": "ancestry", "code": "membership_unregistered_parentless",
        "message": "Issue #123 has no native parent and no registered stream membership. "
        "Register #123 as a native sub-issue of one registered stream root or its overflow container; "
        "if the native link is at capacity, add '- [ ] #123' to exactly one registered root's body "
        "and refresh the membership audit.",
    }]
    assert live.call_count == int(source == "live")
    live.reset_mock()
    assert checker.observe_membership({}, REPO, 123)["errors"][0]["code"] == "membership_unregistered_parentless"
    live.assert_not_called()


@pytest.mark.parametrize("change", [
    {"generated_at": 0}, {"generated_at": time.time() + 10000},
    {"membership_complete": False}, {"incomplete_nodes": [6943]},
    {"repository": "other/repo"}, {"streams": {"devops": [5703]}},
    {"schema_version": 2}, {"schema_version": True},
    {"effective_membership": {
        "123": {"epics": [5703, 6943], "streams": ["devops", "harness"], "via": "body", "unique_stream": False}
    }},
    {"multi_homed": [{"number": 456}]}, {"open_total": True}, {"open_total": 2},
    {"open_issue_numbers": None}, {"open_issue_numbers": [123, 123], "open_total": 2},
    {"open_issue_numbers": list(range(1, 501)), "open_total": 500},
    {"warnings": [{"code": "unresolved_subissue", "issue": 6943}]},
    {"warnings": [{"code": "unresolved_subissue", "issue": []}]},
])
def test_cache_writer_rejects_invalid_report_without_replacing_good_cache(monkeypatch, membership_cache, change):
    assert checker.write_membership_cache(audit_report(body=[123]), REPO, REGISTRY)
    before = membership_cache.read_bytes()
    report = {**audit_report(body=[123]), **change}
    assert checker.write_membership_cache(report, REPO, REGISTRY) is False
    assert membership_cache.read_bytes() == before
    assert list(membership_cache.parent.iterdir()) == [membership_cache]


@pytest.mark.parametrize("entry", [
    {"epics": [9999], "streams": ["devops"], "via": "body", "unique_stream": True},
    {"epics": [5703], "streams": ["harness"], "via": "body", "unique_stream": True},
])
def test_cache_writer_rejects_membership_outside_registry(membership_cache, entry):
    report = audit_report(body=[123])
    report["effective_membership"]["123"] = entry
    assert checker.write_membership_cache(report, REPO, REGISTRY) is False
    assert not membership_cache.exists()


def test_cache_writer_publishes_only_complete_json_by_atomic_rename(monkeypatch, membership_cache):
    membership_cache.write_text("previous cache")
    replace = checker.os.replace
    calls = []

    def inspect_then_replace(temporary, destination):
        from pathlib import Path

        temporary = Path(temporary)
        assert temporary.parent == destination.parent == membership_cache.parent
        assert membership_cache.read_text() == "previous cache"
        assert json.loads(temporary.read_text())["root_results"]["5703"] == {"native": [456], "body": [123]}
        calls.append(destination)
        replace(temporary, destination)

    monkeypatch.setattr(checker.os, "replace", inspect_then_replace)
    assert checker.write_membership_cache(audit_report(native=[456], body=[123]), REPO, REGISTRY)
    assert calls == [membership_cache]
    assert list(membership_cache.parent.iterdir()) == [membership_cache]


def test_writer_and_reader_share_primary_cache_from_linked_worktree(monkeypatch, tmp_path):
    primary = tmp_path / "primary"
    gitdir = primary / ".git/worktrees/worker"
    gitdir.mkdir(parents=True)
    checkout = tmp_path / "worker"
    checkout.mkdir()
    (checkout / ".git").write_text(f"gitdir: {gitdir}\n")
    monkeypatch.setattr(checker, "ROOT", checkout)
    assert checker.write_membership_cache(audit_report(body=[123]), REPO, REGISTRY, root=checkout)
    assert (primary / "batch_state/issue_stream_audit.json").is_file()
    assert not (checkout / "batch_state").exists()
    assert checker.cached_membership({}, REPO, 123, REGISTRY, {123: None}) == {
        "status": "PASS", "errors": [], "pending_native_link": True,
    }


@pytest.mark.parametrize("operation", ["fsync", "replace"])
def test_cache_write_failure_preserves_destination_and_removes_temporary(monkeypatch, membership_cache, operation):
    membership_cache.write_text("previous cache")

    def fail(*a):
        raise OSError("failure canary")

    monkeypatch.setattr(checker.os, operation, fail)
    with pytest.raises(OSError, match="failure canary"):
        checker.write_membership_cache(audit_report(body=[123]), REPO, REGISTRY)
    assert membership_cache.read_text() == "previous cache"
    assert list(membership_cache.parent.iterdir()) == [membership_cache]


@pytest.mark.parametrize("change", [{"schema_version": 2}, {"root_results": {}}, {"schema_version": True}])
def test_versioned_cache_schema_is_validated(monkeypatch, membership_cache, change):
    assert checker.write_membership_cache(audit_report(body=[123]), REPO, REGISTRY)
    report = json.loads(membership_cache.read_text())
    membership_cache.write_text(json.dumps({**report, **change}))
    monkeypatch.setattr(checker, "live_audit", lambda *a, **k: {**audit_report(), "membership_complete": False})
    result = checker.observe_membership({}, REPO, 123)
    assert result["status"] == "WARN"
    assert result["cache_rejection"] == "membership_audit_cache_schema"


def test_live_cache_write_failure_does_not_discard_verified_membership(monkeypatch, membership_cache):
    monkeypatch.setattr(checker, "live_audit", lambda *a, **k: audit_report(body=[123]))

    def fail(*a, **k):
        raise OSError("private exception canary")

    monkeypatch.setattr(checker, "write_membership_cache", fail)
    result = checker.observe_membership({}, REPO, 123)
    assert result == {
        "status": "PASS", "errors": [], "pending_native_link": True,
        "cache_write_error": "membership_audit_cache_write_failed",
    }


@pytest.mark.parametrize("source", ["--body", "--body-file", "--issue"])
@pytest.mark.parametrize("strict", [False, True])
@pytest.mark.parametrize("as_json", [False, True])
@pytest.mark.parametrize("repo", [REPO, "learn-ukrainian/learn-ukrainian-infra-private"])
def test_cli_matrix(source, strict, as_json, repo, tmp_path, monkeypatch, capsys):
    bodyfile = tmp_path / "body.md"
    bodyfile.write_text(COMPLETE)
    monkeypatch.setattr(checker, "fetch_issue", lambda *a: {"body": COMPLETE})
    monkeypatch.setattr(
        checker,
        "observe_membership",
        lambda *a: checker.section("PASS" if repo == REPO else "membership_not_applicable"),
    )
    value = {"--body": COMPLETE, "--body-file": str(bodyfile), "--issue": "123"}[source]
    assert (
        checker.main(
            [source, value, "--repo", repo] + (["--strict"] if strict else []) + (["--json"] if as_json else [])
        )
        == 0
    )
    output = capsys.readouterr().out
    if as_json:
        result = json.loads(output)
        assert result["membership"]["status"] == (
            "unchecked" if source != "--issue" else "PASS" if repo == REPO else "membership_not_applicable"
        )


def test_trivial_does_not_exempt_live_membership():
    result = checker.evaluate_issue({"body": "trivial: yes"}, checker.membership_error("membership_missing_parent"))
    assert result["trivial"]
    assert result["verdict"] == "WARN"
    assert result["dod"]["status"] == "exempt"


def test_comment_private_boundary_and_bot_filter():
    issue = {"body": "SECRET_BODY_CANARY", "title": "SECRET_TITLE_CANARY", "_observed_at": "2026-10-15T00:00:00Z"}
    issue["_quality"] = checker.evaluate_issue(issue, checker.membership_error("membership_missing_parent"))
    text = commenter.render_comment(issue)
    assert "SECRET" not in text
    assert "no native parent observed at 2026-10-15T00:00:00Z; dispatch re-checks live" in text
    calls = []
    commenter.reconcile_comments(
        issue, [{"body": MARKER, "id": 9, "user": {"login": "person"}}], lambda *a: calls.append(a), "/issues/123"
    )
    assert [c[0] for c in calls] == ["POST"]


@pytest.mark.parametrize("membership", [checker.membership_error("membership_missing_parent"),
                                      checker.section("PASS", pending_native_link=True)])
def test_workflow_observes_once_without_retrying_or_auditing(monkeypatch, membership):
    calls = []

    def observe(*args, **kwargs):
        calls.append((args, kwargs))
        return membership

    monkeypatch.setattr(commenter, "observe_membership", observe)
    issue = {"body": COMPLETE}
    result = commenter.check_current_issue(issue, REPO, 123)
    assert result["membership"] == membership
    assert calls == [((issue, REPO, 123), {"audit_orphans": False})]


def test_comment_main_rate_limit_skip(monkeypatch, capsys):
    def fail():
        raise checker.github_client.GitHubRateLimited(2000)

    monkeypatch.setattr(commenter, "_main", fail)
    assert commenter.main() == 0
    assert "rate_limited" in capsys.readouterr().out


@pytest.mark.parametrize("script", [
    "scripts/ci/comment_issue_task_quality.py",
    "scripts/orchestration/issue_quality_report.py",
])
def test_issue_quality_file_help_without_repository_import_path(script, tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    result = subprocess.run(
        [sys.executable, "-I", str(Path(__file__).resolve().parents[1] / script), "--help"],
        cwd=tmp_path,
        env={key: value for key, value in os.environ.items() if key not in {
            "PYTHONPATH", "GITHUB_TOKEN", "GITHUB_REPOSITORY", "GITHUB_EVENT_PATH",
        }},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--help" in result.stdout
    assert "Outputs:" in result.stdout
    assert "Exit codes:" in result.stdout


def test_cli_stub_entrypoint_and_safe_errors(tmp_path, monkeypatch, capsys):
    import subprocess
    import sys
    from pathlib import Path

    command = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "scripts/check_issue_task_quality.py"),
        "--body",
        "trivial: yes",
        "--json",
        "--strict",
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=True)
    assert json.loads(result.stdout)["membership"]["status"] == "unchecked"

    def fail(*a):
        raise ValueError("PRIVATE_BODY_CANARY")

    monkeypatch.setattr(checker, "fetch_issue", fail)
    assert checker.main(["--issue", "123", "--json", "--strict"]) == 1
    output = capsys.readouterr().out
    assert "CANARY" not in output and "checker_error" in output


@pytest.mark.parametrize("parent", [None, {"number": 5703, "repository": {"nameWithOwner": REPO}}])
def test_typed_parent_reader(monkeypatch, parent):
    document = {"data": {"repository": {"nameWithOwner": REPO, "issue": {"number": 123, "parent": parent}}}}
    monkeypatch.setattr(
        checker, "read", lambda *a, **k: checker.subprocess.CompletedProcess([], 0, json.dumps(document), "")
    )
    result = checker.read_parent(REPO, 123)
    assert result == (None if parent is None else {"number": 5703, "repository": REPO})
    document["data"]["repository"]["nameWithOwner"] = "other/repository"
    with pytest.raises(ValueError):
        checker.read_parent(REPO, 123)


def test_claim_from_parent_line_resolved_through_registry():
    report = audit_report(native=[123, 456])
    result = checker.evaluate_membership(
        {"body": "Parent: #456"}, REPO, 123, REGISTRY, {123: {"number": 6943, "repository": REPO}}, report
    )
    assert result["errors"][0]["code"] == "membership_conflicting_ancestry"


def test_unknown_repository_and_empty_registry(monkeypatch):
    assert (
        checker.observe_membership({}, "other/unregistered", 5703)["errors"][0]["code"] == "membership_registry_absent"
    )
    monkeypatch.setattr(checker, "registry_for", lambda *a: {})
    assert checker.observe_membership({}, REPO, 123)["errors"][0]["code"] == "membership_registry_absent"


def test_total_deadline_restores_handler():
    import signal

    previous = signal.getsignal(signal.SIGALRM)
    with pytest.raises(TimeoutError), checker.time_budget(0.01):
        signal.pause()
    assert signal.getsignal(signal.SIGALRM) == previous


def test_comment_refetches_current_issue_and_paginates(monkeypatch, tmp_path):
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"action": "edited", "issue": {"number": 123, "body": "STALE_EVENT_CANARY"}}))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("GITHUB_TOKEN", "fixture")
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    calls = []

    class Response:
        def __init__(self, value):
            self.value = value

        def require_fresh(self):
            return self.value

    class Client:
        def __init__(self, **kw):
            pass

        def request(self, method, path, **kwargs):
            calls.append((method, path, kwargs.get("payload")))
            if method != "GET":
                return Response({})
            if "comments?" in path:
                if path.endswith("&page=1"):
                    return Response([{"id": i, "body": "other", "user": {"login": "person"}} for i in range(100)])
                return Response([])
            return Response({"number": 123, "body": COMPLETE, "title": "Current"})

    monkeypatch.setattr(commenter, "GitHubClient", Client)

    def check(issue, *a, **kw):
        assert issue["body"] == COMPLETE
        return checker.evaluate_issue(issue, checker.section("PASS"))

    monkeypatch.setattr(commenter, "check_current_issue", check)
    assert commenter.main() == 0
    assert len([c for c in calls if "comments?" in c[1]]) == 2
    assert calls[-1][0] == "POST"
    assert "STALE_EVENT_CANARY" not in json.dumps(calls)


def test_workflow_membership_timeout_preserves_card(monkeypatch):
    import signal

    budget = checker.time_budget
    monkeypatch.setattr(commenter, "time_budget", lambda: budget(0.01))
    monkeypatch.setattr(commenter, "observe_membership", lambda *a, **k: signal.pause())
    result = commenter.check_current_issue({"body": COMPLETE + "\n- [ ] AC-01: duplicate"}, REPO, 123)
    assert result["missing"] == ["dod_structure_malformed", "membership_timeout"]


def test_deadline_cannot_be_swallowed_by_audit_retry_handlers():
    import signal

    with pytest.raises(TimeoutError), checker.time_budget(0.01):
        try:
            signal.pause()
        except (OSError, RuntimeError, ValueError):
            pytest.fail("audit swallowed the global deadline")


def test_ancestor_null_is_unknown_and_does_not_report_target_as_orphan():
    parents = {123: {"number": 456, "repository": REPO}, 456: None}
    result = checker.evaluate_membership({}, REPO, 123, REGISTRY, parents)
    assert result["errors"][0]["code"] == "membership_unknown"


def test_absent_public_registry_is_reported_as_absent(monkeypatch):
    def missing(*a, **k):
        raise FileNotFoundError

    monkeypatch.setattr(audit, "load_registry", missing)
    assert checker.observe_membership({}, REPO, 123)["errors"][0]["code"] == "membership_registry_absent"


def test_in_memory_audit_refuses_mismatched_checkout(monkeypatch):
    monkeypatch.setattr(audit, "_repo_owner_name", lambda *a: ("other", "repository"))
    monkeypatch.setattr(audit, "fetch_open_issues", lambda *a: pytest.fail("must refuse before fetching"))
    with pytest.raises(ValueError, match="audit repository does not match target"):
        checker.live_audit(REPO, REGISTRY)


@pytest.mark.parametrize("failure", [ValueError("PRIVATE_CANARY"), TimeoutError(),
                                     checker.subprocess.TimeoutExpired("fetch", 60),
                                     checker.github_client.GitHubRateLimited(2000)])
def test_fetch_failure_does_not_invent_card_findings(monkeypatch, capsys, failure):
    def fail(*args):
        raise failure

    monkeypatch.setattr(checker, "fetch_issue", fail)
    assert checker.main(["--issue", "123", "--strict", "--json"]) == 1
    output = capsys.readouterr().out
    result = json.loads(output)
    timeout = isinstance(failure, (TimeoutError, checker.subprocess.TimeoutExpired))
    assert result["missing"] == ["input", "checker_error"] + (["membership_timeout_target_fetch"] if timeout else [])
    assert result["dod"] == {"status": "unchecked", "errors": []}
    assert result["dor"] == {"status": "unchecked", "errors": []}
    assert result["membership"]["status"] == "unchecked"
    assert result["membership"]["errors"] == ([{
        "section": "membership", "field": "ancestry", "code": "membership_timeout_target_fetch",
        "message": "membership timeout target fetch",
    }] if timeout else [])
    assert "PRIVATE_CANARY" not in output


@pytest.mark.parametrize("trivial", ["body", "flag", "label"])
def test_trivial_malformed_dod_is_reported_without_refusal(trivial, monkeypatch, capsys):
    body = COMPLETE + "\n- [ ] AC-01: duplicate"
    issue = {"body": ("trivial: yes\n" if trivial == "body" else "") + body,
             "labels": [{"name": "trivial"}] if trivial == "label" else []}
    monkeypatch.setattr(checker, "fetch_issue", lambda *a: issue)
    monkeypatch.setattr(checker, "observe_membership", lambda *a: checker.section("PASS"))
    assert checker.main(["--issue", "123", "--strict", "--json"] + (["--trivial"] if trivial == "flag" else [])) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["verdict"] == "PASS"
    assert result["missing"] == []
    assert result["dod"]["status"] == "WARN"
    assert [e["code"] for e in result["dod"]["errors"]] == ["dod_structure_malformed"]
    assert "dod_structure_malformed" in result["notes"]
    assert "dod_structure_malformed" in commenter.render_comment({**issue, "_quality": result})


def test_bot_marker_inside_other_comment_is_untouched():
    calls = []
    reconcile_comments({"body": COMPLETE}, [
        {"id": 10, "body": "Quoted example: " + MARKER, "user": {"login": commenter.BOT_LOGIN}},
        {"id": 11, "body": MARKER + "\nuser copy", "user": {"login": "person"}},
    ], lambda *a: calls.append(a), "/issues/123")
    assert len(calls) == 1
    assert calls[0][:2] == ("POST", "/issues/123/comments")


@pytest.mark.parametrize("depth", [1, 8, 9])
def test_workflow_native_parent_reads_are_bounded(monkeypatch, depth):
    calls = []
    monkeypatch.setattr(checker, "registry_for", lambda r: REGISTRY)

    def parent(repo, number):
        calls.append(number)
        target = 5703 if len(calls) == depth else number + 1
        return {"number": target, "repository": repo}

    monkeypatch.setattr(checker, "read_parent", parent)
    monkeypatch.setattr(checker, "live_audit", lambda *a: pytest.fail("workflow must not audit"))
    result = commenter.check_current_issue({"body": COMPLETE}, REPO, 123)
    assert len(calls) == min(depth, 8)
    if depth <= 8:
        assert result["membership"]["status"] == "PASS"
    else:
        assert result["missing"] == ["membership_unknown"]


@pytest.mark.parametrize("action,body,parent,exit_code", [
    ("opened", COMPLETE, None, 1),
    ("edited", COMPLETE, None, 0),
    ("edited", COMPLETE + "\n- [ ] AC-01: duplicate", 5703, 1),
    ("opened", "trivial: yes\n" + COMPLETE + "\n- [ ] AC-01: duplicate", 5703, 0),
], ids=["opened-orphan", "edited-orphan", "malformed", "trivial-malformed"])
def test_event_api_cost_and_exit_status(monkeypatch, tmp_path, action, body, parent, exit_code, capsys):
    """Reviewer API-cost probe: an orphan event has a ceiling of 4 reads.

    Two workflow GETs fetch the current issue and its empty comment page.
    The real publisher/REST parent reader fetches the issue and its parent,
    which returns a typed 404 for an orphan. The synthetic
    tree has 17 roots and 31/19/6 containers, so any full audit exceeds this
    fixed ceiling independently of the size of the live repository.
    """
    import itertools
    import subprocess

    roots = list(range(5703, 5720))
    registry = {"devops": roots}
    children = {}
    counter = itertools.count(100000)
    level = roots
    for containers in [31, 19, 6]:
        following = []
        for number in level:
            children[number] = [next(counter) for _ in range(5)]
            following.extend(children[number])
        level = following[:containers]
    for number in level:
        children[number] = [next(counter) for _ in range(3)]

    calls = []
    comments = []

    def command(args, **kwargs):
        endpoint = args[4]
        calls.append(endpoint)
        number = int(endpoint.split("?")[0].split("/")[4])
        if endpoint.endswith("/parent"):
            if parent is None:
                result = subprocess.CompletedProcess(args, 1, "", "")
                result.github_result = checker.github_client.Result(status=404, error="github_http_error")
                return result
            value = {"number": parent, "html_url": f"https://github.com/{REPO}/issues/{parent}",
                     "repository_url": f"https://api.github.com/repos/{REPO}"}
        elif "/sub_issues" in endpoint:
            value = [{"number": child, "repository_url": f"https://api.github.com/repos/{REPO}",
                      "sub_issues_summary": {"total": len(children.get(child, []))}}
                     for child in children.get(number, [])]
        else:
            value = {"number": number, "state": "open", "body": "", "labels": [],
                     "html_url": f"https://github.com/{REPO}/issues/{number}",
                     "repository_url": f"https://api.github.com/repos/{REPO}"}
        return subprocess.CompletedProcess(args, 0, json.dumps(value), "")

    class Client:
        def __init__(self, **kwargs):
            pass

        def request(self, method, path, **kwargs):
            if method == "GET":
                calls.append(path)
                value = [] if "comments?" in path else {"number": 123, "body": body, "title": "target"}
                return checker.github_client.Result(value=value)
            assert method == "POST"
            comments.append(kwargs["payload"]["body"])
            return checker.github_client.Result(value={})

    monkeypatch.setattr(checker, "registry_for", lambda r: registry)
    monkeypatch.setattr(checker.github_client, "command", command)
    monkeypatch.setattr(audit, "_repo_owner_name", lambda *a: tuple(REPO.split("/")))
    monkeypatch.setattr(audit, "fetch_open_issues", lambda *a: [{"number": 123, "title": "target"}])
    monkeypatch.setattr(commenter, "GitHubClient", Client)
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"action": action, "issue": {"number": 123}}))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("GITHUB_TOKEN", "fixture")
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    assert commenter.main() == exit_code
    assert len(calls) <= 4
    assert calls == [f"repos/{REPO}/issues/123", f"repos/{REPO}/issues/123", f"repos/{REPO}/issues/123/parent",
                     f"repos/{REPO}/issues/123/comments?per_page=100&page=1"]
    assert len(comments) == 1
    assert ("membership_missing_parent" if parent is None else "Membership: PASS") in comments[0]
    assert "membership_unknown" not in comments[0]
    assert "synchronized" in capsys.readouterr().out
