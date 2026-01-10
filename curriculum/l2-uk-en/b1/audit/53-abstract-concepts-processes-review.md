# Audit Report: 53-abstract-concepts-processes.md
**Phase:** B1.5 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики процесів' Q2 prompt length 6 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики процесів' Q4 prompt length 4 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики процесів' Q5 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики процесів' Q6 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики процесів' Q7 prompt length 5 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики процесів' Q8 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 1 has 4 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 2 has 4 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 3 has 4 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 4 has 4 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 5 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 6 has 4 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 7 has 3 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 8 has 4 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[SECTION_ORDER]** '## Лексика' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[SECTION_ORDER]** Content section '## Діалоги' appears after end section '## Лексика'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [розуміння-лексики-процесів] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [колокації--дієслово-+-іменник] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [антоніми] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [групування-за-типом-тренду] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [вибір-слова-з-контексту] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [правильні-колокації] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [правила-використання] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [заповніть-пропуски-в-тексті] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [складіть-речення] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [виправте-помилки-в-колокаціях] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [переклад-речень] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-abstract-concepts-processes.yaml: [знайдіть-слова-процесів-та-змін] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка|Тест' found: Вступ, Українські контексти
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Практика' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 31 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1699/1500
- **Activities:** ✅ 12/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 13/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 12 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 28 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.5% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ✅ 96% (vocabulary)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 30 | 20 | 100% | 25% | 25.0% |
| usage_examples | 17 | 15 | 100% | 20% | 20.0% |
| engagement | 13 | 4 | 100% | 15% | 15.0% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| visual | 8 | 3 | 100% | 10% | 10.0% |
| register_notes | 13 | 5 | 100% | 10% | 10.0% |
| variety | 0.96 | - | 96% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 52 | Included in Core |
| **Вступ** | ⚪️ | 91 | Skipped |
| **Лексика** | ⚪️ | 404 | Skipped |
| **Використання** | ⚪️ | 218 | Skipped |
| **Читання** | ✅ | 372 | Included in Core |
| **Діалоги** | ✅ | 252 | Included in Core |
| **Підсумок** | ✅ | 200 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |