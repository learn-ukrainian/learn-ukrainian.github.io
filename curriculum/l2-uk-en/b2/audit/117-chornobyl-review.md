# Audit Report: 117-chornobyl.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1400
**Overall Status:** ❌ FAIL

## LINT ERRORS
- ❌ Line 99: Use Ukrainian angular quotes («...») instead of ASCII quotes (").

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [reading_comp_1] quiz: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [vocab_context_1] fill-in: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [content_check_1] true-false: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [grammar_passive_1] error-correction: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [terms_matching] match-up: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [synonyms_matching] match-up: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [source_analysis] select: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [grammar_passive_voice] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [sentence_unjumble] unjumble: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [sorting_categories] group-sort: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [text_cloze] cloze: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [translation] translate: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [linguistic_features] select: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 117-chornobyl.yaml: [general_knowledge] quiz: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## Recommendation
**🔄 REWRITE** (severity 77/100)

- 16 violations (severe - consider revision)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 2118/1400
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 21/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 1 Format Errors
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 10-14)
- **Immersion:** 🇺🇦 100.0% (target 98-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 3 | 100% | 24% | 23.8% |
| engagement | 21 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 21 | 4 | 100% | 10% | 9.5% |
| variety | 0.96 | - | 96% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 10 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 82 | Included in Core |
| **Вступ** | ⚪️ | 207 | Skipped |
| **Ніч катастрофи** | ⚪️ | 325 | Skipped |
| **Ліквідатори: Герої без захисту** | ⚪️ | 500 | Skipped |
| **Чорнобиль як каталізатор деколонізації** | ⚪️ | 608 | Skipped |
| **Первинні джерела** | ⚪️ | 242 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 92 | Skipped |
| **Підсумок** | ✅ | 62 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |