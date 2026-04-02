"""
Tests for Starlight website integrity.

Validates that the generated Starlight site is internally consistent:
1. Every track has a landing page (index.mdx) with valid frontmatter
2. Every module link in landing pages resolves to an existing .mdx file
3. MDX files have valid frontmatter (title required)
4. No stale files from old naming conventions (module-NN.mdx, numbered slugs)
5. Curriculum manifest (curriculum.yaml) is in sync with Starlight content
6. No broken internal links between modules

Run: pytest tests/test_starlight_links.py -v
Run only website tests: pytest -m website
"""

import os
import re
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mark all tests in this module
pytestmark = pytest.mark.website

STARLIGHT_DIR = Path(__file__).parent.parent / "starlight"
DOCS_DIR = STARLIGHT_DIR / "src" / "content" / "docs"
MANIFEST_PATH = Path(__file__).parent.parent / "curriculum" / "l2-uk-en" / "curriculum.yaml"

# All tracks that should exist in the docs directory
ALL_TRACKS = [
    "a1", "a2", "b1", "b2", "c1", "c2",
    "hist", "b2-pro",
    "bio", "istorio", "c1-pro",
    "lit", "oes", "ruth",
]

# Tracks that have content modules with links in their index.mdx.
TRACKS_WITH_MODULES = [
    "a1", "a2", "b1", "b2",
    "hist", "c1", "bio", "istorio",
]

# Tracks where ALL manifest modules should have MDX (fully built).
COMPLETE_TRACKS: list[str] = ["a1"]

# Minimum expected module counts per track (regression floor).
MIN_MODULE_COUNTS = {
    "a1": 44,
    "a2": 31,
    "b1": 5,
    "b2": 2,
    "hist": 6,
    "bio": 4,
    "istorio": 2,
}


# =============================================================================
# HELPERS
# =============================================================================

def _parse_frontmatter(mdx_path: Path) -> dict:
    """Extract YAML frontmatter from an MDX file."""
    text = mdx_path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        # Fallback to simple parsing
        fm = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                fm[key.strip()] = val.strip()
        return fm


def _extract_module_links(index_path: Path) -> list[str]:
    """Extract relative module links from a landing page's markdown.

    Matches patterns like [Title](./slug) or [Title](./slug/) in markdown.
    Returns list of slugs (without ./ prefix or trailing /).
    """
    text = index_path.read_text(encoding="utf-8")
    # Match both ./slug and ./slug/ patterns
    links = re.findall(r"\[.*?\]\(\./([^)/#]+)/?(?:#[^)]*)?\)", text)
    return links


def _load_manifest() -> dict:
    """Load curriculum.yaml manifest."""
    if not MANIFEST_PATH.is_file():
        pytest.skip("curriculum.yaml not found")
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


def _skip_if_no_starlight():
    """Skip test if Starlight directory doesn't exist."""
    if not DOCS_DIR.is_dir():
        pytest.skip("Starlight docs directory not found")


# =============================================================================
# 1. LANDING PAGE EXISTENCE
# =============================================================================

class TestLandingPages:
    """Every track directory must have a landing page."""

    @pytest.fixture(autouse=True)
    def check_starlight(self):
        _skip_if_no_starlight()

    @pytest.mark.parametrize("track", ALL_TRACKS)
    def test_track_directory_exists(self, track):
        track_dir = DOCS_DIR / track
        assert track_dir.is_dir(), f"Missing track directory: {track}/"

    @pytest.mark.parametrize("track", ALL_TRACKS)
    def test_landing_page_exists(self, track):
        # Starlight uses index.mdx for landing pages
        index = DOCS_DIR / track / "index.mdx"
        if not index.is_file():
            # Also check for index.md
            index = DOCS_DIR / track / "index.md"
        assert index.is_file(), f"Missing landing page: {track}/index.mdx"

    @pytest.mark.parametrize("track", ALL_TRACKS)
    def test_landing_page_has_title(self, track):
        index = DOCS_DIR / track / "index.mdx"
        if not index.is_file():
            index = DOCS_DIR / track / "index.md"
        if not index.is_file():
            pytest.skip(f"No index for {track}")
        fm = _parse_frontmatter(index)
        assert fm.get("title"), f"{track}/index.mdx missing or empty 'title'"


# =============================================================================
# 2. MODULE LINK INTEGRITY
# =============================================================================

class TestModuleLinks:
    """Every module link in landing pages must resolve to an existing MDX file."""

    @pytest.fixture(autouse=True)
    def check_starlight(self):
        _skip_if_no_starlight()

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_all_links_resolve(self, track):
        """Every ./slug link in the landing page points to an existing .mdx file."""
        index = DOCS_DIR / track / "index.mdx"
        if not index.is_file():
            pytest.skip(f"No index.mdx for {track}")

        slugs = _extract_module_links(index)
        if not slugs:
            pytest.skip(f"No module links found in {track}/index.mdx")

        missing = []
        for s in slugs:
            # Starlight can use .mdx or .md
            if not (DOCS_DIR / track / f"{s}.mdx").is_file() and \
               not (DOCS_DIR / track / f"{s}.md").is_file():
                missing.append(s)

        assert not missing, (
            f"{track}/index.mdx has {len(missing)} broken links:\n"
            + "\n".join(f"  - ./{s} -> {s}.mdx NOT FOUND" for s in missing[:20])
            + (f"\n  ... and {len(missing) - 20} more" if len(missing) > 20 else "")
        )

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_no_numbered_slug_links(self, track):
        """Landing pages must not link to numbered slugs (e.g., ./01-slug)."""
        index = DOCS_DIR / track / "index.mdx"
        if not index.is_file():
            pytest.skip(f"No index.mdx for {track}")

        numbered = [s for s in _extract_module_links(index) if re.match(r"^\d+-", s)]
        assert not numbered, (
            f"{track}/index.mdx links to numbered slugs:\n"
            + "\n".join(f"  - ./{s}" for s in numbered[:10])
        )

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_no_module_nn_links(self, track):
        """Landing pages must not use the old module-NN link format."""
        index = DOCS_DIR / track / "index.mdx"
        if not index.is_file():
            pytest.skip(f"No index.mdx for {track}")

        old_links = re.findall(r"\./module-\d+", index.read_text(encoding="utf-8"))
        assert not old_links, (
            f"{track}/index.mdx uses old module-NN links:\n"
            + "\n".join(f"  - {link}" for link in old_links[:10])
        )


# =============================================================================
# 3. MDX FILE INTEGRITY
# =============================================================================

class TestMdxFiles:
    """MDX module files must have valid frontmatter."""

    @pytest.fixture(autouse=True)
    def check_starlight(self):
        _skip_if_no_starlight()

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_all_mdx_have_title(self, track):
        """Every module .mdx file has title in frontmatter (required by Starlight)."""
        track_dir = DOCS_DIR / track
        module_files = [f for f in sorted(track_dir.glob("*.mdx")) if f.name != "index.mdx"]

        missing = [f.name for f in module_files if not _parse_frontmatter(f).get("title")]
        assert not missing, (
            f"{track}/ has {len(missing)} MDX files without title:\n"
            + "\n".join(f"  - {n}" for n in missing[:20])
            + (f"\n  ... and {len(missing) - 20} more" if len(missing) > 20 else "")
        )

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_all_mdx_have_frontmatter(self, track):
        """Every module .mdx file has valid YAML frontmatter."""
        track_dir = DOCS_DIR / track
        module_files = [f for f in sorted(track_dir.glob("*.mdx")) if f.name != "index.mdx"]

        no_fm = [f.name for f in module_files if not _parse_frontmatter(f)]
        assert not no_fm, (
            f"{track}/ has {len(no_fm)} MDX files without frontmatter:\n"
            + "\n".join(f"  - {n}" for n in no_fm[:20])
        )

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_no_old_module_nn_files(self, track):
        """No module-NN.mdx files should remain (pre-migration artifact)."""
        old_files = sorted((DOCS_DIR / track).glob("module-*.mdx"))
        assert not old_files, (
            f"{track}/ has stale module-NN.mdx files:\n"
            + "\n".join(f"  - {f.name}" for f in old_files[:10])
        )


# =============================================================================
# 4. MODULE COUNT SANITY
# =============================================================================

class TestModuleCounts:
    """Tracks must have the expected minimum number of modules."""

    @pytest.fixture(autouse=True)
    def check_starlight(self):
        _skip_if_no_starlight()

    @pytest.mark.parametrize("track,min_count", MIN_MODULE_COUNTS.items())
    def test_minimum_module_count(self, track, min_count):
        """Track has at least the minimum expected number of module .mdx files."""
        track_dir = DOCS_DIR / track
        if not track_dir.is_dir():
            pytest.skip(f"Track directory {track}/ not found")
        mdx_files = [f for f in track_dir.glob("*.mdx") if f.name != "index.mdx"]
        assert len(mdx_files) >= min_count, (
            f"{track}/ has {len(mdx_files)} modules, expected >= {min_count}"
        )


# =============================================================================
# 5. INTERNAL LINK VALIDATION
# =============================================================================

class TestInternalLinks:
    """MDX files must not contain broken internal links."""

    @pytest.fixture(autouse=True)
    def check_starlight(self):
        _skip_if_no_starlight()

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_no_broken_cross_references(self, track):
        """Links within MDX files that reference other modules should resolve."""
        track_dir = DOCS_DIR / track
        if not track_dir.is_dir():
            pytest.skip(f"No {track}/ directory")

        module_files = sorted(track_dir.glob("*.mdx"))
        broken = []

        for mdx_file in module_files:
            text = mdx_file.read_text(encoding="utf-8")
            # Find relative links like [text](./other-slug) or [text](../other-track/slug)
            local_links = re.findall(r'\[.*?\]\(\./([^)/#]+)/?(?:#[^)]*)?\)', text)
            for link in local_links:
                if not (track_dir / f"{link}.mdx").is_file() and \
                   not (track_dir / f"{link}.md").is_file() and \
                   not (track_dir / link / "index.mdx").is_file():
                    broken.append(f"{mdx_file.name} -> ./{link}")

        assert not broken, (
            f"{track}/ has {len(broken)} broken internal links:\n"
            + "\n".join(f"  - {b}" for b in broken[:20])
        )


# =============================================================================
# 6. CROSS-CHECK: CURRICULUM.YAML vs STARLIGHT
# =============================================================================

class TestCurriculumSync:
    """Curriculum manifest (curriculum.yaml) must be in sync with Starlight content."""

    @pytest.fixture(autouse=True)
    def check_starlight(self):
        _skip_if_no_starlight()

    @pytest.fixture(scope="class")
    def manifest(self):
        return _load_manifest()

    @pytest.mark.parametrize("track", COMPLETE_TRACKS)
    def test_manifest_modules_have_mdx(self, track, manifest):
        """Every module in curriculum.yaml for complete tracks has a .mdx file."""
        levels = manifest.get("levels", {})
        if track not in levels:
            pytest.skip(f"{track} not in manifest")

        modules = levels[track].get("modules", [])
        if not modules:
            pytest.skip(f"No modules in manifest for {track}")

        missing = []
        for slug in modules:
            bare = re.sub(r"^\d+-", "", slug)
            if not (DOCS_DIR / track / f"{bare}.mdx").is_file() and \
               not (DOCS_DIR / track / f"{bare}.md").is_file():
                missing.append(bare)

        assert not missing, (
            f"curriculum.yaml lists {len(missing)} modules for {track} without .mdx:\n"
            + "\n".join(f"  - {s}" for s in missing[:20])
            + (f"\n  ... and {len(missing) - 20} more" if len(missing) > 20 else "")
        )


# =============================================================================
# 7. STARLIGHT-SPECIFIC CHECKS
# =============================================================================

class TestStarlightConfig:
    """Starlight configuration integrity."""

    def test_astro_config_exists(self):
        config = STARLIGHT_DIR / "astro.config.mjs"
        assert config.is_file(), "Missing astro.config.mjs"

    def test_package_json_exists(self):
        pkg = STARLIGHT_DIR / "package.json"
        assert pkg.is_file(), "Missing package.json"

    def test_homepage_exists(self):
        index = DOCS_DIR / "index.mdx"
        assert index.is_file(), "Missing docs/index.mdx homepage"

    def test_homepage_has_title(self):
        index = DOCS_DIR / "index.mdx"
        if not index.is_file():
            pytest.skip("No homepage")
        fm = _parse_frontmatter(index)
        assert fm.get("title"), "Homepage missing title"
