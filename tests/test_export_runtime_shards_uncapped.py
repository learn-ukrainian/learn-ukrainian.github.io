"""Runtime shard exporter uncapped tests, split for loadfile scheduling."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.atlas import export_runtime_shards as exporter
from scripts.atlas.export_runtime_shards import gzip_bytes
from tests.test_export_runtime_shards import (
    _SHARED_KEY_CAP,
    _build_aliases_traced,
    _search_shard_raw,
    _shared_key_alias_index,
)

pytest_plugins = ("tests._export_runtime_shards_fixtures",)


@pytest.mark.parametrize("terminal", [False, True], ids=["unsplittable", "terminal"])
@pytest.mark.parametrize("level", [0, 1, 6, 9])
def test_uncapped_search_bucket_is_exact_and_heap_does_not_grow_with_it(
    tmp_path: Path, level: int, terminal: bool
) -> None:
    peaks: dict[int, int] = {}
    bodies: dict[int, int] = {}
    for rows in (250, 1_000):
        _index, records = _shared_key_alias_index(rows, terminal=terminal)
        raw = _search_shard_raw(exporter.SEARCH_ALIAS_SCHEMA, "a", records, terminal=terminal)
        expected = gzip_bytes(raw, compression_level=level)
        assert len(expected) > 20 * _SHARED_KEY_CAP
        out = tmp_path / f"rows{rows}"
        error, peaks[rows] = _build_aliases_traced(rows, out, terminal=terminal, level=level)
        bodies[rows] = len(raw)
        if terminal:
            assert error is None
            shard = f"search/aliases/{exporter.search_shard_id('a')}.term.json.gz"
            assert (out / shard).read_bytes() == expected
        else:
            assert error == (
                f"search aliases shard for prefix='a' exceeds max "
                f"({len(expected)} > {_SHARED_KEY_CAP}) and cannot split"
            )
            assert not out.exists(), "a failing bucket writes nothing"
    assert bodies[1_000] > 4 * bodies[250] * 0.95
    assert peaks[1_000] < peaks[250] * 1.25, peaks
    assert peaks[1_000] < bodies[1_000] * 0.2, (peaks, bodies)
