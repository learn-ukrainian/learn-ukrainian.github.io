# Audit Report: M23 — checkpoint-dative.md
**Level:** A2 | **Module:** M23 | **Phase:** A2.3 | **Pedagogy:** Review | **Target:** 1500
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
| 1 | quiz |  | 8 | 8 | ✅ |
| 2 | fill-in |  | 8 | 8 | ✅ |
| 3 | match-up |  | 8 | 8 | ✅ |
| 4 | error-correction |  | 6 | 6 | ✅ |
| 5 | group-sort |  | 7 | 8 | ❌ |
| 6 | true-false |  | 6 | 8 | ❌ |

**Summary:**
- Total activities: 6 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 6/15 (error-correction, fill-in, group-sort, match-up, quiz, true-false) ✅
- Low density activities: 2

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** Sentence too long for A2: 23 words (max 15)
  - FIX: Break into shorter sentences. First 5 words: 'Це оди́н із найважли́ві́ших відмі́нків...'
- **[COMPLEXITY]** Sentence too long for A2: 16 words (max 15)
  - FIX: Break into shorter sentences. First 5 words: 'Якщо ви можете впе́внено відпові́сти́...'
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q1 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q2 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q3 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q5 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q6 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q7 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q8 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY]** group-sort '' has 7 items (target: 8-999)
  - FIX: Adjust number of items to sort to 8-999.
- **[COMPLEXITY]** true-false '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 true-false requires at least 8 items.
- **[METALANGUAGE]** Metalanguage terms used but not in vocabulary: прикметник, іменник, займенник
  - FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'what?)* |...'.
  - FIX: Vary sentence structure.
- **[INLINE_ENGLISH_IN_PROSE]** Inline English translations in B1+ prose (3 occurrences): (To the dear teacher), (To the beloved mommy), (To my best friend) — breaks immersion target
  - FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section
- **[YAML_SCHEMA_VIOLATION]** Schema error in checkpoint-dative.yaml: Schema validation error at key '6': {'id': 'unjumble-sentences', 'type': 'unjumble', 'instruction': 'Складіть правильне речення зі слів', 'items': [{'words': ['дуже', 'Мені', 'сьогодні', 'холодно.'], 'correct_order': ['Мені', 'сьогодні', 'дуже', 'холодно.']}, {'words': ['телефон.', 'братові', 'подаруємо', 'новий', 'Ми'], 'correct_order': ['Ми', 'подаруємо', 'братові', 'новий', 'телефон.']}, {'words': ['книга.', 'подобається', 'Моїй', 'подрузі', 'ця'], 'correct_order': ['Моїй', 'подрузі', 'подобається', 'ця', 'книга.']}, {'words': ['лист.', 'надіслати', 'Вам', 'потрібно', 'цей'], 'correct_order': ['Вам', 'потрібно', 'надіслати', 'цей', 'лист.']}, {'words': ['Він', 'своїй', 'завжди', 'допомагає', 'бабусі.'], 'correct_order': ['Він', 'завжди', 'допомагає', 'своїй', 'бабусі.']}, {'words': ['років', 'вашому', 'Скільки', 'синові?'], 'correct_order': ['Скільки', 'років', 'вашому', 'синові?']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 15 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1763/1500 (raw: 1966)
- **Activities:** ✅ 6/0
- **Density:** ❌ 2 < 8
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 1/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 30/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 63.1% (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
|  | group-sort | 7 | 8 | Add 1 more items |
|  | true-false | 6 | 8 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 486 | Included in Core |
| **Частина 2: Ви́бір фо́рми (Part 2: Choosing the Correct Form)** | ✅ | 552 | Included in Core |
| **Частина 3: Продукува́ння (Part 3: Production)** | ➖ | 398 | Excluded Type |
| **О́гляд помило́к та порівняння відмінків (Error Review and Case Comparison)** | ✅ | 202 | Included in Core |
| **Підсумок** | ✅ | 125 | Included in Core |