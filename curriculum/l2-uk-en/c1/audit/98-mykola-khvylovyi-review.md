# Audit Report: 98-mykola-khvylovyi.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту: Життя Миколи Хвильового' Q1 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту: Життя Миколи Хвильового' Q2 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту: Життя Миколи Хвильового' Q4 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту: Життя Миколи Хвильового' Q5 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 98-mykola-khvylovyi.yaml: [c1-98-essay] essay-response: Additional properties are not allowed ('id' was unexpected)
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
- **Words:** ✅ 2236/2000
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 24/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 5 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 100.0% (target 98-100% (biography))
- **Richness:** ❌ 92% < 95% min (biography)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 92% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 7 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 13 | 3 | 100% | 14% | 14.3% |
| cultural | 1 | 4 | 25% | 10% | 2.4% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 28 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **92.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 106 | Included in Core |
| **Вступ** | ⚪️ | 228 | Skipped |
| **Біографія** | ⚪️ | 663 | Skipped |
| **Сучасний контекст** | ✅ | 230 | Included in Core |
| **Історичний контекст** | ✅ | 382 | Included in Core |
| **Порівняльний аналіз** | ✅ | 184 | Included in Core |
| **Підсумок** | ✅ | 129 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 203 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 111 | Skipped |