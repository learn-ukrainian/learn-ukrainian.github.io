"""
Tests for the track scoring system.

Tests scripts/scoring/metrics.py (metric extraction) and
scripts/scoring/caps.py (critical failure caps).
All pure functions with no file I/O.

Run with: pytest tests/test_scoring.py -v
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.scoring.caps import (
    apply_critical_caps,
    check_cap_violations,
)
from scripts.scoring.metrics import (
    analyze_toponyms,
)

# =============================================================================
# TEST: count_callouts
# =============================================================================


# =============================================================================
# TEST: count_agency_markers
# =============================================================================


# =============================================================================
# TEST: analyze_toponyms
# =============================================================================

class TestAnalyzeToponyms:
    def test_colonial_names_detected(self):
        content = "Місто Киев було столицею. Харьков на сході."
        violations, _correct = analyze_toponyms(content)
        assert violations >= 2

    def test_ukrainian_names_counted(self):
        content = "Київ — столиця України. Харків на сході. Львів на заході."
        violations, correct = analyze_toponyms(content)
        assert violations == 0
        assert correct >= 3


# =============================================================================
# TEST: count_cross_references
# =============================================================================


# =============================================================================
# TEST: calculate_citation_ratio
# =============================================================================


# =============================================================================
# TEST: count_stylistic_devices
# =============================================================================


# =============================================================================
# TEST: count_analysis_sections
# =============================================================================


# =============================================================================
# TEST: count_legacy_sections
# =============================================================================


# =============================================================================
# TEST: get_caps_for_track
# =============================================================================


# =============================================================================
# TEST: apply_critical_caps
# =============================================================================

class TestApplyCriticalCaps:
    def test_cap_applied_zero_myth_busters(self):
        """Zero myth-busters should cap decolonization score."""
        metrics = {'total_myth_buster_callouts': 0, 'total_quote_callouts': 5,
                   'agency_marker_ratio': 0.2, 'total_cross_references': 3}
        scores = {'decolonization_perspective': 9.0, 'primary_source_integration': 8.0}
        updated, results = apply_critical_caps('hist', metrics, scores)
        assert updated['decolonization_perspective'] <= 4.0
        assert any(r.cap_applied and r.cap_name == 'zero_myth_busters' for r in results)


# =============================================================================
# TEST: check_cap_violations
# =============================================================================

class TestCheckCapViolations:
    def test_detects_violations(self):
        metrics = {'total_myth_buster_callouts': 0, 'total_quote_callouts': 0,
                   'agency_marker_ratio': 0.05, 'total_cross_references': 0}
        violations = check_cap_violations('hist', metrics)
        assert len(violations) >= 3
        cap_names = [v['cap_name'] for v in violations]
        assert 'zero_myth_busters' in cap_names
        assert 'zero_quotes' in cap_names


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
