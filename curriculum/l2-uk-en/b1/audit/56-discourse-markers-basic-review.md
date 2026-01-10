# Audit Report: 56-discourse-markers-basic.md
**Phase:** B1.5 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з маркерами' item 2 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з маркерами' item 4 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з маркерами' item 6 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY]** mark-the-words 'Знайдіть контрастні маркери' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[SECTION_ORDER]** '## Лексика' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[SECTION_ORDER]** Content section '## Діалоги' appears after end section '## Лексика'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[MISSING_FIELD]** mark-the-words 'Знайдіть контрастні маркери' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [match-function] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [sort-register] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [fill-contrast] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [fill-causal] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [quiz-explanation] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [quiz-generalization] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [cloze-news] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [cloze-academic] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [error-markers] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [unjumble-sentences] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [translate-markers] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [mark-contrast] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [select-multiple] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-discourse-markers-basic.yaml: [tf-usage] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Практика' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 22 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1659/1500
- **Activities:** ✅ 14/8
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 16/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 21 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 21 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.9% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ✅ 98% (vocabulary)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 19 | 20 | 95% | 25% | 23.8% |
| usage_examples | 21 | 15 | 100% | 20% | 20.0% |
| engagement | 16 | 4 | 100% | 15% | 15.0% |
| cultural | 7 | 3 | 100% | 10% | 10.0% |
| visual | 9 | 3 | 100% | 10% | 10.0% |
| register_notes | 15 | 5 | 100% | 10% | 10.0% |
| variety | 0.97 | - | 97% | 5% | 4.9% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **98.6%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Знайдіть контрастні маркери | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 49 | Included in Core |
| **Вступ** | ⚪️ | 89 | Skipped |
| **Лексика** | ⚪️ | 385 | Skipped |
| **Використання** | ⚪️ | 212 | Skipped |
| **Читання** | ✅ | 236 | Included in Core |
| **Діалоги** | ✅ | 254 | Included in Core |
| **Додаткові маркери** | ⚪️ | 144 | Skipped |
| **Підсумок** | ✅ | 180 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |