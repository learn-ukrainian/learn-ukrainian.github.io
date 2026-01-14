# Audit Report: 114-volodymyr-ivasyuk.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння біографії' Q1 prompt length 8 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння біографії' Q2 prompt length 9 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння біографії' Q4 prompt length 8 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 114-volodymyr-ivasyuk.yaml: Schema validation error at key 'options': ['Буковині', 'Донбасі', 'Криму'] is too short
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

- 7 violations (significant)

## Gates
- **Words:** ✅ 2010/2000
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 4 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 99.9% (target 90-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 13 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 13 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 27 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 16 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 75 | Included in Core |
| **Вступ** | ⚪️ | 219 | Skipped |
| **Біографія** | ⚪️ | 553 | Skipped |
| **Історичний контекст** | ✅ | 254 | Included in Core |
| **Порівняльний аналіз** | ✅ | 168 | Included in Core |
| **Есе** | ⚪️ | 375 | Skipped |
| **Підсумок** | ✅ | 46 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 200 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 120 | Skipped |