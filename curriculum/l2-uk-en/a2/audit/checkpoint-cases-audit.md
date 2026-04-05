# Audit Report: M39 — checkpoint-cases.md
**Level:** A2 | **Module:** M39 | **Phase:** A2.5 | **Pedagogy:** Review | **Target:** 1500
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:04:44

## Configuration
**Type:** A2
**Word Target:** 1500 words
**Activities:** 0-4 required
**Items per Activity:** ≥8 items
**Unique Types:** ≥0 types required
**Priority Types:** cloze, error-correction, fill-in, group-sort, mark-the-words, match-up, observe, odd-one-out, order, quiz, reading, select, translate, true-false, unjumble
**Engagement:** ≥3 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | group-sort |  | 8 | 8 | ✅ |
| 2 | quiz |  | 8 | 8 | ✅ |
| 3 | error-correction |  | 6 | 6 | ✅ |
| 4 | fill-in |  | 8 | 8 | ✅ |
| 5 | match-up |  | 6 | 8 | ❌ |
| 6 | group-sort |  | 9 | 8 | ✅ |
| 7 | true-false |  | 6 | 8 | ❌ |
| 8 | quiz |  | 6 | 8 | ❌ |

**Summary:**
- Total activities: 8 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 6/15 (error-correction, fill-in, group-sort, match-up, quiz, true-false) ✅
- Low density activities: 3

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** group-sort '' has 7 groups (target: 2-4)
  - FIX: Adjust number of sorting categories to 2-4.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q1 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q2 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q3 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q4 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q6 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q7 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q8 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY]** match-up '' has 6 pairs (target: 8-14)
  - FIX: Adjust number of pairs to 8-14.
- **[COMPLEXITY]** true-false '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 true-false requires at least 8 items.
- **[COMPLEXITY]** quiz '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 quiz requires at least 8 items.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q2 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q3 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q4 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q5 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q6 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[METALANGUAGE]** Metalanguage terms used but not in vocabulary: однина, множина
  - FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'the phrase...'.
  - FIX: Vary sentence structure.
- **[YAML_SCHEMA_VIOLATION]** Schema error in checkpoint-cases.yaml: Schema validation error at key '8': {'id': 'unjumble-sentences', 'type': 'unjumble', 'instruction': 'Складіть правильне речення зі слів', 'items': [{'words': ['у', 'немає', 'братів.', 'мене'], 'correct_order': ['У', 'мене', 'немає', 'братів.']}, {'words': ["п'ю", 'з', 'каву', 'Я', 'молоком.'], 'correct_order': ['Я', "п'ю", 'каву', 'з', 'молоком.']}, {'words': ['допомагаю', 'завжди', 'Я', 'мамі.'], 'correct_order': ['Я', 'завжди', 'допомагаю', 'мамі.']}, {'words': ['багато', 'У', 'вікон.', 'кімнаті'], 'correct_order': ['У', 'кімнаті', 'багато', 'вікон.']}, {'words': ['цікавимося', 'історією.', 'Ми'], 'correct_order': ['Ми', 'цікавимося', 'історією.']}, {'words': ['бачу', 'студентів.', 'нових', 'Я'], 'correct_order': ['Я', 'бачу', 'нових', 'студентів.']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**🔄 REWRITE** (severity 100/100)

- 19 violations (severe - consider revision)
- Immersion 31% off target (major rebalancing needed)
- Activity density below minimum

## Gates
- **Words:** ✅ 1999/1500 (raw: 2044)
- **Activities:** ✅ 8/0
- **Density:** ❌ 3 < 8
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 1/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 54/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ❌ 18.6% LOW (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
|  | match-up | 6 | 8 | Add 2 more items |
|  | true-false | 6 | 8 | Add 2 more items |
|  | quiz | 6 | 8 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 611 | Included in Core |
| **Частина 2: Який відмінок? (Part 2: Which Case?)** | ✅ | 610 | Included in Core |
| **Частина 3: Вільне мовлення (Part 3: Free Production)** | ➖ | 626 | Excluded Type |
| **Підсумок** | ✅ | 152 | Included in Core |