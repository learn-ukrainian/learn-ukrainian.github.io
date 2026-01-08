# Audit Report: 108-rozstriliane-vidrodzennia-postati.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1400
**Overall Status:** ❌ FAIL

## LINT ERRORS
- ❌ Line 9: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 15: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 25: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 27: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 31: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 33: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 39: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 96: Use Ukrainian angular quotes («...») instead of ASCII quotes (").

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [reading_comp_1] quiz: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [vocab_context_1] fill-in: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [personalities_matching] match-up: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [grammar_voice_1] error-correction: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [source_analysis_select] select: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [grammar_participles_1] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [sentence_unjumble_1] unjumble: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [sorting_categories_history] group-sort: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [text_cloze_executed] cloze: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [synonyms_matching_repressions] match-up: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [terms_translation_repressions] translate: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [linguistic_features_repressions] select: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [general_knowledge_executed] quiz: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [content_check_executed] true-false: 'title' is a required property
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
- **Words:** ✅ 1630/1400
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 37/20
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 8 Format Errors
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 10-14)
- **Immersion:** 🇺🇦 100.0% (target 98-100% (history))
- **Richness:** ✅ 97% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 9 | 3 | 100% | 24% | 23.8% |
| engagement | 8 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 77 | Included in Core |
| **Вступ: Будинок «Слово» як символ епохи** | ⚪️ | 310 | Skipped |
| **Історичний наратив: Творці нового світу** | ⚪️ | 748 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 213 | Skipped |
| **Первинні джерела** | ⚪️ | 216 | Skipped |
| **Підсумок** | ✅ | 66 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |