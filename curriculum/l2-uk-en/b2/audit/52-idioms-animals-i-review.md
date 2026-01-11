# Audit Report: 52-idioms-animals-i.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть відповідність' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Вибір фразеологізму' Q7 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Класифікація ідіом' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 1 has 7 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 2 has 7 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 3 has 7 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 4 has 7 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 5 has 6 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 6 has 6 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 7 has 6 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 8 has 6 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY]** match-up 'Контекст вживання (Регістри)' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Тварини та якості' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q1 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q2 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q3 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q4 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q6 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q7 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q8 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 52-idioms-animals-i.yaml: Array validation: {'type': 'translate', 'title': 'Переклад значень', 'instruction': 'Знайдіть правильний український фразеологізм для англійського виразу.', 'items': [{'source': 'Speak of the devil', 'options': [{'text': 'Про вовка промовка', 'correct': True}, {'text': 'Вовком вити', 'correct': False}, {'text': "Собаку з'їв", 'correct': False}, {'text': 'Кінь не валявся'}], 'explanation': 'Це прямий аналог за ситуацією вживання.'}, {'source': 'To know inside out / To be an old hand', 'options': [{'text': "Собаку з'їсти", 'correct': True}, {'text': 'Працювати як кінь', 'correct': False}, {'text': 'Темна конячка', 'correct': False}, {'text': 'Троянський кінь'}], 'explanation': 'Вказує на великий досвід та майстерність.'}, {'source': "Work hasn't even started", 'options': [{'text': 'Кінь не валявся', 'correct': True}, {'text': 'Про вовка промовка', 'correct': False}, {'text': 'Собача смерть', 'correct': False}, {'text': 'Вовком вити'}], 'explanation': 'Означає повну відсутність прогресу у справі.'}, {'source': 'To work like a dog/horse', 'options': [{'text': 'Працювати як кінь', 'correct': True}, {'text': 'Вовком вити', 'correct': False}, {'text': "Собаку з'їсти", 'correct': False}, {'text': 'Темна конячка'}], 'explanation': 'Про дуже важку фізичну або розумову працю.'}, {'source': 'Dark horse', 'options': [{'text': 'Темна конячка', 'correct': True}, {'text': 'Троянський кінь', 'correct': False}, {'text': 'Кінь не валявся', 'correct': False}, {'text': 'Чорний вовк'}], 'explanation': 'Дослівний та смисловий переклад.'}, {'source': 'Trojan horse', 'options': [{'text': 'Троянський кінь', 'correct': True}, {'text': 'Грецький кінь', 'correct': False}, {'text': 'Підступний пес', 'correct': False}, {'text': 'Собача смерть'}], 'explanation': 'Вираз походить з античної міфології.'}, {'source': 'In utter despair', 'options': [{'text': 'Вовком вити', 'correct': True}, {'text': "Собаку з'їсти", 'correct': False}, {'text': 'Кінь не валявся', 'correct': False}, {'text': 'Про вовка промовка'}], 'explanation': 'Передає стан крайнього горя.'}, {'source': 'To get what one deserves (negative)', 'options': [{'text': 'Собаці собача смерть', 'correct': True}, {'text': 'Працювати як кінь', 'correct': False}, {'text': "Собаку з'їсти", 'correct': False}, {'text': 'Кінь не валявся'}], 'explanation': 'Вказує на справедливу, але жорстоку відплату.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 52-idioms-animals-i.yaml: [index-9] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вживання у контексті' per template 'b2-phraseology-module-template'
  - FIX: Add '## Вживання у контексті' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 24 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1816/1750
- **Activities:** ✅ 13/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 107/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 23 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.7% (target 90-100% (vocab))
- **Richness:** ✅ 98% (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 9 | 4 | 100% | 25% | 25.0% |
| variety | 0.99 | - | 99% | 17% | 16.5% |
| cultural | 5 | - | 100% | 17% | 16.7% |
| visual | 3 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.87 | - | 87% | 8% | 7.3% |
| examples | 34 | - | 100% | 8% | 8.3% |
| realworld | 6 | - | 100% | 8% | 8.3% |
| questions | 10 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **98.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 75 | Included in Core |
| **Вступ: Тварини як символи нашої ідентичності** | ⚪️ | 190 | Skipped |
| **Частина 1: Вовк — Символ дикості та раптовості** | ✅ | 181 | Included in Core |
| **Частина 2: Собака — Експертність та сувора доля** | ✅ | 162 | Included in Core |
| **Частина 3: Кінь — Робота та таємниці** | ✅ | 291 | Included in Core |
| **Культурний код: Тварини в українському житті** | ✅ | 453 | Included in Core |
| **Тварини в українській літературі та класиці** | ⚪️ | 150 | Skipped |
| **Практичний додаток: Регістри та нюанси** | ⚪️ | 133 | Skipped |
| **Підсумок** | ✅ | 71 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |