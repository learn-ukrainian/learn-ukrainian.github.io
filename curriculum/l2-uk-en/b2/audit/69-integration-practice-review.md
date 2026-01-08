# Audit Report: 69-integration-practice.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** Practice | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть мудрість із контекстом' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну ідіому' Q1 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну ідіому' Q3 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну ідіому' Q4 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну ідіому' Q5 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну ідіому' Q6 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну ідіому' Q7 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну ідіому' Q8 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** group-sort 'Стилістична палітра' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Трансформація тексту' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Логіка та Зв'язок' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q1 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q2 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q3 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q4 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q5 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q6 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q7 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кейс: Робота в Харкові' Q8 prompt length 3 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-integration-practice.yaml: [оберіть-точну-ідіому] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-integration-practice.yaml: [виправте-стиль] error-correction: 'items.7.options' - ["Дірява пам'ять", 'Золоті руки', 'Залізна воля'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-integration-practice.yaml: [переклад-інтеграції] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-integration-practice.yaml: [всі-засоби-виразності] select: 'items.0.options' - [{'text': 'ідіоми', 'correct': True}, {'text': "прислів'я", 'correct': True}, {'text': 'метафори', 'correct': True}, {'text': 'точні синоніми', 'correct': True}, {'text': 'епітети', 'correct': True}, {'text': 'порівняння', 'correct': True}, {'text': 'фразеологізми', 'correct': True}, {'text': 'риторичні фігури', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-integration-practice.yaml: [кейс:-робота-в-харкові] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-integration-practice.yaml: [майстерність-виступу] select: 'items.0.options' - [{'text': "влучні прислів'я", 'correct': True}, {'text': 'риторичні запитання', 'correct': True}, {'text': 'складні сполучники', 'correct': True}, {'text': 'професійна лексика', 'correct': True}, {'text': 'виразний висновок', 'correct': True}, {'text': 'емоційні ідіоми', 'correct': True}, {'text': "зв'язність тексту", 'correct': True}, {'text': 'віра в успіх', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (14 words): багатий, володіння, різноманітний, природний, автентичний...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 27 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1901/1750
- **Activities:** ✅ 14/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 46/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 26 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.8% (target 98-100% (vocab))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 35 | 24 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| dialogues | 4 | 4 | 100% | 15% | 15.0% |
| variety | 0.99 | - | 99% | 10% | 9.9% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| realworld | 7 | 3 | 100% | 10% | 10.0% |
| visual | 8 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 11 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.9%** |

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
| **Need More Practice?** | ⚪️ | 0 | Skipped |