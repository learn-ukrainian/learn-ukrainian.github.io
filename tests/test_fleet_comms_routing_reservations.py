"""Focused durability and contention coverage for routing reservations (#6293)."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.fleet_comms.migrations import MIGRATIONS, apply_migrations
from scripts.fleet_comms.routing_reservations import (
    RoutingReservationError,
    RoutingReservationLedger,
    RoutingReservationRequest,
    RoutingReservationUnavailable,
    RoutingSelection,
    list_routing_decisions,
)


def _root(tmp_path: Path) -> Path:
    return tmp_path / "fleet-comms" / "v1"


def _request(authority_key: str, idempotency_key: str, initiator: str = "codex") -> RoutingReservationRequest:
    return RoutingReservationRequest(
        authority_key=authority_key,
        idempotency_key=idempotency_key,
        initiator=initiator,
        author_model="gpt-5.6-sol",
        author_family="openai",
        requested_role="formal-review",
        requested_profile="critical",
        requested_risk="high",
        route_mode="auto",
        estimated_input_bytes=1200,
    )


def _selection(context: object) -> RoutingSelection:
    usage = context.bucket_usage("codex-weekly")  # type: ignore[attr-defined]
    assert usage.inflight_reservations >= 0
    assert context.available_slots("codex-api-key-a", 1) >= 0  # type: ignore[attr-defined]
    assert context.quota_available_slots("codex-weekly", 1) >= 0  # type: ignore[attr-defined]
    return RoutingSelection(
        candidate="codex",
        route="codex-primary",
        model="gpt-5.6-sol",
        family="openai",
        quota_bucket="codex-weekly",
        credential_bucket="codex-api-key-a",
        quota_limit=1,
        credential_limit=1,
        policy_version="resolver-v1",
        quota_snapshot={"remaining": 1},
        quota_fresh_at="2035-01-01T00:00:00Z",
        trace={"source": "pure-policy"},
    )


def test_v6_migration_is_idempotent_and_has_authority_tables(tmp_path: Path) -> None:
    connection = sqlite3.connect(tmp_path / "comms.sqlite3")
    try:
        assert apply_migrations(connection) == MIGRATIONS[-1].version == 7
        assert apply_migrations(connection) == 7
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert {"routing_reservations", "routing_reservation_decisions", "routing_circuit_state"} <= tables
    finally:
        connection.close()


def _reserve(root: Path, authority_key: str, initiator: str) -> str:
    with RoutingReservationLedger(root=root) as ledger:
        try:
            return ledger.reserve_selection(
                _request(authority_key, f"idempotency-{initiator}", initiator),
                _selection,
                now="2035-01-01T00:00:00Z",
            ).reservation_id
        except RoutingReservationUnavailable:
            return "unavailable"


def test_shared_bucket_concurrency_prevents_overallocation(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with RoutingReservationLedger(root=root):
        pass
    simultaneous = (("head-grok", "grok"), ("head-codex", "codex"), ("head-claude", "claude"))
    with ThreadPoolExecutor(max_workers=3) as pool:
        outcomes = list(pool.map(lambda item: _reserve(root, *item), simultaneous))
    assert outcomes.count("unavailable") == 2
    assert len({outcome for outcome in outcomes if outcome != "unavailable"}) == 1


def test_exact_head_replay_expiry_recovery_and_failure_release(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with RoutingReservationLedger(root=root) as ledger:
        first = ledger.reserve_selection(
            _request("repo:1:head", "attempt-1"),
            _selection,
            ttl_seconds=1,
            now="2035-01-01T00:00:00Z",
        )
        joined = ledger.reserve_selection(
            _request("repo:1:head", "attempt-2", "other"),
            _selection,
            now="2035-01-01T00:00:00Z",
        )
        assert joined.reservation_id == first.reservation_id
        assert ledger.mark_started(first.reservation_id, now="2035-01-01T00:00:00Z").status == "running"
        assert ledger.recover_expired(now="2035-01-01T00:00:02Z")[0].status == "expired"

        retry = ledger.reserve_selection(_request("repo:1:head", "attempt-3"), _selection, now="2035-01-01T00:00:03Z")
        failed = ledger.fail_and_release(
            retry.reservation_id,
            "provider_unavailable",
            circuit_open_seconds=30,
            now="2035-01-01T00:00:04Z",
        )
        assert failed.status == "failed"
        circuit = ledger.bucket_circuit_state("codex-weekly", "codex-api-key-a")
        assert circuit is not None and circuit.recent_failure_count == 2

        with pytest.raises(RoutingReservationUnavailable, match="credential_bucket_circuit_open"):
            ledger.reserve_selection(_request("repo:2:head", "attempt-4"), _selection, now="2035-01-01T00:00:05Z")

        released = ledger.reserve_selection(
            _request("repo:2:head", "attempt-5"),
            lambda context: replace(_selection(context), credential_bucket="codex-api-key-b"),
            now="2035-01-01T00:00:05Z",
        )
        assert released.status == "reserved"


def test_idempotent_settlement_completed_replay_and_append_only_evidence(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with RoutingReservationLedger(root=root) as ledger:
        reservation = ledger.reserve_selection(
            _request("repo:9:head", "attempt-1"), _selection, now="2035-01-01T00:00:00Z"
        )
        settled = ledger.settle(
            reservation.reservation_id,
            status="complete",
            actual_input_bytes=1200,
            actual_output_bytes=300,
            actual_input_tokens=160,
            actual_output_tokens=40,
            now="2035-01-01T00:00:01Z",
        )
        assert (
            ledger.settle(
                reservation.reservation_id,
                status="complete",
                actual_input_bytes=1200,
                actual_output_bytes=300,
                actual_input_tokens=160,
                actual_output_tokens=40,
                now="2035-01-01T00:00:02Z",
            )
            == settled
        )
        assert ledger.completed_replay("repo:9:head") == settled
        usage = ledger._bucket_usage("codex-weekly", now_iso="2035-01-01T00:00:02Z", rolling_window_seconds=60)
        assert usage.completed_window_bytes == 1500 and usage.reserved_input_bytes == 0
        decisions = ledger.decisions(reservation.reservation_id)
        assert [decision.event_type for decision in decisions] == ["reserved", "settled"]
        with pytest.raises(sqlite3.IntegrityError, match="routing_reservation_decision_immutable"):
            ledger._conn.execute(
                "UPDATE routing_reservation_decisions SET state = 'tampered' WHERE decision_id = ?",
                (decisions[0].decision_id,),
            )

    evidence = list_routing_decisions(root=root, limit=10)
    assert evidence[0]["authority_key"] == "repo:9:head"
    assert evidence[0]["requested"]["role"] == "formal-review"
    assert evidence[0]["resolved"]["route"] == "codex-primary"
    assert evidence[0]["quota"]["bucket"] == "codex-weekly"
    assert evidence[0]["quota"]["credential_bucket"] == "codex-api-key-a"
    assert evidence[0]["retry"]["attempt"] == 1
    assert evidence[0]["replay"]["completed"] is True
    assert evidence[0]["lifecycle"]["actual_input_tokens"] == 160
    assert evidence[0]["lifecycle"]["actual_output_tokens"] == 40


def test_read_projection_does_not_create_or_migrate_missing_plane(tmp_path: Path) -> None:
    root = _root(tmp_path) / "missing"
    assert list_routing_decisions(root=root) == []
    assert not root.exists()


def test_same_authority_key_semantic_conflict_fails_closed(tmp_path: Path) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        ledger.reserve_selection(_request("repo:semantic:head", "first"), _selection, now="2035-01-01T00:00:00Z")
        changed = replace(_request("repo:semantic:head", "second"), requested_risk="critical")
        with pytest.raises(RoutingReservationError, match="authority_key_semantic_conflict"):
            ledger.reserve_selection(changed, _selection, now="2035-01-01T00:00:01Z")


def test_one_result_invalid_substitution_is_linked_idempotent_and_single_use(tmp_path: Path) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        first = ledger.reserve_selection(
            _request("repo:substitution:head", "first"), _selection, now="2035-01-01T00:00:00Z"
        )
        ledger.settle(
            first.reservation_id, status="failed", failure_classification="result_invalid",
            now="2035-01-01T00:00:01Z",
        )
        substitute = replace(
            _request("repo:substitution:head", "substitute"),
            route_mode="explicit", requested_reviewer="glm-5.2",
        )
        evidence = {
            "prior_reservation_id": first.reservation_id,
            "reason": "operator-authorized invalid-result substitution",
            "review_id": "review_fixture", "authority_job_id": "authority-job_fixture",
            "authority_key": "repo:substitution:head", "data_egress_policy": "approved",
        }
        def selection(context: object) -> RoutingSelection:
            return replace(_selection(context), candidate="glm-5.2", family="zhipu")

        second = ledger.reserve_selection(substitute, selection, now="2035-01-01T00:00:02Z", substitution=evidence)
        assert second.attempt == 2 and second.fallback_from is None
        assert ledger.reserve_selection(substitute, selection, now="2035-01-01T00:00:03Z", substitution=evidence) == second
        assert "authorized_substitution" in {item.event_type for item in ledger.decisions(second.reservation_id)}
        with pytest.raises(RoutingReservationError, match="substitution_idempotency_conflict"):
            ledger.reserve_selection(
                substitute,
                selection,
                now="2035-01-01T00:00:03Z",
                substitution={**evidence, "reason": "different operator reason"},
            )
        with pytest.raises(RoutingReservationError, match="substitution_already_authorized"):
            ledger.reserve_selection(
                replace(substitute, idempotency_key="second-substitution"), selection,
                now="2035-01-01T00:00:04Z", substitution=evidence,
            )


def _failed_result_invalid_reservation(
    ledger: RoutingReservationLedger,
    *,
    authority_key: str,
) -> tuple[RoutingReservationRequest, dict[str, str]]:
    original = replace(
        _request(authority_key, "first"),
        required_capabilities=("code_review", "sealed_evidence"),
        data_egress_policy="approved",
        isolation_required=True,
    )
    first = ledger.reserve_selection(original, _selection, now="2035-01-01T00:00:00Z")
    ledger.settle(
        first.reservation_id,
        status="failed",
        failure_classification="result_invalid",
        now="2035-01-01T00:00:01Z",
    )
    substitute = replace(
        original,
        idempotency_key="substitute",
        route_mode="explicit",
        requested_reviewer="glm-5.2",
    )
    return substitute, {
        "prior_reservation_id": first.reservation_id,
        "reason": "operator-authorized invalid-result substitution",
        "review_id": "review_fixture",
        "authority_job_id": "authority-job_fixture",
        "authority_key": authority_key,
        "data_egress_policy": "approved",
    }


def _glm_selection(context: object) -> RoutingSelection:
    return replace(_selection(context), candidate="glm-5.2", family="zhipu")


def _legacy_failed_result_invalid_reservation(
    ledger: RoutingReservationLedger,
    monkeypatch: pytest.MonkeyPatch,
    *,
    authority_key: str,
) -> tuple[RoutingReservationRequest, dict[str, str], str]:
    """Create a pre-#6342 reservation whose decision lacks the new envelope."""
    original_append = ledger._append_decision_tx

    def append_without_envelope(
        reservation_id: str,
        event_type: str,
        state: str,
        evidence: dict[str, object],
        created_at: str,
    ) -> None:
        legacy_evidence = dict(evidence)
        if event_type == "reserved":
            legacy_evidence.pop("authorization_envelope", None)
        original_append(reservation_id, event_type, state, legacy_evidence, created_at)

    monkeypatch.setattr(ledger, "_append_decision_tx", append_without_envelope)
    original = replace(
        _request(authority_key, "legacy-first"),
        required_capabilities=("code_review", "sealed_evidence"),
        isolation_required=True,
    )
    first = ledger.reserve_selection(original, _selection, now="2035-01-01T00:00:00Z")
    monkeypatch.setattr(ledger, "_append_decision_tx", original_append)
    ledger.settle(
        first.reservation_id,
        status="failed",
        failure_classification="result_invalid",
        now="2035-01-01T00:00:01Z",
    )
    substitute = replace(
        original,
        idempotency_key="legacy-substitute",
        route_mode="explicit",
        requested_reviewer="glm-5.2",
    )
    evidence = {
        "prior_reservation_id": first.reservation_id,
        "reason": "operator-authorized legacy result-invalid substitution",
        "review_id": "review_fixture",
        "authority_job_id": "authority-job_fixture",
        "authority_key": authority_key,
    }
    return substitute, evidence, first.reservation_id


def test_substitution_reconstructs_only_the_legacy_formal_review_default_envelope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        substitute, evidence, prior_id = _legacy_failed_result_invalid_reservation(
            ledger,
            monkeypatch,
            authority_key="repo:substitution:legacy-default",
        )
        second = ledger.reserve_selection(
            substitute,
            _glm_selection,
            now="2035-01-01T00:00:02Z",
            substitution=evidence,
        )

        assert second.attempt == 2
        reconstruction = [
            decision
            for decision in ledger.decisions(prior_id)
            if decision.event_type == "legacy_authorization_envelope_reconstructed"
        ]
        assert len(reconstruction) == 1
        assert reconstruction[0].evidence == {
            "authorization_envelope": {
                "required_capabilities": ["code_review", "sealed_evidence"],
                "data_egress_policy": None,
                "isolation_required": True,
            },
            "source": "formal-review-default-contract-before-6342",
            "substitution_reason": evidence["reason"],
        }
        assert "authorized_substitution" in {
            decision.event_type for decision in ledger.decisions(second.reservation_id)
        }


@pytest.mark.parametrize(
    "changed",
    (
        {"required_capabilities": ("code_review",)},
        {"data_egress_policy": "local_interactive"},
        {"isolation_required": False},
    ),
)
def test_substitution_rejects_legacy_envelope_expansion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    changed: dict[str, object],
) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        substitute, evidence, prior_id = _legacy_failed_result_invalid_reservation(
            ledger,
            monkeypatch,
            authority_key=f"repo:substitution:legacy-reject:{next(iter(changed))}",
        )
        with pytest.raises(
            RoutingReservationError,
            match="substitution_legacy_authorization_envelope_unavailable",
        ):
            ledger.reserve_selection(
                replace(substitute, **changed),
                _glm_selection,
                now="2035-01-01T00:00:02Z",
                substitution=evidence,
            )

        assert "legacy_authorization_envelope_reconstructed" not in {
            decision.event_type for decision in ledger.decisions(prior_id)
        }


def test_substitution_rolls_back_legacy_reconstruction_when_selection_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        substitute, evidence, prior_id = _legacy_failed_result_invalid_reservation(
            ledger,
            monkeypatch,
            authority_key="repo:substitution:legacy-rollback",
        )
        with pytest.raises(RoutingReservationUnavailable, match="no_policy_approved_route"):
            ledger.reserve_selection(
                substitute,
                lambda _context: None,
                now="2035-01-01T00:00:02Z",
                substitution=evidence,
            )

        assert "legacy_authorization_envelope_reconstructed" not in {
            decision.event_type for decision in ledger.decisions(prior_id)
        }


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("author_model", "glm-5.2"),
        ("author_family", "zhipu"),
        ("requested_role", "security-review"),
        ("requested_profile", "security"),
        ("requested_risk", "critical"),
        ("estimated_input_bytes", 1201),
        ("required_capabilities", ("code_review",)),
        ("data_egress_policy", "different-approved-policy"),
        ("isolation_required", False),
    ),
)
def test_substitution_rejects_authorization_envelope_drift(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        substitute, evidence = _failed_result_invalid_reservation(
            ledger,
            authority_key=f"repo:substitution:drift:{field}",
        )

        with pytest.raises(RoutingReservationError, match="substitution_authorization_envelope_drift"):
            ledger.reserve_selection(
                replace(substitute, **{field: value}),
                _glm_selection,
                now="2035-01-01T00:00:02Z",
                substitution=evidence,
            )


def test_substitution_rejects_active_or_non_result_invalid_prior(tmp_path: Path) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        active = ledger.reserve_selection(
            _request("repo:substitution:active", "first"),
            _selection,
            now="2035-01-01T00:00:00Z",
        )
        request = replace(
            _request("repo:substitution:active", "substitute"),
            route_mode="explicit",
            requested_reviewer="glm-5.2",
        )
        evidence = {"prior_reservation_id": active.reservation_id, "reason": "operator-authorized"}
        with pytest.raises(RoutingReservationError, match="substitution_prior_not_result_invalid"):
            ledger.reserve_selection(request, _glm_selection, substitution=evidence)

        ledger.settle(
            active.reservation_id,
            status="failed",
            failure_classification="transport_error",
            now="2035-01-01T00:00:01Z",
        )
        with pytest.raises(RoutingReservationError, match="substitution_prior_not_result_invalid"):
            ledger.reserve_selection(request, _glm_selection, substitution=evidence)


@pytest.mark.parametrize(
    ("reason", "error"),
    (
        ("", "substitution_reason_required"),
        ("x" * 501, "substitution_reason_too_long"),
    ),
)
def test_substitution_reason_is_required_and_bounded(tmp_path: Path, reason: str, error: str) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        substitute, evidence = _failed_result_invalid_reservation(
            ledger,
            authority_key=f"repo:substitution:reason:{len(reason)}",
        )
        with pytest.raises(RoutingReservationError, match=error):
            ledger.reserve_selection(
                substitute,
                _glm_selection,
                now="2035-01-01T00:00:02Z",
                substitution={**evidence, "reason": reason},
            )


def test_substitution_rejects_stale_link_and_ineligible_selection(tmp_path: Path) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        substitute, evidence = _failed_result_invalid_reservation(
            ledger,
            authority_key="repo:substitution:selection",
        )
        with pytest.raises(RoutingReservationError, match="substitution_prior_not_latest"):
            ledger.reserve_selection(
                substitute,
                _glm_selection,
                now="2035-01-01T00:00:02Z",
                substitution={**evidence, "prior_reservation_id": "routing-reservation_wrong"},
            )
        with pytest.raises(RoutingReservationError, match="substitution_selected_reviewer_mismatch"):
            ledger.reserve_selection(
                substitute,
                _selection,
                now="2035-01-01T00:00:02Z",
                substitution=evidence,
            )
        with pytest.raises(RoutingReservationError, match="substitution_same_family"):
            ledger.reserve_selection(
                substitute,
                lambda context: replace(_glm_selection(context), family="openai"),
                now="2035-01-01T00:00:02Z",
                substitution=evidence,
            )
        with pytest.raises(RoutingReservationError, match="substitution_reviewer_unchanged"):
            ledger.reserve_selection(
                replace(substitute, requested_reviewer="codex"),
                lambda context: replace(_selection(context), family="xai"),
                now="2035-01-01T00:00:02Z",
                substitution=evidence,
            )


def test_substitution_selector_or_admission_failure_leaves_no_compensating_reservation(
    tmp_path: Path,
) -> None:
    root = _root(tmp_path)
    with RoutingReservationLedger(root=root) as ledger:
        substitute, evidence = _failed_result_invalid_reservation(
            ledger,
            authority_key="repo:substitution:rollback",
        )
        prior = ledger.latest_for_authority_key(substitute.authority_key)
        assert prior is not None
        with pytest.raises(RoutingReservationUnavailable, match="no_policy_approved_route"):
            ledger.reserve_selection(
                substitute,
                lambda _context: None,
                now="2035-01-01T00:00:02Z",
                substitution=evidence,
            )
        assert ledger.latest_for_authority_key(substitute.authority_key) == prior
        assert "authorized_substitution" not in {
            decision.event_type for decision in ledger.decisions(prior.reservation_id)
        }

        ledger.reserve_selection(
            _request("repo:substitution:blocker", "blocker"),
            _selection,
            now="2035-01-01T00:00:02Z",
        )
        with pytest.raises(RoutingReservationUnavailable, match="credential_bucket_exhausted"):
            ledger.reserve_selection(
                substitute,
                _glm_selection,
                now="2035-01-01T00:00:03Z",
                substitution=evidence,
            )
        assert ledger.latest_for_authority_key(substitute.authority_key) == prior


def test_credential_admission_and_completed_bytes_are_independent_of_quota_bucket(
    tmp_path: Path,
) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        first = ledger.reserve_selection(_request("repo:credential-a", "first"), _selection, now="2035-01-01T00:00:00Z")

        def other_quota_same_credential(context: object) -> RoutingSelection:
            return replace(_selection(context), quota_bucket="shared-accounting-bucket")

        with pytest.raises(RoutingReservationUnavailable, match="credential_bucket_exhausted"):
            ledger.reserve_selection(
                _request("repo:credential-b", "second"),
                other_quota_same_credential,
                now="2035-01-01T00:00:01Z",
            )
        ledger.settle(
            first.reservation_id,
            status="complete",
            actual_input_bytes=8,
            actual_output_bytes=4,
            actual_input_tokens=2,
            actual_output_tokens=1,
            now="2035-01-01T00:00:02Z",
        )
        current = ledger._bucket_usage("codex-weekly", now_iso="2035-01-01T00:00:30Z", rolling_window_seconds=60)
        expired = ledger._bucket_usage("codex-weekly", now_iso="2035-01-01T00:02:30Z", rolling_window_seconds=60)
        assert current.completed_window_bytes == 12
        assert expired.completed_window_bytes == 0


def test_recent_failures_use_the_same_settlement_window_as_completed_usage(tmp_path: Path) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        old = ledger.reserve_selection(_request("repo:old-failure", "old"), _selection, now="2035-01-01T00:00:00Z")
        ledger.fail_and_release(old.reservation_id, "provider_unavailable", now="2035-01-01T00:00:00Z")

        current = ledger.reserve_selection(
            _request("repo:current-failure", "current"),
            _selection,
            now="2035-01-01T00:01:01Z",
        )
        ledger.fail_and_release(current.reservation_id, "provider_unavailable", now="2035-01-01T00:01:01Z")

        usage = ledger._bucket_usage("codex-weekly", now_iso="2035-01-01T00:01:01Z", rolling_window_seconds=60)
        assert usage.recent_failures == 1


def test_success_heals_circuit_without_erasing_failure_decisions(tmp_path: Path) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        failed = ledger.reserve_selection(_request("repo:failed", "failed"), _selection, now="2035-01-01T00:00:00Z")
        ledger.fail_and_release(
            failed.reservation_id,
            "provider_unavailable",
            circuit_open_seconds=30,
            now="2035-01-01T00:00:01Z",
        )

        with pytest.raises(RoutingReservationUnavailable, match="credential_bucket_circuit_open"):
            ledger.reserve_selection(_request("repo:blocked", "blocked"), _selection, now="2035-01-01T00:00:30Z")

        recovered = ledger.reserve_selection(
            _request("repo:recovered", "recovered"),
            _selection,
            now="2035-01-01T00:00:31Z",
        )
        ledger.settle(recovered.reservation_id, status="complete", now="2035-01-01T00:00:32Z")

        circuit = ledger.bucket_circuit_state("codex-weekly", "codex-api-key-a")
        assert circuit is not None
        assert circuit.recent_failure_count == 0
        assert circuit.open_until is None
        assert circuit.last_failure_classification == "provider_unavailable"
        assert {decision.event_type for decision in ledger.decisions(failed.reservation_id)} == {
            "reserved",
            "settled",
            "circuit_recorded",
        }
        assert {decision.event_type for decision in ledger.decisions(recovered.reservation_id)} == {
            "reserved",
            "settled",
            "circuit_healed",
        }


def test_ttl_recovery_does_not_clear_an_open_circuit(tmp_path: Path) -> None:
    def two_slot_selection(context: object) -> RoutingSelection:
        return replace(_selection(context), quota_limit=2, credential_limit=2)

    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        failed = ledger.reserve_selection(
            _request("repo:failed", "failed"), two_slot_selection, ttl_seconds=60, now="2035-01-01T00:00:00Z"
        )
        orphan = ledger.reserve_selection(
            _request("repo:orphan", "orphan"), two_slot_selection, ttl_seconds=10, now="2035-01-01T00:00:00Z"
        )
        ledger.fail_and_release(
            failed.reservation_id,
            "provider_unavailable",
            circuit_open_seconds=30,
            now="2035-01-01T00:00:01Z",
        )
        assert ledger.recover_expired(now="2035-01-01T00:00:10Z") == (ledger.get(orphan.reservation_id),)

        circuit = ledger.bucket_circuit_state("codex-weekly", "codex-api-key-a")
        assert circuit is not None and circuit.open_until == "2035-01-01T00:00:31Z"
        with pytest.raises(RoutingReservationUnavailable, match="credential_bucket_circuit_open"):
            ledger.reserve_selection(_request("repo:blocked", "blocked"), _selection, now="2035-01-01T00:00:10Z")


def test_quota_bucket_admission_is_shared_across_distinct_credentials(tmp_path: Path) -> None:
    with RoutingReservationLedger(root=_root(tmp_path)) as ledger:
        ledger.reserve_selection(
            _request("repo:quota-a", "first"),
            _selection,
            now="2035-01-01T00:00:00Z",
        )

        def same_quota_other_credential(context: object) -> RoutingSelection:
            return replace(_selection(context), credential_bucket="codex-api-key-b")

        with pytest.raises(RoutingReservationUnavailable, match="quota_bucket_exhausted"):
            ledger.reserve_selection(
                _request("repo:quota-b", "second"),
                same_quota_other_credential,
                now="2035-01-01T00:00:01Z",
            )
