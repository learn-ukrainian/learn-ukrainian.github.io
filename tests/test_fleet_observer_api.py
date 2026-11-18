"""Product fleet batch snapshot behind the Monitor's fleet operations view.

The Monitor's ``/api/fleet/*`` routes are machinery code and are tested in the
machinery repository; these tests cover only the product's batch provider.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lu_machinery.api.monitor_context import fixture_context

import scripts.project_api.batch_progress as product_batch_progress


def test_operations_batch_snapshot_reuses_uncached_read_models(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = fixture_context(tmp_path)
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_preseed_logs",
        lambda ctx: [
            {
                "track": "hist",
                "complete": False,
                "age_seconds": 30,
                "last_line": "private log line",
            },
            {"track": "bio", "complete": True, "age_seconds": 10},
        ],
    )
    monkeypatch.setattr(
        product_batch_progress,
        "_check_build_processes",
        lambda: ([{"track": "hist", "pid": 123, "cmd": "private command"}], None),
    )
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_track_progress",
        lambda ctx, track: {
            "track": track,
            "total_expected": 10,
            "research_done": 3,
            "remaining": 7,
            "recent_30min": 0,
            "throughput_per_hour": 0,
            "last_created": {"slug": "private-slug"},
        },
    )
    # The comms router keeps no cache since lu-machinery 0.1.31 (machinery
    # #743); the batch progress module's own cache_set binding is the write
    # this snapshot must not reach.
    monkeypatch.setattr(
        product_batch_progress,
        "cache_set",
        lambda *_args, **_kwargs: pytest.fail("operations snapshot must not write cache state"),
    )

    snapshot = product_batch_progress.fleet_batch_snapshot(ctx)

    assert snapshot["running_processes"] == 1
    assert snapshot["tracks"]["hist"]["health"] == "healthy"
    assert snapshot["tracks"]["bio"]["health"] == "complete"


def _batch_progress_stub(track: str) -> dict:
    return {
        "track": track,
        "total_expected": 10,
        "research_done": 3,
        "remaining": 7,
        "recent_30min": 0,
        "throughput_per_hour": 0,
        "last_created": None,
    }


def test_legacy_batch_snapshot_old_log_is_unknown_when_process_probe_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = fixture_context(tmp_path)
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_preseed_logs",
        lambda ctx: [{"track": "hist", "complete": False, "age_seconds": 1200}],
    )
    monkeypatch.setattr(
        product_batch_progress,
        "_check_build_processes",
        lambda: ([], "ps: TimeoutExpired"),
    )
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_track_progress",
        lambda ctx, track: _batch_progress_stub(track),
    )

    snapshot = product_batch_progress.fleet_batch_snapshot(ctx)

    assert snapshot["running_processes"] is None
    assert snapshot["errors"] == ["ps: TimeoutExpired"]
    assert snapshot["tracks"]["hist"]["health"] == "unknown"
    assert snapshot["tracks"]["hist"]["reason"] == "ps: TimeoutExpired"


def test_legacy_batch_snapshot_old_log_stays_dead_when_process_probe_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = fixture_context(tmp_path)
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_preseed_logs",
        lambda ctx: [{"track": "hist", "complete": False, "age_seconds": 1200}],
    )
    monkeypatch.setattr(
        product_batch_progress,
        "_check_build_processes",
        lambda: ([], None),
    )
    monkeypatch.setattr(
        product_batch_progress,
        "_scan_track_progress",
        lambda ctx, track: _batch_progress_stub(track),
    )

    snapshot = product_batch_progress.fleet_batch_snapshot(ctx)

    assert snapshot["running_processes"] == 0
    assert "errors" not in snapshot
    assert snapshot["tracks"]["hist"]["health"] == "dead"
    assert "reason" not in snapshot["tracks"]["hist"]
