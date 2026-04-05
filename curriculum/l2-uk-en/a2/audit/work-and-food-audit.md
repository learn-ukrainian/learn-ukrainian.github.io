# Audit Report: M30 — work-and-food.md
**Level:** A2 | **Module:** M30 | **Phase:** A2.4 | **Pedagogy:** TBL | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:05:09

## Configuration
**Type:** A2
**Word Target:** 2000 words
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
| 1 | match-up |  | 8 | 8 | ✅ |
| 2 | fill-in |  | 8 | 8 | ✅ |
| 3 | true-false |  | 8 | 8 | ✅ |
| 4 | quiz |  | 8 | 8 | ✅ |
| 5 | match-up |  | 6 | 8 | ❌ |
| 6 | fill-in |  | 6 | 8 | ❌ |
| 7 | group-sort |  | 8 | 8 | ✅ |
| 8 | quiz |  | 6 | 8 | ❌ |
| 9 | fill-in |  | 6 | 8 | ❌ |
| 10 | fill-in |  | 6 | 8 | ❌ |
| 11 | match-up |  | 7 | 8 | ❌ |
| 12 | quiz |  | 6 | 8 | ❌ |

**Summary:**
- Total activities: 12 (target: 0-4) ❌
- Unique types: 5 (minimum: 0) ✅
- Priority types used: 5/15 (fill-in, group-sort, match-up, quiz, true-false) ✅
- Low density activities: 7

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q1 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q2 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q3 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q4 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q5 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q7 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY]** match-up '' has 6 pairs (target: 8-14)
  - FIX: Adjust number of pairs to 8-14.
- **[COMPLEXITY]** fill-in '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 fill-in requires at least 8 items.
- **[COMPLEXITY]** quiz '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 quiz requires at least 8 items.
- **[COMPLEXITY]** fill-in '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 fill-in requires at least 8 items.
- **[COMPLEXITY]** fill-in '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 fill-in requires at least 8 items.
- **[COMPLEXITY]** match-up '' has 7 pairs (target: 8-14)
  - FIX: Adjust number of pairs to 8-14.
- **[COMPLEXITY]** quiz '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 quiz requires at least 8 items.
- **[YAML_SCHEMA_VIOLATION]** Schema error in work-and-food.yaml: Schema validation error at key '11': {'id': 'possession-who-has-quiz', 'type': 'quiz', 'instruction': 'Визначте, у кого є предмет.', 'items': [{'question': '«У мене є новий рецепт.» Хто має рецепт?', 'options': ['Я', 'Ти', 'Він', 'Вона'], 'correct': 0}, {'question': '«У неї є свіжа картопля.» Хто має картоплю?', 'options': ['Вона', 'Він', 'Я', 'Ти'], 'correct': 0}, {'question': '«У нього є гострий ніж.» Хто має ніж?', 'options': ['Він', 'Вона', 'Ми', 'Вони'], 'correct': 0}, {'question': '«У нас є смачні помідори.» Хто має помідори?', 'options': ['Ми', 'Ви', 'Вони', 'Я'], 'correct': 0}, {'question': '«У них є велика ложка.» Хто має ложку?', 'options': ['Вони', 'Ви', 'Ми', 'Він'], 'correct': 0}, {'question': '«У тебе є олія?» Хто має олію?', 'options': ['Ти', 'Я', 'Він', 'Вона'], 'correct': 0}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 70/100)

- Revision recommended (severity 70/100)
- 14 violations (severe - consider revision)
- Immersion 10% off target (minor)
- Activity density below minimum

## Gates
- **Words:** ✅ 2296/2000 (raw: 2346)
- **Activities:** ✅ 12/0
- **Density:** ❌ 7 < 8
- **Unique_types:** ✅ 5/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 72/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ❌ 40.2% LOW (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 2+ cultural hooks but content has no cultural section

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
|  | match-up | 6 | 8 | Add 2 more items |
|  | fill-in | 6 | 8 | Add 2 more items |
|  | quiz | 6 | 8 | Add 2 more items |
|  | fill-in | 6 | 8 | Add 2 more items |
|  | fill-in | 6 | 8 | Add 2 more items |
|  | match-up | 7 | 8 | Add 1 more items |
|  | quiz | 6 | 8 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 657 | Included in Core |
| **На кухні: Готуємо разом (In the Kitchen: Cooking Together)** | ✅ | 763 | Included in Core |
| **Мій робочий день (My Workday)** | ✅ | 422 | Included in Core |
| **Практика: Розкажи про себе (Practice: Tell About Yourself)** | ✅ | 274 | Included in Core |
| **Підсумок** | ✅ | 180 | Included in Core |