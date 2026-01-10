# Audit Report: 35-concessive-khocha.md
**Phase:** B1.3b | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** mark-the-words 'Позначте допустові сполучники та підсилювальні слова' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Позначте допустові сполучники та підсилювальні слова' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-concessive-khocha.yaml: [виберіть-правильну-відповідь] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-concessive-khocha.yaml: [з'єднайте-сполучник-з-функцією] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-concessive-khocha.yaml: [доповніть-речення-правильною-формою] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-concessive-khocha.yaml: [правда-чи-неправда?] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-concessive-khocha.yaml: [розподіліть-конструкції-за-типами] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-concessive-khocha.yaml: [складіть-речення-з-розсипаних-слів] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-concessive-khocha.yaml: [знайдіть-і-виправте-помилку] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-concessive-khocha.yaml: [заповніть-пропуски-в-тексті] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-concessive-khocha.yaml: [позначте-допустові-сполучники-та-підсилювальні-слова] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-concessive-khocha.yaml: [виберіть-усі-граматично-правильні-речення] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-concessive-khocha.yaml: [перекладіть-на-українську-мову] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 35 has 96.9% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 14 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1728/1500
- **Activities:** ✅ 11/8
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 15 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 13 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 96.9% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 95% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 44 | 24 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| dialogues | 15 | 4 | 100% | 15% | 15.0% |
| variety | 0.95 | - | 95% | 10% | 9.5% |
| cultural | 6 | 3 | 100% | 10% | 10.0% |
| realworld | 2 | 3 | 67% | 10% | 6.7% |
| visual | 9 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.92 | - | 92% | 5% | 4.6% |
| questions | 21 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **95.8%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Позначте допустові сполучники та підсилювальні слова | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 59 | Included in Core |
| **Тест: Перевірте себе** | ⚪️ | 105 | Skipped |
| **Пояснення** | ⚪️ | 728 | Skipped |
| **Практика** | ⚪️ | 223 | Skipped |
| **Діалоги** | ✅ | 337 | Included in Core |
| **Підсумок** | ✅ | 166 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |