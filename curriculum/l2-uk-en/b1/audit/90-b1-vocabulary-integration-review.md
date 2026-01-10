# Audit Report: 90-b1-vocabulary-integration.md
**Phase:** B1.8 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 2 has 6 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 4 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 5 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 6 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 7 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 8 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 9 has 6 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 11 has 6 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [комплексний-огляд-лексики-b1] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [колокації--дієслово-+-іменник] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [синоніми-та-антоніми] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [групування-за-доменом] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [вибір-правильного-слова-з-контексту] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [виберіть-всі-правильні-варіанти] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [правила-використання-лексики-b1] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [заповніть-пропуски-в-тексті-про-україну] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [складіть-речення-з-лексикою-b1] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [виправте-помилки-в-лексиці-та-колокаціях] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [переклад-речень-з-усіх-доменів] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [знайдіть-дискурсні-маркери-в-тексті] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [знайдіть-абстрактні-іменники-в-тексті] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 90 has 97.6% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 23 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2097/1500
- **Activities:** ✅ 13/10
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/4
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 18/15
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 21 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 97.6% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 96% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 21 | 24 | 88% | 20% | 17.6% |
| engagement | 11 | 5 | 100% | 15% | 15.0% |
| dialogues | 6 | 4 | 100% | 15% | 15.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 12 | 3 | 100% | 10% | 10.0% |
| realworld | 7 | 3 | 100% | 10% | 10.0% |
| visual | 9 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.92 | - | 92% | 5% | 4.6% |
| questions | 19 | 5 | 100% | 5% | 5.0% |
| proverbs | 1 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **97.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 49 | Included in Core |
| **Діагностика** | ✅ | 148 | Included in Core |
| **Аналіз** | ✅ | 1072 | Included in Core |
| **Поглиблення** | ⚪️ | 305 | Skipped |
| **Практика** | ⚪️ | 289 | Skipped |
| **Підсумок** | ✅ | 124 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |