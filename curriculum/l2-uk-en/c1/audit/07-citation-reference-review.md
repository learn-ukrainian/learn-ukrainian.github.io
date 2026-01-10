# Audit Report: 07-citation-reference.md
**Phase:** C1.1 | **Level:** C1 | **Pedagogy:** TTT | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-vocab-match] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-citation-verbs-fill] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-indirect-speech-transform] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-plagiarism-quiz] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-essay-citation-analysis] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-citation-order] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-synonym-match] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-true-false-culture] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-prepositions-fill] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-register-id] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-plagiarism-scenarios-ii] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-citation-punctuation] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-synonym-gradient] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-case-match] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-cultural-quiz-ii] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 07-citation-reference.yaml: [07-paraphrasing-id] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Культурний контекст: Джерела української науки, Вступ до академічної доброчесності
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Аналіз' found: Мистецтво перефразування та аналізу тексту, Аналіз тексту: від простого переказу до глибокої інтерпретації
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 19 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2373/2000
- **Activities:** ✅ 16/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 6/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 26/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.3% (target 98-100% (grammar))
- **Richness:** ✅ 100% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 100% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 41 | 24 | 100% | 20% | 20.0% |
| engagement | 11 | 5 | 100% | 15% | 15.0% |
| dialogues | 7 | 4 | 100% | 15% | 15.0% |
| variety | 1.00 | - | 100% | 10% | 10.0% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 5 | 3 | 100% | 10% | 10.0% |
| visual | 12 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 10 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Вступ до академічної доброчесності** | ⚪️ | 235 | Skipped |
| **Лінгвістичні засоби цитування** | ⚪️ | 654 | Skipped |
| **Діалог: Консультація з науковим керівником** | ✅ | 333 | Included in Core |
| **Культурний контекст: Джерела української науки** | ✅ | 556 | Included in Core |
| **Мистецтво перефразування та аналізу тексту** | ✅ | 230 | Included in Core |
| **Етика та стандарти оформлення бібліографії** | ⚪️ | 308 | Skipped |
| **Підсумок** | ✅ | 57 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |