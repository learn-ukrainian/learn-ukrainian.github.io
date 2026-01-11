# Audit Report: 01-b2-review-bridge.md
**Phase:** C1.1 | **Level:** C1 | **Pedagogy:** Academic | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [match-definitions-text1] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [quiz-comprehension-text1] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [match-synonyms-text2] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [quiz-comprehension-text2] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [group-sort-style] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [fill-in-academic-phrases] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [error-correction-register] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [cloze-academic-text] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [unjumble-sentences-c1] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [mark-passive] mark-the-words: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [fill-in-connectors] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [select-academic-verbs] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [text-comparison-quiz] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [true-false-analysis] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [register-id-match] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [fill-in-passive-transform] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 01-b2-review-bridge.yaml: [essay-transition-c1] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'c1-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/c1-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 19 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2534/2000
- **Activities:** ✅ 17/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 17 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (grammar))
- **Richness:** ✅ 96% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 59 | 24 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| dialogues | 9 | 4 | 100% | 15% | 15.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 10 | 3 | 100% | 10% | 10.0% |
| visual | 9 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 15 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 84 | Included in Core |
| **Текст 1: Від впевненого користувача до майстра слова** | ✅ | 703 | Included in Core |
| **Текст 2: Українська мова в сучасному науковому дискурсі** | ✅ | 984 | Included in Core |
| **Порівняльний аналіз** | ✅ | 405 | Included in Core |
| **Письмо: Академічне есе** | ⚪️ | 314 | Skipped |
| **Підсумок** | ✅ | 44 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |