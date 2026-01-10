# Audit Report: 15-checkpoint-aspect-mastery.md
**Phase:** B1.1 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1200
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [комплексний-тест--основи-виду-(m06)] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [комплексний-тест--вид-у-минулому-(m07-08)] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [комплексний-тест--вид-у-майбутньому-(m09)] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [комплексний-тест--заперечення-та-наказ-(m10-11)] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [видові-пари] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [маркер--вид] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [наказовий-спосіб--тип] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [вибір-виду--минулий-час] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [вибір-виду--майбутній-час] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [твердження-про-вид] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [типи-видових-пар] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [маркери-за-видом] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [речення-з-вибором-виду] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [типові-помилки-з-видом] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [інтеграційний-текст--один-день] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [знайдіть-дієслова-доконаного-виду] mark-the-words: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [правильні-твердження-про-вид] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 15-checkpoint-aspect-mastery.yaml: [переклад-з-англійської] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка|Тест' per template 'b1-grammar-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Практика' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 21 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1821/1200
- **Activities:** ✅ 18/10
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 13/10
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 18 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.8% (checkpoint - no gate)
- **Richness:** ✅ 98% (checkpoint)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 11 | 8 | 100% | 25% | 25.0% |
| review_sections | 26 | 3 | 100% | 20% | 20.0% |
| variety | 0.92 | - | 92% | 15% | 13.8% |
| engagement | 6 | 3 | 100% | 10% | 10.0% |
| cultural | 3 | - | 100% | 10% | 10.0% |
| visual | 8 | 3 | 100% | 10% | 10.0% |
| paragraph_var | 0.99 | - | 99% | 10% | 9.9% |
| **TOTAL** | | | | | **98.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 70 | Included in Core |
| **Огляд** | ⚪️ | 64 | Skipped |
| **Skill 1: Вид у минулому часі** | ⚪️ | 326 | Skipped |
| **Skill 2: Вид у майбутньому часі** | ⚪️ | 207 | Skipped |
| **Skill 3: Вид у запереченні** | ⚪️ | 325 | Skipped |
| **Skill 4: Вид у наказовому способі** | ⚪️ | 279 | Skipped |
| **Skill 5: Видові пари** | ⚪️ | 151 | Skipped |
| **Інтеграційне завдання** | ⚪️ | 157 | Skipped |
| **Підсумок** | ✅ | 132 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |