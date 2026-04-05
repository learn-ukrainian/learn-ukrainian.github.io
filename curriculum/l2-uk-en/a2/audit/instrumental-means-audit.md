# Audit Report: M25 — instrumental-means.md
**Level:** A2 | **Module:** M25 | **Phase:** A2.4 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:05:00

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
| 2 | quiz |  | 8 | 8 | ✅ |
| 3 | match-up |  | 8 | 8 | ✅ |
| 4 | group-sort |  | 8 | 8 | ✅ |

**Summary:**
- Total activities: 4 (target: 0-4) ✅
- Unique types: 4 (minimum: 0) ✅
- Priority types used: 4/15 (fill-in, group-sort, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q6 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[METALANGUAGE]** Metalanguage terms used but not in vocabulary: іменник
  - FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
- **[RUSSICISM_DETECTED]** Found 2 Russicism(s) in content: 'давайте подивимося' → подивімося
  - FIX: Replace Russicisms with standard Ukrainian equivalents. These are Russian calques that have standard Ukrainian forms. See Phase B prompt 'Russianisms Pre-Output Scan' table.
- **[YAML_SCHEMA_VIOLATION]** Schema error in instrumental-means.yaml: Schema validation error at key '4': {'id': 'unjumble-phrases', 'type': 'unjumble', 'instruction': 'Складіть правильне речення зі слів (Make a correct sentence from the words)', 'items': [{'words': ['автобусом.', 'Я', 'на', 'роботу', 'їду'], 'correct_order': ['Я', 'їду', 'на', 'роботу', 'автобусом.']}, {'words': ['малюють', 'олівцями.', 'Діти', 'кольоровими'], 'correct_order': ['Діти', 'малюють', 'кольоровими', 'олівцями.']}, {'words': ['подорожувати', 'потягом.', 'Ми', 'любимо'], 'correct_order': ['Ми', 'любимо', 'подорожувати', 'потягом.']}, {'words': ['гострим', "м'ясо", 'ножем.', 'Брат', 'ріже'], 'correct_order': ['Брат', 'ріже', "м'ясо", 'гострим', 'ножем.']}, {'words': ['вікно', 'Мама', 'чистою', 'миє', 'ганчіркою.'], 'correct_order': ['Мама', 'миє', 'вікно', 'чистою', 'ганчіркою.']}, {'words': ['летять', 'літаком.', 'у', 'відпустку', 'Вони'], 'correct_order': ['Вони', 'летять', 'у', 'відпустку', 'літаком.']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 4 violations (moderate)

## Gates
- **Words:** ✅ 3001/2000 (raw: 3122)
- **Activities:** ✅ 4/0
- **Density:** ✅ All > 8
- **Unique_types:** ✅ 4/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 37/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ⚠️ 47.6% (target 50-80%, within tolerance (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 720 | Included in Core |
| **Їхати автобусом: Засіб пересування (Travel by Bus: Means of Transport)** | ✅ | 745 | Included in Core |
| **Орудний відмінок множини (Instrumental Plural)** | ✅ | 666 | Included in Core |
| **Практика: Знаряддя чи супутник?** | ✅ | 680 | Included in Core |
| **Підсумок** | ✅ | 190 | Included in Core |