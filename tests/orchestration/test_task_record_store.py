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


def test_locate_finds_a_record_restored_between_its_probes(tmp_path, monkeypatch):
    """A restore lands after the hot probe and before the archive probe (#10501)."""
    tasks = tmp_path / "tasks"
    archived = store.archived_task_record_path(tasks, "review")
    hot = store.task_record_path(tasks, "review")
    _write(archived, {"task_id": "review"})
    original = type(hot).is_file
    probes = []

    def is_file(self):
        found = original(self)
        probes.append((self, found))
        if self == hot and len(probes) == 1:
            os.link(archived, hot)  # The supported restore: link into the hot directory, then unlink.
            archived.unlink()
        return found

    monkeypatch.setattr(type(hot), "is_file", is_file)
    assert store.locate_task_record(tasks, "review") == hot
    assert probes == [(hot, False), (archived, False), (hot, True)]


@pytest.mark.parametrize(
    "build,name,kind",
    [
        ("staging", "review.json", "moving"),
        ("staging", "review.result", "moving"),
        ("parked", "review.json", "parked"),
        ("parked", "review.result", "parked"),
        ("staging", "review.snapshots", None),
        ("parked", "review.snapshots", None),
        ("plain", "review.json", None),
        ("plain", "review.json.lock", None),
        ("plain", "review.json.tmp.123", None),
        ("plain", ".review.json.moving", None),
        ("plain", "review.json.unplaced-xyz", None),
    ],
)
def test_relocation_residue_names_only_mid_move_records_and_replies(build, name, kind):
    builders = {"staging": store.staging_name, "parked": store.parked_name, "plain": lambda value: value}
    assert store.relocation_residue(builders[build](name)) == kind


def test_staging_and_parked_names_are_unique_per_call():
    assert store.staging_name("review.json") != store.staging_name("review.json")
    assert store.staging_name("review.json").startswith(f".review.json.{os.getpid()}.")
    assert store.parked_name("review.json") != store.parked_name("review.json")


# The store generation, a seqlock over every supported change (#10501).
@pytest.fixture(autouse=True)
def _fresh_generation_floor(monkeypatch):
    monkeypatch.setattr(store, "_GENERATION_FLOOR", {})


@pytest.fixture
def tasks(tmp_path):
    path = tmp_path / "tasks"
    path.mkdir()
    return path


def _generation_file(tasks):
    return tasks / store.CONTROL_DIR_NAME / store.GENERATION_NAME


def test_a_store_never_changed_reads_as_the_legacy_generation(tasks):
    assert store.read_generation(tasks) == store.LEGACY_GENERATION == (None, 0)
    assert not (tasks / store.CONTROL_DIR_NAME).exists()


def test_a_change_is_odd_while_it_runs_and_even_after(tasks):
    with store.store_change(tasks) as change:
        inside = store.read_generation(tasks)
        assert inside == change.generation and inside.value == 1 and change.repaired is None
        assert len(inside.epoch) == 16
    after = store.read_generation(tasks)
    assert after == (inside.epoch, 2)
    with store.store_change(tasks):
        pass
    assert store.read_generation(tasks) == (inside.epoch, 4)
    assert json.loads(_generation_file(tasks).read_text()) == {"epoch": inside.epoch, "generation": 4}


def test_a_change_that_raises_still_ends_even(tasks):
    with pytest.raises(RuntimeError, match="move failed"), store.store_change(tasks):
        raise RuntimeError("move failed")
    assert store.read_generation(tasks).value == 2


def test_the_next_writer_repairs_an_abandoned_change_and_proceeds(tasks):
    """Each writer holds the lock through its odd window, so an odd value under the lock is a dead writer's."""
    _generation_file(tasks).parent.mkdir()
    _generation_file(tasks).write_text(json.dumps({"epoch": "0123456789abcdef", "generation": 7}))
    with store.store_change(tasks) as change:
        assert change.repaired == "abandoned change at generation 7 closed"
        assert store.read_generation(tasks) == ("0123456789abcdef", 9)
    assert store.read_generation(tasks) == ("0123456789abcdef", 10)


@pytest.mark.parametrize("content", ["{", "[]", '{"epoch": "short", "generation": 4}'])
def test_the_next_writer_replaces_a_malformed_generation_with_a_new_epoch(tasks, content):
    _generation_file(tasks).parent.mkdir()
    _generation_file(tasks).write_text(content)
    with pytest.raises(store.TaskRecordUnavailable, match="malformed"):
        store.read_generation(tasks)
    with store.store_change(tasks) as change:
        assert change.repaired == "malformed generation replaced by a new epoch"
    generation = store.read_generation(tasks)
    assert generation.value == 2 and generation.epoch != "0123456789abcdef"


def test_writers_are_serialized_by_the_store_lock(tasks):
    entered, release, order = threading.Event(), threading.Event(), []

    def first():
        with store.store_change(tasks):
            order.append("first-in")
            entered.set()
            release.wait(5)
            order.append("first-out")

    def second():
        entered.wait(5)
        with store.store_change(tasks) as change:
            order.append(("second-in", change.generation.value))

    threads = [threading.Thread(target=first), threading.Thread(target=second)]
    for thread in threads:
        thread.start()
    entered.wait(5)
    assert store.read_generation(tasks).value == 1  # The second writer waits; nothing else bumped.
    release.set()
    for thread in threads:
        thread.join(5)
    assert order == ["first-in", "first-out", ("second-in", 3)]
    assert store.read_generation(tasks).value == 4


def test_a_symlinked_control_directory_is_unreadable_and_refused(tasks, tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (tasks / store.CONTROL_DIR_NAME).symlink_to(elsewhere)
    with pytest.raises(store.TaskRecordUnavailable, match="control directory"):
        store.read_generation(tasks)
    with pytest.raises(OSError), store.store_change(tasks):
        pass
    assert list(elsewhere.iterdir()) == []


def test_stable_read_returns_a_read_no_change_overlapped(tasks):
    with store.store_change(tasks):
        pass
    assert store.stable_read(tasks, lambda: "snapshot") == "snapshot"


def test_stable_read_retries_a_read_a_change_overlapped(tasks, monkeypatch):
    monkeypatch.setattr(store, "READ_BACKOFF_S", 0.0)
    reads = []

    def read():
        reads.append(1)
        if len(reads) == 1:
            with store.store_change(tasks):
                pass
        return len(reads)

    assert store.stable_read(tasks, read) == 2


def test_stable_read_exhaustion_keeps_the_last_read_as_partial(tasks, monkeypatch):
    monkeypatch.setattr(store, "READ_BACKOFF_S", 0.0)
    reads = []

    def read():
        reads.append(1)
        with store.store_change(tasks):
            pass
        return len(reads)

    with pytest.raises(store.StoreUnstable, match="changed while it was read") as error:
        store.stable_read(tasks, read)
    assert error.value.partial == store.READ_ATTEMPTS == len(reads)


def test_stable_read_never_reads_during_a_change(tasks, monkeypatch):
    monkeypatch.setattr(store, "READ_BACKOFF_S", 0.0)
    reads = []
    with store.store_change(tasks), pytest.raises(store.StoreUnstable, match="in progress") as error:
        store.stable_read(tasks, lambda: reads.append(1))
    assert reads == [] and error.value.partial is None


def test_stable_read_backs_off_between_attempts(tasks, monkeypatch):
    sleeps = []
    monkeypatch.setattr(store.time, "sleep", sleeps.append)
    with store.store_change(tasks), pytest.raises(store.StoreUnstable):
        store.stable_read(tasks, lambda: None)
    assert sleeps == [store.READ_BACKOFF_S, 2 * store.READ_BACKOFF_S]


@pytest.mark.parametrize("change", ["backwards", "new-epoch", "deleted"])
def test_stable_read_refuses_a_generation_reset_since_this_process_read_it(tasks, change):
    for _ in range(2):
        with store.store_change(tasks):
            pass
    assert store.stable_read(tasks, lambda: "ok") == "ok"
    epoch = store.read_generation(tasks).epoch
    if change == "backwards":
        _generation_file(tasks).write_text(json.dumps({"epoch": epoch, "generation": 2}))
    elif change == "new-epoch":
        _generation_file(tasks).write_text(json.dumps({"epoch": "f" * 16, "generation": 8}))
    else:
        _generation_file(tasks).unlink()
        (tasks / store.CONTROL_DIR_NAME / store.LOCK_NAME).unlink()
        (tasks / store.CONTROL_DIR_NAME).rmdir()
    with pytest.raises(store.StoreUnstable, match=r"reset|backwards"):
        store.stable_read(tasks, lambda: "ok")


def test_a_legacy_store_may_gain_its_first_generation(tasks):
    assert store.stable_read(tasks, lambda: "legacy") == "legacy"
    with store.store_change(tasks):
        pass
    assert store.stable_read(tasks, lambda: "changed") == "changed"


def test_the_receipt_write_is_a_store_change(tasks):
    path = tasks / "reviewed.json"
    _write(path, {"task_id": "reviewed", "status": "done"})
    seen = []

    def bind(record):
        seen.append(store.read_generation(tasks).value)
        return {**record, "cf_recording": {"schema": "cf-recording.v1"}}

    store.update_located_record(tasks, "reviewed", bind)
    assert seen == [1] and store.read_generation(tasks).value == 2
    assert json.loads(path.read_text())["cf_recording"] == {"schema": "cf-recording.v1"}
