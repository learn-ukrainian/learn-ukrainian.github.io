"""
Tests for site website integrity.

Validates that the generated site is internally consistent:
1. Every track has a landing page (index.mdx) with valid frontmatter
2. Every module link in landing pages resolves, and none uses a retired format
3. MDX files have valid frontmatter (title required)
4. No stale files from old naming conventions (module-NN.mdx, numbered slugs)
5. Curriculum manifest (curriculum.yaml) is in sync with site content
6. No broken internal links between modules

Run: pytest tests/test_site_links.py -v
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
pytestmark = [pytest.mark.website, pytest.mark.reads_content]

SITE_DIR = Path(__file__).parent.parent / "site"
DOCS_DIR = SITE_DIR / "src" / "content" / "docs"
MANIFEST_PATH = Path(__file__).parent.parent / "curriculum" / "l2-uk-en" / "curriculum.yaml"

# Tracks where ALL manifest modules should have MDX (fully built).
COMPLETE_TRACKS: list[str] = ["a1"]


# =============================================================================
# HELPERS
# =============================================================================


def _load_manifest() -> dict:
    """Load curriculum.yaml manifest."""
    if not MANIFEST_PATH.is_file():
        pytest.skip("curriculum.yaml not found")
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


def _skip_if_no_site():
    """Skip test if site directory doesn't exist."""
    if not DOCS_DIR.is_dir():
        pytest.skip("site docs directory not found")


# =============================================================================
# 1. LANDING PAGE EXISTENCE
# =============================================================================


# =============================================================================
# 2. MODULE LINK INTEGRITY
# =============================================================================


# =============================================================================
# 3. MDX FILE INTEGRITY
# =============================================================================

class TestMdxFiles:
    """MDX module files must have valid frontmatter."""

    @pytest.fixture(autouse=True)
    def check_site(self):
        _skip_if_no_site()


# =============================================================================
# 4. MODULE COUNT SANITY
# =============================================================================

class TestModuleCounts:
    """Tracks must have the expected minimum number of modules."""

    @pytest.fixture(autouse=True)
    def check_site(self):
        _skip_if_no_site()


# =============================================================================
# 5. INTERNAL LINK VALIDATION
# =============================================================================

class TestInternalLinks:
    """MDX files must not contain broken internal links."""

    @pytest.fixture(autouse=True)
    def check_site(self):
        _skip_if_no_site()


# =============================================================================
# 6. CROSS-CHECK: CURRICULUM.YAML vs STARLIGHT
# =============================================================================

class TestCurriculumSync:
    """Curriculum manifest (curriculum.yaml) must be in sync with site content."""

    @pytest.fixture(autouse=True)
    def check_site(self):
        _skip_if_no_site()

    @pytest.fixture(scope="class")
    def manifest(self):
        return _load_manifest()

    @pytest.mark.parametrize("track", COMPLETE_TRACKS)
    def test_manifest_modules_have_mdx(self, track, manifest):
        """Every module in curriculum.yaml for complete tracks has a .mdx file.

        Modules that haven't finished the pipeline's ``publish`` phase
        — either still in-progress or parked in a human terminal
        — legitimately have no MDX. Those are skipped so a single
        in-flight module doesn't fail the whole sync check. The gate
        is: ``orchestration/{slug}/state.json::phases.publish.status
        == "complete"``. Plus the convergent pipeline terminal
        sentinels for plan revision or exhausted budget.
        """
        import json as _json

        levels = manifest.get("levels", {})
        if track not in levels:
            pytest.skip(f"{track} not in manifest")

        modules = levels[track].get("modules", [])
        if not modules:
            pytest.skip(f"No modules in manifest for {track}")

        curriculum_root = MANIFEST_PATH.parent / track

        def _is_in_progress(bare_slug: str) -> bool:
            orch = curriculum_root / "orchestration" / bare_slug
            if (orch / "plan_revision_request.yaml").is_file() or (orch / "budget_exhausted.yaml").is_file():
                return True
            state_path = orch / "state.json"
            if not state_path.is_file():
                # No orchestration run yet → not yet being built.
                return True
            try:
                state = _json.loads(state_path.read_text(encoding="utf-8"))
            except (OSError, _json.JSONDecodeError):
                return False
            publish_phase = state.get("phases", {}).get("publish", {})
            return publish_phase.get("status") != "complete"

        missing = []
        for slug in modules:
            bare = re.sub(r"^\d+-", "", slug)
            if _is_in_progress(bare):
                continue
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
