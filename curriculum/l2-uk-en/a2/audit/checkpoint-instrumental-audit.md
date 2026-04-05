# Audit Report: M31 — checkpoint-instrumental.md
**Level:** A2 | **Module:** M31 | **Phase:** A2.4 | **Pedagogy:** Review | **Target:** 1500
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:04:47

## Configuration
**Type:** A2
**Word Target:** 1500 words
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
| 1 | group-sort |  | 8 | 8 | ✅ |
| 2 | fill-in |  | 8 | 8 | ✅ |
| 3 | quiz |  | 8 | 8 | ✅ |
| 4 | error-correction |  | 6 | 6 | ✅ |
| 5 | match-up |  | 6 | 8 | ❌ |
| 6 | translate |  | 6 | 6 | ✅ |

**Summary:**
- Total activities: 6 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 6/15 (error-correction, fill-in, group-sort, match-up, quiz, translate) ✅
- Low density activities: 1

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** Sentence too long for A2: 18 words (max 15)
  - FIX: Break into shorter sentences. First 5 words: 'його допомогою ми можемо описати...'
- **[COMPLEXITY]** Sentence too long for A2: 19 words (max 15)
  - FIX: Break into shorter sentences. First 5 words: 'Дуже важливо розрізняти чистий орудний...'
- **[COMPLEXITY]** Sentence too long for A2: 20 words (max 15)
  - FIX: Break into shorter sentences. First 5 words: 'кіт солодко спить під столом...'
- **[COMPLEXITY]** Sentence too long for A2: 19 words (max 15)
  - FIX: Break into shorter sentences. First 5 words: 'Наприклад ми швидко прибираємо брудну...'
- **[COMPLEXITY]** Sentence too long for A2: 24 words (max 15)
  - FIX: Break into shorter sentences. First 5 words: 'Вони мають закінчення ем наприклад...'
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q7 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q8 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY]** match-up '' has 6 pairs (target: 8-14)
  - FIX: Adjust number of pairs to 8-14.
- **[INLINE_ENGLISH_IN_PROSE]** Inline English translations in B1+ prose (3 occurrences): (She works as a doctor), (She will be a doctor), (He quickly became a director) — breaks immersion target
  - FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section
- **[YAML_SCHEMA_VIOLATION]** Schema error in checkpoint-instrumental.yaml: Schema validation error at key '5': {'id': 'translate-practice', 'type': 'translate', 'instruction': 'Оберіть правильний переклад речення', 'items': [{'source': 'I write with a pen.', 'options': [{'text': 'Я пишу ручкою.', 'correct': True}, {'text': 'Я пишу з ручкою.', 'correct': False}, {'text': 'Я пишу ручку.', 'correct': False}, {'text': 'Я пишу на ручці.', 'correct': False}]}, {'source': 'She works as a doctor.', 'options': [{'text': 'Вона працює лікаркою.', 'correct': True}, {'text': 'Вона працює з лікаркою.', 'correct': False}, {'text': 'Вона працює лікарка.', 'correct': False}, {'text': 'Вона працює лікарку.', 'correct': False}]}, {'source': 'The cat sleeps under the table.', 'options': [{'text': 'Кіт спить під столом.', 'correct': True}, {'text': 'Кіт спить під стіл.', 'correct': False}, {'text': 'Кіт спить під столі.', 'correct': False}, {'text': 'Кіт спить на столі.', 'correct': False}]}, {'source': 'We drink coffee with sugar.', 'options': [{'text': "Ми п'ємо каву з цукром.", 'correct': True}, {'text': "Ми п'ємо каву цукром.", 'correct': False}, {'text': "Ми п'ємо каву з цукру.", 'correct': False}, {'text': "Ми п'ємо каву цукор.", 'correct': False}]}, {'source': 'They travel by bus.', 'options': [{'text': 'Вони подорожують автобусом.', 'correct': True}, {'text': 'Вони подорожують з автобусом.', 'correct': False}, {'text': 'Вони подорожують на автобус.', 'correct': False}, {'text': 'Вони подорожують в автобусі.', 'correct': False}]}, {'source': 'I walk with my friend.', 'options': [{'text': 'Я гуляю з другом.', 'correct': True}, {'text': 'Я гуляю другом.', 'correct': False}, {'text': 'Я гуляю з друга.', 'correct': False}, {'text': 'Я гуляю на другу.', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 10 violations (significant)
- Activity density below minimum

## Gates
- **Words:** ✅ 1901/1500 (raw: 1948)
- **Activities:** ✅ 6/0
- **Density:** ❌ 1 < 8
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 3/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 21/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 50.7% (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
|  | match-up | 6 | 8 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 588 | Included in Core |
| **Частина 2: Вибір та застосування** | ✅ | 529 | Included in Core |
| **Частина 3: Вільне вживання** | ✅ | 619 | Included in Core |
| **Підсумок** | ✅ | 165 | Included in Core |