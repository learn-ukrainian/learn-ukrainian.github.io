# Audit Report: 55-agreement-disagreement.md
**Phase:** B1.5 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про згоду та незгоду' item 1 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про згоду та незгоду' item 2 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про згоду та незгоду' item 3 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про згоду та незгоду' item 4 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про згоду та незгоду' item 5 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про згоду та незгоду' item 6 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[SECTION_ORDER]** '## Лексика' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[SECTION_ORDER]** Content section '## Діалоги' appears after end section '## Лексика'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [розуміння-згоди-та-незгоди] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [рівні-інтенсивності-згоди-та-незгоди] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [переклад-слів-згоди-та-незгоди] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [згода-чи-незгода?] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [реєстр--формальне-чи-неформальне?] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [вибір-правильного-слова-для-згоди-або-незгоди] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [вибір-усіх-слів-для-вираження-згоди] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [правила-використання-згоди-та-незгоди] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [заповніть-діалог-про-робочий-проєкт] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [складіть-речення-про-згоду-та-незгоду] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [виправте-помилки-у-виразах-згоди-та-незгоди] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [переклад-виразів-згоди-та-незгоди] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-agreement-disagreement.yaml: [знайдіть-слова-згоди-та-незгоди-в-тексті] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Практика' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 23 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1693/1500
- **Activities:** ✅ 13/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 13/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 18 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 21 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.6% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ✅ 99% (vocabulary)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 30 | 20 | 100% | 25% | 25.0% |
| usage_examples | 37 | 15 | 100% | 20% | 20.0% |
| engagement | 13 | 4 | 100% | 15% | 15.0% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| visual | 8 | 3 | 100% | 10% | 10.0% |
| register_notes | 15 | 5 | 100% | 10% | 10.0% |
| variety | 0.97 | - | 97% | 5% | 4.9% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 48 | Included in Core |
| **Вступ** | ⚪️ | 109 | Skipped |
| **Лексика** | ⚪️ | 442 | Skipped |
| **Використання** | ⚪️ | 279 | Skipped |
| **Читання** | ✅ | 301 | Included in Core |
| **Діалоги** | ✅ | 237 | Included in Core |
| **Підсумок** | ✅ | 167 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |