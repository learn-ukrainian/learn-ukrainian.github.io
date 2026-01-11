# Audit Report: 59-synonyms-communication.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть контекст мовлення' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне дієслово' Q5 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне дієслово' Q7 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Рівень офіційності' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Спілкування та Регістри' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Антоніми спілкування' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q1 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q2 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q3 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q4 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q5 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q6 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q7 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q8 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 59-synonyms-communication.yaml: Array validation: {'type': 'select', 'title': 'Професійна комунікація', 'instruction': 'Оберіть слова, які доречні в ділових переговорах (6+ елементів).', 'items': [{'question': 'Яка лексика пасує для офіційних зустрічей?', 'options': [{'text': 'пропонувати', 'correct': True}, {'text': 'узгоджувати', 'correct': True}, {'text': 'базікати', 'correct': False}, {'text': 'підтверджувати', 'correct': True}, {'text': 'теревенити', 'correct': False}, {'text': 'резюмувати', 'correct': True}, {'text': 'обговорювати', 'correct': True}, {'text': 'уточнювати', 'correct': True}]}, {'question': 'Оберіть дієслова для підбиття підсумків:', 'options': [{'text': 'резюмувати', 'correct': True}, {'text': 'підсумовувати', 'correct': True}, {'text': 'базікати', 'correct': False}, {'text': 'висновувати', 'correct': True}]}, {'question': 'Які слова описують процес переконання?', 'options': [{'text': 'аргументувати', 'correct': True}, {'text': 'переконувати', 'correct': True}, {'text': 'обґрунтовувати', 'correct': True}, {'text': 'мовчати', 'correct': False}]}, {'question': 'Оберіть терміни для ділового спілкування:', 'options': [{'text': 'порядок денний', 'correct': True}, {'text': 'протокол', 'correct': True}, {'text': 'регламент', 'correct': True}, {'text': 'плітки', 'correct': False}]}, {'question': 'Які дієслова вказують на офіційне повідомлення?', 'options': [{'text': 'сповіщати', 'correct': True}, {'text': 'інформувати', 'correct': True}, {'text': 'повідомляти', 'correct': True}, {'text': 'шепотіти', 'correct': False}]}, {'question': 'Оберіть форми офіційного звернення:', 'options': [{'text': 'запит', 'correct': True}, {'text': 'заява', 'correct': True}, {'text': 'клопотання', 'correct': True}, {'text': 'балачка', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 59-synonyms-communication.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 59-synonyms-communication.yaml: [index-13] select: 'items.0.options' - [{'text': 'пропонувати', 'correct': True}, {'text': 'узгоджувати', 'correct': True}, {'text': 'базікати', 'correct': False}, {'text': 'підтверджувати', 'correct': True}, {'text': 'теревенити', 'correct': False}, {'text': 'резюмувати', 'correct': True}, {'text': 'обговорювати', 'correct': True}, {'text': 'уточнювати', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Вступ: Мистецтво висловлення думки, Частина 5: Практичний додаток — Тон та Контекст
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
- **Words:** ✅ 1809/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 58/35
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
| engagement | 10 | 4 | 100% | 25% | 25.0% |
| variety | 0.98 | - | 98% | 17% | 16.3% |
| cultural | 7 | - | 100% | 17% | 16.7% |
| visual | 8 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.82 | - | 82% | 8% | 6.8% |
| examples | 40 | - | 100% | 8% | 8.3% |
| realworld | 10 | - | 100% | 8% | 8.3% |
| questions | 8 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **98.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 70 | Included in Core |
| **Вступ: Мистецтво висловлення думки** | ⚪️ | 115 | Skipped |
| **Частина 1: Сказати — Як передати інформацію** | ✅ | 190 | Included in Core |
| **Частина 2: Питати — Як дізнатися істину** | ✅ | 144 | Included in Core |
| **Частина 3: Форми комунікації — Від монологу до переговорів** | ✅ | 205 | Included in Core |
| **Частина 4: Мовлення в українській літературі та фольклорі** | ✅ | 108 | Included in Core |
| **Частина 5: Практичний додаток — Тон та Контекст** | ✅ | 41 | Included in Core |
| **Частина 6: Комунікація в сучасному світі** | ✅ | 106 | Included in Core |
| **Частина 7: Дискусія як інструмент розвитку** | ✅ | 335 | Included in Core |
| **Частина 7: Рух у просторі культури через діалог** | ✅ | 337 | Included in Core |
| **Підсумок** | ✅ | 48 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |