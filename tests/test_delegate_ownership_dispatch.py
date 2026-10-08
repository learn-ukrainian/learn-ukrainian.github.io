"""#10015: directory ownership refuses the reviewer's live-dispatch reproduction."""

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
