# Audit Report: 65-synonyms-state.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть відтінок стану' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний стан' Q5 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Об'єктивне чи Суб'єктивне?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Стан та Регістри' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Стан та Чинники' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q1 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q2 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q3 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q4 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q5 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q6 prompt length 3 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q7 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q8 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: Array validation: {'type': 'translate', 'title': 'Переклад стану', 'instruction': 'Оберіть правильний український синонім до англійського слова.', 'items': [{'source': 'to exist', 'options': [{'text': 'існувати', 'correct': True}, {'text': 'базікати', 'correct': False}, {'text': 'хапати', 'correct': False}, {'text': 'руйнувати', 'correct': False}], 'explanation': 'Найкращий відповідник для філософського буття.'}, {'source': 'to stay / be located', 'options': [{'text': 'перебувати', 'correct': True}, {'text': 'виглядати', 'correct': False}, {'text': 'здаватися', 'correct': False}, {'text': 'мріяти', 'correct': False}], 'explanation': 'Для офіційного перебування.'}, {'source': 'to turn out', 'options': [{'text': 'виявлятися', 'correct': True}, {'text': 'існувати', 'correct': False}, {'text': 'становити', 'correct': False}, {'text': 'бути'}], 'explanation': 'Відкриття реального стану.'}, {'source': 'to constitute', 'options': [{'text': 'становити', 'correct': True}, {'text': 'виглядати', 'correct': False}, {'text': 'панікувати', 'correct': False}, {'text': 'співати'}], 'explanation': 'Про частину цілого.'}, {'source': 'environment', 'options': [{'text': 'середовище', 'correct': True}, {'text': 'точка', 'correct': False}, {'text': 'мить', 'correct': False}, {'text': 'час'}], 'explanation': 'Оточуючі умови.'}, {'source': 'circumstances', 'options': [{'text': 'обставини', 'correct': True}, {'text': 'мрії', 'correct': False}, {'text': 'думки', 'correct': False}, {'text': 'слова'}], 'explanation': 'Супутні факти.'}, {'source': 'stability', 'options': [{'text': 'стабільність', 'correct': True}, {'text': 'хаос', 'correct': False}, {'text': 'паніка', 'correct': False}, {'text': 'зміна'}], 'explanation': 'Незмінність стану.'}, {'source': 'impression', 'options': [{'text': 'враження', 'correct': True}, {'text': 'робота', 'correct': False}, {'text': 'чину', 'correct': False}, {'text': 'браку'}], 'explanation': 'Результат впливу образу.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
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
- 18 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1786/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 33 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 16 violations
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
| variety | 0.94 | - | 94% | 17% | 15.7% |
| cultural | 9 | - | 100% | 17% | 16.7% |
| visual | 7 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.81 | - | 81% | 8% | 6.8% |
| examples | 42 | - | 100% | 8% | 8.3% |
| realworld | 6 | - | 100% | 8% | 8.3% |
| questions | 7 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **97.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 80 | Included in Core |
| **Вступ: Глибина українського буття** | ⚪️ | 100 | Skipped |
| **Частина 1: Бути — Як ми фіксуємо існування** | ✅ | 159 | Included in Core |
| **Частина 2: Здаватися — Світ через призму сприйняття** | ✅ | 121 | Included in Core |
| **Частина 3: Категорії стану — Від умов до середовища** | ✅ | 116 | Included in Core |
| **Частина 4: Стан у дзеркалі української літератури та психології** | ✅ | 55 | Included in Core |
| **Частина 5: Практичний додаток — Тон та Аналіз** | ✅ | 9 | Included in Core |
| **Частина 6: Стан у сучасному світі: Стабільність та Криза** | ✅ | 93 | Included in Core |
| **Частина 7: Буття як цінність** | ✅ | 61 | Included in Core |
| **Частина 8: Стан довкілля та Екологічне Буття** | ✅ | 81 | Included in Core |
| **Частина 9: Історичний Стан: Між Минулим та Майбутнім** | ✅ | 84 | Included in Core |
| **Частина 10: Стан у цифровому просторі та Майбутнє Буття** | ✅ | 95 | Included in Core |
| **Частина 11: Стан спокою у містах Суми та Полтава** | ✅ | 79 | Included in Core |
| **Частина 12: Естетичне Буття в Ужгород** | ✅ | 146 | Included in Core |
| **Частина 13: Стан архітектури та Історичне Буття** | ✅ | 153 | Included in Core |
| **Частина 14: Стан в офіційному листуванні та Звітності** | ✅ | 97 | Included in Core |
| **Частина 15: Психологія стабільності в епоху змін** | ✅ | 99 | Included in Core |
| **Підсумок** | ✅ | 48 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |