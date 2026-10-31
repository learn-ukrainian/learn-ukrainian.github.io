"""
Tests for plan validation (scripts/validate_plan_config.py).

Uses tmp_path fixtures to create test plan files.

Run with: pytest tests/test_plan_validation.py -v
"""

import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from scripts.validate_plan_config import get_config_target, validate_plan

# =============================================================================
# TEST: get_config_target
# =============================================================================


# =============================================================================
# TEST: validate_plan
# =============================================================================

class TestValidatePlan:
    def _write_plan(self, tmp_path, plan_data):
        """Helper to write a plan YAML file."""
        plan_path = tmp_path / "test-plan.yaml"
        with open(plan_path, 'w', encoding='utf-8') as f:
            yaml.dump(plan_data, f, allow_unicode=True)
        return plan_path

    def test_valid_plan(self, tmp_path):
        target = get_config_target('b1')
        plan = {
            'module': 'test-module',
            'level': 'B1',
            'title': 'Test Module',
            'objectives': ['Learn something'],
            'word_target': target,
            'content_outline': [
                {'section': 'Intro', 'words': target // 2},
                {'section': 'Body', 'words': target - (target // 2)},
            ],
        }
        path = self._write_plan(tmp_path, plan)
        errors = validate_plan(path, 'b1')
        assert len(errors) == 0

    def test_missing_word_target(self, tmp_path):
        plan = {
            'module': 'test-module',
            'level': 'B1',
            'title': 'Test Module',
            'objectives': ['Learn something'],
            'content_outline': [{'section': 'Intro', 'words': 500}],
        }
        path = self._write_plan(tmp_path, plan)
        errors = validate_plan(path, 'b1')
        assert errors == []

    def test_low_word_target_is_ignored(self, tmp_path):
        """A word target below the old config floor is not an error."""
        config_target = get_config_target('b1')
        plan = {
            'module': 'test-module',
            'level': 'B1',
            'title': 'Test Module',
            'objectives': ['Learn something'],
            'word_target': config_target // 2,  # Way too low
            'content_outline': [
                {'section': 'Intro', 'words': config_target // 2},
            ],
        }
        path = self._write_plan(tmp_path, plan)
        errors = validate_plan(path, 'b1')
        assert errors == []

    def test_valid_reviewed_size_policy_allows_bio_target_below_config(self, tmp_path):
        plan = {
            'module': 'test-module',
            'level': 'BIO',
            'title': 'Test Module',
            'objectives': ['Learn something'],
            'word_target': 4200,
            'content_outline': [{'section': 'Intro', 'words': 4200}],
            'size_policy': {
                'floor_words': 4200,
                'recommended_range': [4200, 4600],
                'ceiling_words': 4800,
                'basis': 'Bounded chronology with verified primary-source coverage.',
                'saturation_evidence': 'The dossier exhausts the available dated sources.',
                'exceptional_justification': 'required_above_ceiling',
            },
        }

        errors = validate_plan(self._write_plan(tmp_path, plan), 'bio')

        assert not any('word_target under config' in error for error in errors)

    def test_invalid_size_policy_does_not_fail_the_plan(self, tmp_path):
        plan = {
            'module': 'test-module',
            'level': 'BIO',
            'title': 'Test Module',
            'objectives': ['Learn something'],
            'word_target': 4200,
            'content_outline': [{'section': 'Intro', 'words': 4200}],
            'size_policy': {
                'floor_words': 4100,
                'recommended_range': [4100, 4600],
                'ceiling_words': 4800,
                'basis': '',
                'saturation_evidence': '',
                'exceptional_justification': 'optional',
            },
        }

        errors = validate_plan(self._write_plan(tmp_path, plan), 'bio')

        assert errors == []

    def test_missing_outline(self, tmp_path):
        target = get_config_target('b1')
        plan = {
            'module': 'test-module',
            'level': 'B1',
            'title': 'Test Module',
            'objectives': ['Learn something'],
            'word_target': target,
        }
        path = self._write_plan(tmp_path, plan)
        errors = validate_plan(path, 'b1')
        assert any('Missing content_outline' in e for e in errors)

    def test_outline_sum_is_ignored(self, tmp_path):
        target = get_config_target('b1')
        plan = {
            'module': 'test-module',
            'level': 'B1',
            'title': 'Test Module',
            'objectives': ['Learn something'],
            'word_target': target,
            'content_outline': [
                {'section': 'Intro', 'words': 100},  # Way too low
            ],
        }
        path = self._write_plan(tmp_path, plan)
        errors = validate_plan(path, 'b1')
        assert errors == []

    def test_empty_plan(self, tmp_path):
        plan_path = tmp_path / "empty.yaml"
        plan_path.write_text("", encoding='utf-8')
        errors = validate_plan(plan_path, 'b1')
        assert any('Empty' in e for e in errors)

    def test_missing_required_fields(self, tmp_path):
        plan = {
            'word_target': 2000,
            'content_outline': [{'section': 'Intro', 'words': 2000}],
        }
        path = self._write_plan(tmp_path, plan)
        errors = validate_plan(path, 'b1')
        # Should flag missing module, level, title, objectives
        assert any('module' in e for e in errors)
        assert any('title' in e for e in errors)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
