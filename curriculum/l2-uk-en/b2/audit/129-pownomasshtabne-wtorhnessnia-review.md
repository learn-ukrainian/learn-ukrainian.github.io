# Audit Report: 129-pownomasshtabne-wtorhnessnia.md
**Phase:** B2.3e | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [reading_comp_1] quiz: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [vocab_context_1] fill-in: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [grammar_emergency_1] error-correction: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [terms_matching_1] match-up: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [source_analysis_1] select: Additional properties are not allowed ('id', 'question', 'text' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [grammar_passive_1] mark-the-words: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [sentence_structure_1] unjumble: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [content_check_1] true-false: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [categories_war_1] group-sort: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [text_cloze_1] cloze: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [synonyms_matching_1] match-up: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [terms_translation_1] translate: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [vocabulary_features_1] select: Additional properties are not allowed ('id', 'question' were unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [final_comp_check_1] quiz: Additional properties are not allowed ('id', 'question' were unexpected)
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
- **Words:** ❌ 1812/2000
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 12/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 10-14)
- **Immersion:** 🇺🇦 99.2% (target 98-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 8 | 3 | 100% | 24% | 23.8% |
| engagement | 12 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 16 | 10 | 100% | 14% | 14.3% |
| decolonization | 8 | 2 | 100% | 14% | 14.3% |
| cultural | 6 | 4 | 100% | 10% | 9.5% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 13 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 106 | Included in Core |
| **Вступ: Ранок, що триває** | ⚪️ | 225 | Skipped |
| **Історичний наратив: Крах бліцкригу** | ⚪️ | 743 | Skipped |
| **Первинні джерела** | ⚪️ | 294 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 252 | Skipped |
| **Підсумок** | ✅ | 82 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |