# Audit Report: 73-regions-east.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 1 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 2 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 3 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 4 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 5 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 6 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 7 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 8 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 73-regions-east.yaml: [складіть-речення] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 73-regions-east.yaml: [знайдіть-слова,-пов'язані-з-промисловістю] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 11 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1773/1500
- **Activities:** ✅ 12/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 47/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 10 violations
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
| cultural | 8 | 5 | 100% | 33% | 33.3% |
| engagement | 13 | 6 | 100% | 20% | 20.0% |
| visual | 4 | 4 | 100% | 13% | 13.3% |
| variety | 0.97 | - | 97% | 7% | 6.5% |
| paragraph_var | 0.79 | - | 79% | 7% | 5.3% |
| examples | 21 | - | 100% | 7% | 6.7% |
| realworld | 3 | - | 100% | 7% | 6.7% |
| questions | 37 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **98.4%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Заповніть пропуски | cloze | 12 | 14 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 67 | Included in Core |
| **Вступ** | ⚪️ | 127 | Skipped |
| **Презентація** | ⚪️ | 857 | Skipped |
| **Практика** | ⚪️ | 188 | Skipped |
| **Продукція** | ⚪️ | 362 | Skipped |
| **Підсумок** | ✅ | 0 | Included in Core |
| **Що ви дізналися** | ⚪️ | 172 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |