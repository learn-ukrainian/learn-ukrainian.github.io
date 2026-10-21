"""Tests for pipeline/screen.py — deterministic fix helpers.

Covers pure functions extracted from _run_deterministic_fixes and
_deterministic_screen. Does NOT test functions requiring ModuleContext
or file I/O (those are integration-tested via test_pipeline_v5.py).

Issue: #782
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.screen import (
    _run_ipa_scan,
)

# =============================================================================
# _fix_extra_h1
# =============================================================================


# =============================================================================
# _fix_ipa_brackets
# =============================================================================


# =============================================================================
# _run_ipa_scan
# =============================================================================

class TestRunIpaScan:
    def test_detects_syllable_breakdown(self):
        text = "Привіт [pry-vit] is a greeting"
        issues = _run_ipa_scan(text)
        assert any(i["type"] == "IPA_BANNED" for i in issues)
