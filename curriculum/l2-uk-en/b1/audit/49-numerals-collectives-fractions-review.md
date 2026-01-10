# Audit Report: 49-numerals-collectives-fractions.md
**Phase:** B1.4 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** mark-the-words 'Знайдіть числівники' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Знайдіть числівники' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [розуміння-збірних-числівників] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [кількісні-та-збірні-числівники] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [виберіть-правильну-форму] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [правила-числівників] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [тип-числівника] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [побудуйте-речення] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [виправте-помилки] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [статистичний-звіт] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [знайдіть-числівники] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [правильні-форми] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 49-numerals-collectives-fractions.yaml: [перекладіть-українською] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 13 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1730/1500
- **Activities:** ✅ 11/8
- **Density:** ❌ 2 < 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 19/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 34/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 13 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.0% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ✅ 98% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 58 | 24 | 100% | 20% | 20.0% |
| engagement | 16 | 5 | 100% | 15% | 15.0% |
| dialogues | 18 | 4 | 100% | 15% | 15.0% |
| variety | 0.90 | - | 90% | 10% | 9.0% |
| cultural | 6 | 3 | 100% | 10% | 10.0% |
| realworld | 13 | 3 | 100% | 10% | 10.0% |
| visual | 14 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 34 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.0%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Виберіть правильну форму | cloze | 8 | 12 | Add 4 more items |
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
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |