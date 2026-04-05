# Audit Report: M24 — instrumental-accompaniment.md
**Level:** A2 | **Module:** M24 | **Phase:** A2.4 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:04:59

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
| 1 | match-up |  | 8 | 8 | ✅ |
| 2 | fill-in |  | 8 | 8 | ✅ |
| 3 | quiz |  | 8 | 8 | ✅ |
| 4 | fill-in |  | 8 | 8 | ✅ |
| 5 | error-correction |  | 6 | 6 | ✅ |

**Summary:**
- Total activities: 5 (target: 0-4) ❌
- Unique types: 4 (minimum: 0) ✅
- Priority types used: 4/15 (error-correction, fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** Sentence too long for A2: 19 words (max 15)
  - FIX: Break into shorter sentences. First 5 words: 'Деякі слова жіночого роду мають...'
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q1 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q2 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q3 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q4 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q5 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q6 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q7 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q8 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[METALANGUAGE]** Metalanguage terms used but not in vocabulary: займенник
  - FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
- **[INLINE_ENGLISH_IN_PROSE]** Inline English translations in B1+ prose (6 occurrences): (Instrumental case), (She lives with her parents), (Accusative case) — breaks immersion target
  - FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section
- **[YAML_SCHEMA_VIOLATION]** Schema error in instrumental-accompaniment.yaml: Schema validation error at key '5': {'id': 'error-correction-endings', 'type': 'error-correction', 'instruction': 'Знайдіть і виправте помилку в закінченні орудного відмінка', 'items': [{'sentence': "Я п'ю каву з молоко.", 'error': 'молоко', 'correction': 'молоком', 'error_type': 'word', 'options': ['молоком', 'молока', 'молоку'], 'explanation': 'Після прийменника «з» потрібен орудний відмінок: з молоком.'}, {'sentence': 'Він розмовляє із сестра.', 'error': 'сестра', 'correction': 'сестрою', 'error_type': 'word', 'options': ['сестри', 'сестрою', 'сестрі'], 'explanation': 'Жіночий рід на -а в орудному відмінку має закінчення -ою (із сестрою).'}, {'sentence': 'Вона живе з хлопець.', 'error': 'хлопець', 'correction': 'хлопцем', 'error_type': 'word', 'options': ['хлопця', 'хлопцем', 'хлопцю'], 'explanation': "Слово «хлопець» втрачає голосну «е» і отримує м'яке закінчення -ем."}, {'sentence': 'Ми їмо салат зі сметаном.', 'error': 'сметаном', 'correction': 'сметаною', 'error_type': 'word', 'options': ['сметаною', 'сметани', 'сметані'], 'explanation': '«Сметана» — це жіночий рід, тому правильне закінчення -ою.'}, {'sentence': 'Я люблю чай з лимона.', 'error': 'лимона', 'correction': 'лимоном', 'error_type': 'word', 'options': ['лимоном', 'лимону', 'лимоні'], 'explanation': 'Орудний відмінок чоловічого роду після твердого приголосного має закінчення -ом.'}, {'sentence': 'Мені потрібен бутерброд із сиру.', 'error': 'сиру', 'correction': 'сиром', 'error_type': 'word', 'options': ['сиром', 'сирі', 'сир'], 'explanation': 'Орудний відмінок відповідає на питання «з чим?» — із сиром.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 12 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2313/2000 (raw: 2559)
- **Activities:** ✅ 5/0
- **Density:** ✅ All > 8
- **Unique_types:** ✅ 4/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 33/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 70.9% (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 461 | Included in Core |
| **Закінчення орудного відмінка однини (Instrumental Singular Endings)** | ✅ | 590 | Included in Core |
| **З/із/зі + орудний відмінок (Z/iz/zi + Instrumental)** | ✅ | 523 | Included in Core |
| **Практика: З ким? З чим? (Practice: With Whom? With What?)** | ✅ | 569 | Included in Core |
| **Підсумок** | ✅ | 170 | Included in Core |