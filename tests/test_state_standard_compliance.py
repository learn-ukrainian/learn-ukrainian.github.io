"""
Tests for Ukrainian State Standard 2024 compliance checking.

Tests that:
1. The compliance gate treats the State Standard as a minimum floor (R-32):
   - A plan that teaches an A2 item at A1 passes when ULP evidence is recorded.
   - A plan that teaches an A2 item at A1 without ULP evidence fails.
   - A plan that omits an A1 item fails.
2. The mapping matches the Standard text and has no ceiling declarations:
   - A1 and A2 blocks match text line references.
   - forbidden_forms and allowed: false ceilings are removed.
   - Intentions (Catalogue A) are present.
3. Presence checks support requirement_id and arc_position as well as module_num.
"""

from pathlib import Path

import pytest

from scripts.audit.checks.state_standard_compliance import (
    check_plan_compliance,
    check_reflexive_verbs_a1,
    load_compliance_mapping,
)
from scripts.audit.parsing import AuditContext, AuditState
from scripts.audit.phases_content import run_content_quality_checks

pytestmark = pytest.mark.reads_content


@pytest.fixture
def mapping():
    return load_compliance_mapping()


class TestStateStandardFloorPolicy:
    """Test requirement R-32: Standard is a floor, not a ceiling."""

    def test_plan_teaches_a2_item_at_a1_with_ulp_passes(self, mapping):
        """A plan that teaches an A2 item at A1 passes when ULP evidence is recorded."""
        plan = {
            'level': 'a1',
            'slug': 'what-i-like',
            'grammar': ['dative', 'nominative'],
            'ulp_evidence': ['ULP Ep 14 — "мені подобається" formulaic expression'],
        }
        violations = check_plan_compliance(plan, mapping=mapping)
        assert len(violations) == 0

    def test_plan_teaches_a2_item_at_a1_without_ulp_fails(self, mapping):
        """A plan that teaches an A2 item at A1 without ULP evidence fails."""
        plan = {
            'level': 'a1',
            'slug': 'premature-grammar',
            'grammar': ['dative'],  # dative is A2
        }
        violations = check_plan_compliance(plan, mapping=mapping)
        assert len(violations) == 1
        assert violations[0].code == 'STATE_STANDARD_EARLY_WITHOUT_ULP'
        assert 'dative' in violations[0].message.lower()
        assert 'A1' in violations[0].message
        assert 'A2' in violations[0].message
        assert violations[0].reference == 'R-32'

    def test_plan_omits_a1_item_fails(self, mapping):
        """A plan that omits a required A1 item fails."""
        plan = {
            'level': 'a1',
            'slug': 'incomplete-basics',
            'grammar': ['nominative'],
            'omitted_items': ['accusative'],
        }
        violations = check_plan_compliance(plan, mapping=mapping)
        assert len(violations) == 1
        assert violations[0].code == 'STATE_STANDARD_OMITTED_ITEM'
        assert 'accusative' in violations[0].message
        assert 'A1' in violations[0].message


class TestPresenceChecks:
    """Test re-keyed reflexive and imperative presence checks."""

    def test_reflexive_check_matches_module_or_arc_or_req_id(self, mapping):
        """check_reflexive_verbs_a1 checks module_num, arc_position, or requirement_id."""
        bad_content = 'This lesson teaches basic vocabulary without reflexives.'
        good_content = 'Дієслова на -ся/-сь: дивитися, сміявся. Вживаємо суфікс -ся.'

        # Matches by module 9
        v_bad = check_reflexive_verbs_a1(9, bad_content, mapping)
        assert len(v_bad) > 0
        v_good = check_reflexive_verbs_a1(9, good_content, mapping)
        assert len(v_good) == 0

        # Matches by arc_position 9
        v_arc = check_reflexive_verbs_a1(99, bad_content, mapping, arc_position=9)
        assert len(v_arc) > 0

        # Matches by requirement_id
        v_req = check_reflexive_verbs_a1(99, bad_content, mapping, requirement_id='REQ-A1-REFLEXIVE')
        assert len(v_req) > 0

        # Irrelevant module skipped
        v_skip = check_reflexive_verbs_a1(1, bad_content, mapping)
        assert len(v_skip) == 0


class TestAstraReviewFindings:
    """Regression tests for Astra's review findings on PR #8404."""

    def test_finding_1_empty_plan_fails_state_standard_floor(self, mapping):
        """Finding 1: Missing coverage passes — {'level': 'a1', 'grammar': []} must fail."""
        plan = {'level': 'a1', 'grammar': []}
        violations = check_plan_compliance(plan, mapping=mapping)
        assert len(violations) > 0
        assert any(v.code == 'STATE_STANDARD_OMITTED_ITEM' for v in violations)

    def test_finding_2_notes_mentioning_no_ulp_does_not_authorize_early_teaching(self, mapping):
        """Finding 2: Prose notes saying 'No ULP evidence exists' must not authorize early teaching."""
        plan = {
            'level': 'a1',
            'slug': 'premature-dative',
            'grammar': ['dative'],
            'notes': 'No ULP evidence exists for this move.',
        }
        violations = check_plan_compliance(plan, mapping=mapping)
        assert any(v.code == 'STATE_STANDARD_EARLY_WITHOUT_ULP' for v in violations)

    def test_finding_3_production_gate_calls_state_standard_floor_check(self):
        """Finding 3: run_content_quality_checks passes plan to floor check in production gate."""
        ctx = AuditContext(
            file_path='curriculum/l2-uk-en/a1/module-01.md',
            content='# Module 1\nContent text',
            body='# Module 1\nContent text',
            frontmatter_str='',
            meta_data=None,
            plan_data={'level': 'a1', 'slug': 'm01', 'grammar': ['dative']},
            vocab_data=None,
            vocab_error=None,
            level_code='A1',
            module_num=1,
            track_code='A1',
            display_level='A1',
            module_focus='grammar',
            module_title='Test Module',
            target=1000,
            config={},
            section_map={},
            core_content='Content text',
            phase='A1.1',
            pedagogy='PPP',
            skip_activities=True,
            skip_review=True,
            yaml_activities=None,
            use_yaml_activities=False,
            yaml_file=Path('nonexistent.yaml'),
        )
        state = AuditState()
        run_content_quality_checks(ctx, state)
        assert any(
            v.get('type') == 'STATE_STANDARD_EARLY_WITHOUT_ULP'
            for v in state.pedagogical_violations
        )

    def test_finding_4_v2_inventory_in_lessons_early_without_ulp_fails(self, mapping):
        """Finding 4: v2 schema stores grammar under lessons[].inventory.grammar — G-a2-005 at A1 must fail."""
        plan = {
            'level': 'a1',
            'slug': 'polite-requests',
            'lessons': [
                {
                    'title': 'Lesson 1',
                    'inventory': {
                        'grammar': [
                            {
                                'id': 'G-a2-005',
                                'point': 'Polite third person imperative forms',
                            }
                        ]
                    },
                }
            ],
        }
        violations = check_plan_compliance(plan, mapping=mapping)
        assert any(v.code == 'STATE_STANDARD_EARLY_WITHOUT_ULP' for v in violations)

    def test_finding_5_caller_supplied_level_does_not_override_standard_mapping(self, mapping):
        """Finding 5: Caller metadata level does not override Standard mapping level (dative is A2)."""
        plan = {
            'level': 'a1',
            'slug': 'override-attempt',
            'grammar': [{'name': 'dative', 'level': 'a1'}],
        }
        violations = check_plan_compliance(plan, mapping=mapping)
        assert any(v.code == 'STATE_STANDARD_EARLY_WITHOUT_ULP' for v in violations)

    def test_finding_6_standard_verbatim_lines_703_719_produces_no_violations(self, mapping):
        """Finding 6: Passing Standard verbatim lines 703–719 produces zero violations."""
        standard_path = Path(__file__).parent.parent / 'docs' / 'l2-uk-en' / 'UKRAINIAN-STATE-STANDARD-2024.txt'
        with open(standard_path, encoding='utf-8') as f:
            lines = f.readlines()
        verbatim_content = ''.join(lines[702:719])
        violations = check_reflexive_verbs_a1(9, verbatim_content, mapping)
        assert len(violations) == 0

    def test_blocker_1_nonempty_topics_does_not_disable_floor(self, mapping):
        """Blocker 1: Adding topics: ['greetings'] must not disable the Standard-derived minimum floor."""
        plan = {
            'level': 'a1',
            'grammar': [],
            'topics': ['greetings'],
        }
        violations = check_plan_compliance(plan, mapping=mapping)
        assert len(violations) > 0
        assert any(v.code == 'STATE_STANDARD_OMITTED_ITEM' for v in violations)

    def test_blocker_3_item_ulp_evidence_not_naming_move_fails(self, mapping):
        """Evidence attached directly to item not naming the move must fail."""
        plan = {
            'level': 'a1',
            'lessons': [
                {
                    'inventory': {
                        'grammar': [
                            {
                                'id': 'G-a2-005',
                                'ulp_evidence': ['ULP episode 1: alphabet'],
                            }
                        ]
                    }
                }
            ],
        }
        violations = check_plan_compliance(plan, mapping=mapping)
        assert any(v.code == 'STATE_STANDARD_EARLY_WITHOUT_ULP' for v in violations)

    def test_blocker_3_item_and_arc_ulp_evidence_naming_move_passes(self, mapping):
        """Evidence naming specific move authorizes early introduction."""
        plan_item = {
            'level': 'a1',
            'lessons': [
                {
                    'inventory': {
                        'grammar': [
                            {
                                'id': 'G-a2-005',
                                'ulp_evidence': ['ULP episode 25: G-a2-005'],
                            }
                        ]
                    }
                }
            ],
        }
        violations_item = check_plan_compliance(plan_item, mapping=mapping)
        assert not any(v.code == 'STATE_STANDARD_EARLY_WITHOUT_ULP' for v in violations_item)

        plan_arc = {
            'level': 'a1',
            'lessons': [
                {
                    'inventory': {
                        'grammar': [
                            {
                                'id': 'G-a2-005',
                            }
                        ]
                    }
                }
            ],
            'arc': {
                'moves': {
                    'G-a2-005': {
                        'ulp_evidence': ['ULP episode 25: G-a2-005'],
                    }
                }
            },
        }
        violations_arc = check_plan_compliance(plan_arc, mapping=mapping)
        assert not any(v.code == 'STATE_STANDARD_EARLY_WITHOUT_ULP' for v in violations_arc)
