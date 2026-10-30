"""The ULIF raw cache sits beside the Sources store selector, never in a generation directory (#12158)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lexicon import ulif_raw_cache

GENERATION = "sources.20261030T191244Z-485bfef02834.db"


@pytest.fixture(autouse=True)
def _no_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LU_ULIF_RAW_CACHE", raising=False)


def _selector_layout(data: Path) -> Path:
    generations = data / "sources-generations"
    generations.mkdir(parents=True)
    (generations / GENERATION).write_bytes(b"")
    selector = data / "sources.db"
    selector.symlink_to(f"sources-generations/{GENERATION}")
    return selector


def test_selector_and_followed_generation_share_the_data_dir_cache(tmp_path: Path) -> None:
    data = tmp_path / "data"
    selector = _selector_layout(data)
    expected = data.resolve() / "lexicon/cache/ulif_raw.sqlite"

    assert ulif_raw_cache.cache_path(selector) == expected
    assert ulif_raw_cache.cache_path(selector.resolve()) == expected
    assert ulif_raw_cache.store_data_dir(selector.resolve()) == data.resolve()
    assert [p.name for p in (data / "sources-generations").iterdir()] == [GENERATION]


def test_fixture_database_keeps_its_sibling_cache(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture" / "sources.db"
    fixture.parent.mkdir()
    fixture.write_bytes(b"")

    assert ulif_raw_cache.cache_path(fixture) == fixture.parent.resolve() / "lexicon/cache/ulif_raw.sqlite"
    assert ulif_raw_cache.store_data_dir(fixture) == fixture.parent.resolve()
