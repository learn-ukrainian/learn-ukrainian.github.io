"""Sources store generations: publication under live readers and writers.

Every interleaving is coordinated with events between real processes (never
sleeps): a reader or writer pauses at a named point, the parent publishes, and
the paused process continues. All stores are synthetic and live under tmp_path.
"""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.lib.readonly_sqlite import CorpusDatabaseWriteRefused, open_readonly, refuse_writable_corpus_database
from scripts.storage import cli as storage_cli
from scripts.storage import generations
from scripts.storage import topology as storage_topology
from tests.test_sources_db import sample_data, sources_report_log_dir  # noqa: F401  (fixtures)

SPAWN = multiprocessing.get_context("spawn")
WAIT = 60  # an event that never fires fails the test instead of hanging it


@pytest.fixture(autouse=True)
def _no_disk_margin(monkeypatch):
    # The real margin (generation + 10 GiB + 4 GiB) is tested on its own below.
    monkeypatch.setenv("LU_EVIDENCE_FREE_DISK_FLOOR_BYTES", "0")
    monkeypatch.setenv("LU_EVIDENCE_WAL_CEILING_BYTES", "0")
    monkeypatch.delenv(generations.ENV_WRITER_FD, raising=False)
    monkeypatch.delenv(generations.ENV_WRITER_SELECTOR, raising=False)


def _legacy_store(selector: Path, value: str = "g0") -> Path:
    selector.parent.mkdir(parents=True, exist_ok=True)
    seed = selector.with_name("seed.db")
    with closing(sqlite3.connect(seed)) as conn:
        assert conn.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        conn.execute("CREATE TABLE t (v TEXT)")
        conn.execute("CREATE TABLE w (v TEXT)")
        conn.execute("INSERT INTO t VALUES (?)", (value,))
        conn.commit()
    seed.rename(selector)
    generations.hold_database(selector)
    return selector


@pytest.fixture
def selector(tmp_path) -> Path:
    path = _legacy_store(tmp_path / "data" / "sources.db")
    with generations.writer_lock(path) as held:
        generations.checkpoint_legacy_store(held)
        generations.publish_generation(path, held, mode="bootstrap")
    return path


def _value(path: Path) -> str:
    with closing(open_readonly(path)) as conn:
        return conn.execute("SELECT v FROM t").fetchone()[0]


def _stage(held: generations.HeldWriter, value: str) -> Path:
    """A candidate built from the generation the lock holder sees, with ``t`` changed."""
    stage = held.data_dir / f"stage-{value}.db"
    with closing(open_readonly(held.generation)) as source, closing(sqlite3.connect(stage)) as target:
        source.backup(target)
        target.execute("UPDATE t SET v = ?", (value,))
        target.commit()
    return stage


def publish(selector: Path, value: str, *, now: datetime | None = None) -> generations.Publication:
    with generations.writer_lock(selector) as held:
        return generations.publish_generation(_stage(held, value), held, now=now)


# --- child processes (module level so the spawn context can import them) ---------------


def reader_child(selector: str, point: str, ready, go, out) -> None:
    try:
        if point == "resolved":
            generation = Path(selector).resolve()
            ready.set()
            assert go.wait(WAIT)
            out.put(_value(generation))
        elif point == "opened":
            with closing(open_readonly(selector)) as conn:
                ready.set()
                assert go.wait(WAIT)
                out.put(conn.execute("SELECT v FROM t").fetchone()[0])
        else:
            with closing(open_readonly(selector, isolation_level=None)) as conn:
                conn.execute("BEGIN")
                first = conn.execute("SELECT v FROM t").fetchone()[0]
                ready.set()
                assert go.wait(WAIT)
                second = conn.execute("SELECT v FROM t").fetchone()[0]
                conn.execute("COMMIT")
                out.put(f"{first}|{second}")
    except BaseException as error:  # report, so the parent fails with the cause
        ready.set()
        out.put(f"error:{error!r}")


def _write_row(target: Path, value: str) -> None:
    # A declared store writer opens the connection, so the guard sees the lock.
    from scripts.lexicon.runner.fetch_ulif_homonyms import prepare_database

    conn = prepare_database(target)
    try:
        conn.execute("INSERT INTO w VALUES (?)", (value,))
        conn.commit()
    finally:
        conn.close()


def stale_writer_child(selector: str, ready, go, out) -> None:
    try:
        stale = Path(selector).resolve()
        ready.set()
        assert go.wait(WAIT)
        try:
            _write_row(stale, "stale")
            out.put("stale-open-allowed")
        except CorpusDatabaseWriteRefused as error:
            out.put(f"refused:{error}")
        with generations.store_writer(selector) as target:
            _write_row(target, "late")
            out.put(f"wrote:{target.name}")
    except BaseException as error:
        out.put(f"error:{error!r}")


def locked_writer_child(selector: str, ready, go, out) -> None:
    try:
        with generations.store_writer(selector) as target:
            _write_row(target, "under-lock")
            ready.set()
            assert go.wait(WAIT)
        out.put("released")
    except BaseException as error:
        ready.set()
        out.put(f"error:{error!r}")


def _run(target, *args):
    ready, go, out = SPAWN.Event(), SPAWN.Event(), SPAWN.Queue()
    process = SPAWN.Process(target=target, args=(*args, ready, go, out))
    process.start()
    assert ready.wait(WAIT)
    return process, go, out


def _finish(process, go, out, count: int = 1) -> list[str]:
    go.set()
    results = [out.get(timeout=WAIT) for _ in range(count)]
    process.join(WAIT)
    assert process.exitcode == 0
    assert not any(str(r).startswith("error:") for r in results), results
    return results


# --- layout and selector ---------------------------------------------------------------


def test_bootstrap_makes_the_legacy_file_the_first_generation(tmp_path):
    selector = _legacy_store(tmp_path / "data" / "sources.db")
    inode = selector.stat().st_ino
    with generations.writer_lock(selector) as held:
        generations.checkpoint_legacy_store(held)
        publication = generations.publish_generation(selector, held, mode="bootstrap")
    assert selector.is_symlink()
    assert os.readlink(selector) == f"sources-generations/{publication.generation.name}"
    assert publication.generation.stat().st_ino == inode  # the same file, not a copy
    assert generations.is_held(publication.generation)
    assert not Path(f"{selector}-wal").exists() and not Path(f"{selector}-shm").exists()
    assert generations.read_receipt(publication.generation)["state"] == "published"
    assert _value(selector) == "g0"


def test_publication_refuses_a_regular_file_except_in_bootstrap(tmp_path):
    selector = _legacy_store(tmp_path / "data" / "sources.db")
    with generations.writer_lock(selector) as held:
        with pytest.raises(generations.GenerationError, match="selector_is_regular_file"):
            generations.publish_generation(_stage(held, "g1"), held)
    assert not selector.is_symlink()


def test_bootstrap_refuses_while_an_idle_reader_is_connected(tmp_path):
    selector = _legacy_store(tmp_path / "data" / "sources.db")
    with closing(open_readonly(selector)) as reader:
        assert reader.execute("SELECT v FROM t").fetchone() == ("g0",)  # connected, no transaction
        with generations.writer_lock(selector) as held:
            with pytest.raises(generations.GenerationError, match="store_in_use"):
                generations.checkpoint_legacy_store(held)
    assert not selector.is_symlink()


def test_bootstrap_refuses_while_a_reader_holds_a_transaction(tmp_path):
    selector = _legacy_store(tmp_path / "data" / "sources.db")
    with closing(open_readonly(selector, isolation_level=None)) as reader:
        reader.execute("BEGIN")
        reader.execute("SELECT v FROM t").fetchone()
        generations.lift_database(selector)
        with closing(sqlite3.connect(selector)) as writer:
            writer.execute("INSERT INTO w VALUES ('pending')")
            writer.commit()
            with generations.writer_lock(selector) as held, pytest.raises(generations.GenerationError):
                generations.checkpoint_legacy_store(held)
        reader.execute("COMMIT")
    assert not selector.is_symlink()


@pytest.mark.parametrize("text,reason", [
    ("/abs/sources-generations/sources.20260101T000000Z-0123456789ab.db", "selector_target_outside_generations"),
    ("../sources-generations/sources.20260101T000000Z-0123456789ab.db", "selector_target_outside_generations"),
    ("sources-generations/other.db", "selector_target_outside_generations"),
    ("sources-generations/sources.20260101T000000Z-0123456789ab.db", "selected_generation_missing"),
])
def test_selector_is_confined_to_the_generation_directory(tmp_path, text, reason):
    data = tmp_path / "data"
    (data / "sources-generations").mkdir(parents=True)
    (data / "sources.db").symlink_to(text)
    state = generations.inspect_selector(data / "sources.db")
    assert (state.layout, state.reason) == ("invalid", reason)
    with pytest.raises(generations.GenerationError, match=reason):
        with generations.writer_lock(data / "sources.db"):
            pass


def test_generation_directory_must_be_real(tmp_path, selector):
    elsewhere = tmp_path / "elsewhere"
    (selector.parent / "sources-generations").rename(elsewhere)
    (selector.parent / "sources-generations").symlink_to(elsewhere)
    assert generations.inspect_selector(selector).reason == "generations_dir_not_real_directory"


# --- readers ---------------------------------------------------------------------------


@pytest.mark.parametrize("point", ["resolved", "opened", "transaction"])
def test_paused_readers_see_only_their_generation_across_publications(selector, point):
    expected_old = "g0"
    for step in range(1, 4):
        value = f"g{step}"
        process, go, out = _run(reader_child, str(selector), point)
        publish(selector, value)
        assert _value(selector) == value  # a new open sees only the new generation
        [result] = _finish(process, go, out)
        assert result == (f"{expected_old}|{expected_old}" if point == "transaction" else expected_old)
        expected_old = value


def test_sidecars_stay_with_their_generation(selector):
    old = selector.resolve()
    with closing(open_readonly(selector, isolation_level=None)) as held_reader:
        # A first read attaches the reader to the WAL index, so the writer's
        # close is not the last one and does not checkpoint the WAL away.
        assert held_reader.execute("SELECT v FROM t").fetchone()[0] == "g0"
        with generations.store_writer(selector) as target:
            from scripts.lexicon.runner.fetch_ulif_homonyms import prepare_database

            conn = prepare_database(target)
            conn.execute("PRAGMA wal_autocheckpoint=0")
            conn.execute("UPDATE t SET v = 'committed-in-wal'")
            conn.commit()
            conn.close()
        assert Path(f"{old}-wal").stat().st_size > 0  # committed pages still in the WAL
        held_reader.execute("BEGIN")
        assert held_reader.execute("SELECT v FROM t").fetchone()[0] == "committed-in-wal"
        with generations.writer_lock(selector) as held:
            stage = held.data_dir / "stage.db"
            with closing(open_readonly(held.generation)) as source, closing(sqlite3.connect(stage)) as copy:
                source.backup(copy)
            new = generations.publish_generation(stage, held).generation
        assert not Path(f"{new}-wal").exists() and not Path(f"{new}-shm").exists()
        with generations.store_writer(selector) as target:
            _write_row(target, "only-new")
        assert held_reader.execute("SELECT COUNT(*) FROM w").fetchone()[0] == 0
        held_reader.execute("COMMIT")
    assert Path(f"{old}-wal").stat().st_size > 0
    with closing(open_readonly(selector)) as fresh:
        assert fresh.execute("SELECT v FROM t").fetchone()[0] == "committed-in-wal"
        assert fresh.execute("SELECT v FROM w").fetchall() == [("only-new",)]
    with closing(open_readonly(old)) as previous:
        assert previous.execute("SELECT COUNT(*) FROM w").fetchone()[0] == 0


# --- writers ---------------------------------------------------------------------------


def test_writer_that_resolved_before_a_switch_is_refused_then_reresolves(selector):
    process, go, out = _run(stale_writer_child, str(selector))
    new = publish(selector, "g1").generation
    refused, wrote = _finish(process, go, out, count=2)
    assert refused.startswith("refused:") and "writer_lock_not_held" in refused
    assert wrote == f"wrote:{new.name}"
    with closing(open_readonly(selector)) as conn:
        assert conn.execute("SELECT v FROM w").fetchall() == [("late",)]


def test_publication_refuses_while_a_writer_holds_the_lock(selector):
    process, go, out = _run(locked_writer_child, str(selector))
    with pytest.raises(generations.GenerationError, match="writer_lock_busy"):
        publish(selector, "g1")
    assert _finish(process, go, out) == ["released"]
    publish(selector, "g1")
    with closing(open_readonly(selector)) as conn:  # built from the current generation
        assert conn.execute("SELECT v FROM w").fetchall() == [("under-lock",)]


def test_publication_refuses_when_the_current_generation_changed_under_the_lock(selector):
    with generations.writer_lock(selector) as held:
        stage = _stage(held, "g1")
        info = held.generation.stat()
        os.utime(held.generation, ns=(info.st_atime_ns, info.st_mtime_ns + 1))
        with pytest.raises(generations.GenerationError, match="current_generation_changed"):
            generations.publish_generation(stage, held)
    assert _value(selector) == "g0"


def test_writable_open_needs_the_lock_and_the_selected_generation(selector):
    old = selector.resolve()
    for path in (selector, old):
        with pytest.raises(CorpusDatabaseWriteRefused, match="writer_lock_not_held"):
            _write_row(path, "unlocked")
    with pytest.raises(CorpusDatabaseWriteRefused, match=r"corpus database sources\.db"):
        refuse_writable_corpus_database(old)  # no declared writer on the stack
    publish(selector, "g1")
    with generations.writer_lock(selector):
        assert generations.writable_open_refusal(selector) is None
        assert generations.writable_open_refusal(selector.resolve()) is None
        assert generations.writable_open_refusal(old) == "not_selected_generation"
    with pytest.raises(generations.GenerationError, match="generation_named_directly"):
        with generations.store_writer(old):
            pass


def test_lock_release_closes_tracked_connections_and_holds_again(selector):
    from scripts.lexicon.runner.fetch_ulif_homonyms import prepare_database

    with generations.store_writer(selector) as target:
        assert not generations.is_held(target)
        conn = prepare_database(target)
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")
    assert generations.is_held(target)


# --- failure injection -----------------------------------------------------------------


def test_failure_while_persisting_the_generation_keeps_the_old_selection(selector, monkeypatch):
    real = generations._fsync_path

    def fail_on_generation(path, *, directory=False):
        if not directory and generations.is_generation_name(Path(path).name):
            raise OSError("injected fsync failure")
        real(path, directory=directory)

    now = datetime(2026, 1, 1, tzinfo=UTC)
    with generations.writer_lock(selector) as held:
        stage = _stage(held, "g1")
        monkeypatch.setattr(generations, "_fsync_path", fail_on_generation)
        with pytest.raises(OSError, match="injected"):
            generations.publish_generation(stage, held, now=now)
        assert _value(selector) == "g0"
        monkeypatch.setattr(generations, "_fsync_path", real)
        publication = generations.publish_generation(stage, held, now=now)  # the retry reuses its link
    assert _value(selector) == "g1" and not stage.exists()
    assert generations.read_receipt(publication.generation)["state"] == "published"


def test_failure_replacing_the_selector_keeps_the_old_selection(selector, monkeypatch):
    real = os.replace

    def fail_on_selector(source, target):
        if Path(target) == selector:
            raise OSError("injected replace failure")
        real(source, target)

    with generations.writer_lock(selector) as held:
        stage = _stage(held, "g1")
        monkeypatch.setattr(generations.os, "replace", fail_on_selector)
        with pytest.raises(OSError, match="injected"):
            generations.publish_generation(stage, held)
        monkeypatch.setattr(generations.os, "replace", real)
    assert _value(selector) == "g0"
    assert not list(selector.parent.glob(".sources.db.*.link"))
    staged = [row for row in generations.generation_status(selector)["generations"] if not row["selected"]]
    assert [row["receipt_state"] for row in staged] == ["staged"]  # an orphan, never selected


def test_failure_completing_the_receipt_after_the_switch_is_recovered(selector, monkeypatch):
    real = generations._complete_receipt
    first = publish(selector, "g1").generation

    def fail_for(generation):
        if generation != first:
            raise OSError("injected receipt failure")
        real(generation)

    with generations.writer_lock(selector) as held:
        stage = _stage(held, "g2")
        monkeypatch.setattr(generations, "_complete_receipt", fail_for)
        with pytest.raises(OSError, match="injected"):
            generations.publish_generation(stage, held, now=datetime.now(UTC) + timedelta(seconds=1))
    monkeypatch.setattr(generations, "_complete_receipt", real)
    assert _value(selector) == "g2"  # the switch is the commit point
    second = selector.resolve()
    assert generations.read_receipt(second)["state"] == "staged"
    publish(selector, "g3", now=datetime.now(UTC) + timedelta(seconds=2))
    assert generations.read_receipt(second)["state"] == "published"
    assert generations.read_receipt(selector.resolve())["previous"] == second.name


def test_publication_refuses_without_free_space(selector, monkeypatch):
    monkeypatch.delenv("LU_EVIDENCE_FREE_DISK_FLOOR_BYTES")
    monkeypatch.delenv("LU_EVIDENCE_WAL_CEILING_BYTES")
    usage = generations.shutil.disk_usage(selector.parent)
    margin = 14 * 1024**3
    monkeypatch.setattr(generations.shutil, "disk_usage", lambda path: usage._replace(free=margin))
    with pytest.raises(generations.GenerationError, match="insufficient_free_space"):
        publish(selector, "g1")
    assert _value(selector) == "g0"


# --- hold, lift, write, rebuild --------------------------------------------------------


def test_lift_and_hold_act_on_the_selected_generation_under_the_lock(selector, capsys):
    old = selector.resolve()
    assert storage_cli.main(["lift", str(selector)]) == 0
    assert not generations.is_held(old)
    with pytest.raises(generations.GenerationError, match="current_generation_writable"):
        publish(selector, "g1")
    assert storage_cli.main(["hold", str(selector)]) == 0
    assert storage_cli.main(["lift", str(old)]) == 3
    assert "generation_named_directly" in capsys.readouterr().err
    with generations.writer_lock(selector):
        assert storage_cli.main(["hold", str(selector)]) == 3


def test_write_runs_a_writer_with_the_inherited_lock(selector, tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).resolve().parents[1]))
    out = tmp_path / "child.txt"
    probe = (
        "import sys, pathlib; from scripts.storage import generations; "
        "pathlib.Path(sys.argv[2]).write_text(str(generations.writable_open_refusal(sys.argv[1])))"
    )
    command = [sys.executable, "-c", probe, str(selector), str(out)]
    subprocess.run(command, check=True, timeout=WAIT)
    assert out.read_text() == "writer_lock_not_held"
    assert storage_cli.main(["write", "--store", str(selector), "--", *command]) == 0
    assert out.read_text() == "None"
    assert generations.is_held(selector.resolve())  # held again after the writer


def test_rebuild_publishes_a_generation_and_refuses_the_legacy_live_file(
    tmp_path, sample_data, monkeypatch, sources_report_log_dir  # noqa: F811
):
    import wiki.build_sources_db as bdb

    monkeypatch.setattr(bdb, "PROJECT_ROOT", sample_data["project_root"])
    inputs = (sample_data["ext_dir"], sample_data["tb_dir"], sample_data["gdrive"])
    data = tmp_path / "store"
    data.mkdir()
    legacy = data / "sources.db"
    bdb.build(legacy, *inputs)  # an ordinary path: the in-place build is unchanged
    monkeypatch.setattr(storage_topology, "live_store_path", lambda: legacy)
    with pytest.raises(generations.GenerationError, match="rebuild_requires_selector"):
        bdb.build(legacy, *inputs, force=True)
    generations.hold_database(legacy, strict=False)
    with generations.writer_lock(legacy) as held:
        generations.checkpoint_legacy_store(held)
        # The rebuild below is byte-identical; an earlier stamp keeps its name distinct.
        generations.publish_generation(legacy, held, mode="bootstrap", now=datetime(2026, 1, 1, tzinfo=UTC))
    old = legacy.resolve()
    from scripts.lexicon.runner.fetch_ulif_homonyms import prepare_database

    with generations.store_writer(legacy) as target:
        conn = prepare_database(target)
        conn.execute("CREATE TABLE marker (v TEXT)")
        conn.execute("INSERT INTO marker VALUES ('old generation')")
        conn.commit()
        conn.close()
    with closing(open_readonly(legacy, isolation_level=None)) as reader:
        reader.execute("BEGIN")
        assert reader.execute("SELECT v FROM marker").fetchone()[0] == "old generation"
        bdb.build(legacy, *inputs, force=True)
        assert legacy.resolve() != old and legacy.is_symlink()
        assert reader.execute("SELECT v FROM marker").fetchone()[0] == "old generation"
        reader.execute("COMMIT")
    with closing(open_readonly(legacy)) as fresh:
        assert not fresh.execute("SELECT name FROM sqlite_master WHERE name = 'marker'").fetchall()
    assert generations.is_held(legacy.resolve())
    assert generations.read_receipt(legacy.resolve())["previous"] == old.name
    with closing(open_readonly(legacy)) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert conn.execute("SELECT COUNT(*) FROM sum11").fetchone()[0] == 1
