# Audit Report: M27 — vocative-expanded.md
**Level:** A2 | **Module:** M27 | **Phase:** A2.4 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:05:08

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
| 2 | match-up |  | 8 | 8 | ✅ |
| 3 | error-correction |  | 8 | 6 | ✅ |
| 4 | quiz |  | 8 | 8 | ✅ |
| 5 | group-sort |  | 8 | 8 | ✅ |
| 6 | true-false |  | 6 | 8 | ❌ |

**Summary:**
- Total activities: 6 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 6/15 (error-correction, fill-in, group-sort, match-up, quiz, true-false) ✅
- Low density activities: 1

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q1 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q2 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q3 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q5 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY]** true-false '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 true-false requires at least 8 items.
- **[METALANGUAGE]** Metalanguage terms used but not in vocabulary: іменник, займенник
  - FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
- **[YAML_SCHEMA_VIOLATION]** Schema error in vocative-expanded.yaml: Schema validation error at key '0': '— Що вас турбує?' is valid under each of {'required': ['words', 'correct_order'], 'additionalProperties': False, 'properties': {'words': {'type': 'array', 'minItems': 3, 'items': {'type': 'string', 'minLength': 1}}, 'correct_order': {'type': 'array', 'minItems': 3, 'items': {'type': 'string', 'minLength': 1}}}}, {'required': ['words', 'answer'], 'additionalProperties': False, 'properties': {'words': {'type': 'array', 'minItems': 3, 'items': {'type': 'string', 'minLength': 1}}, 'answer': {'type': 'string', 'minLength': 1}}}
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 7 violations (significant)
- Activity density below minimum

## Gates
- **Words:** ✅ 2485/2000 (raw: 2714)
- **Activities:** ✅ 6/0
- **Density:** ❌ 1 < 8
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 42/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 60.0% (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
|  | true-false | 6 | 8 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 640 | Included in Core |
| **Професі́йні звертання (Professional Vocative)** | ✅ | 560 | Included in Core |
| **Дру́же мій, люба́ моя́: емоці́йний кличний (Emotional Vocative)** | ✅ | 717 | Included in Core |
| **Яки́й кличний обра́ти? (Choosing the Right Vocative)** | ✅ | 407 | Included in Core |
| **Підсумок** | ✅ | 161 | Included in Core |