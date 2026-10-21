"""
Tests for audit helper modules decomposed from audit_module.py.

Covers: lint, parsing, validators, report_helpers, activity_helpers,
activity_format_checks, activity_pedagogy_checks, activity_counting,
yaml_item_fixers, yaml_schema_fixes, phases_activity, phases_content,
phases_gates, phases_report.

Run with: pytest tests/test_audit_helpers.py -v
"""

import os
import sys

import pytest

pytestmark = pytest.mark.reads_content

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TEST: scripts/audit/lint.py
# =============================================================================



# =============================================================================
# TEST: scripts/audit/parsing.py
# =============================================================================



# =============================================================================
# TEST: scripts/audit/validators.py
# =============================================================================

from scripts.audit.validators import (
    validate_tone,
)


class TestValidateTone:

    def test_kiev_usage(self):
        errors = validate_tone("The city of Kiev is beautiful.")
        assert any("Kiev" in e for e in errors)


# =============================================================================
# TEST: scripts/audit/report_helpers.py
# =============================================================================

from scripts.audit.report_helpers import (
    compute_overall_status,
)


class TestComputeOverallStatus:
    def test_all_pass(self):
        gates = {
            'meta': {'status': 'pass', 'violations': 0, 'message': ''},
            'lesson': {'status': 'pass', 'violations': 0, 'message': ''},
        }
        result = compute_overall_status(gates, False, [])
        assert result['status'] == 'pass'
        assert result['pass_count'] == 2


# =============================================================================
# TEST: scripts/audit/checks/activity_helpers.py
# =============================================================================

from scripts.audit.checks.activity_helpers import (
    get_items,
)


class TestGetItems:

    def test_from_dict_returns_items_list(self):
        """get_items on a plain dict returns the 'items' list, NOT the
        dict.items() built-in method.  Regression for #1294."""
        activity_dict = {"type": "quiz", "items": [1, 2, 3]}
        assert get_items(activity_dict) == [1, 2, 3]


# =============================================================================
# TEST: scripts/audit/checks/activity_format_checks.py
# =============================================================================



# =============================================================================
# TEST: scripts/audit/checks/activity_pedagogy_checks.py
# =============================================================================



# =============================================================================
# TEST: scripts/audit/checks/activity_counting.py
# =============================================================================



# =============================================================================
# TEST: scripts/audit/checks/yaml_item_fixers.py
# =============================================================================

from scripts.audit.checks.yaml_item_fixers import (
    fix_error_correction_items,
)


class TestFixErrorCorrectionItems:
    def test_rename_text_to_sentence(self):
        activity = {'items': [{'text': 'Він читає', 'error': 'читає', 'answer': 'читав'}]}
        fixes = fix_error_correction_items(activity)
        assert activity['items'][0]['sentence'] == 'Він читає'
# =============================================================================
# TEST: scripts/audit/checks/yaml_schema_fixes.py
# =============================================================================



# =============================================================================
# TEST: scripts/audit/phases_activity.py (unit-testable parts)
# =============================================================================



if __name__ == '__main__':
    pytest.main([__file__, '-v'])
