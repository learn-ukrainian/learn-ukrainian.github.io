"""#9907: settle writers use delegate's public-cause sink, including without a callback."""

from __future__ import annotations

import argparse
import ast
import json
import stat
from pathlib import Path

import pytest

from scripts import delegate
from scripts.orchestration import dead_worker_state, dispatch_settle, task_record_causes

RAW_REASON = "synthetic settle diagnostic at private-worker.example.invalid"
DEFAULT_REASONS = {
    "dead-worker": "worker_process_dead",
    "missing-worktree": "worktree_missing_at_settle",
}


def _record(tmp_path: Path, writer: str, last_error: str | None, schema: int | None = None) -> tuple[Path, dict]:
    path = tmp_path / f"{writer}.json"
    state = {
        "task_id": writer,
        "status": "running",
        "pid": 999_999_999,
        "run_nonce": "attempt-1",
        "started_at": "2026-01-01T00:00:00Z",
        "worktree_path": str(tmp_path / "missing"),
        "require_review_verdict": True,
        "last_error": last_error,
        "finalize_error": RAW_REASON,
        "auto_finalize": {"error": RAW_REASON},
    }
    if schema is not None:
        state.update(schema_version=schema, process_start=None)
    path.write_text(json.dumps(state), encoding="utf-8")
    return path, state


def _assert_persisted(path: Path, writer: str, last_error: str | None) -> None:
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["status"] == "failed"
    assert record["exit_code"] == record["returncode"] == -9
    assert record["failure_reason"] == (
        "worker_process_dead" if writer == "dead-worker" else "worktree_missing_at_settle"
    )
    for field in delegate.PUBLIC_RECORD_REASON_FIELDS:
        if record.get(field) is not None:
            assert delegate.is_public_cause(record[field]), (field, record[field])
    assert record["last_error"] == (
        last_error if last_error == "worker_failed" else "unclassified_error" if last_error else DEFAULT_REASONS[writer]
    )
    assert record["finalize_error"] == record["auto_finalize"]["error"] == "unclassified_error"
    diagnostic = path.with_suffix(".diag")
    assert stat.S_IMODE(diagnostic.stat().st_mode) == 0o600
    entries = [json.loads(line) for line in diagnostic.read_text(encoding="utf-8").splitlines()]
    kept = {entry["field"]: entry["diagnostic"] for entry in entries}
    assert kept["finalize_error"] == kept["auto_finalize.error"] == RAW_REASON
    if not last_error or last_error == "worker_failed":
        assert "last_error" not in kept
    else:
        assert kept["last_error"] == last_error
    assert all(entry["source"] == "record" for entry in entries)


@pytest.mark.parametrize("last_error", [None, RAW_REASON, "worker_failed"])
@pytest.mark.parametrize("schema", [None, 1, 2])
def test_dead_worker_settle_persists_only_public_causes(tmp_path, monkeypatch, capsys, last_error, schema):
    path, _state = _record(tmp_path, "dead-worker", last_error, schema)
    monkeypatch.setattr(dispatch_settle, "_pid_alive", lambda _pid: False)

    assert dispatch_settle.heal_zombie_task(tmp_path, "dead-worker") == ["marked_failed_zombie_running"]

    _assert_persisted(path, "dead-worker", last_error)
    monkeypatch.setattr(delegate, "tasks_dir", lambda: tmp_path)
    assert delegate.cmd_status(argparse.Namespace(task_id="dead-worker", run_nonce=None)) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["last_error"] == json.loads(path.read_text(encoding="utf-8"))["last_error"]
    assert RAW_REASON not in json.dumps(shown)


@pytest.mark.parametrize("last_error", [None, RAW_REASON, "worker_failed"])
@pytest.mark.parametrize("schema", [None, 1, 2])
def test_missing_worktree_settle_persists_only_public_causes(tmp_path, monkeypatch, capsys, last_error, schema):
    path, _state = _record(tmp_path, "missing-worktree", last_error, schema)
    monkeypatch.setattr(dispatch_settle, "_pid_alive", lambda _pid: False)

    assert dispatch_settle.settle_missing_worktree(tmp_path, "missing-worktree") == ["marked_failed_missing_worktree"]

    _assert_persisted(path, "missing-worktree", last_error)
    monkeypatch.setattr(delegate, "tasks_dir", lambda: tmp_path)
    assert delegate.cmd_status(argparse.Namespace(task_id="missing-worktree", run_nonce=None)) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["last_error"] == json.loads(path.read_text(encoding="utf-8"))["last_error"]
    assert RAW_REASON not in json.dumps(shown)


@pytest.mark.parametrize("schema", [None, 1, 2])
@pytest.mark.parametrize("injected", [False, True])
def test_orphaned_default_writer_uses_the_same_sink(tmp_path, monkeypatch, schema, injected):
    from unittest.mock import Mock

    from scripts.dispatcher import store

    path, state = _record(tmp_path, "orphaned", RAW_REASON, schema)
    clock = Mock(wraps=dead_worker_state.datetime)
    clock.now.return_value = dead_worker_state.datetime(2026, 1, 1, tzinfo=dead_worker_state.UTC)
    monkeypatch.setattr(dead_worker_state, "datetime", clock)
    monkeypatch.setattr(task_record_causes, "datetime", clock)
    monkeypatch.setattr(delegate, "datetime", clock)
    replace = Mock(wraps=store.replace)
    monkeypatch.setattr(store, "replace", replace)
    write = Mock(wraps=delegate._write_record_unlocked) if injected else None
    current, changed = dead_worker_state._mark_orphaned_pidless_crashed(
        path,
        state,
        is_orphaned=lambda _state: True,
        reason="dispatch_died_during_worktree_prep",
        excerpt=lambda _state, _prior: "dispatcher died",
        write=write,
    )
    assert changed
    if injected:
        write.assert_called_once_with(path, current)
    elif schema == 2:
        replace.assert_called_once()
        assert replace.call_args.args[1] == path
    else:
        replace.assert_not_called()
    expected_path = tmp_path / "expected.json"
    delegate._write_record_unlocked(expected_path, current)
    if schema != 2 or injected:
        assert path.read_bytes() == expected_path.read_bytes()
    else:
        assert json.loads(path.read_text()) == json.loads(expected_path.read_text())
    assert path.with_suffix(".diag").read_bytes() == expected_path.with_suffix(".diag").read_bytes()
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["status"] == "crashed"
    assert record["last_error"] == "unclassified_error"
    entries = [json.loads(line) for line in path.with_suffix(".diag").read_text(encoding="utf-8").splitlines()]
    assert any(entry["field"] == "last_error" and entry["diagnostic"] == RAW_REASON for entry in entries)


def test_settle_default_writers_cannot_bypass_the_public_cause_sink():
    """Extend #9878's delegate sink enumeration to the external settle writers."""
    tree = ast.parse(Path(dead_worker_state.__file__).read_text(encoding="utf-8"))
    writers = {}
    for function in tree.body:
        if not isinstance(function, ast.FunctionDef):
            continue
        for call in ast.walk(function):
            if not isinstance(call, ast.Call):
                continue
            if isinstance(call.func, ast.Name):
                assert call.func.id != "write_state_unlocked", function.name
            elif isinstance(call.func, ast.BoolOp):
                writers[function.name] = ast.unparse(call.func)
    assert writers == {
        "_replace_if_unchanged": "write or write_record_unlocked",
    }
