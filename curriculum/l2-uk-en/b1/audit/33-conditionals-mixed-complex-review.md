# Audit Report: 33-conditionals-mixed-complex.md
**Phase:** B1.3a | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 33-conditionals-mixed-complex.yaml: [виберіть-правильну-відповідь] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 33-conditionals-mixed-complex.yaml: [з'єднайте-умову-з-наслідком] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 33-conditionals-mixed-complex.yaml: [доповніть-речення-правильною-формою] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 33-conditionals-mixed-complex.yaml: [правда-чи-неправда?] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 33-conditionals-mixed-complex.yaml: [розподіліть-речення-за-типами] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 33-conditionals-mixed-complex.yaml: [складіть-речення-з-розсипаних-слів] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 33-conditionals-mixed-complex.yaml: [знайдіть-і-виправте-помилку] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 33-conditionals-mixed-complex.yaml: [заповніть-пропуски-в-тексті] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 33-conditionals-mixed-complex.yaml: [позначте-часові-маркери-та-сполучники-умови] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 33-conditionals-mixed-complex.yaml: [перекладіть-на-українську-мову] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 33-conditionals-mixed-complex.yaml: [виберіть-усі-речення-зі-змішаними-умовами] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 33 has 96.1% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 12 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1755/1500
- **Activities:** ✅ 11/8
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 17 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 11 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 96.1% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 39 | 24 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| dialogues | 16 | 4 | 100% | 15% | 15.0% |
| variety | 0.91 | - | 91% | 10% | 9.1% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 4 | 3 | 100% | 10% | 10.0% |
| visual | 7 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.99 | - | 99% | 5% | 5.0% |
| questions | 24 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.0%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Доповніть речення правильною формою | cloze | 8 | 12 | Add 4 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 52 | Included in Core |
| **Тест: Перевірте себе** | ⚪️ | 127 | Skipped |
| **Пояснення** | ⚪️ | 635 | Skipped |
| **Практика** | ⚪️ | 270 | Skipped |
| **Діалоги** | ✅ | 399 | Included in Core |
| **Підсумок** | ✅ | 162 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |