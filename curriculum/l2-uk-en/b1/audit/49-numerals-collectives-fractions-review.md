# Audit Report: 49-numerals-collectives-fractions.md
**Phase:** B1.4 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** mark-the-words 'Знайдіть числівники' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Знайдіть числівники' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [побудуйте-речення] unjumble: 'items.5' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [знайдіть-числівники] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 5 violations (moderate)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1620/1500
- **Activities:** ❌ 11/12
- **Density:** ❌ 2 < 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 18/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 34/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 4 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.8% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ✅ 98% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 57 | 24 | 100% | 20% | 20.0% |
| engagement | 15 | 5 | 100% | 15% | 15.0% |
| dialogues | 18 | 4 | 100% | 15% | 15.0% |
| variety | 0.89 | - | 89% | 10% | 8.9% |
| cultural | 6 | 3 | 100% | 10% | 10.0% |
| realworld | 13 | 3 | 100% | 10% | 10.0% |
| visual | 14 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 34 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **98.9%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Виберіть правильну форму | cloze | 8 | 14 | Add 6 more items |
| Знайдіть числівники | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 50 | Included in Core |
| **Тест** | ⚪️ | 230 | Skipped |
| **Пояснення** | ⚪️ | 366 | Skipped |
| **Дроби та відсотки** | ⚪️ | 325 | Skipped |
| **Практика** | ⚪️ | 181 | Skipped |
| **Діалоги** | ✅ | 309 | Included in Core |
| **Підсумок** | ✅ | 159 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |