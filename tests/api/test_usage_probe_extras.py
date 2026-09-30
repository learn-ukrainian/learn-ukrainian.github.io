"""Recorded native quota payloads through normalization, routing API and CLI."""

from __future__ import annotations

import copy
import io
import json
import subprocess
import urllib.error
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api import state_router
from scripts.api import subscription_usage as probes
from scripts.api.monitor_context import fixture_context
from scripts.fleet import capacity_pick, usage
from tests.api.test_routing_budget_endpoint import _configure

FIXTURES = Path(__file__).parents[1] / "fixtures" / "usage_9270"
NOW = datetime(2026, 9, 30, 8, 0, tzinfo=UTC)
SENTINEL = "SYNTHETIC_SECRET_SENTINEL"
IDENTIFIER = "SYNTHETIC_IDENTIFIER_SENTINEL"


@pytest.fixture
def payloads():
    return {
        name: json.loads((FIXTURES / f"{name}.json").read_text()) for name in ("codex", "codex_resets", "claude", "agy")
    }


def _probe(monkeypatch, payloads, lane, *, error=None):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW

    monkeypatch.setattr(probes, "datetime", Clock)
    monkeypatch.setattr(probes, "_load_codex_oauth_token", lambda: SENTINEL)
    monkeypatch.setattr(probes, "_load_claude_oauth_token", lambda: SENTINEL)
    monkeypatch.setattr(probes, "_agy_cli_bin", lambda: "fixture-agy")
    calls = []

    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if error:
            return error
        key = "codex_resets" if url.endswith("reset-credits") else lane
        return 200, payloads[key], None

    monkeypatch.setattr(probes, "_http_json_request", request)
    monkeypatch.setattr(
        probes.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a, 0, json.dumps(payloads["agy"]), "")
    )
    result = {
        "codex": probes._probe_codex_native,
        "claude": probes._probe_claude_native,
        "gemini": probes._probe_antigravity_native,
    }[lane](timeout_s=1)
    result.update(freshness="fresh", age_s=0, stale=False)
    return result, calls


def _api_cli(monkeypatch, tmp_path, capsys, lane, result):
    _configure(monkeypatch, tmp_path, [])
    monkeypatch.setattr(state_router, "get_provider_usage_data", lambda p: result if p == lane else None)
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(state_router.router, prefix="/api/state")
    response = TestClient(app).get("/api/state/routing-budget")
    assert response.status_code == 200
    budget = response.json()
    # Exercise the command entry point over the actual API response.
    monkeypatch.setattr(usage, "read_budget", lambda **kw: budget)
    assert usage.main(["show"]) == 0
    human = capsys.readouterr().out
    assert usage.main(["json"]) == 0
    assert json.loads(capsys.readouterr().out) == budget
    return budget, human


@pytest.mark.parametrize("lane", ["codex", "claude", "gemini"])
def test_recordings_reach_api_and_usage_show(monkeypatch, tmp_path, capsys, payloads, lane):
    # Unrecognized provider fields must never reach outward-facing data.
    for body in payloads.values():
        body["account_id"] = IDENTIFIER
        body["debug"] = SENTINEL
    for credit in payloads["codex_resets"]["credits"]:
        credit.update(id=IDENTIFIER, title=SENTINEL, description=SENTINEL)
    payloads["claude"]["limits"][0]["scope"]["model"]["id"] = IDENTIFIER
    result, calls = _probe(monkeypatch, payloads, lane)
    budget, human = _api_cli(monkeypatch, tmp_path, capsys, lane, result)
    info = budget["agents"][lane]
    assert SENTINEL not in json.dumps(budget) + human
    assert IDENTIFIER not in json.dumps(budget) + human
    if lane == "codex":
        assert info["credit_balance"] == 62500
        assert info["reset_credits"]["available_count"] == 2
        assert info["reset_credits"]["expires_at"] == [c["expires_at"] for c in payloads["codex_resets"]["credits"]]
        assert info["codexbar"]["reset_credits"] == info["reset_credits"]
        assert "balance=62500.0" in human and "free full resets: available=2" in human
        assert all(method == "GET" for method, _, _ in calls)
        assert calls[1][2]["headers"]["OpenAI-Beta"] == "codex-1"
        assert calls[1][2]["headers"]["originator"] == "Codex Desktop"
    elif lane == "claude":
        assert info["fable_weekly"]["used_pct"] == 42
        assert info["fable_weekly"]["window_minutes"] == 10080
        assert info["interactive"]["burn_pct_7d"] == 67
        assert info["agentic_pool"]["burn_pct_cycle"] is None
        assert "Fable only (weekly): used=42.0%" in human
        assert "agentic (monthly): status=unknown" in human
    else:
        assert info["claude_gpt_windows"]["five_hour"]["used_pct"] == 0
        assert info["claude_gpt_windows"]["weekly"]["used_pct"] == 0
        assert info["codexbar"]["weekly_used_pct"] == pytest.approx(0.15184879302978516)
        assert "Claude/GPT (5h): used=0.0%" in human
        assert "Claude/GPT (weekly): used=0.0%" in human


@pytest.mark.parametrize("case", ["zero", "missing", "expired", "failed_inventory"])
def test_codex_credit_edges(monkeypatch, tmp_path, capsys, payloads, case):
    if case == "zero":
        payloads["codex"]["credits"]["balance"] = "0"
        payloads["codex"]["rate_limit"]["primary_window"]["used_percent"] = 0
        payloads["codex_resets"] = {"available_count": 0, "credits": []}
    elif case == "missing":
        payloads["codex"].pop("credits")
        payloads["codex_resets"] = {}
    elif case == "expired":
        for credit in payloads["codex_resets"]["credits"]:
            credit["expires_at"] = "2026-09-29T00:00:00Z"
    result, _ = _probe(monkeypatch, payloads, "codex")
    if case == "failed_inventory":

        def request(method, url, **kwargs):
            if url.endswith("reset-credits"):
                return 500, {"error": SENTINEL}, IDENTIFIER
            return 200, payloads["codex"], None

        monkeypatch.setattr(probes, "_http_json_request", request)
        result = probes._probe_codex_native(timeout_s=1)
        result.update(freshness="fresh")
    budget, human = _api_cli(monkeypatch, tmp_path, capsys, "codex", result)
    info = budget["agents"]["codex"]
    if case in {"missing", "failed_inventory"}:
        assert info["reset_credits"] is None
        assert "free full resets: available=unknown" in human
    else:
        assert info["reset_credits"]["available_count"] == 0
        assert "free full resets: available=0" in human
    if case == "missing":
        assert info["credit_balance"] is None and "balance=unknown" in human
    if case == "zero":
        assert info["credit_balance"] == 0
        assert info["codexbar"]["weekly_used_pct"] == 0
    assert SENTINEL not in json.dumps(budget) + human
    assert IDENTIFIER not in json.dumps(budget) + human


@pytest.mark.parametrize("case", ["zero", "missing", "wrong_kind", "wrong_group"])
def test_fable_window_edges(monkeypatch, tmp_path, capsys, payloads, case):
    if case == "zero":
        payloads["claude"]["limits"][0]["percent"] = 0
    elif case == "missing":
        payloads["claude"].pop("limits")
    elif case == "wrong_kind":
        payloads["claude"]["limits"][0]["kind"] = "session"
    else:
        payloads["claude"]["limits"][0]["group"] = "monthly"
    result, _ = _probe(monkeypatch, payloads, "claude")
    budget, human = _api_cli(monkeypatch, tmp_path, capsys, "claude", result)
    assert budget["agents"]["claude"]["fable_weekly"]["used_pct"] == (0 if case == "zero" else None)
    assert f"Fable only (weekly): used={'0.0%' if case == 'zero' else 'unknown'}" in human


@pytest.mark.parametrize("case", ["group_missing", "5h_missing", "weekly_missing", "used"])
def test_agy_windows_independent(monkeypatch, tmp_path, capsys, payloads, case):
    groups = payloads["agy"]["command"]["data"]["groups"]
    if case == "group_missing":
        groups.pop()
    elif case.endswith("missing"):
        missing = "5h" if case == "5h_missing" else "weekly"
        groups[1]["buckets"] = [b for b in groups[1]["buckets"] if b["window"] != missing]
    else:
        groups[1]["buckets"][0]["remaining_fraction"] = 0.75
    result, _ = _probe(monkeypatch, payloads, "gemini")
    budget, human = _api_cli(monkeypatch, tmp_path, capsys, "gemini", result)
    windows = budget["agents"]["gemini"]["claude_gpt_windows"]
    assert windows["five_hour"]["used_pct"] == (None if case in {"group_missing", "5h_missing"} else 0)
    assert windows["weekly"]["used_pct"] == (
        None if case in {"group_missing", "weekly_missing"} else 25 if case == "used" else 0
    )
    assert "Claude/GPT" in human


@pytest.mark.parametrize("lane", ["codex", "claude"])
@pytest.mark.parametrize("status", [0, 429, 500])
def test_provider_error_forwarding_drops_secrets(monkeypatch, tmp_path, capsys, payloads, lane, status):
    result, _ = _probe(monkeypatch, payloads, lane, error=(status, {"error": SENTINEL}, IDENTIFIER + SENTINEL))
    budget, human = _api_cli(monkeypatch, tmp_path, capsys, lane, result)
    assert result["status"] == "unavailable"
    assert str(status) in result["auth_error"]
    assert SENTINEL not in json.dumps(budget) + human
    assert IDENTIFIER not in json.dumps(budget) + human


@pytest.mark.parametrize("exception", ["http", "network", "timeout", "json"])
def test_http_errors_do_not_return_provider_body_or_reason(monkeypatch, exception):
    def fail(*a, **kw):
        if exception == "http":
            raise urllib.error.HTTPError(
                "https://example.invalid", 500, IDENTIFIER, {}, io.BytesIO(json.dumps({"error": SENTINEL}).encode())
            )
        if exception == "network":
            raise urllib.error.URLError(SENTINEL + IDENTIFIER)
        if exception == "timeout":
            raise TimeoutError(SENTINEL)
        raise json.JSONDecodeError(SENTINEL, IDENTIFIER, 0)

    monkeypatch.setattr(probes.urllib.request, "urlopen", fail)
    status, body, error = probes._http_json_request("GET", "https://example.invalid")
    assert status == (500 if exception == "http" else 0)
    assert body is None
    assert SENTINEL not in error and IDENTIFIER not in error


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"available_count": True, "credits": []},
        {"available_count": 1, "credits": [None]},
        {"available_count": 1, "credits": [{"status": "available", "expires_at": SENTINEL}]},
    ],
)
def test_malformed_reset_inventory_unknown(payload):
    assert probes._codex_reset_inventory(payload, now=NOW) is None


def test_reset_inventory_filters_status_and_accepts_no_expiry():
    result = probes._codex_reset_inventory(
        {
            "available_count": 1,
            "credits": [{"status": "redeemed", "expires_at": None}, {"status": "available", "expires_at": None}],
        },
        now=NOW,
    )
    assert result["available_count"] == 1 and result["expires_at"] == [None]


@pytest.mark.parametrize(
    "freshness,expires",
    [("fresh", "2099-01-01T00:00:00Z"), ("fresh", "2000-01-01T00:00:00Z"), ("stale_last_good", "2099-01-01T00:00:00Z")],
)
def test_inventory_note_never_changes_reserve_or_admission(freshness, expires):
    info = {"status": "near_cap", "burn_pct_7d": 95, "freshness": freshness, "remaining_pct": 5, "eligible": False}
    reserve = {"remaining_resets": 0, "asserted_at": None}
    budget = {"agents": {"codex": info}, "reset_reserve": reserve}
    before = capacity_pick.build_lane_rows(budget, reset_reserve=reserve)
    frozen = copy.deepcopy(reserve)
    info["reset_credits"] = {"available_count": 2, "expires_at": [expires, expires]}
    after = capacity_pick.build_lane_rows(budget, reset_reserve=reserve)
    base = next(row for row in before if row["lane"] == "codex")
    row = next(row for row in after if row["lane"] == "codex")
    assert reserve == frozen
    assert {k: v for k, v in row.items() if k != "notes"} == {k: v for k, v in base.items() if k != "notes"}
    assert row["avoid"] is True
    has_note = "free full reset available" in row["notes"]
    assert has_note is (freshness == "fresh" and expires.startswith("2099"))


def test_recorded_codex_near_cap_reaches_note_without_relaxing(monkeypatch, tmp_path, capsys, payloads):
    payloads["codex"]["rate_limit"]["primary_window"]["used_percent"] = 95
    result, _ = _probe(monkeypatch, payloads, "codex")
    budget, _ = _api_cli(monkeypatch, tmp_path, capsys, "codex", result)
    reserve = {"remaining_resets": 0, "asserted_at": None}
    row = next(r for r in capacity_pick.build_lane_rows(budget, reset_reserve=reserve) if r["lane"] == "codex")
    assert "free full reset available (2; operator decision)" in row["notes"]
    assert row["avoid"] and not row["reset_reserve_eligible"]
    assert reserve == {"remaining_resets": 0, "asserted_at": None}


@pytest.mark.parametrize("raw", [SENTINEL, IDENTIFIER, None])
def test_window_helper_drops_invalid_reset_text(raw):
    assert probes._window_from_used_pct(0, window_minutes=300, resets_at=raw) == {
        "usedPercent": 0,
        "windowMinutes": 300,
        "resetsAt": None,
    }
