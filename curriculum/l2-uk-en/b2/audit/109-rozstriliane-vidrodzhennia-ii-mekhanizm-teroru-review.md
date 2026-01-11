# Audit Report: 109-rozstriliane-vidrodzhennia-ii-mekhanizm-teroru.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння' Q4 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Встановіть відповідності' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння' Q1 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння' Q2 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння' Q4 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння' Q6 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння' Q8 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 109-rozstriliane-vidrodzhennia-ii-mekhanizm-teroru.yaml: Array validation: {'type': 'select', 'instruction': 'Виберіть усі правильні твердження щодо наслідків сталінського терору для української культури.', 'items': [{'question': 'Якими були реальні наслідки репресій для культурного життя України?', 'options': [{'text': 'Було знищено або репресовано близько 80% творчої еліти', 'correct': True}, {'text': 'Культура почала розвиватися швидше завдяки державній підтримці', 'correct': False}, {'text': 'Відбувся розрив тяглості культурного розвитку поколінь', 'correct': True}, {'text': 'Митці опинилися под жорстким тиском цензури та соцреалізму', 'correct': True}, {'text': 'Російська мова стала єдиною дозволеною мовою в театрах', 'correct': False}, {'text': 'Багато творів було назавжди втрачено або заборонено', 'correct': True}, {'text': 'Культура була штучно загнана у рамки етнографізму', 'correct': True}]}, {'question': 'Які методи використовували спецслужби для приховування правди про розстріли?', 'options': [{'text': 'Видача фальшивих свідоцтв про смерть від хвороб', 'correct': True}, {'text': 'Засекречування архівів на довгі десятиліття', 'correct': True}, {'text': 'Маскування розстрільних ям за допомогою насаджень дерев', 'correct': True}, {'text': 'Публікація списків розстріляних у місцевих газетах', 'correct': False}, {'text': 'Використання віддалених урочищ для страт', 'correct': True}]}, {'question': 'Що було характерним для перебування українських інтелектуалів на Соловках?', 'options': [{'text': 'Робота на важких лісозаготівлях та будівництві', 'correct': True}, {'text': 'Можливість вільного листування з родинами без цензури', 'correct': False}, {'text': 'Намагання продовжувати творчу та інтелектуальну діяльність', 'correct': True}, {'text': "Створення 'українського земляцтва' для підтримки один одного", 'correct': True}, {'text': 'Отримання підвищеного харчового пайка як для науковців', 'correct': False}]}, {'question': 'Які звинувачення найчастіше висували українським митцям?', 'options': [{'text': 'Шпигунство на користь іноземних розвідок', 'correct': True}, {'text': 'Контрреволюційна терористична діяльність', 'correct': True}, {'text': 'Приналежність до вигаданих підпільних організацій', 'correct': True}, {'text': 'Порушення правил дорожнього руху у Києві', 'correct': False}, {'text': 'Український буржуазний націоналізм', 'correct': True}]}, {'question': 'Чому Сандармох вважається символом трагедії Розстріляного відродження?', 'options': [{'text': 'Там було знищено понад 300 представників української еліти за один тиждень', 'correct': True}, {'text': 'Це було місце таємних масових поховань, прихованих державою', 'correct': True}, {'text': 'Там загинули такі видатні постаті як Курбас, Зеров та Куліш', 'correct': True}, {'text': 'Це було місце підписання акту про незалежність', 'correct': False}, {'text': 'Відкриття цього місця у 1997 році стало моментом істини для нації', 'correct': True}]}, {'question': 'Яким був вплив репресій на подальший розвиток української мови та культури?', 'options': [{'text': 'Штучне звуження сфер вживання української мови', 'correct': True}, {'text': "Нав'язування комплексу меншовартості українцям", 'correct': True}, {'text': 'Знищення модерних та авангардних напрямків у мистецтві', 'correct': True}, {'text': 'Стрімке зростання кількості україномовних видань', 'correct': False}, {'text': 'Фізичне усунення носіїв високої інтелектуальної традиції', 'correct': True}]}], 'title': 'Виберіть правильні відповіді'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 109-rozstriliane-vidrodzhennia-ii-mekhanizm-teroru.yaml: [index-4] select: 'items.0.options' - [{'text': 'Було знищено або репресовано близько 80% творчої еліти', 'correct': True}, {'text': 'Культура почала розвиватися швидше завдяки державній підтримці', 'correct': False}, {'text': 'Відбувся розрив тяглості культурного розвитку поколінь', 'correct': True}, {'text': 'Митці опинилися под жорстким тиском цензури та соцреалізму', 'correct': True}, {'text': 'Російська мова стала єдиною дозволеною мовою в театрах', 'correct': False}, {'text': 'Багато творів було назавжди втрачено або заборонено', 'correct': True}, {'text': 'Культура була штучно загнана у рамки етнографізму', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Контекст: Від сподівань до розстрільних ям, Вступ, Контекст: Велика чистка та Наказ № 00447
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!myth-buster]' per template 'b2-history-module-template'
  - FIX: Add a `> [!myth-buster]` box as specified in the template. This enhances module quality.
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!history-bite]' per template 'b2-history-module-template'
  - FIX: Add a `> [!history-bite]` box as specified in the template. This enhances module quality.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 15 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2002/2000
- **Activities:** ✅ 13/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 26/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 11 violations
- **Content_heavy:** ✅ Content-heavy OK (13 activities)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 6 | 3 | 100% | 24% | 23.8% |
| engagement | 8 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 14 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 4 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 4 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 58 | Included in Core |
| **Вступ** | ⚪️ | 161 | Skipped |
| **Машина державного терору** | ⚪️ | 1202 | Skipped |
| **Первинні джерела** | ⚪️ | 108 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 151 | Skipped |
| **Підсумок** | ✅ | 212 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |