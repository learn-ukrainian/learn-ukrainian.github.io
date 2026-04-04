# Audit Report: M36 — food-and-drink.md
**Level:** A1 | **Module:** M36 | **Phase:** A1.6 | **Pedagogy:** PPP | **Target:** 1200
**Overall Status:** ✅ PASS
**Generated:** 2026-04-04 19:29:58

## Configuration
**Type:** A1-vocab
**Word Target:** 1200 words
**Activities:** 0-4 required
**Items per Activity:** ≥6 items
**Unique Types:** ≥0 types required
**Priority Types:** anagram, classify, fill-in, image-to-letter, match-up, quiz, unjumble, watch-and-repeat
**Engagement:** ≥0 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | fill-in |  | 6 | 6 | ✅ |
| 2 | quiz |  | 6 | 6 | ✅ |
| 3 | match-up |  | 10 | 6 | ✅ |
| 4 | group-sort |  | 10 | 6 | ✅ |
| 5 | true-false |  | 6 | 6 | ✅ |
| 6 | anagram |  | 8 | 6 | ✅ |
| 7 | translate |  | 6 | 6 | ✅ |
| 8 | error-correction |  | 6 | 6 | ✅ |
| 9 | quiz |  | 6 | 6 | ✅ |

**Summary:**
- Total activities: 9 (target: 0-4) ❌
- Unique types: 8 (minimum: 0) ✅
- Priority types used: 4/8 (anagram, fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[LEVEL_RESTRICTION]** Activity 'anagram' should be phased out after A1 M10 (current: M36)
  - FIX: Anagram is for Cyrillic scaffolding only. Use unjumble for word-ordering practice.
- **[HINT_IN_ACTIVITY]** anagram activity 'Untitled' has item-level hint in item 1
  - FIX: Remove all 'hint' fields from activity items (they break activities and provide no real pedagogical value)
- **[YAML_SCHEMA_VIOLATION]** Schema error in food-and-drink.yaml: Schema validation error at key 'correct': 2 is not of type 'boolean'
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 3 violations (minor)

## Gates
- **Words:** ✅ 1643/1200 (raw: 1738)
- **Activities:** ✅ 9/0
- **Density:** ✅ All > 6
- **Unique_types:** ✅ 8/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 4/0
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 74/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 30.3% (target 20-40% (M36))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 449 | Included in Core |
| **Ї́жа (Food)** | ✅ | 456 | Included in Core |
| **Напо́ї (Drinks)** | ✅ | 442 | Included in Core |
| **Підсумок — Summary** | ✅ | 296 | Included in Core |