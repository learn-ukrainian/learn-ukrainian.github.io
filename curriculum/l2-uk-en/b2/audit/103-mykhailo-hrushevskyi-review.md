# Audit Report: 103-mykhailo-hrushevskyi.md
**Phase:** B2.3b | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1400
**Overall Status:** ❌ FAIL

## LINT ERRORS
- ❌ Line 9: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 11: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 36: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 65: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 70: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 71: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 75: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 77: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 105: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 137: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 139: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 145: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 153: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 155: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 165: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 167: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 170: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 171: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 176: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 177: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 201: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 208: Use Ukrainian angular quotes («...») instead of ASCII quotes (").

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 103-mykhailo-hrushevskyi.yaml: [словниковий-запас-модуля] match-up: 'pairs.15' - 'left' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 103-mykhailo-hrushevskyi.yaml: [правда-чи-міф?] true-false: 'items.15' - 'statement' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 103-mykhailo-hrushevskyi.yaml: [лексика-в-контексті] fill-in: 'items.15' - 'sentence' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 103-mykhailo-hrushevskyi.yaml: [аналіз-тексту-грушевського] select: Additional properties are not allowed ('text' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 103-mykhailo-hrushevskyi.yaml: [переклад-термінів] translate: 'items.15' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 103-mykhailo-hrushevskyi.yaml: [хронологія-життя-грушевського] match-up: 'pairs.15' - 'left' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## Recommendation
**🔄 REWRITE** (severity 75/100)

- 8 violations (significant)
- 22 format errors (many)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1772/1400
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 54/20
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 22 Format Errors
- **Pedagogy:** ❌ 8 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 10-14)
- **Immersion:** 🇺🇦 99.9% (target 98-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 10 | 3 | 100% | 24% | 23.8% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 6 | 4 | 100% | 10% | 9.5% |
| visual | 5 | 4 | 100% | 10% | 9.5% |
| variety | 0.95 | - | 95% | 5% | 4.5% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 7 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 103 | Included in Core |
| **Вступ** | ⚪️ | 206 | Skipped |
| **Від Києва до Львова: формування вченого** | ⚪️ | 186 | Skipped |
| **Наукове товариство імені Шевченка** | ⚪️ | 315 | Skipped |
| **Центральна Рада і президентство** | ⚪️ | 207 | Skipped |
| **Еміграція і повернення** | ⚪️ | 301 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 278 | Skipped |
| **Підсумок** | ✅ | 176 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |