"""The hot/archive task-record layout shared by every reader (#8625)."""

from __future__ import annotations

import json
import os
import threading

import pytest

from scripts.orchestration import task_record_store as store
from scripts.orchestration.dead_worker_state import task_state_lock, write_state_unlocked


def test_iter_task_records_yields_hot_then_archive(tmp_path):
    tasks = tmp_path / "tasks"
    (tasks / "archive").mkdir(parents=True)
    for path in (tasks / "b.json", tasks / "a.json", tasks / "archive" / "a.json", tasks / "archive" / "c.json"):
        path.write_text("{}", encoding="utf-8")
    (tasks / "a.result").write_text("reply", encoding="utf-8")
    (tasks / "nested.json").mkdir()  # a directory is never a record

    names = [str(path.relative_to(tasks)) for path in store.iter_task_records(tasks, include_archive=True)]
    assert names == ["a.json", "b.json", "archive/a.json", "archive/c.json"]
    hot = [path.name for path in store.iter_task_records(tasks, include_archive=False)]
    assert hot == ["a.json", "b.json"]
    assert list(store.iter_task_records(tmp_path / "missing", include_archive=True)) == []


def test_locate_prefers_the_hot_record(tmp_path):
    tasks = tmp_path / "tasks"
    archived = store.archived_task_record_path(tasks, "codex/task")
    archived.parent.mkdir(parents=True)
    archived.write_text("{}", encoding="utf-8")
    assert archived.name == "codex_task.json"
    assert store.locate_task_record(tasks, "codex/task") == archived
    hot = store.task_record_path(tasks, "codex/task")
    hot.write_text("{}", encoding="utf-8")
    assert store.locate_task_record(tasks, "codex/task") == hot
    assert store.locate_task_record(tasks, "absent") is None


def test_relocated_result_file_points_at_the_moved_sidecar(tmp_path):
    tasks = tmp_path / "tasks"
    archived = store.archived_task_record_path(tasks, "old")
    archived.parent.mkdir(parents=True)
    hot_result = str(tasks / "old.result")
    # Sidecar not moved (never had one): the recorded path is returned unchanged.
    assert store.relocated_result_file(archived, hot_result) == hot_result
    archived.with_suffix(".result").write_text("reply", encoding="utf-8")
    assert store.relocated_result_file(archived, hot_result) == str(archived.with_suffix(".result"))
    # Hot records and empty values are never rewritten.
    assert store.relocated_result_file(tasks / "old.json", hot_result) == hot_result
    assert store.relocated_result_file(archived, None) is None


def _write(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")


@pytest.mark.parametrize("archived", [False, True])
def test_update_located_record_merges_into_the_hot_or_archived_record(tmp_path, archived):
    tasks = tmp_path / "tasks"
    path = (store.archived_task_record_path if archived else store.task_record_path)(tasks, "review")
    _write(path, {"task_id": "review", "keep": 1})
    written = store.update_located_record(tasks, "review", lambda record: {**record, "added": 2})
    assert written == path
    assert json.loads(path.read_text()) == {"task_id": "review", "keep": 1, "added": 2}
    assert not store.task_record_path(tasks, "review").exists() or not archived


def test_update_returning_none_leaves_the_file_untouched(tmp_path):
    tasks = tmp_path / "tasks"
    path = store.task_record_path(tasks, "review")
    _write(path, {"task_id": "review"})
    os.utime(path, ns=(1, 1))
    store.update_located_record(tasks, "review", lambda record: None)
    assert path.stat().st_mtime_ns == 1


@pytest.mark.parametrize("content,reason", [(None, "not found"), ("{", "unreadable"), ("[]", "malformed")])
def test_missing_unreadable_or_malformed_record_refuses(tmp_path, content, reason):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    if content is not None:
        store.task_record_path(tasks, "review").write_text(content)
    with pytest.raises(store.TaskRecordUnavailable, match=reason):
        store.update_located_record(tasks, "review", lambda record: pytest.fail("update must not run"))


def test_update_refusal_propagates_without_writing(tmp_path):
    tasks = tmp_path / "tasks"
    path = store.task_record_path(tasks, "review")
    _write(path, {"task_id": "review"})

    def refuse(record):
        raise ValueError("conflict")

    with pytest.raises(ValueError, match="conflict"):
        store.update_located_record(tasks, "review", refuse)
    assert json.loads(path.read_text()) == {"task_id": "review"}


def test_record_archived_between_lookup_and_lock_is_located_again(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    hot = store.task_record_path(tasks, "review")
    archived = store.archived_task_record_path(tasks, "review")
    _write(hot, {"task_id": "review"})
    locate = store.locate_task_record
    calls = []

    def racing(directory, task_id):
        found = locate(directory, task_id)
        if not calls:
            # An archiver moves the record after lookup, before the lock.
            archived.parent.mkdir(parents=True, exist_ok=True)
            hot.rename(archived)
        calls.append(found)
        return found

    monkeypatch.setattr(store, "locate_task_record", racing)
    assert store.update_located_record(tasks, "review", lambda record: {**record, "added": 1}) == archived
    assert calls == [hot, archived]
    assert json.loads(archived.read_text()) == {"task_id": "review", "added": 1}
    assert not hot.exists()


def test_record_that_keeps_moving_refuses(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    ghost = store.task_record_path(tasks, "review")
    tasks.mkdir()
    monkeypatch.setattr(store, "locate_task_record", lambda directory, task_id: ghost)
    with pytest.raises(store.TaskRecordUnavailable, match="moved"):
        store.update_located_record(tasks, "review", lambda record: record)


def test_concurrent_updates_both_survive(tmp_path):
    tasks = tmp_path / "tasks"
    path = store.task_record_path(tasks, "review")
    _write(path, {"task_id": "review"})
    started = threading.Event()

    def update():
        started.set()
        store.update_located_record(tasks, "review", lambda record: {**record, "receipt": "bound"})

    with task_state_lock(path):
        worker = threading.Thread(target=update)
        worker.start()
        started.wait(5)
        record = json.loads(path.read_text())
        write_state_unlocked(path, {**record, "reaped": True})
    worker.join(10)
    assert not worker.is_alive()
    assert json.loads(path.read_text()) == {"task_id": "review", "reaped": True, "receipt": "bound"}
