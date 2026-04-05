# Audit Report: M34 — plural-other-cases.md
**Level:** A2 | **Module:** M34 | **Phase:** A2.5 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:05:06

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
| 3 | quiz |  | 8 | 8 | ✅ |
| 4 | error-correction |  | 6 | 6 | ✅ |

**Summary:**
- Total activities: 4 (target: 0-4) ✅
- Unique types: 4 (minimum: 0) ✅
- Priority types used: 4/15 (error-correction, fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q1 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q2 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q4 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q6 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[METALANGUAGE]** Metalanguage terms used but not in vocabulary: іменник
  - FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
- **[YAML_SCHEMA_VIOLATION]** Schema error in plural-other-cases.yaml: Schema validation error at key '4': {'id': 'unjumble-cases-practice', 'type': 'unjumble', 'instruction': 'Складіть правильне речення зі слів', 'items': [{'words': ['подарунками.', 'Я', 'дітям', 'з', 'допомагаю'], 'correct_order': ['Я', 'допомагаю', 'дітям', 'з', 'подарунками.']}, {'words': ['по', 'Вони', 'вулицях.', 'гуляють', 'часто'], 'correct_order': ['Вони', 'часто', 'гуляють', 'по', 'вулицях.']}, {'words': ['людьми.', 'Вона', 'з', 'новими', 'спілкується'], 'correct_order': ['Вона', 'спілкується', 'з', 'новими', 'людьми.']}, {'words': ['радити', 'колегам.', 'люблю', 'проєкти', 'Я', 'нові'], 'correct_order': ['Я', 'люблю', 'радити', 'нові', 'проєкти', 'колегам.']}, {'words': ['школах.', 'вчаться', 'у', 'Діти', 'завжди'], 'correct_order': ['Діти', 'завжди', 'вчаться', 'у', 'школах.']}, {'words': ['квітами.', 'кімнати', 'свої', 'Люди', 'прикрашають'], 'correct_order': ['Люди', 'прикрашають', 'свої', 'кімнати', 'квітами.']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 6 violations (moderate)
- Immersion 7% off target (minor)

## Gates
- **Words:** ✅ 3030/2000 (raw: 3123)
- **Activities:** ✅ 4/0
- **Density:** ✅ All > 8
- **Unique_types:** ✅ 4/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 31/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ❌ 42.8% LOW (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 788 | Included in Core |
| **Орудний множини: З ким? Чим?** | ✅ | 834 | Included in Core |
| **Місцевий множини: Де? На чому?** | ✅ | 764 | Included in Core |
| **Три відмінки разом: Практика** | ✅ | 440 | Included in Core |
| **Підсумок** | ✅ | 204 | Included in Core |