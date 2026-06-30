from scripts import manifest_utils
from scripts.generate_mdx.core import get_modules_from_manifest


def test_track_constant_covers_manifest_tracks():
    manifest = manifest_utils.load_manifest()
    manifest_tracks = {
        level
        for level, data in manifest.get("levels", {}).items()
        if isinstance(data, dict) and data.get("type") == "track"
    }

    assert manifest_tracks <= set(manifest_utils.TRACKS)


def test_generate_mdx_manifest_includes_folk_modules():
    slugs = {module.slug for module in get_modules_from_manifest("folk")}

    assert "kalendarna-obriadovist-zvychai" in slugs
