"""The hot/archive task-record layout shared by every reader (#8625)."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

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

    names = (
        "codex_task.json", "codex_task.20261023T091234123Z.archived.json",
        "codex_task.20261023T091234Z.42.archived.json",
        "codex_task.20261023T091234Z.42.archived.20261023T101234Z.7.archived.json",
        "codex_task-extra.json", "codex_task.bad.archived.json", "codex_task.result",
    )
    expected = tuple(sorted(names[:4]))
    assert store.candidate_task_record_names("codex/task", names) == expected
    assert store.candidate_task_record_names("codex\\task", names) == expected
    # Pure filtering does not hide an unsafe matching filesystem entry.
    hot.unlink()
    hot.mkdir()
    assert store.candidate_task_record_names("codex/task", [hot.name]) == (hot.name,)
    assert store.candidate_task_record_names("other", names) == ()


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


@pytest.mark.parametrize("schema", [None, 2])
def test_shared_writer_atomically_sanitizes_records_without_importing_delegate(tmp_path, schema):
    """#11708: maintenance must preserve the cause sink without loading the retired CLI."""
    path = tmp_path / "worker.json"
    result = subprocess.run(
        [sys.executable, "-c", '''
import builtins
import json
import os
import stat
import sys
from pathlib import Path

original_import = builtins.__import__
def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if "delegate" in name.split(".") or "delegate" in (fromlist or ()):
        raise AssertionError("maintenance imported delegate")
    return original_import(name, globals, locals, fromlist, level)
builtins.__import__ = guarded_import

from scripts.orchestration import task_record_store as store

path = Path(sys.argv[1])
schema = json.loads(sys.argv[2])
record = {"task_id": "worker", "status": "crashed", "last_error": "raw private diagnostic"}
if schema is not None:
    record["schema_version"] = schema
path.write_text('{"status": "running"}')
before = path.read_bytes()
replace = os.replace
calls = []
def observed_replace(source, target):
    assert path.read_bytes() == before
    assert Path(source).parent == path.parent
    assert json.loads(Path(source).read_text())["last_error"] == "unclassified_error"
    calls.append(str(target))
    replace(source, target)
os.replace = observed_replace
with store.task_state_lock(path):
    store.write_record_unlocked(path, record)
assert calls == [str(path)]
assert record["last_error"] == "raw private diagnostic"
assert path.with_suffix(".json.lock").is_file()
assert not list(path.parent.glob("*.tmp.*"))
diagnostic = path.with_suffix(".diag")
assert stat.S_IMODE(diagnostic.stat().st_mode) == 0o600
entry = json.loads(diagnostic.read_text())
assert entry["diagnostic"] == "raw private diagnostic"
assert entry["source"] == "record"
assert not any(name == "delegate" or name.endswith(".delegate") for name in sys.modules)
print(path.read_text())
''', str(path), json.dumps(schema)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    expected = {"task_id": "worker", "status": "crashed", "last_error": "unclassified_error"}
    if schema is not None:
        expected["schema_version"] = schema
    assert json.loads(result.stdout) == expected
