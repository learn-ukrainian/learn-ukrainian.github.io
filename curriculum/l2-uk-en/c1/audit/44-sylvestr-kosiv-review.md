# Audit Report: 44-sylvestr-kosiv.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-quiz-1] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-fill-in-1] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-match-1] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-error-1] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-select-1] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-comp-1] comparative-study: 'items_to_compare.1' - {'«Петро Могила': 'Системна інституційна реформа, спроба легального діалогу з владою...»'} is not of type 'string'
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-essay-1] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-group-1] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-unjumble-1] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-cloze-1] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-trans-1] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-tf-1] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-mark-1] mark-the-words: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-tf-2] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 44-sylvestr-kosiv.yaml: [c1-44-crit-1] critical-analysis: Additional properties are not allowed ('id' was unexpected)
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
- 19 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2078/2000
- **Activities:** ✅ 16/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 15/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 15 violations
- **Content_heavy:** ✅ Content-heavy OK (16 activities)
- **Immersion:** 🇺🇦 99.8% (target 98-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 8 | 4 | 100% | 19% | 19.0% |
| engagement | 12 | 6 | 100% | 14% | 14.3% |
| quotes | 5 | 3 | 100% | 14% | 14.3% |
| cultural | 7 | 4 | 100% | 10% | 9.5% |
| visual | 11 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 22 | 8 | 100% | 10% | 9.5% |
| legacy | 9 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 10 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 88 | Included in Core |
| **Вступ** | ⚪️ | 216 | Skipped |
| **Біографія** | ⚪️ | 670 | Skipped |
| **Історичний контекст** | ✅ | 381 | Included in Core |
| **Архітектура інтелектуального спротиву** | ⚪️ | 403 | Skipped |
| **Порівняльний аналіз** | ✅ | 141 | Included in Core |
| **Критичне мислення: Питання для глибокого аналізу** | ✅ | 82 | Included in Core |
| **Підсумок** | ✅ | 97 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |