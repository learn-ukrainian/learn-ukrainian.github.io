"""Sol PR-L retention plan/apply digest gates."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts.hygiene.retention_engine import (
    apply_plan,
    build_plan,
    plan_digest,
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
