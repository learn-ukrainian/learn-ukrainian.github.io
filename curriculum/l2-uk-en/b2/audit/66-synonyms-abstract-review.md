# Audit Report: 66-synonyms-abstract.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть точне поняття' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** group-sort 'Рівні абстракції' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть інтелектуальну фразу' item 4 has 21 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY]** match-up 'Регістри та Поняття' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Думка та Наслідок' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q1 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q2 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q3 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q4 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q5 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q6 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q7 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q8 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: Array validation: {'type': 'select', 'title': 'Стратегічні Поняття', 'instruction': 'Оберіть усі слова про високі ідеали (6+ елементів).', 'items': [{'question': 'Які терміни описують цінності (6+):', 'options': [{'text': 'свобода', 'correct': True}, {'text': 'справедливість', 'correct': True}, {'text': 'гідність', 'correct': True}, {'text': 'істина', 'correct': True}, {'text': 'честь', 'correct': True}, {'text': 'гуманізм', 'correct': True}, {'text': 'солідарність', 'correct': True}, {'text': 'толерантність', 'correct': True}]}, {'question': 'Які слова описують духовний розвиток?', 'options': [{'text': 'просвітлення', 'correct': True}, {'text': 'самовдосконалення', 'correct': True}, {'text': 'пізнання', 'correct': True}, {'text': 'застій', 'correct': False}]}, {'question': "Оберіть характеристики 'наукового' підходу:", 'options': [{'text': "об'єктивність", 'correct': True}, {'text': 'доказовість', 'correct': True}, {'text': 'системність', 'correct': True}, {'text': 'чутки', 'correct': False}]}, {'question': "Які слова вказують на 'візію' майбутнього?", 'options': [{'text': 'перспектива', 'correct': True}, {'text': 'прогноз', 'correct': True}, {'text': 'проєкт', 'correct': True}, {'text': 'минуле', 'correct': False}]}, {'question': "Оберіть терміни для опису 'істини':", 'options': [{'text': "об'єктивна", 'correct': True}, {'text': 'незаперечна', 'correct': True}, {'text': 'абсолютна', 'correct': True}, {'text': 'хибна', 'correct': False}]}, {'question': "Які слова описують 'національний' вимір?", 'options': [{'text': 'ідентичність', 'correct': True}, {'text': 'свідомість', 'correct': True}, {'text': 'патріотизм', 'correct': True}, {'text': 'байдужість', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [index-9] select: 'items.0.options' - [{'text': 'концепція', 'correct': True}, {'text': 'теорія', 'correct': True}, {'text': 'гіпотеза', 'correct': True}, {'text': 'поняття', 'correct': True}, {'text': 'аксіома', 'correct': True}, {'text': 'принцип', 'correct': True}, {'text': 'теза', 'correct': True}, {'text': 'доктрина', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [index-13] select: 'items.0.options' - [{'text': 'свобода', 'correct': True}, {'text': 'справедливість', 'correct': True}, {'text': 'гідність', 'correct': True}, {'text': 'істина', 'correct': True}, {'text': 'честь', 'correct': True}, {'text': 'гуманізм', 'correct': True}, {'text': 'солідарність', 'correct': True}, {'text': 'толерантність', 'correct': True}] is too long
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
- 20 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2524/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 87/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 18 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (vocab))
- **Richness:** ✅ 98% (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 11 | 4 | 100% | 25% | 25.0% |
| variety | 0.95 | - | 95% | 17% | 15.8% |
| cultural | 3 | - | 100% | 17% | 16.7% |
| visual | 11 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.93 | - | 93% | 8% | 7.8% |
| examples | 52 | - | 100% | 8% | 8.3% |
| realworld | 8 | - | 100% | 8% | 8.3% |
| questions | 11 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **98.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 74 | Included in Core |
| **Вступ: Лабіринти української думки** | ⚪️ | 95 | Skipped |
| **Частина 1: Світ Думки — Від «здогаду» до «переконання»** | ✅ | 171 | Included in Core |
| **Частина 2: Архітектура Теорії — Від «поняття» до «концепції»** | ✅ | 182 | Included in Core |
| **Частина 3: Логіка Аргументації — Від «підстави» до «висновку»** | ✅ | 121 | Included in Core |
| **Частина 6: Етика ідей та Інтелектуальна Відповідальність** | ✅ | 115 | Included in Core |
| **Частина 7: Абстрактні Поняття у Державотворенні** | ✅ | 143 | Included in Core |
| **Частина 8: Формування ідей у цифрову епоху** | ✅ | 97 | Included in Core |
| **Частина 9: Психологія Сприйняття та Уявлення про світ** | ✅ | 139 | Included in Core |
| **Частина 10: Логічна Стрункість Аргументації та доказовість** | ✅ | 92 | Included in Core |
| **Частина 11: Концепція Свободи в Українській Думці** | ✅ | 96 | Included in Core |
| **Частина 12: Логіка Наукового Пізнання та Відкриттів** | ✅ | 116 | Included in Core |
| **Частина 13: Формування Культури Дискусії** | ✅ | 79 | Included in Core |
| **Частина 11: Глибоке коріння української філософської думки** | ✅ | 174 | Included in Core |
| **Частина 12: Абстрактні Поняття в епоху Штучного Інтелекту** | ✅ | 126 | Included in Core |
| **Частина 13: Психологія ідей та їхній вплив на вчинки** | ✅ | 236 | Included in Core |
| **Частина 14: Інтелектуальна Стійкість у Світі Фейків** | ✅ | 161 | Included in Core |
| **Частина 15: Філософія Серця та Сучасні Цінності** | ✅ | 144 | Included in Core |
| **Підсумок** | ✅ | 53 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |