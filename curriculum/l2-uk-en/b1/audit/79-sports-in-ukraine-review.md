# Audit Report: 79-sports-in-ukraine.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Речення про спорт' item 1 has 8 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Речення про спорт' item 2 has 8 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Речення про спорт' item 8 has 8 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 79-sports-in-ukraine.yaml: [речення-про-спорт] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 79-sports-in-ukraine.yaml: [знайдіть-спортивні-терміни] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 6 violations (moderate)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1641/1500
- **Activities:** ❌ 11/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 69/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 5 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.6% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 99% (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 7 | 5 | 100% | 33% | 33.3% |
| engagement | 7 | 6 | 100% | 20% | 20.0% |
| visual | 7 | 4 | 100% | 13% | 13.3% |
| variety | 0.98 | - | 98% | 7% | 6.5% |
| paragraph_var | 1.00 | - | 100% | 7% | 6.7% |
| examples | 37 | - | 100% | 7% | 6.7% |
| realworld | 1 | - | 100% | 7% | 6.7% |
| questions | 21 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **99.9%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Спортивна лексика | cloze | 12 | 14 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 110 | Included in Core |
| **Презентація** | ⚪️ | 843 | Skipped |
| **Практика** | ⚪️ | 123 | Skipped |
| **Продукція** | ⚪️ | 354 | Skipped |
| **Підсумок** | ✅ | 211 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |