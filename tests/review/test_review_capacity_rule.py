"""#10016: approved review allowance rule and operational snapshot boundary."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from scripts.fleet import credit_lane
from scripts.review import closeout_cli
from scripts.review.capacity import review_capacity, review_capacity_action
from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, ResolverInputs, evaluate_candidate, resolve_reviewer


def snapshot(*, remaining=54, short=96, stale=False, **lane):
    return {
        "diagnostics": {"stale": stale, "records_loaded": 5},
        "agents": {
            "claude": {
                "status": "hot",
                "status_source": "weekly_pace",
                "remaining_pct": remaining,
                "codexbar": {
                    "weekly_remaining_pct": remaining,
                    "primary_remaining_pct": short,
                    "weekly_pace_delta_pct": 9,
                    "will_last_to_reset": False,
                },
                **lane,
            },
        },
    }


def inputs(data):
    return ResolverInputs(author_model="gpt-6.1-sol", risk="critical", language_lane=True, routing_snapshot=data)


def test_c6b_pace_only_selects_opus_without_attesting_missing_health():
    result = resolve_reviewer(inputs(snapshot()))
    assert result.selected.concrete_model == "claude-opus-5-5"
    # Known allowance does not manufacture verified route health.
    assert result.selected.health != "healthy"
    assert result.selected.selection_score[:2] == (0, 9)


@pytest.mark.parametrize("key", ["claude", "claude-opus-5-5", "anthropic"])
@pytest.mark.parametrize("status", ["hot", " HOT ", "near_cap"])
@pytest.mark.parametrize("remaining", [54, 10])
def test_capacity_uses_the_same_supported_aliases_as_health(key, status, remaining):
    data = snapshot(remaining=remaining, status=status)
    record = data["agents"].pop("claude")
    data["agents"][key] = record
    result = resolve_reviewer(inputs(data))
    opus = next(item for item in result.trace if item.name == "claude-opus-5-5")
    assert opus.capacity.remaining_pct == remaining
    assert opus.capacity.near_cap is (remaining == 10)
    if remaining == 10:
        assert result.selected is None
    else:
        assert result.selected.name == "claude-opus-5-5"
        assert result.selected.health is None
        assert result.selected.capacity.pressure == result.selected.selection_score[1] == 9


def test_model_health_alias_cannot_hide_canonical_seat_exhaustion():
    data = snapshot(remaining=5)
    data["agents"]["claude-opus-5-5"] = {"status": "cool", "health": {"healthy": True}}
    result = resolve_reviewer(inputs(data))
    assert result.selected is None
    opus = next(item for item in result.trace if item.name == "claude-opus-5-5")
    assert opus.capacity.remaining_pct == 5 and opus.capacity.near_cap


@pytest.mark.parametrize("weekly,short", [(10, 96), (54, 10), (0, 96), (54, 0)])
def test_tightest_allowance_at_or_below_reserve_excludes(weekly, short):
    result = resolve_reviewer(inputs(snapshot(remaining=weekly, short=short)))
    assert result.selected is None
    assert any(item.health == "near_cap" and "near cap" in item.reason for item in result.trace)


def test_policy_threshold_is_used(monkeypatch):
    policy = replace(credit_lane.load_policy(), near_cap_remaining_pct=55)
    monkeypatch.setattr(credit_lane, "load_policy", lambda: policy)
    assert resolve_reviewer(inputs(snapshot())).selected is None


def test_capacity_reads_one_fresh_policy_per_call(monkeypatch):
    policy = credit_lane.load_policy()
    policies = iter([
        replace(policy, near_cap_remaining_pct=10, credit_max_age_s=30),
        replace(policy, near_cap_remaining_pct=20, credit_max_age_s=60),
    ])
    reads = []

    def load_policy():
        value = next(policies)
        reads.append(value)
        return value

    monkeypatch.setattr(credit_lane, "load_policy", load_policy)
    record = {"remaining_pct": 15, "codexbar": {"freshness": "fresh", "age_s": 45}}
    first = review_capacity(record, {"stale": False})
    second = review_capacity(record, {"stale": False})
    assert len(reads) == 2
    assert first.freshness == credit_lane.STALE and not first.near_cap
    assert second.freshness == credit_lane.FRESH and second.near_cap


@pytest.mark.parametrize("data", [snapshot(stale=True, remaining=0), {"agents": {"claude": {"status": "near_cap"}}}])
def test_stale_or_missing_allowance_is_advisory_and_recorded(data):
    result = resolve_reviewer(inputs(data))
    assert result.selected.concrete_model == "claude-opus-5-5"
    assert result.selected.health is None
    capacity = review_capacity(data["agents"]["claude"], data.get("diagnostics"))
    assert capacity.freshness in {credit_lane.STALE, credit_lane.UNKNOWN}
    assert capacity.fallback_reason
    assert not capacity.near_cap


def test_pace_pressure_orders_only_equal_fits():
    data = snapshot()
    data["agents"]["codex"] = {"status": "cool", "remaining_pct": 40}
    result = resolve_reviewer(ResolverInputs(author_model="grok-4.7", risk="critical", routing_snapshot=data))
    assert result.selected.concrete_model == "gpt-6.1-sol"
    # Suitability/tier remains ahead of pressure: Sonnet cannot replace Opus at critical.
    assert resolve_reviewer(inputs(data)).selected.concrete_model == "claude-opus-5-5"


def test_10016_known_capacity_with_pace_pressure_precedes_unknown_capacity():
    data = snapshot(remaining=80, status="cool", health={"healthy": True})
    data["agents"]["claude"]["codexbar"]["weekly_pace_delta_pct"] = 1
    result = resolve_reviewer(ResolverInputs(author_model="grok-4.7", risk="critical", routing_snapshot=data))

    assert result.selected.concrete_model == "claude-opus-5-5"
    assert result.selected.health == "healthy"
    sol = next(item for item in result.trace if item.name == "openai_frontier")
    assert sol.status == "eligible"
    assert sol.capacity.remaining_pct is None
    assert sol.capacity.freshness == credit_lane.UNKNOWN
    assert result.selected.selection_score < sol.selection_score


@pytest.mark.parametrize(
    "lane,reason",
    [
        ({"runtime": {"headroom_blocked": True}}, "runtime headroom"),
        ({"scheduler": {"capacity_exhausted": True, "active_reserved_input_bytes": 900}}, "concurrency"),
        ({"scheduler": {"circuit_open": True}}, "circuit"),
        ({"health": {"healthy": False}}, "unhealthy"),
    ],
)
def test_sole_reviewer_still_refuses_runtime_concurrency_and_circuit(lane, reason):
    data = snapshot(**lane)
    assert resolve_reviewer(inputs(data)).selected is None
    blocked, cause = review_capacity_action("claude", data["agents"]["claude"], data["diagnostics"], "claude-opus-5-5")
    assert blocked and reason in cause


def test_active_reservation_still_excludes_sole_bucket():
    assert resolve_reviewer(inputs(snapshot()), excluded_quota_buckets=frozenset({"claude"})).selected is None


def run_cli(tmp_path, capsys, *extra):
    result = closeout_cli.main(
        [
            "--state-file",
            str(tmp_path / "state.json"),
            "resolve-reviewer",
            "--author-model",
            "gpt-6.1-sol",
            "--risk",
            "critical",
            "--owned-path",
            "ordinary.py",
            "--language-lane",
            *extra,
        ]
    )
    return result, json.loads(capsys.readouterr().out)


def test_same_snapshot_bytes_live_and_file_select_identically(tmp_path, capsys, monkeypatch):
    raw = json.dumps(snapshot()).encode()
    reads = []

    def read(**kwargs):
        reads.append(kwargs)
        return json.loads(raw)

    monkeypatch.setattr(credit_lane, "read_routing_budget", read)
    live_code, live = run_cli(tmp_path, capsys)
    path = tmp_path / "snapshot.json"
    path.write_bytes(raw)
    file_code, explicit = run_cli(tmp_path, capsys, "--routing-snapshot-file", str(path))
    assert live_code == file_code == 0
    assert live["selected"] == explicit["selected"]
    assert live["trace"] == explicit["trace"]
    assert reads == [{"timeout": 8.0}]
    assert live["routing_snapshot"] == {"source": "live", "freshness": "fresh", "fallback_reason": None}
    assert explicit["routing_snapshot"]["source"] == "file"


def test_differing_file_wins_without_live_read(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(
        credit_lane, "read_routing_budget", lambda **_: pytest.fail("explicit file must bypass live read")
    )
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot(remaining=0)))
    code, result = run_cli(tmp_path, capsys, "--routing-snapshot-file", str(path))
    assert code == 1 and result["selected"] is None
    assert result["routing_snapshot"]["source"] == "file"


@pytest.mark.parametrize(
    "data,freshness,reason",
    [
        (None, "unknown", "live routing snapshot unavailable"),
        (snapshot(stale=True), "stale", "routing-budget snapshot is stale"),
    ],
)
def test_live_fallback_receipt(tmp_path, capsys, monkeypatch, data, freshness, reason):
    monkeypatch.setattr(credit_lane, "read_routing_budget", lambda **_: data)
    code, result = run_cli(tmp_path, capsys)
    assert code == 0
    assert result["routing_snapshot"] == {"source": "live", "freshness": freshness, "fallback_reason": reason}
    assert result["selected"]["health"] is None


def test_unreadable_policy_keeps_retained_reserve(monkeypatch):
    monkeypatch.setattr(credit_lane, "load_policy", lambda: (_ for _ in ()).throw(ValueError("unreadable")))
    assert review_capacity({"remaining_pct": 10}, {"stale": False}).near_cap
    assert not review_capacity({"remaining_pct": 11}, {"stale": False}).near_cap


def test_capacity_free_evaluation_has_no_live_reads(monkeypatch):
    monkeypatch.setattr(credit_lane, "read_routing_budget", lambda **_: pytest.fail("resolver must stay injected"))
    result = evaluate_candidate(REVIEW_CANDIDATES["claude-opus-5-5"], replace(inputs(None), routing_snapshot=None))
    assert result.status == "eligible" and result.health is None


def test_legacy_normalization_keeps_writer_policy_and_hot_orders_equal_review_fits():
    from scripts.review.reviewer_resolver import normalize_routing_snapshot

    data = {"claude": "hot", "codex": "healthy"}
    assert normalize_routing_snapshot(data) == {"claude": "near_cap", "codex": "healthy"}
    result = resolve_reviewer(ResolverInputs(author_model="grok-4.7", risk="critical", routing_snapshot=data))
    assert result.selected.concrete_model == "gpt-6.1-sol"
    assert next(item for item in result.trace if item.concrete_model == "claude-opus-5-5").status == "eligible"


@pytest.mark.parametrize("delta", [None, True, float("nan"), float("inf"), -5])
def test_invalid_or_negative_pace_does_not_invent_pressure(delta):
    assert review_capacity({"codexbar": {"weekly_pace_delta_pct": delta}}).pressure == 0


@pytest.mark.parametrize(
    "record,reason",
    [
        ({"eligible": False}, "ineligible"),
        ({"login_state": "NEED_LOGIN"}, "NEED_LOGIN"),
        ({"probe_state": "NEED_LOGIN"}, "NEED_LOGIN"),
        ({"status": "unhealthy"}, "unhealthy"),
        ({"circuit_open": True}, "circuit"),
        ({"runtime": {"circuit_open": True}}, "circuit"),
    ],
)
def test_existing_admission_hard_blocks(record, reason):
    blocked, cause = review_capacity_action("claude", record, None, "claude-opus-5-5")
    assert blocked and reason in cause


def test_sole_pace_only_reviewer_cannot_exceed_durable_reservation_limits(tmp_path):
    from scripts.fleet_comms.routing_reservations import (
        RoutingReservationLedger,
        RoutingReservationRequest,
        RoutingReservationUnavailable,
        RoutingSelection,
    )

    reads = []

    def select(_context):
        data = snapshot()
        reads.append(data)
        result = resolve_reviewer(inputs(data))
        selected = result.selected
        assert selected.concrete_model == "claude-opus-5-5"
        return RoutingSelection(
            candidate=selected.name,
            route=selected.route,
            model=selected.concrete_model,
            family=selected.family,
            quota_bucket=selected.quota_bucket,
            credential_bucket=selected.credential_bucket,
            quota_limit=selected.quota_limit,
            credential_limit=selected.credential_limit,
            policy_version=result.policy_version,
            quota_snapshot=data,
        )

    selected = select(None)
    reads.clear()
    limit = min(selected.quota_limit, selected.credential_limit)
    assert limit > 0
    with RoutingReservationLedger(root=tmp_path / "fleet") as ledger:
        for index in range(limit + 1):
            request = RoutingReservationRequest(
                authority_key=f"head-{index}",
                idempotency_key=f"request-{index}",
                initiator="codex",
                author_model="gpt-6.1-sol",
                author_family="openai",
                requested_role="formal-review",
                requested_profile="code",
                requested_risk="critical",
                route_mode="auto",
                estimated_input_bytes=100,
            )
            if index < limit:
                assert ledger.reserve_selection(request, select).reservation_id
            else:
                with pytest.raises(RoutingReservationUnavailable, match=r"(credential|quota)_bucket_exhausted"):
                    ledger.reserve_selection(request, select)
    assert len(reads) == limit + 1
