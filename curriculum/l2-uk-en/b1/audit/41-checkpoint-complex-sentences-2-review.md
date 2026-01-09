# Audit Report: 41-checkpoint-complex-sentences-2.md
**Phase:** B1.3b | **Level:** B1 | **Pedagogy:** TTT | **Target:** 800
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** mark-the-words 'Позначте сполучники складних речень' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Позначте сполучники складних речень' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [позначте-сполучники-складних-речень] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка|Тест' per template 'b1-grammar-module-template'
  - FIX: Add '## Warm-up' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Presentation|Grammar|Focus|Презентація|Граматика|Теорія|Пояснення' per template 'b1-grammar-module-template'
  - FIX: Add '## Presentation' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Practice|Exercises|Activity|Практика|Вправи' found: Practice:, Практика
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 7 violations (significant)
- Activity density below minimum

## Gates
- **Words:** ✅ 1876/800
- **Activities:** ✅ 14/10
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 4/3
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 5 < 10 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 100.0% (checkpoint - no gate)
- **Richness:** ❌ 84% < 85% min (checkpoint)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 84% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 11 | 8 | 100% | 25% | 25.0% |
| review_sections | 33 | 3 | 100% | 20% | 20.0% |
| variety | 0.88 | - | 88% | 15% | 13.2% |
| engagement | 3 | 3 | 100% | 10% | 10.0% |
| cultural | 0 | - | 0% | 10% | 0.0% |
| visual | 2 | 3 | 67% | 10% | 6.7% |
| paragraph_var | 1.00 | - | 100% | 10% | 10.0% |
| **TOTAL** | | | | | **84.9%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Позначте сполучники складних речень | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 142 | Included in Core |
| **Skill 1: Допустові речення** | ⚪️ | 143 | Skipped |
| **Skill 2: Причинові та наслідкові речення** | ⚪️ | 163 | Skipped |
| **Skill 3: Часові речення** | ⚪️ | 176 | Skipped |
| **Skill 4: Інтеграція типів підрядних речень** | ⚪️ | 163 | Skipped |
| **Skill 5: Непряма мова — твердження** | ⚪️ | 137 | Skipped |
| **Skill 6: Непряма мова — питання** | ⚪️ | 132 | Skipped |
| **Skill 7: Непряма мова — накази та прохання** | ⚪️ | 131 | Skipped |
| **Integration Challenge** | ⚪️ | 190 | Skipped |
| **Практика** | ⚪️ | 288 | Skipped |
| **Підсумок** | ✅ | 211 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |