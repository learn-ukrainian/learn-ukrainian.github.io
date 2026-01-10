# Audit Report: 30-history-of-language.md
**Phase:** C1.1 | **Level:** C1 | **Pedagogy:** history | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Походження української мови' Q1 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Походження української мови' Q3 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Походження української мови' Q4 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Міфи про мову' Q2 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Міфи про мову' Q3 prompt length 8 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Міфи про мову' Q4 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Міфи про мову' Q5 prompt length 9 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: [origins-quiz] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: [historical-terms-match] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: [repressions-fill] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: [epochs-sort] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: [shevelov-quote] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: [identify-archaisms] mark-the-words: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: [myths-quiz] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: [modern-revival] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: [soviet-myth] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: [quotes-match] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: [fix-facts] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Потрібно більше практики?' per template 'b2-history-module-template'
  - FIX: Add '## Потрібно більше практики?' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 19 violations (severe - consider revision)

## Gates
- **Words:** ❌ 1656/2000
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 9/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 18 violations
- **Content_heavy:** ⚠️ 1 fill-in with year answers
- **Immersion:** 🇺🇦 99.2% (target 98-100% (history))
- **Richness:** ✅ 100% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 100% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 3 | 100% | 24% | 23.8% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 13 | 2 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 5 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 41 | Included in Core |
| **Контекст** | ✅ | 260 | Included in Core |
| **Золота доба** | ⚪️ | 151 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 237 | Skipped |
| **Радянська епоха** | ⚪️ | 188 | Skipped |
| **Відродження та Сучасність** | ⚪️ | 130 | Skipped |
| **Первинні джерела** | ⚪️ | 149 | Skipped |
| **8. Приклади історичних змін** | ⚪️ | 147 | Skipped |
| **9. Читання: Голос діаспори** | ✅ | 150 | Included in Core |
| **Підсумок** | ✅ | 99 | Included in Core |
| **Need More Practice?** | ⚪️ | 104 | Skipped |