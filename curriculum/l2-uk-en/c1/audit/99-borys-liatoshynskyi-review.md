# Audit Report: 99-borys-liatoshynskyi.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту: Життя Бориса Лятошинського' Q1 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту: Життя Бориса Лятошинського' Q3 prompt length 9 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту: Життя Бориса Лятошинського' Q4 prompt length 8 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту: Життя Бориса Лятошинського' Q5 prompt length 8 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 99-borys-liatoshynskyi.yaml: [c1-99-essay] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Спадщина' per template 'c1-biography-module-template'
  - FIX: Add '## Спадщина' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md

## Recommendation
**📝 UPDATE** (severity 30/100)

- 8 violations (significant)

## Gates
- **Words:** ✅ 2008/2000
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 24/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 5 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 100.0% (target 98-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 6 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 9 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 22 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 102 | Included in Core |
| **Вступ** | ⚪️ | 233 | Skipped |
| **Біографія** | ⚪️ | 633 | Skipped |
| **Сучасний контекст** | ✅ | 165 | Included in Core |
| **Історичний контекст** | ✅ | 313 | Included in Core |
| **Порівняльний аналіз** | ✅ | 162 | Included in Core |
| **Підсумок** | ✅ | 111 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 184 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 105 | Skipped |