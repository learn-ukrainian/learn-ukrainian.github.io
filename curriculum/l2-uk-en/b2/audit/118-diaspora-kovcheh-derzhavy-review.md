# Audit Report: 118-diaspora-kovcheh-derzhavy.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q1 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q2 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q3 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q4 prompt length 3 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q5 prompt length 5 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q6 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q7 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q8 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Поєднайте терміни з їхніми визначеннями.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Доберіть синоніми до слів.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про діаспору.' item 3 has 6 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про діаспору.' item 5 has 6 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої загальні знання про діаспору.' Q2 prompt length 5 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої загальні знання про діаспору.' Q4 prompt length 4 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої загальні знання про діаспору.' Q5 prompt length 3 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої загальні знання про діаспору.' Q6 prompt length 3 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої загальні знання про діаспору.' Q7 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої загальні знання про діаспору.' Q8 prompt length 4 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 118-diaspora-kovcheh-derzhavy.yaml: Array validation: {'type': 'select', 'items': [{'correct': True, 'question': 'Метафора «ковчег» для позначення рятівної місії.'}, {'correct': True, 'question': 'Урочиста лексика (клейноди, святиня, місія).'}, {'correct': False, 'question': 'Використання жаргонізмів та сленгу.'}, {'correct': True, 'question': 'Історичні терміни (Директорія, УНР, екзил).'}, {'correct': True, 'question': 'Емоційно забарвлені слова (плакали, надія, гідність).'}, {'correct': False, 'question': 'Науковий стиль без емоцій.'}], 'title': 'Які мовні засоби використовуються в тексті для опису ролі діаспори?', 'instruction': 'Оберіть усі правильні відповіді.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 118-diaspora-kovcheh-derzhavy.yaml: [index-6] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 118-diaspora-kovcheh-derzhavy.yaml: [index-7] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 118-diaspora-kovcheh-derzhavy.yaml: [index-11] translate: 'items.7.options' - [{'text': 'Independence', 'correct': True}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 118-diaspora-kovcheh-derzhavy.yaml: [index-12] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 26 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2054/2000
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 20/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 25 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 3 | 100% | 24% | 23.8% |
| engagement | 20 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 19 | 4 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 0.99 | - | 99% | 5% | 4.7% |
| questions | 5 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 90 | Included in Core |
| **Вступ** | ⚪️ | 178 | Skipped |
| **Уряд УНР в екзилі** | ⚪️ | 253 | Skipped |
| **Діаспорні інституції** | ⚪️ | 833 | Skipped |
| **Передача клейнодів** | ⚪️ | 198 | Skipped |
| **Первинні джерела** | ⚪️ | 183 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 154 | Skipped |
| **Підсумок** | ✅ | 55 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |