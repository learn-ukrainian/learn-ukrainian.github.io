# Audit Report: 110-vasyl-symonenko.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння біографії' Q1 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння біографії' Q2 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння біографії' Q3 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння біографії' Q4 prompt length 8 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння біографії' Q5 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-vasyl-symonenko.yaml: Schema validation error at key 'options': ['Полтавщині', 'Київщині', 'Львівщині'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Спадщина' per template 'c1-biography-module-template.md'
  - FIX: Add '## Спадщина' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 30/100)

- 9 violations (significant)

## Gates
- **Words:** ✅ 2191/2000
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 6 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 99.9% (target 90-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 10 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 14 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 13 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 21 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 68 | Included in Core |
| **Вступ** | ⚪️ | 245 | Skipped |
| **Біографія** | ⚪️ | 677 | Skipped |
| **Історичний контекст** | ✅ | 317 | Included in Core |
| **Порівняльний аналіз** | ✅ | 216 | Included in Core |
| **Есе** | ⚪️ | 384 | Skipped |
| **Підсумок** | ✅ | 44 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 127 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 113 | Skipped |