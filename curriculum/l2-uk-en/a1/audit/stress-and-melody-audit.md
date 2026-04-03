# Audit Report: M04 — stress-and-melody.md
**Level:** A1 | **Module:** M04 | **Phase:** A1.1 | **Pedagogy:** PPP | **Target:** 1200
**Overall Status:** ✅ PASS
**Generated:** 2026-04-03 14:02:15

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
| 1 | quiz |  | 8 | 6 | ✅ |
| 2 | match-up |  | 8 | 6 | ✅ |
| 3 | quiz |  | 7 | 6 | ✅ |
| 4 | fill-in |  | 8 | 6 | ✅ |
| 5 | group-sort |  | 10 | 6 | ✅ |
| 6 | true-false |  | 8 | 6 | ✅ |
| 7 | quiz |  | 6 | 6 | ✅ |
| 8 | match-up |  | 8 | 6 | ✅ |

**Summary:**
- Total activities: 8 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 3/8 (fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_OPTIONS]** quiz '' Q1 has 2 options (target: [3, 4])
  - FIX: Provide [3, 4] options for A1 quizzes.
- **[COMPLEXITY_OPTIONS]** quiz '' Q2 has 2 options (target: [3, 4])
  - FIX: Provide [3, 4] options for A1 quizzes.
- **[COMPLEXITY_OPTIONS]** quiz '' Q3 has 2 options (target: [3, 4])
  - FIX: Provide [3, 4] options for A1 quizzes.
- **[COMPLEXITY_OPTIONS]** quiz '' Q4 has 2 options (target: [3, 4])
  - FIX: Provide [3, 4] options for A1 quizzes.
- **[COMPLEXITY_OPTIONS]** quiz '' Q8 has 2 options (target: [3, 4])
  - FIX: Provide [3, 4] options for A1 quizzes.
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'the word...'.
  - FIX: Vary sentence structure.
- **[INLINE_ENGLISH_IN_PROSE]** Inline English translations in B1+ prose (3 occurrences): (Divide into syllables), (Find the stress), (Read together) — breaks immersion target
  - FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section
- **[YAML_SCHEMA_VIOLATION]** Schema error in stress-and-melody.yaml: Schema validation error at key '8': {'type': 'observe', 'examples': ['ЗАмок (castle) ↔ замОк (lock)', 'МУка (torment) ↔ мукА (flour)', 'АТлас (atlas/maps) ↔ атлАС (satin fabric)', 'МАма — stress stays on the first syllable', 'воДА — stress stays on the last syllable', 'фотоГРАфія — stress stays on the third syllable'], 'prompt': 'Look at the first three pairs. What happens to the MEANING of a Ukrainian word when you move the stress to a different syllable? Now look at the last three examples — what does this tell you about learning new Ukrainian words?'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 30/100)

- 8 violations (significant)

## Gates
- **Words:** ✅ 1790/1200 (raw: 1823)
- **Activities:** ✅ 8/0
- **Density:** ✅ All > 6
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 1/0
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 48/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 14.2% (target 8-30% (M04))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 578 | Included in Core |
| **Інтона́ція (Intonation)** | ✅ | 479 | Included in Core |
| **Чита́ємо вго́лос (Reading Aloud)** | ⚪️ | 0 | Skipped (using YAML) |
| **Підсумок — Summary** | ✅ | 308 | Included in Core |