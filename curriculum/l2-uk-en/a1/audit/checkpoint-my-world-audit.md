# Audit Report: M14 — checkpoint-my-world.md
**Level:** A1 | **Module:** M14 | **Phase:** A1.2 | **Pedagogy:** PPP | **Target:** 1200
**Overall Status:** ✅ PASS
**Generated:** 2026-04-03 14:02:03

## Configuration
**Type:** A1
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
| 1 | quiz |  | 10 | 6 | ✅ |
| 2 | fill-in |  | 8 | 6 | ✅ |
| 3 | group-sort |  | 18 | 6 | ✅ |
| 4 | quiz |  | 8 | 6 | ✅ |
| 5 | match-up |  | 8 | 6 | ✅ |
| 6 | error-correction |  | 6 | 6 | ✅ |
| 7 | true-false |  | 7 | 6 | ✅ |
| 8 | fill-in |  | 8 | 6 | ✅ |
| 9 | match-up |  | 6 | 6 | ✅ |

**Summary:**
- Total activities: 9 (target: 0-4) ❌
- Unique types: 7 (minimum: 0) ✅
- Priority types used: 3/8 (fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[GRAMMAR]** Instrumental case used at A1: 'нами'
  - FIX: Instrumental case not allowed until A2 (M36+). Restructure sentence.
- **[COMPLEXITY]** Sentence too long for A1: 12 words (max 10)
  - FIX: Break into shorter sentences. First 5 words: 'великий велика велике новий нова́...'
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'you can...'.
  - FIX: Vary sentence structure.
- **[YAML_SCHEMA_VIOLATION]** Schema error in checkpoint-my-world.yaml: Schema validation error at key '8': {'type': 'match-up', 'instruction': 'Match the number to its Ukrainian word. These are the prices from the ярмарок dialogue — no formulas needed, just vocabulary.', 'pairs': [{'left': '20', 'right': 'двадцять'}, {'left': '25', 'right': "двадцять п'ять"}, {'left': '75', 'right': "сімдесят п'ять"}, {'left': '100', 'right': 'сто'}, {'left': '200', 'right': 'двісті'}, {'left': '300', 'right': 'триста'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 4 violations (moderate)

## Gates
- **Words:** ✅ 1538/1200 (raw: 1578)
- **Activities:** ✅ 9/0
- **Density:** ✅ All > 6
- **Unique_types:** ✅ 7/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 0/0
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 49/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 23.4% (target 10-38% (M14))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 298 | Included in Core |
| **Чита́ння (Reading Practice)** | ⚪️ | 0 | Skipped (using YAML) |
| **Грама́тика (Grammar Summary)** | ✅ | 291 | Included in Core |
| **Діало́г (Connected Dialogue)** | ✅ | 380 | Included in Core |
| **Підсумок — Summary** | ✅ | 277 | Included in Core |