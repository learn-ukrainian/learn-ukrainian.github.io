"""Unit tests for the exact-head cross-family CI lock (#7141)."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ci import gate_required_results as gate
from scripts.ci.cf_attest import (
    FAMILY_CURSOR_AUTO_UNION,
    author_family_from_agents,
    evaluate_attestation,
    main,
    normalize_family,
    parse_attestation,
    parse_pr_number,
    resolve_pr_head_sha,
    run_event,
    x_agent_seats_from_messages,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

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


def test_parse_rejects_missing_and_blocked() -> None:
    assert parse_attestation("looks fine, no review") is None
    assert parse_attestation(f"I approve head `{PR_HEAD}`") is None
    assert (
        parse_attestation(
            f"Cross-family review (claude-sonnet-5) at head `{PR_HEAD}` "
            "VERDICT: CHANGES_REQUESTED"
        )
        is None
    )
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
    assert author_family_from_agents(["claude", "codex"]) == "unknown"
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
