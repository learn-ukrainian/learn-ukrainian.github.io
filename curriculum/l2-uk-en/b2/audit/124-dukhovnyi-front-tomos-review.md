# Audit Report: 124-dukhovnyi-front-tomos.md
**Phase:** B2.3d | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1400
**Overall Status:** ❌ FAIL

## LINT ERRORS
- ❌ Line 11: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 23: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 27: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 35: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 57: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 69: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 75: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 93: Use Ukrainian angular quotes («...») instead of ASCII quotes (").

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [reading_comp_1] quiz: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [vocab_context_1] fill-in: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [church_matching] match-up: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [grammar_church_1] error-correction: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [source_analysis_select] select: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [grammar_adjectives_1] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [sentence_unjumble_1] unjumble: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [sorting_categories_church] group-sort: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [text_cloze_church] cloze: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [translation_church] translate: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [language_nuances_church] select: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [general_knowledge_church] quiz: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [content_check_church] true-false: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [synonyms_church] match-up: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## Recommendation
**🔄 REWRITE** (severity 95/100)

- 16 violations (severe - consider revision)
- 8 format errors (many)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1857/1400
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 8 Format Errors
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 10-14)
- **Immersion:** 🇺🇦 99.9% (target 98-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 12 | 3 | 100% | 24% | 23.8% |
| engagement | 10 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 114 | Included in Core |
| **Вступ** | ⚪️ | 224 | Skipped |
| **Історичний наратив: Від анексії до свободи** | ⚪️ | 959 | Skipped |
| **Первинні джерела** | ⚪️ | 254 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 251 | Skipped |
| **Підсумок** | ✅ | 55 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |