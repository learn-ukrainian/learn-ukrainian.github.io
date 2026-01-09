# Audit Report: 90-b1-vocabulary-integration.md
**Phase:** B1.8 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q1 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q2 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q3 prompt length 10 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q4 prompt length 10 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q5 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q6 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q7 prompt length 10 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q8 prompt length 10 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q9 prompt length 10 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q11 prompt length 10 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q12 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q13 prompt length 9 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Комплексний огляд лексики B1' Q14 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 1 has 9 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 2 has 6 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 3 has 8 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 4 has 7 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 5 has 7 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 6 has 7 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 7 has 7 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 8 has 7 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 9 has 6 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 10 has 9 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 11 has 6 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з лексикою B1' item 12 has 9 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [складіть-речення-з-лексикою-b1] unjumble: 'items.11' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [знайдіть-дискурсні-маркери-в-тексті] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 90-b1-vocabulary-integration.yaml: [знайдіть-абстрактні-іменники-в-тексті] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Presentation|Grammar|Focus|Презентація|Граматика|Теорія|Пояснення' per template 'b1-grammar-module-template'
  - FIX: Add '## Presentation' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 30 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1987/1000
- **Activities:** ✅ 13/10
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/4
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 18/15
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 28 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.1% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 96% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 20 | 24 | 83% | 20% | 16.6% |
| engagement | 10 | 5 | 100% | 15% | 15.0% |
| dialogues | 6 | 4 | 100% | 15% | 15.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 12 | 3 | 100% | 10% | 10.0% |
| realworld | 7 | 3 | 100% | 10% | 10.0% |
| visual | 9 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.94 | - | 94% | 5% | 4.7% |
| questions | 19 | 5 | 100% | 5% | 5.0% |
| proverbs | 1 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 49 | Included in Core |
| **Діагностика** | ✅ | 148 | Included in Core |
| **Аналіз** | ✅ | 1072 | Included in Core |
| **Поглиблення** | ⚪️ | 305 | Skipped |
| **Практика** | ⚪️ | 289 | Skipped |
| **Підсумок** | ✅ | 124 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |