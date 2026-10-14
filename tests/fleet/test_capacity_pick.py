"""Diagnostic usage observations must not alter the capacity consumer's budget."""

import copy
import io
import json
import subprocess

import pytest

from scripts.api import state_router, subscription_usage
from scripts.fleet import capacity_pick, usage


@pytest.mark.parametrize("fresh", [True, False], ids=["fresh", "monitor"])
@pytest.mark.parametrize("agy_signal", [False, True], ids=["inherit-gemini", "own-hot-row"])
@pytest.mark.parametrize("diagnostic", ["hot", "zero", "full", "stale", "error", "cold"])
def test_hot_agy_remains_avoid_through_budget_and_capacity_cli(monkeypatch, capsys, fresh, agy_signal, diagnostic):
    quota = {
        "status": "hot",
        "remaining_pct": 3.0,
        "freshness": "fresh",
        "age_s": 0.0,
        "eligible": True,
        "health": {"healthy": True},
    }
    budget = {
        "agents": {"gemini": quota, "agy": copy.deepcopy(quota) if agy_signal else {"status": "unknown"}},
        "api_accounts": {},
        "recommendation": {"primary_agent_for_code": "agy", "warnings": []},
    }
    original = copy.deepcopy(budget)
    fraction = {"zero": 0, "full": 1}.get(diagnostic, 0.03)
    payload = {
        "command": {
            "data": {
                "groups": [
                    {"name": "Gemini PRIVATE_LABEL", "buckets": [{"window": "5h", "remaining_fraction": fraction}]}
                ]
            }
        },
        "account": "PRIVATE_ACCOUNT account@example.com",
        "credits": 987654,
    }
    if diagnostic == "error":
        payload["error"] = {"kind": "rate_limit", "code": 429, "message": "PRIVATE_ERROR"}
    subscription_usage._reset_agy_quota_observation_for_tests()
    if diagnostic == "stale":
        monkeypatch.setattr(subscription_usage, "_codexbar_cache_ttl_s", lambda: 0)
    monkeypatch.setattr(subscription_usage, "_agy_cli_bin", lambda: "/fixture/agy")
    monkeypatch.setattr(
        subscription_usage.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 0, stdout=json.dumps(payload), stderr="PRIVATE_STDERR"
        ),
    )
    monkeypatch.setattr(subscription_usage, "get_provider_usage_data", lambda *args, **kwargs: {})
    refreshes = []

    def observe():
        if diagnostic == "cold":
            return
        subscription_usage._probe_antigravity_native(timeout_s=1)

    def refresh(providers):
        refreshes.append("subscription")
        observe()

    monkeypatch.setattr(subscription_usage, "refresh_provider_usage_data", refresh)
    monkeypatch.setattr(subscription_usage, "refresh_api_account_data", lambda providers: refreshes.append("prepaid"))
    monkeypatch.setattr(state_router, "compute_routing_budget", lambda **kwargs: budget)
    monkeypatch.setattr(usage.urllib.request, "urlopen", lambda *args, **kwargs: io.StringIO(json.dumps(budget)))
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda: {})
    monkeypatch.setattr(capacity_pick, "admission_status", lambda: {"admitted": None, "line": "fixture"})
    monkeypatch.setattr(capacity_pick, "load_write_success_stats", lambda: {})
    monkeypatch.setattr(capacity_pick, "load_reset_reserve", lambda *args, **kwargs: {"available": False})
    if not fresh:
        observe()

    try:
        # A diagnostic reading exists even though it must never replace routing facts.
        display_status = "healthy" if diagnostic in {"hot", "zero", "full"} else "unknown"
        assert subscription_usage.project_agy_for_status(subscription_usage.get_agy_quota_observation())["status"] == (
            "unknown" if fresh else display_status
        )
        read = usage.read_budget(fresh=fresh)
        assert (
            subscription_usage.project_agy_for_status(subscription_usage.get_agy_quota_observation())["status"]
            == display_status
        )
        report = capacity_pick.build_report(read, active_in_flight={})
        agy = next(row for row in report["rows"] if row["lane"] == "agy")
        assert agy["avoid"] is True, agy
        assert (agy["status"], agy["remaining_pct"], agy["capacity"]["state"]) == ("hot", 3.0, "avoid")
        assert read["agents"] == original["agents"]
        assert budget == original
        argv = ["--json", "--strict"] + (["--fresh"] if fresh else [])
        assert capacity_pick.main(argv) == 2
        output = json.loads(capsys.readouterr().out)
        pick = next(row for row in output["pick_order"] if row["lane"] == "agy")
        assert pick["pick"] == "AVOID"
        assert output["recommendation"]["primary_agent_for_code"] is None
        assert "agy" not in output["cooler_lanes"]
        assert not any(row["lane"] == "agy" and row["pick"] != "AVOID" for row in output["pick_order"])
        assert "muse" not in read["agents"]
        if not agy_signal:
            assert "quota:gemini" in agy["notes"]

        # Render both public views through the real refresh/read/display boundary,
        # then prove that neither the source budget nor later capacity picks changed.
        for command in ("json", "show"):
            assert usage.main([command] + (["--fresh"] if fresh else [])) == 0
            public = capsys.readouterr().out
            for sentinel in (
                "PRIVATE_LABEL",
                "PRIVATE_ACCOUNT",
                "account@example.com",
                "987654",
                "PRIVATE_ERROR",
                "PRIVATE_STDERR",
            ):
                assert sentinel not in public
            if command == "json":
                rows = json.loads(public)["agents"]
                assert {"muse", "agy", "gemini"} <= rows.keys()
                assert rows["gemini"] == quota
                assert rows["agy"]["status"] == display_status
                if diagnostic in {"hot", "zero", "full"}:
                    group = rows["agy"]["quota_groups"][0]
                    assert group["label"] == "Gemini Models"
                    assert group["windows"][0]["remaining_pct"] == fraction * 100
                elif diagnostic == "cold":
                    assert (rows["agy"]["error_kind"], rows["agy"]["error_code"]) == ("unavailable", None)
                elif diagnostic == "error":
                    assert (rows["agy"]["error_kind"], rows["agy"]["error_code"]) == ("rate_limit", 429)
                else:
                    assert rows["agy"]["freshness"] == "stale_last_good"
                    assert rows["agy"]["quota_groups"][0]["windows"][0]["remaining_pct"] is None
            else:
                assert f"agy | {display_status} | unknown |" in public
                assert "muse | unknown | unknown |" in public
            assert budget == original
        later = capacity_pick.build_report(usage.read_budget(fresh=fresh), active_in_flight={})
        assert next(row for row in later["pick_order"] if row["lane"] == "agy")["pick"] == "AVOID"
        assert sorted(refreshes) == (["prepaid"] * 5 + ["subscription"] * 5 if fresh else [])
    finally:
        subscription_usage._reset_agy_quota_observation_for_tests()
