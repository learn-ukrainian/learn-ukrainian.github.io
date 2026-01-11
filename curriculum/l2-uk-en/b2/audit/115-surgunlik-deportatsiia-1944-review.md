# Audit Report: 115-surgunlik-deportatsiia-1944.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q5 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Встановіть відповідність між терміном та його історичним значенням.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Знайдіть синоніми до слів з тексту модуля.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_OPTIONS]** quiz 'Перевірка розуміння' Q3 has 2 options (target: [4])
  - FIX: Provide [4] options for B2 quizzes.
- **[COMPLEXITY_OPTIONS]** quiz 'Перевірка розуміння' Q4 has 2 options (target: [4])
  - FIX: Provide [4] options for B2 quizzes.
- **[COMPLEXITY_OPTIONS]** quiz 'Перевірка розуміння' Q5 has 2 options (target: [4])
  - FIX: Provide [4] options for B2 quizzes.
- **[COMPLEXITY_OPTIONS]** quiz 'Перевірка розуміння' Q6 has 2 options (target: [4])
  - FIX: Provide [4] options for B2 quizzes.
- **[COMPLEXITY_OPTIONS]** quiz 'Перевірка розуміння' Q7 has 2 options (target: [4])
  - FIX: Provide [4] options for B2 quizzes.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння' Q8 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_OPTIONS]** quiz 'Перевірка розуміння' Q8 has 2 options (target: [4])
  - FIX: Provide [4] options for B2 quizzes.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 115-surgunlik-deportatsiia-1944.yaml: Array validation: {'type': 'quiz', 'items': [{'question': 'Чому важливо використовувати назву киримли замість просто татари?', 'options': [{'text': "Це підкреслює самоназву та суб'єктність корінного народу Криму", 'correct': True}, {'text': 'Це просто коротша назва, яку легше вимовляти іноземцям', 'correct': False}, {'text': 'Ця назва була вигадана радянськими вченими для класифікації', 'correct': False}, {'text': 'Ця назва вказує на релігійну приналежність людей до ісламу', 'correct': False}]}, {'question': 'Яка головна мета топонімічної агресії (перейменування міст) у Криму?', 'options': [{'text': "Створення ілюзії 'ісконно руської' землі через стирання татарських назв", 'correct': True}, {'text': 'Полегшення орієнтування на місцевості для нових переселенців', 'correct': False}, {'text': 'Виконання плану з модернізації географічних карт СРСР', 'correct': False}, {'text': 'Бажання зробити назви міст більш поетичними та красивими', 'correct': False}]}, {'question': 'Що символізує 18 травня для сучасного українського суспільства?', 'options': [{'text': "Спільну пам'ять про жертв тоталітаризму та солідарність у боротьбі", 'correct': True}, {'text': 'Просто ще один вихідний день у календарі офіційних дат', 'correct': False}]}, {'question': 'Яке значення має закон про корінні народи для майбутнього Криму?', 'options': [{'text': 'Він створює правову базу для відновлення прав після деокупації', 'correct': True}, {'text': 'Він забороняє будь-кому іншому жити на території Криму', 'correct': False}]}, {'question': 'Як пісня Джамали змінила сприйняття трагедії 1944 року у світі?', 'options': [{'text': 'Вона перетворила особисту сімейну історію на глобальний маніфест за людяність', 'correct': True}, {'text': 'Вона стала причиною заборони будь-яких пісень про історію на конкурсах', 'correct': False}]}, {'question': 'У чому полягає суть деколонізаційного погляду на історію?', 'options': [{'text': 'У поверненні голосу пригніченим народам та розвінчуванні імперських міфів', 'correct': True}, {'text': 'У заміні одного виду пропаганди на інший без пошуку правди', 'correct': False}]}, {'question': 'Який термін найкраще описує політику СРСР щодо кримськотатарської культури?', 'options': [{'text': 'Культурний геноцид', 'correct': True}, {'text': 'Культурний обмін', 'correct': False}]}, {'question': 'Що було головною зброєю кримськотатарського національного руху?', 'options': [{'text': 'Мирний спротив, листи, мітинги та правда', 'correct': True}, {'text': 'Збройні повстання та терористичні акти', 'correct': False}]}], 'title': 'Перевірка розуміння', 'instruction': 'Оберіть правильну відповідь.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 115-surgunlik-deportatsiia-1944.yaml: [index-4] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 115-surgunlik-deportatsiia-1944.yaml: [index-5] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 115-surgunlik-deportatsiia-1944.yaml: [index-10] translate: 'items.7.options' - [{'text': 'Тоталітарний режим', 'correct': True}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 115-surgunlik-deportatsiia-1944.yaml: [index-12] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 115-surgunlik-deportatsiia-1944.yaml: [index-13] quiz: 'items.7.options' - [{'text': 'Мирний спротив, листи, мітинги та правда', 'correct': True}, {'text': 'Збройні повстання та терористичні акти', 'correct': False}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Контекст та передумови геноциду, Вступ
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 20 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2011/2000
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 18 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 98.8% (target 90-100% (history))
- **Richness:** ✅ 97% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 11 | 3 | 100% | 24% | 23.8% |
| engagement | 12 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 162 | Included in Core |
| **Вступ** | ⚪️ | 252 | Skipped |
| **Історичний наратив: Трагедія Sürgünlik** | ⚪️ | 866 | Skipped |
| **Первинні джерела** | ⚪️ | 266 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 289 | Skipped |
| **Підсумок** | ✅ | 66 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |