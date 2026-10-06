"""#9518: credit-balance lanes, the credit-period model allowlist and reset advice.

Covers the state machine (``scripts.fleet.credit_lane``) including the
rate-limit evidence rule and UTC-only timestamps, the router rows and output
(``scripts.fleet.capacity_pick``), dispatch admission
(``delegate._credit_period_refusal`` and the ``--check-budget`` guard), a bad
policy file's blast radius, and a lock that every lane without a credit
policy keeps its origin/main row.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.fleet import capacity_pick, credit_lane, reset_reserve
from scripts.fleet.reset_reserve import unavailable_reserve

NOW = datetime(2026, 10, 2, 17, 0, tzinfo=UTC)
POLICY = credit_lane.load_policy()
# conftest replaces the runtime-records reader per test; keep the real one.
REAL_RATE_LIMIT_READER = credit_lane.read_recent_rate_limits


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
            "fetched_at": (NOW - timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
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
    assert (
        POLICY.near_cap_remaining_pct,
        POLICY.credit_max_age_s,
        POLICY.rate_limit_window_s,
        POLICY.reset_hold_hours,
    ) == (10.0, 900.0, 3600.0, 48.0)


def test_builtin_default_allowlist_equals_shipped_policy():
    assert POLICY.allowed_models == credit_lane.DEFAULT_ALLOWED_MODELS


def test_policy_allowlist_names_active_catalog_models():
    from scripts.review.model_catalog import canonical_model_id, load_model_catalog

    catalog = load_model_catalog()
    for models in POLICY.allowed_models.values():
        for model in models:
            assert canonical_model_id(model) == model
            assert catalog["models"][model]["lifecycle"] == "active"


_GOOD_HEAD = (
    "schema_version: credit-lanes.v1\nnear_cap_remaining_pct: 10\ncredit_max_age_s: 900\n"
    "rate_limit_window_s: 3600\nreset_hold_hours: 48\n"
)
BAD_POLICIES = {
    "malformed-yaml": "schema_version: credit-lanes.v1\nlanes: {codex: [unclosed\n",
    "schema": "schema_version: other\nlanes: {}\n",
    "empty-allowlist": _GOOD_HEAD + "lanes: {codex: {allowed_models: []}}\n",
    "no-lanes": _GOOD_HEAD + "lanes: {}\n",
    "negative-threshold": _GOOD_HEAD.replace("near_cap_remaining_pct: 10", "near_cap_remaining_pct: -1")
    + "lanes: {codex: {allowed_models: [gpt-6.1-sol]}}\n",
    "threshold-string": _GOOD_HEAD.replace("near_cap_remaining_pct: 10", "near_cap_remaining_pct: ten")
    + "lanes: {codex: {allowed_models: [gpt-6.1-sol]}}\n",
    "zero-rate-limit-window": _GOOD_HEAD.replace("rate_limit_window_s: 3600", "rate_limit_window_s: 0")
    + "lanes: {codex: {allowed_models: [gpt-6.1-sol]}}\n",
    "missing-rate-limit-window": _GOOD_HEAD.replace("rate_limit_window_s: 3600\n", "")
    + "lanes: {codex: {allowed_models: [gpt-6.1-sol]}}\n",
    "lanes-list": _GOOD_HEAD + "lanes: [codex]\n",
    "allowlist-string": _GOOD_HEAD + "lanes: {codex: {allowed_models: gpt-6.1-sol}}\n",
    "top-level-list": "- codex\n",
}


@pytest.mark.parametrize("text", list(BAD_POLICIES.values()), ids=list(BAD_POLICIES))
def test_malformed_policy_raises(tmp_path, text):
    path = tmp_path / "credit_lanes.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        credit_lane.load_policy(path)


def test_missing_policy_file_raises(tmp_path):
    with pytest.raises(ValueError, match="cannot read credit-lane policy"):
        credit_lane.load_policy(tmp_path / "absent.yaml")


# --- state machine -----------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"remaining_pct": 60.0, "codexbar": {"weekly_remaining_pct": 60.0}}, credit_lane.PLAN_HEALTHY),
        ({}, credit_lane.CREDIT_BALANCE_PRESENT),
        (
            {
                "remaining_pct": 10.0,
                "codexbar": {"weekly_remaining_pct": 10.0, "freshness": "fresh", "fetched_at": "2026-10-02T16:59:00Z"},
            },
            credit_lane.CREDIT_BALANCE_PRESENT,
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
        ({"runtime": {"headroom_blocked": True}}, credit_lane.CREDIT_USE_UNCONFIRMED),
        (
            {"runtime": {"window_s": 300, "rate_limited": 4, "headroom_blocked": False}},
            credit_lane.CREDIT_USE_UNCONFIRMED,
        ),
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
        "runtime-headroom-blocked",
        "runtime-rate-limited-unblocked",
        "plan-unknown",
    ],
)
def test_state_machine(overrides, expected):
    state = credit_lane.lane_credit_state("codex", _codex(**overrides), POLICY, now=NOW)
    assert state["state"] == expected, state
    assert state["allowed_models"] == ["gpt-6.1-sol", "gpt-6-luna"]
    if expected == credit_lane.CREDIT_BALANCE_PRESENT:
        assert state["reason"].endswith("draw not verified by the router")
        assert state["credit_balance"] == 62500.0
        assert state["coverage"] == {"dispatches": None, "basis": credit_lane.COVERAGE_BASIS}
    else:
        assert "coverage" not in state


def test_tightest_plan_window_governs():
    info = _codex(remaining_pct=60.0, codexbar={**_codex()["codexbar"], "weekly_remaining_pct": 60.0})
    info["codexbar"]["primary_remaining_pct"] = 3.0
    assert credit_lane.lane_credit_state("codex", info, POLICY, now=NOW)["state"] == credit_lane.CREDIT_BALANCE_PRESENT


def test_stale_snapshot_fails_closed():
    state = credit_lane.lane_credit_state("codex", _codex(), POLICY, now=NOW, snapshot_stale=True)
    assert state["state"] == credit_lane.CREDITS_UNVERIFIED


def test_balance_falls_back_to_native_record():
    info = _codex(credit_balance=None)
    info["codexbar"]["credit_balance"] = 100.0
    assert credit_lane.lane_credit_state("codex", info, POLICY, now=NOW)["state"] == credit_lane.CREDIT_BALANCE_PRESENT


def test_unconfigured_lane_ignores_credit_data():
    assert credit_lane.lane_credit_state("claude", _codex(), POLICY) == {"state": credit_lane.NOT_CONFIGURED}
    assert credit_lane.lane_credit_report("cursor", _codex(), POLICY) == {"state": credit_lane.NOT_CONFIGURED}


# --- reset advice ------------------------------------------------------------


def _advice(info: dict, state: str = credit_lane.CREDIT_BALANCE_PRESENT) -> dict:
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


# --- rate-limit evidence -----------------------------------------------------


def _rate_limits(monkeypatch, count: int, last: str | None = "2026-10-02T16:40:00Z") -> list:
    calls: list = []

    def read(lane, window_s, *, now=None, usage_dir=None):
        calls.append((lane, window_s, now))
        return {"count": count, "last_rate_limited_at": last if count else None}

    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", read)
    return calls


def test_recent_rate_limit_refutes_the_credit_balance(monkeypatch):
    calls = _rate_limits(monkeypatch, 1)
    state = credit_lane.lane_credit_state("codex", _codex(), POLICY, now=NOW)
    assert state["state"] == credit_lane.CREDIT_USE_UNCONFIRMED
    assert state["reason"] == "recent rate limit while the plan window is exhausted: credit use not confirmed"
    assert state["evidence"] == {
        "rate_limited_count": 1,
        "rate_limit_window_s": 3600.0,
        "last_rate_limited_at": "2026-10-02T16:40:00Z",
        "credit_balance": 62500.0,
        "credit_fetched_at": "2026-10-02T16:59:00Z",
    }
    assert "coverage" not in state
    assert calls == [("codex", 3600.0, NOW)]


def test_rate_limits_are_not_read_while_the_plan_is_healthy(monkeypatch):
    calls = _rate_limits(monkeypatch, 3)
    info = _codex(remaining_pct=60.0, codexbar={**_codex()["codexbar"], "weekly_remaining_pct": 60.0})
    assert credit_lane.lane_credit_state("codex", info, POLICY, now=NOW)["state"] == credit_lane.PLAN_HEALTHY
    assert calls == []


def test_snapshot_runtime_window_wider_than_policy_is_not_counted(monkeypatch):
    _rate_limits(monkeypatch, 0)
    info = _codex(runtime={"window_s": 7200, "rate_limited": 2, "headroom_blocked": False})
    assert credit_lane.lane_credit_state("codex", info, POLICY, now=NOW)["state"] == credit_lane.CREDIT_BALANCE_PRESENT


def test_unreadable_runtime_records_fail_closed(monkeypatch):
    def broken(*_args, **_kwargs):
        raise OSError("usage dir unreadable")

    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", broken)
    state = credit_lane.lane_credit_state("codex", _codex(), POLICY, now=NOW)
    assert state["state"] == credit_lane.CREDITS_UNVERIFIED
    assert state["reason"] == "runtime usage records unreadable"


def test_real_reader_counts_rate_limits_inside_the_window_only(monkeypatch, tmp_path):
    from scripts.agent_runtime import usage

    usage._reset_rate_limit_cache_for_tests()
    monkeypatch.setattr(usage, "_usage_dir", lambda: tmp_path)
    records = [
        {"ts": "2026-10-02T16:30:00Z", "outcome": "rate_limited", "model": "gpt-6.1-sol"},
        {"ts": "2026-10-02T16:45:00Z", "outcome": "ok", "model": "gpt-6.1-sol"},
        {"ts": "2026-10-02T15:30:00Z", "outcome": "rate_limited", "model": "gpt-6.1-sol"},
    ]
    (tmp_path / "usage_codex-delegate_2026-10-02.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
    )
    (tmp_path / "usage_claude-delegate_2026-10-02.jsonl").write_text(
        json.dumps({"ts": "2026-10-02T16:50:00Z", "outcome": "rate_limited"}) + "\n", encoding="utf-8"
    )
    assert REAL_RATE_LIMIT_READER("codex", 3600.0, now=NOW) == {
        "count": 1,
        "last_rate_limited_at": "2026-10-02T16:30:00Z",
        "unreadable": {"files": 0, "lines": 0, "records": 0, "total": 0},
    }
    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", REAL_RATE_LIMIT_READER)
    state = credit_lane.lane_credit_state("codex", _codex(), POLICY, now=NOW)
    assert state["state"] == credit_lane.CREDIT_USE_UNCONFIRMED
    assert state["evidence"]["rate_limited_count"] == 1


# --- unreadable rate-limit evidence fails closed (real reader, nothing stubbed) --------


def _real_reader_state(monkeypatch, tmp_path, files: dict[str, bytes | None]) -> dict:
    """Credit state of the fresh near-cap Codex record with the real usage reader over ``files``."""
    from scripts.agent_runtime import usage

    usage._reset_rate_limit_cache_for_tests()
    monkeypatch.setattr(usage, "_usage_dir", lambda: tmp_path)
    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", REAL_RATE_LIMIT_READER)
    for name, content in files.items():
        if content is not None:
            (tmp_path / name).write_bytes(content)
    return credit_lane.lane_credit_state("codex", _codex(), POLICY, now=NOW)


def _line(**record) -> bytes:
    return (json.dumps({"outcome": "rate_limited", "model": "gpt-6.1-sol", **record}) + "\n").encode()


_LANE_FILE = "usage_codex-delegate_2026-10-02.jsonl"
_PRESENT = credit_lane.CREDIT_BALANCE_PRESENT
_UNVERIFIED = credit_lane.CREDITS_UNVERIFIED
_UNCONFIRMED = credit_lane.CREDIT_USE_UNCONFIRMED
_EDGE = NOW - timedelta(seconds=POLICY.rate_limit_window_s)

UNREADABLE_EVIDENCE = {
    "record-without-timestamp": (_line(), _UNVERIFIED, {"records": 1}),
    "record-with-null-timestamp": (_line(ts=None), _UNVERIFIED, {"records": 1}),
    "record-with-naive-timestamp": (_line(ts="2026-10-02T16:30:00"), _UNVERIFIED, {"records": 1}),
    "record-with-malformed-timestamp": (_line(ts="yesterday"), _UNVERIFIED, {"records": 1}),
    "record-with-epoch-timestamp": (_line(ts=1790958600), _UNVERIFIED, {"records": 1}),
    "record-with-non-utc-offset": (_line(ts="2026-10-02T18:30:00+02:00"), _UNVERIFIED, {"records": 1}),
    "record-with-utc-offset": (_line(ts="2026-10-02T16:30:00+00:00"), _UNCONFIRMED, None),
    "record-with-z": (_line(ts="2026-10-02T16:30:00Z"), _UNCONFIRMED, None),
    "truncated-line": (b'{"ts": "2026-10-02T16:30:00Z", "outcome": "rate_li', _UNVERIFIED, {"lines": 1}),
    "non-object-line": (b"[1, 2, 3]\n", _UNVERIFIED, {"lines": 1}),
    "binary-garbage": (bytes(b for b in range(256) if b != 10) * 4, _UNVERIFIED, {"lines": 1}),
    "empty-file": (b"", _PRESENT, None),
    "blank-lines-only": (b"\n\n", _PRESENT, None),
    "readable-ok-record": (_line(ts="2026-10-02T16:30:00Z", outcome="ok"), _PRESENT, None),
    "stale-utc-rate-limit": (_line(ts="2026-10-02T15:30:00Z"), _PRESENT, None),
    "exactly-at-window-edge": (_line(ts=_EDGE.isoformat()), _UNCONFIRMED, None),
    "one-millisecond-older": (_line(ts=(_EDGE - timedelta(milliseconds=1)).isoformat()), _PRESENT, None),
}


@pytest.mark.parametrize("scenario", list(UNREADABLE_EVIDENCE))
def test_real_reader_evidence_states(monkeypatch, tmp_path, scenario):
    content, expected, unreadable = UNREADABLE_EVIDENCE[scenario]
    state = _real_reader_state(monkeypatch, tmp_path, {_LANE_FILE: content})
    assert state["state"] == expected, (scenario, state["reason"])
    assert state["allowlist_applies"] is True
    assert state["evidence"].get("unreadable_records") == unreadable
    if expected == _UNVERIFIED:
        assert state["reason"].startswith("runtime usage records unreadable (")
        assert "rate limits cannot be ruled out" in state["reason"]
        assert state["evidence"]["rate_limited_count"] is None


def test_missing_file_and_missing_directory_are_the_empty_case(monkeypatch, tmp_path):
    assert _real_reader_state(monkeypatch, tmp_path, {})["state"] == _PRESENT
    monkeypatch.setattr("scripts.agent_runtime.usage._usage_dir", lambda: tmp_path / "absent")
    assert credit_lane.lane_credit_state("codex", _codex(), POLICY, now=NOW)["state"] == _PRESENT


def test_another_lanes_garbage_file_is_ignored(monkeypatch, tmp_path):
    files = {
        "usage_claude-delegate_2026-10-02.jsonl": b"\xff\xfe garbage {{{ rate_limited",
        "usage_cursor-delegate_2026-10-02.jsonl": b'{"outcome": "rate_limited"}\n',
    }
    state = _real_reader_state(monkeypatch, tmp_path, files)
    assert state["state"] == _PRESENT
    assert "unreadable_records" not in state["evidence"]


def test_unlistable_lane_file_is_unreadable_evidence(monkeypatch, tmp_path):
    # A symlink loop makes stat() fail with ELOOP (an OSError that is not "missing"); it works as root too.
    (tmp_path / _LANE_FILE).symlink_to(tmp_path / _LANE_FILE)
    state = _real_reader_state(monkeypatch, tmp_path, {})
    assert state["state"] == _UNVERIFIED
    assert state["evidence"]["unreadable_records"] == {"files": 1}


def test_dangling_symlink_named_like_a_lane_file_is_unreadable_evidence(monkeypatch, tmp_path):
    # The glob lists the link, stat() follows it and raises FileNotFoundError: the evidence is gone, not removed.
    (tmp_path / _LANE_FILE).symlink_to(tmp_path / "missing-target.jsonl")
    state = _real_reader_state(monkeypatch, tmp_path, {})
    assert state["state"] == _UNVERIFIED
    assert state["evidence"]["unreadable_records"] == {"files": 1}


def test_symlink_to_a_readable_file_without_rate_limits_is_readable(monkeypatch, tmp_path):
    (tmp_path / "target.jsonl").write_bytes(_line(ts="2026-10-02T16:30:00Z", outcome="ok"))
    (tmp_path / _LANE_FILE).symlink_to(tmp_path / "target.jsonl")
    state = _real_reader_state(monkeypatch, tmp_path, {})
    assert state["state"] == _PRESENT
    assert "unreadable_records" not in state["evidence"]


def test_symlink_to_a_file_with_a_utc_rate_limit_is_counted(monkeypatch, tmp_path):
    (tmp_path / "target.jsonl").write_bytes(_line(ts="2026-10-02T16:30:00Z"))
    (tmp_path / _LANE_FILE).symlink_to(tmp_path / "target.jsonl")
    state = _real_reader_state(monkeypatch, tmp_path, {})
    assert state["state"] == _UNCONFIRMED
    assert "unreadable_records" not in state["evidence"]


def test_regular_file_removed_between_listing_and_open_is_ignored(monkeypatch, tmp_path):
    from scripts.agent_runtime import usage

    path = tmp_path / _LANE_FILE
    path.write_bytes(_line())  # would be unreadable evidence if it were still read

    def vanishing_open(file, *args, **kwargs):
        Path(file).unlink()
        raise FileNotFoundError(2, "No such file or directory", str(file))

    monkeypatch.setattr(usage, "open", vanishing_open, raising=False)
    state = _real_reader_state(monkeypatch, tmp_path, {})
    assert not path.exists()
    assert state["state"] == _PRESENT
    assert "unreadable_records" not in state["evidence"]


def test_dangling_symlink_of_another_lane_is_ignored(monkeypatch, tmp_path):
    (tmp_path / "usage_claude-delegate_2026-10-02.jsonl").symlink_to(tmp_path / "missing-target.jsonl")
    state = _real_reader_state(monkeypatch, tmp_path, {})
    assert state["state"] == _PRESENT
    assert "unreadable_records" not in state["evidence"]


def test_directory_in_place_of_a_lane_file_is_unreadable_evidence(monkeypatch, tmp_path):
    (tmp_path / _LANE_FILE).mkdir()
    assert _real_reader_state(monkeypatch, tmp_path, {})["state"] == _UNVERIFIED


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads mode-000 files")
def test_mode_000_lane_file_is_unreadable_evidence(monkeypatch, tmp_path):
    path = tmp_path / _LANE_FILE
    path.write_bytes(_line(ts="2026-10-02T16:30:00Z"))
    path.chmod(0)
    try:
        state = _real_reader_state(monkeypatch, tmp_path, {})
    finally:
        path.chmod(0o600)
    assert state["state"] == _UNVERIFIED
    assert state["evidence"]["unreadable_records"] == {"files": 1}


def test_unreadable_evidence_keeps_the_allowlist_and_the_near_cap_router_row(monkeypatch, tmp_path):
    from scripts.agent_runtime import usage

    usage._reset_rate_limit_cache_for_tests()
    monkeypatch.setattr(usage, "_usage_dir", lambda: tmp_path)
    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", REAL_RATE_LIMIT_READER)
    (tmp_path / _LANE_FILE).write_bytes(_line())
    row = _row(_budget())
    assert row["credit"]["state"] == _UNVERIFIED
    assert row["status"] == "near_cap"
    assert credit_lane.allowlist_applies(row["credit"]) is True


def test_summary_unreadable_is_zero_for_other_callers_with_healthy_records(tmp_path):
    from scripts.agent_runtime import usage

    usage._reset_rate_limit_cache_for_tests()
    (tmp_path / _LANE_FILE).write_bytes(
        _line(ts="2026-10-02T16:30:00Z") + _line(ts="2026-10-02T16:31:00Z", outcome="ok")
    )
    summary = usage.summarize_lane_runtime("codex", window_s=3600, usage_dir=tmp_path, now=NOW.timestamp())
    assert summary["unreadable"] == {"files": 0, "lines": 0, "records": 0, "total": 0}
    assert (summary["rate_limited"], summary["ok"]) == (1, 1)


# --- UTC-only timestamps (parity with the reset reserve) ---------------------

_TIMES = {
    "z": ("2026-10-02T16:59:00Z", True),
    "utc-offset": ("2026-10-02T16:59:00+00:00", True),
    "naive": ("2026-10-02T16:59:00", False),
    "non-utc-offset": ("2026-10-02T18:59:00+02:00", False),
    "malformed": ("yesterday", False),
    "epoch": (int(datetime(2026, 10, 2, 16, 59, tzinfo=UTC).timestamp()), False),
}


def test_credit_lane_shares_the_reset_reserve_parser(monkeypatch):
    seen: list = []

    def parse(value):
        seen.append(value)
        return NOW

    monkeypatch.setattr(reset_reserve, "utc_datetime", parse)
    assert credit_lane.utc_datetime("anything") == NOW
    assert seen == ["anything"]


@pytest.mark.parametrize(("value", "accepted"), list(_TIMES.values()), ids=list(_TIMES))
def test_balance_fetch_time_must_be_explicit_utc(value, accepted):
    info = _codex()
    info["codexbar"]["fetched_at"] = value
    state = credit_lane.lane_credit_state("codex", info, POLICY, now=NOW)
    assert reset_reserve.utc_datetime(value) is not None if accepted else reset_reserve.utc_datetime(value) is None
    if accepted:
        assert state["state"] == credit_lane.CREDIT_BALANCE_PRESENT
    else:
        assert state["state"] == credit_lane.CREDITS_UNVERIFIED
        assert state["reason"].startswith("credit balance fetch time missing, not explicit UTC")
        assert state["credit_balance"] is None


@pytest.mark.parametrize(("value", "accepted"), list(_TIMES.values()), ids=list(_TIMES))
def test_reset_inventory_fetch_time_must_be_explicit_utc(value, accepted):
    info = _codex()
    info["reset_credits"]["fetched_at"] = value
    advice = _advice(info)
    if accepted:
        assert advice["free_resets_available"] == 2
    else:
        assert advice["free_resets_available"] is None
        assert advice["reason"] == "free-reset inventory missing or stale"


@pytest.mark.parametrize("value", ["2026-10-22T21:07:26", "2026-10-22T23:07:26+02:00", "soon"])
def test_reset_expiry_must_be_explicit_utc(value):
    info = _codex()
    info["reset_credits"]["expires_at"] = [value, "2026-10-29T19:15:04Z"]
    assert _advice(info)["free_resets_available"] is None


def test_balance_fetch_time_in_the_future_or_too_old_fails_closed():
    for value in ("2026-10-02T17:05:00Z", "2026-10-02T16:44:00Z"):
        info = _codex()
        info["codexbar"]["fetched_at"] = value
        assert credit_lane.lane_credit_state("codex", info, POLICY, now=NOW)["state"] == credit_lane.CREDITS_UNVERIFIED


def test_natural_reset_rejects_naive_text():
    info = _codex()
    info["codexbar"]["weekly_resets_at"] = "2026-10-03T17:00:00"
    assert _advice(info)["natural_reset_at"] is None


# --- router rows and output --------------------------------------------------


def test_credit_balance_codex_is_usable_and_labelled_without_claiming_a_draw():
    row = _row(_budget())
    assert row["avoid"] is False
    assert row["status"] == credit_lane.CREDIT_BALANCE_PRESENT
    assert row["remaining_pct"] == 1.0
    assert (
        "credit balance present (62500; draw not verified by the router; models gpt-6.1-sol, gpt-6-luna only)"
        in row["notes"]
    )
    assert row["credit"]["evidence"] == {
        "rate_limited_count": 0,
        "rate_limit_window_s": 3600.0,
        "last_rate_limited_at": None,
        "credit_balance": 62500.0,
        "credit_fetched_at": "2026-10-02T16:59:00Z",
    }
    assert row["credit"]["state"] == credit_lane.CREDIT_BALANCE_PRESENT
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


def test_credit_balance_lane_ranks_after_plan_backed_seats_and_counts_as_usable():
    budget = _budget(cursor={"status": "cool", "remaining_pct": 90.0}, kimi={"status": "hot", "remaining_pct": 40.0})
    report = capacity_pick.build_report(budget, reset_reserve=unavailable_reserve(), now=NOW)
    order = [entry["lane"] for entry in report["pick_order"] if entry["pick"] != "AVOID"]
    assert order.index("cursor") < order.index("codex")
    assert "codex" in report["cooler_lanes"]
    assert report["recommendation"]["primary_agent_for_code"] == "codex"
    assert any(
        "is past its plan cap with a credit balance present; draw not verified by the router: "
        "dispatch only gpt-6.1-sol, gpt-6-luna" in w
        for w in report["recommendation"]["warnings"]
    )


def test_human_output_states_credit_and_reset_advice():
    report = capacity_pick.build_report(_budget(), reset_reserve=unavailable_reserve(), now=NOW)
    human = capacity_pick.format_human(report)
    assert (
        "credit lane codex: credit_balance_present (plan remaining 1% at or below 10%; fresh credit balance "
        "62500; no rate limit in the last 3600s; draw not verified by the router) | evidence: rate limits 0 in "
        "last 3600s; balance 62500.0 fetched 2026-10-02T16:59:00Z | "
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
    assert "only while a fresh credit balance exists past the plan cap" in human


def test_human_output_states_the_gate_for_a_recent_rate_limit(monkeypatch):
    monkeypatch.setattr(
        credit_lane, "read_recent_rate_limits", lambda *_a, **_k: {"count": 1, "last_rate_limited_at": None}
    )
    report = capacity_pick.build_report(_budget(), reset_reserve=unavailable_reserve(), now=NOW)
    human = capacity_pick.format_human(report)
    assert "credit lane codex: credit_use_unconfirmed" in human
    assert "dispatch admits only gpt-6.1-sol, gpt-6-luna (fresh credit balance with the plan window exhausted)" in human


def test_main_json_carries_credit_fields(monkeypatch, capsys):
    from scripts.fleet import usage

    budget = _budget()
    budget["agents"]["codex"]["reset_credits"]["fetched_at"] = datetime.now(UTC).isoformat()
    _live(budget["agents"]["codex"])
    budget["agents"]["codex"]["codexbar"]["weekly_resets_at"] = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    monkeypatch.setattr(usage, "read_budget", lambda **_kwargs: budget)
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: {})
    monkeypatch.setattr(capacity_pick, "load_reset_reserve", lambda *_args, **_kwargs: unavailable_reserve())
    monkeypatch.setattr(capacity_pick, "admission_status", lambda: None)
    assert capacity_pick.main(["--json", "--strict"]) == 0
    payload = json.loads(capsys.readouterr().out)
    rows = {row["lane"]: row for row in payload["rows"]}
    credit = rows["codex"]["credit"]
    assert credit["state"] == "credit_balance_present" and credit["credit_balance"] == 62500.0
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


def test_recent_rate_limit_keeps_codex_near_cap_avoid(monkeypatch):
    _rate_limits(monkeypatch, 2)
    report = capacity_pick.build_report(_budget(), reset_reserve=unavailable_reserve(), now=NOW)
    row = next(r for r in report["rows"] if r["lane"] == "codex")
    assert (row["status"], row["avoid"]) == ("near_cap", True)
    assert (
        "credit_use_unconfirmed: recent rate limit while the plan window is exhausted: credit use not confirmed"
        in row["notes"]
    )
    assert row["credit"]["evidence"]["rate_limited_count"] == 2
    assert "codex" not in report["cooler_lanes"]
    human = capacity_pick.format_human(report)
    assert "evidence: rate limits 2 in last 3600s; balance 62500.0 fetched 2026-10-02T16:59:00Z" in human


def test_snapshot_rate_limits_without_headroom_block_keep_codex_avoid():
    info = _codex(runtime={"window_s": 300, "rate_limited": 4, "headroom_blocked": False})
    row = _row(_budget(info))
    assert (row["status"], row["avoid"], row["credit"]["state"]) == ("near_cap", True, "credit_use_unconfirmed")


# --- a bad policy file -------------------------------------------------------


@pytest.fixture(params=["missing-file", *BAD_POLICIES])
def bad_policy(request, monkeypatch, tmp_path):
    path = tmp_path / "credit_lanes.yaml"
    if request.param != "missing-file":
        path.write_text(BAD_POLICIES[request.param], encoding="utf-8")
    monkeypatch.setattr(credit_lane, "POLICY_PATH", path)
    return path


def _all_lanes_budget() -> dict:
    return _budget(
        claude={"status": "cool", "remaining_pct": 60.0},
        cursor={"status": "cool", "remaining_pct": 90.0},
        kimi={"status": "warm", "remaining_pct": 40.0},
        agy={"status": "cool", "remaining_pct": 80.0},
    )


def test_bad_policy_keeps_other_router_rows_and_codex_plan_state(bad_policy):
    good = {
        row["lane"]: row
        for row in capacity_pick.build_lane_rows(
            _all_lanes_budget(), reset_reserve=unavailable_reserve(), now=NOW, credit_policy=POLICY
        )
    }
    report = capacity_pick.build_report(_all_lanes_budget(), reset_reserve=unavailable_reserve(), now=NOW)
    rows = {row["lane"]: row for row in report["rows"]}
    assert set(rows) == set(capacity_pick.CODE_LANES)
    for lane in capacity_pick.CODE_LANES:
        if lane != "codex":
            assert rows[lane] == good[lane], lane
    codex = rows["codex"]
    assert (codex["status"], codex["avoid"]) == ("near_cap", True)
    assert codex["credit"]["state"] == credit_lane.POLICY_ERROR
    assert codex["credit"]["allowed_models"] == ["gpt-6.1-sol", "gpt-6-luna"]
    assert "policy_error: credit-lane policy unreadable" in codex["notes"]
    warning = next(w for w in report["recommendation"]["warnings"] if "credit-lane policy unreadable" in w)
    assert str(bad_policy) in warning
    assert "codex keeps its plan state and dispatch admits only gpt-6.1-sol, gpt-6-luna" in warning
    assert warning.endswith("other lanes unaffected")
    human = capacity_pick.format_human(report)
    assert "credit lane codex: policy_error (credit-lane policy unreadable" in human
    assert "| dispatch admits only gpt-6.1-sol, gpt-6-luna" in human
    assert "cursor" in report["cooler_lanes"] and "codex" not in report["cooler_lanes"]


def test_bad_policy_admission_restricts_only_codex(bad_policy, snapshot, capsys):
    for lane, model in (
        ("claude", "claude-opus-5-5"),
        ("cursor", "gpt-6-astra"),
        ("agy", "gemini-3.8-flash-high"),
        ("kimi", None),
        ("codex", "gpt-6.1-sol"),
        ("codex", "gpt-6-luna"),
    ):
        assert delegate._credit_period_refusal(lane, model) is None, (lane, model)
    refusal = delegate._credit_period_refusal("codex", "gpt-6-astra")
    assert refusal is not None
    assert refusal.startswith("CREDIT_PERIOD_MODEL_REFUSED: lane codex is policy_error (credit-lane policy unreadable")
    assert "model gpt-6-astra is outside the built-in credit-period allowlist [gpt-6.1-sol, gpt-6-luna]" in refusal
    err = capsys.readouterr().err
    assert "credit-lane policy unreadable" in err and "only codex dispatches are restricted" in err
    assert snapshot["reads"] == 0


def test_bad_policy_dispatch_of_another_lane_is_admitted(bad_policy, dispatch_env, capsys):
    argv = ["dispatch", "--agent", "claude", "--task-id", "other-lane", "--prompt", "Map the parser flags."]
    argv += ["--model", "claude-sonnet-5-5", "--mode", "read-only", "--cwd", str(delegate._REPO_ROOT)]
    rc = delegate.cmd_dispatch(delegate.build_parser().parse_args(argv))
    err = capsys.readouterr().err
    assert rc == 0, err
    assert "CREDIT_PERIOD_MODEL_REFUSED" not in err
    assert len(dispatch_env.spawned) == 1


def test_bad_policy_dispatch_of_off_allowlist_codex_is_refused(bad_policy, dispatch_env, capsys, monkeypatch):
    monkeypatch.setattr(delegate, "_lane_default_model", lambda _agent: "gpt-5-codex")
    rc = _dispatch_codex(None, task_id="bad-policy-codex")
    err = capsys.readouterr().err
    assert rc == 2, err
    assert "CREDIT_PERIOD_MODEL_REFUSED: lane codex is policy_error" in err
    assert "model gpt-5-codex is outside the built-in credit-period allowlist" in err
    assert "[gpt-6.1-sol, gpt-6-luna]" in err
    assert dispatch_env.spawned == []


# --- unchanged lanes (denominator lock) --------------------------------------

_SCENARIOS = ("plan_healthy", "near_cap_with_credits", "near_cap_without_credits", "credits_stale")


def _scenario_info(scenario: str) -> dict:
    base = {
        "freshness": "fresh",
        "age_s": 10,
        "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "eligible": True,
        "health": {"healthy": True},
    }
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
    rows = {
        row["lane"]: row
        for row in capacity_pick.build_lane_rows(budget, active_in_flight={}, reset_reserve=unavailable_reserve())
    }
    assert set(rows) == set(capacity_pick.CODE_LANES)
    for lane in capacity_pick.CODE_LANES:
        if lane == "codex":
            continue
        row = dict(rows[lane])
        assert row.pop("credit") == {"state": "not_configured"}
        # #9740 additive row facts; the origin/main fields stay byte-identical.
        facts = row.pop("routing_facts")
        assert row.pop("capacity")["state"] == ("avoid" if row["avoid"] else "verified")
        assert row.pop("health") == facts["health"] == "healthy"
        assert row.pop("remaining_source") == facts["remaining_source"] == "remaining_pct"
        assert row == _origin_main_row(lane, scenario), lane
    codex = rows["codex"]
    expected = {
        "plan_healthy": (credit_lane.PLAN_HEALTHY, "cool", False),
        "near_cap_with_credits": (credit_lane.CREDIT_BALANCE_PRESENT, credit_lane.CREDIT_BALANCE_PRESENT, False),
        "near_cap_without_credits": (credit_lane.CREDITS_EXHAUSTED, "near_cap", True),
        "credits_stale": (credit_lane.CREDITS_UNVERIFIED, "near_cap", True),
    }[scenario]
    assert (codex["credit"]["state"], codex["status"], codex["avoid"]) == expected


# --- dispatch admission ------------------------------------------------------


def _live(info: dict) -> dict:
    """Stamp the probe fetch time with the real clock, for code paths that read ``now`` themselves."""
    info["codexbar"]["fetched_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return info


def _credit_balance_snapshot() -> dict:
    return _budget(_live(_codex(reset_credits=None)))


@pytest.fixture
def snapshot(monkeypatch):
    """Serve ``credit_lane.read_routing_budget`` from a mutable box; count reads."""
    box = {"budget": _credit_balance_snapshot(), "reads": 0}

    def read(**_kwargs):
        box["reads"] += 1
        return box["budget"]

    monkeypatch.setattr(credit_lane, "read_routing_budget", read)
    return box


@pytest.mark.parametrize("model", ["gpt-6-astra", "gpt-5-codex", "claude-opus-5-5"])
def test_admission_refuses_off_allowlist_model_on_credit_balance_lane(snapshot, model):
    refusal = delegate._credit_period_refusal("codex", model)
    assert refusal is not None
    assert refusal.startswith("CREDIT_PERIOD_MODEL_REFUSED: lane codex is credit_balance_present")
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
        lambda box: box["budget"]["agents"]["codex"]["codexbar"].update(fetched_at="2026-10-02T17:00:00"),
    ],
    ids=[
        "plan-healthy",
        "credits-missing",
        "credits-stale",
        "snapshot-stale",
        "monitor-unreachable",
        "naive-fetch-time",
    ],
)
def test_admission_keeps_todays_behaviour_without_a_fresh_positive_balance(snapshot, mutate):
    mutate(snapshot)
    assert delegate._credit_period_refusal("codex", "gpt-6-astra") is None


# The admission gate is separate from the router recommendation: the allowlist
# holds whenever the plan window is exhausted AND a fresh positive balance exists,
# whatever the rate-limit evidence says (a recent rate limit only stops the router
# recommending the lane). Each scenario: (setup, router status, router credit state,
# allowlist applies).
def _no_rate_limit(monkeypatch):
    monkeypatch.setattr(
        credit_lane, "read_recent_rate_limits", lambda *_a, **_k: {"count": 0, "last_rate_limited_at": None}
    )


def _recent_rate_limit(monkeypatch):
    monkeypatch.setattr(
        credit_lane, "read_recent_rate_limits", lambda *_a, **_k: {"count": 2, "last_rate_limited_at": None}
    )


def _unreadable_usage(monkeypatch):
    def broken(*_a, **_k):
        raise OSError("usage records unreadable")

    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", broken)


def _codex_edit(**edits):
    def apply(box):
        box["budget"]["agents"]["codex"].update(edits)

    return apply


def _live_row(budget: dict) -> dict:
    """Codex router row on the real clock (the snapshot fixture stamps its probe time live)."""
    rows = capacity_pick.build_lane_rows(budget, reset_reserve=unavailable_reserve())
    return next(row for row in rows if row["lane"] == "codex")


def _policy_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(credit_lane, "POLICY_PATH", tmp_path / "absent.yaml")


GATE_SCENARIOS = {
    "plan-healthy": (
        _codex_edit(
            status="cool", remaining_pct=60.0, codexbar={**_live(_codex())["codexbar"], "weekly_remaining_pct": 60.0}
        ),
        _no_rate_limit,
        ("cool", credit_lane.PLAN_HEALTHY, False),
    ),
    "exhausted-fresh-balance": (None, _no_rate_limit, (credit_lane.CREDIT_BALANCE_PRESENT,) * 2 + (True,)),
    "exhausted-fresh-balance-recent-rate-limit": (
        None,
        _recent_rate_limit,
        ("near_cap", credit_lane.CREDIT_USE_UNCONFIRMED, True),
    ),
    "exhausted-fresh-balance-unreadable-usage": (
        None,
        _unreadable_usage,
        ("near_cap", credit_lane.CREDITS_UNVERIFIED, True),
    ),
    "exhausted-no-balance": (
        _codex_edit(credit_balance=None),
        _no_rate_limit,
        ("near_cap", credit_lane.CREDITS_UNVERIFIED, False),
    ),
    "exhausted-stale-balance": (
        _codex_edit(age_s=5000.0),
        _no_rate_limit,
        ("near_cap", credit_lane.CREDITS_UNVERIFIED, False),
    ),
    "exhausted-stale-balance-recent-rate-limit": (
        _codex_edit(age_s=5000.0),
        _recent_rate_limit,
        ("near_cap", credit_lane.CREDITS_UNVERIFIED, False),
    ),
    "exhausted-balance-zero": (
        _codex_edit(credit_balance=0.0),
        _no_rate_limit,
        ("near_cap", credit_lane.CREDITS_EXHAUSTED, False),
    ),
    "policy-error": ("policy", _no_rate_limit, ("near_cap", credit_lane.POLICY_ERROR, True)),
}
_ALLOWLISTED = "gpt-6.1-sol"
_OFF_ALLOWLIST = "gpt-5-codex"


@pytest.mark.parametrize("scenario", list(GATE_SCENARIOS))
@pytest.mark.parametrize("lane", ["codex", "cursor"])
@pytest.mark.parametrize(
    "model", [_ALLOWLISTED, _OFF_ALLOWLIST, None], ids=["allowlisted", "off-allowlist", "no-model"]
)
def test_allowlist_gate_table(snapshot, monkeypatch, tmp_path, scenario, lane, model):
    edit, reader, (status, state, gated) = GATE_SCENARIOS[scenario]
    reader(monkeypatch)
    if edit == "policy":
        _policy_missing(monkeypatch, tmp_path)
    elif edit is not None:
        edit(snapshot)
    refusal = credit_lane.dispatch_refusal(lane, model)
    # A model-less call is judged as no allowlisted model; the real caller resolves the lane default first.
    expect_refusal = lane == "codex" and gated and model != _ALLOWLISTED
    assert (refusal is not None) == expect_refusal, (scenario, lane, model, refusal)
    if expect_refusal:
        assert refusal.startswith(f"CREDIT_PERIOD_MODEL_REFUSED: lane codex is {state}")
    if lane == "codex" and model == _OFF_ALLOWLIST:
        # The router recommendation state is what round 2 specified, independent of the gate.
        row = _live_row(snapshot["budget"])
        assert (row["status"], row["credit"]["state"]) == (status, state), scenario
        assert credit_lane.allowlist_applies(row["credit"]) is gated, scenario


def test_dispatch_refusal_does_not_depend_on_the_router_recommending_the_lane(snapshot, monkeypatch):
    _recent_rate_limit(monkeypatch)
    row = _live_row(snapshot["budget"])
    assert row["avoid"] is True and row["credit"]["state"] == credit_lane.CREDIT_USE_UNCONFIRMED
    refusal = delegate._credit_period_refusal("codex", "gpt-5-codex")
    assert refusal is not None and "lane codex is credit_use_unconfirmed" in refusal


def test_admission_ignores_unconfigured_lanes(snapshot):
    assert delegate._credit_period_refusal("claude", "claude-opus-5-5") is None
    assert delegate._credit_period_refusal("cursor", "gpt-6-astra") is None
    assert snapshot["reads"] == 0


def _guard_budget(codex: dict) -> dict:
    return {
        "agents": {"codex": codex, "cursor": {"status": "cool", "remaining_pct": 90.0}},
        "diagnostics": {"records_loaded": 5, "stale": False, "codexbar_data_available": True},
        "recommendation": {},
    }


def test_budget_guard_keeps_credit_balance_codex(monkeypatch, capsys):
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: _guard_budget(_live(_codex(age_s=10.0))))
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_args, **_kwargs: unavailable_reserve())
    chosen = delegate._resolve_agent_with_budget_guard("codex", fallbacks={"codex": "cursor"})
    assert chosen == "codex"
    assert "lane codex has a credit balance present; draw not verified by the router" in capsys.readouterr().err


def test_budget_guard_substitutes_codex_after_a_recent_rate_limit(monkeypatch):
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: _guard_budget(_live(_codex(age_s=10.0))))
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_args, **_kwargs: unavailable_reserve())
    monkeypatch.setattr(
        credit_lane, "read_recent_rate_limits", lambda *_a, **_k: {"count": 1, "last_rate_limited_at": None}
    )
    assert delegate._resolve_agent_with_budget_guard("codex", fallbacks={"codex": "cursor"}) == "cursor"


def test_budget_guard_keeps_todays_guard_on_unreadable_policy(monkeypatch, tmp_path):
    monkeypatch.setattr(credit_lane, "POLICY_PATH", tmp_path / "absent.yaml")
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: _guard_budget(_live(_codex(age_s=10.0))))
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_args, **_kwargs: unavailable_reserve())
    assert delegate._resolve_agent_with_budget_guard("codex", fallbacks={"codex": "cursor"}) == "cursor"


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
    assert "CREDIT_PERIOD_MODEL_REFUSED: lane codex is credit_balance_present" in err
    assert "model gpt-5-codex is outside the credit-period allowlist" in err
    assert dispatch_env.spawned == []
    assert not (dispatch_env.tasks / "credit-worker.json").exists()


@pytest.mark.parametrize("model", ["gpt-6.1-sol", None])
def test_dispatch_admits_allowlisted_and_default_model_on_credit_balance_lane(dispatch_env, capsys, model):
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


# --- #9517: explicit usage directory and published-state re-check -----------


def test_explicit_usage_dir_is_read_instead_of_the_shared_one(monkeypatch, tmp_path):
    from scripts.agent_runtime import usage

    usage._reset_rate_limit_cache_for_tests()
    shared = tmp_path / "shared"
    explicit = tmp_path / "explicit"
    shared.mkdir()
    explicit.mkdir()
    monkeypatch.setattr(usage, "_usage_dir", lambda: shared)
    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", REAL_RATE_LIMIT_READER)
    (explicit / "usage_codex-delegate_2026-10-02.jsonl").write_text(
        json.dumps({"ts": "2026-10-02T16:40:00Z", "outcome": "rate_limited"}) + "\n", encoding="utf-8"
    )
    assert credit_lane.lane_credit_state("codex", _codex(), POLICY, now=NOW)["state"] == _PRESENT
    state = credit_lane.lane_credit_state("codex", _codex(), POLICY, now=NOW, usage_dir=explicit)
    assert state["state"] == credit_lane.CREDIT_USE_UNCONFIRMED


def _published(**overrides) -> dict:
    return {**credit_lane.lane_credit_state("codex", _codex(), POLICY, now=NOW), **overrides}


def test_published_credit_relief_receipt_for_a_fresh_present_state():
    receipt = credit_lane.published_credit_relief("codex", _published(), "gpt-6.1-sol", policy=POLICY, now=NOW)
    assert receipt["state"] == _PRESENT
    assert receipt["model_allowed"] is True
    assert receipt["allowed_models"] == ["gpt-6.1-sol", "gpt-6-luna"]
    assert receipt["draw"] == credit_lane.DRAW_NOT_VERIFIED
    assert receipt["evidence"]["credit_fetched_at"] == "2026-10-02T16:59:00Z"
    off = credit_lane.published_credit_relief("codex", _published(), "gpt-5.5", policy=POLICY, now=NOW)
    assert off["model_allowed"] is False


@pytest.mark.parametrize(
    "published",
    [
        None,
        "credit_balance_present",
        {"state": credit_lane.CREDIT_USE_UNCONFIRMED},
        {"state": credit_lane.CREDITS_UNVERIFIED},
        {"state": credit_lane.CREDITS_EXHAUSTED},
        {"state": credit_lane.POLICY_ERROR},
        {"state": credit_lane.PLAN_UNKNOWN},
        {"state": credit_lane.PLAN_HEALTHY},
        {"state": credit_lane.NOT_CONFIGURED},
    ],
)
def test_published_credit_relief_is_none_unless_present(published):
    assert credit_lane.published_credit_relief("codex", published, "gpt-6.1-sol", policy=POLICY, now=NOW) is None


def test_published_credit_relief_is_none_for_an_unconfigured_lane_or_unreadable_policy(monkeypatch):
    assert credit_lane.published_credit_relief("claude", _published(), "gpt-6.1-sol", policy=POLICY, now=NOW) is None

    def broken(path=None):
        raise ValueError("unreadable")

    monkeypatch.setattr(credit_lane, "load_policy", broken)
    assert credit_lane.published_credit_relief("codex", _published(), "gpt-6.1-sol", now=NOW) is None


@pytest.mark.parametrize(
    "fetched_at",
    [None, "2026-10-02T16:59:00", "2026-10-02T15:00:00Z", "2026-10-02T17:30:00Z"],
    ids=["missing", "naive", "too-old", "future"],
)
def test_published_credit_relief_rechecks_freshness_now(fetched_at):
    published = _published()
    published["evidence"] = {**published["evidence"], "credit_fetched_at": fetched_at}
    receipt = credit_lane.published_credit_relief("codex", published, "gpt-6.1-sol", policy=POLICY, now=NOW)
    assert receipt["state"] == credit_lane.CREDITS_UNVERIFIED
    assert receipt["reason"].startswith("published credit balance fetch time") and "900s" in receipt["reason"]


def test_published_credit_relief_rechecks_current_rate_limits_in_the_shared_log(monkeypatch, tmp_path):
    """A snapshot published before a rate limit no longer grants relief (real reader, shared log)."""
    from scripts.agent_runtime import usage

    published = _published()  # conftest reader: no rate limits when the snapshot was published
    assert published["state"] == _PRESENT
    usage._reset_rate_limit_cache_for_tests()
    monkeypatch.setattr(usage, "_usage_dir", lambda: tmp_path)
    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", REAL_RATE_LIMIT_READER)
    (tmp_path / "usage_codex-delegate_2026-10-02.jsonl").write_text(
        json.dumps({"ts": "2026-10-02T16:55:00Z", "outcome": "rate_limited"}) + "\n", encoding="utf-8"
    )
    canonical = credit_lane.lane_credit_state("codex", _codex(), POLICY, now=NOW)
    receipt = credit_lane.published_credit_relief("codex", published, "gpt-6.1-sol", policy=POLICY, now=NOW)
    assert canonical["state"] == receipt["state"] == credit_lane.CREDIT_USE_UNCONFIRMED
    assert receipt["reason"] == credit_lane.RATE_LIMIT_REASON
    assert receipt["evidence"]["rate_limited_count"] == 1
    assert receipt["evidence"]["last_rate_limited_at"] == "2026-10-02T16:55:00Z"


def test_published_credit_relief_records_the_current_rate_limit_check():
    receipt = credit_lane.published_credit_relief("codex", _published(), "gpt-6.1-sol", policy=POLICY, now=NOW)
    assert receipt["state"] == _PRESENT
    assert receipt["evidence"]["rate_limited_count"] == 0
    assert receipt["evidence"]["rate_limits_checked_at"] == "2026-10-02T17:00:00Z"


def test_published_credit_relief_denies_relief_when_the_reader_fails(monkeypatch):
    def broken(*_args, **_kwargs):
        raise OSError("usage dir unreadable")

    published = _published()
    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", broken)
    receipt = credit_lane.published_credit_relief("codex", published, "gpt-6.1-sol", policy=POLICY, now=NOW)
    assert receipt["state"] == credit_lane.CREDITS_UNVERIFIED
    assert receipt["reason"].startswith("runtime usage records unreadable now")
    assert receipt["evidence"]["rate_limited_count"] is None


def test_published_credit_relief_denies_relief_for_unreadable_records(monkeypatch):
    published = _published()
    monkeypatch.setattr(
        credit_lane,
        "read_recent_rate_limits",
        lambda *_a, **_k: {
            "count": 0,
            "last_rate_limited_at": None,
            "unreadable": {"files": 1, "lines": 0, "records": 0, "total": 1},
        },
    )
    receipt = credit_lane.published_credit_relief("codex", published, "gpt-6.1-sol", policy=POLICY, now=NOW)
    assert receipt["state"] == credit_lane.CREDITS_UNVERIFIED
    assert receipt["evidence"]["unreadable_records"] == {"files": 1}


# --- #9740: one interpretation of routing facts --------------------------------


def _pace_hot(**pace) -> dict:
    """A fresh weekly-pace hot Codex record with a visible deficit above the cap and no reserves."""
    return _codex(
        status="hot",
        status_source="weekly_pace",
        remaining_pct=60.0,
        credit_balance=0.0,
        reset_credits=None,
        codexbar={
            **_codex()["codexbar"],
            "weekly_used_pct": 40.0,
            "weekly_remaining_pct": 60.0,
            "weekly_expected_pct": 25.0,
            "weekly_pace_delta_pct": 15.0,
            "will_last_to_reset": False,
            **pace,
        },
    )


def _pace_hot_with_credits() -> dict:
    return {**_pace_hot(), "credit_balance": 62500.0}


def _facts(info: dict, *, model: str | None = None, stale: bool | None = False) -> credit_lane.RoutingFacts:
    metadata = None if stale is None else {"stale": stale}
    return credit_lane.routing_facts("codex", info, model=model, snapshot_metadata=metadata, policy=POLICY, now=NOW)


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        (
            {
                "remaining_pct": 40,
                "codexbar": {"weekly_remaining_pct": 40, "primary_remaining_pct": 3, "secondary_remaining_pct": 80},
            },
            (3.0, "codexbar.primary_remaining_pct"),
        ),
        ({"remaining_pct": True, "codexbar": {"weekly_remaining_pct": 50}}, (50.0, "codexbar.weekly_remaining_pct")),
        ({"burn_pct_7d": 95.0, "headroom_pct": 5.0}, (None, None)),
        ({"remaining_pct": float("nan")}, (None, None)),
        ({"provider_windows": {"auto": {"remaining_pct": 61.0}}}, (61.0, "provider_windows.auto.remaining_pct")),
        (
            {"codexbar": {"provider_windows": {"auto": {"remaining_pct": 7.0}, "api": {"remaining_pct": 1.0}}}},
            (7.0, "provider_windows.auto.remaining_pct"),
        ),
    ],
    ids=["tightest-window", "boolean-rejected", "burn-only-unknown", "non-finite", "cursor-auto", "api-pool-separate"],
)
def test_plan_remaining_reading_is_the_one_remaining_interpretation(record, expected):
    """F1: the owner's tightest window, the Cursor Auto allowance, and nothing from booleans or burn."""
    assert credit_lane.plan_remaining_reading(record) == expected
    assert capacity_pick.remaining_pct(record) == expected[0]


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        ({"freshness": "fresh", "age_s": 10.0}, credit_lane.FRESH),
        ({"freshness": "fresh", "age_s": 900.0}, credit_lane.STALE),
        ({"freshness": "stale_last_good", "age_s": 10.0}, credit_lane.STALE),
        ({"freshness": "fresh", "age_s": 10.0, "codexbar": {"stale": True}}, credit_lane.STALE),
        ({"freshness": "fresh"}, credit_lane.UNKNOWN),
        ({"freshness": "unavailable", "age_s": 1.0}, credit_lane.UNKNOWN),
        ({}, credit_lane.UNKNOWN),
    ],
)
def test_probe_freshness_never_reads_missing_as_fresh(record, expected):
    """F5/A6: only an explicit fresh label with an in-window age is fresh."""
    assert credit_lane.probe_freshness(record, POLICY.credit_max_age_s)[0] == expected


@pytest.mark.parametrize(
    ("metadata", "expected"),
    [
        ({"stale": True}, credit_lane.STALE),
        ({"stale": False}, credit_lane.FRESH),
        ({}, credit_lane.UNKNOWN),
        (None, credit_lane.UNKNOWN),
    ],
)
def test_snapshot_freshness_missing_is_unknown(metadata, expected):
    assert credit_lane.snapshot_freshness(metadata)[0] == expected


@pytest.mark.parametrize(
    ("health", "expected"),
    [
        ({"healthy": True, "basis": "scan_observed_idle"}, credit_lane.HEALTHY),
        ({"healthy": False, "last_error": "boom"}, credit_lane.UNHEALTHY),
        ({"healthy": None, "basis": "scan_unavailable"}, credit_lane.UNKNOWN),
        (None, credit_lane.UNKNOWN),
    ],
)
def test_health_fact_missing_is_unknown(health, expected):
    """F4: health is established only by an explicit boolean."""
    assert credit_lane.health_fact({"health": health} if health is not None else {})[0] == expected


def test_stale_pace_deficit_is_unknown_stale_but_owner_pace_decision_is_unchanged():
    """F2/A2: the qualifier is typed; raw_deficit and uncovered stay the owner's values."""
    fresh = _facts(_pace_hot())
    stale = _facts(_pace_hot(), stale=True)
    assert (fresh.raw_deficit, fresh.uncovered, fresh.capacity) == (True, True, credit_lane.CAPACITY_AVOID)
    assert (stale.raw_deficit, stale.uncovered) == (True, True)
    assert stale.capacity == credit_lane.CAPACITY_UNKNOWN_STALE
    assert stale.capacity_reason.startswith(credit_lane.STALE_ADVISORY_LABEL)
    assert (
        credit_lane.pace_deficit_state("codex", _pace_hot(), policy=POLICY, now=NOW, snapshot_stale=True)["uncovered"]
        is True
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"status": "near_cap", "remaining_pct": 5.0},
        {"remaining_pct": 5.0},
        {"runtime": {"headroom_blocked": True, "rate_limited": 3}},
        {"health": {"healthy": False}},
        {"login_state": "NEED_LOGIN"},
        {"eligible": False},
        {"status_source": "ledger_burn"},
        {"status_source": None},
    ],
    ids=[
        "near-cap-status",
        "near-cap-window",
        "runtime-blocked-hot",
        "unhealthy",
        "need-login",
        "ineligible",
        "ledger-hot",
        "sourceless-hot",
    ],
)
def test_stale_snapshot_never_relaxes_current_avoid_reasons(overrides):
    """A2: near cap (also with stale credit evidence), runtime-blocked hot, unhealthy, NEED_LOGIN,
    ineligible and a hot label that is not weekly pace stay AVOID on a stale snapshot."""
    info = _pace_hot(**{})
    info.update(overrides)
    if "remaining_pct" in overrides:
        info["codexbar"] = {**info["codexbar"], "weekly_remaining_pct": overrides["remaining_pct"]}
        info["credit_balance"] = 62500.0
    assert _facts(info, stale=True).capacity == credit_lane.CAPACITY_AVOID


@pytest.mark.parametrize(("blocked", "status"), [(False, "warm"), (True, "hot")])
def test_hidden_pace_hot_takes_the_allowance_status_never_a_default_cool(blocked, status):
    """F3/A3: below the visibility floor a weekly-pace hot label takes the remaining-allowance
    status (45% remaining is warm), unless runtime blockage set the hot label."""
    info = _pace_hot(weekly_expected_pct=0.1)
    info.update(remaining_pct=45.0)
    info["codexbar"]["weekly_remaining_pct"] = 45.0
    if blocked:
        info["runtime"] = {"headroom_blocked": True, "rate_limited": 2}
    facts = _facts(info)
    assert facts.pace_visible is False and facts.raw_deficit is None
    assert facts.status == status
    assert facts.capacity == (credit_lane.CAPACITY_AVOID if blocked else credit_lane.CAPACITY_VERIFIED)


@pytest.mark.parametrize(
    ("overrides", "stale", "status", "capacity"),
    [
        ({}, False, "warm", credit_lane.CAPACITY_VERIFIED),
        ({"runtime": {"headroom_blocked": True, "rate_limited": 2}}, False, "hot", credit_lane.CAPACITY_AVOID),
        ({"status_source": "cursor_auto"}, False, "hot", credit_lane.CAPACITY_AVOID),
        ({"status_source": None}, False, "hot", credit_lane.CAPACITY_AVOID),
        ({}, True, "hot", credit_lane.CAPACITY_UNKNOWN_STALE),
        ({}, None, "hot", credit_lane.CAPACITY_AVOID),
    ],
    ids=["fresh-cleared", "runtime-blocked", "cursor-auto", "sourceless", "stale-snapshot", "staleness-unknown"],
)
def test_weekly_pace_hot_without_a_deficit_is_cleared_by_the_owner_only_when_fresh(overrides, stale, status, capacity):
    """#9040 (A8) in the owner: a visible on-pace reading clears a weekly-pace hot label on a fresh
    observation and takes the remaining-allowance status (45% remaining is warm). A runtime block,
    another source, or a stale or unknown observation keeps the label."""
    info = _pace_hot(weekly_pace_delta_pct=0.49)
    info.update(remaining_pct=45.0, **overrides)
    info["codexbar"]["weekly_remaining_pct"] = 45.0
    facts = _facts(info, stale=stale)
    assert facts.pace_visible is True and facts.raw_deficit is False
    assert facts.status == status
    assert facts.capacity == capacity, facts.capacity_reason
    if status != "hot":
        assert facts.pace_reason.startswith("no pace deficit on a fresh observation")


@pytest.mark.parametrize("missing", ["age_s", "freshness"], ids=["probe-age-missing", "probe-freshness-unknown"])
def test_weekly_pace_hot_label_needs_a_positively_fresh_probe(missing):
    """#9040 (A8): a fresh snapshot alone never clears the label; an incomplete probe keeps it hot."""
    info = _pace_hot(weekly_pace_delta_pct=0.49)
    info.update(remaining_pct=45.0)
    info["codexbar"]["weekly_remaining_pct"] = 45.0
    info.pop(missing)
    info["codexbar"].pop(missing)
    facts = _facts(info)
    assert (facts.snapshot_freshness, facts.probe_freshness) == (credit_lane.FRESH, credit_lane.UNKNOWN)
    # The observation helper still reads fresh (a probe-less lane's snapshot covers it); the clearance does not.
    assert facts.observation_freshness == credit_lane.FRESH
    assert facts.pace_visible is True and facts.raw_deficit is False
    assert facts.status == "hot"
    assert facts.capacity == credit_lane.CAPACITY_AVOID, facts.capacity_reason


def test_hidden_pace_with_unknown_allowance_is_unknown_not_cool():
    info = _pace_hot(weekly_expected_pct=0.1)
    for key in ("remaining_pct",):
        info.pop(key)
    info["codexbar"] = {k: v for k, v in info["codexbar"].items() if not k.endswith("remaining_pct")}
    facts = _facts(info)
    assert facts.status == credit_lane.UNKNOWN
    assert facts.capacity == credit_lane.CAPACITY_UNKNOWN


def test_conflicting_pace_aliases_have_one_meaning():
    """F3 key order: expected_pct, expectedUsedPercent, weekly_expected_pct, then the reset fallback."""
    from scripts.api.subscription_usage import PACE_EXPECTED_PCT_ALIASES, pace_expected_pct, pace_is_deficit

    pace = {
        "expectedUsedPercent": 0.1,
        "weekly_expected_pct": 40.0,
        "weekly_pace_delta_pct": 20.0,
        "will_last_to_reset": False,
    }
    assert PACE_EXPECTED_PCT_ALIASES == ("expected_pct", "expectedUsedPercent", "weekly_expected_pct")
    assert pace_expected_pct(pace) == 0.1
    assert pace_is_deficit(pace) is None
    facts = _facts(
        _codex(
            status="cool", remaining_pct=60.0, codexbar={**_codex()["codexbar"], **pace, "weekly_remaining_pct": 60.0}
        )
    )
    assert (facts.pace_visible, facts.raw_deficit) == (False, None)


def test_model_change_against_identical_credit_evidence():
    """F7: None is lane inventory (coverage for the listed models); a concrete route is model-specific."""
    info = _pace_hot_with_credits()
    inventory = _facts(info)
    allowed = _facts(info, model="gpt-6.1-sol")
    forbidden = _facts(info, model="gpt-5-codex")
    assert inventory.covered_by == allowed.covered_by == ("credits",)
    assert inventory.credit_models == ("gpt-6.1-sol", "gpt-6-luna")
    assert inventory.model_permission is None
    assert forbidden.covered_by == () and forbidden.uncovered is True
    assert forbidden.capacity == credit_lane.CAPACITY_AVOID
    # Above the cap the credit-period allowlist does not gate admission: permission is not refused.
    assert forbidden.model_permission is True and forbidden.refusal_reason is None


def test_off_allowlist_model_near_cap_with_credit_is_refused_not_relieved():
    """A4/F7: lane-level relief is not model permission; the refusal carries CREDIT_PERIOD_MODEL_REFUSED."""
    lane = _facts(_codex())
    off = _facts(_codex(), model="gpt-5-codex")
    assert lane.capacity == credit_lane.CAPACITY_VERIFIED and lane.credit_relief
    assert off.model_permission is False and not off.credit_relief
    assert off.capacity == credit_lane.CAPACITY_AVOID
    assert off.refusal_reason.startswith(credit_lane.REFUSAL_CODE)


def test_routing_facts_share_one_rate_limit_observation(monkeypatch):
    """Credit state and pace coverage read the runtime records once per call."""
    calls: list[str] = []

    def reader(lane, *_a, **_k):
        calls.append(lane)
        return {"count": 0, "last_rate_limited_at": None}

    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", reader)
    facts = _facts(_pace_hot_with_credits())
    assert facts.covered_by == ("credits",)
    assert calls == ["codex"]


def test_routing_facts_ignore_published_conclusions():
    """Published ``credit``/``pace_deficit`` leaves never substitute for their inputs."""
    info = _pace_hot()
    info["credit"] = {"state": credit_lane.CREDIT_BALANCE_PRESENT}
    info["pace_deficit"] = {"uncovered": False, "covered_by": ["credits"]}
    facts = _facts(info)
    assert facts.uncovered is True and facts.capacity == credit_lane.CAPACITY_AVOID


def test_routing_facts_unreadable_policy_is_policy_error(monkeypatch):
    def broken(*_a, **_k):
        raise ValueError("bad policy")

    monkeypatch.setattr(credit_lane, "load_policy", broken)
    facts = credit_lane.routing_facts(
        "codex", _codex(), model="gpt-5-codex", snapshot_metadata={"stale": False}, now=NOW
    )
    assert facts.credit["state"] == credit_lane.POLICY_ERROR
    assert facts.capacity == credit_lane.CAPACITY_AVOID
    assert facts.model_permission is False and facts.refusal_reason.startswith(credit_lane.REFUSAL_CODE)


@pytest.mark.parametrize(
    ("overrides", "stale"),
    [
        ({"freshness": "stale_last_good"}, False),
        ({"age_s": 5000.0}, False),
        ({"stale": True}, False),
        ({"freshness": None, "codexbar": {**_codex()["codexbar"], "freshness": None}}, False),
        ({}, True),
    ],
    ids=["probe-stale-label", "probe-over-age", "stale-flag", "freshness-missing", "snapshot-stale"],
)
def test_published_relief_rechecks_the_complete_record(overrides, stale):
    """F6: a published credit_balance_present leaf cannot override contradictory probe evidence."""
    record = _codex(**overrides)
    receipt = credit_lane.published_credit_relief(
        "codex", _published(), "gpt-6.1-sol", policy=POLICY, now=NOW, record=record, snapshot_stale=stale
    )
    assert receipt["state"] == credit_lane.CREDITS_UNVERIFIED
    assert receipt["reason"].startswith("published credit relief not re-verified")
    fresh = credit_lane.published_credit_relief(
        "codex", _published(), "gpt-6.1-sol", policy=POLICY, now=NOW, record=_codex()
    )
    assert fresh["state"] == _PRESENT


# Consumers whose decisions the owner makes. Each may call the owner, but must
# not hold its own reader of the raw fields the owner interprets (#9740).
_CONSUMER_MODULES = (
    "scripts/fleet/capacity_pick.py",
    "scripts/fleet/idle_settle.py",
    "scripts/review/reviewer_scheduler.py",
    "scripts/orchestration/curriculum_coordinator.py",
)
_OWNER_ONLY_FIELDS = frozenset(
    {
        "remaining_pct",
        "weekly_remaining_pct",
        "primary_remaining_pct",
        "secondary_remaining_pct",
        "headroom_pct",
        "expected_pct",
        "expectedUsedPercent",
        "weekly_expected_pct",
        "credit_fetched_at",
        "age_s",
        "quota_ok",
    }
)


_OWNER_OUTPUTS = frozenset({"row", "entry", "evidence", "credit", "advice", "published", "facts_row"})


@pytest.mark.parametrize("path", _CONSUMER_MODULES)
def test_consumers_do_not_rederive_owner_decisions(path):
    """Structural guard: no consumer reads the raw window, pace-alias, freshness-age or remaining
    fields that ``credit_lane`` interprets, and none parses ``healthy`` or ``stale`` with a default."""
    import ast

    source = (Path(__file__).resolve().parents[1] / path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    reads: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            # Rows, receipts and evidence are the owner's own output, not raw lane records.
            and not (isinstance(node.func.value, ast.Name) and node.func.value.id in _OWNER_OUTPUTS)
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            key = node.args[0].value
            if key in _OWNER_ONLY_FIELDS and not (path.endswith("idle_settle.py") and key == "quota_ok"):
                reads.append(f"{path}:{node.lineno}: .get({key!r})")
            if key == "healthy" and len(node.args) > 1:
                reads.append(f"{path}:{node.lineno}: .get('healthy', default)")
    assert reads == [], "consumer re-derives an owner decision:\n" + "\n".join(reads)
