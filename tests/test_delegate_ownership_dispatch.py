"""#10015: directory ownership refuses the reviewer's live-dispatch reproduction."""

import json
import os
from pathlib import Path

import pytest

from scripts.guardrails import delegate_ownership as ownership
from tests.test_delegate_admission import (
    _live_danger_args,
    _running_record,
    _stub_worktree,
    delegate,
)
from tests.test_delegate_admission import (
    tasks_dir as tasks_dir,
)


@pytest.mark.parametrize(
    "held,incoming",
    [
        ("scripts/agent_runtime", "scripts/agent_runtime/runner.py"),
        ("scripts/agent_runtime/runner.py", "scripts/agent_runtime"),
    ],
)
def test_dispatch_refuses_directory_child_overlap(tasks_dir, monkeypatch, capsys, held, incoming):
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setenv("DELEGATE_OWNERSHIP_MODE", "refuse")
    pid = os.getpid()
    _running_record(Path(os.environ["LEARN_UKRAINIAN_OWNERSHIP_TASK_STATE_DIR"]), "holder", pid=pid)
    holder = ownership.admit_write_paths(
        task_id="holder", mode="workspace-write", owned_paths=[held], pid=pid
    )
    assert holder.admitted
    monkeypatch.setattr(
        delegate.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("overlapping writer must not spawn")
    )
    args = _live_danger_args(tasks_dir, "directory-overlap")
    args.owned_path = [incoming]
    args.research_owned_path = ["docs/**"]

    assert delegate.cmd_dispatch(args) == 2

    err = capsys.readouterr().err
    assert "write-path ownership refused" in err
    assert "overlaps holder" in err
    assert not delegate._state_path(args.task_id).exists()
    with ownership.OwnershipLedger()._connect() as conn:
        assert conn.execute("SELECT count(*) FROM write_claims WHERE task_id = ?", (args.task_id,)).fetchone()[0] == 0


def test_dispatch_requeues_twice_with_one_notice_to_its_initiator(tasks_dir, monkeypatch, capsys):
    """AC-02: timeout retries the guarded admission, never spawns an overlapping writer."""
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setenv("DELEGATE_OWNERSHIP_MODE", "refuse")
    monkeypatch.setenv("DELEGATE_OWNERSHIP_WAIT_S", "12")
    pid = os.getpid()
    _running_record(Path(os.environ["LEARN_UKRAINIAN_OWNERSHIP_TASK_STATE_DIR"]), "holder", pid=pid)
    assert ownership.admit_write_paths(
        task_id="holder", mode="workspace-write", owned_paths=["scripts/pkg/a.py"], pid=pid
    ).admitted
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tasks_dir / "fleet"))
    now = [1_000_000.0]
    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds
        if sum(slept) >= 30:
            ledger = ownership.OwnershipLedger()
            ledger.release("holder", pid=pid)
            # Simulate an existing peer with unknown intent at the next admission.
            with ledger._connect() as conn:
                conn.execute("INSERT INTO write_claims VALUES (?,?,?,?)", (
                    "unknown", json.dumps(ownership.normalize_claim("scripts/*").as_dict()),
                    pid, ownership.time.time(),
                ))

    monkeypatch.setattr(ownership, "_sleep", fake_sleep, raising=False)
    monkeypatch.setattr(ownership, "_clock", lambda: now[0], raising=False)
    monkeypatch.setattr(ownership, "_monotonic", lambda: now[0], raising=False)
    monkeypatch.setattr(
        delegate.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("queued writer must not spawn")
    )
    args = _live_danger_args(tasks_dir, "same-file-waiter")
    args.owned_path = ["scripts/pkg/a.py"]
    args.initiator = "claude-infra"

    assert delegate.cmd_dispatch(args) == 2

    err = capsys.readouterr().err
    assert "write-path ownership: queued behind holder" in err
    assert "cannot prove write-path disjointness" in err
    assert sum(slept) == pytest.approx(34.0)
    from scripts.fleet_comms.authority import AuthorityService

    with AuthorityService(root=tasks_dir / "fleet") as service:
        rows = service._conn.execute("SELECT recipient FROM authority_deliveries").fetchall()
        assert [row[0] for row in rows] == ["claude-infra"]
        message = service._conn.execute("SELECT message_id FROM comms_messages").fetchone()
        assert "re-queued" in service.read_message_body(message[0])
    assert not delegate._state_path(args.task_id).exists()
    with ownership.OwnershipLedger()._connect() as conn:
        assert conn.execute("SELECT count(*) FROM write_claims WHERE task_id = ?", (args.task_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM write_waiters").fetchone()[0] == 0
        events = [json.loads(row[0]) for row in conn.execute(
            "SELECT payload FROM admission_events WHERE task_id = ? AND event = 'requeued'", (args.task_id,),
        )]
        assert len(events) == 2
        assert events[0]["ticket"] < events[1]["ticket"]
