# Audit Report: 85-ukrainian-cuisine.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## LINT ERRORS
- ❌ Line 37: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 100: Use Ukrainian angular quotes («...») instead of ASCII quotes (").

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння української кухні' Q4 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння української кухні' Q5 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння української кухні' Q7 prompt length 8 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння української кухні' Q8 prompt length 8 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння української кухні' Q9 prompt length 9 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українську кухню' item 1 has 4 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українську кухню' item 2 has 4 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українську кухню' item 3 has 6 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українську кухню' item 4 has 4 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українську кухню' item 5 has 3 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українську кухню' item 6 has 4 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українську кухню' item 7 has 5 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українську кухню' item 8 has 5 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 85-ukrainian-cuisine.yaml: [складіть-речення-про-українську-кухню] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 85-ukrainian-cuisine.yaml: [знайдіть-кулінарну-лексику] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (21 words): пекти, крашанки, тост, сало, рецепт...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 62/100)

- Revision recommended (severity 62/100)
- 16 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1694/1500
- **Activities:** ✅ 12/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 75/25
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 2 Format Errors
- **Pedagogy:** ❌ 15 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.6% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 98% (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 11 | 5 | 100% | 33% | 33.3% |
| engagement | 8 | 6 | 100% | 20% | 20.0% |
| visual | 4 | 4 | 100% | 13% | 13.3% |
| variety | 0.98 | - | 98% | 7% | 6.5% |
| paragraph_var | 0.83 | - | 83% | 7% | 5.5% |
| examples | 21 | - | 100% | 7% | 6.7% |
| realworld | 6 | - | 100% | 7% | 6.7% |
| questions | 36 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **98.7%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Кулінарна лексика в контексті | cloze | 12 | 14 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 50 | Included in Core |
| **Вступ** | ⚪️ | 134 | Skipped |
| **Презентація** | ⚪️ | 733 | Skipped |
| **Практика** | ⚪️ | 311 | Skipped |
| **Продукція** | ⚪️ | 323 | Skipped |
| **Підсумок** | ✅ | 143 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |