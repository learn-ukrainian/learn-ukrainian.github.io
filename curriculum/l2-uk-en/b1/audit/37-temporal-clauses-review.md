# Audit Report: 37-temporal-clauses.md
**Phase:** B1.3b | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** mark-the-words 'Позначте часові сполучники' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Позначте часові сполучники' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-temporal-clauses.yaml: [часові-сполучники] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-temporal-clauses.yaml: [сполучник-та-його-функція] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-temporal-clauses.yaml: [доповніть-речення-правильним-сполучником] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-temporal-clauses.yaml: [правда-чи-неправда?] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-temporal-clauses.yaml: [розподіліть-сполучники-за-типом-часових-відношень] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-temporal-clauses.yaml: [складіть-речення-з-розсипаних-слів] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-temporal-clauses.yaml: [знайдіть-і-виправте-помилку] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-temporal-clauses.yaml: [заповніть-пропуски-в-тексті] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-temporal-clauses.yaml: [позначте-часові-сполучники] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-temporal-clauses.yaml: [виберіть-усі-граматично-правильні-речення] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-temporal-clauses.yaml: [перекладіть-на-українську-мову] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 13 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1577/1500
- **Activities:** ✅ 11/8
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 14 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 13 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.9% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 95% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 36 | 24 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| dialogues | 13 | 4 | 100% | 15% | 15.0% |
| variety | 0.92 | - | 92% | 10% | 9.2% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 3 | 3 | 100% | 10% | 10.0% |
| visual | 6 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.97 | - | 97% | 5% | 4.9% |
| questions | 24 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **95.8%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Позначте часові сполучники | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 61 | Included in Core |
| **Тест** | ⚪️ | 154 | Skipped |
| **Пояснення** | ⚪️ | 632 | Skipped |
| **Практика** | ⚪️ | 217 | Skipped |
| **Діалоги** | ✅ | 225 | Included in Core |
| **Підсумок** | ✅ | 178 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |