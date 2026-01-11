# Audit Report: 67-advanced-conjunctions-i.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** Grammar | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть логічний зв'язок' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка речення' Q1 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка речення' Q2 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка речення' Q3 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка речення' Q4 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка речення' Q5 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка речення' Q6 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка речення' Q7 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка речення' Q8 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Причина чи Допуск?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Стилі та Сполучники' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Логічні ланцюжки' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пунктуаційний квест' Q1 prompt length 3 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пунктуаційний квест' Q2 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пунктуаційний квест' Q3 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пунктуаційний квест' Q4 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пунктуаційний квест' Q5 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пунктуаційний квест' Q6 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пунктуаційний квест' Q7 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пунктуаційний квест' Q8 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 67-advanced-conjunctions-i.yaml: Array validation: {'type': 'select', 'title': 'Допустові конструкції', 'instruction': 'Оберіть усі сполучники допуску (6+ елементів).', 'items': [{'question': 'Які слова вказують на допуск? (6+)', 'options': [{'text': 'хоча', 'correct': True}, {'text': 'незважаючи на те що', 'correct': True}, {'text': 'попри те що', 'correct': True}, {'text': 'дарма що', 'correct': True}, {'text': 'хай', 'correct': True}, {'text': 'хоч', 'correct': True}, {'text': 'нехай', 'correct': True}, {'text': 'все ж', 'correct': True}]}, {'question': "Оберіть синоніми до 'незважаючи на':", 'options': [{'text': 'попри', 'correct': True}, {'text': 'наперекір', 'correct': True}, {'text': 'всупереч', 'correct': True}, {'text': 'завдяки', 'correct': False}]}, {'question': 'Які слова виражають іронічний допуск?', 'options': [{'text': 'дарма що', 'correct': True}, {'text': 'хоч і', 'correct': True}, {'text': 'куди там', 'correct': True}, {'text': 'тому що', 'correct': False}]}, {'question': 'Оберіть сполучники для опису перешкод:', 'options': [{'text': 'хоча', 'correct': True}, {'text': 'незважаючи на', 'correct': True}, {'text': 'попри', 'correct': True}, {'text': 'оскільки', 'correct': False}]}, {'question': 'Які слова вказують на крайню поступку?', 'options': [{'text': 'хай', 'correct': True}, {'text': 'нехай', 'correct': True}, {'text': 'навіть якщо', 'correct': True}, {'text': 'бо', 'correct': False}]}, {'question': 'Оберіть ознаки допустового речення:', 'options': [{'text': 'наявність перешкоди', 'correct': True}, {'text': 'дія всупереч', 'correct': True}, {'text': 'логічний парадокс', 'correct': True}, {'text': 'проста причина', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 67-advanced-conjunctions-i.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 67-advanced-conjunctions-i.yaml: [index-9] select: 'items.0.options' - [{'text': 'тому що', 'correct': True}, {'text': 'бо', 'correct': True}, {'text': 'оскільки', 'correct': True}, {'text': 'через те що', 'correct': True}, {'text': 'завдяки тому що', 'correct': True}, {'text': 'внаслідок того що', 'correct': True}, {'text': 'адже', 'correct': True}, {'text': 'бо ж', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 67-advanced-conjunctions-i.yaml: [index-13] select: 'items.0.options' - [{'text': 'хоча', 'correct': True}, {'text': 'незважаючи на те що', 'correct': True}, {'text': 'попри те що', 'correct': True}, {'text': 'дарма що', 'correct': True}, {'text': 'хай', 'correct': True}, {'text': 'хоч', 'correct': True}, {'text': 'нехай', 'correct': True}, {'text': 'все ж', 'correct': True}] is too long
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
- 27 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2097/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 42/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 25 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.3% (target 90-100% (vocab))
- **Richness:** ✅ 99% (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 8 | 4 | 100% | 25% | 25.0% |
| variety | 0.95 | - | 95% | 17% | 15.8% |
| cultural | 3 | - | 100% | 17% | 16.7% |
| visual | 8 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 1.00 | - | 100% | 8% | 8.3% |
| examples | 45 | - | 100% | 8% | 8.3% |
| realworld | 7 | - | 100% | 8% | 8.3% |
| questions | 15 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **99.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 77 | Included in Core |
| **Вступ: Логіка зв'язків у Миколаєві та Херсоні** | ⚪️ | 80 | Skipped |
| **Частина 1: Причинні Сполучники — Майстерність пояснення «Чому?»** | ✅ | 181 | Included in Core |
| **Частина 2: Допустові Сполучники — Мистецтво всупереч обставинам** | ✅ | 127 | Included in Core |
| **Частина 3: Діалог про стратегію: Причина та Допуск у дії** | ✅ | 133 | Included in Core |
| **Частина 7: Логіка Аргументації та Сполучники у Праві** | ✅ | 94 | Included in Core |
| **Частина 8: Причинно-наслідкові зв'язки в Екології** | ✅ | 124 | Included in Core |
| **Частина 9: Побудова професійної дискусії та культури допусту** | ✅ | 84 | Included in Core |
| **Частина 10: Сполучники у Сучасних Медіа та Публіцистиці** | ✅ | 101 | Included in Core |
| **Частина 11: Побудова Аналітичного Звіту: Логіка Причини** | ✅ | 121 | Included in Core |
| **Частина 12: Культура Допуску та Стійкості** | ✅ | 83 | Included in Core |
| **Частина 10: Логічна архітектура речень у новинах** | ✅ | 146 | Included in Core |
| **Частина 11: Побудова аргументів у діловому середовищі** | ✅ | 145 | Included in Core |
| **Частина 12: Мова незламності та стратегічного вибору** | ✅ | 179 | Included in Core |
| **Частина 13: Діалог про результати кварталу: Логіка успіху** | ✅ | 164 | Included in Core |
| **Частина 14: Висновки про логічну структуру мови** | ✅ | 93 | Included in Core |
| **Підсумок** | ✅ | 55 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |