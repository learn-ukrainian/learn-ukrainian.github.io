"""#9518: credit-backed lanes, the credit-period model allowlist and reset advice.

Covers the state machine (``scripts.fleet.credit_lane``), the router rows and
output (``scripts.fleet.capacity_pick``), dispatch admission
(``delegate._credit_period_refusal`` and the ``--check-budget`` guard), and a
lock that every lane without a credit policy keeps its origin/main row.
"""

from __future__ import annotations

import copy
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.fleet import capacity_pick, credit_lane
from scripts.fleet.reset_reserve import unavailable_reserve

NOW = datetime(2026, 10, 2, 17, 0, tzinfo=UTC)
POLICY = credit_lane.load_policy()


def _codex(**overrides) -> dict:
    """A fresh near-cap Codex record with 62500 credits and two free resets (2026-10-02 shape)."""
    info = {
        "status": "near_cap",
        "remaining_pct": 1.0,
        "burn_pct_7d": 99.0,
        "freshness": "fresh",
        "age_s": 60.0,
        "eligible": True,
        "health": {"healthy": True},
        "credit_balance": 62500.0,
        "reset_credits": {
            "available_count": 2,
            "expires_at": ["2026-10-22T21:07:26Z", "2026-10-29T19:15:04Z"],
            "fetched_at": (NOW - timedelta(minutes=1)).isoformat(),
        },
        "runtime": {"headroom_blocked": False, "rate_limited": 0},
        "codexbar": {
            "weekly_used_pct": 99.0,
            "weekly_remaining_pct": 1.0,
            "weekly_resets_at": (NOW + timedelta(hours=24)).isoformat(),
            "will_last_to_reset": False,
            "pace_summary": "13% in deficit",
            "freshness": "fresh",
            "age_s": 60.0,
            "stale": False,
        },
    }
    info.update(overrides)
    return info


def _budget(codex: dict | None = None, **agents) -> dict:
    return {
        "agents": {"codex": codex if codex is not None else _codex(), **agents},
        "api_accounts": {},
        "diagnostics": {"stale": False},
        "recommendation": {"primary_agent_for_code": "codex", "rationale": "", "warnings": []},
    }


def _row(budget: dict, lane: str = "codex") -> dict:
    rows = capacity_pick.build_lane_rows(budget, reset_reserve=unavailable_reserve(), now=NOW)
    return next(row for row in rows if row["lane"] == lane)


# --- policy ------------------------------------------------------------------


def test_policy_reads_codex_allowlist_from_config():
    assert POLICY.path.name == "credit_lanes.yaml"
    assert POLICY.lane_models("codex") == ("gpt-6.1-sol", "gpt-6-luna")
    assert POLICY.lane_models("claude") is None
    assert (POLICY.near_cap_remaining_pct, POLICY.credit_max_age_s, POLICY.reset_hold_hours) == (10.0, 900.0, 48.0)


def test_policy_allowlist_names_active_catalog_models():
    from scripts.review.model_catalog import canonical_model_id, load_model_catalog

    catalog = load_model_catalog()
    for models in POLICY.allowed_models.values():
        for model in models:
            assert canonical_model_id(model) == model
            assert catalog["models"][model]["lifecycle"] == "active"


@pytest.mark.parametrize(
    "text",
    [
        "schema_version: other\nlanes: {}\n",
        "schema_version: credit-lanes.v1\nnear_cap_remaining_pct: 10\ncredit_max_age_s: 900\n"
        "reset_hold_hours: 48\nlanes: {codex: {allowed_models: []}}\n",
        "schema_version: credit-lanes.v1\nnear_cap_remaining_pct: -1\ncredit_max_age_s: 900\n"
        "reset_hold_hours: 48\nlanes: {codex: {allowed_models: [gpt-6.1-sol]}}\n",
    ],
    ids=["schema", "empty-allowlist", "negative-threshold"],
)
def test_malformed_policy_raises(tmp_path, text):
    path = tmp_path / "credit_lanes.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        credit_lane.load_policy(path)


# --- state machine -----------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"remaining_pct": 60.0, "codexbar": {"weekly_remaining_pct": 60.0}}, credit_lane.PLAN_HEALTHY),
        ({}, credit_lane.CREDIT_BACKED),
        (
            {"remaining_pct": 10.0, "codexbar": {"weekly_remaining_pct": 10.0, "freshness": "fresh"}},
            credit_lane.CREDIT_BACKED,
        ),
        ({"credit_balance": 0.0}, credit_lane.CREDITS_EXHAUSTED),
        ({"credit_balance": -5.0}, credit_lane.CREDITS_EXHAUSTED),
        ({"credit_balance": None}, credit_lane.CREDITS_UNVERIFIED),
        ({"credit_balance": "62500"}, credit_lane.CREDITS_UNVERIFIED),
        ({"credit_balance": True}, credit_lane.CREDITS_UNVERIFIED),
        ({"credit_balance": float("nan")}, credit_lane.CREDITS_UNVERIFIED),
        ({"freshness": "stale_last_good"}, credit_lane.CREDITS_UNVERIFIED),
        ({"age_s": 900.0}, credit_lane.CREDITS_UNVERIFIED),
        ({"age_s": None, "codexbar": {"weekly_remaining_pct": 1.0}}, credit_lane.CREDITS_UNVERIFIED),
        ({"runtime": {"headroom_blocked": True}}, credit_lane.CREDITS_UNVERIFIED),
        ({"remaining_pct": None, "codexbar": {}}, credit_lane.PLAN_UNKNOWN),
    ],
    ids=[
        "plan-healthy",
        "near-cap-with-credits",
        "at-threshold-with-credits",
        "credits-zero",
        "credits-negative",
        "credits-missing",
        "credits-string",
        "credits-bool",
        "credits-nan",
        "credits-stale-freshness",
        "credits-too-old",
        "credits-age-missing",
        "runtime-rate-limited",
        "plan-unknown",
    ],
)
def test_state_machine(overrides, expected):
    state = credit_lane.lane_credit_state("codex", _codex(**overrides), POLICY)
    assert state["state"] == expected, state
    assert state["allowed_models"] == ["gpt-6.1-sol", "gpt-6-luna"]
    if expected == credit_lane.CREDIT_BACKED:
        assert state["credit_balance"] == 62500.0
        assert state["coverage"] == {"dispatches": None, "basis": credit_lane.COVERAGE_BASIS}
    else:
        assert "coverage" not in state


def test_tightest_plan_window_governs():
    info = _codex(remaining_pct=60.0, codexbar={**_codex()["codexbar"], "weekly_remaining_pct": 60.0})
    info["codexbar"]["primary_remaining_pct"] = 3.0
    assert credit_lane.lane_credit_state("codex", info, POLICY)["state"] == credit_lane.CREDIT_BACKED


def test_stale_snapshot_fails_closed():
    state = credit_lane.lane_credit_state("codex", _codex(), POLICY, snapshot_stale=True)
    assert state["state"] == credit_lane.CREDITS_UNVERIFIED


def test_balance_falls_back_to_native_record():
    info = _codex(credit_balance=None)
    info["codexbar"]["credit_balance"] = 100.0
    assert credit_lane.lane_credit_state("codex", info, POLICY)["state"] == credit_lane.CREDIT_BACKED


def test_unconfigured_lane_ignores_credit_data():
    assert credit_lane.lane_credit_state("claude", _codex(), POLICY) == {"state": credit_lane.NOT_CONFIGURED}
    assert credit_lane.lane_credit_report("cursor", _codex(), POLICY) == {"state": credit_lane.NOT_CONFIGURED}


# --- reset advice ------------------------------------------------------------


def _advice(info: dict, state: str = credit_lane.CREDIT_BACKED) -> dict:
    return credit_lane.reset_advice("codex", info, POLICY, state, now=NOW)


def test_reset_held_when_natural_reset_is_near():
    advice = _advice(_codex())
    assert advice["advice"] == credit_lane.HOLD_RESET
    assert advice["hours_to_natural_reset"] == 24.0
    assert advice["free_resets_available"] == 2
    assert advice["free_reset_expires_at"] == ["2026-10-22T21:07:26Z", "2026-10-29T19:15:04Z"]
    assert advice["window_anchor_evidence"].startswith("unverified")
    assert "within the 48h hold window" in advice["reason"]


def test_reset_useful_when_natural_reset_is_far():
    info = _codex()
    info["codexbar"]["weekly_resets_at"] = (NOW + timedelta(days=5)).isoformat()
    advice = _advice(info)
    assert advice["advice"] == credit_lane.USE_RESET_NOW
    assert advice["hours_to_natural_reset"] == 120.0
    assert "operator decision" in advice["reason"]


def test_reset_hold_boundary_is_inclusive():
    info = _codex()
    info["codexbar"]["weekly_resets_at"] = (NOW + timedelta(hours=48)).isoformat()
    assert _advice(info)["advice"] == credit_lane.HOLD_RESET


def test_reset_held_when_natural_reset_unknown():
    info = _codex()
    info["codexbar"]["weekly_resets_at"] = None
    advice = _advice(info)
    assert advice["advice"] == credit_lane.HOLD_RESET
    assert advice["natural_reset_at"] is None


def test_natural_reset_reads_epoch_seconds():
    info = _codex()
    info["codexbar"]["weekly_resets_at"] = int((NOW + timedelta(hours=10)).timestamp())
    assert _advice(info)["hours_to_natural_reset"] == 10.0


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda info: info.update(reset_credits=None), "free-reset inventory missing or stale"),
        (
            lambda info: info["reset_credits"].update(fetched_at=(NOW - timedelta(hours=2)).isoformat()),
            "free-reset inventory missing or stale",
        ),
        (lambda info: info.update(freshness="stale_last_good"), "free-reset inventory missing or stale"),
        (
            lambda info: info["reset_credits"].update(available_count=0, expires_at=[]),
            "no free full reset available",
        ),
        (
            lambda info: info["reset_credits"].update(expires_at=["2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z"]),
            "no free full reset available",
        ),
    ],
    ids=["missing", "inventory-old", "probe-stale", "zero", "all-expired"],
)
def test_reset_not_applicable_without_verified_inventory(mutate, reason):
    info = _codex()
    mutate(info)
    advice = _advice(info)
    assert advice["advice"] == credit_lane.NOT_APPLICABLE
    assert advice["reason"] == reason


def test_reset_not_applicable_while_plan_is_healthy():
    advice = _advice(_codex(), state=credit_lane.PLAN_HEALTHY)
    assert advice["advice"] == credit_lane.NOT_APPLICABLE
    assert "plan_healthy" in advice["reason"]


def test_reset_advice_is_held_for_exhausted_credits_near_reset():
    advice = _advice(_codex(credit_balance=0.0), state=credit_lane.CREDITS_EXHAUSTED)
    assert advice["advice"] == credit_lane.HOLD_RESET


# --- router rows and output --------------------------------------------------


def test_credit_backed_codex_is_usable_and_labelled():
    row = _row(_budget())
    assert row["avoid"] is False
    assert row["status"] == credit_lane.CREDIT_BACKED
    assert row["remaining_pct"] == 1.0
    assert "credit-backed (balance 62500; models gpt-6.1-sol, gpt-6-luna only)" in row["notes"]
    assert row["credit"]["state"] == credit_lane.CREDIT_BACKED
    assert row["credit"]["reset_advice"]["advice"] == credit_lane.HOLD_RESET


@pytest.mark.parametrize(
    ("overrides", "state"),
    [
        ({"credit_balance": 0.0}, credit_lane.CREDITS_EXHAUSTED),
        ({"credit_balance": None}, credit_lane.CREDITS_UNVERIFIED),
        ({"age_s": 5000.0}, credit_lane.CREDITS_UNVERIFIED),
    ],
    ids=["exhausted", "missing", "stale"],
)
def test_codex_without_usable_credits_keeps_near_cap_avoid(overrides, state):
    row = _row(_budget(_codex(**overrides)))
    assert row["avoid"] is True
    assert row["status"] == "near_cap"
    assert "AVOID" in row["notes"] and "near_cap" in row["notes"]
    assert f"{state}:" in row["notes"]
    assert row["credit"]["state"] == state


@pytest.mark.parametrize(
    "overrides",
    [
        {"health": {"healthy": False, "last_error": "spawn failed"}},
        {"eligible": False},
        {"probe_state": "NEED_LOGIN"},
    ],
    ids=["unhealthy", "ineligible", "need-login"],
)
def test_credits_never_relax_hard_avoid(overrides):
    row = _row(_budget(_codex(**overrides)))
    assert row["avoid"] is True
    assert row["status"] == "near_cap"


def test_acp_transport_ineligible_codex_stays_avoid():
    budget = _budget()
    budget["transport"] = "acp"
    del budget["agents"]["codex"]["eligible"]
    assert _row(budget)["avoid"] is True


def test_credit_backed_ranks_after_plan_backed_seats_and_counts_as_usable():
    budget = _budget(cursor={"status": "cool", "remaining_pct": 90.0}, kimi={"status": "hot", "remaining_pct": 40.0})
    report = capacity_pick.build_report(budget, reset_reserve=unavailable_reserve(), now=NOW)
    order = [entry["lane"] for entry in report["pick_order"] if entry["pick"] != "AVOID"]
    assert order.index("cursor") < order.index("codex")
    assert "codex" in report["cooler_lanes"]
    assert report["recommendation"]["primary_agent_for_code"] == "codex"
    assert any(
        "runs on prepaid credits: dispatch only gpt-6.1-sol, gpt-6-luna" in w
        for w in report["recommendation"]["warnings"]
    )


def test_human_output_states_credit_and_reset_advice():
    report = capacity_pick.build_report(_budget(), reset_reserve=unavailable_reserve(), now=NOW)
    human = capacity_pick.format_human(report)
    assert (
        "credit lane codex: credit_backed (plan remaining 1% at or below 10%; fresh credit balance 62500) | "
        "coverage: unknown: runtime usage records carry no per-task credit consumption | "
        "models: gpt-6.1-sol, gpt-6-luna only"
    ) in human
    assert "reset advice codex: hold_reset — natural reset in 24h is within the 48h hold window" in human
    assert "free full resets 2 (expire 2026-10-22T21:07:26Z, 2026-10-29T19:15:04Z)" in human
    assert "window anchor unverified" in human and "never consumed automatically" in human


def test_human_output_for_unverified_credits():
    report = capacity_pick.build_report(
        _budget(_codex(credit_balance=None)), reset_reserve=unavailable_reserve(), now=NOW
    )
    human = capacity_pick.format_human(report)
    assert "credit lane codex: credits_unverified (credit balance missing or non-numeric)" in human
    assert "only while credit_backed" in human


def test_main_json_carries_credit_fields(monkeypatch, capsys):
    from scripts.fleet import usage

    budget = _budget()
    budget["agents"]["codex"]["reset_credits"]["fetched_at"] = datetime.now(UTC).isoformat()
    budget["agents"]["codex"]["codexbar"]["weekly_resets_at"] = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    monkeypatch.setattr(usage, "read_budget", lambda **_kwargs: budget)
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: {})
    monkeypatch.setattr(capacity_pick, "load_reset_reserve", lambda *_args, **_kwargs: unavailable_reserve())
    monkeypatch.setattr(capacity_pick, "admission_status", lambda: None)
    assert capacity_pick.main(["--json", "--strict"]) == 0
    payload = json.loads(capsys.readouterr().out)
    rows = {row["lane"]: row for row in payload["rows"]}
    credit = rows["codex"]["credit"]
    assert credit["state"] == "credit_backed" and credit["credit_balance"] == 62500.0
    assert set(credit["reset_advice"]) >= {
        "advice",
        "reason",
        "natural_reset_at",
        "hours_to_natural_reset",
        "free_resets_available",
        "free_reset_expires_at",
        "window_anchor_evidence",
    }
    assert credit["reset_advice"]["advice"] == "hold_reset"
    assert rows["claude"]["credit"] == {"state": "not_configured"}
    assert payload["cooler_lanes"] == ["codex"]


def test_router_never_consumes_credits_or_resets(monkeypatch):
    import urllib.request

    def no_network(*_args, **_kwargs):
        raise AssertionError("the router must not call the provider")

    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    budget = _budget()
    frozen = copy.deepcopy(budget)
    capacity_pick.build_report(budget, reset_reserve=unavailable_reserve(), now=NOW)
    assert budget == frozen


# --- unchanged lanes (denominator lock) --------------------------------------

_SCENARIOS = ("plan_healthy", "near_cap_with_credits", "near_cap_without_credits", "credits_stale")


def _scenario_info(scenario: str) -> dict:
    base = {"freshness": "fresh", "age_s": 10, "eligible": True, "health": {"healthy": True}}
    if scenario == "plan_healthy":
        return {**base, "status": "cool", "remaining_pct": 80.0, "burn_pct_7d": 20.0, "credit_balance": 500.0}
    near = {**base, "status": "near_cap", "remaining_pct": 2.0, "burn_pct_7d": 98.0}
    if scenario == "near_cap_with_credits":
        return {**near, "credit_balance": 62500.0}
    if scenario == "near_cap_without_credits":
        return {**near, "credit_balance": 0.0}
    return {**near, "credit_balance": 62500.0, "freshness": "stale_last_good", "age_s": 5000}


def _origin_main_row(lane: str, scenario: str) -> dict:
    """The row origin/main's ``build_lane_rows`` produced for this lane and scenario (captured 2026-10-02)."""
    healthy = scenario == "plan_healthy"
    retired = {"gemini": "agy", "glm": "cursor"}.get(lane)
    if lane == "deepseek":
        status, avoid, notes = "cool", False, "idle"
    elif healthy:
        status, avoid = "cool", retired is not None
        notes = f"AVOID; retired→{retired}" if retired else "idle"
    else:
        status, avoid = "near_cap", True
        notes = f"AVOID; retired→{retired}; near_cap" if retired else "AVOID; near_cap"
    return {
        "lane": lane,
        "status": status,
        "remaining_pct": 80.0 if healthy else 2.0,
        "will_last": None,
        "pace": "—",
        "in_flight": 0,
        "avoid": avoid,
        "reset_reserve_eligible": False,
        "notes": notes,
    }


@pytest.mark.parametrize("scenario", _SCENARIOS)
def test_lanes_without_credit_policy_keep_origin_main_rows(scenario):
    budget = {
        "agents": {lane: _scenario_info(scenario) for lane in capacity_pick.CODE_LANES},
        "api_accounts": {
            "deepseek": {
                "probe_state": "ok",
                "freshness": "fresh",
                "age_s": 0,
                "currency": "USD",
                "total_balance": 30.0,
                "is_available": True,
            }
        },
        "diagnostics": {"stale": False},
    }
    rows = {row["lane"]: row for row in capacity_pick.build_lane_rows(budget, reset_reserve=unavailable_reserve())}
    assert set(rows) == set(capacity_pick.CODE_LANES)
    for lane in capacity_pick.CODE_LANES:
        if lane == "codex":
            continue
        row = dict(rows[lane])
        assert row.pop("credit") == {"state": "not_configured"}
        assert row == _origin_main_row(lane, scenario), lane
    codex = rows["codex"]
    expected = {
        "plan_healthy": (credit_lane.PLAN_HEALTHY, "cool", False),
        "near_cap_with_credits": (credit_lane.CREDIT_BACKED, credit_lane.CREDIT_BACKED, False),
        "near_cap_without_credits": (credit_lane.CREDITS_EXHAUSTED, "near_cap", True),
        "credits_stale": (credit_lane.CREDITS_UNVERIFIED, "near_cap", True),
    }[scenario]
    assert (codex["credit"]["state"], codex["status"], codex["avoid"]) == expected


# --- dispatch admission ------------------------------------------------------


def _credit_backed_snapshot() -> dict:
    return _budget(_codex(reset_credits=None))


@pytest.fixture
def snapshot(monkeypatch):
    """Serve ``credit_lane.read_routing_budget`` from a mutable box; count reads."""
    box = {"budget": _credit_backed_snapshot(), "reads": 0}

    def read(**_kwargs):
        box["reads"] += 1
        return box["budget"]

    monkeypatch.setattr(credit_lane, "read_routing_budget", read)
    return box


@pytest.mark.parametrize("model", ["gpt-6-astra", "gpt-5-codex", "claude-opus-5-5"])
def test_admission_refuses_off_allowlist_model_on_credit_backed_lane(snapshot, model):
    refusal = delegate._credit_period_refusal("codex", model)
    assert refusal is not None
    assert refusal.startswith("CREDIT_PERIOD_MODEL_REFUSED: lane codex is credit_backed")
    assert f"model {model} is outside the credit-period allowlist [gpt-6.1-sol, gpt-6-luna]" in refusal
    assert "credit_lanes.yaml" in refusal


@pytest.mark.parametrize("model", ["gpt-6.1-sol", "gpt-6-luna", "codex:gpt-6-luna", "GPT-6.1-Sol", None])
def test_admission_accepts_allowlisted_and_default_models_without_reading_state(snapshot, model):
    assert delegate._credit_period_refusal("codex", model) is None
    assert snapshot["reads"] == 0


def test_admission_judges_a_missing_model_by_the_lane_default(snapshot, monkeypatch):
    monkeypatch.setattr(delegate, "_lane_default_model", lambda _agent: "gpt-6-astra")
    refusal = delegate._credit_period_refusal("codex", None)
    assert refusal is not None and "model gpt-6-astra" in refusal


@pytest.mark.parametrize(
    "mutate",
    [
        lambda box: box.update(budget=_budget(_codex(remaining_pct=60.0, codexbar={"weekly_remaining_pct": 60.0}))),
        lambda box: box.update(budget=_budget(_codex(credit_balance=None))),
        lambda box: box.update(budget=_budget(_codex(age_s=5000.0))),
        lambda box: box["budget"]["diagnostics"].update(stale=True),
        lambda box: box.update(budget=None),
    ],
    ids=["plan-healthy", "credits-missing", "credits-stale", "snapshot-stale", "monitor-unreachable"],
)
def test_admission_keeps_todays_behaviour_unless_credit_backed(snapshot, mutate):
    mutate(snapshot)
    assert delegate._credit_period_refusal("codex", "gpt-6-astra") is None


def test_admission_ignores_unconfigured_lanes(snapshot):
    assert delegate._credit_period_refusal("claude", "claude-opus-5-5") is None
    assert delegate._credit_period_refusal("cursor", "gpt-6-astra") is None
    assert snapshot["reads"] == 0


def test_admission_refuses_when_policy_is_unreadable(snapshot, monkeypatch):
    def broken(*_args, **_kwargs):
        raise ValueError("bad policy")

    monkeypatch.setattr(credit_lane, "load_policy", broken)
    refusal = delegate._credit_period_refusal("codex", "gpt-6.1-sol")
    assert refusal == "CREDIT_PERIOD_MODEL_REFUSED: credit-lane policy unreadable: bad policy"


def _guard_budget(codex: dict) -> dict:
    return {
        "agents": {"codex": codex, "cursor": {"status": "cool", "remaining_pct": 90.0}},
        "diagnostics": {"records_loaded": 5, "stale": False, "codexbar_data_available": True},
        "recommendation": {},
    }


def test_budget_guard_keeps_credit_backed_codex(monkeypatch, capsys):
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: _guard_budget(_codex(age_s=10.0)))
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_args, **_kwargs: unavailable_reserve())
    chosen = delegate._resolve_agent_with_budget_guard("codex", fallbacks={"codex": "cursor"})
    assert chosen == "codex"
    assert "lane codex is credit-backed" in capsys.readouterr().err


def test_budget_guard_substitutes_codex_without_usable_credits(monkeypatch):
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: _guard_budget(_codex(credit_balance=0.0)))
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_args, **_kwargs: unavailable_reserve())
    assert delegate._resolve_agent_with_budget_guard("codex", fallbacks={"codex": "cursor"}) == "cursor"


# --- the gate on the real dispatch path --------------------------------------


@pytest.fixture
def dispatch_env(monkeypatch, tmp_path, snapshot):
    """Read-only dispatches with recorded worker spawns (same seams as test_delegate_bounded_advisory)."""
    import subprocess

    import scripts.audit.check_primary_integrity as cpi

    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setenv("LU_ALLOW_NOTEBOOK_DISPATCH", "1")
    monkeypatch.delenv("LU_DISPATCH_CHECK_BUDGET", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setattr(cpi, "check_primary_integrity", lambda *_a, **_k: (True, "primary on main (test stub)"))
    spawned: list[list[str]] = []
    real_popen = subprocess.Popen

    class _Stdin:
        def write(self, _data: bytes) -> None:
            pass

        def close(self) -> None:
            pass

    def fake_popen(command, *args, **kwargs):
        if not (isinstance(command, (list, tuple)) and "_worker" in command):
            return real_popen(command, *args, **kwargs)
        spawned.append(list(command))
        return type("_Proc", (), {"pid": 424242, "stdin": _Stdin()})()

    class _Health:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

    def health_only(url, *_args, **_kwargs):
        if "/api/health" in str(url):
            return _Health()
        raise AssertionError(f"unexpected urlopen {url}")

    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=delegate._REPO_ROOT, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", lambda **_kwargs: head_sha)
    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", health_only)
    telemetry = type("_Telemetry", (), {"model": "fixture-model", "effort": "high", "cli_version": "fixture"})()
    monkeypatch.setattr("agent_runtime.telemetry.resolve_dispatch_start_telemetry", lambda **_kwargs: telemetry)
    return type("_Env", (), {"tasks": tasks, "spawned": spawned, "snapshot": snapshot})()


def _dispatch_codex(model: str | None, task_id: str = "credit-worker") -> int:
    argv = ["dispatch", "--agent", "codex", "--task-id", task_id, "--prompt", "Map the parser flags."]
    if model is not None:
        argv += ["--model", model]
    argv += ["--mode", "read-only", "--cwd", str(delegate._REPO_ROOT)]
    return delegate.cmd_dispatch(delegate.build_parser().parse_args(argv))


def test_dispatch_refuses_off_allowlist_model_before_any_side_effect(dispatch_env, capsys, monkeypatch):
    monkeypatch.setattr(delegate, "_lane_default_model", lambda _agent: "gpt-5-codex")
    rc = _dispatch_codex(None)
    err = capsys.readouterr().err
    assert rc == 2, err
    assert "CREDIT_PERIOD_MODEL_REFUSED: lane codex is credit_backed" in err
    assert "model gpt-5-codex is outside the credit-period allowlist" in err
    assert dispatch_env.spawned == []
    assert not (dispatch_env.tasks / "credit-worker.json").exists()


@pytest.mark.parametrize("model", ["gpt-6.1-sol", None])
def test_dispatch_admits_allowlisted_and_default_model_on_credit_backed_lane(dispatch_env, capsys, model):
    rc = _dispatch_codex(model)
    err = capsys.readouterr().err
    assert rc == 0, err
    assert "CREDIT_PERIOD_MODEL_REFUSED" not in err
    assert len(dispatch_env.spawned) == 1


def test_dispatch_of_luna_passes_the_credit_gate(dispatch_env, capsys):
    rc = _dispatch_codex("gpt-6-luna")
    err = capsys.readouterr().err
    # Luna still needs its #9275 advisory envelope; the credit gate itself admits it.
    assert "CREDIT_PERIOD_MODEL_REFUSED" not in err
    assert "BOUNDED_ENVELOPE_REQUIRED" in err and rc == 2
    assert dispatch_env.snapshot["reads"] == 0
