# Audit Report: 06-aspect-complete-system.md
**Phase:** B1.1 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [визначення-виду] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [вид-і-контекст] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [вибір-виду] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [вид-дієслова] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [маркери-виду] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [речення-про-вид] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [виправлення-помилок] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [текст-про-аспект] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [знайдіть-дієслова-дв] mark-the-words: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [аспект-у-запитаннях] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [послідовність-дій] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [маркери-часу-і-вид] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [множинний-вибір--вид] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 06-aspect-complete-system.yaml: [переклад--вид] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 14 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1591/1500
- **Activities:** ✅ 14/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 28/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 14 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.4% (target 85-100% (B1.1 Aspect))
- **Richness:** ✅ 96% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 74 | 24 | 100% | 20% | 20.0% |
| engagement | 11 | 5 | 100% | 15% | 15.0% |
| dialogues | 12 | 4 | 100% | 15% | 15.0% |
| variety | 0.95 | - | 95% | 10% | 9.5% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 9 | 3 | 100% | 10% | 10.0% |
| visual | 2 | 3 | 67% | 5% | 3.4% |
| paragraph_var | 0.73 | - | 73% | 5% | 3.6% |
| questions | 50 | 5 | 100% | 5% | 5.0% |
| proverbs | 3 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 41 | Included in Core |
| **Тест** | ⚪️ | 91 | Skipped |
| **Граматика** | ⚪️ | 223 | Skipped |
| **Практика** | ⚪️ | 861 | Skipped |
| **Діалоги** | ✅ | 145 | Included in Core |
| **Підсумок** | ✅ | 165 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 65 | Skipped |