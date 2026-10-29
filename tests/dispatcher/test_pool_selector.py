"""The approved selector acceptance table and the observation-only dispatch hook."""

import contextlib
import copy
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from scripts.dispatcher import cli
from scripts.dispatcher import pool_selector as s

NOW = datetime(2026, 1, 1, tzinfo=UTC)
SOON = NOW + timedelta(hours=1)
LATER = NOW + timedelta(days=1)


def pool(key, *, agent="codex", kind="subscription", **kw):
    return s.Pool(key, agent, kind, key, ("weekly",), authorized=True,
                  binding_verified=True, protects_held=True, **kw)


def meter(left=50, *, end=LATER, age=0, **kw):
    return s.Meter(NOW - timedelta(seconds=age), (s.Window("weekly", left, end),), "ok", **kw)


@pytest.mark.parametrize("case,expected,chosen,rejection", [
    ("unknown", s.Refused, None, "meter_not_checked"),
    ("stale", s.Refused, None, "meter_stale"),
    ("stale_boundary", s.Refused, None, "meter_stale"),
    ("future_observation", s.Refused, None, "meter_stale"),
    ("unknown_window", s.Refused, None, "window_not_checked"),
    ("malformed_window", s.Refused, None, "window_not_checked"),
    ("missing_deadline", s.Refused, None, "deadline_not_checked"),
    ("exhausted", s.Refused, None, "window_exhausted"),
    ("one_window_exhausted", s.Refused, None, "window_exhausted"),
    ("expiry_boundary", s.Selected, "second", "capacity_lapsed"),
    ("held", s.Selected, "second", "held"),
    ("unverified_protection", s.Refused, None, "held_credit_protection_not_checked"),
    ("deterministic_tie", s.Selected, "first", "lower_priority"),
    ("earliest_expiry", s.Selected, "second", "lower_priority"),
    ("claude_drain", s.Selected, "first", "lower_priority"),
    ("claude_99_switch", s.Selected, "second", "claude_99_percent_switch"),
    ("claude_session_relief", s.Selected, "second", "window_exhausted"),
    ("subscription_before_reset", s.Selected, "first", "lower_priority"),
    ("reset_before_api", s.ResetRequired, "second", "window_exhausted"),
    ("headless_api", s.Selected, "second", "headless_requires_api"),
    ("api_overflow", s.Selected, "second", "window_exhausted"),
])
def test_selector_acceptance_table(case, expected, chosen, rejection):
    first, second = pool("first"), pool("second")
    meters = {"first": meter(), "second": meter()}
    pools = [first]
    route, task = s.Route("codex", "approved-model"), s.Task()
    active = None
    if case == "unknown":
        meters = {}
    elif case.startswith("stale"):
        meters["first"] = meter(age=720 if case == "stale_boundary" else 721)
    elif case == "future_observation":
        meters["first"] = meter(age=-1)
    elif case == "unknown_window":
        meters["first"] = s.Meter(NOW, (), "ok")
    elif case == "malformed_window":
        meters["first"] = meter(float("nan"))
    elif case == "missing_deadline":
        meters["first"] = meter(end=None)
    elif case == "exhausted":
        meters["first"] = meter(0)
    elif case == "one_window_exhausted":
        meters["first"] = replace(meter(), windows=(*meter().windows, s.Window("session", 0, SOON)))
    elif case == "unverified_protection":
        pools = [replace(first, protects_held=False)]
    else:
        pools = [first, second]
        if case == "expiry_boundary":
            meters["first"] = meter(end=NOW)
        elif case == "held":
            pools[0] = replace(first, held=True)
        elif case == "earliest_expiry":
            meters["second"] = meter(end=SOON)
        elif case.startswith("claude"):
            route = s.Route("claude", "approved-model")
            pools = [pool("first", agent="claude"), pool("second", agent="claude")]
            active = "first"
            meters["first"] = meter(1 if case == "claude_99_switch" else 1.01)
            meters["second"] = meter(end=SOON)
            if case == "claude_session_relief":
                meters["first"] = replace(meter(), windows=(*meter().windows, s.Window("session", 0, SOON)))
        elif case == "subscription_before_reset":
            pools[1] = pool("second", kind="reset")
            meters["second"] = meter(end=SOON)
        elif case == "reset_before_api":
            pools += [pool("third", kind="api")]
            pools[1] = pool("second", kind="reset")
            meters.update(first=meter(0), third=meter(end=SOON))
        elif case in {"headless_api", "api_overflow"}:
            pools[1] = pool("second", kind="api")
            if case == "headless_api":
                task = s.Task(headless=True)
            else:
                meters["first"] = meter(0)
    policy = s.Policy("test-policy", tuple(pools), claude_active_pool=active)
    original = copy.deepcopy((route, task, meters, policy))
    decision = s.choose_pool(route, task, meters, policy, NOW)
    assert type(decision) is expected
    assert getattr(decision, "pool", None) == chosen
    assert rejection in {r.reason for r in decision.rejected}
    # Candidate iteration order never affects either the decision or its explanation.
    assert s.choose_pool(route, task, meters, replace(policy, pools=tuple(reversed(pools))), NOW) == decision
    assert (route, task, meters, policy) == original


def test_dispatch_records_shadow_without_changing_account(tmp_path, monkeypatch):
    """A different shadow account reaches storage but cannot enter the launch spec."""
    from scripts.dispatcher import store

    record = {"task_id": "shadow-hook", "status": "spawning", "agent": "claude", "model": "approved-model",
              "provider": None, "claude_account": "live-login", "prompt_file": str(tmp_path / "task.prompt")}
    shadow = {"decision": "Selected", "pool": "shadow-account", "shadow_only": True}
    seen = {}
    args = cli.build_parser().parse_args(["dispatch", "--agent", "claude", "--model", "approved-model",
        "--task-id", "shadow-hook", "--prompt", "bounded task", "--mode", "read-only", "--worktree"])
    monkeypatch.setattr(cli.admission, "claude_account", lambda *_: {"claude_account": "live-login"})
    monkeypatch.setattr(cli.git, "resolve_repo", lambda *_: (tmp_path, {"key": "public", "github": "test/repo"}))
    monkeypatch.setattr(cli.git, "worktree_plan", lambda *_args, **_kw: (tmp_path, "test-branch", "a" * 40))
    monkeypatch.setattr(cli.git, "create_worktree", lambda *_args, **_kw: None)
    monkeypatch.setattr(cli.worker, "settle_left_worktrees", lambda: None)
    monkeypatch.setattr(cli.host_admission, "precheck", lambda *_args, **_kw: None)
    monkeypatch.setattr(cli.headroom, "check_plan", lambda *_args, **_kw: None)
    monkeypatch.setattr(cli.host_admission, "check_credit", lambda *_: None)
    monkeypatch.setattr(cli.host_admission, "check", lambda *_args, **_kw: None)
    monkeypatch.setattr(cli.host_admission, "reserve", lambda *_args, **_kw: contextlib.nullcontext())
    monkeypatch.setattr(cli.checks, "check_bounded_advisory", lambda *_: {})
    monkeypatch.setattr(cli.checks, "check_advisory_role", lambda *_: {})
    monkeypatch.setattr(cli.checks, "check_private_input", lambda *_: None)
    monkeypatch.setattr(cli.checks, "check_review_family", lambda *_: None)
    monkeypatch.setattr(cli.providers, "read_only_refusal", lambda *_: None)
    monkeypatch.setattr(cli, "child_env", lambda *_: {})
    monkeypatch.setattr(store, "read", lambda *_args, **_kw: None)
    monkeypatch.setattr(store, "record_path", lambda *_: tmp_path / "task.json")
    monkeypatch.setattr(store, "new_record", lambda *_args, **_kw: dict(record, run_nonce="nonce"))
    monkeypatch.setattr(s, "shadow_decision", lambda actual: dict(shadow))

    def start(spec, actual, prompt, *_):
        seen.update(spec_account=spec.claude_account)
        store.create(actual, prompt)

    monkeypatch.setattr(cli.worker, "start", start)
    assert cli._dispatch(args) == 0
    saved = json.loads((tmp_path / "task.json").read_text())
    assert seen["spec_account"] == "live-login"
    assert saved["claude_account"] == "live-login"
    assert saved["pool_shadow"] == shadow
