# Audit Report: 64-yevhen-chykalenko.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-yevhen-chykalenko.yaml: [c1-64-quiz-01] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-yevhen-chykalenko.yaml: [c1-64-fill-in-01] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-yevhen-chykalenko.yaml: [c1-64-error-01] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-yevhen-chykalenko.yaml: [c1-64-match-01] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-yevhen-chykalenko.yaml: [c1-64-select-01] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-yevhen-chykalenko.yaml: [c1-64-unjumble-01] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-yevhen-chykalenko.yaml: [c1-64-cloze-01] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-yevhen-chykalenko.yaml: [c1-64-tf-01] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-yevhen-chykalenko.yaml: [c1-64-gs-01] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-yevhen-chykalenko.yaml: [c1-64-essay-01] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'c1-biography-module-template'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 14 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1924/2000 (76 short)
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 28/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 10 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 99.9% (target 98-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 8 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 5 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 8 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 89 | Included in Core |
| **Вступ** | ⚪️ | 210 | Skipped |
| **Біографія** | ⚪️ | 1031 | Skipped |
| **Історичний контекст** | ✅ | 299 | Included in Core |
| **Порівняльний аналіз** | ✅ | 129 | Included in Core |
| **Summary** | ✅ | 166 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |