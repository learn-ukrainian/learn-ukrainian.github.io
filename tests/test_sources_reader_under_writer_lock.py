"""A read-only Sources caller still reads while another process holds the writer lock."""

from __future__ import annotations

import multiprocessing
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from scripts.storage import generations

SPAWN = multiprocessing.get_context("spawn")
WAIT = 60


def _hold_writer_lock(selector: str, ready, go, out) -> None:
    try:
        with generations.writer_lock(Path(selector)):
            ready.set()
            if not go.wait(WAIT):
                out.put("error:timeout")
                return
        out.put("released")
    except BaseException as error:
        ready.set()
        out.put(f"error:{error!r}")


def _wikipedia_selector(tmp_path: Path) -> Path:
    selector = tmp_path / "data" / "sources.db"
    selector.parent.mkdir(parents=True)
    seed = selector.with_name("seed.db")
    with closing(sqlite3.connect(seed)) as conn:
        assert conn.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        conn.execute("CREATE TABLE wikipedia (title TEXT, char_count INTEGER)")
        conn.execute("INSERT INTO wikipedia (title, char_count) VALUES ('Київ', 5)")
        conn.commit()
    seed.rename(selector)
    generations.hold_database(selector)
    with generations.writer_lock(selector) as held:
        generations.checkpoint_legacy_store(held)
        generations.publish_generation(selector, held, mode="bootstrap")
    return selector


def test_status_query_reads_while_another_process_holds_the_writer_lock(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LU_EVIDENCE_FREE_DISK_FLOOR_BYTES", "0")
    monkeypatch.setenv("LU_EVIDENCE_WAL_CEILING_BYTES", "0")
    monkeypatch.delenv(generations.ENV_WRITER_FD, raising=False)
    monkeypatch.delenv(generations.ENV_WRITER_SELECTOR, raising=False)
    selector = _wikipedia_selector(tmp_path)
    monkeypatch.setenv("LU_SOURCES_DB", str(selector))

    ready, go, out = SPAWN.Event(), SPAWN.Event(), SPAWN.Queue()
    process = SPAWN.Process(target=_hold_writer_lock, args=(str(selector), ready, go, out))
    process.start()
    try:
        assert ready.wait(WAIT)
        with pytest.raises(generations.GenerationError, match="writer_lock_busy"):
            with generations.writer_lock(selector):
                pass
        from scripts.wiki.fetch_wikipedia import show_status

        show_status()
        captured = capsys.readouterr().out
        assert "Wikipedia: 1 articles, 5 chars" in captured
        assert "Київ" in captured
    finally:
        go.set()
        process.join(WAIT)
    assert process.exitcode == 0
    assert out.get(timeout=WAIT) == "released"
