# Audit Report: 69-integration-practice.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** Practice | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть мудрість із контекстом' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну ідіому' Q3 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну ідіому' Q8 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Стилістична палітра' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Трансформація тексту' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Логіка та Зв'язок' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q1 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q2 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q3 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q4 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q5 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q6 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q7 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q8 prompt length 3 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-integration-practice.yaml: Array validation: {'type': 'select', 'title': 'Майстерність виступу', 'instruction': 'Оберіть елементи рівня B2 (6+ елементів).', 'items': [{'question': 'Які прийоми варто використовувати? (6+)', 'options': [{'text': "влучні прислів'я", 'correct': True}, {'text': 'риторичні запитання', 'correct': True}, {'text': 'складні сполучники', 'correct': True}, {'text': 'професійна лексика', 'correct': True}, {'text': 'виразний висновок', 'correct': True}, {'text': 'емоційні ідіоми', 'correct': True}, {'text': "зв'язність тексту", 'correct': True}, {'text': 'віра в успіх', 'correct': True}]}, {'question': 'Оберіть ознаки професійної презентації:', 'options': [{'text': 'структурованість', 'correct': True}, {'text': 'аргументованість', 'correct': True}, {'text': 'динамічність', 'correct': True}, {'text': 'хаотичність', 'correct': False}]}, {'question': 'Які слова підсилюють довіру аудиторії?', 'options': [{'text': 'обґрунтовано', 'correct': True}, {'text': 'доведено', 'correct': True}, {'text': 'фахово', 'correct': True}, {'text': 'мабуть', 'correct': False}]}, {'question': 'Оберіть засоби невербальної комунікації:', 'options': [{'text': 'зоровий контакт', 'correct': True}, {'text': 'жестикуляція', 'correct': True}, {'text': 'впевнений голос', 'correct': True}, {'text': 'читання в підлогу', 'correct': False}]}, {'question': 'Які ідіоми пасують для заклику до дії?', 'options': [{'text': 'гори звернути', 'correct': True}, {'text': 'взяти себе в руки', 'correct': True}, {'text': 'не пасти задніх', 'correct': True}, {'text': 'бити байдики', 'correct': False}]}, {'question': 'Оберіть частини успішного виступу:', 'options': [{'text': 'яскравий вступ', 'correct': True}, {'text': 'доказова частина', 'correct': True}, {'text': 'сильний підсумок', 'correct': True}, {'text': 'мовчання', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-integration-practice.yaml: [index-6] error-correction: 'items.7.options' - ["Дірява пам'ять", 'Золоті руки', 'Залізна воля'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-integration-practice.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-integration-practice.yaml: [index-9] select: 'items.0.options' - [{'text': 'ідіоми', 'correct': True}, {'text': "прислів'я", 'correct': True}, {'text': 'метафори', 'correct': True}, {'text': 'точні синоніми', 'correct': True}, {'text': 'епітети', 'correct': True}, {'text': 'порівняння', 'correct': True}, {'text': 'фразеологізми', 'correct': True}, {'text': 'риторичні фігури', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-integration-practice.yaml: [index-13] select: 'items.0.options' - [{'text': "влучні прислів'я", 'correct': True}, {'text': 'риторичні запитання', 'correct': True}, {'text': 'складні сполучники', 'correct': True}, {'text': 'професійна лексика', 'correct': True}, {'text': 'виразний висновок', 'correct': True}, {'text': 'емоційні ідіоми', 'correct': True}, {'text': "зв'язність тексту", 'correct': True}, {'text': 'віра в успіх', 'correct': True}] is too long
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
- 22 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2011/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 46/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 20 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 90-100% (vocab))
- **Richness:** ✅ 99% (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 9 | 4 | 100% | 25% | 25.0% |
| variety | 0.99 | - | 99% | 17% | 16.5% |
| cultural | 4 | - | 100% | 17% | 16.7% |
| visual | 8 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 1.00 | - | 100% | 8% | 8.3% |
| examples | 36 | - | 100% | 8% | 8.3% |
| realworld | 7 | - | 100% | 8% | 8.3% |
| questions | 11 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Вступ: Мозаїка вільних знань та професійного зростання** | ⚪️ | 120 | Skipped |
| **Частина 1: Аргументація з народним корінням та логічною структурою** | ✅ | 195 | Included in Core |
| **Частина 2: Діалог про майбутнє: Координація зусиль у Дніпрі** | ✅ | 217 | Included in Core |
| **Частина 3: Ідіоми в наративі: Оживляємо розповідь про Одесу** | ✅ | 90 | Included in Core |
| **Частина 4: Синонімічна гнучкість: Тонка робота з регістрами** | ✅ | 96 | Included in Core |
| **Частина 5: Складні сполучники як архітектура зрілої думки** | ✅ | 64 | Included in Core |
| **Частина 6: Культурний код та Сучасність у мовленні** | ✅ | 136 | Included in Core |
| **Частина 7: Аналіз тексту на фразеологічне багатство** | ✅ | 200 | Included in Core |
| **Частина 8: Публічний виступ: Як підкорити аудиторію словом** | ✅ | 187 | Included in Core |
| **Частина 9: Лист до майбутнього себе: Практика вільного письма** | ✅ | 110 | Included in Core |
| **Частина 10: Етика професійної дискусії: Коли мовчання — золото** | ✅ | 154 | Included in Core |
| **Частина 11: Письмова практика: Складання переконливого мотиваційного есею** | ✅ | 212 | Included in Core |
| **Підсумок** | ✅ | 48 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |