# Audit Report: M14 — mine-and-yours.md
**Level:** A1 | **Module:** M14 | **Phase:** A1.2 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-18 21:14:59

## Configuration
**Type:** A1-grammar
**Word Target:** 2000 words
**Activities:** 8-12 required
**Items per Activity:** ≥12 items
**Unique Types:** ≥4 types required
**Priority Types:** anagram, fill-in, match-up, quiz, unjumble
**Required Types:** fill-in, match-up, quiz, true-false
**Engagement:** ≥3 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | group-sort | Сортування: Мій, Моя, Моє, Мої | 20 | 12 | ✅ |
| 2 | match-up | Переклад: Займенники | 10 | 8 | ✅ |
| 3 | quiz | Тест: Виберіть правильну форму | 10 | 8 | ✅ |
| 4 | fill-in | Впишіть слово | 10 | 8 | ✅ |
| 5 | true-false | Правда чи Брехня | 10 | 8 | ✅ |

**Summary:**
- Total activities: 5 (target: 8-12) ❌
- Unique types: 5 (minimum: 4) ✅
- Priority types used: 3/5 (fill-in, match-up, quiz) ✅
- Required types used: 4/4 (fill-in, match-up, quiz, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Тест: Виберіть правильну форму' Q1 prompt length 2 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Тест: Виберіть правильну форму' Q2 prompt length 2 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Тест: Виберіть правильну форму' Q3 prompt length 2 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Тест: Виберіть правильну форму' Q4 prompt length 2 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Тест: Виберіть правильну форму' Q5 prompt length 4 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Тест: Виберіть правильну форму' Q6 prompt length 4 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Тест: Виберіть правильну форму' Q7 prompt length 4 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Тест: Виберіть правильну форму' Q8 prompt length 3 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Тест: Виберіть правильну форму' Q9 prompt length 3 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Тест: Виберіть правильну форму' Q10 prompt length 3 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'it takes...'.
  - FIX: Vary sentence structure.
- **[INLINE_ENGLISH_IN_PROSE]** Inline English translations in B1+ prose (4 occurrences): (Here is my mom), (Points to a girl nearby), (Points to a man) — breaks immersion target
  - FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section
- **[YAML_SCHEMA_VIOLATION]** Schema error in mine-and-yours.yaml: Schema validation error at key '4': {'instruction': 'Determine if the statement is True or False.', 'items': [{'answer': False, 'explanation': 'Книга is feminine, so it must be "Моя книга".', 'question': "Is 'Мій книга' correct?"}, {'answer': True, 'explanation': 'Його (his) and Її (her) are unchangeable forms.', 'question': "Do 'Його' and 'Її' stay the same regardless of the object?"}, {'answer': False, 'explanation': 'Твій is informal (singular). Ваш is formal (plural).', 'question': "Is 'Твій' the formal way to say 'Your'?"}, {'answer': True, 'explanation': 'Їхній behaves like an adjective and changes by gender.', 'question': "Does 'Їхній' change by gender?"}, {'answer': True, 'explanation': 'Consonants usually indicate masculine gender.', 'question': 'Does a consonant ending usually indicate masculine gender?'}, {'answer': False, 'explanation': '-А/-Я usually indicates feminine gender.', 'question': 'Does words ending in -А usually indicate masculine gender?'}, {'answer': True, 'explanation': '-О/-Е usually indicates neuter gender.', 'question': 'Does words ending in -О usually indicate neuter gender?'}, {'answer': True, 'explanation': 'Ваш is capitalized in letters to one person as a sign of respect.', 'question': "Should 'Ваш' be capitalized in a letter to a professor?"}, {'answer': False, 'explanation': "Їх (like 'це їх дім') is colloquial/surzhyk. Use Їхній.", 'question': "Is 'Це їх дім' considered standard literary Ukrainian?"}, {'answer': True, 'explanation': 'Свій refers back to the subject of the sentence.', 'question': "Does 'Свій' mean 'one's own'?"}], 'title': 'Правда чи Брехня', 'type': 'true-false'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**🔄 REWRITE** (severity 75/100)

- 13 violations (severe - consider revision)
- Immersion 8% off target (minor)
- Activity count below minimum

## Gates
- **Words:** ✅ 2805/2000 (raw: 3277)
- **Activities:** ❌ 5/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 5/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 5/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 15/1
- **Structure:** ✅ Valid Structure
- **Ipa:** ⚠️ 5 IPA issues (run lint_ipa.py --fix)
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 13 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ❌ 17.2% LOW (target 25-40% (M14))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Mine and Yours** | ✅ | 68 | Included in Core |
| **Вступ: Бюро знахідок** | ✅ | 373 | Included in Core |
| **Граматика: Мій, твій, наш** | ✅ | 911 | Included in Core |
| **Практика: Чия це річ?** | ✅ | 507 | Included in Core |
| **Діалоги: Це мій телефон** | ✅ | 440 | Included in Core |
| **Культура: Твій чи Ваш?** | ✅ | 461 | Included in Core |
| **Підсумок** | ✅ | 45 | Included in Core |
| **Vocabulary** | ➖ | 0 | Excluded Type |