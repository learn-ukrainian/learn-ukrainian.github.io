# Audit Report: 121-ukraine-1991-2004.md
**Phase:** B2.3d | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q1 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q3 prompt length 3 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q4 prompt length 5 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q5 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q6 prompt length 5 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q7 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q8 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Поєднайте дати з відповідними історичними подіями.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** group-sort 'Розподіліть за групами' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Доберіть синоніми до термінів політичного дискурсу.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 121-ukraine-1991-2004.yaml: Array validation: {'type': 'translate', 'items': [{'source': 'Nuclear weapons', 'options': [{'text': 'Ядерна зброя', 'correct': True}]}, {'source': 'Hyperinflation', 'options': [{'text': 'Гіперінфляція', 'correct': True}]}, {'source': 'Civil society', 'options': [{'text': 'Громадянське суспільство', 'correct': True}]}, {'source': 'Security guarantees', 'options': [{'text': 'Гарантії безпеки', 'correct': True}]}, {'source': 'National currency', 'options': [{'text': 'Національна валюта', 'correct': True}]}, {'source': 'State border', 'options': [{'text': 'Державний кордон', 'correct': True}]}, {'source': 'Oligarchic clans', 'options': [{'text': 'Олігархічні клани', 'correct': True}]}, {'source': 'Economic collapse', 'options': [{'text': 'Економічний колапс', 'correct': True}]}], 'title': 'Оберіть правильний переклад для термінів епохи становлення.', 'instruction': 'Оберіть правильний переклад.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 121-ukraine-1991-2004.yaml: [index-4] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 121-ukraine-1991-2004.yaml: [index-5] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 121-ukraine-1991-2004.yaml: [index-12] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 121-ukraine-1991-2004.yaml: [index-13] translate: 'items.7.options' - [{'text': 'Економічний колапс', 'correct': True}] is too short
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
- 18 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1914/2000 (86 short)
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 37/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 17 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 11 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 15 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 97 | Included in Core |
| **Вступ** | ⚪️ | 262 | Skipped |
| **Історичний наратив: Шлях крізь шторм** | ⚪️ | 782 | Skipped |
| **Первинні джерела** | ⚪️ | 279 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 327 | Skipped |
| **Підсумок** | ✅ | 57 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |