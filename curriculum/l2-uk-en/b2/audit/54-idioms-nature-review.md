# Audit Report: 54-idioms-nature.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## LINT ERRORS
- ❌ Line 11: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 13: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 134: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 136: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 164: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 186: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 206: Use Ukrainian angular quotes («...») instead of ASCII quotes (").

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть пояснення' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Стихії в житті' Q3 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Стихії в житті' Q5 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Стихії в житті' Q6 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Стихії в житті' Q7 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Стихії в житті' Q8 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** group-sort 'Стихії та Значення' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Зберіть речення' item 1 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Зберіть речення' item 2 has 7 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Зберіть речення' item 3 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Зберіть речення' item 4 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Зберіть речення' item 5 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Зберіть речення' item 6 has 7 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Зберіть речення' item 7 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Зберіть речення' item 8 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY]** match-up 'Синоніми та образи' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Природні асоціації' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Традиції та мова' Q1 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Традиції та мова' Q2 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Традиції та мова' Q3 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Традиції та мова' Q4 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Традиції та мова' Q5 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Традиції та мова' Q6 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Традиції та мова' Q7 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Традиції та мова' Q8 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 54-idioms-nature.yaml: [знайдіть-аналог] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 54-idioms-nature.yaml: [традиції-та-мова] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (18 words): дивитися, чистий, нога, вогонь, випробування...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 70/100)

- Revision recommended (severity 70/100)
- 29 violations (severe - consider revision)
- 7 format errors (many)

## Gates
- **Words:** ✅ 1807/1750
- **Activities:** ✅ 13/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 101/35
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 7 Format Errors
- **Pedagogy:** ❌ 28 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.8% (target 98-100% (vocab))
- **Richness:** ✅ 99% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 45 | 15 | 100% | 25% | 25.0% |
| engagement | 9 | 5 | 100% | 19% | 18.7% |
| variety | 0.99 | - | 99% | 12% | 12.4% |
| cultural | 8 | 4 | 100% | 12% | 12.5% |
| realworld | 6 | 3 | 100% | 12% | 12.5% |
| visual | 4 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.97 | - | 97% | 6% | 6.1% |
| questions | 8 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **99.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 82 | Included in Core |
| **Вступ: Життя в обіймах стихій** | ⚪️ | 248 | Skipped |
| **Частина 1: Вода — Дзеркало правди та зайвих слів** | ✅ | 261 | Included in Core |
| **Частина 2: Вогонь — Ризик та вище загартування** | ✅ | 253 | Included in Core |
| **Частина 3: Земля та Вітер — Пошук опори та Легковажність** | ✅ | 154 | Included in Core |
| **Культурний код: Стихії в українському світогляді** | ✅ | 366 | Included in Core |
| **Природа та стихії в українському фольклорі** | ⚪️ | 109 | Skipped |
| **Практичний додаток: Стилістичні нюанси** | ⚪️ | 107 | Skipped |
| **Стихії та емоційний інтелект** | ⚪️ | 158 | Skipped |
| **Підсумок** | ✅ | 69 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |