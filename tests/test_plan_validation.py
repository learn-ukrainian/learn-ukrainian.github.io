"""
Tests for plan validation (scripts/validate_plan_config.py).

Uses tmp_path fixtures to create test plan files.

Run with: pytest tests/test_plan_validation.py -v
"""

import pytest
import sys
import os
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from scripts.validate_plan_config import get_config_target, validate_plan


# =============================================================================
# TEST: get_config_target
# =============================================================================

class TestGetConfigTarget:
    def test_a1_target(self):
        target = get_config_target('a1')
        assert isinstance(target, int)
        assert target > 0

    def test_b2_hist_target(self):
        target = get_config_target('b2-hist')
        assert isinstance(target, int)
        assert target >= 2000

    def test_c1_bio_target(self):
        target = get_config_target('c1-bio')
        assert isinstance(target, int)
        assert target >= 2000

    def test_lit_target(self):
        target = get_config_target('lit')
        assert isinstance(target, int)
        assert target > 0


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
        assert any('Missing word_target' in e for e in errors)

    def test_target_mismatch(self, tmp_path):
        """Plan target significantly below config = error."""
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
        assert any('word_target under config' in e for e in errors)

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

    def test_outline_sum_mismatch(self, tmp_path):
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
        assert any("doesn't match" in e for e in errors)

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

    def test_over_target_allowed(self, tmp_path):
        """Plan target above config target is fine (more content is good)."""
        config_target = get_config_target('b1')
        plan = {
            'module': 'test-module',
            'level': 'B1',
            'title': 'Test Module',
            'objectives': ['Learn something'],
            'word_target': config_target + 1000,
            'content_outline': [
                {'section': 'Intro', 'words': (config_target + 1000) // 2},
                {'section': 'Body', 'words': config_target + 1000 - ((config_target + 1000) // 2)},
            ],
        }
        path = self._write_plan(tmp_path, plan)
        errors = validate_plan(path, 'b1')
        # No word_target errors (over is allowed)
        target_errors = [e for e in errors if 'word_target' in e]
        assert len(target_errors) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
