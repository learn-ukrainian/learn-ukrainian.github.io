# Audit Report: 52-idioms-animals-i.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## LINT ERRORS
- ❌ Line 9: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 13: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 51: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 59: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 129: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 131: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 160: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 164: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 173: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 174: Use Ukrainian angular quotes («...») instead of ASCII quotes (").

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть відповідність' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Вибір фразеологізму' Q1 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Вибір фразеологізму' Q3 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Вибір фразеологізму' Q5 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Вибір фразеологізму' Q6 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Вибір фразеологізму' Q7 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Вибір фразеологізму' Q8 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** group-sort 'Класифікація ідіом' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 1 has 7 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 2 has 7 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 3 has 7 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 4 has 7 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 5 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 6 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 7 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть речення' item 8 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY]** match-up 'Контекст вживання (Регістри)' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Тварини та якості' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q1 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q2 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q3 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q4 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q5 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q6 prompt length 8 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q7 prompt length 8 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст' Q8 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 52-idioms-animals-i.yaml: [переклад-значень] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 52-idioms-animals-i.yaml: [культурний-контекст] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (13 words): небезпека, темний, поведінка, смерть, сила...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 70/100)

- Revision recommended (severity 70/100)
- 30 violations (severe - consider revision)
- 10 format errors (many)

## Gates
- **Words:** ⚠️ 1706/1750 (44 short)
- **Activities:** ✅ 13/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 107/35
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 10 Format Errors
- **Pedagogy:** ❌ 29 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.4% (target 98-100% (vocab))
- **Richness:** ✅ 97% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 33 | 15 | 100% | 25% | 25.0% |
| engagement | 8 | 5 | 100% | 19% | 18.7% |
| variety | 0.99 | - | 99% | 12% | 12.4% |
| cultural | 5 | 4 | 100% | 12% | 12.5% |
| realworld | 6 | 3 | 100% | 12% | 12.5% |
| visual | 3 | 4 | 75% | 6% | 4.7% |
| paragraph_var | 0.89 | - | 89% | 6% | 5.6% |
| questions | 10 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 75 | Included in Core |
| **Вступ: Тварини як символи нашої ідентичності** | ⚪️ | 190 | Skipped |
| **Частина 1: Вовк — Символ дикості та раптовості** | ✅ | 181 | Included in Core |
| **Частина 2: Собака — Експертність та сувора доля** | ✅ | 162 | Included in Core |
| **Частина 3: Кінь — Робота та таємниці** | ✅ | 291 | Included in Core |
| **Культурний код: Тварини в українському житті** | ✅ | 453 | Included in Core |
| **Тварини в українській літературі та класиці** | ⚪️ | 150 | Skipped |
| **Практичний додаток: Регістри та нюанси** | ⚪️ | 133 | Skipped |
| **Підсумок** | ✅ | 71 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |