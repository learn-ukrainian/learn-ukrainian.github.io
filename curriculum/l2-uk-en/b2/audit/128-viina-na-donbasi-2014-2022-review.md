# Audit Report: 128-viina-na-donbasi-2014-2022.md
**Phase:** B2.3e | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Дайте відповідь на запитання на основі прочитаного тексту про війну на Донбасі.' Q2 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Дайте відповідь на запитання на основі прочитаного тексту про війну на Донбасі.' Q3 prompt length 5 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Дайте відповідь на запитання на основі прочитаного тексту про війну на Донбасі.' Q5 prompt length 3 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Дайте відповідь на запитання на основі прочитаного тексту про війну на Донбасі.' Q6 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Поєднайте дати та події.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про війну.' item 1 has 6 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про війну.' item 2 has 5 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про війну.' item 3 has 5 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про війну.' item 4 has 6 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про війну.' item 5 has 6 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про війну.' item 6 has 5 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання фактів.' Q1 prompt length 5 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання фактів.' Q3 prompt length 3 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання фактів.' Q4 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання фактів.' Q5 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання фактів.' Q7 prompt length 4 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання фактів.' Q8 prompt length 4 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 128-viina-na-donbasi-2014-2022.yaml: Array validation: {'type': 'select', 'items': [{'correct': True, 'question': "Слов'янськ"}, {'correct': True, 'question': 'Краматорськ'}, {'correct': False, 'question': 'Донецьк'}, {'correct': True, 'question': 'Маріуполь'}, {'correct': False, 'question': 'Луганськ'}, {'correct': True, 'question': 'Сєвєродонецьк'}], 'title': 'Які міста були звільнені українською армією влітку 2014 року?', 'instruction': 'Оберіть усі правильні відповіді.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 128-viina-na-donbasi-2014-2022.yaml: [index-4] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 128-viina-na-donbasi-2014-2022.yaml: [index-5] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 128-viina-na-donbasi-2014-2022.yaml: [index-9] translate: 'items.7.options' - [{'text': "Перемир'я", 'correct': True}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 128-viina-na-donbasi-2014-2022.yaml: [index-10] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 128-viina-na-donbasi-2014-2022.yaml: [index-13] select: 'items.5' - 'options' is a required property
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
- 26 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1952/2000 (48 short)
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 25 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.0% (target 90-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 8 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 5 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 6 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 86 | Included in Core |
| **Вступ** | ⚪️ | 169 | Skipped |
| **Історичний наратив: Хроніка оборони** | ⚪️ | 1085 | Skipped |
| **Первинні джерела** | ⚪️ | 220 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 214 | Skipped |
| **Підсумок** | ✅ | 68 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |