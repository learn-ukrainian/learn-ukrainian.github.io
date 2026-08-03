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
