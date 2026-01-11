# Audit Report: 62-synonyms-place.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть місце' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Орієнтування у просторі' Q5 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Орієнтування у просторі' Q7 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Статика чи Напрямок?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Простір та Об'єкти' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Антоніми простору' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q1 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q2 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q3 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q4 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q5 prompt length 3 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q6 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q7 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q8 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 62-synonyms-place.yaml: Array validation: {'type': 'translate', 'title': 'Переклад простору', 'instruction': 'Оберіть правильний український синонім до англійського слова.', 'items': [{'source': 'here (colloquial/cozy)', 'options': [{'text': 'тутечки', 'correct': True}, {'text': 'там', 'correct': False}, {'text': 'далеко', 'correct': False}, {'text': 'сюди', 'correct': False}], 'explanation': 'Найкращий розмовний відповідник.'}, {'source': 'nearby / close by', 'options': [{'text': 'поблизу', 'correct': True}, {'text': 'далеко', 'correct': False}, {'text': 'ніде', 'correct': False}, {'text': 'звідти', 'correct': False}], 'explanation': 'Вказує на територіальну близькість.'}, {'source': 'everywhere', 'options': [{'text': 'всюди', 'correct': True}, {'text': 'десь', 'correct': False}, {'text': 'кудись', 'correct': False}, {'text': 'звідкись'}], 'explanation': 'Позначає кожну точку простору.'}, {'source': 'from here', 'options': [{'text': 'звідси', 'correct': True}, {'text': 'сюди', 'correct': False}, {'text': 'туди', 'correct': False}, {'text': 'там'}], 'explanation': 'Джерело руху від мовця.'}, {'source': 'over there (pointing)', 'options': [{'text': 'он там', 'correct': True}, {'text': 'тутечки', 'correct': False}, {'text': 'сюди', 'correct': False}, {'text': 'звідси'}], 'explanation': "Вказівка на віддалений видимий об'єкт."}, {'source': 'nowhere', 'options': [{'text': 'ніде', 'correct': True}, {'text': 'всюди', 'correct': False}, {'text': 'десь', 'correct': False}, {'text': 'кудись'}], 'explanation': 'Відсутність будь-якого місця.'}, {'source': 'boundary / limit', 'options': [{'text': 'межа', 'correct': True}, {'text': 'точка', 'correct': False}, {'text': 'район', 'correct': False}, {'text': 'обрій'}], 'explanation': 'Край або кордон простору.'}, {'source': 'horizon', 'options': [{'text': 'обрій', 'correct': True}, {'text': 'зона', 'correct': False}, {'text': 'місце', 'correct': False}, {'text': 'точка'}], 'explanation': 'Межа неба і землі.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 62-synonyms-place.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
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
- 19 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1766/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 57/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 17 violations
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
| variety | 0.95 | - | 95% | 17% | 15.8% |
| cultural | 4 | - | 100% | 17% | 16.7% |
| visual | 6 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.84 | - | 84% | 8% | 7.0% |
| examples | 33 | - | 100% | 8% | 8.3% |
| realworld | 6 | - | 100% | 8% | 8.3% |
| questions | 12 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **97.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ: Карта українського простору** | ⚪️ | 97 | Skipped |
| **Частина 1: Тут і Там — Магія вказівки** | ✅ | 153 | Included in Core |
| **Частина 2: Відстань та Близькість** | ✅ | 79 | Included in Core |
| **Частина 3: Простір та Локації — Від точки до території** | ✅ | 106 | Included in Core |
| **Частина 4: Простір в українській культурі — Шацькі озера** | ✅ | 65 | Included in Core |
| **Частина 5: Практичний додаток — Навігація в розмові** | ✅ | 50 | Included in Core |
| **Частина 6: Напрямок руху — Від «сюди» до «кудись»** | ✅ | 63 | Included in Core |
| **Частина 7: Простір у цифрову епоху** | ✅ | 71 | Included in Core |
| **Частина 8: Концепція дому в українському світогляді** | ✅ | 100 | Included in Core |
| **Частина 9: Ландшафт як доля — Гори, Степ та Море** | ✅ | 91 | Included in Core |
| **Частина 10: Простір майбутнього — Урбаністика та Екологія** | ✅ | 98 | Included in Core |
| **Частина 11: Простір пам'яті та меморіальна лексика** | ✅ | 208 | Included in Core |
| **Частина 12: Простір у художній візії та мистецтві** | ✅ | 81 | Included in Core |
| **Частина 13: Геометрія українського міста: Від майдану до дворика** | ✅ | 81 | Included in Core |
| **Частина 14: Психологія рідного місця: Дім та Оселя** | ✅ | 96 | Included in Core |
| **Частина 15: Простір як виклик та можливість** | ✅ | 82 | Included in Core |
| **Підсумок** | ✅ | 48 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |