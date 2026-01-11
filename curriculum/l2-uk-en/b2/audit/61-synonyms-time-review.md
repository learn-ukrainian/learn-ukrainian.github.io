# Audit Report: 61-synonyms-time.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть часовий відтінок' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Точність моменту' Q7 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** match-up 'Регістри та Час' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Час та Події' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q1 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q2 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q3 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q5 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q6 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q7 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q8 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: Array validation: {'type': 'translate', 'title': 'Переклад термінів часу', 'instruction': 'Оберіть правильний український синонім до англійського слова.', 'items': [{'source': 'at present / currently', 'options': [{'text': 'наразі', 'correct': True}, {'text': 'давно', 'correct': False}, {'text': 'колись', 'correct': False}, {'text': 'щойно', 'correct': False}], 'explanation': 'Найкращий офіційний відповідник для currently.'}, {'source': 'just now', 'options': [{'text': 'щойно', 'correct': True}, {'text': 'потім', 'correct': False}, {'text': 'завтра', 'correct': False}, {'text': 'нині', 'correct': False}], 'explanation': 'Вказує на дію, що відбулася секунду тому.'}, {'source': 'nowadays', 'options': [{'text': 'нині', 'correct': True}, {'text': 'раніше', 'correct': False}, {'text': 'давно', 'correct': False}, {'text': 'вчора'}], 'explanation': 'Урочисте позначення сучасності.'}, {'source': 'eventually / later', 'options': [{'text': 'згодом', 'correct': True}, {'text': 'зараз', 'correct': False}, {'text': 'сьогодні', 'correct': False}, {'text': 'щойно'}], 'explanation': 'Через певний проміжок часу.'}, {'source': 'formerly / earlier', 'options': [{'text': 'раніше', 'correct': True}, {'text': 'тепер', 'correct': False}, {'text': 'наразі', 'correct': False}, {'text': 'завтра'}], 'explanation': 'Порівняння з теперішнім часом.'}, {'source': 'epoch', 'options': [{'text': 'епоха', 'correct': True}, {'text': 'мить', 'correct': False}, {'text': 'секунда', 'correct': False}, {'text': 'хвилина'}], 'explanation': 'Великий історичний проміжок.'}, {'source': 'eternity', 'options': [{'text': 'вічність', 'correct': True}, {'text': 'доба', 'correct': False}, {'text': 'момент', 'correct': False}, {'text': 'термін'}], 'explanation': 'Нескінченний час.'}, {'source': 'deadline', 'options': [{'text': 'дедлайн', 'correct': True}, {'text': 'початок', 'correct': False}, {'text': 'мить', 'correct': False}, {'text': 'вічність'}], 'explanation': 'Крайній термін виконання.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Фразеологізми' per template 'b2-phraseology-module-template'
  - FIX: Add '## Фразеологізми' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вживання у контексті' per template 'b2-phraseology-module-template'
  - FIX: Add '## Вживання у контексті' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 16 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1872/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 65/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 14 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 90-100% (vocab))
- **Richness:** ✅ 97% (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 8 | 4 | 100% | 25% | 25.0% |
| variety | 0.97 | - | 97% | 17% | 16.2% |
| cultural | 4 | - | 100% | 17% | 16.7% |
| visual | 5 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.79 | - | 79% | 8% | 6.6% |
| examples | 29 | - | 100% | 8% | 8.3% |
| realworld | 9 | - | 100% | 8% | 8.3% |
| questions | 5 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **97.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 79 | Included in Core |
| **Вступ: Плин часу в українському просторі** | ⚪️ | 86 | Skipped |
| **Частина 1: Теперішній момент — Від «зараз» до «наразі»** | ✅ | 174 | Included in Core |
| **Частина 2: Минуле — Від «щойно» до «вічності»** | ✅ | 124 | Included in Core |
| **Частина 3: Масштаби часу — Від миті до епохи** | ✅ | 103 | Included in Core |
| **Частина 4: Час в українській культурі — «Розстріляне відродження»** | ✅ | 62 | Included in Core |
| **Частина 5: Практичний додаток — Ритм повідомлення** | ✅ | 48 | Included in Core |
| **Частина 6: Майбутнє — Від «завтра» до «згодом»** | ✅ | 69 | Included in Core |
| **Частина 7: Час у цифрову епоху** | ✅ | 80 | Included in Core |
| **Частина 8: Час у народній уяві та обрядах** | ✅ | 86 | Included in Core |
| **Частина 9: Історична пам'ять та тяглість поколінь** | ✅ | 86 | Included in Core |
| **Частина 10: Психологія сприйняття часу** | ✅ | 110 | Included in Core |
| **Частина 11: Час у сучасному мистецтві та медіа** | ✅ | 91 | Included in Core |
| **Частина 12: Майбутнє як простір надії та планування** | ✅ | 259 | Included in Core |
| **Частина 14: Час у науковому пізнанні світу** | ✅ | 97 | Included in Core |
| **Частина 15: Сприйняття часу в різних культурах** | ✅ | 161 | Included in Core |
| **Підсумок** | ✅ | 47 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |