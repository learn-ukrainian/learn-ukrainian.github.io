"""The ULIF raw cache sits beside the Sources store selector, never in a generation directory (#12158)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.audit.verbatim_overlap_gate import get_default_index_db_path
from scripts.ingest.slovnyk_me_ingest import backup_database
from scripts.lexicon import ulif_raw_cache
from scripts.storage.topology import GENERATIONS_DIRNAME, SELECTOR_NAME, store_data_dir

GENERATION = "sources.20261030T191244Z-485bfef02834.db"


@pytest.fixture(autouse=True)
def _no_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LU_ULIF_RAW_CACHE", raising=False)


def _selector_layout(data: Path) -> Path:
    generations = data / GENERATIONS_DIRNAME
    generations.mkdir(parents=True)
    (generations / GENERATION).write_bytes(b"")
    selector = data / SELECTOR_NAME
    selector.symlink_to(f"{GENERATIONS_DIRNAME}/{GENERATION}")
    return selector


def test_selector_and_followed_generation_share_the_data_dir_cache(tmp_path: Path) -> None:
    data = tmp_path / "data"
    selector = _selector_layout(data)
    generations_dir = data / GENERATIONS_DIRNAME
    expected = data.resolve() / "lexicon/cache/ulif_raw.sqlite"

    assert ulif_raw_cache.cache_path(selector) == expected
    assert ulif_raw_cache.cache_path(selector.resolve()) == expected
    assert store_data_dir(selector.resolve()) == data.resolve()
    assert [p.name for p in generations_dir.iterdir()] == [GENERATION]


def test_fixture_database_keeps_its_sibling_cache(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture" / SELECTOR_NAME
    fixture.parent.mkdir()
    fixture.write_bytes(b"")

    assert ulif_raw_cache.cache_path(fixture) == fixture.parent.resolve() / "lexicon/cache/ulif_raw.sqlite"
    assert store_data_dir(fixture) == fixture.parent.resolve()


def test_other_store_relative_paths_stay_out_of_the_generation_dir(tmp_path: Path) -> None:
    data = tmp_path / "data"
    selector = _selector_layout(data)
    generation = selector.resolve()
    (data / GENERATIONS_DIRNAME / GENERATION).unlink()
    sqlite3.connect(generation).close()
    generations_dir = data / GENERATIONS_DIRNAME

    for store in (selector, generation):
        assert get_default_index_db_path(store, 5) == data.resolve() / "verbatim_shingle_k5.db"
        conn = sqlite3.connect(store)
        try:
            backup = backup_database(conn, store)
        finally:
            conn.close()
        assert backup.parent == data.resolve() / "backups"
        backup.unlink()
    assert [p.name for p in generations_dir.iterdir()] == [GENERATION]
