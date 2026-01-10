# Audit Report: 17-motion-coming-going.md
**Phase:** B1.2 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 17-motion-coming-going.yaml: [префікси-руху] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 17-motion-coming-going.yaml: [префікс-і-значення] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 17-motion-coming-going.yaml: [вибір-дієслова] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 17-motion-coming-going.yaml: [правила-префіксів] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 17-motion-coming-going.yaml: [дієслова-за-префіксами] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 17-motion-coming-going.yaml: [складіть-речення] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 17-motion-coming-going.yaml: [помилки-з-префіксами] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 17-motion-coming-going.yaml: [текст-з-дієсловами-руху] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 17-motion-coming-going.yaml: [знайдіть-дієслова-з-при-] mark-the-words: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 17-motion-coming-going.yaml: [переклад] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 17-motion-coming-going.yaml: [множинний-вибір] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 17 has 91.9% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка|Тест' found: Тест, Приклади в реальному контексті
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 13 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1768/1500
- **Activities:** ✅ 11/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 28/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 11 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 91.9% (target 85-100% (B1.2 Motion))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 37 | 24 | 100% | 20% | 20.0% |
| engagement | 6 | 5 | 100% | 15% | 15.0% |
| dialogues | 16 | 4 | 100% | 15% | 15.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 8 | 3 | 100% | 10% | 10.0% |
| visual | 7 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.94 | - | 94% | 5% | 4.7% |
| questions | 24 | 5 | 100% | 5% | 5.0% |
| proverbs | 1 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 157 | Included in Core |
| **Тест** | ⚪️ | 104 | Skipped |
| **Пояснення** | ⚪️ | 463 | Skipped |
| **Практика** | ⚪️ | 536 | Skipped |
| **Діалоги** | ✅ | 282 | Included in Core |
| **Підсумок** | ✅ | 116 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |