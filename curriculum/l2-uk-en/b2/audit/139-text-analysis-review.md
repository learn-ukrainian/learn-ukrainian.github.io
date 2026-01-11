# Audit Report: 139-text-analysis.md
**Phase:** B2.4 | **Level:** B2 | **Pedagogy:** TTT | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Основи аналізу тексту' Q3 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Визначення риторичних фігур' item 4 has 8 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Визначення цільової аудиторії' Q6 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 139-text-analysis.yaml: Array validation: {'type': 'translate', 'title': 'Трансформація: Факт vs Судження', 'items': [{'options': [{'text': 'Запропонований законопроект передбачає зміну податкових ставок на 5%.', 'correct': True}, {'text': 'Уряд хоче вкрасти наші гроші через нові правила.'}, {'text': 'Це найгірше рішення в історії нашої держави.'}], 'source': 'Цей жахливий закон знищить нашу економіку.'}, {'options': [{'text': 'За даними поліції, у заході взяли участь близько трьох тисяч осіб.', 'correct': True}, {'text': "Весь народ вийшов на вулиці, щоб сказати 'ні'."}, {'text': 'Ми бачили неймовірну кількість небайдужих людей.'}], 'source': 'На мітинг прийшла величезна купа патріотів.'}, {'options': [{'text': 'Наведені посадовцем цифри не збігаються з даними офіційної статистики.', 'correct': True}, {'text': 'Всі знають, що він ніколи не каже правду.'}, {'text': 'Його слова — це просто чергова порція маніпуляцій.'}], 'source': 'Він знову бреше про свої успіхи на посаді.'}, {'options': [{'text': 'Збройні Сили України продовжують утримувати оборонні позиції на вказаному напрямку.', 'correct': True}, {'text': 'Ніхто і ніколи не здолає наш сталевий дух.'}, {'text': 'Ворог тремтить перед силою нашої незламної армії.'}], 'source': 'Наші воїни — це справжні титани, яких неможливо перемогти.'}, {'options': [{'text': 'Внаслідок обстрілу було пошкоджено десять житлових будинків та школу.', 'correct': True}, {'text': 'Окупанти перетворили наш квітучий сад на руїни.'}, {'text': 'Це трагедія, яку неможливо описати жодними словами.'}], 'source': 'Місто виглядає просто жахливо після обстрілу.'}, {'options': [{'text': 'Запроваджена реформа отримала позитивні оцінки від експертів Світового банку.', 'correct': True}, {'text': 'Нарешті ми маємо найкращий у світі план розвитку.'}, {'text': 'Уряд зробив те, про що ми всі мріяли роками.'}], 'source': 'Ця реформа — просто геніальний крок уряду.'}, {'options': [{'text': 'Проти даної особи порушено кримінальну справу за статтею про державну зраду.', 'correct': True}, {'text': 'Він продав свою совість за тридцять срібняків.'}, {'text': 'Його вчинки свідчать про повну відсутність патріотизму.'}], 'source': 'Він — типовий зрадник і прислужник окупантів.'}, {'options': [{'text': 'Роман отримав високі відгуки критиків за глибокий психологізм.', 'correct': True}, {'text': 'Ви ніколи не будете такими, як раніше, після читання цього шедевру.'}, {'text': 'Це найкращий текст, написаний українською мовою в цьому столітті.'}], 'source': 'Ця книга змінить ваше життя назавжди.'}], 'instruction': 'Виберіть найбільш об’єктивну (фактологічну) версію для наведеного речення.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 139-text-analysis.yaml: [index-7] error-correction: 'items.7' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 139-text-analysis.yaml: [index-8] translate: 'items.7.options.2' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 139-text-analysis.yaml: [index-11] translate: 'items.7.options.2' - 'correct' is a required property
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
- 12 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2440/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 8 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.0% (target 90-100% (skills))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 88 | 24 | 100% | 20% | 20.0% |
| engagement | 7 | 5 | 100% | 15% | 15.0% |
| dialogues | 8 | 4 | 100% | 15% | 15.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 6 | 3 | 100% | 10% | 10.0% |
| visual | 3 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 14 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 69 | Included in Core |
| **Diagnostic: Що ми бачимо?** | ✅ | 339 | Included in Core |
| **Analysis: Читання між рядків** | ✅ | 327 | Included in Core |
| **Deep Dive: Риторика та маніпуляція** | ✅ | 290 | Included in Core |
| **Аналіз художнього образу: Imagery Mapping** | ✅ | 251 | Included in Core |
| **Practice: Розбір у дії** | ⚪️ | 482 | Skipped |
| **Reading Practice: Деконструкція воєнного звернення** | ✅ | 289 | Included in Core |
| **✍️ Аналітичний розбір** | ⚪️ | 218 | Skipped |
| **Summary** | ✅ | 65 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |