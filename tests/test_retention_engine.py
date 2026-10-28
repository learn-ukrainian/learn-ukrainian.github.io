"""Sol PR-L retention plan digest and Gate 5 observation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts.hygiene.retention_engine import (
    build_plan,
    plan_digest,
    record_gate5_observation,
    write_plan,
)


def test_plan_digest_is_stable_and_plan_never_mutates(tmp_path: Path) -> None:
    with (
        patch("scripts.hygiene.retention_engine.scan_dispatch_worktrees", return_value=[]),
        patch(
            "scripts.hygiene.retention_engine.primary_checkout_root",
            side_effect=lambda p: Path(p),
        ),
    ):
        plan = build_plan(
            repo_root=tmp_path,
            archive_root=tmp_path / "archives",
            stale_hours=72.0,
            include_home=False,
        )
        assert plan["schema"] == "fleet-comms.retention.plan.v1"
        assert plan["mutations"] == 0
        assert set(plan["candidates"]) == {"scanner_stale", "home_sessions"}
        digest = plan["digest"]
        assert digest == plan_digest(plan)
        assert len(digest) == 64

        path = write_plan(plan, tmp_path / "plans")
        assert path.is_file()
        assert (tmp_path / "plans" / "latest.json").is_file()


def test_record_gate5_observation_one_day_per_calendar_label(tmp_path: Path) -> None:
    from scripts.hygiene.retention_engine import _gate5_ready_for_apply_go

    plan_dir = tmp_path / "retention"
    plan = {
        "schema": "fleet-comms.retention.plan.v1",
        "mode": "dry-run",
        "created_at": "2026-07-24T12:00:00Z",
        "digest": "abc123",
        "mutations": 0,
        "counts": {"scanner_stale": 0},
    }
    path = write_plan(plan, plan_dir)
    log1 = record_gate5_observation(plan, plan_path=path, log_path=plan_dir / "gate5-observation-log.json")
    assert log1["days_count"] == 1
    assert log1["observation_days_recorded"] == ["2026-07-24"]
    assert log1["apply_armed"] is False
    assert log1["ready_for_apply_go"] is False

    # Same calendar day, second plan — day count stays 1
    plan2 = dict(plan)
    plan2["created_at"] = "2026-07-24T18:00:00Z"
    plan2["digest"] = "def456"
    path2 = write_plan(plan2, plan_dir)
    log2 = record_gate5_observation(plan2, plan_path=path2, log_path=plan_dir / "gate5-observation-log.json")
    assert log2["days_count"] == 1
    assert len(log2["plans"]) == 2

    # Contiguous new day → ready at target_days=2
    plan3 = dict(plan)
    plan3["created_at"] = "2026-07-25T01:00:00Z"
    plan3["digest"] = "ghi789"
    path3 = write_plan(plan3, plan_dir)
    with patch(
        "scripts.hygiene.retention_engine._utc_now",
        return_value="2026-07-25T02:00:00Z",
    ):
        log3 = record_gate5_observation(
            plan3,
            plan_path=path3,
            log_path=plan_dir / "gate5-observation-log.json",
            target_days=2,
        )
    assert log3["days_count"] == 2
    assert log3["ready_for_apply_go"] is True
    assert log3["apply_armed"] is False

    # Sparse days are not contiguous → not ready (CF #5667 P1)
    assert (
        _gate5_ready_for_apply_go(
            ["2026-01-01", "2026-03-01", "2026-07-25"],
            target_days=3,
            now_utc="2026-07-25T00:00:00Z",
        )
        is False
    )
    # Contiguous tail of length 3 is ready
    assert (
        _gate5_ready_for_apply_go(
            ["2026-07-23", "2026-07-24", "2026-07-25"],
            target_days=3,
            now_utc="2026-07-25T00:00:00Z",
        )
        is True
    )

    # Stale latest day → not ready even if day count is high
    with patch(
        "scripts.hygiene.retention_engine._utc_now",
        return_value="2026-08-10T00:00:00Z",
    ):
        log4 = record_gate5_observation(
            plan3,
            plan_path=path3,
            log_path=plan_dir / "gate5-observation-log.json",
            target_days=2,
        )
    assert log4["days_count"] == 2
    assert log4["ready_for_apply_go"] is False


def test_plan_digest_ignores_volatile_envelope_fields() -> None:
    body = {
        "schema": "fleet-comms.retention.plan.v1",
        "mode": "dry-run",
        "repo_root": "/tmp/repo",
        "archive_root": "/tmp/archives",
        "policy": {"stale_hours": 72.0},
        "candidates": {"scanner_stale": [], "home_sessions": []},
        "counts": {"scanner_stale": 0},
        "mutations": 0,
    }
    first = dict(body, created_at="2026-07-24T12:00:00Z", digest="aaa", plan_path="/tmp/plan-aaa.json")
    second = dict(
        body,
        created_at="2026-08-01T00:00:00Z",
        digest="bbb",
        plan_path="/tmp/plan-bbb.json",
        receipt={"ok": True, "mutations": 0},
    )
    assert plan_digest(first) == plan_digest(second)
