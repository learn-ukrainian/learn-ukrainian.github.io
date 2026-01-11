# Audit Report: 63-synonyms-quantity.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть точну міру' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть масштаб' Q8 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Багато чи Мало?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Регістри та Кількість' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Кількість та Об'єкти' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q1 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q2 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q3 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q4 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q5 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q6 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q7 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q8 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: Array validation: {'type': 'select', 'title': 'Всі відтінки багатоманітності', 'instruction': 'Оберіть усі слова, що позначають велику кількість (6+ елементів).', 'items': [{'question': 'Які синоніми вказують на значний обсяг? (6+)', 'options': [{'text': 'чимало', 'correct': True}, {'text': 'безліч', 'correct': True}, {'text': 'сила-силенна', 'correct': True}, {'text': 'маса', 'correct': True}, {'text': 'купа', 'correct': True}, {'text': 'повно', 'correct': True}, {'text': 'хоч греблю гати', 'correct': True}, {'text': 'мізер', 'correct': False}]}, {'question': 'Які слова вказують на надлишок?', 'options': [{'text': 'занадто', 'correct': True}, {'text': 'надто', 'correct': True}, {'text': 'надмір', 'correct': True}, {'text': 'дефіцит', 'correct': False}]}, {'question': 'Оберіть терміни для фінансових розрахунків:', 'options': [{'text': 'сума', 'correct': True}, {'text': 'бюджет', 'correct': True}, {'text': 'витрати', 'correct': True}, {'text': 'радість', 'correct': False}]}, {'question': 'Які слова описують нескінченність?', 'options': [{'text': 'безмежність', 'correct': True}, {'text': 'неосяжність', 'correct': True}, {'text': 'нескінченність', 'correct': True}, {'text': 'кілька', 'correct': False}]}, {'question': "Оберіть синоніми до 'мало':", 'options': [{'text': 'небагато', 'correct': True}, {'text': 'мізер', 'correct': True}, {'text': "дріб'язок", 'correct': True}, {'text': 'маса', 'correct': False}]}, {'question': 'Які слова вказують на достатність?', 'options': [{'text': 'вдосталь', 'correct': True}, {'text': 'достатньо', 'correct': True}, {'text': 'доволі', 'correct': True}, {'text': 'замало', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [index-9] select: 'items.0.options' - [{'text': 'чимало', 'correct': True}, {'text': 'безліч', 'correct': True}, {'text': 'сила-силенна', 'correct': True}, {'text': 'маса', 'correct': True}, {'text': 'купа', 'correct': True}, {'text': 'повно', 'correct': True}, {'text': 'хоч греблю гати', 'correct': True}, {'text': 'мізер', 'correct': False}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Вступ: Масштаби українського життя, Таблиця відповідності регістрам та контекстам
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Фразеологізми' per template 'b2-phraseology-module-template'
  - FIX: Add '## Фразеологізми' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вживання у контексті' per template 'b2-phraseology-module-template'
  - FIX: Add '## Вживання у контексті' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 20 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2392/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 60/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 17 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.3% (target 90-100% (vocab))
- **Richness:** ❌ 93% < 95% min (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 93% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 9 | 4 | 100% | 25% | 25.0% |
| variety | 0.71 | - | 71% | 17% | 11.8% |
| cultural | 5 | - | 100% | 17% | 16.7% |
| visual | 8 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.85 | - | 85% | 8% | 7.1% |
| examples | 65 | - | 100% | 8% | 8.3% |
| realworld | 9 | - | 100% | 8% | 8.3% |
| questions | 9 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **93.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 69 | Included in Core |
| **Вступ: Масштаби українського життя** | ⚪️ | 98 | Skipped |
| **Частина 1: Океан багатоманітності — Від «багато» до «безлічі»** | ✅ | 280 | Included in Core |
| **Частина 2: Острів недостатності — Від «мало» до «декількох»** | ✅ | 253 | Included in Core |
| **Частина 3: Параметри вимірювання та Аналіз обсягів** | ✅ | 111 | Included in Core |
| **Частина 4: Кількість у дзеркалі української історії та культури** | ✅ | 135 | Included in Core |
| **Частина 5: Практичний додаток — Регістри та Акценти** | ✅ | 16 | Included in Core |
| **Частина 6: Психологія сприйняття кількості** | ✅ | 116 | Included in Core |
| **Частина 7: Формування культури достатку** | ✅ | 133 | Included in Core |
| **Частина 8: Кількість у цифрову епоху** | ✅ | 95 | Included in Core |
| **Частина 9: Соціальний масштаб та Кількість можливостей** | ✅ | 80 | Included in Core |
| **Частина 3: Параметри вимірювання та Аналіз обсягів у професійній мові** | ✅ | 166 | Included in Core |
| **Частина 5: Практичний додаток — Регістри та Кількісні Акценти** | ✅ | 22 | Included in Core |
| **Частина 6: Психологія сприйняття кількості та баланс у житті** | ✅ | 138 | Included in Core |
| **Частина 7: Формування культури свідомого достатку** | ✅ | 96 | Included in Core |
| **Підсумок** | ✅ | 52 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |