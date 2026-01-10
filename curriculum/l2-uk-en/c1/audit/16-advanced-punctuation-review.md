# Audit Report: 16-advanced-punctuation.md
**Phase:** C1.1 | **Level:** C1 | **Pedagogy:** immersion | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Теорія знаків' Q1 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Теорія знаків' Q2 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Теорія знаків' Q6 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Теорія знаків' Q8 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Вибір знака: Складний список' Q1 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Вибір знака: Складний список' Q2 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Вибір знака: Складний список' Q4 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Вибір знака: Складний список' Q7 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [теорія-знаків] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [тире-чи-дефіс?] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [кома:-бути-чи-не-бути?] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [класифікація-знаків] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [виправлення-помилок] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [складання-переліку] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [синтаксичний-пазл] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [кома-у-складному-реченні] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [пунктуаційна-синонімія] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [переклад-термінів] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [апостроф-чи-ні?] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [пунктуаційна-культура] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [складання-речення:-лапки] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [вибір-знака:-складний-список] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [синтаксична-синонімія] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 16-advanced-punctuation.yaml: [письмове-завдання:-редагування-пунктуації] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 24 violations (severe - consider revision)

## Gates
- **Words:** ❌ 1866/2000
- **Activities:** ✅ 16/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 9/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 23 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 24 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.7% (target 98-100% (grammar))
- **Richness:** ✅ 96% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 26 | 24 | 100% | 20% | 20.0% |
| engagement | 12 | 5 | 100% | 15% | 15.0% |
| dialogues | 3 | 4 | 75% | 15% | 11.2% |
| variety | 0.99 | - | 99% | 10% | 9.9% |
| cultural | 8 | 3 | 100% | 10% | 10.0% |
| realworld | 5 | 3 | 100% | 10% | 10.0% |
| visual | 7 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 8 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 125 | Included in Core |
| **Вступ** | ⚪️ | 194 | Skipped |
| **Аналіз: Кома у складних конструкціях** | ✅ | 211 | Included in Core |
| **Розділ 2: Тире — знак інтелектуального акценту** | ⚪️ | 165 | Skipped |
| **Розділ 3: Двокрапка та Крапка з комою в переліках** | ⚪️ | 173 | Skipped |
| **Розділ 4: Лапки та цитування** | ⚪️ | 120 | Skipped |
| **Розділ 5: Пунктуація та однозначність** | ⚪️ | 136 | Skipped |
| **Розділ 6: Ситуативний діалог про редагування** | ✅ | 166 | Included in Core |
| **Розділ 7: Пунктуаційна культура в цифрову добу** | ✅ | 156 | Included in Core |
| **Розділ 8: Етика розділових знаків та цитування** | ⚪️ | 107 | Skipped |
| **Розділ 9: Пунктуація у математичних та статистичних виразах** | ⚪️ | 104 | Skipped |
| **Розділ 10: Історія українських розділових знаків** | ⚪️ | 129 | Skipped |
| **Підсумок** | ✅ | 67 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 13 | Skipped |