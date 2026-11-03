"""Shared isolation for build tests that render Atlas links."""

import pytest


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
