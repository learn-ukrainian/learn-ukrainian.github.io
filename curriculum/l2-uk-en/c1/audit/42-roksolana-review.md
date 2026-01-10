# Audit Report: 42-roksolana.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 42-roksolana.yaml: YAML parse error: mapping values are not allowed here
  in "curriculum/l2-uk-en/c1/activities/42-roksolana.yaml", line 247, column 82
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: biography) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: biography) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Спадщина' per template 'c1-biography-module-template'
  - FIX: Add '## Спадщина' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Need More Practice?' per template 'c1-biography-module-template'
  - FIX: Add '## Need More Practice?' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md

## Recommendation
**📝 UPDATE** (severity 55/100)

- Revision recommended (severity 55/100)
- 7 violations (significant)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ⚠️ 1939/2000 (61 short)
- **Activities:** ❌ 0/12
- **Density:** ❌ 0 < 12
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 9/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 12-16)
- **Immersion:** 🇺🇦 99.8% (target 98-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 5 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 8 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 14 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 95 | Included in Core |
| **Вступ** | ⚪️ | 259 | Skipped |
| **Біографія** | ⚪️ | 762 | Skipped |
| **Історичний контекст** | ✅ | 307 | Included in Core |
| **Лінгвістична еволюція та мовна стратегія** | ⚪️ | 180 | Skipped |
| **Порівняльний аналіз** | ✅ | 136 | Included in Core |
| **Критичне мислення** | ⚪️ | 72 | Skipped |
| **Підсумок** | ✅ | 128 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |