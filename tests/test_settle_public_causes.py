"""Legacy settle records and diagnostics remain byte-for-byte read-only."""

from __future__ import annotations

import json

import pytest

from scripts.orchestration import dead_worker_state, dispatch_settle


@pytest.mark.parametrize("schema", [None, 1])
@pytest.mark.parametrize("writer", ["dead-worker", "missing-worktree", "orphaned"])
def test_legacy_settle_preserves_records_diagnostics_and_claims(tmp_path, monkeypatch, schema, writer):
    from unittest.mock import Mock

    path = tmp_path / "worker.json"
    state = {
        "task_id": "worker", "status": "running", "pid": 999_999_999,
        "run_nonce": "attempt-1", "worktree_path": str(tmp_path / "missing"),
        "last_error": "worker_failed", "finalize_error": "unclassified_error",
    }
    if schema is not None:
        state["schema_version"] = schema
    path.write_text(json.dumps(state))
    diagnostic = path.with_suffix(".diag")
    diagnostic.write_text("existing diagnostic\n")
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    ledger = Mock()
    monkeypatch.setattr(dispatch_settle, "_pid_alive", lambda _pid: False)

    for _ in range(2):
        if writer == "dead-worker":
            assert dispatch_settle.heal_zombie_task(tmp_path, "worker", ledger=ledger) == []
        elif writer == "missing-worktree":
            assert dispatch_settle.settle_missing_worktree(tmp_path, "worker", ledger=ledger) == []
        else:
            current, changed = dead_worker_state._mark_orphaned_pidless_crashed(
                path, state, is_orphaned=lambda _state: True,
                reason="dispatch_died_during_worktree_prep", excerpt=lambda *_args: "dispatcher died",
            )
            assert not changed and current == state
        assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before
        ledger.release.assert_not_called()
