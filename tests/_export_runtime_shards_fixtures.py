"""Shared pytest fixtures for runtime shard exporter tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.atlas.export_runtime_shards import export_runtime_shards

FIXTURE_DB_PATH = Path(__file__).resolve().parent / "fixtures" / "atlas" / "runtime_shards_fixture.db"


@pytest.fixture(scope="module")
def fixture_db() -> Path:
    assert FIXTURE_DB_PATH.is_file(), f"missing fixture DB: {FIXTURE_DB_PATH}"
    return FIXTURE_DB_PATH


@pytest.fixture(scope="module")
def fixture_export(fixture_db: Path, tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict]:
    """One immutable fixture export for tests that only inspect its output."""
    out = tmp_path_factory.mktemp("runtime-shards") / "out"
    report = export_runtime_shards(
        db_path=fixture_db,
        out_dir=out,
        deck_dir=None,
        include_decks=False,
        verify=True,
    )
    return out, report


@pytest.fixture(scope="module")
def edge_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    from tests.test_export_runtime_shards import _make_source_db

    return _make_source_db(tmp_path_factory.mktemp("edge") / "edge.db")


@pytest.fixture(scope="module")
def verified_tree(edge_db: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    from tests.test_export_runtime_shards import _export

    out = tmp_path_factory.mktemp("verify") / "out"
    _export(edge_db, out, entry_max_gzip_bytes=9_000, search_max_gzip_bytes=1_200)
    return out
