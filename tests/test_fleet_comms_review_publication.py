"""Unit tests for Fleet Comms PR-G verdict publisher prep (pure, no GitHub I/O)."""

from __future__ import annotations

import json

import pytest

from scripts.fleet_comms.review_publication import (
    DEFAULT_GATE_KIND,
    DEFAULT_STATUS_CONTEXT,
    STATUS_ERROR,
    STATUS_FAILURE,
    STATUS_SUCCESS,
    HeadFreshness,
    ReviewPublicationError,
    SealedVerdict,
    assert_head_fresh,
    build_thin_verdict_comment,
    check_head_freshness,
    map_verdict_to_commit_status,
    normalize_verdict,
    parse_sealed_verdict_payload,
    parse_verdict_token,
    plan_publication,
    publication_idempotency_key,
)

_SHA_A = "a" * 40
_SHA_B = "b" * 40


def _sealed(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "review_id": "review_deadbeef",
        "repository": "learn-ukrainian/learn-ukrainian.github.io",
        "pr_number": 5512,
        "head_sha": _SHA_A,
        "gate_kind": DEFAULT_GATE_KIND,
        "verdict": "APPROVED",
        "model": "claude-opus-4-6",
        "family": "anthropic",
        "harness": "claude",
    }
    base.update(overrides)
    return base


# ── verdict parsing ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("APPROVED", "APPROVED"),
        ("approved", "APPROVED"),
        ("CHANGES_REQUESTED", "CHANGES_REQUESTED"),
        ("changes_requested", "CHANGES_REQUESTED"),
        ("BLOCKED", "BLOCKED"),
        ("  blocked  ", "BLOCKED"),
    ],
)
def test_normalize_verdict_accepts_canonical_states(raw: str, expected: str) -> None:
    assert normalize_verdict(raw) == expected


@pytest.mark.parametrize("raw", ["", "PASS", "correct", "APPROVE", None, 1])
def test_normalize_verdict_rejects_unknown(raw: object) -> None:
    with pytest.raises(ReviewPublicationError, match="invalid_verdict"):
        normalize_verdict(raw)  # type: ignore[arg-type]


def test_parse_verdict_token_from_text() -> None:
    body = "notes...\nVERDICT: CHANGES_REQUESTED\nmore"
    assert parse_verdict_token(body) == "CHANGES_REQUESTED"


def test_parse_verdict_token_missing() -> None:
    with pytest.raises(ReviewPublicationError, match="verdict_missing"):
        parse_verdict_token("no formal marker here")


def test_parse_sealed_verdict_payload_from_mapping() -> None:
    sealed = parse_sealed_verdict_payload(_sealed())
    assert isinstance(sealed, SealedVerdict)
    assert sealed.verdict == "APPROVED"
    assert sealed.pr_number == 5512
    assert sealed.head_sha == _SHA_A
    assert sealed.gate_kind == DEFAULT_GATE_KIND


def test_parse_sealed_verdict_payload_from_json_bytes() -> None:
    sealed = parse_sealed_verdict_payload(json.dumps(_sealed(verdict="BLOCKED")).encode())
    assert sealed.verdict == "BLOCKED"
    assert sealed.to_dict()["review_id"] == "review_deadbeef"


def test_parse_sealed_verdict_accepts_pr_alias_and_verdict_text() -> None:
    payload = _sealed()
    del payload["pr_number"]
    del payload["verdict"]
    payload["pr"] = 99
    payload["verdict_text"] = "Summary\nVERDICT: CHANGES_REQUESTED\n"
    sealed = parse_sealed_verdict_payload(payload)
    assert sealed.pr_number == 99
    assert sealed.verdict == "CHANGES_REQUESTED"


def test_parse_sealed_verdict_defaults_gate_kind() -> None:
    payload = _sealed()
    del payload["gate_kind"]
    sealed = parse_sealed_verdict_payload(payload)
    assert sealed.gate_kind == DEFAULT_GATE_KIND


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"review_id": ""}, "missing_review_id"),
        ({"head_sha": "not-a-sha"}, "invalid_head_sha"),
        ({"pr_number": 0}, "invalid_pr_number"),
        ({"pr_number": True}, "invalid_pr_number"),
        ({"verdict": "PASS"}, "invalid_verdict"),
        ({"model": "  "}, "missing_model"),
    ],
)
def test_parse_sealed_verdict_fail_closed(overrides: dict[str, object], match: str) -> None:
    with pytest.raises(ReviewPublicationError, match=match):
        parse_sealed_verdict_payload(_sealed(**overrides))


def test_parse_sealed_verdict_rejects_non_object_json() -> None:
    with pytest.raises(ReviewPublicationError, match="JSON object"):
        parse_sealed_verdict_payload("[1, 2]")


# ── stale-head check ─────────────────────────────────────────────────────────


def test_check_head_freshness_fresh() -> None:
    result = check_head_freshness(expected_sha=_SHA_A, current_sha=_SHA_A.upper())
    assert result == HeadFreshness(expected_sha=_SHA_A, current_sha=_SHA_A, is_fresh=True)
    assert result.is_stale is False


def test_check_head_freshness_stale() -> None:
    result = check_head_freshness(expected_sha=_SHA_A, current_sha=_SHA_B)
    assert result.is_fresh is False
    assert result.is_stale is True


def test_assert_head_fresh_raises_on_drift() -> None:
    with pytest.raises(ReviewPublicationError, match="stale_head"):
        assert_head_fresh(expected_sha=_SHA_A, current_sha=_SHA_B)


def test_assert_head_fresh_ok() -> None:
    result = assert_head_fresh(expected_sha=_SHA_A, current_sha=_SHA_A)
    assert result.is_fresh is True


# ── idempotency key ──────────────────────────────────────────────────────────


def test_publication_idempotency_key_stable_and_sensitive() -> None:
    key1 = publication_idempotency_key(
        repository="learn-ukrainian/learn-ukrainian.github.io",
        pr_number=5512,
        head_sha=_SHA_A,
        gate_kind=DEFAULT_GATE_KIND,
    )
    key2 = publication_idempotency_key(
        repository="Learn-Ukrainian/learn-ukrainian.github.io",
        pr_number=5512,
        head_sha=_SHA_A.upper(),
        gate_kind=DEFAULT_GATE_KIND,
    )
    assert key1 == key2
    assert key1.startswith("fleet-pub:")
    assert len(key1) == len("fleet-pub:") + 64

    different_sha = publication_idempotency_key(
        repository="learn-ukrainian/learn-ukrainian.github.io",
        pr_number=5512,
        head_sha=_SHA_B,
        gate_kind=DEFAULT_GATE_KIND,
    )
    different_pr = publication_idempotency_key(
        repository="learn-ukrainian/learn-ukrainian.github.io",
        pr_number=5513,
        head_sha=_SHA_A,
        gate_kind=DEFAULT_GATE_KIND,
    )
    different_gate = publication_idempotency_key(
        repository="learn-ukrainian/learn-ukrainian.github.io",
        pr_number=5512,
        head_sha=_SHA_A,
        gate_kind="advisory-review",
    )
    assert len({key1, different_sha, different_pr, different_gate}) == 4


# ── status mapping + thin comment ────────────────────────────────────────────


@pytest.mark.parametrize(
    ("verdict", "state"),
    [
        ("APPROVED", STATUS_SUCCESS),
        ("CHANGES_REQUESTED", STATUS_FAILURE),
        ("BLOCKED", STATUS_ERROR),
    ],
)
def test_map_verdict_to_commit_status(verdict: str, state: str) -> None:
    assert map_verdict_to_commit_status(verdict) == state


def test_build_thin_verdict_comment_has_no_findings() -> None:
    sealed = parse_sealed_verdict_payload(_sealed(verdict="CHANGES_REQUESTED"))
    body = build_thin_verdict_comment(sealed)
    assert "VERDICT: CHANGES_REQUESTED" in body
    assert f"Head SHA: {_SHA_A}" in body
    assert "Review ID: review_deadbeef" in body
    assert "model=claude-opus-4-6" in body
    assert "findings" not in body.lower()


# ── publication plan (dry-run default, no live mutation) ─────────────────────


def test_plan_publication_dry_run_default_ready() -> None:
    sealed = parse_sealed_verdict_payload(_sealed())
    plan = plan_publication(sealed, current_head_sha=_SHA_A)
    assert plan.action == "publish"
    assert plan.mutate is False
    assert plan.status_context == DEFAULT_STATUS_CONTEXT
    assert plan.status_state == STATUS_SUCCESS
    assert plan.comment_body is not None
    assert "VERDICT: APPROVED" in plan.comment_body
    assert "dry_run" in plan.reason
    assert plan.idempotency_key == publication_idempotency_key(
        repository=sealed.repository,
        pr_number=sealed.pr_number,
        head_sha=sealed.head_sha,
        gate_kind=sealed.gate_kind,
    )


def test_plan_publication_mutate_flag_only_marks_intent() -> None:
    """mutate=True records intent; this helper still performs zero I/O."""
    sealed = parse_sealed_verdict_payload(_sealed(verdict="BLOCKED"))
    plan = plan_publication(sealed, current_head_sha=_SHA_A, mutate=True)
    assert plan.action == "publish"
    assert plan.mutate is True
    assert plan.status_state == STATUS_ERROR
    assert plan.reason == "ready_to_publish"


def test_plan_publication_refuses_stale_head_without_posting() -> None:
    sealed = parse_sealed_verdict_payload(_sealed())
    plan = plan_publication(sealed, current_head_sha=_SHA_B, mutate=True)
    assert plan.action == "refuse_stale"
    assert plan.mutate is False  # never mutate on stale
    assert plan.comment_body is None
    assert plan.status_state is None
    assert "stale_head" in plan.reason


def test_plan_publication_idempotent_skip_on_repeat() -> None:
    sealed = parse_sealed_verdict_payload(_sealed())
    key = publication_idempotency_key(
        repository=sealed.repository,
        pr_number=sealed.pr_number,
        head_sha=sealed.head_sha,
        gate_kind=sealed.gate_kind,
    )
    plan = plan_publication(
        sealed,
        current_head_sha=_SHA_A,
        already_published_key=key,
        mutate=True,
    )
    assert plan.action == "skip_idempotent"
    assert plan.mutate is False
    assert plan.comment_body is None
    assert "already_published" in plan.reason


def test_plan_publication_all_verdicts_for_fake_github_matrix() -> None:
    """PR-G acceptance matrix (approved / changes / blocked) without live GH."""
    for verdict, status in (
        ("APPROVED", STATUS_SUCCESS),
        ("CHANGES_REQUESTED", STATUS_FAILURE),
        ("BLOCKED", STATUS_ERROR),
    ):
        sealed = parse_sealed_verdict_payload(_sealed(verdict=verdict))
        plan = plan_publication(sealed, current_head_sha=_SHA_A)
        assert plan.action == "publish"
        assert plan.status_state == status
        assert plan.to_dict()["verdict"] == verdict
