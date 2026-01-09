# Audit Report: 80-active-lifestyle.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту' Q1 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту' Q3 prompt length 4 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту' Q4 prompt length 5 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту' Q5 prompt length 6 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту' Q6 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту' Q7 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту' Q8 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту' Q10 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Речення про здоров'я' item 1 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Речення про здоров'я' item 2 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Речення про здоров'я' item 3 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Речення про здоров'я' item 4 has 8 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Речення про здоров'я' item 5 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Речення про здоров'я' item 6 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Речення про здоров'я' item 7 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Речення про здоров'я' item 8 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 80-active-lifestyle.yaml: [mark-verbs] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 80 has 96.3% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## TEMPLATE COMPLIANCE
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**🔄 REWRITE** (severity 75/100)

- 19 violations (severe - consider revision)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1888/1500
- **Activities:** ❌ 11/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 30/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 17 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 96.3% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ❌ 93% < 95% min (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 93% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 6 | 5 | 100% | 33% | 33.3% |
| engagement | 7 | 6 | 100% | 20% | 20.0% |
| visual | 2 | 4 | 50% | 13% | 6.7% |
| variety | 0.98 | - | 98% | 7% | 6.5% |
| paragraph_var | 1.00 | - | 100% | 7% | 6.7% |
| examples | 15 | - | 100% | 7% | 6.7% |
| realworld | 6 | - | 100% | 7% | 6.7% |
| questions | 29 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **93.2%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Ранкова пробіжка | cloze | 11 | 14 | Add 3 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Вступ** | ⚪️ | 228 | Skipped |
| **Презентація** | ⚪️ | 983 | Skipped |
| **Практика** | ⚪️ | 37 | Skipped |
| **Продукція** | ⚪️ | 509 | Skipped |
| **Підсумок** | ✅ | 131 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |