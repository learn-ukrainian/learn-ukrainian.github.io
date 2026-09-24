"""The hot/archive task-record layout shared by every reader (#8625)."""

from __future__ import annotations

from scripts.orchestration import task_record_store as store


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
