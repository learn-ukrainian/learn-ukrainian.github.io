# Audit Report: 123-epokha-yanukovycha.md
**Phase:** B2.3d | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Дайте відповідь на запитання на основі прочитаного тексту про епоху Януковича.' Q1 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Дайте відповідь на запитання на основі прочитаного тексту про епоху Януковича.' Q2 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Дайте відповідь на запитання на основі прочитаного тексту про епоху Януковича.' Q3 prompt length 5 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Дайте відповідь на запитання на основі прочитаного тексту про епоху Януковича.' Q8 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Поєднайте дати з відповідними подіями епохи Януковича.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** group-sort 'Розподіліть за групами' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про події 2010-2013 років.' item 1 has 6 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про події 2010-2013 років.' item 5 has 6 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY]** match-up 'Доберіть синоніми до політичних термінів.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 123-epokha-yanukovycha.yaml: Array validation: {'type': 'translate', 'items': [{'source': 'Association Agreement', 'options': [{'text': 'Угода про асоціацію', 'correct': True}]}, {'source': 'Political prisoner', 'options': [{'text': "Політичний в'язень", 'correct': True}]}, {'source': 'Law enforcement', 'options': [{'text': 'Правоохоронні органи', 'correct': True}]}, {'source': 'State treason', 'options': [{'text': 'Державна зрада', 'correct': True}]}, {'source': 'Freedom of speech', 'options': [{'text': 'Свобода слова', 'correct': True}]}, {'source': 'Human rights', 'options': [{'text': 'Права людини', 'correct': True}]}, {'source': 'Customs Union', 'options': [{'text': 'Митний союз', 'correct': True}]}, {'source': 'Trade war', 'options': [{'text': 'Торговельна війна', 'correct': True}]}], 'title': 'Оберіть правильний переклад термінів.', 'instruction': 'Оберіть правильний переклад.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 123-epokha-yanukovycha.yaml: [index-4] select: 'items.7' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 123-epokha-yanukovycha.yaml: [index-5] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 123-epokha-yanukovycha.yaml: [index-12] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 123-epokha-yanukovycha.yaml: [index-13] translate: 'items.7.options' - [{'text': 'Торговельна війна', 'correct': True}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 17 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1951/2000 (49 short)
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.3% (target 90-100% (history))
- **Richness:** ✅ 100% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 100% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 11 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 10 | 2 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 6 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 88 | Included in Core |
| **Вступ** | ⚪️ | 235 | Skipped |
| **Історичний наратив: Хроніка узурпації** | ⚪️ | 1028 | Skipped |
| **Первинні джерела** | ⚪️ | 204 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 229 | Skipped |
| **Підсумок** | ✅ | 57 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |