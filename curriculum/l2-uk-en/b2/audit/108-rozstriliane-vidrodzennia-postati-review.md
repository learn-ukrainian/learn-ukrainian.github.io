# Audit Report: 108-rozstriliane-vidrodzennia-postati.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q1 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q4 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q5 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Поєднайте митців з їхніми досягненнями або ідеями.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** select 'Виберіть правильні відповіді' has 1 items (minimum: 6)
  - FIX: Add more items. B2 select requires at least 6 items.
- **[COMPLEXITY]** match-up 'Доберіть синоніми до термінів епохи терору.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** select 'Виберіть правильні відповіді' has 1 items (minimum: 6)
  - FIX: Add more items. B2 select requires at least 6 items.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте знання фактів про долі митців.' Q1 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте знання фактів про долі митців.' Q2 prompt length 4 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте знання фактів про долі митців.' Q4 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте знання фактів про долі митців.' Q5 prompt length 5 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте знання фактів про долі митців.' Q8 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: Array validation: {'type': 'select', 'items': [{'question': 'Виберіть правильні відповіді', 'options': [{'text': 'Гідність', 'correct': True}, {'text': 'Чесність із собою', 'correct': True}, {'text': "П'ятирічка", 'correct': False}, {'text': 'Соцреалізм', 'correct': False}, {'text': 'Свобода слова', 'correct': True}, {'text': 'Партійний квиток', 'correct': False}]}], 'title': 'Виберіть правильні відповіді', 'instruction': 'Оберіть усі правильні відповіді.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [index-5] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 108-rozstriliane-vidrodzennia-postati.yaml: [index-10] translate: 'items.7.options' - [{'text': 'Табір для інтернованих', 'correct': True}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 18 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ❌ 1740/2000
- **Activities:** ✅ 14/10
- **Density:** ❌ 2 < 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 37/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 17 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (history))
- **Richness:** ✅ 97% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 9 | 3 | 100% | 24% | 23.8% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Виберіть правильні відповіді | select | 1 | 6 | Add 5 more items |
| Виберіть правильні відповіді | select | 1 | 6 | Add 5 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 77 | Included in Core |
| **Вступ: Будинок «Слово» як символ епохи** | ⚪️ | 310 | Skipped |
| **Історичний наратив: Творці нового світу** | ⚪️ | 748 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 213 | Skipped |
| **Первинні джерела** | ⚪️ | 216 | Skipped |
| **Підсумок** | ✅ | 66 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |