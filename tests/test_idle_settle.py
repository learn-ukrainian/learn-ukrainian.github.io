"""Tests for scripts.fleet.idle_settle (#6976 reminder + #6998 admission / enforce codes)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.fleet import idle_settle as idle


def _snapshot(
    *,
    lanes: list[dict] | None = None,
    items: list[dict] | None = None,
    caps: dict | None = None,
) -> idle.EligibilitySnapshot:
    return idle.parse_snapshot(
        {
            "lanes": lanes
            if lanes is not None
            else [{"lane": "cursor", "status": "cool", "in_flight": 0, "will_last": True}],
            "items": items
            if items is not None
            else [
                {
                    "item_id": "issue:6976",
                    "kind": "issue",
                    "ready": True,
                    "valuable": True,
                    "independent": True,
                }
            ],
            "caps": caps or {},
        }
    )


def test_disposition_codes_include_original_six_and_new_wip() -> None:
    assert {
        "dependency_blocked",
        "review_wip_cap",
        "ci_capacity",
        "disk_capacity",
        "human_decision",
        "no_ready_work",
        "authoring_wip_cap",
        "worktree_wip_cap",
        "integration_wip_cap",
    } == idle.DISPOSITION_CODES
    for code in idle.DISPOSITION_CODES:
        assert idle.disposition_accepted(code) is True
    assert idle.disposition_accepted("busywork") is False
    assert idle.disposition_accepted("") is False
    assert idle.normalize_disposition("  ") is None
    assert idle.normalize_disposition(" human_decision ") == "human_decision"


def test_reminder_silent_when_nothing_actionable() -> None:
    snap = _snapshot(items=[])
    decision = idle.evaluate_settle(snap)
    assert decision.eligible is False
    assert decision.reminder_fired is False
    assert decision.reminder_required is False
    assert decision.outcome == "silent"
    assert idle.format_reminder(decision, snap) is None


def test_reminder_silent_when_lane_unhealthy_or_busy() -> None:
    hot = _snapshot(lanes=[{"lane": "codex", "status": "hot", "in_flight": 0, "will_last": True}])
    busy = _snapshot(lanes=[{"lane": "cursor", "status": "cool", "in_flight": 1, "will_last": True}])
    deficit = _snapshot(lanes=[{"lane": "kimi", "status": "cool", "in_flight": 0, "will_last": False}])
    for snap in (hot, busy, deficit):
        decision = idle.evaluate_settle(snap)
        assert decision.eligible is False
        assert decision.reminder_fired is False


def test_reminder_silent_when_item_not_fillable() -> None:
    blocked = _snapshot(items=[{"item_id": "issue:1", "dependency_blocked": True}])
    unready = _snapshot(items=[{"item_id": "issue:2", "ready": False}])
    cheap = _snapshot(items=[{"item_id": "issue:3", "valuable": False}])
    colliding = _snapshot(items=[{"item_id": "issue:4", "independent": False}])
    for snap in (blocked, unready, cheap, colliding):
        decision = idle.evaluate_settle(snap)
        assert decision.eligible is False
        assert decision.reminder_fired is False


def test_resource_caps_suppress_eligibility() -> None:
    review_cap = _snapshot(caps={"review_in_flight": 4, "review_wip_limit": 4})
    ci = _snapshot(caps={"ci_capacity_ok": False})
    disk = _snapshot(caps={"disk_ok": False})
    for snap, code in (
        (review_cap, "review_wip_cap"),
        (ci, "ci_capacity"),
        (disk, "disk_capacity"),
    ):
        decision = idle.evaluate_settle(snap)
        assert decision.eligible is False
        assert decision.reminder_fired is False
        assert code in decision.active_constraints


def test_reminder_fires_only_when_eligible_and_no_action() -> None:
    snap = _snapshot()
    decision = idle.evaluate_settle(snap)
    assert decision.eligible is True
    assert decision.reminder_required is True
    assert decision.reminder_fired is True
    assert decision.outcome == "missing_action"
    assert decision.accepted is False
    text = idle.format_reminder(decision, snap)
    assert text is not None
    assert "issue:6976" in text
    assert "ACTION REQUIRED" in text
    assert "review_wip=" in text
    assert "cursor" in text


def test_dispatch_satisfies_and_does_not_nag() -> None:
    snap = _snapshot()
    decision = idle.evaluate_settle(snap, dispatched=True)
    assert decision.outcome == "dispatched"
    assert decision.accepted is True
    assert decision.reminder_required is False
    assert decision.reminder_fired is False
    text = idle.format_reminder(decision, snap)
    assert text is not None
    assert "satisfied via dispatched" in text
    assert "ACTION REQUIRED" not in text


@pytest.mark.parametrize("code", sorted(idle.DISPOSITION_CODES))
def test_six_disposition_codes_accepted(code: str) -> None:
    snap = _snapshot()
    decision = idle.evaluate_settle(snap, disposition=code)
    assert decision.outcome == "disposed"
    assert decision.accepted is True
    assert decision.disposition_valid is True
    assert decision.reminder_fired is False
    assert decision.disposition == code


def test_unknown_disposition_rejected() -> None:
    snap = _snapshot()
    decision = idle.evaluate_settle(snap, disposition="taking_a_break")
    assert decision.outcome == "invalid_disposition"
    assert decision.accepted is False
    assert decision.disposition_valid is False
    assert decision.reminder_fired is True


def test_compatible_lanes_must_intersect() -> None:
    snap = _snapshot(
        lanes=[
            {"lane": "cursor", "status": "cool", "in_flight": 0, "will_last": True},
            {"lane": "codex", "status": "hot", "in_flight": 0, "will_last": True},
        ],
        items=[{"item_id": "issue:1", "compatible_lanes": ["codex"]}],
    )
    decision = idle.evaluate_settle(snap)
    assert decision.eligible is False
    snap2 = _snapshot(
        items=[{"item_id": "issue:1", "compatible_lanes": ["cursor"]}],
    )
    decision2 = idle.evaluate_settle(snap2)
    assert decision2.eligible is True
    assert decision2.eligible_pairs == (idle.EligiblePair(lane="cursor", item_id="issue:1"),)


def test_no_ready_work_is_dishonest_when_eligible() -> None:
    snap = _snapshot()
    decision = idle.evaluate_settle(snap, disposition="no_ready_work")
    assert decision.disposition_honest is False
    empty = _snapshot(items=[])
    honest = idle.evaluate_settle(empty, disposition="no_ready_work")
    assert honest.disposition_honest is True
    assert honest.reminder_fired is False


def test_human_decision_is_always_honest() -> None:
    snap = _snapshot()
    decision = idle.evaluate_settle(snap, disposition="human_decision")
    assert decision.disposition_honest is True


def test_opportunity_seconds_only_when_previous_was_eligible() -> None:
    t0 = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
    t1 = t0 + timedelta(seconds=45)
    prev_eligible = {"eligible": True, "recorded_at": idle.format_iso(t0)}
    prev_silent = {"eligible": False, "recorded_at": idle.format_iso(t0)}
    assert idle.opportunity_seconds_since(prev_eligible, t1) == 45.0
    assert idle.opportunity_seconds_since(prev_silent, t1) == 0.0
    assert idle.opportunity_seconds_since(None, t1) == 0.0


def test_record_and_report_counts_missing_and_opportunity(tmp_path: Path) -> None:
    store = tmp_path / "events.jsonl"
    snap = _snapshot()
    t0 = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
    t1 = t0 + timedelta(seconds=30)
    first = idle.evaluate_settle(snap)
    idle.record_settle(store, first, now=t0, event_id="e1")
    second = idle.evaluate_settle(snap, dispatched=True)
    idle.record_settle(store, second, now=t1, event_id="e2")
    report = idle.build_report(idle.load_events(store))
    assert report["schema"] == idle.REPORT_SCHEMA
    assert report["report_only"] is True
    assert report["event_count"] == 2
    assert report["settle_events_missing_action"] == 1
    assert report["settle_events_dispatched"] == 1
    assert report["eligible_idle_opportunity_seconds"] == 30.0
    assert "pass" not in report
    assert "threshold" not in report


def test_cli_evaluate_rejects_unknown_disposition(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    snap_path = tmp_path / "snap.json"
    snap_path.write_text(json.dumps(_snapshot().to_dict()), encoding="utf-8")
    store = tmp_path / "events.jsonl"
    rc = idle.main(
        [
            "evaluate",
            "--snapshot-json",
            str(snap_path),
            "--store",
            str(store),
            "--disposition",
            "taking_a_break",
            "--json",
        ]
    )
    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == "invalid_disposition"


def test_cli_evaluate_missing_action_is_report_only_zero(tmp_path: Path) -> None:
    snap_path = tmp_path / "snap.json"
    snap_path.write_text(json.dumps(_snapshot().to_dict()), encoding="utf-8")
    store = tmp_path / "events.jsonl"
    rc = idle.main(
        [
            "evaluate",
            "--snapshot-json",
            str(snap_path),
            "--store",
            str(store),
            "--task-id",
            "infra-6976",
        ]
    )
    assert rc == 0
    report = idle.build_report(idle.load_events(store))
    assert report["settle_events_missing_action"] == 1


def test_cli_report_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    store = tmp_path / "events.jsonl"
    idle.record_settle(store, idle.evaluate_settle(_snapshot()), now=datetime(2026, 8, 17, tzinfo=UTC))
    rc = idle.main(["report", "--store", str(store), "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_only"] is True
    assert payload["settle_events_missing_action"] == 1


def test_infer_review_kind() -> None:
    assert idle.infer_settle_kind("review-6981") == "review"
    assert idle.infer_settle_kind("infra-6976") == "dispatch"


def test_items_from_work_next_marks_blockers() -> None:
    items = idle.items_from_work_next_queue(
        [
            {
                "work_id": "issue:1",
                "resource_kind": "issue",
                "safe_next_action": {"code": "RESOLVE_BLOCKER", "reason_codes": ["blocked_by"]},
            },
            {"work_id": "issue:2", "resource_kind": "pr", "safe_next_action": {"code": "REQUEST_CF_REVIEW"}},
        ]
    )
    assert items[0].dependency_blocked is True
    assert items[1].dependency_blocked is False
    assert items[1].is_fillable() is True


def test_lanes_from_capacity_rows_mark_avoid_as_quota_fail() -> None:
    lanes = idle.lanes_from_capacity_rows(
        [
            {"lane": "codex", "status": "hot", "in_flight": 0, "will_last": False, "avoid": True},
            {"lane": "cursor", "status": "cool", "in_flight": 0, "will_last": True, "avoid": False},
        ]
    )
    assert lanes[0].is_healthy_available() is False
    assert lanes[1].is_healthy_available() is True


@pytest.mark.parametrize(
    ("caps", "reason"),
    [
        ({"authoring_in_flight": 3, "authoring_wip_limit": 3}, "authoring_wip_cap"),
        ({"review_in_flight": 4, "review_wip_limit": 4}, "review_wip_cap"),
        ({"ci_in_flight": 2, "ci_wip_limit": 2}, "ci_capacity"),
        ({"ci_capacity_ok": False}, "ci_capacity"),
        ({"worktrees_in_flight": 8, "worktrees_wip_limit": 8}, "worktree_wip_cap"),
        ({"disk_in_flight": 1, "disk_wip_limit": 1}, "disk_capacity"),
        ({"disk_ok": False}, "disk_capacity"),
        ({"integration_in_flight": 1, "integration_wip_limit": 1}, "integration_wip_cap"),
    ],
)
def test_admission_wip_reason_codes(caps: dict, reason: str) -> None:
    snap = _snapshot(caps=caps)
    state = idle.evaluate_admission(snap)
    assert state.admitted is False
    assert reason in state.reason_codes
    assert state.queue_ready is True
    dim = next(name for name, code in idle.WIP_REASON_CODES.items() if code == reason)
    assert state.wip[dim]["ok"] is False
    assert state.wip[dim]["reason_code"] == reason
    decision = idle.evaluate_settle(snap, disposition=reason)
    assert decision.disposition_honest is True
    assert reason in decision.active_constraints


def test_admission_admitted_when_under_limits_and_queue_ready() -> None:
    snap = _snapshot(
        caps={
            "authoring_in_flight": 1,
            "authoring_wip_limit": 3,
            "review_in_flight": 0,
            "review_wip_limit": 4,
            "ci_in_flight": 0,
            "ci_wip_limit": 5,
            "worktrees_in_flight": 2,
            "worktrees_wip_limit": 6,
            "disk_in_flight": 0,
            "disk_wip_limit": 1,
            "integration_in_flight": 0,
            "integration_wip_limit": 2,
        }
    )
    state = idle.evaluate_admission(snap)
    assert state.admitted is True
    assert state.queue_ready is True
    assert state.ready_item_count == 1
    assert state.reason_codes == ()
    for name in idle.WIP_DIMENSIONS:
        assert state.wip[name]["ok"] is True
        assert state.wip[name]["reason_code"] is None


def test_admission_queue_not_ready() -> None:
    snap = _snapshot(items=[{"item_id": "issue:1", "ready": False}])
    state = idle.evaluate_admission(snap)
    assert state.admitted is False
    assert state.queue_ready is False
    assert state.reason_codes == ("no_ready_work",)


def test_enforce_fail_codes_ignore_idle_seconds() -> None:
    missing = idle.build_report(
        [{"outcome": "missing_action", "opportunity_seconds_since_prev": 9, "disposition_honest": None}],
        enforce=True,
    )
    assert missing["enforce_fail_codes"] == [idle.ENFORCE_MISSING]
    assert missing["idle_seconds_never_enforce"] is True
    honest = idle.build_report(
        [
            {
                "outcome": "disposed",
                "opportunity_seconds_since_prev": 99999,
                "disposition_honest": True,
            }
        ],
        enforce=True,
    )
    assert honest["enforce_fail_codes"] == []
    assert honest["eligible_idle_opportunity_seconds"] == 99999
    assert idle.enforce_fail_codes(honest) == ()
    dishonest = idle.build_report(
        [{"outcome": "disposed", "disposition_honest": False, "opportunity_seconds_since_prev": 0}],
        enforce=True,
    )
    assert dishonest["enforce_fail_codes"] == [idle.ENFORCE_DISHONEST]


def test_cli_admission_json_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ok = tmp_path / "ok.json"
    ok.write_text(json.dumps(_snapshot().to_dict()), encoding="utf-8")
    blocked = tmp_path / "blocked.json"
    blocked.write_text(
        json.dumps(_snapshot(caps={"worktrees_in_flight": 5, "worktrees_wip_limit": 4}).to_dict()),
        encoding="utf-8",
    )
    assert idle.main(["admission", "--snapshot-json", str(ok), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["admitted"] is True
    assert idle.main(["admission", "--snapshot-json", str(blocked), "--json"]) == 2
    refused = json.loads(capsys.readouterr().out)
    assert refused["reason_codes"] == ["worktree_wip_cap"]
