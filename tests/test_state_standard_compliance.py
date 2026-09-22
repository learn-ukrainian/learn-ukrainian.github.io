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
    check_immersion_compliance,
    check_imperative_complete_a2,
    check_plan_compliance,
    check_reflexive_verbs_a1,
    check_state_standard_compliance,
    find_item_standard_level,
    load_compliance_mapping,
)
from scripts.audit.parsing import AuditContext, AuditState
from scripts.audit.phases_content import run_content_quality_checks


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

    def test_plan_teaches_a2_grammar_point_with_ulp_passes(self, mapping):
        """Plan with v2 G-a2 point and ULP pack evidence passes at A1."""
        plan = {
            'level': 'a1',
            'slug': 'polite-requests',
            'inventory': {
                'grammar': [
                    {
                        'id': 'G-a2-005',
                        'point': 'Polite third person imperative forms',
                        'evidence': ['ULP-25', 'T-102'],
                    }
                ]
            },
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

    def test_plan_missing_required_items_fails(self, mapping):
        """A plan failing to cover its declared required_items fails."""
        plan = {
            'level': 'a1',
            'slug': 'verbs-lesson',
            'required_items': ['nominative', 'reflexive_verbs'],
            'grammar': ['nominative'],  # reflexive_verbs is missing
        }
        violations = check_plan_compliance(plan, mapping=mapping)
        assert len(violations) == 1
        assert violations[0].code == 'STATE_STANDARD_OMITTED_ITEM'
        assert 'reflexive_verbs' in violations[0].message

    def test_plan_standard_a1_passes(self, mapping):
        """A normal A1 plan covering A1 items passes."""
        plan = {
            'level': 'a1',
            'slug': 'first-nouns',
            'grammar': ['nominative', 'accusative'],
        }
        violations = check_plan_compliance(plan, mapping=mapping)
        assert len(violations) == 0

    def test_find_item_standard_level(self, mapping):
        """find_item_standard_level correctly locates earliest level."""
        assert find_item_standard_level('nominative', mapping) == 'a1'
        assert find_item_standard_level('dative', mapping) == 'a2'
        assert find_item_standard_level('imperative_complete', mapping) == 'a2'
        assert find_item_standard_level('person_names', mapping) == 'b1'


class TestMappingVerificationA1:
    """Verify that A1 mapping matches UKRAINIAN-STATE-STANDARD-2024.txt."""

    def test_a1_accusative_prepositions_no_za_cherez(self, mapping):
        """A1 accusative prepositions are в/у, на, про; no 'за', 'через' (issue #8404: :84)."""
        acc = mapping['a1']['cases']['accusative']
        desc = acc['description']
        assert 'за' not in desc
        assert 'через' not in desc
        assert 'про' in desc
        assert acc['lines'] == [678, 688]

    def test_a1_locative_no_po(self, mapping):
        """A1 locative prepositions are у, в, на; no 'по'."""
        import re
        loc = mapping['a1']['cases']['locative']
        assert re.search(r'\bпо\b', loc['description']) is None
        assert loc['lines'] == [690, 695]

    def test_a1_complex_sentences_no_shcho_koly_de(self, mapping):
        """A1 complex sentences has only і (й), але, тому що, бо (issue #8404: :126)."""
        complex_sent = mapping['a1']['syntax']['complex_sentence']
        desc = complex_sent['description']
        assert 'і (й)' in desc
        assert 'але' in desc
        assert 'тому що' in desc
        assert 'бо' in desc
        # Ensure що, коли, де are not in A1 complex sentence description
        assert 'коли' not in desc
        assert complex_sent['lines'] == [741, 747]

    def test_a1_no_ceilings(self, mapping):
        """A1 mapping must not declare forbidden_forms or allowed: false ceilings."""
        cases = mapping['a1']['cases']
        # Dative and instrumental should not be marked allowed: false
        assert 'allowed' not in cases.get('dative', {})
        assert 'allowed' not in cases.get('instrumental', {})
        # Imperative should not declare forbidden_forms
        imperative = mapping['a1']['verbs']['imperative']
        assert 'forbidden_forms' not in imperative

    def test_a1_has_intentions(self, mapping):
        """A1 mapping includes Catalogue A communicative intentions."""
        assert 'intentions' in mapping['a1']
        assert mapping['a1']['intentions']['lines'] == [453, 477]
        assert len(mapping['a1']['intentions']['items']) > 10


class TestMappingVerificationA2:
    """Verify that A2 mapping matches UKRAINIAN-STATE-STANDARD-2024.txt."""

    def test_a2_genitive_prepositions(self, mapping):
        """A2 genitive prepositions: з/із/зі, до, для, біля, навпроти; no без, від, після, коло (:187)."""
        gen = mapping['a2']['cases']['genitive']
        desc = gen['description']
        prep_part = desc.split('із прийменниками')[1]
        for prep in ('без', 'від', 'після', 'коло'):
            assert prep not in prep_part
        for prep in ('до', 'для', 'біля', 'навпроти'):
            assert prep in prep_part
        assert gen['lines'] == [1265, 1285]

    def test_a2_dative_no_impersonal(self, mapping):
        """A2 dative is beneficiary and age only; no impersonal constructions (:191)."""
        dat = mapping['a2']['cases']['dative']
        desc = dat['description']
        assert 'impersonal' not in desc.lower()
        assert 'холодно' not in desc
        assert dat['lines'] == [1287, 1291]

    def test_a2_accusative_no_pid_nad_mizh(self, mapping):
        """A2 accusative has в, у, на, про; no під, над, між (:197)."""
        acc = mapping['a2']['cases']['accusative']
        desc = acc['description']
        for prep in ('під', 'над', 'між'):
            assert prep not in desc
        assert acc['lines'] == [1293, 1302]

    def test_a2_nominative_no_passive_comparative(self, mapping):
        """A2 nominative has no passive or comparative constructions (:183)."""
        nom = mapping['a2']['cases']['nominative']
        desc = nom['description']
        assert 'passive' not in desc.lower()
        assert 'comparative' not in desc.lower()
        assert nom['lines'] == [1258, 1263]

    def test_a2_pronouns_personal_possessive_only(self, mapping):
        """A2 pronouns are personal and possessive only (:176)."""
        pron = mapping['a2']['morphology']['pronoun']
        desc = pron['description']
        assert 'demonstrative' not in desc.lower()
        assert 'interrogative' not in desc.lower()
        assert 'вказівн' not in desc.lower()
        assert 'особові' in desc
        assert 'присвійні' in desc
        assert pron['lines'] == [1244, 1254]

    def test_a2_numerals_ordinals_and_odyn_only(self, mapping):
        """A2 numerals are ordinals + один (:172)."""
        num = mapping['a2']['morphology']['numeral']
        desc = num['description']
        assert 'cardinals' not in desc.lower()
        assert 'порядкових' in desc
        assert 'один' in desc
        assert num['lines'] == [1235, 1242]

    def test_a2_imperative_no_1st_plural(self, mapping):
        """A2 imperative is 2nd and 3rd person only; 1pl is B1 (:222)."""
        imp = mapping['a2']['verbs']['imperative']
        desc = imp['description']
        assert 'читаймо' not in desc
        assert '1st person plural' not in desc
        assert '3-ї особи' in desc or '3rd_person' in imp.get('required_forms', [])
        assert imp['lines'] == [1361, 1365]

    def test_a2_complex_sentences(self, mapping):
        """A2 complex sentences match :1403-1416; no якщо, хоча, який (:253)."""
        cs = mapping['a2']['syntax']['complex_sentence']
        desc = cs['description']
        for absent in ('якщо', 'хоча', 'який', 'для того щоб'):
            assert absent not in desc
        for present in ('де', 'куди', 'звідки', 'що', 'тому що', 'бо', 'щоб'):
            assert present in desc
        assert cs['lines'] == [1403, 1416]

    def test_a2_interrogatives(self, mapping):
        """A2 interrogatives do not have скільки, чому, який (:245)."""
        interrogative = mapping['a2']['syntax']['interrogative']
        desc = interrogative['description']
        for word in ('скільки', 'чому'):
            assert word not in desc
        assert interrogative['lines'] == [1391, 1398]

    def test_a2_stylistics(self, mapping):
        """A2 stylistics has antonyms, synonyms, epithets, metaphors; no diminutives (:260)."""
        lex = mapping['a2']['stylistics']['lexical']
        desc = lex['description']
        assert 'diminutives' not in desc.lower()
        assert 'colloquial' not in desc.lower()
        assert 'антоніми' in desc
        assert 'синоніми' in desc
        assert 'епітети' in desc
        assert 'метафори' in desc
        assert lex['lines'] == [1420, 1425]

    def test_a2_declarative(self, mapping):
        """A2 declarative is affirmative vs negative (:241)."""
        decl = mapping['a2']['syntax']['declarative']
        desc = decl['description']
        assert 'expanded word order' not in desc.lower()
        assert 'стверджувальне' in desc
        assert 'заперечне' in desc
        assert decl['lines'] == [1387, 1389]

    def test_a2_phonetics_alternations(self, mapping):
        """A2 phonetics is vowel/consonant alternations (:145)."""
        vc = mapping['a2']['phonetics']['vowels_consonants']
        desc = vc['description']
        assert 'assimilation' not in desc.lower()
        assert 'Чергування' in desc or 'чергування' in desc
        assert vc['lines'] == [1176, 1181]

    def test_a2_has_intentions_and_immersion(self, mapping):
        """A2 mapping has Catalogue A and immersion key."""
        assert 'intentions' in mapping['a2']
        assert mapping['a2']['intentions']['lines'] == [1029, 1070]
        assert 'immersion' in mapping['a2']


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

    def test_imperative_check_matches_module_or_arc_or_req_id(self, mapping):
        """check_imperative_complete_a2 checks module_num, arc_position, or requirement_id."""
        bad_content = 'This lesson has no 3rd person imperative.'
        good_content = 'Наказовий спосіб 3-ї особи: хай читає, нехай приходить.'

        # Matches by module 23
        v_bad = check_imperative_complete_a2(23, bad_content, mapping)
        assert len(v_bad) > 0
        v_good = check_imperative_complete_a2(23, good_content, mapping)
        assert len(v_good) == 0

        # Matches by arc_position 23
        v_arc = check_imperative_complete_a2(99, bad_content, mapping, arc_position=23)
        assert len(v_arc) > 0

        # Matches by requirement_id
        v_req = check_imperative_complete_a2(99, bad_content, mapping, requirement_id='REQ-A2-IMPERATIVE-3RD')
        assert len(v_req) > 0


class TestCheckStateStandardComplianceIntegration:
    """Test integrated check_state_standard_compliance function."""

    def test_backwards_compatible_call(self):
        """Original signature (level, module_num, content, immersion_pct) works."""
        violations = check_state_standard_compliance(
            level='A1',
            module_num=1,
            content='Це студент. Він читає.',
            immersion_pct=None,
        )
        assert isinstance(violations, list)
        assert len(violations) == 0

    def test_with_plan_floor_check(self):
        """Passing plan to check_state_standard_compliance runs floor checks."""
        # A2 item taught at A1 without ULP
        violations = check_state_standard_compliance(
            level='A1',
            module_num=1,
            content='',
            plan={'level': 'a1', 'grammar': ['dative']},
        )
        assert any(v.code == 'STATE_STANDARD_EARLY_WITHOUT_ULP' for v in violations)

        # A2 item taught at A1 with ULP
        violations_ulp = check_state_standard_compliance(
            level='A1',
            module_num=1,
            content='',
            plan={'level': 'a1', 'grammar': ['dative'], 'ulp_evidence': ['ULP Ep 14 — "мені подобається" formulaic expression']},
        )
        assert not any(v.code == 'STATE_STANDARD_EARLY_WITHOUT_ULP' for v in violations_ulp)

    def test_immersion_compliance(self, mapping):
        """Immersion compliance flags low immersion for B1+."""
        violations = check_immersion_compliance('b1', 10, 85.0, mapping)
        assert len(violations) == 1
        assert violations[0].code == 'STATE_STANDARD_LOW_IMMERSION'


class TestAstraReviewFindings:
    """Regression tests for Astra's review findings on PR #8404."""

    def test_finding_1_empty_plan_fails_state_standard_floor(self, mapping):
        """Finding 1: Missing coverage passes — {'level': 'a1', 'grammar': []} must fail."""
        plan = {'level': 'a1', 'grammar': []}
        violations = check_plan_compliance(plan, mapping=mapping)
        assert len(violations) > 0
        assert any(v.code == 'STATE_STANDARD_OMITTED_ITEM' for v in violations)

    def test_finding_1_removing_item_and_declaration_fails(self, mapping):
        """Finding 1: Removing an item and its declaration must fail (Standard mapping is authority)."""
        # Module 9 at A1 requires reflexive_verbs per the Standard mapping
        plan = {
            'level': 'a1',
            'module': 9,
            'slug': 'verbs-lesson',
            'grammar': ['nominative'],  # reflexive_verbs removed from grammar and not in required_items
        }
        violations = check_plan_compliance(plan, mapping=mapping)
        assert any(v.code == 'STATE_STANDARD_OMITTED_ITEM' and 'reflexive_verbs' in v.message for v in violations)

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

    def test_finding_2_bare_boolean_ulp_evidence_does_not_authorize_early_teaching(self, mapping):
        """Finding 2: Bare boolean ulp_evidence: true must not authorize early teaching without actual evidence."""
        plan = {
            'level': 'a1',
            'slug': 'premature-dative',
            'grammar': ['dative'],
            'ulp_evidence': True,
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
