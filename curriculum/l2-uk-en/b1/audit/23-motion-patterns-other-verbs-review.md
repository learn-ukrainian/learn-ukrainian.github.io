# Audit Report: 23-motion-patterns-other-verbs.md
**Phase:** B1.2 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка префіксів' Q2 prompt length 10 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка префіксів' Q3 prompt length 10 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка префіксів' Q4 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка префіксів' Q6 prompt length 7 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка префіксів' Q7 prompt length 9 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Логіка префіксів' Q8 prompt length 10 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY]** mark-the-words 'Знайдіть префіксальні дієслова' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Знайдіть префіксальні дієслова' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 23-motion-patterns-other-verbs.yaml: [find-prefixed-verbs] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 23 has 97.5% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## TEMPLATE COMPLIANCE
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**🔄 REWRITE** (severity 75/100)

- 11 violations (severe - consider revision)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1574/1500
- **Activities:** ❌ 11/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 44/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 9 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 97.5% (target 85-100% (B1.3-4 Complex))
- **Richness:** ❌ 94% < 95% min (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 94% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 42 | 24 | 100% | 20% | 20.0% |
| engagement | 7 | 5 | 100% | 15% | 15.0% |
| dialogues | 8 | 4 | 100% | 15% | 15.0% |
| variety | 1.00 | - | 100% | 10% | 10.0% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 6 | 3 | 100% | 10% | 10.0% |
| visual | 2 | 3 | 67% | 5% | 3.4% |
| paragraph_var | 0.91 | - | 91% | 5% | 4.6% |
| questions | 14 | 5 | 100% | 5% | 5.0% |
| proverbs | 4 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **94.6%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Знайдіть префіксальні дієслова | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 64 | Included in Core |
| **Тест** | ⚪️ | 85 | Skipped |
| **Пояснення** | ⚪️ | 889 | Skipped |
| **Практика** | ⚪️ | 124 | Skipped |
| **Діалоги** | ✅ | 222 | Included in Core |
| **Підсумок** | ✅ | 190 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |