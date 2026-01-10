# Audit Report: 02-academic-style-markers.md
**Phase:** C1.1 | **Level:** C1 | **Pedagogy:** ttt | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [quiz-comprehension-text1] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [match-markers] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [group-sort-style] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [fill-in-nominalization] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [select-hedging] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [fill-in-impersonal] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [match-synonyms] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [fill-in-connectors] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [quiz-register-errors] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [unjumble-hedging] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [true-false-passive] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [fill-in-academic-verbs] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [quiz-references] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [quiz-analytical-reading] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [fill-in-phrases] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [fill-in-vocab] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [quiz-summary] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: [essay-editing] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'c1-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/c1-module-template.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Аналіз' found: Критичний аналіз, Порівняльний аналіз, Аналіз тексту: Деконструкція Академічності
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 21 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2428/2000
- **Activities:** ✅ 18/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 8/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 30/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 18 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.3% (target 98-100% (grammar))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 58 | 24 | 100% | 20% | 20.0% |
| engagement | 10 | 5 | 100% | 15% | 15.0% |
| dialogues | 6 | 4 | 100% | 15% | 15.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 5 | 3 | 100% | 10% | 10.0% |
| visual | 21 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 17 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 86 | Included in Core |
| **Текст 1: Науковий дискурс** | ✅ | 739 | Included in Core |
| **Академічне письмо: Теорія та Практика** | ⚪️ | 590 | Skipped |
| **Порівняльний аналіз** | ✅ | 443 | Included in Core |
| **Практика** | ⚪️ | 395 | Skipped |
| **Підсумок** | ✅ | 175 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |