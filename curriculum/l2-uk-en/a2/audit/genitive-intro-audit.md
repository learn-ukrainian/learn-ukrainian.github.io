# Audit Report: M05 — genitive-intro.md
**Level:** A2 | **Module:** M05 | **Phase:** A2.1 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-11 01:40:23

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
| 1 | quiz | Оберіть правильний варіант | 8 | 8 | ✅ |
| 2 | fill-in | Вставте іменник у формі родового відмінка (однина) | 8 | 8 | ✅ |
| 3 | match-up | З'єднайте форму називного відмінка (однина) з правильною формою після слів кільк | 8 | 8 | ✅ |
| 4 | match-up | З'єднайте українські фрази з їхнім англійським перекладом | 8 | 8 | ✅ |
| 5 | error-correction | Знайдіть і виправте помилку | 6 | 6 | ✅ |
| 6 | group-sort | Розподіліть іменники за їхнім закінченням у родовому відмінку (однина) | 12 | 8 | ✅ |
| 7 | true-false | Правда чи ні? | 6 | 8 | ❌ |

**Summary:**
- Total activities: 7 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 6/15 (error-correction, fill-in, group-sort, match-up, quiz, true-false) ✅
- Low density activities: 1

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть правильний варіант' Q2 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть правильний варіант' Q3 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть правильний варіант' Q4 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть правильний варіант' Q6 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY]** true-false 'Правда чи ні?' has 6 items (minimum: 8)
  - FIX: Add more items. A2 true-false requires at least 8 items.
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'there is...'.
  - FIX: Vary sentence structure.
- **[GLOSSARY_LIST_IN_PROSE]** Glossary-style list (3 items) in narrative prose starting: '**У мене багато машин.** — *I have a lot of cars.*' — vocab tables belong in vocabulary YAML
  - FIX: Move vocabulary definitions to vocabulary/{slug}.yaml or rewrite as natural prose with words introduced in context
- **[LLM_PERSONA_LEAK]** LLM persona leak: 'I am your' — content should not role-play as a teacher/character
  - FIX: Rewrite in neutral educational voice. Remove first-person teacher persona.
- **[INLINE_ENGLISH_IN_PROSE]** Inline English translations in B1+ prose (4 occurrences): (There is a table here), (There is no table here), (Shortened form) — breaks immersion target
  - FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 9 violations (significant)
- Immersion 8% off target (minor)
- Activity density below minimum

## Gates
- **Words:** ✅ 3207/2000 (raw: 3276)
- **Activities:** ✅ 7/0
- **Density:** ❌ 1 < 8
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 3/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 57/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ❌ 22.0% LOW (target 30-55% (A2.1))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Правда чи ні? | true-false | 6 | 8 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 826 | Included in Core |
| **Закінчення родового відмінка однини (Genitive Singular Endings)** | ✅ | 1180 | Included in Core |
| **Коли є багато або мало (When There Is a Lot or a Little)** | ✅ | 1022 | Included in Core |
| **Підсумок — Summary** | ✅ | 179 | Included in Core |