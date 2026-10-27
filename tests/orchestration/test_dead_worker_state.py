"""Namespace and start-time evidence for worker liveness (#10621)."""

from __future__ import annotations

import os

import pytest

from scripts.orchestration import dead_worker_state as d


def _stat(pid, start, state="S"):
    return f"{pid} (worker (with spaces)) " + " ".join([state] + ["0"] * 18 + [str(start)])


@pytest.fixture
def proc(tmp_path, monkeypatch):
    root = tmp_path / "proc"
    for pid, number in (("self", os.getpid()), ("1", 1), ("123", 123)):
        directory = root / pid
        (directory / "ns").mkdir(parents=True)
        (directory / "stat").write_text(_stat(number, 100))
        (directory / "ns" / "pid").symlink_to(d.INITIAL_PID_NAMESPACE)
    monkeypatch.setattr(d, "PROC_ROOT", root)
    return root


def _record():
    return {"pid": 123, "worker_identity": {
        "pid": 123, "host_pid": 123, "start_time": 100,
        "pid_namespace": d.INITIAL_PID_NAMESPACE,
        "recorder_pid_namespace": d.INITIAL_PID_NAMESPACE,
    }}


@pytest.mark.parametrize("schema", [None, 1, 2])
def test_matching_start_time_proves_alive_even_when_signal_probe_reports_absent(proc, monkeypatch, schema):
    from scripts.dispatcher import worker

    monkeypatch.setattr(worker, "_identity", lambda pid: "boot:100")
    record = _record() if schema != 2 else {"pid": 123, "process_start": "boot:100"}
    if schema is not None:
        record["schema_version"] = schema
    assert d.worker_liveness(record, pid_alive=lambda pid: False) is True


@pytest.mark.parametrize("bad_stat", ["malformed", None])
def test_unreadable_start_time_is_unknown(proc, bad_stat):
    path = proc / "123" / "stat"
    if bad_stat is None:
        path.unlink()
    else:
        path.write_text(bad_stat)
    assert d.worker_liveness(_record()) is None


@pytest.mark.parametrize("schema", [None, 1, 2])
def test_pid_reuse_is_dead(proc, monkeypatch, schema):
    from scripts.dispatcher import worker

    (proc / "123" / "stat").write_text(_stat(123, 101))
    monkeypatch.setattr(worker, "_identity", lambda pid: "boot:101")
    record = _record() if schema != 2 else {"pid": 123, "process_start": "boot:100"}
    if schema is not None:
        record["schema_version"] = schema
    assert d.worker_liveness(record, pid_alive=lambda pid: True) is False


@pytest.mark.parametrize("identity", [True, False])
@pytest.mark.parametrize("state,alive", [("Z", False), ("S", True), ("R", True)])
def test_zombie_supervisor_does_not_keep_a_clean_settled_tree(proc, identity, state, alive):
    (proc / "123" / "stat").write_text(_stat(123, 100, state))
    record = _record() if identity else {"pid": 123}
    assert d.worker_liveness(record, pid_alive=lambda _pid: True) is alive


@pytest.mark.parametrize("identity", [True, False])
@pytest.mark.parametrize("entry", [PermissionError(), FileNotFoundError(), UnicodeError(), "broken"])
def test_zombie_supervisor_unreadable_stat_fails_closed(proc, monkeypatch, identity, entry):
    from pathlib import Path

    read_text = Path.read_text
    def read_stat(path, *args, **kwargs):
        if path == proc / "123" / "stat":
            if isinstance(entry, Exception):
                raise entry
            return entry
        return read_text(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", read_stat)
    record = _record() if identity else {"pid": 123}
    assert d.worker_liveness(record, pid_alive=lambda _pid: True) is (None if identity else True)


@pytest.mark.parametrize("identity_case,gone", [("foreign", False), ("reused", True), ("alive", False), ("invalid", False)])
def test_dispatcher_owner_uses_namespace_and_start_time(proc, identity_case, gone):
    from scripts.orchestration.worktree_prep import owner_gone

    identity = _record()["worker_identity"]
    if identity_case == "foreign":
        identity["pid_namespace"] = "pid:[999999]"
    elif identity_case == "reused":
        identity["start_time"] -= 1
    assert owner_gone({
        "owner_pid": 123, "owner_start": 100,
        "owner_identity": None if identity_case == "invalid" else identity,
    }) is gone


@pytest.mark.parametrize("schema", [None, 1, 2])
@pytest.mark.parametrize("process_start", [None, "boot:100"])
def test_missing_same_namespace_process_is_dead(proc, schema, process_start):
    record = {"pid": 999_999_998, "worker_identity": {**_record()["worker_identity"], "pid": 999_999_998}}
    if schema is not None:
        record.update(schema_version=schema, process_start=process_start)
    assert d.worker_liveness(record) is False


def test_legacy_record_is_unknown_in_foreign_namespace(proc):
    link = proc / "self" / "ns" / "pid"
    link.unlink()
    link.symlink_to("pid:[999999]")
    assert d.worker_liveness({"pid": 456}, pid_alive=lambda pid: False) is None


def test_capture_host_identity(proc):
    identity = d.capture_worker_identity(123)
    assert identity == _record()["worker_identity"]


def test_worker_captures_host_proc_pid_instead_of_sandbox_getpid(proc, monkeypatch):
    monkeypatch.setattr(d.os, "getpid", lambda: 223)
    identity = d.capture_worker_identity(223, self_process=True)
    assert identity["pid"] == int((proc / "self" / "stat").read_text().split()[0])
    assert identity["host_pid"] == identity["pid"]
    assert identity["start_time"] == 100


def test_nested_proc_capture_does_not_invent_host_pid(proc):
    for pid in ("self", "1"):
        link = proc / pid / "ns" / "pid"
        link.unlink()
        link.symlink_to("pid:[999999]")
    identity = d.capture_worker_identity(123)
    assert identity["host_pid"] is None
    assert identity["pid_namespace"] == "pid:[999999]"
    assert d.worker_liveness({"pid": 123, "worker_identity": identity}) is True


def test_missing_namespace_evidence_is_unknown(proc):
    (proc / "self" / "ns" / "pid").unlink()
    assert d.worker_liveness(_record()) is None


def test_foreign_matching_pid_and_start_are_still_unknown(proc):
    record = _record()
    record["worker_identity"]["pid_namespace"] = "pid:[999999]"
    assert d.worker_liveness(record) is None


@pytest.mark.parametrize("foreign", [True, False])
@pytest.mark.parametrize("schema", [None, 1, 2])
@pytest.mark.parametrize("late_terminal", [False, True])
@pytest.mark.parametrize("marker", ["dead", "missing", "prep", "admission"])
def test_marker_rechecks_identity_before_writing_or_releasing_claim(
    proc, foreign, tmp_path, monkeypatch, schema, late_terminal, marker,
):
    import json
    from unittest.mock import Mock

    from scripts.dispatcher import store, worker

    record = {**_record(), "task_id": "worker", "status": "running", "run_nonce": "run",
              "worktree_path": str(tmp_path / "missing"), "worktree_prep": {}, "admission_hold": {}}
    if schema is not None:
        record.update(schema_version=schema, process_start="boot:100")
    if foreign:
        record["worker_identity"]["pid_namespace"] = "pid:[999999]"
    else:
        (proc / "123" / "stat").write_text(_stat(123, 101))
    if schema == 2:
        monkeypatch.setattr(worker, "_identity", lambda pid: "boot:101")
        if foreign:
            monkeypatch.setattr(d, "_pid_namespace", lambda *args: "pid:[999999]")
    path = tmp_path / "worker.json"
    path.write_text(json.dumps(record))
    before = path.read_bytes()
    done = {**record, "status": "done", "returncode": 0}
    ledger = Mock()
    write = Mock(wraps=d.write_state_unlocked)
    proof = Mock(return_value=not foreign)
    if late_terminal:
        monkeypatch.setattr(d, "worker_liveness", lambda *args, **kwargs: (store.replace(done, path), False)[1])
        proof = Mock(side_effect=lambda state: (store.replace(done, path), True)[1])
    if marker == "dead":
        current, changed = d.mark_dead_worker_terminal(
            path, record, source="admission", terminal_status="crashed",
            allowed_statuses=("running",), pid_alive=lambda pid: False,
            resolve_head=lambda path: None, ledger=ledger, write=write,
        )
    elif marker == "missing":
        current, changed = d.mark_missing_worktree_failed(
            path, record, pid_alive=lambda pid: False, ledger=ledger, write=write,
        )
    else:
        callback = d.mark_orphaned_worktree_prep_crashed if marker == "prep" else d.mark_orphaned_admission_hold_crashed
        kwargs = {"reason": "dispatch_died_after_admission"} if marker == "admission" else {}
        current, changed = callback(path, record, source="test", is_orphaned=proof, write=write, **kwargs)
    assert changed is (not foreign and not late_terminal)
    if late_terminal:
        assert current == done
        assert json.loads(path.read_text()) == done
        write.assert_not_called()
        ledger.release.assert_not_called()
    elif foreign:
        assert current["status"] == "running"
        assert path.read_bytes() == before
        write.assert_not_called()
        ledger.release.assert_not_called()
    else:
        assert current["status"] == ("failed" if marker == "missing" else "crashed")
        assert json.loads(path.read_text()) == current
        write.assert_called_once_with(path, current)
        if marker in ("dead", "missing"):
            ledger.release.assert_called_once_with("worker", pid=123)
        else:
            ledger.release.assert_not_called()


def test_pidless_dead_marker_does_not_release_unproven_worker_claim(proc, tmp_path):
    import json
    from unittest.mock import Mock

    record = {"task_id": "worker", "status": "running", "pid": None, "worker_identity": _record()["worker_identity"]}
    path = tmp_path / "worker.json"
    path.write_text(json.dumps(record))
    ledger = Mock()
    d.mark_dead_worker_terminal(
        path, record, source="admission", terminal_status="crashed",
        allowed_statuses=("running",), pid_alive=lambda pid: False,
        resolve_head=lambda path: None, ledger=ledger, write=d.write_state_unlocked,
    )
    ledger.release.assert_not_called()


@pytest.mark.parametrize("pid", [None, True, 0, -1, "not-a-pid"])
def test_invalid_pid_is_unknown(proc, pid):
    assert d.worker_liveness({"pid": pid}) is None


def test_capture_unreadable_identity_keeps_unknown_start_time(proc):
    (proc / "123" / "stat").write_text("malformed")
    identity = d.capture_worker_identity(123)
    assert identity["start_time"] is None
    assert d.worker_liveness({"pid": 123, "worker_identity": identity}) is None


def test_live_same_namespace_worker_hidden_from_proc_is_unknown(proc):
    # A restricted procfs view can omit a process in our own PID namespace.
    # Signal-0 still sees this real process, so absence is not proof of death.
    record = {"pid": os.getpid(), "worker_identity": {
        **_record()["worker_identity"], "pid": os.getpid(), "host_pid": os.getpid(),
    }}
    assert d.worker_liveness(record) is None


def test_confirmed_nested_namespace_dead_pid_ignores_legacy_unknown_callback(proc):
    for name in ("self", "1"):
        link = proc / name / "ns" / "pid"
        link.unlink()
        link.symlink_to("pid:[999999]")
    record = {"pid": 999_999_998, "worker_identity": {
        "pid": 999_999_998, "start_time": 100, "pid_namespace": "pid:[999999]",
    }}
    assert d.worker_liveness(record, pid_alive=lambda pid: True) is False
