"""Shared pytest fixtures for runtime shard exporter tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.atlas.export_runtime_shards import export_runtime_shards
from tests.fixtures.atlas.build_runtime_shards_fixture import sanitized_fixture_db

FIXTURE_DB_PATH = Path(__file__).resolve().parent / "fixtures" / "atlas" / "runtime_shards_fixture.db"


@pytest.fixture(scope="module")
def fixture_db(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    assert FIXTURE_DB_PATH.is_file(), f"missing fixture DB: {FIXTURE_DB_PATH}"
    # The historical snapshot predates #M-6. Keep the transport fixture while
    # withholding old learner sections that cite the Soviet dictionary.
    destination = tmp_path_factory.mktemp("runtime-shards-source") / "source.db"
    try:
        yield sanitized_fixture_db(FIXTURE_DB_PATH, destination)
    finally:
        for path in (destination, Path(f"{destination}-wal"), Path(f"{destination}-shm")):
            path.unlink(missing_ok=True)


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
