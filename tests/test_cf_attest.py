"""Unit tests for the exact-head cross-family CI lock (#7141)."""

from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError

import pytest
import yaml

from scripts.ci import gate_required_results as gate
from scripts.ci.cf_attest import (
    FAMILY_CURSOR_AUTO_UNION,
    author_family_from_agents,
    build_attest_feedback,
    diagnose_attest_comment,
    evaluate_attestation,
    families_independent,
    main,
    normalize_family,
    parse_attestation,
    parse_pr_number,
    rerun_stale_failed_cf_attest,
    resolve_pr_head_sha,
    run_event,
    x_agent_seats_from_messages,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
_COMMENT_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "cf-attest-on-comment.yml"

PR_HEAD = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
MERGE_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
STALE_HEAD = "cccccccccccccccccccccccccccccccccccccccc"
AUTHOR_CURSOR = "X-Agent: cursor/cf-attest-gate-lock\n"
AUTHOR_CLAUDE = "X-Agent: claude/review-lock\n"


def _formal_agy(head: str) -> str:
    return (
        "## Cross-family review (AGY / Gemini) — review of record\n\n"
        f"**Head:** `{head}`\n"
        "**Reviewer family:** Gemini (AGY) — outside OpenAI author family\n\n"
        "### VERDICT: APPROVED\n"
    )


def _idle_grok(head: str) -> str:
    return f"## Cross-family CF (Grok / xAI)\n**VERDICT: APPROVE** at head `{head}`.\n"


def _sonnet_inline(head: str) -> str:
    return (
        f"Cross-family review (claude-sonnet-5, review of record, head `{head}`) "
        "VERDICT: APPROVE\n"
    )


def _cf_of_record(head: str) -> str:
    return (
        f"Cross-family CF of record (AGY / Gemini) at exact head `{head}`\n"
        "VERDICT: APPROVE\n"
    )


def _fleet_provenance(head: str) -> str:
    return (
        "VERDICT: APPROVED\n"
        f"Head SHA: {head}\n"
        "Reviewer provenance: model=claude-sonnet-5; family=anthropic; harness=claude\n"
    )


def test_parse_existing_cf_shapes() -> None:
    for body in (
        _formal_agy(PR_HEAD),
        _idle_grok(PR_HEAD),
        _sonnet_inline(PR_HEAD),
        _cf_of_record(PR_HEAD),
        _fleet_provenance(PR_HEAD),
    ):
        parsed = parse_attestation(body)
        assert parsed is not None
        assert parsed.head_sha == PR_HEAD
        assert parsed.verdict == "APPROVE"
        assert parsed.reviewer_family in {"google", "xai", "anthropic"}


def test_parse_shared_identity_comment_contract_shape() -> None:
    """#7472 durable path: gh pr comment body matching the module contract."""
    body = (
        "**VERDICT: APPROVE**\n\n"
        "Cross-family review of record (Codex)\n"
        "Reviewer family: OpenAI\n"
        f"At exact head `{PR_HEAD}`\n"
    )
    parsed = parse_attestation(body)
    assert parsed is not None
    assert parsed.head_sha == PR_HEAD
    assert parsed.verdict == "APPROVE"
    assert parsed.reviewer_family == "openai"


def test_parse_rejects_missing_and_blocked() -> None:
    assert parse_attestation("looks fine, no review") is None
    assert parse_attestation(f"I approve head `{PR_HEAD}`") is None
    # #7487: a blocking verdict now parses as a REVOCATION instead of being
    # dropped — latest-wins evaluation needs to see it.
    blocked = parse_attestation(
        f"Cross-family review (claude-sonnet-5) at head `{PR_HEAD}` "
        "VERDICT: CHANGES_REQUESTED"
    )
    assert blocked is not None and blocked.verdict == "BLOCK"
    assert parse_attestation("Cross-family CF of record (AGY / Gemini) VERDICT: APPROVE") is None


def test_pass_independent_exact_head() -> None:
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family=FAMILY_CURSOR_AUTO_UNION,
        bodies=[("comment", _sonnet_inline(PR_HEAD))],
    )
    assert result.ok
    assert result.reviewer_family == "anthropic"


def test_fail_missing_cf() -> None:
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family="anthropic",
        bodies=[],
    )
    assert not result.ok
    assert "missing CF" in result.reason


def test_fail_same_family() -> None:
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family="xai",
        bodies=[("comment", _idle_grok(PR_HEAD))],
    )
    assert not result.ok
    assert "same-family" in result.reason


def test_fail_stale_sha() -> None:
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family=FAMILY_CURSOR_AUTO_UNION,
        bodies=[("comment", _formal_agy(STALE_HEAD))],
    )
    assert not result.ok
    assert "stale CF" in result.reason
    assert result.attested_head == STALE_HEAD


def test_cursor_auto_rejects_xai_or_moonshot_reviewer() -> None:
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family=FAMILY_CURSOR_AUTO_UNION,
        bodies=[("comment", _idle_grok(PR_HEAD))],
    )
    assert not result.ok
    assert "same-family" in result.reason


def test_author_family_from_x_agent_trailers() -> None:
    assert author_family_from_agents(["cursor"]) == FAMILY_CURSOR_AUTO_UNION
    assert author_family_from_agents(["claude", "claude-inline"]) == "anthropic"
    assert author_family_from_agents(["cursor", "claude"]) == "anthropic"
    # Multi-family authorship resolves to a canonical union token (stricter
    # independence: reviewer must be outside every member), not UNKNOWN —
    # a driver landing a reviewer-prescribed fix on a worker's PR is the
    # normal flow and must stay attestable (#7571, 2026-09-01).
    assert author_family_from_agents(["claude", "codex"]) == "anthropic+openai"
    assert author_family_from_agents(["codex", "claude"]) == "anthropic+openai"
    assert author_family_from_agents(["claude", "codex", "bogus-seat"]) == "unknown"
    assert author_family_from_agents(["antigravity"]) == "google"
    assert x_agent_seats_from_messages([AUTHOR_CURSOR, "unrelated"]) == ("cursor",)


def test_normalize_family_tokens() -> None:
    assert normalize_family("claude-sonnet-5") == "anthropic"
    assert normalize_family("AGY / Gemini") == "google"
    assert normalize_family("antigravity") == "google"
    assert normalize_family("Grok / xAI") == "xai"
    assert normalize_family("cursor") == FAMILY_CURSOR_AUTO_UNION


def test_merge_group_uses_pr_head_not_merge_sha() -> None:
    def api_get(path: str) -> dict:
        assert "/pulls/7447" in path
        return {"head": {"sha": PR_HEAD}}

    expected = resolve_pr_head_sha(
        event_name="merge_group",
        event_sha=MERGE_SHA,
        pr_head_sha="",
        pr_number="",
        merge_group_head_ref="refs/heads/gh-readonly-queue/main/pr-7447-" + MERGE_SHA,
        repository="learn-ukrainian/learn-ukrainian.github.io",
        api_get=api_get,
    )
    assert expected == PR_HEAD
    assert expected != MERGE_SHA


def test_merge_group_pass_does_not_require_cf_on_merge_sha() -> None:
    def api_get(path: str) -> object:
        if path.endswith("/pulls/88") or "/pulls/88?" in path:
            return {"head": {"sha": PR_HEAD}}
        raise AssertionError(f"unexpected API path {path}")

    result = run_event(
        event_name="merge_group",
        event_sha=MERGE_SHA,
        pr_head_sha="",
        pr_number="",
        merge_group_head_ref="refs/heads/gh-readonly-queue/main/pr-88-" + MERGE_SHA,
        repository="learn-ukrainian/learn-ukrainian.github.io",
        api_get=api_get,
        bodies=[("review", _formal_agy(PR_HEAD))],
        author_agents=("cursor",),
    )
    assert result.ok
    assert result.expected_head == PR_HEAD
    assert result.attested_head == PR_HEAD


def test_merge_group_fails_if_cf_attests_merge_commit() -> None:
    def api_get(path: str) -> dict:
        return {"head": {"sha": PR_HEAD}}

    result = run_event(
        event_name="merge_group",
        event_sha=MERGE_SHA,
        pr_head_sha="",
        pr_number="88",
        merge_group_head_ref="refs/heads/gh-readonly-queue/main/pr-88-" + MERGE_SHA,
        repository="learn-ukrainian/learn-ukrainian.github.io",
        api_get=api_get,
        bodies=[("comment", _sonnet_inline(MERGE_SHA))],
        author_agents=("cursor",),
    )
    assert not result.ok
    assert "stale CF" in result.reason


def test_pull_request_prefers_pr_head_over_event_sha() -> None:
    expected = resolve_pr_head_sha(
        event_name="pull_request",
        event_sha=MERGE_SHA,
        pr_head_sha=PR_HEAD,
        pr_number="12",
        merge_group_head_ref="",
        repository="learn-ukrainian/learn-ukrainian.github.io",
    )
    assert expected == PR_HEAD


def test_push_event_is_noop() -> None:
    result = run_event(
        event_name="push",
        event_sha=MERGE_SHA,
        pr_head_sha="",
        pr_number="",
        merge_group_head_ref="",
        repository="learn-ukrainian/learn-ukrainian.github.io",
        bodies=[],
        author_agents=(),
    )
    assert result.ok
    assert "no-op" in result.reason


def test_parse_pr_number_from_queue_ref() -> None:
    assert parse_pr_number("refs/heads/gh-readonly-queue/main/pr-7449-deadbeef") == 7449
    assert parse_pr_number("not-a-queue-ref") is None


def test_main_fails_closed_without_pr_context(capsys) -> None:
    assert main(["--event", "pull_request"]) == 1
    err = capsys.readouterr().err
    assert "fail-closed" in err


def _load_ci() -> dict:
    data = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_workflow_pins_cf_attest_into_gate_needs() -> None:
    jobs = _load_ci()["jobs"]
    assert "cf-attest" in jobs
    assert jobs["cf-attest"].get("if") is None
    assert jobs["cf-attest"]["needs"] == ["ruff"]
    assert "cf-attest" in jobs["ci-gate"]["needs"]
    assert set(jobs["ci-gate"]["needs"]) == set(gate.GATE_NEEDS_JOBS)
    assert "cf-attest" in gate.LIGHT_REQUIRED
    assert "cf-attest" in gate.FULL_REQUIRED


def test_workflow_merge_group_checks_pr_head_not_merge_sha() -> None:
    job = _load_ci()["jobs"]["cf-attest"]
    step = next(
        item for item in job["steps"] if item.get("name") == "Require exact-head cross-family review"
    )
    env = step["env"]
    assert env["PR_HEAD_SHA"] == "${{ github.event.pull_request.head.sha || '' }}"
    assert env["MERGE_GROUP_HEAD_REF"] == "${{ github.event.merge_group.head_ref || '' }}"
    assert env["EVENT_SHA"] == "${{ github.sha }}"
    assert "merge_group.head_sha" not in step["run"]
    assert "github.event.merge_group.head_sha" not in yaml.dump(step)
    assert step["run"] == "python3 scripts/ci/cf_attest.py"
    assert "${{" not in step["run"]


def test_gate_results_env_includes_cf_attest() -> None:
    evaluate = next(
        step
        for step in _load_ci()["jobs"]["ci-gate"]["steps"]
        if step.get("name") == "Fail unless every event-required job succeeded"
    )
    assert "cf-attest=${{ needs.cf-attest.result }}" in evaluate["env"]["RESULTS"]


def _load_comment_workflow() -> dict:
    data = yaml.safe_load(_COMMENT_WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _comment_triggers(workflow: dict) -> dict:
    # PyYAML (YAML 1.1) parses the bare ``on:`` key as the boolean True.
    raw = workflow.get("on", workflow.get(True))
    assert isinstance(raw, dict), "comment workflow has no `on:` triggers"
    return raw


def test_comment_workflow_triggers_on_issue_comment_created() -> None:
    """#7544: dedicated workflow re-evaluates attest when the CF comment lands."""
    assert _COMMENT_WORKFLOW.is_file(), f"missing workflow: {_COMMENT_WORKFLOW}"
    triggers = _comment_triggers(_load_comment_workflow())
    assert set(triggers) == {"issue_comment"}
    assert triggers["issue_comment"] == {"types": ["created"]}


def test_comment_workflow_is_pr_only_and_verdict_shaped() -> None:
    job = _load_comment_workflow()["jobs"]["cf-attest"]
    condition = " ".join(str(job.get("if") or "").split())
    assert "github.event.issue.pull_request" in condition
    assert "VERDICT:" in condition
    assert "usage limit" in condition
    # #M-4 (2026-09-01): the family may arrive via a resolved_model: line, so
    # requiring a literal "Reviewer family:" silently skipped valid verdicts
    # (runs 33552592932 / 33552245509). The evaluator fail-closes instead.
    assert "Reviewer family:" not in condition
    assert job.get("continue-on-error") is not True


def test_comment_workflow_pins_exact_head_env_and_run() -> None:
    workflow = _load_comment_workflow()
    assert workflow["permissions"] == {"contents": "read", "pull-requests": "read"}
    job = workflow["jobs"]["cf-attest"]
    assert job["name"] == "CF attest"
    # Job-level writes are scoped to exactly the two side effects: the gap
    # comment (pull-requests) and the stale-run rerun (actions).
    assert job["permissions"] == {
        "contents": "read",
        "pull-requests": "write",
        "actions": "write",
    }
    resolve = next(step for step in job["steps"] if step.get("id") == "pr")
    assert "fail-closed" in resolve["run"]
    assert "github.event.comment.body" not in resolve["run"]
    step = next(
        item
        for item in job["steps"]
        if item.get("name") == "Require exact-head cross-family review"
    )
    env = step["env"]
    assert env["EVENT_NAME"] == "pull_request"
    assert env["PR_HEAD_SHA"] == "${{ steps.pr.outputs.head_sha }}"
    assert env["PR_NUMBER"] == "${{ github.event.issue.number }}"
    assert env["EVENT_SHA"] == "${{ github.sha }}"
    # The untrusted comment body reaches the evaluator via env only, so a
    # verdict that cannot be attested earns ONE gap comment — never a skip.
    assert env["COMMENT_BODY"] == "${{ github.event.comment.body }}"
    assert step["run"] == "python3 scripts/ci/cf_attest.py --feedback-comment"
    assert "${{" not in step["run"]
    assert step.get("continue-on-error") is not True
    rerun = next(
        item
        for item in job["steps"]
        if item.get("name") == "Rerun stale failed CF attest at this head"
    )
    assert rerun["if"] == "success()"
    assert rerun["run"] == "python3 scripts/ci/cf_attest.py --rerun-stale-failed"
    assert "${{" not in rerun["run"]
    assert rerun["env"]["PR_HEAD_SHA"] == "${{ steps.pr.outputs.head_sha }}"
    assert rerun["env"]["GITHUB_REPOSITORY"] == "${{ github.repository }}"
    checkout = next(
        item for item in job["steps"] if str(item.get("uses", "")).startswith("actions/checkout@")
    )
    assert checkout["with"]["persist-credentials"] is False
    # #7487: trusted default-branch evaluator; PR head is PR_HEAD_SHA only.
    assert "ref" not in checkout["with"]
    assert "scripts/ci" in str(checkout["with"].get("sparse-checkout", ""))


def test_later_block_revokes_earlier_approve_latest_wins() -> None:
    """#7487: an early APPROVE must not survive a later changes-request."""
    approve = (
        f"Cross-family CF of record (codex)\nReviewer family: openai\n"
        f"At exact head `{PR_HEAD}`\nVERDICT: APPROVE"
    )
    block = (
        f"Cross-family CF of record (codex)\nReviewer family: openai\n"
        f"At exact head `{PR_HEAD}`\nVERDICT: CHANGES_REQUESTED"
    )
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family="anthropic",
        bodies=[("comment", approve), ("comment", block)],
    )
    assert not result.ok
    assert "revoked CF" in result.reason

    # And the mirror: an approve GENUINELY LATER than the block stands.
    # It must carry a later timestamp — with equal/absent timestamps the
    # #7502-r2 tie-break deliberately fails closed (block wins).
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family="anthropic",
        bodies=[
            ("comment", block, "2026-08-30T12:00:00Z"),
            ("comment", approve, "2026-08-30T12:05:00Z"),
        ],
    )
    assert result.ok


def test_history_bearing_comment_matches_any_labeled_head() -> None:
    """#7487: an r3 comment recapping r1/r2 heads must not stale-reject."""
    body = (
        f"**VERDICT: APPROVE**\n\nCross-family CF of record (codex)\n"
        f"Reviewer family: openai\nAt exact head `{PR_HEAD}`\n\n"
        f"History: r1 APPROVE at exact head `{STALE_HEAD}` - superseded."
    )
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family="anthropic",
        bodies=[("comment", body)],
    )
    assert result.ok, result.reason


def test_dependabot_token_does_not_neutralize_mixed_author_family() -> None:
    """#7487: one smuggled dependabot trailer must not grant universal
    independence to a PR that also carries a real model family."""
    family = author_family_from_agents(("dependabot", "codex"))
    assert family == "openai"
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family=family,
        bodies=[(
            "comment",
            f"Cross-family CF of record (codex)\nReviewer family: openai\n"
            f"At exact head `{PR_HEAD}`\nVERDICT: APPROVE",
        )],
    )
    assert not result.ok  # openai reviewer vs openai author = same family


def test_api_get_retries_transient_5xx(monkeypatch) -> None:
    import scripts.ci.cf_attest as mod

    calls = {"n": 0}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"[]"

    def fake_urlopen(request, timeout=0):
        calls["n"] += 1
        if calls["n"] < 3:
            raise HTTPError(request.full_url, 502, "bad gateway", None, None)
        return _Resp()

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    monkeypatch.setattr(mod.json, "load", lambda fh: [])
    assert mod.github_api_get("repos/x/y/issues/1/comments") == []
    assert calls["n"] == 3


def test_api_get_does_not_retry_4xx(monkeypatch) -> None:
    import scripts.ci.cf_attest as mod

    calls = {"n": 0}

    def fake_urlopen(request, timeout=0):
        calls["n"] += 1
        raise HTTPError(request.full_url, 404, "nope", None, None)

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    with pytest.raises(HTTPError):
        mod.github_api_get("repos/x/y/issues/1/comments")
    assert calls["n"] == 1


def test_older_review_approve_cannot_outrank_newer_comment_block() -> None:
    """#7502 CF r1: cross-source ordering must be chronological, not
    comments-then-reviews concatenation order."""
    approve = (
        f"Cross-family CF of record (codex)\nReviewer family: openai\n"
        f"At exact head `{PR_HEAD}`\nVERDICT: APPROVE"
    )
    block = (
        f"Cross-family CF of record (codex)\nReviewer family: openai\n"
        f"At exact head `{PR_HEAD}`\nVERDICT: REQUEST_CHANGES"
    )
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family="anthropic",
        bodies=[
            ("comment", block, "2026-08-30T12:00:00Z"),
            ("review", approve, "2026-08-30T11:00:00Z"),  # older review
        ],
    )
    assert not result.ok
    assert "revoked CF" in result.reason


def test_request_changes_spelling_is_a_revocation() -> None:
    """#7502 CF r1: the posting contract's own **VERDICT: REQUEST_CHANGES**."""
    body = (
        f"**VERDICT: REQUEST_CHANGES**\n\nCross-family CF of record (codex)\n"
        f"Reviewer family: openai\nAt exact head `{PR_HEAD}`"
    )
    parsed = parse_attestation(body)
    assert parsed is not None and parsed.verdict == "BLOCK"


def test_body_binds_to_primary_head_only() -> None:
    """#7502 CF r1: one body must not attest every SHA it mentions."""
    body = (
        f"**VERDICT: APPROVE**\n\nCross-family CF of record (codex)\n"
        f"Reviewer family: openai\nAt exact head `{STALE_HEAD}`\n"
        f"History: superseded head at exact head `{PR_HEAD}` earlier."
    )
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family="anthropic",
        bodies=[("comment", body)],
    )
    assert not result.ok
    assert "stale CF" in result.reason


def test_cursor_plus_dependabot_does_not_neutralize_author() -> None:
    """#7502 CF r1: ("cursor", "dependabot") must stay cursor-auto-union."""
    family = author_family_from_agents(("cursor", "dependabot"))
    assert family == FAMILY_CURSOR_AUTO_UNION


def test_same_second_block_outranks_approve_both_orders() -> None:
    """#7502 CF r2: equal timestamps must fail closed (block wins the tie)."""
    approve = (
        f"Cross-family CF of record (codex)\nReviewer family: openai\n"
        f"At exact head `{PR_HEAD}`\nVERDICT: APPROVE"
    )
    block = (
        f"Cross-family CF of record (codex)\nReviewer family: openai\n"
        f"At exact head `{PR_HEAD}`\nVERDICT: REQUEST_CHANGES"
    )
    stamp = "2026-08-30T12:00:00Z"
    for order in ([("comment", block, stamp), ("review", approve, stamp)],
                  [("review", approve, stamp), ("comment", block, stamp)]):
        result = evaluate_attestation(
            expected_head=PR_HEAD, author_family="anthropic", bodies=order
        )
        assert not result.ok, order


def test_pending_review_is_excluded_from_attestation() -> None:
    """#7502 CF r2: an unsubmitted PENDING review must not attest."""
    from scripts.ci.cf_attest import collect_bodies_and_agents

    approve_body = (
        f"Cross-family CF of record (codex)\nReviewer family: openai\n"
        f"At exact head `{PR_HEAD}`\nVERDICT: APPROVE"
    )

    def fake_api(path):
        if path == "repos/o/r/pulls/1" or path.startswith("repos/o/r/pulls/1?"):
            return {"user": {"login": "human"}}
        if "/comments" in path:
            return []
        if "/reviews" in path:
            return [
                {"body": approve_body, "state": "PENDING", "submitted_at": None},
                {"body": approve_body, "state": "APPROVED"},  # missing stamp
            ]
        if "/commits" in path:
            return []
        raise AssertionError(path)

    bodies, _ = collect_bodies_and_agents(
        repository="o/r", pr_number=1, api_get=fake_api
    )
    assert bodies == []


def test_dismissed_review_is_excluded_from_attestation() -> None:
    """#7502 CF r3: a dismissed approval is void — it must not attest."""
    from scripts.ci.cf_attest import collect_bodies_and_agents

    approve_body = (
        f"Cross-family CF of record (codex)\nReviewer family: openai\n"
        f"At exact head `{PR_HEAD}`\nVERDICT: APPROVE"
    )

    def fake_api(path):
        if path == "repos/o/r/pulls/1" or path.startswith("repos/o/r/pulls/1?"):
            return {"user": {"login": "human"}}
        if "/comments" in path:
            return []
        if "/reviews" in path:
            return [
                {
                    "body": approve_body,
                    "state": "DISMISSED",
                    "submitted_at": "2026-08-30T12:00:00Z",
                }
            ]
        if "/commits" in path:
            return []
        raise AssertionError(path)

    bodies, _ = collect_bodies_and_agents(
        repository="o/r", pr_number=1, api_get=fake_api
    )
    assert bodies == []


def test_dependabot_pr_author_maps_to_fixture_family_seat() -> None:
    """Pure Dependabot PRs have no X-Agent trailers; author login must supply the seat."""
    from scripts.ci.cf_attest import (
        author_family_from_agents,
        collect_bodies_and_agents,
        evaluate_attestation,
    )

    def fake_api(path):
        if path == "repos/o/r/pulls/1" or path.startswith("repos/o/r/pulls/1?"):
            return {"user": {"login": "dependabot[bot]"}}
        if "/comments" in path or "/reviews" in path or "/commits" in path:
            return []
        raise AssertionError(path)

    bodies, agents = collect_bodies_and_agents(
        repository="o/r", pr_number=1, api_get=fake_api
    )
    assert bodies == []
    assert agents == ("dependabot",)
    family = author_family_from_agents(agents)
    assert family == "fixture"
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family=family,
        bodies=[(
            "comment",
            f"Cross-family CF of record (codex)\nReviewer family: openai\n"
            f"At exact head `{PR_HEAD}`\nVERDICT: APPROVE",
        )],
    )
    assert result.ok, result.reason


def test_union_author_family_requires_reviewer_outside_every_member() -> None:
    assert families_independent("anthropic+openai", "google") is True
    assert families_independent("anthropic+openai", "deepseek") is True
    assert families_independent("anthropic+openai", "openai") is False
    assert families_independent("anthropic+openai", "anthropic") is False
    # Any non-concrete member fails closed.
    assert families_independent("anthropic+unknown", "google") is False
    assert families_independent("anthropic+cursor-auto-union", "google") is False


def test_pass_union_author_with_outside_reviewer() -> None:
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family="anthropic+openai",
        bodies=[(
            "comment",
            f"Cross-family review of record (agy)\nReviewer family: Google\n"
            f"At exact head `{PR_HEAD}`\n**VERDICT: APPROVE**",
        )],
    )
    assert result.ok, result.reason
    assert result.reviewer_family == "google"


def test_fail_union_author_with_member_reviewer() -> None:
    result = evaluate_attestation(
        expected_head=PR_HEAD,
        author_family="anthropic+openai",
        bodies=[(
            "comment",
            f"Cross-family CF of record (codex)\nReviewer family: openai\n"
            f"At exact head `{PR_HEAD}`\nVERDICT: APPROVE",
        )],
    )
    assert not result.ok


def test_parse_verdict_emphasis_and_resolved_model_shapes() -> None:
    """#M-4: verdict case/emphasis variants and family via resolved_model."""
    variants = [
        (
            f"Cross-family review of record (codex)\nReviewer family: openai\n"
            f"At exact head `{PR_HEAD}`\nVERDICT: APPROVE",
            "openai",
        ),
        (
            f"**VERDICT: APPROVE**\n\nCross-family review of record (codex)\n"
            f"Reviewer family: openai\nAt exact head `{PR_HEAD}`",
            "openai",
        ),
        (
            f"Cross-family review of record (codex)\nReviewer family: openai\n"
            f"At exact head `{PR_HEAD}`\nVERDICT: **APPROVE**",
            "openai",
        ),
        # The exact #M-4 shape: bold verdict + resolved_model, no family line.
        (
            f"**VERDICT: APPROVE**\nCross-family review of record (codex)\n"
            f"resolved_model: gpt-5-codex\nAt exact head `{PR_HEAD}`",
            "openai",
        ),
        (
            f"verdict: approve\nCross-family review (claude-sonnet-5)\n"
            f"resolved_model: claude-sonnet-5\nAt exact head `{PR_HEAD}`",
            "anthropic",
        ),
    ]
    for body, family in variants:
        parsed = parse_attestation(body)
        assert parsed is not None, body
        assert parsed.head_sha == PR_HEAD
        assert parsed.verdict == "APPROVE"
        assert parsed.reviewer_family == family


def test_parse_resolved_model_unresolvable_fails_closed() -> None:
    """An unresolvable resolved_model is a failed attest, not a silent skip."""
    body = (
        "**VERDICT: APPROVE**\nCross-family review of record (mystery-seat)\n"
        f"resolved_model: some-unlisted-model\nAt exact head `{PR_HEAD}`"
    )
    assert parse_attestation(body) is None


def test_diagnose_attest_comment_reports_each_gap() -> None:
    assert diagnose_attest_comment("ordinary chatter, no verdict") is None

    good = (
        "**VERDICT: APPROVE**\nCross-family review of record (codex)\n"
        f"Reviewer family: openai\nAt exact head `{PR_HEAD}`"
    )
    assert diagnose_attest_comment(good, expected_head=PR_HEAD) is None

    stale = diagnose_attest_comment(good, expected_head=STALE_HEAD)
    assert stale is not None
    assert PR_HEAD in stale and STALE_HEAD in stale

    no_family = (
        "**VERDICT: APPROVE**\nCross-family review of record\n"
        f"At exact head `{PR_HEAD}`"
    )
    note = diagnose_attest_comment(no_family, expected_head=PR_HEAD)
    assert note is not None and "reviewer family" in note

    no_head = (
        "**VERDICT: APPROVE**\nCross-family review of record (codex)\n"
        "Reviewer family: openai"
    )
    note = diagnose_attest_comment(no_head, expected_head=PR_HEAD)
    assert note is not None and "head SHA" in note

    bad_model = (
        "**VERDICT: APPROVE**\nCross-family review of record\n"
        f"resolved_model: unlisted-thing\nAt exact head `{PR_HEAD}`"
    )
    note = diagnose_attest_comment(bad_model)
    assert note is not None and "resolved_model" in note


def test_build_attest_feedback_is_one_short_comment() -> None:
    body = build_attest_feedback("missing a resolvable reviewer family")
    assert "VERDICT:" in body
    assert "missing a resolvable reviewer family" in body
    assert "resolved_model" in body


def _failed_cf_check_run(run_id: int = 424242) -> dict:
    return {
        "name": "CF attest",
        "status": "completed",
        "conclusion": "failure",
        "details_url": f"https://github.com/o/r/actions/runs/{run_id}/job/9",
    }


def _run_payload(run_id: int, **overrides: object) -> dict:
    payload = {
        "id": run_id,
        "head_sha": PR_HEAD,
        "status": "completed",
        "conclusion": "failure",
        "run_attempt": 1,
    }
    payload.update(overrides)
    return payload


def test_rerun_stale_failed_cf_attest_reruns_initial_failed_run() -> None:
    posts: list[tuple[str, dict]] = []

    def api_get(path: str) -> object:
        if "check-runs" in path:
            return {"check_runs": [_failed_cf_check_run()]}
        if path.endswith("/actions/runs/424242"):
            return _run_payload(424242)
        raise AssertionError(path)

    summary = rerun_stale_failed_cf_attest(
        repository="o/r",
        head_sha=PR_HEAD,
        api_get=api_get,
        api_post=lambda path, payload: posts.append((path, payload)),
    )
    assert "424242" in summary
    assert posts == [("repos/o/r/actions/runs/424242/rerun-failed-jobs", {})]


def test_rerun_stale_failed_cf_attest_noops_when_check_green() -> None:
    def api_get(path: str) -> object:
        assert "check-runs" in path
        return {"check_runs": [_failed_cf_check_run() | {"conclusion": "success"}]}

    summary = rerun_stale_failed_cf_attest(
        repository="o/r",
        head_sha=PR_HEAD,
        api_get=api_get,
        api_post=lambda path, payload: pytest.fail("must not POST"),
    )
    assert "nothing to rerun" in summary


def test_rerun_stale_failed_cf_attest_never_reruns_a_second_attempt() -> None:
    def api_get(path: str) -> object:
        if "check-runs" in path:
            return {"check_runs": [_failed_cf_check_run()]}
        if path.endswith("/actions/runs/424242"):
            return _run_payload(424242, run_attempt=2)
        raise AssertionError(path)

    summary = rerun_stale_failed_cf_attest(
        repository="o/r",
        head_sha=PR_HEAD,
        api_get=api_get,
        api_post=lambda path, payload: pytest.fail("must not POST"),
    )
    assert "not rerunning again" in summary


def test_rerun_stale_failed_cf_attest_rejects_head_mismatch() -> None:
    def api_get(path: str) -> object:
        if "check-runs" in path:
            return {"check_runs": [_failed_cf_check_run()]}
        if path.endswith("/actions/runs/424242"):
            return _run_payload(424242, head_sha=STALE_HEAD)
        raise AssertionError(path)

    summary = rerun_stale_failed_cf_attest(
        repository="o/r",
        head_sha=PR_HEAD,
        api_get=api_get,
        api_post=lambda path, payload: pytest.fail("must not POST"),
    )
    assert "head SHA mismatch" in summary


def test_rerun_stale_failed_cf_attest_fails_closed_on_bad_head() -> None:
    with pytest.raises(ValueError, match="malformed PR head SHA"):
        rerun_stale_failed_cf_attest(
            repository="o/r",
            head_sha="not-a-sha",
            api_get=lambda path: pytest.fail("must not fetch"),
            api_post=lambda path, payload: pytest.fail("must not POST"),
        )
