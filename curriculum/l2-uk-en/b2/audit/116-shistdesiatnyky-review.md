# Audit Report: 116-shistdesiatnyky.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [reading_comp_1] quiz: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [vocab_context_1] fill-in: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [figures_matching] match-up: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [grammar_voice_1] error-correction: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [source_analysis_1] select: Additional properties are not allowed ('id', 'question', 'text' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [grammar_passive_1] mark-the-words: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [concepts_sorting] group-sort: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [text_cloze_1] cloze: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [sentence_structure_1] unjumble: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [content_check_1] true-false: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [synonyms_match] match-up: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [grammar_prep_1] fill-in: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [cultural_context] select: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [terms_translation] translate: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md

## Recommendation
**🔄 REWRITE** (severity 75/100)

- 17 violations (severe - consider revision)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 2109/2000
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 10-14)
- **Immersion:** 🇺🇦 99.3% (target 98-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 9 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 104 | Included in Core |
| **Вступ** | ⚪️ | 395 | Skipped |
| **Історичний наратив: Від надії до спротиву** | ⚪️ | 912 | Skipped |
| **Первинні джерела** | ⚪️ | 274 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 256 | Skipped |
| **Підсумок** | ✅ | 58 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |