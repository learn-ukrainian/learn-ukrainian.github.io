# Audit Report: 34-checkpoint-complex-sentences-1.md
**Phase:** B1.3a | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1200
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** mark-the-words 'Позначте сполучники й відносні слова' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Позначте сполучники й відносні слова' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [відносні-речення-(м26-28)] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [підрядні-речення-мети-(м29-30)] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [умовні-речення-(м31-33)] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [з'єднайте-тип-речення-з-прикладом] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [інтегрований-тест] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [розподіліть-речення-за-типами] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [комплексний-тест] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [комплексний-тест] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [комплексний-текст] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [позначте-сполучники-й-відносні-слова] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [виберіть-усі-граматично-правильні-речення] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [комплексний-переклад] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка|Тест' per template 'b1-grammar-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 16 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ⚠️ 1173/1200 (27 short)
- **Activities:** ✅ 12/10
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 4/3
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 7 < 10 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 14 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.4% (checkpoint - no gate)
- **Richness:** ✅ 91% (checkpoint)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 91% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 10 | 8 | 100% | 25% | 25.0% |
| review_sections | 20 | 3 | 100% | 20% | 20.0% |
| variety | 0.96 | - | 96% | 15% | 14.4% |
| engagement | 3 | 3 | 100% | 10% | 10.0% |
| cultural | 4 | - | 100% | 10% | 10.0% |
| visual | 1 | 3 | 33% | 10% | 3.3% |
| paragraph_var | 0.84 | - | 84% | 10% | 8.4% |
| **TOTAL** | | | | | **91.1%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Позначте сполучники й відносні слова | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 143 | Included in Core |
| **Skill 1: Відносні речення** | ⚪️ | 144 | Skipped |
| **Skill 2: Підрядні речення мети** | ⚪️ | 109 | Skipped |
| **Skill 3: Умовні речення** | ⚪️ | 148 | Skipped |
| **Integration Challenge** | ⚪️ | 124 | Skipped |
| **Практика** | ⚪️ | 230 | Skipped |
| **Підсумок** | ✅ | 165 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |