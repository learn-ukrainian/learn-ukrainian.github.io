# Audit Report: 77-ukrainian-cinema-and-tv.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** cultural | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українське кіно' item 3 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українське кіно' item 6 has 8 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українське кіно' item 7 has 8 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українське кіно' item 8 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [знайдіть-слова,-пов'язані-з-кіно] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [складіть-речення-про-українське-кіно] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 55/100)

- Revision recommended (severity 55/100)
- 7 violations (significant)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1592/1500
- **Activities:** ❌ 11/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 50/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 6 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.8% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ❌ 94% < 95% min (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 94% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 5 | 5 | 100% | 33% | 33.3% |
| engagement | 8 | 6 | 100% | 20% | 20.0% |
| visual | 3 | 4 | 75% | 13% | 10.0% |
| variety | 0.97 | - | 97% | 7% | 6.5% |
| paragraph_var | 0.74 | - | 74% | 7% | 4.9% |
| examples | 22 | - | 100% | 7% | 6.7% |
| realworld | 3 | - | 100% | 7% | 6.7% |
| questions | 32 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **94.7%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Заповніть пропуски кінолексикою | cloze | 12 | 14 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 131 | Included in Core |
| **Презентація** | ⚪️ | 819 | Skipped |
| **Практика** | ⚪️ | 485 | Skipped |
| **Підсумок** | ✅ | 157 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |