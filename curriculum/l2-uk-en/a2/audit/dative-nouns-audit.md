# Audit Report: M18 — dative-nouns.md
**Level:** A2 | **Module:** M18 | **Phase:** A2.3 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:04:48

## Configuration
**Type:** A2-grammar
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
| 1 | fill-in |  | 8 | 8 | ✅ |
| 2 | group-sort |  | 12 | 8 | ✅ |
| 3 | quiz |  | 8 | 8 | ✅ |
| 4 | match-up |  | 8 | 8 | ✅ |

**Summary:**
- Total activities: 4 (target: 0-4) ✅
- Unique types: 4 (minimum: 0) ✅
- Priority types used: 4/15 (fill-in, group-sort, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q7 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in dative-nouns.yaml: Schema validation error at key '4': {'id': 'unjumble-sentences', 'type': 'unjumble', 'instruction': 'Складіть правильне речення зі слів', 'items': [{'words': ['Тетяна', 'братові', 'подарувала', 'книгу.'], 'correct_order': ['Тетяна', 'подарувала', 'братові', 'книгу.']}, {'words': ['Вчитель', 'студентам', 'показав', 'карту.'], 'correct_order': ['Вчитель', 'показав', 'студентам', 'карту.']}, {'words': ['Мама', 'казку.', 'дитині', 'читає'], 'correct_order': ['Мама', 'читає', 'дитині', 'казку.']}, {'words': ['Дідусь', 'онукові', 'купив', 'велосипед.'], 'correct_order': ['Дідусь', 'купив', 'онукові', 'велосипед.']}, {'words': ['квіти.', 'мамі', 'дарує', 'Батько'], 'correct_order': ['Батько', 'дарує', 'мамі', 'квіти.']}, {'words': ['Ми', 'сестрі', 'пишемо', 'листа.'], 'correct_order': ['Ми', 'пишемо', 'сестрі', 'листа.']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 2 violations (minor)
- Immersion 6% off target (minor)

## Gates
- **Words:** ✅ 3052/2000 (raw: 3200)
- **Activities:** ✅ 4/0
- **Density:** ✅ All > 8
- **Unique_types:** ✅ 4/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 43/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ❌ 34.2% LOW (target 40-70% (A2.1))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 1051 | Included in Core |
| **Давальний відмінок іменників жіно́чого роду (Dative of Feminine Nouns)** | ✅ | 524 | Included in Core |
| **Давальний відмінок іменників сере́днього роду (Dative of Neuter Nouns)** | ✅ | 572 | Included in Core |
| **Давальний відмінок у реченні (Dative Nouns in Sentences)** | ✅ | 714 | Included in Core |
| **Підсумок** | ✅ | 191 | Included in Core |