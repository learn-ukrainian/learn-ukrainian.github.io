"""Shared isolation for build tests that render Atlas links."""

import pytest

from scripts.curriculum.evidence import config


@pytest.fixture(autouse=True)
def _isolate_atlas_manifest(tmp_path_factory: pytest.TempPathFactory):
    from scripts.generate_mdx import atlas_links

    manifest = tmp_path_factory.mktemp("atlas_manifest") / "lexicon-manifest.json"
    manifest.write_text('{"entries": []}', encoding="utf-8")
    mp = pytest.MonkeyPatch()
    mp.setattr(atlas_links, "_DEFAULT_MANIFEST", manifest)
    atlas_links._load_manifest_tables.cache_clear()
    try:
        yield
    finally:
        atlas_links._load_manifest_tables.cache_clear()
        mp.undo()


@pytest.fixture
def no_free_disk_floor(monkeypatch):
    """Keep an owned snapshot off the runner volume.

    The session constructor reads ``config.free_disk_floor_bytes()``, the same hook the
    evidence suite uses, and these tests supply the free-disk reading so ``_guard`` does
    not call ``shutil.disk_usage``. The guard that refuses a low volume stays covered by
    ``test_snapshot_stops_when_free_disk_falls_below_the_floor``.
    """
    from scripts.curriculum.evidence.sources import Sources

    monkeypatch.setenv(config.FREE_DISK_FLOOR_ENV, "0")
    # At least the recorded floor, so ``free < floor`` cannot refuse. Replacing the
    # method keeps the test off the volume.
    monkeypatch.setattr(Sources, "free_disk_bytes", lambda self: config.FREE_DISK_FLOOR_BYTES)
