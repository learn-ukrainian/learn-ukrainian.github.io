# Audit Report: M32 — plural-nominative-accusative.md
**Level:** A2 | **Module:** M32 | **Phase:** A2.5 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:05:05

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
| 4 | error-correction |  | 6 | 6 | ✅ |
| 5 | match-up |  | 8 | 8 | ✅ |
| 6 | fill-in |  | 6 | 8 | ❌ |
| 7 | true-false |  | 6 | 8 | ❌ |

**Summary:**
- Total activities: 7 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 6/15 (error-correction, fill-in, group-sort, match-up, quiz, true-false) ✅
- Low density activities: 2

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** fill-in '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 fill-in requires at least 8 items.
- **[COMPLEXITY]** true-false '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 true-false requires at least 8 items.
- **[METALANGUAGE]** Metalanguage terms used but not in vocabulary: множина
  - FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
- **[YAML_SCHEMA_VIOLATION]** Schema error in plural-nominative-accusative.yaml: Schema validation error at key '0': '— Тоді я швидко приготую холодні напої для всіх.' is valid under each of {'required': ['words', 'correct_order'], 'additionalProperties': False, 'properties': {'words': {'type': 'array', 'minItems': 3, 'items': {'type': 'string', 'minLength': 1}}, 'correct_order': {'type': 'array', 'minItems': 3, 'items': {'type': 'string', 'minLength': 1}}}}, {'required': ['words', 'answer'], 'additionalProperties': False, 'properties': {'words': {'type': 'array', 'minItems': 3, 'items': {'type': 'string', 'minLength': 1}}, 'answer': {'type': 'string', 'minLength': 1}}}
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 4 violations (moderate)
- Activity density below minimum

## Gates
- **Words:** ✅ 2118/2000 (raw: 2163)
- **Activities:** ✅ 7/0
- **Density:** ❌ 2 < 8
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 76/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 71.7% (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
|  | fill-in | 6 | 8 | Add 2 more items |
|  | true-false | 6 | 8 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 162 | Included in Core |
| **Множина називного відмінка (Nominative Plural)** | ✅ | 722 | Included in Core |
| **Знахідний відмінок множини: Живе чи неживе? (Accusative Plural)** | ✅ | 479 | Included in Core |
| **Називний чи знахідний? Визначаємо за контекстом** | ✅ | 647 | Included in Core |
| **Підсумок** | ✅ | 108 | Included in Core |