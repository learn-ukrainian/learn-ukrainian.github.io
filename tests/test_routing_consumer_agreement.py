"""#9740: equivalent routing inputs give equivalent decisions in every capacity and admission consumer.

One routing-budget snapshot per case is built through the real producer
(:func:`state_router.compute_routing_budget`) from external-seam fixtures only:
provider usage records (CodexBar payloads), lane-health task records (or a
tasks directory the scan cannot read), runtime outcome summaries and the
rate-limit records reader. The same object goes to every consumer:

* budget producer and recommendation (``agents.<lane>.routing_facts``, ``recommendation``);
* picker rows, order and CLI (:mod:`scripts.fleet.capacity_pick`);
* budget guard and final admission (``delegate._resolve_agent_with_budget_guard``,
  :func:`credit_lane.dispatch_refusal`) — owned by #9739, round 2;
* reviewer resolver (#9739, round 2) and scheduler;
* curriculum wave gate (``curriculum_coordinator._health_assessment``);
* idle assembly (``idle_settle.assemble_snapshot`` over the picker rows).

Each decision is compared with the owner's facts (:func:`credit_lane.routing_facts`)
for the same record before its final action. Legitimate restrictions keep their
own asserted reasons: the wave's acceptable statuses, positive-health and
freshness requirement; retirement in the picker; the resolver's near-cap
exclusion of a stale deficit; delegate's stale-advisory no-hard-substitution.
Consumers that still disagree are present and marked ``xfail(strict=True)``
until round 2. No case reaches a provider: every provider seam is captured and
must record zero calls.

Recon inventory disposition (``recon-9740``; R = repaired here, A = agrees,
D = different question, 2 = round 2 after #9739):

=====================================================  ===  =========================================
consumer                                               disp evidence in this module / owned tests
=====================================================  ===  =========================================
state_router._capacity_used_pct                        D    raw used-% metric; status via the owner
state_router._status_from_weekly_used                  A    owner ``pace_deficit_state``
state_router._attach_credit_states                     A    owner ``lane_credit_state``
state_router._recommend_agent                          R    F2 stale label, F4 unknown health
state_router.compute_routing_budget (health fill-in)   R    A1 typed scan; A6 freshness labels
state_router._api_lane_status_from_account             A    F8 duplicate, agrees (prepaid)
lane_health.compute_lane_health                        R    A1 ``scan_lane_health``
subscription_usage.pace_is_deficit                     R    F3 one alias reader ``pace_expected_pct``
project_state_store.any_lane_under_weekly_pace         D    notebook overlay, not admission
reset_reserve.codex_is_threatened / _eligible          D    operator reserve precondition
prepaid_status.api_lane_status_from_account            A    F8 duplicate, agrees
capacity_pick.remaining_pct                            R    F1 owner ``plan_remaining_pct``
capacity_pick.is_avoid_lane / build_lane_rows          R    F2/F3/F4/F7 owner ``routing_facts``
capacity_pick.build_pick_order / cooler_lanes          R    A5 stale rank, strict
delegate._budget_needs_hard_capacity_action            2    F3 alias/source split (xfail below)
delegate._resolve_agent_with_budget_guard              2    agreement asserted; xfail where split
delegate._credit_period_refusal / dispatch_refusal     A    A4 CREDIT_PERIOD_MODEL_REFUSED
delegate._budget_cooler_lanes                          2    no model/staleness forwarding (A4: dropped)
delegate._check_capacity_hint                          D    in-flight hint only
idle_settle._lane_quota_ok / LaneState                 R    F5 unknown quota and load
fleet.usage._credit_state_text                         D    display of the published state
curriculum_coordinator._health_assessment              R    F4 owner health, F6 full-record relief
reviewer_resolver.evaluate_candidate                   2    F6 leaf-only relief (xfail below)
reviewer_scheduler.metrics_for                         R    F1 remaining, F5 freshness/counts
bench_health._bench_inventory                          A    forwards ``evaluate_candidate``
agent_runtime.usage.has_headroom                       D    pre-call 429 block, own window
=====================================================  ===  =========================================
"""

from __future__ import annotations

import copy
import json
import subprocess
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from scripts import delegate
from scripts.api import state_router
from scripts.fleet import capacity_pick, credit_lane, idle_settle
from scripts.fleet.reset_reserve import unavailable_reserve
from scripts.orchestration import curriculum_coordinator as coordinator
from scripts.review import reviewer_scheduler
from scripts.review.model_catalog import retired_model_refusal
from scripts.review.reviewer_resolver import OPENAI_FRONTIER, ResolverInputs, evaluate_candidate
from tests.api.test_routing_budget import _configure_base

NOW = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
FETCHED = "2026-10-05T11:59:30Z"
RESETS = "2026-10-09T12:00:00Z"
ROUTE_MODEL = "gpt-6.1-sol"
OFF_ALLOWLIST_MODEL = "gpt-5-codex"
ROUND_2 = "#9740 round 2 after #9739"
NEAR_CAP_LEDGER_GATE = (
    "delegate hard-acts on near_cap only with a non-empty USD ledger (records_loaded > 0); "
    "a CodexBar-only near_cap lane is kept"
)


def _codex(**overrides: Any) -> dict[str, Any]:
    """CodexBar payload for Codex: cool, on pace, fresh probe, no reserves."""
    payload: dict[str, Any] = {
        "lane": "codex",
        "source": "codex_oauth",
        "weekly_used_pct": 20.0,
        "weekly_remaining_pct": 80.0,
        "primary_used_pct": 5.0,
        "primary_remaining_pct": 95.0,
        "weekly_expected_pct": 30.0,
        "weekly_pace_delta_pct": -10.0,
        "will_last_to_reset": True,
        "weekly_resets_at": RESETS,
        "freshness": "fresh",
        "age_s": 30.0,
        "fetched_at": FETCHED,
        "stale": False,
    }
    payload.update(overrides)
    return payload


def _deficit(**overrides: Any) -> dict[str, Any]:
    """A visible weekly-pace deficit above the cap (40% used, 15 points ahead, runs out before reset)."""
    deficit: dict[str, Any] = {
        "weekly_used_pct": 40.0,
        "weekly_remaining_pct": 60.0,
        "weekly_expected_pct": 25.0,
        "weekly_pace_delta_pct": 15.0,
        "will_last_to_reset": False,
    }
    return _codex(**{**deficit, **overrides})


CLAUDE = {
    "lane": "claude",
    "source": "claude_oauth",
    "weekly_used_pct": 10.0,
    "weekly_remaining_pct": 90.0,
    "weekly_expected_pct": 30.0,
    "weekly_pace_delta_pct": -20.0,
    "will_last_to_reset": True,
    "weekly_resets_at": RESETS,
    "freshness": "fresh",
    "age_s": 30.0,
    "fetched_at": FETCHED,
}


# Cursor's own Auto status says hot (status_source cursor_auto) while weekly pace is hidden.
CURSOR_HOT_HIDDEN = {
    "lane": "cursor",
    "source": "cursor_native",
    "status": "hot",
    "login_state": "authenticated",
    "probe_state": "healthy",
    "weekly_used_pct": 30.0,
    "weekly_remaining_pct": 70.0,
    "weekly_expected_pct": 0.1,
    "weekly_pace_delta_pct": 20.0,
    "will_last_to_reset": False,
    "provider_windows": {"auto": {"window": "monthly", "used_pct": 30.0, "remaining_pct": 70.0}},
    "freshness": "fresh",
    "age_s": 30.0,
    "fetched_at": FETCHED,
}


@dataclass(frozen=True)
class Case:
    """One producer snapshot from external seams; ``tasks`` is ``idle`` (scan ran, nothing recent) or ``missing``."""

    name: str
    payloads: dict[str, dict[str, Any] | None]
    tasks: str = "idle"
    runtime_blocked: frozenset[str] = frozenset()
    mutate: str | None = None
    xfail: dict[str, str] = field(default_factory=dict)


CASES: tuple[Case, ...] = (
    # The six snapshot families.
    Case("healthy", {"codex": _codex(), "claude": CLAUDE}),
    Case("covered_deficit", {"codex": _deficit(credit_balance=62500.0), "claude": CLAUDE}),
    Case("uncovered_deficit", {"codex": _deficit(credit_balance=0.0), "claude": CLAUDE}),
    Case(
        "stale_relief",
        {"codex": _deficit(credit_balance=62500.0, stale=True, freshness="stale_last_good"), "claude": CLAUDE},
    ),
    Case("unavailable_telemetry", {"codex": None, "claude": None}, tasks="missing"),
    Case("catalog_disallowed", {"codex": _codex(), "claude": CLAUDE}),
    # Split variants.
    Case(
        "f1_conflicting_windows",
        {"codex": _codex(primary_used_pct=97.0, primary_remaining_pct=3.0), "claude": CLAUDE},
        xfail={"budget_guard": NEAR_CAP_LEDGER_GATE},
    ),
    Case(
        "f2_stale_near_cap_credit",
        {
            "codex": _codex(
                weekly_used_pct=95.0,
                weekly_remaining_pct=5.0,
                credit_balance=62500.0,
                stale=True,
                freshness="stale_last_good",
            ),
            "claude": CLAUDE,
        },
    ),
    Case("f3_hidden_pace", {"codex": _deficit(weekly_expected_pct=0.1), "claude": CLAUDE}),
    Case(
        "f3_hidden_pace_runtime_blocked",
        {"codex": _deficit(weekly_expected_pct=0.1), "claude": CLAUDE},
        runtime_blocked=frozenset({"codex"}),
    ),
    Case(
        "f3_conflicting_aliases",
        {"codex": _deficit(expectedUsedPercent=0.1, weekly_expected_pct=40.0), "claude": CLAUDE},
    ),
    Case("f4_scan_error_health", {"codex": _codex(), "claude": CLAUDE}, tasks="missing"),
    Case(
        "f3_hidden_pace_non_pace_source",
        {"codex": _codex(), "claude": CLAUDE, "cursor": CURSOR_HOT_HIDDEN},
        xfail={
            "budget_guard_cursor": "F3: delegate clears a hidden-pace hot label without checking status_source",
        },
    ),
    Case(
        "f6_contradictory_relief",
        {"codex": _codex(weekly_used_pct=95.0, weekly_remaining_pct=5.0, credit_balance=62500.0), "claude": CLAUDE},
        mutate="probe_relabelled_stale_after_publication",
        xfail={
            "resolver": "F6: the resolver still re-checks only the published credit leaf",
            "budget_guard": NEAR_CAP_LEDGER_GATE,
        },
    ),
    Case(
        "f7_near_cap_credit",
        {"codex": _codex(weekly_used_pct=95.0, weekly_remaining_pct=5.0, credit_balance=62500.0), "claude": CLAUDE},
    ),
)
CASE_IDS = [case.name for case in CASES]


class ProviderCalls(list):
    """Captured provider-facing calls (prompt subprocesses, network, live usage refresh)."""


_VERSION_PROBES = frozenset({"--version", "--help"})


class _FrozenDatetime(datetime):
    """One clock for every consumer: owner calls made without ``now`` read this instant."""

    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return NOW.astimezone(tz) if tz is not None else NOW.replace(tzinfo=None)


@pytest.fixture
def provider_calls(monkeypatch: pytest.MonkeyPatch) -> ProviderCalls:
    """Capture every provider seam. Local ``--version``/``--help`` binary probes are answered, not counted."""
    calls = ProviderCalls()

    def capture(name: str):
        def recorder(*args: Any, **kwargs: Any) -> Any:
            argv = args[0] if args else kwargs.get("args")
            if name == "subprocess.run" and isinstance(argv, (list, tuple)) and _VERSION_PROBES & set(argv[1:]):
                return subprocess.CompletedProcess(argv, 0, stdout="0.0.0\n", stderr="")
            calls.append((name, argv))
            raise AssertionError(f"provider call attempted: {name}")

        return recorder

    monkeypatch.setattr(subprocess, "Popen", capture("subprocess.Popen"))
    monkeypatch.setattr(subprocess, "run", capture("subprocess.run"))
    monkeypatch.setattr(urllib.request, "urlopen", capture("urllib.request.urlopen"))
    monkeypatch.setattr(state_router, "refresh_provider_usage_data", capture("refresh_provider_usage_data"))
    monkeypatch.setattr(state_router, "refresh_api_account_data", capture("refresh_api_account_data"))
    monkeypatch.setattr(credit_lane, "datetime", _FrozenDatetime)
    return calls


def _runtime(lane: str, blocked: bool) -> dict[str, Any]:
    return {
        "source": "agent_runtime_jsonl",
        "window_s": 300,
        "ok": 1,
        "error": 0,
        "rate_limited": 2 if blocked else 0,
        "timeout": 0,
        "other": 0,
        "total": 3 if blocked else 1,
        "last_outcome_at": FETCHED,
        "last_rate_limited_at": FETCHED if blocked else None,
        "models_rate_limited": [ROUTE_MODEL] if blocked else [],
        "headroom_blocked": blocked,
        "headroom_reason": "2 rate_limited in 300s" if blocked else "",
    }


def produce(case: Case, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Any]:
    """The real producer over this case's external-seam fixtures; one snapshot shared by every consumer."""
    budget_path = _configure_base(monkeypatch, tmp_path)
    tasks_dir = tmp_path / "tasks"
    if case.tasks == "missing":
        tasks_dir = tmp_path / "unreadable-tasks"
    payloads = copy.deepcopy(case.payloads)
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda lane: copy.deepcopy(payloads.get(lane)))
    monkeypatch.setattr(state_router, "get_cursor_lane_usage", lambda: copy.deepcopy(payloads.get("cursor")))
    monkeypatch.setattr(state_router, "summarize_fleet_burn", lambda *_a, **_k: {"windows": {}})
    monkeypatch.setattr(
        state_router, "summarize_lane_runtime", lambda lane, **_k: _runtime(lane, lane in case.runtime_blocked)
    )
    budget = state_router.compute_routing_budget(
        NOW,
        budget_config_path=budget_path,
        tasks_dir=tasks_dir,
        project_root=tmp_path,
        curriculum_root=tmp_path,
        batch_state_dir=tmp_path,
    )
    if case.mutate == "probe_relabelled_stale_after_publication":
        # F6: the published credit leaf says credit_balance_present, but the probe record it
        # rests on is now stale_last_good (a later partial refresh). Only the record changes.
        assert budget["agents"]["codex"]["credit"]["state"] == credit_lane.CREDIT_BALANCE_PRESENT
        budget["agents"]["codex"]["freshness"] = "stale_last_good"
        budget["agents"]["codex"]["codexbar"]["freshness"] = "stale_last_good"
    return json.loads(json.dumps(budget))  # the JSON boundary every consumer reads across


def owner(budget: dict[str, Any], lane: str = "codex", *, model: str | None = None) -> credit_lane.RoutingFacts:
    return credit_lane.routing_facts(
        lane,
        budget["agents"].get(lane),
        model=model,
        snapshot_metadata=budget["diagnostics"],
        now=NOW,
    )


def _case_marks(case: Case, consumer: str) -> list[Any]:
    reason = case.xfail.get(consumer)
    return [pytest.mark.xfail(strict=True, reason=f"{ROUND_2}: {reason}")] if reason else []


def _params(consumer: str) -> list[Any]:
    return [pytest.param(case, id=case.name, marks=_case_marks(case, consumer)) for case in CASES]


@pytest.fixture
def snapshot(request, monkeypatch, tmp_path, provider_calls):
    budget = produce(request.param, monkeypatch, tmp_path)
    yield request.param, budget
    assert list(provider_calls) == [], "a routing consumer reached a provider"


# --- shared facts in the producer ---------------------------------------------------


@pytest.mark.parametrize("snapshot", _params("producer"), indirect=True)
def test_producer_publishes_the_owner_facts(snapshot):
    case, budget = snapshot
    if case.mutate is not None:
        # The published copy is the producer's at publication; consumers recompute and never trust it.
        published = budget["agents"]["codex"]["routing_facts"]
        assert published["credit_state"] == credit_lane.CREDIT_BALANCE_PRESENT
        assert owner(budget).credit["state"] == credit_lane.CREDITS_UNVERIFIED
        return
    for lane in ("codex", "claude"):
        published = dict(budget["agents"][lane]["routing_facts"])
        facts = owner(budget, lane)
        assert published.pop("credit_state") == facts.credit.get("state")
        assert published["capacity"] == facts.capacity, lane
        assert published["health"] == facts.health, lane
        assert published["observation_freshness"] == facts.observation_freshness, lane
        assert published["plan_remaining_pct"] == facts.plan_remaining_pct, lane


@pytest.mark.parametrize("snapshot", _params("recommendation"), indirect=True)
def test_recommendation_agrees_with_owner_capacity(snapshot):
    _case, budget = snapshot
    rec = budget["recommendation"]
    facts = owner(budget)
    if rec["primary_agent_for_code"] == "codex":
        assert facts.capacity == credit_lane.CAPACITY_VERIFIED
    stale_label = any(f"lane codex: {credit_lane.STALE_ADVISORY_LABEL}" in w for w in rec["warnings"])
    assert stale_label is (facts.capacity == credit_lane.CAPACITY_UNKNOWN_STALE)
    if facts.health == credit_lane.UNKNOWN:
        assert not any("skipped for recommendation" in w for w in rec["warnings"])


# --- picker rows, order and CLI -------------------------------------------------------


def _rows(budget: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = capacity_pick.build_lane_rows(budget, reset_reserve=unavailable_reserve(), now=NOW)
    return {row["lane"]: row for row in rows}


@pytest.mark.parametrize("snapshot", _params("picker"), indirect=True)
def test_picker_rows_agree_with_owner_facts(snapshot):
    _case, budget = snapshot
    rows = _rows(budget)
    for lane in ("codex", "claude"):
        row, facts = rows[lane], owner(budget, lane)
        assert row["remaining_pct"] == facts.plan_remaining_pct
        assert row["health"] == facts.health
        assert row["capacity"]["state"] == facts.capacity, lane
        assert row["avoid"] is (facts.capacity == credit_lane.CAPACITY_AVOID)
        assert (lane in capacity_pick.cooler_lanes(list(rows.values()))) is (
            facts.capacity == credit_lane.CAPACITY_VERIFIED
        )
    # Legitimate picker-local restriction: retired aliases stay AVOID with their own reason.
    for retired, target in (("gemini", "agy"), ("glm", "cursor")):
        assert rows[retired]["avoid"] is True
        assert f"retired→{target}" in rows[retired]["notes"]


@pytest.mark.parametrize("snapshot", _params("picker_cli"), indirect=True)
def test_picker_cli_reports_the_same_rows(snapshot, monkeypatch, capsys):
    _case, budget = snapshot
    from scripts.fleet import usage

    monkeypatch.setattr(usage, "read_budget", lambda **_kwargs: budget)
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: None)
    monkeypatch.setattr(capacity_pick, "load_reset_reserve", lambda *_a, **_k: unavailable_reserve())
    monkeypatch.setattr(capacity_pick, "admission_status", lambda: {"admitted": None, "line": "admission: fixture"})
    rc = capacity_pick.main(["--json", "--strict"])
    report = json.loads(capsys.readouterr().out)
    expected = _rows(budget)
    for row in report["rows"]:
        assert row["capacity"] == expected[row["lane"]]["capacity"]
        assert row["status"] == expected[row["lane"]]["status"]
    assert rc == (0 if report["cooler_lanes"] else 2)
    verified = [r["lane"] for r in report["pick_order"] if r["capacity"]["state"] == credit_lane.CAPACITY_VERIFIED]
    stale = [r["lane"] for r in report["pick_order"] if r["capacity"]["state"] == credit_lane.CAPACITY_UNKNOWN_STALE]
    order = [r["lane"] for r in report["pick_order"]]
    # A5: an UNKNOWN — stale/advisory row never ranks ahead of fresh verified capacity.
    for lane in stale:
        assert all(order.index(lane) > order.index(other) for other in verified)


# --- budget guard and final admission (round 2) -------------------------------------


def _guard(budget: dict[str, Any], monkeypatch: pytest.MonkeyPatch, model: str) -> str:
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: budget)
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_a, **_k: unavailable_reserve())
    return delegate._resolve_agent_with_budget_guard("codex", requested_model=model, fallbacks={"codex": "claude"})


@pytest.mark.parametrize("snapshot", _params("budget_guard"), indirect=True)
def test_budget_guard_agrees_with_owner_route_facts(snapshot, monkeypatch):
    _case, budget = snapshot
    facts = owner(budget, model=ROUTE_MODEL)
    chosen = _guard(budget, monkeypatch, ROUTE_MODEL)
    if budget["diagnostics"].get("stale"):
        # Legitimate restriction (A2): a stale snapshot is advisory in delegate; never a hard substitution.
        assert chosen == "codex"
    elif facts.capacity == credit_lane.CAPACITY_AVOID:
        assert chosen == "claude"
    else:
        assert chosen == "codex"


@pytest.mark.parametrize("snapshot", _params("budget_guard_cursor"), indirect=True)
def test_budget_guard_honours_the_hot_label_source(snapshot, monkeypatch):
    """F3 source restriction: only a weekly-pace hot label may be cleared by hidden pace (A3)."""
    _case, budget = snapshot
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: budget)
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_a, **_k: unavailable_reserve())
    facts = owner(budget, "cursor")
    chosen = delegate._resolve_agent_with_budget_guard("cursor", requested_model=None, fallbacks={"cursor": "claude"})
    if budget["diagnostics"].get("stale") or facts.capacity != credit_lane.CAPACITY_AVOID:
        assert chosen == "cursor"
    else:
        assert chosen == "claude", facts.capacity_reason


@pytest.mark.parametrize("snapshot", _params("final_admission"), indirect=True)
def test_final_admission_refuses_off_allowlist_models_exactly_when_the_owner_does(snapshot, monkeypatch):
    """A4/F7: an off-allowlist model with credit present ends in CREDIT_PERIOD_MODEL_REFUSED, never a substitution."""
    _case, budget = snapshot
    monkeypatch.setattr(credit_lane, "read_routing_budget", lambda **_kwargs: budget)
    refusal = credit_lane.dispatch_refusal("codex", OFF_ALLOWLIST_MODEL)
    facts = owner(budget, model=OFF_ALLOWLIST_MODEL)
    assert (refusal is not None) is (facts.model_permission is False)
    if refusal is not None:
        assert refusal.startswith(credit_lane.REFUSAL_CODE)
    assert credit_lane.dispatch_refusal("codex", ROUTE_MODEL) is None


@pytest.mark.parametrize("snapshot", _params("catalog"), indirect=True)
def test_catalog_disallowed_route_is_refused_before_any_provider_call(snapshot):
    """Healthy capacity never admits a retired route: the catalog refuses first (zero provider calls)."""
    _case, budget = snapshot
    assert retired_model_refusal("grok-4.6") is not None or retired_model_refusal("gpt-5.5") is not None
    assert retired_model_refusal(ROUTE_MODEL) is None
    rows = _rows(budget)
    assert rows["gemini"]["avoid"] is True and rows["gemini"]["capacity"]["state"] == credit_lane.CAPACITY_AVOID


# --- reviewer resolver (round 2) and scheduler ----------------------------------------


@pytest.mark.parametrize("snapshot", _params("resolver"), indirect=True)
def test_resolver_agrees_with_owner_route_facts(snapshot):
    _case, budget = snapshot
    facts = owner(budget, model=OPENAI_FRONTIER.concrete_model)
    result = evaluate_candidate(
        OPENAI_FRONTIER, ResolverInputs(author_model="claude-opus-5-5", routing_snapshot=budget)
    )
    if facts.capacity == credit_lane.CAPACITY_AVOID:
        assert result.status == "excluded", result.reason
    elif facts.capacity == credit_lane.CAPACITY_UNKNOWN_STALE:
        # Legitimate stricter restriction (A2): the resolver's near-cap exclusion of an uncovered
        # deficit is unchanged on a stale snapshot.
        assert result.status == "excluded" and "near" in str(result.reason)
    elif facts.capacity == credit_lane.CAPACITY_VERIFIED:
        assert result.status != "excluded", result.reason


@pytest.mark.parametrize("snapshot", _params("scheduler"), indirect=True)
def test_scheduler_metrics_are_the_owner_readings(snapshot):
    _case, budget = snapshot
    facts = owner(budget)
    metrics = reviewer_scheduler.metrics_for(OPENAI_FRONTIER, budget)
    assert metrics.quota_remaining_pct == facts.plan_remaining_pct
    expected_fresh = {credit_lane.FRESH: True, credit_lane.STALE: False}.get(facts.observation_freshness)
    assert metrics.quota_fresh is expected_fresh
    observed = isinstance(budget.get("in_flight"), dict)
    assert (metrics.inflight is None) is not observed


# --- wave gate and idle assembly -----------------------------------------------------------


@pytest.mark.parametrize("snapshot", _params("wave"), indirect=True)
def test_wave_gate_counts_only_what_the_owner_establishes(snapshot):
    _case, budget = snapshot
    config = coordinator.load_config()["health"]
    passed, assessment = coordinator._health_assessment(budget, config, now=NOW)
    group = next(g for g in assessment["groups"] if g["id"] == "curriculum-build")
    [lane] = group["lanes"]
    facts = owner(budget)
    available = group["available"] == 1
    if available:
        assert facts.health == credit_lane.HEALTHY
        assert facts.status in config["acceptable_statuses"] or facts.credit_relief
        assert not lane["stale"]
    # Unknown health is never counted, and the receipt says unknown (null with
    # its basis), distinct from an established unhealthy lane.
    if facts.health != credit_lane.HEALTHY:
        assert not available
    if facts.health == credit_lane.UNHEALTHY:
        assert lane["healthy"] is False and "health_basis" not in lane
    if facts.health == credit_lane.UNKNOWN:
        assert lane["healthy"] is None and lane["health_basis"] == facts.health_basis
    # Legitimate restriction: the wave's freshness requirement refuses any stale snapshot.
    if budget["diagnostics"].get("stale"):
        assert not passed and assessment["fresh"] is False


@pytest.mark.parametrize("snapshot", _params("idle"), indirect=True)
def test_idle_assembly_requires_established_capacity_and_load(snapshot):
    _case, budget = snapshot
    rows = list(_rows(budget).values())
    snap = idle_settle.assemble_snapshot(capacity_rows=rows, work_next_queue=[{"work_id": "issue:9740"}])
    lanes = {lane.lane: lane for lane in snap.lanes}
    for name in ("codex", "claude"):
        facts = owner(budget, name)
        lane = lanes[name]
        if lane.is_healthy_available():
            assert facts.capacity == credit_lane.CAPACITY_VERIFIED
            assert lane.in_flight == 0
        if facts.capacity == credit_lane.CAPACITY_VERIFIED and facts.status in {"cool", "warm"}:
            assert lane.is_healthy_available() is (budget.get("in_flight") is not None)
    decision = idle_settle.evaluate_settle(snap)
    assert set(decision.eligible_lanes) <= {
        name for name, lane in lanes.items() if lane.quota_ok is True and lane.in_flight == 0
    }


# --- per-case expectations: the owner facts themselves ---------------------------------------

EXPECTED_CODEX = {
    "healthy": (credit_lane.CAPACITY_VERIFIED, credit_lane.HEALTHY, credit_lane.FRESH),
    "covered_deficit": (credit_lane.CAPACITY_VERIFIED, credit_lane.HEALTHY, credit_lane.FRESH),
    "uncovered_deficit": (credit_lane.CAPACITY_AVOID, credit_lane.HEALTHY, credit_lane.FRESH),
    "stale_relief": (credit_lane.CAPACITY_UNKNOWN_STALE, credit_lane.HEALTHY, credit_lane.STALE),
    "unavailable_telemetry": (credit_lane.CAPACITY_UNKNOWN, credit_lane.UNKNOWN, credit_lane.FRESH),
    "catalog_disallowed": (credit_lane.CAPACITY_VERIFIED, credit_lane.HEALTHY, credit_lane.FRESH),
    "f1_conflicting_windows": (credit_lane.CAPACITY_AVOID, credit_lane.HEALTHY, credit_lane.FRESH),
    "f2_stale_near_cap_credit": (credit_lane.CAPACITY_AVOID, credit_lane.HEALTHY, credit_lane.STALE),
    "f3_hidden_pace": (credit_lane.CAPACITY_VERIFIED, credit_lane.HEALTHY, credit_lane.FRESH),
    "f3_hidden_pace_runtime_blocked": (credit_lane.CAPACITY_AVOID, credit_lane.HEALTHY, credit_lane.FRESH),
    "f3_conflicting_aliases": (credit_lane.CAPACITY_AVOID, credit_lane.HEALTHY, credit_lane.FRESH),
    "f4_scan_error_health": (credit_lane.CAPACITY_VERIFIED, credit_lane.UNKNOWN, credit_lane.FRESH),
    "f3_hidden_pace_non_pace_source": (credit_lane.CAPACITY_VERIFIED, credit_lane.HEALTHY, credit_lane.FRESH),
    "f6_contradictory_relief": (credit_lane.CAPACITY_AVOID, credit_lane.HEALTHY, credit_lane.STALE),
    "f7_near_cap_credit": (credit_lane.CAPACITY_VERIFIED, credit_lane.HEALTHY, credit_lane.FRESH),
}


@pytest.mark.parametrize("snapshot", _params("owner"), indirect=True)
def test_owner_facts_per_case(snapshot):
    case, budget = snapshot
    facts = owner(budget)
    assert (facts.capacity, facts.health, facts.observation_freshness) == EXPECTED_CODEX[case.name], (
        facts.capacity_reason
    )
    if case.name == "f1_conflicting_windows":
        assert (facts.plan_remaining_pct, facts.remaining_source) == (3.0, "codexbar.primary_remaining_pct")
    if case.name == "unavailable_telemetry":
        assert facts.plan_remaining_pct is None and budget["in_flight"] is None
    if case.name in {"covered_deficit", "f7_near_cap_credit"}:
        route = owner(budget, model=ROUTE_MODEL)
        off = owner(budget, model=OFF_ALLOWLIST_MODEL)
        assert route.capacity == credit_lane.CAPACITY_VERIFIED
        assert off.capacity == credit_lane.CAPACITY_AVOID
        assert facts.credit_models == ("gpt-6.1-sol", "gpt-6-luna")
    if case.name == "f3_hidden_pace":
        assert (facts.pace_visible, facts.raw_deficit) == (False, None)


def test_every_case_has_an_expectation():
    assert set(EXPECTED_CODEX) == set(CASE_IDS)


@pytest.mark.parametrize("snapshot", [pytest.param(CASES[0], id="healthy")], indirect=True)
def test_snapshot_served_later_than_the_credit_age_limit_loses_relief(snapshot, monkeypatch):
    """Control: the same healthy snapshot read past ``credit_max_age_s`` keeps plan capacity (no credit involved)."""
    _case, budget = snapshot
    later = NOW + timedelta(seconds=credit_lane.load_policy().credit_max_age_s + 1)
    facts = credit_lane.routing_facts(
        "codex", budget["agents"]["codex"], model=None, snapshot_metadata=budget["diagnostics"], now=later
    )
    assert facts.capacity == credit_lane.CAPACITY_VERIFIED
