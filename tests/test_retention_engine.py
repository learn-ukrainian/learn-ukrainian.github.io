"""Sol PR-L retention plan/apply digest gates."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts.hygiene.retention_engine import (
    apply_plan,
    build_plan,
    plan_digest,
    record_gate5_observation,
    write_plan,
)
from scripts.orchestration.reap_worktrees import ReapResult


def _fake_reap(*, apply: bool = False, **_kwargs):
    action = "removed" if apply else "would_remove"
    return [
        ReapResult(
            path="/tmp/fake-worktree",
            branch="grok/fake",
            action=action,
            reason="merged PR",
            dirty=False,
            pr={"number": 1, "state": "MERGED"},
        )
    ]


def test_plan_digest_stable_and_apply_rejects_mismatch(tmp_path: Path) -> None:
    with (
        patch("scripts.hygiene.retention_engine.reap_worktrees", side_effect=_fake_reap),
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
        assert plan["counts"]["would_reap"] == 1
        digest = plan["digest"]
        assert digest == plan_digest(plan)
        assert len(digest) == 64

        path = write_plan(plan, tmp_path / "plans")
        assert path.is_file()
        assert (tmp_path / "plans" / "latest.json").is_file()

        # Matching digest: dry-run apply ok with zero mutations when dry_run
        receipt = apply_plan(plan, repo_root=tmp_path, dry_run=True)
        assert receipt["ok"] is True
        assert receipt["mutations"] == 0

        # Mutate plan candidates → digest mismatch on re-plan
        bad = dict(plan)
        bad["candidates"] = {
            **plan["candidates"],
            "worktree_reap": [],
        }
        # force wrong stored digest
        bad["digest"] = "0" * 64
        receipt2 = apply_plan(bad, repo_root=tmp_path, dry_run=False)
        assert receipt2["ok"] is False
        assert receipt2["error"] == "plan_digest_mismatch"
        assert receipt2["mutations"] == 0


def test_record_gate5_observation_one_day_per_calendar_label(tmp_path: Path) -> None:
    plan_dir = tmp_path / "retention"
    plan = {
        "schema": "fleet-comms.retention.plan.v1",
        "mode": "dry-run",
        "created_at": "2026-07-24T12:00:00Z",
        "digest": "abc123",
        "mutations": 0,
        "counts": {"would_reap": 0, "scanner_stale": 0},
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

    # New day advances count
    plan3 = dict(plan)
    plan3["created_at"] = "2026-07-25T01:00:00Z"
    plan3["digest"] = "ghi789"
    path3 = write_plan(plan3, plan_dir)
    # Pin "today" so readiness uses recency (CF P2), not wall-clock alone.
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


def test_apply_runs_reaper_only_when_digest_matches(tmp_path: Path) -> None:
    calls: list[bool] = []

    def tracking_reap(*, apply: bool = False, **kwargs):
        calls.append(apply)
        return _fake_reap(apply=apply, **kwargs)

    with (
        patch("scripts.hygiene.retention_engine.reap_worktrees", side_effect=tracking_reap),
        patch("scripts.hygiene.retention_engine.scan_dispatch_worktrees", return_value=[]),
        patch(
            "scripts.hygiene.retention_engine.primary_checkout_root",
            side_effect=lambda p: Path(p),
        ),
    ):
        plan = build_plan(repo_root=tmp_path, archive_root=tmp_path / "a")
        receipt = apply_plan(plan, repo_root=tmp_path, dry_run=False)
        assert receipt["ok"] is True
        assert receipt["mode"] == "apply"
        assert receipt["mutations"] == 1
        # build_plan called reap once (False), apply once (True)
        assert False in calls
        assert True in calls
