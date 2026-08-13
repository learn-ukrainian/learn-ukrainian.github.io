"""Tests for the read-only scheduled home-session retention check (#4956)."""

from __future__ import annotations

from scripts.hygiene import home_session_retention_check as check
from scripts.hygiene.inventory_home_sessions import SessionCandidate, SessionRootReport


def test_build_report_measures_each_lane_and_flags_stale_bytes(monkeypatch) -> None:
    roots = [
        SessionRootReport("codex", "/home/.codex", True, 200, 1.0, 3),
        SessionRootReport("claude", "/home/.claude", False, 0, None, 0),
    ]
    candidates = [
        SessionCandidate("codex", "/home/.codex/sessions/old.jsonl", "sessions/old.jsonl", 75, 14.0)
    ]
    monkeypatch.setattr(
        check.inventory_home_sessions,
        "inventory_home_sessions",
        lambda *, retention_days: (roots, candidates),
    )

    report = check.build_report(retention_days=14)

    assert report["mode"] == "read_only"
    assert report["policy"] == {
        "retention_days": 14,
        "max_stale_files": 0,
        "max_stale_bytes": 0,
    }
    assert report["lanes"] == [
        {
            "provider": "codex",
            "exists": True,
            "session_files": 3,
            "root_bytes": 200,
            "stale_files": 1,
            "stale_bytes": 75,
            "skipped_reason": None,
        },
        {
            "provider": "claude",
            "exists": False,
            "session_files": 0,
            "root_bytes": 0,
            "stale_files": 0,
            "stale_bytes": 0,
            "skipped_reason": None,
        },
    ]
    assert report["summary"] == {
        "lanes": 2,
        "session_files": 3,
        "root_bytes": 200,
        "stale_files": 1,
        "stale_bytes": 75,
        "violations": 1,
    }
    assert check.warning_lines(report) == [
        "HARD WARNING: codex has 1 allowlisted session file(s) (75 bytes) at least 14 days old; "
        "archive them before any local deletion."
    ]


def test_build_report_fails_closed_when_an_existing_root_cannot_be_measured(monkeypatch) -> None:
    roots = [
        SessionRootReport(
            "cursor",
            "/home/.cursor",
            True,
            None,
            None,
            0,
            "provider home is not a real directory",
        )
    ]
    monkeypatch.setattr(
        check.inventory_home_sessions,
        "inventory_home_sessions",
        lambda *, retention_days: (roots, []),
    )

    report = check.build_report()

    assert report["violations"] == [
        {
            "provider": "cursor",
            "kind": "unmeasurable_root",
            "detail": "provider home is not a real directory",
        }
    ]


def test_main_never_enables_apply_and_returns_nonzero_for_policy_violation(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        check,
        "build_report",
        lambda *, retention_days: {
            "policy": {"retention_days": retention_days},
            "lanes": [],
            "violations": [
                {"provider": "grok", "kind": "stale_sessions", "stale_files": 2, "stale_bytes": 9}
            ],
        },
    )

    assert check.main([]) == 1

    captured = capsys.readouterr()
    assert "read-only" in captured.out
    assert "HARD WARNING" in captured.err
