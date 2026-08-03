"""Cutover contracts for the retired review-pr bridge lifecycle."""

from __future__ import annotations

from argparse import Namespace
from contextlib import contextmanager
from types import SimpleNamespace

from ai_agent_bridge import _review_pr


def _args(*, background: bool = False, dry_run: bool = False) -> Namespace:
    return Namespace(
        pr="5900",
        reviewer="auto",
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
