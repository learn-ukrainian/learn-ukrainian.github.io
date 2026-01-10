# Audit Report: 130-zlochyny-i-stiikist.md
**Phase:** B2.3e | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [reading_comp_1] quiz: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [vocab_context_1] fill-in: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [grammar_resilience_1] error-correction: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [terms_matching_crimes] match-up: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [source_analysis_select_1] select: Additional properties are not allowed ('id', 'question', 'text' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [grammar_passive_context] mark-the-words: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [sentence_unjumble_resilience] unjumble: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [war_events_sorting] group-sort: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [text_cloze_1] cloze: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [synonyms_resilience] match-up: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [terms_translation_resilience] translate: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [linguistic_features_war] select: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [final_comp_check_resilience] quiz: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 130-zlochyny-i-stiikist.yaml: [additional_check_resilience] true-false: Additional properties are not allowed ('id', 'question' were unexpected)
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
- **Words:** ❌ 1859/2000
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
- **Immersion:** 🇺🇦 99.0% (target 98-100% (history))
- **Richness:** ✅ 97% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 10 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 18 | 10 | 100% | 14% | 14.3% |
| decolonization | 13 | 2 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 14 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 111 | Included in Core |
| **Вступ: Обличчя окупації** | ⚪️ | 251 | Skipped |
| **Історичний наратив: Тріумф визволення та випробування темрявою** | ⚪️ | 700 | Skipped |
| **Первинні джерела** | ⚪️ | 320 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 289 | Skipped |
| **Підсумок** | ✅ | 78 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |