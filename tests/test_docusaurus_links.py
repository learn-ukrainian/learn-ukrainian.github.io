"""
Tests for Docusaurus website integrity.

Validates that the generated Docusaurus site is internally consistent:
1. Every track has a landing page (index.mdx) with valid frontmatter
2. Every module link in landing pages resolves to an existing .mdx file
3. MDX files have valid, non-duplicate sidebar_position values
4. No stale files from old naming conventions (module-NN.mdx, numbered slugs)
5. Homepage and sidebar reference valid track directories
6. Curriculum manifest (curriculum.yaml) is in sync with generated MDX

Run: pytest tests/test_docusaurus_links.py -v
Run only website tests: pytest -m website
"""

import re
import sys
import os
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mark all tests in this module
pytestmark = pytest.mark.website

DOCS_DIR = Path(__file__).parent.parent / "docusaurus" / "docs"
DOCUSAURUS_DIR = Path(__file__).parent.parent / "docusaurus"
MANIFEST_PATH = Path(__file__).parent.parent / "curriculum" / "l2-uk-en" / "curriculum.yaml"

# All tracks that should exist in the docs directory
ALL_TRACKS = [
    "a1", "a2", "b1", "b2", "c1", "c2",
    "b2-hist", "b2-pro",
    "c1-bio", "c1-hist", "c1-pro",
    "lit", "oes", "ruth",
]

# Tracks that have content modules with links in their index.mdx.
# Only include tracks where index.mdx has ./slug links that can be tested.
TRACKS_WITH_MODULES = [
    "a1", "a2", "b1", "b2",
    "b2-hist",
]

# Tracks where ALL manifest modules should have MDX (fully built).
# Empty until a track has 100% of its curriculum.yaml modules generated.
COMPLETE_TRACKS: list[str] = []

# Minimum expected module counts per track (regression floor).
# These are ACTUAL current counts — update as modules are built.
# Purpose: prevent accidental deletion of MDX files.
MIN_MODULE_COUNTS = {
    "a1": 43,
    "a2": 6,
    "b1": 5,
    "b2": 2,
    "b2-hist": 6,
    "c1-bio": 4,
    "c1-hist": 2,
}


# =============================================================================
# HELPERS
# =============================================================================

def _parse_frontmatter(mdx_path: Path) -> dict:
    """Extract YAML frontmatter from an MDX file.

    Simple key: value parser — sufficient for sidebar_position and title.
    Does not handle nested YAML or multi-line values.
    """
    text = mdx_path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


def _extract_module_links(index_path: Path) -> list[str]:
    """Extract relative module links from a landing page's markdown table.

    Matches patterns like [Title](./slug) in markdown table rows.
    Returns list of slugs (without ./ prefix).
    """
    text = index_path.read_text(encoding="utf-8")
    return re.findall(r"\[.*?\]\(\./([^)/#]+)\)", text)


def _load_manifest() -> dict:
    """Load curriculum.yaml manifest."""
    if not MANIFEST_PATH.is_file():
        pytest.skip("curriculum.yaml not found")
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


# =============================================================================
# 1. LANDING PAGE EXISTENCE
# =============================================================================

class TestLandingPages:
    """Every track directory must have a landing page."""

    @pytest.mark.parametrize("track", ALL_TRACKS)
    def test_track_directory_exists(self, track):
        track_dir = DOCS_DIR / track
        assert track_dir.is_dir(), f"Missing track directory: docs/{track}/"

    @pytest.mark.parametrize("track", ALL_TRACKS)
    def test_landing_page_exists(self, track):
        index = DOCS_DIR / track / "index.mdx"
        assert index.is_file(), f"Missing landing page: docs/{track}/index.mdx"

    @pytest.mark.parametrize("track", ALL_TRACKS)
    def test_landing_page_has_title(self, track):
        index = DOCS_DIR / track / "index.mdx"
        if not index.is_file():
            pytest.skip(f"No index.mdx for {track}")
        fm = _parse_frontmatter(index)
        assert fm.get("title"), f"docs/{track}/index.mdx missing or empty 'title'"

    @pytest.mark.parametrize("track", ALL_TRACKS)
    def test_landing_page_has_sidebar_position(self, track):
        index = DOCS_DIR / track / "index.mdx"
        if not index.is_file():
            pytest.skip(f"No index.mdx for {track}")
        fm = _parse_frontmatter(index)
        assert "sidebar_position" in fm, (
            f"docs/{track}/index.mdx missing 'sidebar_position' in frontmatter"
        )


# =============================================================================
# 2. MODULE LINK INTEGRITY
# =============================================================================

class TestModuleLinks:
    """Every module link in landing pages must resolve to an existing MDX file."""

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_all_links_resolve(self, track):
        """Every ./slug link in the landing page points to an existing .mdx file."""
        index = DOCS_DIR / track / "index.mdx"
        if not index.is_file():
            pytest.skip(f"No index.mdx for {track}")

        slugs = _extract_module_links(index)
        assert slugs, f"No module links found in docs/{track}/index.mdx"

        missing = [s for s in slugs if not (DOCS_DIR / track / f"{s}.mdx").is_file()]
        assert not missing, (
            f"docs/{track}/index.mdx has {len(missing)} broken links:\n"
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
            f"docs/{track}/index.mdx links to numbered slugs:\n"
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
            f"docs/{track}/index.mdx uses old module-NN links:\n"
            + "\n".join(f"  - {link}" for link in old_links[:10])
        )


# =============================================================================
# 3. MDX FILE INTEGRITY
# =============================================================================

class TestMdxFiles:
    """MDX module files must have valid frontmatter."""

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_all_mdx_have_sidebar_position(self, track):
        """Every module .mdx file has sidebar_position in frontmatter."""
        track_dir = DOCS_DIR / track
        module_files = [f for f in sorted(track_dir.glob("*.mdx")) if f.name != "index.mdx"]

        missing = [f.name for f in module_files if "sidebar_position" not in _parse_frontmatter(f)]
        assert not missing, (
            f"docs/{track}/ has {len(missing)} MDX files without sidebar_position:\n"
            + "\n".join(f"  - {n}" for n in missing[:20])
            + (f"\n  ... and {len(missing) - 20} more" if len(missing) > 20 else "")
        )

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_no_duplicate_sidebar_positions(self, track):
        """No two module MDX files in a track share the same sidebar_position."""
        track_dir = DOCS_DIR / track
        module_files = [f for f in sorted(track_dir.glob("*.mdx")) if f.name != "index.mdx"]

        positions: dict[str, list[str]] = {}
        for f in module_files:
            pos = _parse_frontmatter(f).get("sidebar_position", "")
            if pos:
                positions.setdefault(pos, []).append(f.name)

        dupes = {pos: files for pos, files in positions.items() if len(files) > 1}
        assert not dupes, (
            f"docs/{track}/ has duplicate sidebar_position values:\n"
            + "\n".join(
                f"  - position {pos}: {', '.join(files)}"
                for pos, files in sorted(dupes.items())
            )
        )

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_no_old_module_nn_files(self, track):
        """No module-NN.mdx files should remain (pre-migration artifact)."""
        old_files = sorted((DOCS_DIR / track).glob("module-*.mdx"))
        assert not old_files, (
            f"docs/{track}/ has stale module-NN.mdx files:\n"
            + "\n".join(f"  - {f.name}" for f in old_files[:10])
        )


# =============================================================================
# 4. MODULE COUNT SANITY
# =============================================================================

class TestModuleCounts:
    """Tracks must have the expected minimum number of modules."""

    @pytest.mark.parametrize("track,min_count", MIN_MODULE_COUNTS.items())
    def test_minimum_module_count(self, track, min_count):
        """Track has at least the minimum expected number of module .mdx files."""
        mdx_files = [f for f in (DOCS_DIR / track).glob("*.mdx") if f.name != "index.mdx"]
        assert len(mdx_files) >= min_count, (
            f"docs/{track}/ has {len(mdx_files)} modules, expected >= {min_count}"
        )

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_no_dangling_links(self, track):
        """Every link in the landing page resolves to an existing MDX file.

        Extra MDX files without links are fine (index.mdx may only link
        to a subset of completed modules).
        """
        index = DOCS_DIR / track / "index.mdx"
        if not index.is_file():
            pytest.skip(f"No index.mdx for {track}")

        linked_set = set(_extract_module_links(index))
        if not linked_set:
            pytest.skip(f"No module links in docs/{track}/index.mdx")

        file_set = {f.stem for f in (DOCS_DIR / track).glob("*.mdx") if f.name != "index.mdx"}
        dangling = linked_set - file_set

        assert not dangling, (
            f"docs/{track}/index.mdx has {len(dangling)} broken links (no MDX file):\n"
            + "\n".join(f"  - ./{s}" for s in sorted(dangling)[:20])
        )


# =============================================================================
# 5. HOMEPAGE & SIDEBAR INTEGRITY
# =============================================================================

class TestHomepage:
    """Homepage and sidebar must reference valid paths."""

    def test_homepage_exists(self):
        homepage = DOCUSAURUS_DIR / "src" / "pages" / "index.tsx"
        assert homepage.is_file(), "Missing homepage: src/pages/index.tsx"

    def test_intro_page_exists(self):
        intro = DOCS_DIR / "intro.mdx"
        assert intro.is_file(), "Missing intro page: docs/intro.mdx"

    def test_homepage_track_links(self):
        """Homepage /docs/{track} links point to existing directories."""
        homepage = DOCUSAURUS_DIR / "src" / "pages" / "index.tsx"
        if not homepage.is_file():
            pytest.skip("No homepage file")

        track_refs = re.findall(r'to="/docs/([^"/?#]+)"', homepage.read_text(encoding="utf-8"))
        missing = [t for t in track_refs if not (DOCS_DIR / t).is_dir()]
        assert not missing, (
            f"Homepage references non-existent track directories:\n"
            + "\n".join(f"  - /docs/{t}/" for t in missing)
        )

    def test_sidebar_track_dirs_exist(self):
        """Every autogenerated dirName in sidebars.ts has a matching docs/ directory."""
        sidebars = DOCUSAURUS_DIR / "sidebars.ts"
        if not sidebars.is_file():
            pytest.skip("No sidebars.ts")

        dir_names = re.findall(r"dirName:\s*'([^']+)'", sidebars.read_text(encoding="utf-8"))
        missing = [d for d in dir_names if not (DOCS_DIR / d).is_dir()]
        assert not missing, (
            f"sidebars.ts references non-existent directories:\n"
            + "\n".join(f"  - dirName: '{d}'" for d in missing)
        )


# =============================================================================
# 6. CROSS-CHECK: CURRICULUM.YAML vs DOCUSAURUS
# =============================================================================

class TestCurriculumSync:
    """Curriculum manifest (curriculum.yaml) must be in sync with Docusaurus docs."""

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
            if not (DOCS_DIR / track / f"{bare}.mdx").is_file():
                missing.append(bare)

        assert not missing, (
            f"curriculum.yaml lists {len(missing)} modules for {track} without .mdx:\n"
            + "\n".join(f"  - {s}" for s in missing[:20])
            + (f"\n  ... and {len(missing) - 20} more" if len(missing) > 20 else "")
        )

    @pytest.mark.parametrize("track", TRACKS_WITH_MODULES)
    def test_manifest_order_matches_sidebar_position(self, track, manifest):
        """Module order in curriculum.yaml matches sidebar_position in MDX.

        sidebar_position is 1-based: first module = 1, second = 2, etc.
        The index.mdx also uses sidebar_position 1, but Docusaurus sorts
        index pages first when positions tie.
        """
        levels = manifest.get("levels", {})
        if track not in levels:
            pytest.skip(f"{track} not in manifest")

        modules = levels[track].get("modules", [])
        if not modules:
            pytest.skip(f"No modules in manifest for {track}")

        mismatches = []
        for i, slug in enumerate(modules, start=1):
            bare = re.sub(r"^\d+-", "", slug)
            mdx = DOCS_DIR / track / f"{bare}.mdx"
            if not mdx.is_file():
                continue
            pos = _parse_frontmatter(mdx).get("sidebar_position", "")
            if pos and str(i) != str(pos):
                mismatches.append(f"{bare}: expected {i}, got {pos}")

        assert not mismatches, (
            f"docs/{track}/ sidebar_position mismatches:\n"
            + "\n".join(f"  - {m}" for m in mismatches[:20])
            + (f"\n  ... and {len(mismatches) - 20} more" if len(mismatches) > 20 else "")
        )
