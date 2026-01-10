# Audit Report: 37-kniaz-sviatoslav.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 37-kniaz-sviatoslav.yaml: YAML parse error: mapping values are not allowed here
  in "curriculum/l2-uk-en/c1/activities/37-kniaz-sviatoslav.yaml", line 530, column 65
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
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина' found: Спадщина та сучасне сприйняття, Спадщина
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Need More Practice?' per template 'c1-biography-module-template'
  - FIX: Add '## Need More Practice?' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md

## Recommendation
**📝 UPDATE** (severity 55/100)

- Revision recommended (severity 55/100)
- 7 violations (significant)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 2009/2000
- **Activities:** ❌ 0/12
- **Density:** ❌ 0 < 12
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 12-16)
- **Immersion:** 🇺🇦 99.3% (target 98-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 12 | 8 | 100% | 10% | 9.5% |
| legacy | 9 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 7 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 61 | Included in Core |
| **Вступ** | ⚪️ | 252 | Skipped |
| **Біографія** | ⚪️ | 1126 | Skipped |
| **Історичний контекст** | ✅ | 201 | Included in Core |
| **Порівняльний аналіз** | ✅ | 69 | Included in Core |
| **Спадщина та сучасне сприйняття** | ⚪️ | 152 | Skipped |
| **Спадщина** | ⚪️ | 69 | Skipped |
| **Підсумок** | ✅ | 79 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |