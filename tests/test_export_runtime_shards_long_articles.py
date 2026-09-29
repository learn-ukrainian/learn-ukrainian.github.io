"""Runtime shard exporter long articles tests, split for loadfile scheduling."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.atlas import export_runtime_shards as exporter
from scripts.atlas.export_runtime_shards import ExportError
from tests.test_export_runtime_shards import (
    _SHARED_KEY_CAP,
    _export_traced,
    _make_shared_key_db,
    _reference_export,
    _snapshot,
    _verify_traced,
)

pytest_plugins = ("tests._export_runtime_shards_fixtures",)


@pytest.mark.parametrize("terminal", [False, True], ids=["unsplittable", "terminal"])
@pytest.mark.parametrize("level", [0, 9])
def test_reviewer_long_article_rows_export_matches_reference_in_bounded_heap(
    tmp_path: Path, level: int, terminal: bool
) -> None:
    """Reviewer shape (fixed 8000-char gloss, 250 -> 1000 shared-key rows), export *with* --verify."""
    peaks: dict[int, int] = {}
    verify_peaks: dict[int, int] = {}
    glosses: dict[int, int] = {}
    for rows in (250, 1_000):
        db = _make_shared_key_db(tmp_path / f"shared{rows}.db", rows=rows, terminal=terminal)
        glosses[rows] = sum(len(r[0]) for r in sqlite3.connect(db).execute("SELECT gloss FROM articles"))
        out = tmp_path / f"out{rows}"
        error, peaks[rows] = _export_traced(db, out, level=level)
        if terminal:
            assert error is None
            data_version, files, indexes = _reference_export(
                db, compression_level=level, entry_max=65_536, search_max=_SHARED_KEY_CAP
            )
            tree = _snapshot(out / "atlas" / "versions" / data_version)
            assert {name: blob for name, blob in tree.items() if name != "manifest.json"} == files
            manifest = json.loads(tree["manifest.json"])
            assert manifest["search"]["articles"] == indexes["articles"]
            term = indexes["articles"]["shards"][f"{exporter.search_shard_id('a')}.term"]
            assert term["count"] == rows and term["bytes"] > 20 * _SHARED_KEY_CAP
            verify_peaks[rows] = _verify_traced(out)
        else:
            with pytest.raises(ExportError) as expected:
                _reference_export(db, compression_level=level, entry_max=65_536, search_max=_SHARED_KEY_CAP)
            assert error == str(expected.value)
            assert "prefix='a'" in error and "cannot split" in error
            assert not (out / "atlas" / "current.json").exists()
    assert glosses[1_000] > 7_900_000
    # Per-row index metadata (locators, sort keys, route digests) may grow; shard
    # bodies may not: the old exporter's heap grew by the whole bucket, and the old
    # --verify by the whole inflated terminal shard (twice for entries).
    assert peaks[1_000] - peaks[250] < (glosses[1_000] - glosses[250]) * 0.25, (peaks, glosses)
    assert peaks[1_000] < glosses[1_000] * 0.25, (peaks, glosses)
    if terminal:
        assert verify_peaks[1_000] < verify_peaks[250] * 1.25 + 1_000_000, verify_peaks
        assert verify_peaks[1_000] < glosses[1_000] * 0.2, (verify_peaks, glosses)
