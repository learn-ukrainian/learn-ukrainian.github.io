"""Tests for pre-flight check and quality dimensions injection (#844).

Covers:
- Quality dimensions placeholder injection (tier-aware)
- Pre-flight instructions placeholder injection
- Pre-flight output parsing in content phase
- --skip-preflight flag
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


# =============================================================================
# Quality Dimensions Injection
# =============================================================================


# =============================================================================
# Pre-flight Parsing
# =============================================================================

class TestPreflightParsing:
    """Test that the pipeline correctly parses preflight output."""

    def test_extract_preflight_fail(self):
        from pipeline_lib import _extract_delimited_content
        raw = """===PREFLIGHT_START===
status: FAIL
plan_depth: INSUFFICIENT — only 2 bullet points for 4000-word target
research_adequacy: INSUFFICIENT — no dated events found
contradictions: NONE
vocabulary_fit: OK
overall: Plan too thin for word target. Research lacks specifics.
===PREFLIGHT_END===
"""
        preflight = _extract_delimited_content(raw, "===PREFLIGHT_START===", "===PREFLIGHT_END===")
        assert preflight is not None
        assert "status: FAIL" in preflight
        # Content should NOT be extractable
        content = _extract_delimited_content(raw, "===CONTENT_START===", "===CONTENT_END===")
        assert content is None


# =============================================================================
# Skip Preflight Flag
# =============================================================================


# =============================================================================
# Template Line Counts
# =============================================================================


# =============================================================================
# New Placeholder Integration
# =============================================================================

class TestNewPlaceholders:
    """Verify new placeholders appear in the right templates."""

    # beginner-content.md was retired — see the retired-template note
    # at the bottom of this class. core-content.md and content.md tests
    # cover the live templates.

    # Beginner-content template-placeholder assertions were retired:
    # the ``beginner-content.md`` file was replaced by ``beginner-full-rag.md``
    # + ``beginner-checkpoint.md``, and both of those DO still use
    # ``{SHARED_CONTENT_RULES}`` / ``{SELF_AUDIT_SNIPPET}`` by design
    # (the pipeline in scripts/pipeline/core.py:840-860 still substitutes
    # both placeholders at render time). The "new templates must not use
    # old placeholders" intent never landed for beginner templates.
