# Audit Report: 41-checkpoint-complex-sentences-2.md
**Phase:** B1.3b | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1200
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** mark-the-words 'Позначте сполучники складних речень' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Позначте сполучники складних речень' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [допустові-речення-(м35)] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [причинові-та-наслідкові-речення-(м36)] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [часові-речення-(м37)] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [непряма-мова-(м39-40)] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [з'єднайте-тип-речення-з-прикладом] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [інтегрований-тест] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [розподіліть-сполучники-за-типами] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [комплексний-тест] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [комплексний-тест] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [комплексний-текст] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [позначте-сполучники-складних-речень] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [виберіть-усі-граматично-правильні-речення] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [комплексний-переклад] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 41-checkpoint-complex-sentences-2.yaml: [правила-складних-речень] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка|Тест' per template 'b1-grammar-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 18 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1986/1200
- **Activities:** ✅ 14/10
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 5/3
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 5 < 10 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (checkpoint - no gate)
- **Richness:** ❌ 84% < 85% min (checkpoint)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 84% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 11 | 8 | 100% | 25% | 25.0% |
| review_sections | 36 | 3 | 100% | 20% | 20.0% |
| variety | 0.89 | - | 89% | 15% | 13.4% |
| engagement | 4 | 3 | 100% | 10% | 10.0% |
| cultural | 0 | - | 0% | 10% | 0.0% |
| visual | 2 | 3 | 67% | 10% | 6.7% |
| paragraph_var | 1.00 | - | 100% | 10% | 10.0% |
| **TOTAL** | | | | | **85.0%** |

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
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |