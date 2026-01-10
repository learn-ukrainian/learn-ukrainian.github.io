# Audit Report: 51-hryhoriy-skovoroda.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Глибоке розуміння філософії серця Сковороди' Q3 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Глибоке розуміння філософії серця Сковороди' Q4 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-quiz-1] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-match-1] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-fill-1] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-essay-1] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-select-1] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-tf-1] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-mark-1] mark-the-words: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-unjumble-1] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-cloze-1] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-group-1] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-trans-1] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-err-1] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-tf-2] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-hryhoriy-skovoroda.yaml: [c1-51-crit-1] critical-analysis: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Спадщина' per template 'c1-biography-module-template'
  - FIX: Add '## Спадщина' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 20 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1996/2000 (4 short)
- **Activities:** ✅ 16/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 15/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ✅ Content-heavy OK (16 activities)
- **Immersion:** 🇺🇦 99.9% (target 98-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 8 | 4 | 100% | 19% | 19.0% |
| engagement | 10 | 6 | 100% | 14% | 14.3% |
| quotes | 11 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 13 | 8 | 100% | 10% | 9.5% |
| legacy | 12 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 10 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 98 | Included in Core |
| **Вступ** | ⚪️ | 250 | Skipped |
| **Біографія** | ⚪️ | 704 | Skipped |
| **Історичний контекст: Сковорода як Інтелектуальний Щит** | ✅ | 245 | Included in Core |
| **Архітектура Мудрості Сковороди: Вчення про Три Світи** | ⚪️ | 309 | Skipped |
| **Порівняльний аналіз: Сковорода крізь віки** | ✅ | 175 | Included in Core |
| **Критичне мислення: Питання для глибокого аналізу** | ✅ | 95 | Included in Core |
| **Підсумок** | ✅ | 120 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |