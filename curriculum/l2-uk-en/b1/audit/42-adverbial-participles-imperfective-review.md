# Audit Report: 42-adverbial-participles-imperfective.md
**Phase:** B1.4 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** mark-the-words 'Знайдіть дієприслівники недоконаного виду' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Знайдіть дієприслівники недоконаного виду' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-adverbial-participles-imperfective.yaml: [теоретичні-знання-про-дієприслівники-недоконаного-виду] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-adverbial-participles-imperfective.yaml: [інфінітив-та-відповідний-дієприслівник] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-adverbial-participles-imperfective.yaml: [утворення-дієприслівників-недоконаного-виду] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-adverbial-participles-imperfective.yaml: [правила-вживання-дієприслівників] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-adverbial-participles-imperfective.yaml: [класифікація-форм-дієприслівників] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-adverbial-participles-imperfective.yaml: [побудова-речень-з-дієприслівниками] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-adverbial-participles-imperfective.yaml: [виправлення-помилок-у-дієприслівникових-конструкціях] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-adverbial-participles-imperfective.yaml: [дієприслівники-в-контексті] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-adverbial-participles-imperfective.yaml: [знайдіть-дієприслівники-недоконаного-виду] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-adverbial-participles-imperfective.yaml: [вибір-правильного-дієприслівника] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-adverbial-participles-imperfective.yaml: [переклад-речень-з-дієприслівниками] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка|Тест' per template 'b1-grammar-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 14 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1705/1500
- **Activities:** ✅ 11/8
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 36/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 13 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 35 | 24 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| dialogues | 8 | 4 | 100% | 15% | 15.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| realworld | 3 | 3 | 100% | 10% | 10.0% |
| visual | 4 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 25 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.8%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Знайдіть дієприслівники недоконаного виду | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Діагностика** | ✅ | 98 | Included in Core |
| **Пояснення** | ⚪️ | 646 | Skipped |
| **Практика** | ⚪️ | 365 | Skipped |
| **Діалоги** | ✅ | 277 | Included in Core |
| **Підсумок** | ✅ | 137 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |