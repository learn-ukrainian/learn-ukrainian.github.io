# Audit Report: 56-synonyms-size.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть відповідність' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Регістри та розміри' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Параметри та об'єкти' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q1 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q2 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q3 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q4 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q5 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q6 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q7 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q8 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-synonyms-size.yaml: Array validation: {'type': 'translate', 'title': 'Перекладіть масштаб', 'instruction': 'Оберіть правильний український синонім до англійського слова.', 'items': [{'source': 'enormous', 'options': [{'text': 'величезний', 'correct': True}, {'text': 'мізерний', 'correct': False}, {'text': 'дрібний', 'correct': False}, {'text': 'короткий', 'correct': False}], 'explanation': 'Найкращий відповідник для enormous.'}, {'source': 'tiny', 'options': [{'text': 'крихітний', 'correct': True}, {'text': 'здоровенний', 'correct': False}, {'text': 'грандіозний', 'correct': False}, {'text': 'широкий', 'correct': False}], 'explanation': 'Найкращий відповідник для tiny.'}, {'source': 'insignificant', 'options': [{'text': 'незначний', 'correct': True}, {'text': 'колосальний', 'correct': False}, {'text': 'глибокий', 'correct': False}, {'text': 'масивний', 'correct': False}], 'explanation': 'Найкращий відповідник для insignificant.'}, {'source': 'boundless', 'options': [{'text': 'неозорий', 'correct': True}, {'text': 'вузький', 'correct': False}, {'text': 'тісний', 'correct': False}, {'text': 'мілкий'}], 'explanation': 'Найкращий відповідник для boundless.'}, {'source': 'bulky', 'options': [{'text': 'масивний', 'correct': True}, {'text': 'tonкий', 'correct': False}, {'text': 'дрібний', 'correct': False}, {'text': 'короткий'}], 'explanation': 'Найкращий відповідник для bulky.'}, {'source': 'shallow', 'options': [{'text': 'мілкий', 'correct': True}, {'text': 'глибокий', 'correct': False}, {'text': 'високий', 'correct': False}, {'text': 'широкий'}], 'explanation': 'Найкращий відповідник для shallow.'}, {'source': 'colossal', 'options': [{'text': 'колосальний', 'correct': True}, {'text': 'мізерний', 'correct': False}, {'text': 'крихітний', 'correct': False}, {'text': 'низький'}], 'explanation': 'Пряме запозичення з аналогічним значенням.'}, {'source': 'negligible', 'options': [{'text': 'мізерний', 'correct': True}, {'text': 'велетенський', 'correct': False}, {'text': 'грандіозний', 'correct': False}, {'text': 'товстий'}], 'explanation': 'Найкращий відповідник для negligible.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-synonyms-size.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
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
- 16 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1897/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 112/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 14 violations
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
| engagement | 7 | 4 | 100% | 25% | 25.0% |
| variety | 0.98 | - | 98% | 17% | 16.3% |
| cultural | 5 | - | 100% | 17% | 16.7% |
| visual | 4 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 1.00 | - | 100% | 8% | 8.3% |
| examples | 42 | - | 100% | 8% | 8.3% |
| realworld | 8 | - | 100% | 8% | 8.3% |
| questions | 7 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **99.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 64 | Included in Core |
| **Вступ: Велич і мізерність навколо нас** | ⚪️ | 118 | Skipped |
| **Частина 1: Від великого до колосального — Архітектура та простір** | ✅ | 376 | Included in Core |
| **Частина 2: Світ у краплині води — Увага до деталей** | ✅ | 378 | Included in Core |
| **Частина 3: Параметри, виміри та їхня роль у науці** | ✅ | 263 | Included in Core |
| **Частина 4: Мистецтво порівняння та гіперболи в літературі** | ✅ | 137 | Included in Core |
| **Частина 5: Практичний додаток — Регістр має значення** | ✅ | 165 | Included in Core |
| **Частина 6: Індустріальний масштаб та урбаністика** | ✅ | 226 | Included in Core |
| **Підсумок** | ✅ | 60 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |