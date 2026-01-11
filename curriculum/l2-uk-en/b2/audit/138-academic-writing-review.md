# Audit Report: 138-academic-writing.md
**Phase:** B2.4 | **Level:** B2 | **Pedagogy:** TTT | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Структура та термінологія есе' Q3 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Структура та термінологія есе' Q5 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Структура та термінологія есе' Q7 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Структура та термінологія есе' Q8 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Аналіз логічних зв’язків' Q4 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Аналіз логічних зв’язків' Q6 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Аналіз логічних зв’язків' Q8 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 138-academic-writing.yaml: Array validation: {'type': 'translate', 'title': 'Академічна трансформація', 'items': [{'options': [{'text': 'Результати дослідження підтверджують ефективність даної методики.', 'correct': True}, {'text': 'Ця штука реально працює для всіх людей.'}, {'text': 'Ми думаємо, що це прикольна ідея.'}], 'source': 'Ну, ця штука реально працює в більшості випадків.'}, {'options': [{'text': 'Наведений аргумент викликає певні сумніви через брак доказів.', 'correct': True}, {'text': 'Я не хочу читати те, що він написав.'}, {'text': 'Це просто неправильна думка якогось автора.'}], 'source': 'Я просто не згоден з тим, що він там написав.'}, {'options': [{'text': 'Протягом останнього десятиліття було здійснено низку значущих наукових відкриттів.', 'correct': True}, {'text': "Круті відкриття з'являються щодня в інтернеті."}, {'text': 'Багато людей роблять щось цікаве в науці.'}], 'source': 'Вони зробили багато крутих відкриттів останнім часом.'}, {'options': [{'text': 'Отже, існує об’єктивна потреба у збільшенні фінансування даної галузі.', 'correct': True}, {'text': 'Короче, дайте нам гроші на проекти.'}, {'text': 'Фінанси — це головне для нашої роботи.'}], 'source': 'Короче, нам треба більше грошей на ці речі.'}, {'options': [{'text': 'Згідно з численними дослідженнями, дане явище негативно впливає на розвиток дитини.', 'correct': True}, {'text': 'Всі люди кажуть, що дітям це не подобається.'}, {'text': 'Це погана річ для кожної малої дитини.'}], 'source': 'Всі знають, що це погано впливає на дітей.'}, {'options': [{'text': 'Проаналізуємо наведений приклад детальніше для глибшого розуміння.', 'correct': True}, {'text': 'Давайте ще раз глянемо на цю картинку.'}, {'text': 'Цей приклад дуже важливий для нас сьогодні.'}], 'source': 'Давайте подивимося на цей приклад ще раз.'}, {'options': [{'text': 'Застосування запропонованого підходу сприятиме ефективному розв’язанню проблеми.', 'correct': True}, {'text': 'Я вірю, що ми все зробимо правильно.'}, {'text': 'Ця ідея є суперською для кожного з нас.'}], 'source': 'Я думаю, це допоможе вирішити проблему.'}, {'options': [{'text': 'Дана стаття характеризується надмірною деталізацією та низькою динамікою викладу.', 'correct': True}, {'text': 'Я не зміг дочитати цю довгу статтю до кінця.'}, {'text': 'Текст є великим і нецікавим для студентів.'}], 'source': 'Ця стаття занадто довга і нудна.'}], 'instruction': 'Виберіть найбільш відповідний академічний варіант для розмовного речення.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 138-academic-writing.yaml: [index-7] error-correction: 'items.7' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 138-academic-writing.yaml: [index-8] translate: 'items.7.options.2' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 138-academic-writing.yaml: [index-11] translate: 'items.7.options.2' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: skills) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'b2-integration-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b2-integration-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Стратегії' per template 'b2-integration-module-template'
  - FIX: Add '## Стратегії' section as specified in docs/l2-uk-en/templates/b2-integration-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Практика|Вправи' per template 'b2-integration-module-template'
  - FIX: Add '## Практика' section as specified in docs/l2-uk-en/templates/b2-integration-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'b2-integration-module-template'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/b2-integration-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 16 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2848/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 12 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (skills))
- **Richness:** ✅ 96% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 69 | 24 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| dialogues | 8 | 4 | 100% | 15% | 15.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 5 | 3 | 100% | 10% | 10.0% |
| visual | 6 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 12 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 61 | Included in Core |
| **Diagnostic: Аналіз структури** | ✅ | 455 | Included in Core |
| **Analysis: Анатомія аргументу** | ⚪️ | 328 | Skipped |
| **Deep Dive: Цитування та доброчесність** | ✅ | 678 | Included in Core |
| **Practice: Від чернетки до есе** | ⚪️ | 471 | Skipped |
| **Reading Practice: Мова наукового діалогу** | ✅ | 348 | Included in Core |
| **✍️ Написання есе** | ⚪️ | 320 | Skipped |
| **Summary** | ✅ | 77 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |