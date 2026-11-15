"""Synthetic Claude account fixtures shared by routing tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path


def default_account_file(tmp_path, monkeypatch, content: bytes | None = None, *, mode: int = 0o600) -> Path:
    path = tmp_path / "operator-config" / "claude-default-account"
    path.parent.mkdir(exist_ok=True)
    monkeypatch.setenv("LU_CLAUDE_DEFAULT_ACCOUNT_FILE", str(path))
    if content is not None:
        path.write_bytes(content)
        path.chmod(mode)
    return path


def bind_claude_account_b(tmp_path, monkeypatch, *, bound: bool = True) -> str:
    from tests.agent_runtime.test_attempt_boundary import (
        BOUND_ACCOUNT_UUID,
        CLAUDE_AMBIENT_AUTH,
        DEFAULT_ACCOUNT_UUID,
        _credentials,
        _login_identity,
        _mock_selected_account_runtime,
        _private_json,
    )

    identities, _calls = _mock_selected_account_runtime(tmp_path, monkeypatch)
    for key in (*CLAUDE_AMBIENT_AUTH, "CLAUDE_CONFIG_DIR"):
        monkeypatch.delenv(key, raising=False)
    home, selected = tmp_path / "home", tmp_path / "selected"
    selected.mkdir(mode=0o700)
    token = "fixture-bound-" + "b" * 30
    identities[token] = BOUND_ACCOUNT_UUID
    _private_json(home / ".claude.json", {"oauthAccount": {"accountUuid": DEFAULT_ACCOUNT_UUID}})
    _private_json(selected / ".claude.json", {"oauthAccount": _login_identity(BOUND_ACCOUNT_UUID)})
    _credentials(selected / ".credentials.json", token)
    binding = tmp_path / "binding.json"
    if bound:
        _private_json(binding, {"schema_version": 1, "accounts": {"b": {"config_dir": str(selected), "account_uuid": BOUND_ACCOUNT_UUID}}})
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(binding))
    return str(selected)


def _utc_in(delta: timedelta) -> str:
    return (datetime.now(UTC) + delta).isoformat(timespec="seconds").replace("+00:00", "Z")


def fresh_lane(**overrides) -> dict:
    record = {"health": {"healthy": True}, "freshness": "fresh", "age_s": 30.0, **overrides}
    record["codexbar"] = {"freshness": "fresh", "age_s": 30.0, **record.get("codexbar", {})}
    return record


def account_row(
    weekly_left: float | None,
    *,
    session_left: float | None = 100.0,
    status: str = "ok",
    weekly_resets_in: timedelta = timedelta(days=5),
    reason: str | None = None,
) -> dict:
    def window(left: float | None, resets_in: timedelta) -> dict:
        resets = None if left is None else _utc_in(resets_in)
        return {"left_pct": left, "resets_at": resets, "pace": None, "pace_delta_pct": None, "leftover_pct": None}

    return {
        "session5h": window(session_left, timedelta(hours=3)),
        "weekly": window(weekly_left, weekly_resets_in),
        "updated": _utc_in(timedelta(minutes=-1)),
        "age_s": 60.0,
        "stale": status == "stale",
        "status": status,
        "reason": reason,
    }


UNVERIFIED_ROW = {
    "session5h": dict.fromkeys(("left_pct", "resets_at", "pace", "pace_delta_pct", "leftover_pct")),
    "weekly": dict.fromkeys(("left_pct", "resets_at", "pace", "pace_delta_pct", "leftover_pct")),
    "updated": None,
    "age_s": None,
    "stale": False,
    "status": "unknown",
    "reason": "claude_account_unverified",
}


def default_claude_lane(state: str) -> dict:
    if state == "healthy":
        return fresh_lane(
            status="cool", status_source="weekly_pace", interactive={"status": "cool", "burn_pct_7d": 10.0},
            remaining_pct=90.0,
            codexbar={"weekly_used_pct": 10.0, "weekly_remaining_pct": 90.0, "will_last_to_reset": True},
        )
    if state == "near_cap":
        return fresh_lane(
            status="near_cap", status_source="weekly_pace", interactive={"status": "near_cap", "burn_pct_7d": 99.5},
            remaining_pct=0.5,
            codexbar={"weekly_used_pct": 99.5, "weekly_remaining_pct": 0.5, "primary_remaining_pct": 100.0},
        )
    return fresh_lane(
        status="hot", status_source="weekly_pace", interactive={"status": "hot", "burn_pct_7d": 84.0},
        remaining_pct=16.0,
        codexbar={"weekly_used_pct": 84.0, "weekly_remaining_pct": 16.0, "primary_remaining_pct": 100.0,
                 "weekly_pace_delta_pct": 40.7, "weekly_expected_pct": 43.3, "will_last_to_reset": False},
    )


def accounts_budget(lane: dict, rows: dict[str, dict | None]) -> dict:
    return {
        "recommendation": {"primary_agent_for_code": "codex", "rationale": "fixture rationale", "warnings": []},
        "agents": {"claude": lane, "codex": fresh_lane(status="cool", codexbar={"weekly_remaining_pct": 90.0, "will_last_to_reset": True})},
        "claude_accounts": {f"claude:{label}": row for label, row in rows.items() if row is not None},
        "diagnostics": {"records_loaded": 0, "stale": False, "codexbar_data_available": True},
    }
