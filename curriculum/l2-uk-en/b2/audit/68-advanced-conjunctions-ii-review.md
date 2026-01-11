# Audit Report: 68-advanced-conjunctions-ii.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** Grammar | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть часову межу' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Умова чи Час?' Q1 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Умова чи Час?' Q2 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Умова чи Час?' Q3 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Умова чи Час?' Q4 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Умова чи Час?' Q5 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Умова чи Час?' Q6 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Умова чи Час?' Q7 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Умова чи Час?' Q8 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Часова лінія чи Умова?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Час та Події' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Реальне проти Нереального' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Сценарії майбутнього' Q1 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Сценарії майбутнього' Q2 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Сценарії майбутнього' Q3 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Сценарії майбутнього' Q4 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Сценарії майбутнього' Q5 prompt length 3 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Сценарії майбутнього' Q6 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Сценарії майбутнього' Q7 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Сценарії майбутнього' Q8 prompt length 3 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 68-advanced-conjunctions-ii.yaml: Array validation: {'type': 'select', 'title': 'Часові сполучники', 'instruction': 'Оберіть усі сполучники часу (6+ елементів).', 'items': [{'question': "Які слова відповідають на питання 'Коли?':", 'options': [{'text': 'щойно', 'correct': True}, {'text': 'поки', 'correct': True}, {'text': 'відколи', 'correct': True}, {'text': 'після того як', 'correct': True}, {'text': 'перед тим як', 'correct': True}, {'text': 'доки', 'correct': True}, {'text': 'тільки-но', 'correct': True}, {'text': 'відтоді як', 'correct': True}]}, {'question': 'Які слова описують тривалість?', 'options': [{'text': 'поки', 'correct': True}, {'text': 'доки', 'correct': True}, {'text': 'протягом', 'correct': True}, {'text': 'раптово', 'correct': False}]}, {'question': 'Оберіть сполучники для ретроспективи:', 'options': [{'text': 'відколи', 'correct': True}, {'text': 'відтоді як', 'correct': True}, {'text': 'з того часу як', 'correct': True}, {'text': 'завтра як', 'correct': False}]}, {'question': 'Які слова вказують на паралельність?', 'options': [{'text': 'поки', 'correct': True}, {'text': 'в той час як', 'correct': True}, {'text': 'тим часом як', 'correct': True}, {'text': 'після', 'correct': False}]}, {'question': 'Оберіть терміни для послідовності:', 'options': [{'text': 'спочатку', 'correct': True}, {'text': 'потім', 'correct': True}, {'text': 'згодом', 'correct': True}, {'text': 'разом', 'correct': False}]}, {'question': "Які сполучники мають значення 'відразу після'?", 'options': [{'text': 'щойно', 'correct': True}, {'text': 'тільки-но', 'correct': True}, {'text': 'ледве', 'correct': True}, {'text': 'давно', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 68-advanced-conjunctions-ii.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 68-advanced-conjunctions-ii.yaml: [index-9] select: 'items.0.options' - [{'text': 'якщо', 'correct': True}, {'text': 'якби', 'correct': True}, {'text': 'коли б', 'correct': True}, {'text': 'у випадку якщо', 'correct': True}, {'text': 'за умови що', 'correct': True}, {'text': 'при умові що', 'correct': True}, {'text': 'аби (у значенні умови)', 'correct': True}, {'text': 'коли (у значенні умови)', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 68-advanced-conjunctions-ii.yaml: [index-13] select: 'items.0.options' - [{'text': 'щойно', 'correct': True}, {'text': 'поки', 'correct': True}, {'text': 'відколи', 'correct': True}, {'text': 'після того як', 'correct': True}, {'text': 'перед тим як', 'correct': True}, {'text': 'доки', 'correct': True}, {'text': 'тільки-но', 'correct': True}, {'text': 'відтоді як', 'correct': True}] is too long
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
- **Words:** ✅ 2027/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 51/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 25 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (vocab))
- **Richness:** ✅ 99% (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 8 | 4 | 100% | 25% | 25.0% |
| variety | 0.96 | - | 96% | 17% | 16.0% |
| cultural | 7 | - | 100% | 17% | 16.7% |
| visual | 8 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 1.00 | - | 100% | 8% | 8.3% |
| examples | 26 | - | 100% | 8% | 8.3% |
| realworld | 4 | - | 100% | 8% | 8.3% |
| questions | 15 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **99.3%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 76 | Included in Core |
| **Вступ: Ритми часу в Полтаві та Сумах** | ⚪️ | 81 | Skipped |
| **Частина 1: Часові Сполучники — Майстерність Хронології** | ✅ | 144 | Included in Core |
| **Частина 2: Умовні Сполучники — Мистецтво Можливостей та Гіпотез** | ✅ | 125 | Included in Core |
| **Частина 3: Діалог про подорож: Час та Умова в планах** | ✅ | 114 | Included in Core |
| **Частина 7: Часові сценарії в Українській Літературі** | ✅ | 89 | Included in Core |
| **Частина 8: Умовні конструкції в Бізнес-Плануванні** | ✅ | 101 | Included in Core |
| **Частина 9: Побудова складних логічних ланцюжків у житті** | ✅ | 91 | Included in Core |
| **Частина 10: Сполучники у Плануванні Подорожей та Логістиці** | ✅ | 102 | Included in Core |
| **Частина 11: Час в Історичній Хроніці та Описах** | ✅ | 89 | Included in Core |
| **Частина 12: Гіпотетичне Майбутнє та Умовні Сценарії** | ✅ | 124 | Included in Core |
| **Частина 10: Побудова складних часових ланцюжків** | ✅ | 152 | Included in Core |
| **Частина 11: Умовні Сценарії у Стратегічному Мисленні** | ✅ | 147 | Included in Core |
| **Частина 12: Гіпотетичне Буття та Історична Уява** | ✅ | 180 | Included in Core |
| **Частина 13: Діалог про майбутнє: Сценарії розвитку в Сумах** | ✅ | 154 | Included in Core |
| **Частина 14: Мистецтво часової та умовної координації** | ✅ | 93 | Included in Core |
| **Підсумок** | ✅ | 55 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |