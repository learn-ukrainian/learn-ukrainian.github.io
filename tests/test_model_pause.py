"""Operator model pauses and plan-headroom stops for new dispatches."""

from __future__ import annotations

import contextlib
import json
from datetime import UTC, datetime, timedelta

import pytest

from scripts.agent_runtime import model_pause as mp
from tests.claude_route_accounts import HOST_ACCOUNT, account, unresolved

NOW = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
POLICY = {
    "pauses": [{"pattern": "claude-opus-*", "until": "2026-10-12T07:00:00Z", "reason": "operator pause"}],
    "headroom": [{"lane": "claude", "pattern": "claude-*", "max_weekly_used_pct": 87}],
}


def test_paused_model_is_refused_until_the_reset() -> None:
    with pytest.raises(mp.ModelPausedRefused, match="MODEL_PAUSED"):
        mp.refuse_paused_models(["claude-opus-5-5"], policy=POLICY, now=NOW, used_pct=lambda _l: 10.0)


def test_pause_lifts_by_itself_after_until() -> None:
    later = datetime(2026, 10, 12, 7, 0, tzinfo=UTC) + timedelta(seconds=1)
    mp.refuse_paused_models(["claude-opus-5-5"], policy=POLICY, now=later, used_pct=lambda _l: 10.0)


def test_other_models_pass_while_headroom_remains() -> None:
    mp.refuse_paused_models(
        ["claude-sonnet-5-5", "gpt-6.1-sol", None], policy=POLICY, now=NOW, used_pct=lambda _l: 84.0
    )


def test_headroom_stop_refuses_matching_models_only() -> None:
    with pytest.raises(mp.ModelPausedRefused, match="MODEL_HEADROOM"):
        mp.refuse_paused_models(["claude-sonnet-5-5"], policy=POLICY, now=NOW, used_pct=lambda _l: 87.0)
    mp.refuse_paused_models(["gpt-6.1-sol"], policy=POLICY, now=NOW, used_pct=lambda _l: 99.0)
    agy = mp.policy_for_seat("agy", review=True)
    assert any(entry.get("lane") == mp.AGY_CLAUDE_WINDOW_LANE for entry in agy["headroom"])
    with pytest.raises(mp.ModelPausedRefused, match="MODEL_HEADROOM"):
        mp.refuse_paused_models(["claude-opus-5-5-high"], policy=agy, now=NOW, used_pct=lambda _lane: 100.0)
    mp.refuse_paused_models(["gemini-3.8-flash-high"], policy=agy, now=NOW, used_pct=lambda _lane: 100.0)
    mp.refuse_paused_models(["claude-opus-5-5"], policy=agy, now=NOW, used_pct=lambda _lane: 99.0)
    with pytest.raises(mp.ModelPausedRefused, match="MODEL_HEADROOM_USAGE_UNKNOWN"):
        mp.refuse_paused_models(["claude-sonnet-5-5-agy"], policy=agy, now=NOW, used_pct=lambda _lane: None)
    assert mp.policy_for_seat("agy", check_headroom=False)["headroom"] == []
    native = mp.policy_for_seat("claude", review=True)["headroom"]
    assert all(entry.get("lane") != mp.AGY_CLAUDE_WINDOW_LANE for entry in native)


def test_unreadable_usage_refuses_matching_models_only() -> None:
    with pytest.raises(mp.ModelPausedRefused, match="MODEL_HEADROOM_USAGE_UNKNOWN"):
        mp.refuse_paused_models(["claude-sonnet-5-5"], policy=POLICY, now=NOW, used_pct=lambda _l: None)
    mp.refuse_paused_models(["gpt-6.1-sol"], policy=POLICY, now=NOW, used_pct=lambda _l: None)


def test_headroom_refuses_when_usage_is_stale_under_an_active_cap(monkeypatch) -> None:
    """An active cap must not silently admit capped models when telemetry is stale."""
    _serve(monkeypatch, {
        "agents": {"claude": {"status": "hot", "codexbar": {
            "stale": True, "freshness": "stale_last_good", "weekly_used_pct": 91,
        }}},
    })
    with pytest.raises(mp.ModelPausedRefused, match="MODEL_HEADROOM_USAGE_UNKNOWN"):
        mp.refuse_paused_models(
            ["claude-sonnet-5-5"], policy=POLICY, now=NOW,
            used_pct=mp.account_used_pct(HOST_ACCOUNT),
        )


def test_missing_policy_file_means_no_pauses(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(tmp_path / "absent.json"))
    assert mp.load_policy() == {}
    mp.refuse_paused_models(["claude-opus-5-5"], used_pct=mp.account_used_pct(HOST_ACCOUNT))


def test_policy_file_is_read(tmp_path, monkeypatch) -> None:
    path = tmp_path / "pause.json"
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    path.write_text(json.dumps({"pauses": [{"pattern": "claude-opus-*", "until": future}]}))
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(path))
    with pytest.raises(mp.ModelPausedRefused):
        mp.refuse_paused_models(["claude-opus-5-5"], used_pct=mp.account_used_pct(HOST_ACCOUNT))


def test_admission_refuses_a_paused_seat_default(tmp_path, monkeypatch) -> None:
    from scripts.agent_runtime import target_admission as ta

    path = tmp_path / "pause.json"
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    path.write_text(json.dumps({"pauses": [{"pattern": "paused-model-*", "until": future}]}))
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(path))
    monkeypatch.setattr(ta, "_seat_default_model", lambda seat: "paused-model-1")
    with pytest.raises(mp.ModelPausedRefused):
        ta._refuse_paused([None, ta._seat_default_model("claude")], claude_account=HOST_ACCOUNT, review=True)


def test_reviewer_resolver_excludes_a_paused_candidate(tmp_path, monkeypatch) -> None:
    from scripts.review import reviewer_resolver as rr

    candidate = next(iter(rr.REVIEW_CANDIDATES.values()))
    model = rr.candidate_dispatch_model(candidate)
    path = tmp_path / "pause.json"
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    path.write_text(json.dumps({"pauses": [{"pattern": model, "until": future}]}))
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(path))
    reason = rr._hard_exclusion_reason(candidate, rr.ResolverInputs(author_model="gpt-6.1-sol", claude_account=HOST_ACCOUNT))
    assert reason and "MODEL_PAUSED" in reason


def test_invalid_policy_shapes_are_inert() -> None:
    for policy in ({"pauses": 1}, {"headroom": 1}, {"pauses": [1, "x"]}, {"headroom": [None]}):
        mp.refuse_paused_models(["claude-opus-5-5"], policy=policy, now=NOW, used_pct=lambda _l: 99.0)


def test_malformed_usage_is_unreadable(monkeypatch) -> None:
    import io

    for payload in ("[1, 2]", '{"agents": {"claude": {"codexbar": [1]}}}', '{"agents": 3}'):
        monkeypatch.setattr(mp.urllib.request, "urlopen", lambda *a, _p=payload, **k: io.StringIO(_p))
        assert mp.routing_budget_used_pct("claude", account=HOST_ACCOUNT) is None


def test_messaging_admission_ignores_pauses(tmp_path, monkeypatch) -> None:
    from scripts.agent_runtime import target_admission as ta

    called: list = []
    monkeypatch.setattr(ta, "_refuse_paused", lambda models: called.append(list(models)))
    with contextlib.suppress(Exception):  # other gates may refuse; the pause gate must not
        ta.resolve_and_admit(["claude"], mode="bridge")
    assert called == []


def test_every_dispatch_admission_caller_opts_in() -> None:
    import ast
    from pathlib import Path

    for name in ("cli", "worker"):
        tree = ast.parse(Path(f"scripts/dispatcher/{name}.py").read_text())
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call) and ast.unparse(node.func) == "headroom.check_plan"
        ]
        assert calls, name
        assert all(len(call.args) == 3 and any(k.arg == "review" for k in call.keywords) for call in calls), name


def _agy_window_payload(weekly, five_hour=1.0, *, stale=False, freshness="fresh", status="hot", present=True):
    probe = {"stale": stale, "freshness": freshness, "weekly_used_pct": 22.0}

    def block(used):
        if used is None:
            return {"used_pct": None, "remaining_pct": None}
        return {"used_pct": used, "remaining_pct": max(0.0, 100.0 - used)}

    info = {"status": status, "codexbar": probe}
    if present:
        windows = {"five_hour": block(five_hour), "weekly": block(weekly)}
        info["claude_gpt_windows"] = windows
        probe["claude_gpt_windows"] = windows
    return {
        "diagnostics": {"stale": True},
        "agents": {
            "gemini": info,
            "claude": {"status": "hot", "codexbar": {"stale": False, "freshness": "fresh", "weekly_used_pct": 90}},
        },
    }


def _budget(monkeypatch, payload: dict) -> float | None:
    import io

    monkeypatch.setattr(mp.urllib.request, "urlopen", lambda *a, **k: io.StringIO(json.dumps(payload)))
    return mp.routing_budget_used_pct("claude", account=HOST_ACCOUNT)


def test_only_fresh_probe_readings_count(monkeypatch) -> None:
    fresh = {"stale": False, "freshness": "fresh", "weekly_used_pct": 91}
    ok = {"diagnostics": {"stale": False}, "agents": {"claude": {"status": "hot", "codexbar": fresh}}}
    assert _budget(monkeypatch, ok) == 91.0
    for bad in (
        {**ok, "agents": {"claude": {"status": "near_cap", "codexbar": {**fresh, "stale": True}}}},
        {**ok, "agents": {"claude": {"status": "near_cap", "codexbar": {**fresh, "freshness": "stale_last_good"}}}},
        {**ok, "agents": {"claude": {"status": "unknown", "codexbar": fresh}}},
    ):
        assert _budget(monkeypatch, bad) is None
    monkeypatch.setattr(
        mp, "routing_budget_used_pct", getattr(mp.routing_budget_used_pct, "__wrapped__", mp.routing_budget_used_pct),
    )

    def agy(payload) -> float | None:
        _serve(monkeypatch, payload)
        return mp.routing_budget_used_pct(mp.AGY_CLAUDE_WINDOW_LANE, account=HOST_ACCOUNT)

    assert agy(_agy_window_payload(100.0)) == 100.0
    assert agy(_agy_window_payload(10.0, five_hour=100.0)) == 100.0
    assert agy(_agy_window_payload(10.0, five_hour=1.0)) == 10.0
    assert agy(_agy_window_payload(10.0, stale=True)) is None
    assert agy(_agy_window_payload(10.0, freshness="stale_last_good")) is None
    assert agy(_agy_window_payload(10.0, status="unknown")) is None
    assert agy(_agy_window_payload(10.0, present=False)) is None
    assert agy(_agy_window_payload(None)) is None

    def unusable(weekly: dict) -> float | None:
        payload = _agy_window_payload(10.0)
        gemini = payload["agents"]["gemini"]
        gemini["claude_gpt_windows"]["weekly"] = weekly
        gemini["codexbar"]["claude_gpt_windows"]["weekly"] = weekly
        return agy(payload)

    plausible = {"remaining_pct": 90}
    for used in (float("nan"), float("inf"), True, None, 10**400):
        assert unusable({"used_pct": used, **plausible}) is None
    assert unusable({"used_pct": 10, "remaining_pct": 90, "freshness": None}) is None
    assert unusable({"used_pct": 10, "remaining_pct": 90, "freshness": False}) is None


def test_window_used_pct_requires_false_stale_and_finite_remaining() -> None:
    """Defect (#12367): a non-false stale flag or a non-finite remaining percent was read as usage."""
    for stale in (None, "false", "true", 0):
        assert mp._window_used_pct({"used_pct": 10, "remaining_pct": 90, "stale": stale}) is None
    for remaining in (float("nan"), float("inf"), "90", None):
        assert mp._window_used_pct({"used_pct": 10, "remaining_pct": remaining}) is None
    # Control: valid readings keep today's result.
    assert mp._window_used_pct({"used_pct": 10, "remaining_pct": 90, "stale": False}) == 10.0
    assert mp._window_used_pct({"used_pct": 10}) == 10.0
    assert mp._window_used_pct({"remaining_pct": 0, "stale": False}) == 100.0


def test_aggregate_snapshot_staleness_does_not_hide_a_fresh_lane(monkeypatch) -> None:
    fresh = {"stale": False, "freshness": "fresh", "weekly_used_pct": 91}
    payload = {"diagnostics": {"stale": True}, "agents": {"claude": {"status": "hot", "codexbar": fresh}}}
    assert _budget(monkeypatch, payload) == 91.0


def test_truncated_response_is_unavailable(monkeypatch) -> None:
    import http.client

    def boom(*_a, **_k):
        raise http.client.IncompleteRead(b"{")

    monkeypatch.setattr(mp.urllib.request, "urlopen", boom)
    assert mp.routing_budget_used_pct("claude", account=HOST_ACCOUNT) is None


def test_native_claude_alias_is_paused_with_its_family() -> None:
    policy = {"pauses": [{"pattern": "claude-opus-*", "until": "2999-01-01T00:00:00Z"}]}
    for alias in ("opus", "Opus", "opus[1m]"):
        assert mp.refusal_reason(alias, policy=policy, now=NOW, used_pct=lambda _l: None)
    assert mp.refusal_reason("sonnet", policy=policy, now=NOW, used_pct=lambda _l: None) is None


def test_native_alias_matches_a_concrete_pause(monkeypatch) -> None:
    from scripts.review import model_catalog

    catalog = {
        "models": {
            "claude-opus-5-4": {"family": "anthropic"},
            "claude-opus-5-5": {"family": "anthropic"},
            "claude-sonnet-5-5": {"family": "anthropic"},
        }
    }
    monkeypatch.setattr(model_catalog, "load_model_catalog", lambda *a, **k: catalog)
    policy = {"pauses": [{"pattern": "claude-opus-5-5", "until": "2999-01-01T00:00:00Z"}]}
    for alias in ("opus", "opus[1m]"):
        assert mp.refusal_reason(alias, policy=policy, now=NOW, used_pct=lambda _l: None)
    old = {"pauses": [{"pattern": "claude-opus-5-4", "until": "2999-01-01T00:00:00Z"}]}
    assert mp.refusal_reason("opus", policy=old, now=NOW, used_pct=lambda _l: None) is None


# --- #10619: the headroom stop reads the account a claude dispatch runs as -----------------


def _account(left: float | None, *, status: str = "ok") -> dict:
    window = {"left_pct": left, "resets_at": None, "pace": None, "pace_delta_pct": None, "leftover_pct": None}
    return {
        "session5h": dict(window, left_pct=100.0),
        "weekly": window,
        "updated": None,
        "age_s": 60.0,
        "stale": status == "stale",
        "status": status,
        "reason": None,
    }


def _accounts_payload(b_row: dict | None) -> dict:
    fresh = {"stale": False, "freshness": "fresh"}
    return {
        "agents": {
            "claude": {"status": "hot", "codexbar": {**fresh, "weekly_used_pct": 84}},
            "codex": {"status": "cool", "codexbar": {**fresh, "weekly_used_pct": 30}},
        },
        "claude_accounts": {} if b_row is None else {"claude:b": b_row},
    }


def _serve(monkeypatch, payload: dict) -> None:
    import io

    monkeypatch.setattr(mp.urllib.request, "urlopen", lambda *a, **k: io.StringIO(json.dumps(payload)))


@pytest.mark.parametrize(
    ("b_row", "expected"),
    [
        (_account(89.0), 11.0),
        (_account(15.0), 85.0),
        (_account(89.0, status="stale"), None),
        ({**_account(89.0), "stale": True}, None),
        (_account(None, status="unknown"), None),
        (_account(None), None),
        (_account(101.0), None),
        (None, None),
    ],
)
def test_selected_claude_account_reads_only_its_own_fresh_row(monkeypatch, b_row, expected) -> None:
    _serve(monkeypatch, _accounts_payload(b_row))
    assert mp.routing_budget_used_pct("claude", account=account("b")) == expected
    # Without its own row the default account uses the lane probe.
    for default in (HOST_ACCOUNT, account("a"), account("a", "default-file")):
        assert mp.routing_budget_used_pct("claude", account=default) == 84.0
    assert mp.routing_budget_used_pct("codex", account=account("b")) == 30.0
    # #10630: no account named, or one unresolved, never reads a claude meter.
    for unnamed in (None, unresolved("claude_account_default_file_invalid")):
        assert mp.routing_budget_used_pct("claude", account=unnamed) is None
        assert mp.routing_budget_used_pct("codex", account=unnamed) == 30.0
    # An account row wins over a stale lane, including for the default account.
    if b_row is not None:
        payload = _accounts_payload(None)
        payload["agents"]["claude"]["codexbar"].update(stale=True, freshness="stale_last_good")
        payload["claude_accounts"] = {"claude:a": b_row}
        _serve(monkeypatch, payload)
        assert mp.routing_budget_used_pct("claude", account=HOST_ACCOUNT) == expected


def test_account_reader_holds_only_on_the_selected_accounts_meter(monkeypatch) -> None:
    policy = {"headroom": [{"lane": "claude", "pattern": "claude-*", "max_weekly_used_pct": 80}]}
    _serve(monkeypatch, _accounts_payload(_account(89.0)))
    reader = mp.account_used_pct(account("b"))
    assert mp.refusal_reason("claude-opus-5-5", policy=policy, now=NOW, used_pct=reader) is None
    for default in (HOST_ACCOUNT, account("a")):
        held = mp.refusal_reason("claude-opus-5-5", policy=policy, now=NOW, used_pct=mp.account_used_pct(default))
        assert held == "MODEL_HEADROOM: claude-opus-5-5 is held for plan headroom"
    # An unnamed or unresolved account has no meter, so an active cap refuses it.
    for unnamed in (None, unresolved("claude_account_binding_missing")):
        held = mp.refusal_reason("claude-opus-5-5", policy=policy, now=NOW, used_pct=mp.account_used_pct(unnamed))
        assert held == "MODEL_HEADROOM_USAGE_UNKNOWN: claude-opus-5-5 has no fresh plan usage reading"


def test_usage_readers_require_a_named_claude_account(monkeypatch) -> None:
    """#10630 row 1: there is no default account; a bare label or a missing account fails loudly."""
    _serve(monkeypatch, _accounts_payload(_account(89.0)))
    with pytest.raises(TypeError, match="missing 1 required keyword-only argument: 'account'"):
        mp.routing_budget_used_pct("claude")
    for bare in ("b", "a"):
        with pytest.raises(TypeError, match="named ClaudeAccount"):
            mp.routing_budget_used_pct("claude", account=bare)
        with pytest.raises(TypeError, match="named ClaudeAccount"):
            mp.account_used_pct(bare)
    with pytest.raises(TypeError, match="used_pct"):
        mp.refuse_paused_models(["claude-opus-5-5"], policy={"headroom": []}, now=NOW)


@pytest.mark.parametrize("case,expected", [
    ("ban", "MODEL_ROLE_BANNED"), ("other_role", None), ("expired", None), ("future", None),
    ("trial", "MODEL_ROLE_TRIAL_SHADOW_REQUIRED"), ("shadow", None),
    ("missing_role", "MODEL_ROLE_REQUIRED"), ("malformed", "MODEL_ROLE_POLICY_INVALID"),
    ("caller_failure", "MODEL_ROLE_POLICY_INVALID"), ("forged_source", "MODEL_ROLE_POLICY_INVALID"),
    ("wrong_model", "MODEL_ROLE_POLICY_INVALID"), ("alias", "MODEL_ROLE_BANNED"),
    ("unknown_model", "MODEL_ROLE_POLICY_INVALID"),
    ("review_flags_ban", "MODEL_ROLE_BANNED"),
    ("review_flags_trial", "MODEL_ROLE_TRIAL_SHADOW_REQUIRED"),
])
def test_role_policy_validation_and_expiry(tmp_path, monkeypatch, case, expected):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    task = {"task_id": "role-run", "model": "claude-opus-5-5", "status": "timeout", "duration_s": 12,
            "started_at": "2026-10-09T12:00:00Z", "kill_reason": "hard_timeout",
            "error": "process deadline exceeded"}
    (tasks / "role-run.json").write_text(json.dumps(task))
    run = {"task_id": "role-run", "status": "timeout", "duration_s": 12, "timeout_source": "caller",
           "cause": "process deadline exceeded", "model_failure": False}
    entry = {"model": "claude-opus-5-5", "roles": ["review"], "reason": "Decision citing role-run",
             "start": "2026-10-10T00:00:00Z", "review_date": "2026-10-12T00:00:00Z", "decided_by": "cto",
             "evidence": {"window_start": "2026-10-09T00:00:00Z", "window_end": "2026-10-10T00:00:00Z",
                          "dispatch_records": [run]}}
    policy = {"bans": [entry], "trials": []}
    roles, model, shadow = {"review"}, "claude-opus-5-5", False
    if case == "other_role":
        roles = {"implementation"}
    elif case == "expired":
        entry["review_date"] = NOW.isoformat()
    elif case == "future":
        entry["start"] = "2026-10-11T00:00:00Z"
    elif case in {"trial", "shadow"}:
        policy = {"bans": [], "trials": [entry]}
        shadow = case == "shadow"
    elif case == "missing_role":
        roles = set()
    elif case == "malformed":
        entry["roles"] = "review"
    elif case == "caller_failure":
        run["model_failure"] = True
    elif case == "forged_source":
        run.update(timeout_source="provider", model_failure=True)
    elif case == "wrong_model":
        task["model"] = "gpt-6.1-sol"
        (tasks / "role-run.json").write_text(json.dumps(task))
    elif case == "alias":
        model = "opus[1m]"
    elif case == "unknown_model":
        entry["model"] = "unknown-model"
    elif case == "review_flags_trial":
        policy = {"bans": [], "trials": [entry]}
    path = tmp_path / "model-roles.json"
    path.write_text(json.dumps(policy))
    monkeypatch.setenv("LU_MODEL_ROLES_FILE", str(path))
    reason = mp.role_refusal_reason(model, roles, now=NOW, shadow=shadow)
    assert (reason.split(":", 1)[0] if reason else None) == expected
    if case.startswith("review_flags_"):
        # A non-review research role must not hide review activity at either admission boundary.
        for field, value in [
            ("review_mode", "cross_family"), ("review_mode", "red_team"), ("type", "review"),
            ("pr", 42), ("review_attempt", {"review_id": "r1"}), ("require_review_verdict", True),
            ("review_profile", "code"), ("review_author_model", "gpt-6.1-sol"),
            ("risk", "critical"), ("review_risk", "critical"), ("language_lane", "ukrainian"),
            ("subject_seat", ["codex"]), ("subject_family", ["openai"]),
            ("review_subject_seats", ["codex"]), ("review_subject_families", ["openai"]),
        ]:
            inferred = mp.dispatch_roles({"research_role": "authoring", "mode": "read-only", field: value})
            reason = mp.role_refusal_reason(model, inferred, now=NOW)
            assert (reason.split(":", 1)[0] if reason else None) == expected, (field, value)
        assert mp.dispatch_roles({"research_role": "authoring", "mode": "read-only"}) == {"authoring"}
