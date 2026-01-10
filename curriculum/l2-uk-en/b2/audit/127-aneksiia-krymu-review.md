# Audit Report: 127-aneksiia-krymu.md
**Phase:** B2.3e | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [reading_comp_1] quiz: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [vocab_context_1] fill-in: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [key_figures_match] match-up: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [grammar_agreement] error-correction: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [source_analysis_select] select: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [grammar_passive] mark-the-words: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [sorting_events] group-sort: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [text_cloze] cloze: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [sentence_unjumble] unjumble: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [translation_en_uk] translate: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [linguistic_features] select: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [general_knowledge] quiz: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [additional_check] true-false: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 127-aneksiia-krymu.yaml: [additional_select] select: Additional properties are not allowed ('id', 'question' were unexpected)
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
- **Words:** ✅ 2056/2000
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
- **Immersion:** 🇺🇦 99.2% (target 98-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 7 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 21 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 5 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 111 | Included in Core |
| **Вступ** | ⚪️ | 247 | Skipped |
| **Історичний наратив: Хроніка злочину** | ⚪️ | 1042 | Skipped |
| **Первинні джерела** | ⚪️ | 209 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 251 | Skipped |
| **Підсумок** | ✅ | 86 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |