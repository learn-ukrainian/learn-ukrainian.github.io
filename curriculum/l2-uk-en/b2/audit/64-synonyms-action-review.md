# Audit Report: 64-synonyms-action.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть характер дії' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q1 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q6 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Дія чи Результат?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Дія та Регістри' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Дія та Її Об'єкт' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q1 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q2 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q3 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q4 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q5 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q6 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q7 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q8 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: Array validation: {'type': 'select', 'title': 'Всі форми активності', 'instruction': 'Оберіть усі слова, що позначають процес творення або дії (6+ елементів).', 'items': [{'question': "Оберіть синоніми до 'робити' (6+):", 'options': [{'text': 'чинити', 'correct': True}, {'text': 'діяти', 'correct': True}, {'text': 'виконувати', 'correct': True}, {'text': 'здійснювати', 'correct': True}, {'text': 'реалізовувати', 'correct': True}, {'text': 'втілювати', 'correct': True}, {'text': 'творити', 'correct': True}]}, {'question': 'Які слова вказують на результат дії?', 'options': [{'text': 'результат', 'correct': True}, {'text': 'наслідок', 'correct': True}, {'text': 'ефект', 'correct': True}, {'text': 'процес', 'correct': False}]}, {'question': 'Оберіть дієслова для швидкої реакції:', 'options': [{'text': 'хапати', 'correct': True}, {'text': 'вхопити', 'correct': True}, {'text': 'вихопити', 'correct': True}, {'text': 'чекати', 'correct': False}]}, {'question': 'Які слова описують зміну?', 'options': [{'text': 'перетворювати', 'correct': True}, {'text': 'трансформувати', 'correct': True}, {'text': 'модернізувати', 'correct': True}, {'text': 'зберігати', 'correct': False}]}, {'question': 'Оберіть терміни для соціальної дії:', 'options': [{'text': 'акція', 'correct': True}, {'text': 'ініціатива', 'correct': True}, {'text': 'кампанія', 'correct': True}, {'text': 'сон', 'correct': False}]}, {'question': 'Які дієслова підходять для роботи з планами?', 'options': [{'text': 'здійснювати', 'correct': True}, {'text': 'реалізовувати', 'correct': True}, {'text': 'втілювати', 'correct': True}, {'text': 'руйнувати', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [index-9] select: 'items.0.options' - [{'text': 'чинити', 'correct': True}, {'text': 'діяти', 'correct': True}, {'text': 'виконувати', 'correct': True}, {'text': 'здійснювати', 'correct': True}, {'text': 'реалізовувати', 'correct': True}, {'text': 'втілювати', 'correct': True}, {'text': 'творити', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Частина 5: Практичний додаток — Контекст і Регістр мовлення, Частина 11: Дія в контексті відновлення міст, Вступ: Енергія українського чину та перетворення
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Фразеологізми' per template 'b2-phraseology-module-template'
  - FIX: Add '## Фразеологізми' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вживання у контексті' per template 'b2-phraseology-module-template'
  - FIX: Add '## Вживання у контексті' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 21 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1830/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 67/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 18 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (vocab))
- **Richness:** ✅ 98% (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 8 | 4 | 100% | 25% | 25.0% |
| variety | 0.96 | - | 96% | 17% | 16.0% |
| cultural | 3 | - | 100% | 17% | 16.7% |
| visual | 7 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.86 | - | 86% | 8% | 7.2% |
| examples | 43 | - | 100% | 8% | 8.3% |
| realworld | 8 | - | 100% | 8% | 8.3% |
| questions | 6 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **98.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ: Енергія українського чину та перетворення** | ⚪️ | 109 | Skipped |
| **Частина 1: Робити — Як ми змінюємо світ навколо себе** | ✅ | 286 | Included in Core |
| **Частина 2: Брати — Як ми взаємодіємо з ресурсами та об'єктами** | ✅ | 156 | Included in Core |
| **Частина 3: Категорії дії — Від вчинку до результату в аналізі** | ✅ | 144 | Included in Core |
| **Частина 4: Дія в українській культурі та філософії «чину»** | ✅ | 79 | Included in Core |
| **Частина 5: Практичний додаток — Контекст і Регістр мовлення** | ✅ | 13 | Included in Core |
| **Частина 6: Дія в епоху глобальних перетворень** | ✅ | 101 | Included in Core |
| **Частина 7: Відповідальність за кожен крок та результат** | ✅ | 65 | Included in Core |
| **Частина 8: Мистецтво вчинку та Моральна Дія** | ✅ | 93 | Included in Core |
| **Частина 9: Технологічна дія: Від алгоритму до результату** | ✅ | 79 | Included in Core |
| **Частина 10: Дія як головний інструмент соціальних змін** | ✅ | 171 | Included in Core |
| **Частина 11: Дія в контексті відновлення міст** | ✅ | 90 | Included in Core |
| **Частина 12: Дія як самореалізація в Дніпро** | ✅ | 76 | Included in Core |
| **Частина 13: Дія у сучасному мистецтві та медіа** | ✅ | 121 | Included in Core |
| **Підсумок** | ✅ | 50 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |