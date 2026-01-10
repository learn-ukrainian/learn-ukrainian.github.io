# Audit Report: 30-purpose-shchob-past-form.md
**Phase:** B1.3a | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-purpose-shchob-past-form.yaml: [конструкція-щоб-плюс-минула-форма] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-purpose-shchob-past-form.yaml: [дієслово-і-приклад-конструкції] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-purpose-shchob-past-form.yaml: [оберіть-правильну-форму-дієслова] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-purpose-shchob-past-form.yaml: [правда-чи-неправда?] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-purpose-shchob-past-form.yaml: [категорії-дієслів-з-конструкцією-щоб] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-purpose-shchob-past-form.yaml: [розставте-слова-в-правильному-порядку] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-purpose-shchob-past-form.yaml: [знайдіть-і-виправте-помилку] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-purpose-shchob-past-form.yaml: [щоб-плюс-минула-форма-в-контексті] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-purpose-shchob-past-form.yaml: [знайдіть-минулі-форми-після-щоб] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-purpose-shchob-past-form.yaml: [оберіть-усі-правильні-варіанти] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-purpose-shchob-past-form.yaml: [перекладіть-речення] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 30 has 96.9% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## Recommendation
**🔄 REWRITE** (severity 75/100)

- 12 violations (severe - consider revision)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1725/1500
- **Activities:** ❌ 0/8
- **Density:** ❌ 0 < 12
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 30/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 11 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 96.9% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 42 | 24 | 100% | 20% | 20.0% |
| engagement | 10 | 5 | 100% | 15% | 15.0% |
| dialogues | 14 | 4 | 100% | 15% | 15.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 4 | 3 | 100% | 10% | 10.0% |
| visual | 12 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 26 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 61 | Included in Core |
| **Тест: Перевірте себе** | ⚪️ | 117 | Skipped |
| **Пояснення** | ⚪️ | 517 | Skipped |
| **Практика** | ⚪️ | 412 | Skipped |
| **Діалоги** | ✅ | 353 | Included in Core |
| **Підсумок** | ✅ | 155 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |