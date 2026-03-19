# Audit Report: M14 — checkpoint-first-contact.md
**Level:** A1 | **Module:** M14 | **Phase:** A1.1 | **Pedagogy:** TTT | **Target:** 1200
**Overall Status:** ❌ FAIL
**Generated:** 2026-03-19 12:49:47

## Configuration
**Type:** A1-checkpoint
**Word Target:** 1200 words
**Activities:** 0-4 required
**Items per Activity:** ≥10 items
**Unique Types:** ≥0 types required
**Priority Types:** fill-in, match-up, quiz
**Required Types:** quiz
**Engagement:** ≥2 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Skill Check: Cyrillic Reading and Gender | 8 | 6 | ✅ |
| 2 | quiz | Skill Check: Adjective-Noun Agreement | 8 | 6 | ✅ |
| 3 | quiz | Skill Check: Plurals and Vocabulary | 7 | 6 | ✅ |
| 4 | quiz | Full Integration: Hostel and Cafe Scenarios | 7 | 6 | ✅ |
| 5 | match-up | Match the Noun to Its Correct Adjective Form | 8 | 6 | ✅ |
| 6 | fill-in | Complete the Sentence | 6 | 6 | ✅ |
| 7 | group-sort | Sort Nouns by Gender | 12 | 10 | ✅ |
| 8 | unjumble | Put the Words in Order | 6 | 6 | ✅ |
| 9 | true-false | True or False? Gender and Agreement Rules | 8 | 6 | ✅ |

**Summary:**
- Total activities: 9 (target: 0-4) ❌
- Unique types: 7 (minimum: 0) ✅
- Priority types used: 3/3 (fill-in, match-up, quiz) ✅
- Required types used: 1/1 (quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Put the Words in Order' item 6 has 2 words (target: 4-6)
  - FIX: Adjust sentence length to 4-6 words to match A1 complexity.
- **[METALANGUAGE]** Metalanguage terms used but not in vocabulary: множина
  - FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
- **[LLM_PERSONA_LEAK]** LLM persona leak: 'I am your' — content should not role-play as a teacher/character
  - FIX: Rewrite in neutral educational voice. Remove first-person teacher persona.
- **[YAML_SCHEMA_VIOLATION]** Schema error in checkpoint-first-contact.yaml: Schema validation error at key 'words': ['кафе?', 'Де'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 4 violations (moderate)

## Gates
- **Words:** ✅ 1674/1200 (raw: 1776)
- **Activities:** ✅ 9/0
- **Density:** ✅ All > 10
- **Unique_types:** ✅ 7/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 3/2
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 20/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 7.0% (checkpoint - no gate)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Checkpoint: First Contact** | ➖ | 65 | Excluded Type |
| **Огляд (Overview)** | ✅ | 224 | Included in Core |
| **Навичка 1: Читання та Рід (Skill 1: Reading and Gender)** | ⚪️ | 0 | Skipped (using YAML) |
| **Навичка 2: Прикметники та Множина (Skill 2: Adjectives and Plurals)** | ✅ | 280 | Included in Core |
| **Культурний контекст: Кафе (Cultural Context: Cafe)** | ✅ | 273 | Included in Core |
| **Інтеграційне завдання (Integration Task)** | ✅ | 272 | Included in Core |
| **Підсумок — Summary** | ✅ | 199 | Included in Core |