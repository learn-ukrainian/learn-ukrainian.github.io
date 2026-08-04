"""Cutover contracts for the retired review-pr bridge lifecycle."""

from __future__ import annotations

from argparse import Namespace
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from ai_agent_bridge import _review_pr


def _args(
    *,
    background: bool = False,
    dry_run: bool = False,
    reviewer: str = "auto",
    override_reason: str | None = None,
) -> Namespace:
    return Namespace(
        pr="5900",
        reviewer=reviewer,
        claude_available=None,
        model=None,
        effort=None,
        extra=None,
        task_id=None,
        dry_run=dry_run,
        background=background,
        no_timeout=False,
        initiator="codex/orchestrator",
        author_model="gpt-5.6-sol",
        author_family="openai",
        allow_explicit_fallback=False,
        override_reason=override_reason,
        review_profile=None,
        risk=None,
        role=None,
        required_capability=None,
        data_egress_policy="approved",
        isolation_required=True,
    )


def test_review_pr_background_bridge_worker_is_retired(capsys) -> None:
    assert _review_pr.handle_review_pr(_args(background=True)) == 2
    assert "background bridge workers are retired" in capsys.readouterr().err


def test_review_pr_dry_run_keeps_auto_unresolved_until_authority_transaction(capsys) -> None:
    assert _review_pr.handle_review_pr(_args(dry_run=True)) == 0
    output = capsys.readouterr().out
    assert "reviewer_request=auto" in output
    assert "model=deterministic-scheduler" in output
    assert "initiator=codex/orchestrator" in output


def test_completed_replay_requires_the_original_authorization_envelope() -> None:
    reservation = SimpleNamespace(
        author_model="gpt-5.6-sol",
        author_family="openai",
        requested_role="code:medium",
        requested_profile="code",
        requested_risk="medium",
        route_mode="auto",
        requested_reviewer=None,
        estimated_input_bytes=123,
    )
    request = SimpleNamespace(
        **vars(reservation),
        required_capabilities=("code_review", "sealed_evidence"),
        data_egress_policy="approved",
        isolation_required=True,
    )
    envelope = {
        "required_capabilities": ["code_review", "sealed_evidence"],
        "data_egress_policy": "approved",
        "isolation_required": True,
    }

    assert _review_pr._semantic_request_matches(
        reservation,
        request,
        authorization_envelope=envelope,
    )
    request.data_egress_policy = "different-policy"
    assert not _review_pr._semantic_request_matches(
        reservation,
        request,
        authorization_envelope=envelope,
    )


def test_completed_exact_head_replays_without_provider_call(monkeypatch, capsys, tmp_path) -> None:
    from agent_runtime import runner
    from ai_agent_bridge import _review_worktree

    from scripts.api import state_router
    from scripts.fleet_comms import authority as authority_module
    from scripts.fleet_comms import routing_reservations

    checkout = SimpleNamespace(
        sha="a" * 40,
        base_sha="b" * 40,
        patch_digest="c" * 64,
        changed_paths=("src/app.py",),
        changed_line_numbers={"src/app.py": frozenset({1})},
        path=tmp_path,
        review_prompt_evidence=lambda _engine: "sealed-metadata",
        sealed_acp_tool_config=lambda **_kwargs: tmp_path / "sealed.json",
        sealed_evidence_input_bytes=lambda: 123,
    )

    @contextmanager
    def provision(*_args, **_kwargs):
        yield checkout

    reservation = SimpleNamespace(
        author_model="gpt-5.6-sol",
        author_family="openai",
        requested_role="code:medium",
        requested_profile="code",
        requested_risk="medium",
        route_mode="auto",
        requested_reviewer=None,
        estimated_input_bytes=123,
        resolved_model="claude-sonnet-5",
        resolved_family="anthropic",
        resolved_candidate="claude-sonnet-5",
        quota_bucket="claude",
        credential_bucket="claude",
        reservation_id="routing-reservation_fixture",
    )

    class FakeLedger:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def completed_replay(self, _key):
            return reservation

        def decisions(self, _reservation_id):
            return (
                SimpleNamespace(
                    event_type="reserved",
                    evidence={
                        "authorization_envelope": {
                            "required_capabilities": ["code_review", "sealed_evidence"],
                            "data_egress_policy": "approved",
                            "isolation_required": True,
                        }
                    },
                ),
            )

    job = SimpleNamespace(state="complete", job_id="job_fixture", subject_id="review_fixture")
    formal = SimpleNamespace(review_id="review_fixture", snapshot_artifact_id="artifact_fixture")
    accepted = []

    class FakeAuthority:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def enqueue_formal_review(self, **_kwargs):
            return job

        def require_publishable_formal_review(self, *_args, **_kwargs):
            return formal

        def read_job_result(self, _job_id):
            return (
                b'{"schema_version":"code-review-findings.v1","overall":'
                b'{"correctness":"correct","explanation":"No findings.","confidence":0.95},"findings":[]}'
            )

        def accept_formal_review_verdict(self, _review_id, sealed):
            accepted.append(sealed)

    monkeypatch.setattr(_review_worktree, "provision_review_worktree", provision)
    monkeypatch.setattr(_review_worktree, "validate_code_review_response", lambda *_args, **_kwargs: "d" * 64)
    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **_kwargs: {"agents": {}})
    monkeypatch.setattr(routing_reservations, "RoutingReservationLedger", FakeLedger)
    monkeypatch.setattr(authority_module, "AuthorityService", FakeAuthority)
    monkeypatch.setattr(
        runner,
        "invoke_inter_agent",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("provider call on replay")),
    )

    assert _review_pr.handle_review_pr(_args()) == 0
    assert accepted and accepted[0].model == "claude-sonnet-5"
    assert '"exact_head_replay": true' in capsys.readouterr().out


def test_active_exact_head_exits_before_reservation_or_provider_call(monkeypatch, capsys, tmp_path) -> None:
    from agent_runtime import runner
    from ai_agent_bridge import _review_worktree

    from scripts.api import state_router
    from scripts.fleet_comms import authority as authority_module
    from scripts.fleet_comms import routing_reservations

    checkout = SimpleNamespace(
        sha="a" * 40,
        base_sha="b" * 40,
        patch_digest="c" * 64,
        changed_paths=("src/app.py",),
        changed_line_numbers={"src/app.py": frozenset({1})},
        path=tmp_path,
        review_prompt_evidence=lambda _engine: "sealed-metadata",
        sealed_acp_tool_config=lambda **_kwargs: tmp_path / "sealed.json",
        sealed_evidence_input_bytes=lambda: 123,
    )

    @contextmanager
    def provision(*_args, **_kwargs):
        yield checkout

    class FakeLedger:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def reserve_selection(self, *_args, **_kwargs):
            raise AssertionError("routing reservation created for an already-active exact head")

    job = SimpleNamespace(state="running", job_id="job_active", subject_id="review_active")
    formal = SimpleNamespace(review_id="review_active", snapshot_artifact_id="artifact_active")

    class FakeAuthority:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def enqueue_formal_review(self, **_kwargs):
            return job

        def require_publishable_formal_review(self, *_args, **_kwargs):
            return formal

        def claim_job(self, *_args, **_kwargs):
            raise authority_module.AuthorityStaleLeaseError("job_already_claimed")

    monkeypatch.setattr(_review_worktree, "provision_review_worktree", provision)
    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **_kwargs: {"agents": {}})
    monkeypatch.setattr(routing_reservations, "RoutingReservationLedger", FakeLedger)
    monkeypatch.setattr(authority_module, "AuthorityService", FakeAuthority)
    monkeypatch.setattr(
        runner,
        "invoke_inter_agent",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("duplicate provider call")),
    )

    assert _review_pr.handle_review_pr(_args()) == 1
    assert "already active" in capsys.readouterr().err


@pytest.mark.parametrize("prior_failure", [None, "acp_adapter_missing"])
def test_failed_explicit_review_without_result_invalid_prior_retries_in_place(
    monkeypatch,
    capsys,
    tmp_path,
    prior_failure: str | None,
) -> None:
    from agent_runtime import runner
    from ai_agent_bridge import _review_worktree

    from scripts.api import state_router
    from scripts.fleet_comms import authority as authority_module
    from scripts.fleet_comms import routing_reservations

    checkout = SimpleNamespace(
        sha="a" * 40,
        base_sha="b" * 40,
        patch_digest="c" * 64,
        changed_paths=("src/app.py",),
        changed_line_numbers={"src/app.py": frozenset({1})},
        path=tmp_path,
        review_prompt_evidence=lambda _engine: "sealed-metadata",
        sealed_acp_tool_config=lambda **_kwargs: tmp_path / "sealed.json",
        sealed_evidence_input_bytes=lambda: 123,
    )

    @contextmanager
    def provision(*_args, **_kwargs):
        yield checkout

    class FakeLedger:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def latest_for_authority_key(self, _authority_key):
            if prior_failure is None:
                return None
            return SimpleNamespace(failure_classification=prior_failure)

        def reserve_selection(self, *_args, **_kwargs):
            raise AssertionError("active retry must exit before reserving")

    failed_job = SimpleNamespace(state="failed", job_id="job_failed", subject_id="review_failed")
    queued_job = SimpleNamespace(state="queued", job_id="job_failed", subject_id="review_failed")
    formal = SimpleNamespace(review_id="review_failed", snapshot_artifact_id="artifact_fixture")
    retry_calls: list[str] = []

    class FakeAuthority:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def enqueue_formal_review(self, **_kwargs):
            return failed_job

        def require_publishable_formal_review(self, *_args, **_kwargs):
            return formal

        def retry_job(self, job_id):
            retry_calls.append(job_id)
            return queued_job

        def authorize_formal_review_substitution(self, **_kwargs):
            raise AssertionError("failed admission without a reservation is not a substitution")

        def claim_job(self, *_args, **_kwargs):
            raise authority_module.AuthorityStaleLeaseError("job_already_claimed")

    monkeypatch.setattr(_review_worktree, "provision_review_worktree", provision)
    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **_kwargs: {"agents": {}})
    monkeypatch.setattr(routing_reservations, "RoutingReservationLedger", FakeLedger)
    monkeypatch.setattr(authority_module, "AuthorityService", FakeAuthority)
    monkeypatch.setattr(
        runner,
        "invoke_inter_agent",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("duplicate provider call")),
    )

    assert _review_pr.handle_review_pr(
        _args(reviewer="claude", override_reason="retry after expired circuit")
    ) == 1
    assert retry_calls == [failed_job.job_id]
    assert "already active" in capsys.readouterr().err


@pytest.mark.parametrize(
    "refusal",
    ("substitution_snapshot_drift", "substitution_reservation_expired"),
)
def test_refused_substitution_makes_no_provider_call_or_claim(
    monkeypatch,
    capsys,
    tmp_path,
    refusal: str,
) -> None:
    from agent_runtime import runner
    from ai_agent_bridge import _review_worktree

    from scripts.api import state_router
    from scripts.fleet_comms import authority as authority_module
    from scripts.fleet_comms import routing_reservations

    checkout = SimpleNamespace(
        sha="a" * 40,
        base_sha="b" * 40,
        patch_digest="c" * 64,
        changed_paths=("src/app.py",),
        changed_line_numbers={"src/app.py": frozenset({1})},
        path=tmp_path,
        review_prompt_evidence=lambda _engine: "sealed-metadata",
        sealed_acp_tool_config=lambda **_kwargs: tmp_path / "sealed.json",
        sealed_evidence_input_bytes=lambda: 123,
    )

    @contextmanager
    def provision(*_args, **_kwargs):
        yield checkout

    prior = SimpleNamespace(
        reservation_id="routing-reservation_prior",
        failure_classification="result_invalid",
    )

    class FakeLedger:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def latest_for_authority_key(self, _authority_key):
            return prior

        def reserve_selection(self, *_args, **_kwargs):
            raise AssertionError("refused substitution must not reserve")

    job = SimpleNamespace(state="failed", job_id="job_failed", subject_id="review_failed")
    formal = SimpleNamespace(review_id="review_failed", snapshot_artifact_id="artifact_fixture")

    class FakeAuthority:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def enqueue_formal_review(self, **_kwargs):
            return job

        def require_publishable_formal_review(self, *_args, **_kwargs):
            return formal

        def authorize_formal_review_substitution(self, **_kwargs):
            raise authority_module.AuthorityServiceError(refusal)

        def claim_job(self, *_args, **_kwargs):
            raise AssertionError("refused substitution must not claim")

        def retry_job(self, *_args, **_kwargs):
            raise AssertionError("refused substitution must not requeue")

    monkeypatch.setattr(_review_worktree, "provision_review_worktree", provision)
    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **_kwargs: {"agents": {}})
    monkeypatch.setattr(routing_reservations, "RoutingReservationLedger", FakeLedger)
    monkeypatch.setattr(authority_module, "AuthorityService", FakeAuthority)
    monkeypatch.setattr(
        runner,
        "invoke_inter_agent",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("provider call after refusal")),
    )

    assert _review_pr.handle_review_pr(
        _args(reviewer="glm", override_reason="operator-authorized result-invalid substitution")
    ) == 1
    assert f"formal reviewer substitution refused: {refusal}" in capsys.readouterr().err


def test_expired_reservation_after_successful_substitution_never_reaches_provider(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    from agent_runtime import runner
    from ai_agent_bridge import _review_worktree

    from scripts.api import state_router
    from scripts.fleet_comms import authority as authority_module
    from scripts.fleet_comms import routing_reservations

    checkout = SimpleNamespace(
        sha="a" * 40,
        base_sha="b" * 40,
        patch_digest="c" * 64,
        changed_paths=("src/app.py",),
        changed_line_numbers={"src/app.py": frozenset({1})},
        path=tmp_path,
        review_prompt_evidence=lambda _engine: "sealed-metadata",
        sealed_acp_tool_config=lambda **_kwargs: tmp_path / "sealed.json",
        sealed_evidence_input_bytes=lambda: 123,
    )

    @contextmanager
    def provision(*_args, **_kwargs):
        yield checkout

    prior = SimpleNamespace(
        reservation_id="routing-reservation_prior",
        failure_classification="result_invalid",
    )
    substitute = SimpleNamespace(
        reservation_id="routing-reservation_substitute",
        resolved_candidate="glm-5.2",
        resolved_route="glm",
        resolved_model="glm-5.2",
        resolved_family="zhipu",
        quota_bucket="glm-weekly",
    )

    class FakeLedger:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def latest_for_authority_key(self, _authority_key):
            return prior

        def reserve_selection(self, *_args, **_kwargs):
            raise AssertionError("substitution reservation must already be authority-owned")

        def mark_started(self, reservation_id):
            assert reservation_id == substitute.reservation_id
            return SimpleNamespace(status="expired")

    failed_job = SimpleNamespace(state="failed", job_id="job_failed", subject_id="review_failed")
    queued_job = SimpleNamespace(state="queued", job_id="job_failed", subject_id="review_failed")
    formal = SimpleNamespace(review_id="review_failed", snapshot_artifact_id="artifact_fixture")
    finish_calls: list[dict[str, object]] = []

    class FakeAuthority:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def enqueue_formal_review(self, **_kwargs):
            return failed_job

        def require_publishable_formal_review(self, *_args, **_kwargs):
            return formal

        def authorize_formal_review_substitution(self, **_kwargs):
            return substitute

        def get_job(self, job_id):
            assert job_id == queued_job.job_id
            return queued_job

        def claim_job(self, job_id, _worker_id, **_kwargs):
            assert job_id == queued_job.job_id
            return SimpleNamespace(fence_token=7)

        def finish_job(self, _job_id, **kwargs):
            finish_calls.append(kwargs)

    monkeypatch.setattr(_review_worktree, "provision_review_worktree", provision)
    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **_kwargs: {"agents": {}})
    monkeypatch.setattr(routing_reservations, "RoutingReservationLedger", FakeLedger)
    monkeypatch.setattr(authority_module, "AuthorityService", FakeAuthority)
    monkeypatch.setattr(
        runner,
        "invoke_inter_agent",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("expired route invoked provider")),
    )

    assert _review_pr.handle_review_pr(
        _args(reviewer="glm", override_reason="operator-authorized result-invalid substitution")
    ) == 1
    assert len(finish_calls) == 1
    assert finish_calls[0]["state"] == "failed"
    assert finish_calls[0]["fence_token"] == 7
    assert b'"failure_classification": "routing_reservation_not_active"' in finish_calls[0]["result"]
    assert "provider was not invoked" in capsys.readouterr().err
