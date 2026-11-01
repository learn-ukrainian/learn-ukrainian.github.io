"""Approved coverage for retention-hold clearing and cleanup inventory agreement."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.dispatcher import cli, git, store
from scripts.orchestration import scheduled_worktree_cleanup as cleanup


def test_clear_invalid_retention_hold_removes_disposition(tmp_path, monkeypatch, capsys):
    """A cleared malformed hold must not leave a non-retry invalid disposition."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    path = tmp_path / "held.json"
    base = {"schema_version": 2, "task_id": "held", "run_nonce": "same-run"}
    path.write_text(json.dumps(base))
    assert cli.main(["retain-worktree", "held", "--clear"]) == 0
    never_held = json.loads(path.read_text())
    capsys.readouterr()
    path.write_text(json.dumps({
        **base,
        "worktree_retention_hold": "false",
        "worktree_disposition": "retained",
        "worktree_disposition_reason": "retention_hold_invalid",
        "worktree_disposition_detail": "worktree_retention_hold must be a boolean; got 'false'",
    }))

    assert cli.main(["retain-worktree", "held", "--clear"]) == 0

    assert json.loads(capsys.readouterr().out) == {"task_id": "held", "worktree_retention_hold": False}
    assert json.loads(path.read_text()) == never_held


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("case", ["absent", "false", "true", "null", "string", "zero", "unreadable", "stale"])
def test_inventory_uses_dispatcher_retention_classification(tmp_path, monkeypatch, archived, case):
    """Malformed, unreadable and stale holds must protect the same inventory trees."""
    root = tmp_path / "repo"
    tree = root / ".worktrees" / "held"
    tree.mkdir(parents=True)
    tasks = root / "batch_state" / "tasks"
    directory = tasks / "archive" if archived else tasks
    directory.mkdir(parents=True)
    # Inventory must use its control plane, rather than this unrelated default.
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "unrelated"))
    monkeypatch.setattr(cleanup.worktree_git, "control_plane_root", lambda _root: root)
    path = directory / "held.json"
    record = {
        "schema_version": 2, "task_id": "held", "status": "failed",
        "finished_at": (datetime.now(UTC) - timedelta(hours=7)).isoformat(),
        "worktree_path": str(tree),
    }
    values = {"false": False, "true": True, "null": None, "string": "false", "zero": 0, "stale": True}
    if case in values:
        record["worktree_retention_hold"] = values[case]
    path.write_text(json.dumps(record))
    before = path.read_bytes()
    stale = dict(record)
    if case == "stale":
        stale.pop("worktree_retention_hold")
        monkeypatch.setattr(cleanup, "read_task_record", lambda _path: dict(stale))
    if case == "unreadable":
        real_read = Path.read_text

        def read_text(self, *args, **kwargs):
            if self == path:
                raise PermissionError("synthetic record read refusal")
            return real_read(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read_text)
    inspected = []

    def inspect(_tree, *args):
        inspected.append(args[0])
        return {"status": " M tracked.txt", "rev-list": "0", "rev-parse": "test/held"}[args[0]]

    monkeypatch.setattr(cleanup, "_inspect_terminal_git", inspect)
    report = cleanup.report_terminal_worktrees(root)
    expected_reason = {
        "absent": None, "false": None, "true": "retention_hold", "null": "retention_hold_invalid",
        "string": "retention_hold_invalid", "zero": "retention_hold_invalid",
        "unreadable": "task_record_damaged", "stale": "retention_hold",
    }[case]
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    if expected_reason is None:
        assert git._retention_held(stale) is False
        assert report["summary"] == {"candidate": 1}
        assert report["tasks"][0]["action"] == "report"
        assert inspected == ["status", "rev-list", "rev-parse"]
    else:
        disposition = git.settle_worktree(stale)
        assert disposition["worktree_disposition"] == "retained"
        assert disposition["worktree_disposition_reason"] == expected_reason
        assert report["summary"] == {"candidate": 0}
        if case == "unreadable":
            assert report["tasks"][0]["action"] == "error"
        else:
            assert report["tasks"] == []
        assert inspected == []
    assert path.read_bytes() == before
    assert tree.is_dir()
    assert cleanup.retention_hold_disposition is store.retention_hold_disposition
