"""#9740: equivalent routing inputs give equivalent decisions in every capacity and admission consumer.

One routing-budget snapshot per case is built through the real producer
(:func:`state_router.compute_routing_budget`) from external-seam fixtures only:
provider usage records (CodexBar payloads), lane-health task records (or a
tasks directory the scan cannot read), runtime outcome summaries and the
rate-limit records reader. The same object goes to every consumer:

* budget producer and recommendation (``agents.<lane>.routing_facts``, ``recommendation``);
* picker rows, order and CLI (:mod:`scripts.fleet.capacity_pick`);
* budget guard and final admission (``delegate._resolve_agent_with_budget_guard``,
  :func:`credit_lane.dispatch_refusal`);
* reviewer resolver and scheduler;
* curriculum wave gate (``curriculum_coordinator._health_assessment``);
* idle assembly (``idle_settle.assemble_snapshot`` over the picker rows).

Each decision is compared with the owner's facts (:func:`credit_lane.routing_facts`)
for the same record before its final action. Legitimate restrictions keep their
own asserted reasons: the wave's acceptable statuses, positive-health and
freshness requirement; retirement in the picker; the resolver's near-cap
exclusion of a stale deficit; delegate's stale-advisory no-hard-substitution.
No case reaches a provider: every provider seam is captured and must record
zero calls.

Recon inventory disposition (``recon-9740``; R = repaired here, A = agrees,
D = different question):

=====================================================  ===  =========================================
consumer                                               disp evidence in this module / owned tests
=====================================================  ===  =========================================
state_router._capacity_used_pct                        D    raw used-% metric; status via the owner
state_router._status_from_weekly_used                  A    owner ``pace_deficit_state``
state_router._attach_credit_states                     A    owner ``lane_credit_state``
state_router._recommend_agent                          R    F2 stale label, F4 health, #9040 owner hot
state_router.compute_routing_budget (health fill-in)   R    A1 typed scan; A6 freshness labels
state_router.compute_routing_budget (reserve override) R    owner-verified capacity only (round 6)
state_router.compute_routing_budget (ACP reserve)      R    owner-verified capacity only (round 7)
state_router._api_lane_status_from_account             A    F8 duplicate, agrees (prepaid)
lane_health.compute_lane_health                        R    A1 ``scan_lane_health``
subscription_usage.pace_is_deficit                     R    F3 one alias reader ``pace_expected_pct``
project_state_store.any_lane_under_weekly_pace         D    notebook overlay, not admission
reset_reserve.codex_is_threatened                      D    operator reserve precondition
reset_reserve.codex_reset_reserve_eligible             R    required ``owner_capacity`` (round 7)
prepaid_status.api_lane_status_from_account            A    F8 duplicate, agrees
capacity_pick.remaining_pct                            R    F1 owner ``plan_remaining_pct``
capacity_pick.is_avoid_lane / build_lane_rows          R    F2/F3/F4/F7 owner ``routing_facts``
capacity_pick.build_lane_rows (reserve)                R    ranks only; never lifts AVOID (round 7)
capacity_pick.build_pick_order / cooler_lanes          R    A5 stale rank, strict
delegate._budget_needs_hard_capacity_action            R    F1/F6 owner near cap, F3/#9040 owner hot
delegate._resolve_agent_with_budget_guard              R    agreement asserted; F4 unknown health text
delegate guard + _language_lane_substitute (reserve)   R    owner-verified capacity only (round 7)
delegate._credit_period_refusal / dispatch_refusal     A    A4 CREDIT_PERIOD_MODEL_REFUSED
delegate._budget_cooler_lanes                          D    refusal hint text only (A4)
delegate._check_capacity_hint                          D    in-flight hint only
idle_settle._lane_quota_ok / LaneState                 R    F5 unknown quota and load
fleet.usage._credit_state_text                         D    display of the published state
curriculum_coordinator._health_assessment              R    F4 owner health, F6 full-record relief
reviewer_resolver.evaluate_candidate                   R    F6 full-record relief, #9040 owner hot
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
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from scripts.api import state_router
from scripts.fleet import credit_lane, reset_reserve
from scripts.fleet.reset_reserve import RESERVE_RELATIVE_PATH, SCHEMA_VERSION
from tests.api.test_routing_budget import _configure_base

NOW = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
FETCHED = "2026-10-05T11:59:30Z"
RESETS = "2026-10-09T12:00:00Z"
ROUTE_MODEL = "gpt-6.1-sol"


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


# Cursor's own Auto allowance is 80% used (status hot, status_source cursor_auto) while
# its separate weekly (Grok) window is visible and on pace: the #9040 rule must not clear it.
CURSOR_AUTO_HOT_ON_PACE = {
    "lane": "cursor",
    "source": "cursor_native",
    "status": "hot",
    "login_state": "authenticated",
    "probe_state": "healthy",
    "weekly_used_pct": 20.0,
    "weekly_remaining_pct": 80.0,
    "weekly_expected_pct": 30.0,
    "weekly_pace_delta_pct": -10.0,
    "will_last_to_reset": True,
    "weekly_resets_at": RESETS,
    "provider_windows": {"auto": {"window": "monthly", "used_pct": 80.0, "remaining_pct": 20.0}},
    "freshness": "fresh",
    "age_s": 30.0,
    "fetched_at": FETCHED,
}

NEAR_CAP_CREDIT = {
    "codex": _codex(weekly_used_pct=95.0, weekly_remaining_pct=5.0, credit_balance=62500.0),
    "claude": CLAUDE,
}
# The credit lane is the only candidate: Claude is near cap too, so the recommendation
# picks Codex exactly when credit relief holds.
CREDIT_ONLY_SEAT = {**NEAR_CAP_CREDIT, "claude": {**CLAUDE, "weekly_used_pct": 99.0, "weekly_remaining_pct": 1.0}}
# #9040 controls: Claude near cap, so the recommendation picks Codex exactly when the owner clears its hot label.
CLAUDE_NEAR_CAP = {**CLAUDE, "weekly_used_pct": 99.0, "weekly_remaining_pct": 1.0}
# Free full resets (no credit balance). The ``_deficit`` payload runs out about 2026-10-07T12:00Z:
# never-expiring resets outlast that and cover the deficit; one expiring a day earlier does not.
RESETS_OUTLAST_RUNOUT = {"available_count": 2, "expires_at": [None, None], "fetched_at": FETCHED}
RESET_BEFORE_RUNOUT = {"available_count": 1, "expires_at": ["2026-10-06T12:00:00Z"], "fetched_at": FETCHED}
# An operator-confirmed reset reserve on file (``reset_reserve.RESERVE_RELATIVE_PATH``).
OPERATOR_RESERVE = {
    "schema_version": SCHEMA_VERSION,
    "provider": "codex",
    "remaining_resets": 2,
    "confirmed_at": "2026-10-05T11:00:00Z",
    "expires_at": "2026-10-12T00:00:00Z",
}


@dataclass(frozen=True)
class Case:
    """One producer snapshot from external seams; ``tasks`` is ``idle`` (scan ran, nothing recent) or ``missing``.

    ``removed`` names a freshness input dropped from the published snapshot after ``mutate``
    (see :data:`REMOVED_INPUTS`). ``reserve`` puts :data:`OPERATOR_RESERVE` on file.
    """

    name: str
    payloads: dict[str, dict[str, Any] | None]
    tasks: str = "idle"
    runtime_blocked: frozenset[str] = frozenset()
    mutate: str | None = None
    removed: str | None = None
    reserve: bool = False


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
    ),
    Case(
        "f6_contradictory_relief",
        {"codex": _codex(weekly_used_pct=95.0, weekly_remaining_pct=5.0, credit_balance=62500.0), "claude": CLAUDE},
        mutate="probe_relabelled_stale_after_publication",
    ),
    Case("f7_near_cap_credit", NEAR_CAP_CREDIT),
    # Held-out round-3 contradiction controls (review of record on 34e9530820).
    Case("f7_credit_only_seat", CREDIT_ONLY_SEAT),
    Case("f6_relief_raw_balance_zero", CREDIT_ONLY_SEAT, mutate="raw_balance_zero_after_publication"),
    Case("f6_relief_runtime_blocked", CREDIT_ONLY_SEAT, mutate="runtime_blocked_after_publication"),
    Case(
        "f9040_cursor_auto_hot_on_pace",
        {"codex": _codex(), "claude": CLAUDE, "cursor": CURSOR_AUTO_HOT_ON_PACE},
    ),
    Case("missing_snapshot_staleness", {"codex": _codex(), "claude": CLAUDE}, mutate="snapshot_staleness_removed"),
    # Held-out round-4 controls (review of record on 51df582bbb): a fresh weekly-pace hot label.
    Case(
        "f9040_weekly_hot_on_pace",
        {"codex": _codex(), "claude": CLAUDE_NEAR_CAP},
        mutate="weekly_pace_hot_label",
    ),
    Case(
        "f9040_weekly_hot_deficit",
        {"codex": _deficit(credit_balance=0.0), "claude": CLAUDE_NEAR_CAP},
        mutate="weekly_pace_hot_label",
    ),
    # Held-out round-5 controls (review of record on 0c301aa127): the on-pace weekly-pace hot label
    # with one freshness input missing. None positively establishes freshness, so none clears it.
    *(
        Case(
            f"f9040_weekly_hot_{removed}_missing",
            {"codex": _codex(), "claude": CLAUDE_NEAR_CAP},
            mutate="weekly_pace_hot_label",
            removed=removed,
        )
        for removed in ("probe_age", "probe_freshness", "snapshot_staleness")
    ),
    # Held-out round-6 controls (CI regression on 3517f733f0): a pace deficit covered by free full
    # resets with an operator reserve on file, with established and with unknown lane health, and the
    # same reserve over resets that expire before run-out (the owner leaves that deficit uncovered).
    Case(
        "reset_covered_deficit",
        {"codex": _deficit(credit_balance=0.0, reset_credits=RESETS_OUTLAST_RUNOUT), "claude": CLAUDE_NEAR_CAP},
        reserve=True,
    ),
    Case(
        "reset_covered_deficit_health_unknown",
        {"codex": _deficit(credit_balance=0.0, reset_credits=RESETS_OUTLAST_RUNOUT), "claude": CLAUDE_NEAR_CAP},
        tasks="missing",
        reserve=True,
    ),
    Case(
        "reset_before_runout",
        {"codex": _deficit(credit_balance=0.0, reset_credits=RESET_BEFORE_RUNOUT), "claude": CLAUDE_NEAR_CAP},
        reserve=True,
    ),
)

# Credit relief the producer published, contradicted after publication by the record it rests on.
# Freshness inputs a control drops: the probe's age, the probe's own freshness label (read as
# unknown), the snapshot's ``diagnostics.stale``. Probe fields live on the record and its codexbar.
REMOVED_INPUTS = {"probe_age": "age_s", "probe_freshness": "freshness", "snapshot_staleness": "stale"}


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


def produce(
    case: Case, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, transport: str = "dispatch"
) -> dict[str, Any]:
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
    if case.reserve:
        reserve_path = tmp_path / RESERVE_RELATIVE_PATH
        reserve_path.parent.mkdir(parents=True, exist_ok=True)
        reserve_path.write_text(json.dumps(OPERATOR_RESERVE), encoding="utf-8")
    budget = state_router.compute_routing_budget(
        NOW,
        transport=transport,
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
    if case.mutate == "raw_balance_zero_after_publication":
        # The fresh record's raw balance reads zero; the published leaf still says present.
        assert budget["agents"]["codex"]["credit"]["state"] == credit_lane.CREDIT_BALANCE_PRESENT
        budget["agents"]["codex"]["credit_balance"] = 0.0
        budget["agents"]["codex"]["codexbar"]["credit_balance"] = 0.0
    if case.mutate == "runtime_blocked_after_publication":
        # The record's own runtime evidence now shows a headroom block (rate limits).
        assert budget["agents"]["codex"]["credit"]["state"] == credit_lane.CREDIT_BALANCE_PRESENT
        budget["agents"]["codex"]["runtime"] = _runtime("codex", True)
    if case.mutate == "snapshot_staleness_removed":
        # A healthy producer snapshot without its ``diagnostics.stale`` metadata.
        assert budget["diagnostics"].pop("stale") is False
    if case.mutate == "weekly_pace_hot_label":
        # The #9040 snapshot shape: the producer's weekly-pace label reads hot (the early-window
        # false positive) whatever the record's own pace reading. A deficit payload is already hot.
        codex = budget["agents"]["codex"]
        assert codex["status_source"] == "weekly_pace"
        codex["status"] = "hot"
    if case.removed == "snapshot_staleness":
        assert budget["diagnostics"].pop("stale") is False
    elif case.removed is not None:
        key = REMOVED_INPUTS[case.removed]
        codex = budget["agents"]["codex"]
        assert codex.pop(key) == codex["codexbar"].pop(key)
    return json.loads(json.dumps(budget))  # the JSON boundary every consumer reads across


class _FixtureClock(datetime):
    """The reserve module's wall clock pinned to :data:`NOW` (consumers that pass no ``now``)."""

    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return NOW if tz is None else NOW.astimezone(tz)


# --- shared facts in the producer ---------------------------------------------------


# --- picker rows, order and CLI -------------------------------------------------------


# --- budget guard and final admission ------------------------------------------------


# --- reviewer resolver and scheduler ------------------------------------------------


# --- wave gate and idle assembly -----------------------------------------------------------


# --- per-case expectations: the owner facts themselves ---------------------------------------


# --- held-out round-3 controls: owner, resolver, wave, recommendation and delegate agree ---------


RESET_CONTROLS = [pytest.param(case, id=case.name) for case in CASES if case.reserve]


@pytest.mark.parametrize("case", RESET_CONTROLS)
def test_acp_reset_reserve_defers_to_the_owner(case, monkeypatch, tmp_path, provider_calls):
    """The ACP recommendation's reserve override needs the owner's verified Codex capacity too (#9740)."""
    monkeypatch.setattr(reset_reserve, "datetime", _FixtureClock)
    healthy = {"healthy": True, "eligible": True, "failure_code": None, "scope": "acp_cli_compatibility"}
    monkeypatch.setattr(state_router, "probe_acp_health", lambda _cwd: {"codex": healthy, "claude": healthy})
    budget = produce(case, monkeypatch, tmp_path, transport="acp")
    assert budget["reset_reserve"]["available"] is True
    covered = case.name != "reset_before_runout"
    assert (budget["recommendation"]["primary_agent_for_code"] == "codex") is covered
    assert list(provider_calls) == [], "a routing consumer reached a provider"
