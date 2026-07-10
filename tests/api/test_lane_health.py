"""Tests for lane health tracking and the routing-budget overlay."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.api import state_router
from scripts.api.lane_health import (
    compute_lane_health,
    is_spawn_phase_failure,
    normalize_agent_name,
)
from scripts.delegate import _resolve_agent_with_budget_guard


def test_normalize_agent_name():
    assert normalize_agent_name("Claude") == "claude"
    assert normalize_agent_name("Claude (Interactive)") == "claude"
    assert normalize_agent_name("codex ") == "codex"
    assert normalize_agent_name("deepseek") == "deepseek"
    assert normalize_agent_name("Unknown-Agent") == "unknown-agent"


def test_is_spawn_phase_failure():
    # Spawn failure: status failed, non-zero returncode, short duration
    assert is_spawn_phase_failure({"status": "failed", "returncode": 1, "duration_s": 10}) is True
    assert is_spawn_phase_failure({"status": "error", "returncode": 2, "duration_s": 119}) is True

    # Long duration -> not a spawn failure
    assert is_spawn_phase_failure({"status": "failed", "returncode": 1, "duration_s": 120}) is False
    assert is_spawn_phase_failure({"status": "failed", "returncode": 1, "duration_s": 300}) is False

    # Clean exit (returncode == 0) -> not a spawn failure
    assert is_spawn_phase_failure({"status": "failed", "returncode": 0, "duration_s": 10}) is False

    # Status needs_finalize -> not a spawn failure
    assert is_spawn_phase_failure({"status": "needs_finalize", "returncode": 1, "duration_s": 10}) is False

    # Active/running task (no returncode) -> not a spawn failure
    assert is_spawn_phase_failure({"status": "running", "returncode": None, "duration_s": None}) is False


def _write_task(tmp_path: Path, task_id: str, agent: str, status: str, returncode: int | None, duration_s: float | None, started_at: datetime) -> None:
    task_file = tmp_path / f"{task_id}.json"
    data = {
        "task_id": task_id,
        "agent": agent,
        "status": status,
        "returncode": returncode,
        "duration_s": duration_s,
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
    }
    task_file.write_text(json.dumps(data), encoding="utf-8")


def test_compute_lane_health_consecutive_failures(tmp_path):
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)
    # Write 2 spawn failures for Claude in window
    _write_task(tmp_path, "task-1", "claude", "failed", 1, 15.0, now - timedelta(minutes=45))
    _write_task(tmp_path, "task-2", "claude", "failed", 2, 20.0, now - timedelta(minutes=15))

    health = compute_lane_health(tmp_path, now=now)
    assert health["claude"]["healthy"] is False
    assert health["claude"]["consecutive_failures"] == 2
    assert health["claude"]["span_minutes"] == 45


def test_compute_lane_health_outside_window(tmp_path):
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)
    # Write 1 spawn failure outside window (130m ago) and 1 inside (15m ago)
    _write_task(tmp_path, "task-1", "claude", "failed", 1, 15.0, now - timedelta(minutes=130))
    _write_task(tmp_path, "task-2", "claude", "failed", 2, 20.0, now - timedelta(minutes=15))

    health = compute_lane_health(tmp_path, now=now)
    # Should only count the inside failure, so consecutive_failures = 1
    assert health.get("claude", {}).get("healthy", True) is True
    assert health.get("claude", {}).get("consecutive_failures", 0) == 1


def test_compute_lane_health_success_breaks_streak(tmp_path):
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)
    # failure -> success -> failure
    _write_task(tmp_path, "task-1", "claude", "failed", 1, 10.0, now - timedelta(minutes=50))
    _write_task(tmp_path, "task-2", "claude", "complete", 0, 120.0, now - timedelta(minutes=30))
    _write_task(tmp_path, "task-3", "claude", "failed", 1, 10.0, now - timedelta(minutes=10))

    health = compute_lane_health(tmp_path, now=now)
    # Streak broken by the success (task-2), so only 1 consecutive failure at the end
    assert health.get("claude", {}).get("healthy", True) is True
    assert health.get("claude", {}).get("consecutive_failures", 0) == 1


def test_compute_lane_health_needs_finalize_breaks_streak(tmp_path):
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)
    # failure -> needs_finalize
    _write_task(tmp_path, "task-1", "claude", "failed", 1, 10.0, now - timedelta(minutes=30))
    _write_task(tmp_path, "task-2", "claude", "needs_finalize", 1, 10.0, now - timedelta(minutes=10))

    health = compute_lane_health(tmp_path, now=now)
    # Streak broken by needs_finalize
    assert health.get("claude", {}).get("healthy", True) is True
    assert health.get("claude", {}).get("consecutive_failures", 0) == 0


def test_compute_lane_health_corrupted_json(tmp_path):
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)
    # One valid task failure
    _write_task(tmp_path, "task-1", "claude", "failed", 1, 10.0, now - timedelta(minutes=10))
    # One corrupted file
    (tmp_path / "corrupted.json").write_text("{invalid json", encoding="utf-8")

    # Fail-open: should still run and return the stats of the valid one without crashing
    health = compute_lane_health(tmp_path, now=now)
    assert health.get("claude", {}).get("consecutive_failures", 0) == 1


def test_routing_budget_demotes_unhealthy(monkeypatch, tmp_path):
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)

    # Configure mock budgets (empty budget or mock loaded)
    monkeypatch.setattr(state_router, "BUDGET_CONFIG_PATH", tmp_path / "absent_budgets.yaml")
    monkeypatch.setattr(state_router, "TASKS_DIR", tmp_path)
    monkeypatch.setattr(state_router, "load_cost_records", lambda: [])
    monkeypatch.setattr(
        state_router.delegate_api,
        "list_delegate_tasks",
        lambda **_kwargs: {"tasks": []},
    )

    # Claude unhealthy (2 failures)
    _write_task(tmp_path, "task-1", "claude", "failed", 1, 10.0, now - timedelta(minutes=45))
    _write_task(tmp_path, "task-2", "claude", "failed", 1, 10.0, now - timedelta(minutes=15))

    budget = state_router.compute_routing_budget(now)

    assert budget["agents"]["claude"]["health"]["healthy"] is False
    assert budget["agents"]["claude"]["health"]["consecutive_failures"] == 2

    # Verify demotion: claude must be at the bottom of ranked_by_headroom
    ranked = budget["ranked_by_headroom"]
    assert ranked[-1]["lane"] == "claude"
    assert ranked[-1]["health"]["healthy"] is False


def test_delegate_prints_warning(monkeypatch, capsys):
    # Mock routing budget API payload
    mock_payload = {
        "generated_at": "2026-07-10T12:00:00Z",
        "agents": {
            "claude": {
                "status": "unknown",
                "health": {
                    "healthy": False,
                    "consecutive_failures": 2,
                    "span_minutes": 45,
                }
            },
            "codex": {
                "status": "unknown",
                "health": {
                    "healthy": True,
                    "consecutive_failures": 0,
                    "span_minutes": 0,
                }
            }
        },
        "diagnostics": {
            "records_loaded": 1,
            "stale": False,
            "codexbar_data_available": True,
        },
        "recommendation": {
            "primary_agent_for_code": "codex",
            "rationale": "Test",
            "warnings": [],
        },
        "ranked_by_headroom": [
            {
                "lane": "codex",
                "type": "subscription",
                "status": "unknown",
                "health": {
                    "healthy": True,
                    "consecutive_failures": 0,
                    "span_minutes": 0,
                }
            },
            {
                "lane": "claude",
                "type": "subscription",
                "status": "unknown",
                "health": {
                    "healthy": False,
                    "consecutive_failures": 2,
                    "span_minutes": 45,
                }
            }
        ]
    }

    monkeypatch.setattr("scripts.delegate._fetch_routing_budget", lambda: mock_payload)
    monkeypatch.setattr("scripts.delegate._load_dispatch_fallbacks", lambda: {})

    res = _resolve_agent_with_budget_guard("codex")
    assert res == "codex"

    # Capture outputs
    captured = capsys.readouterr()
    assert "lane claude demoted: 2 spawn failures in 45m" in captured.err
