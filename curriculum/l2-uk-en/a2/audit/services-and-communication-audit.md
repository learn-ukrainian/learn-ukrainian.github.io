# Audit Report: M22 — services-and-communication.md
**Level:** A2 | **Module:** M22 | **Phase:** A2.3 | **Pedagogy:** TBL | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:05:06

## Configuration
**Type:** A2
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
| 4 | group-sort |  | 9 | 8 | ✅ |
| 5 | true-false |  | 8 | 8 | ✅ |
| 6 | error-correction |  | 6 | 6 | ✅ |
| 7 | translate |  | 6 | 6 | ✅ |

**Summary:**
- Total activities: 7 (target: 0-4) ❌
- Unique types: 7 (minimum: 0) ✅
- Priority types used: 7/15 (error-correction, fill-in, group-sort, match-up, quiz, translate, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q1 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q2 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q3 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q4 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q5 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q6 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q7 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q8 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[METALANGUAGE]** Metalanguage terms used but not in vocabulary: прикметник, іменник
  - FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (90% overlap): "The Dative case marks the recipient — the person TO WHOM you send, give, or show something.". Shares significant keywords with sentence at index 27.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in services-and-communication.yaml: Schema validation error at key '6': {'id': 'translate-phrases', 'type': 'translate', 'instruction': 'Оберіть правильний переклад', 'items': [{'source': 'I want to send a parcel.', 'options': [{'text': 'Я хочу відправити посилку.', 'correct': True}, {'text': 'Я хочу отримати посилку.', 'correct': False}, {'text': 'Я хочу відправити конверт.', 'correct': False}, {'text': 'Я хочу купити посилку.', 'correct': False}]}, {'source': 'How much do I owe?', 'options': [{'text': 'Скільки з мене?', 'correct': True}, {'text': 'Скільки тобі?', 'correct': False}, {'text': 'Скільки я плачу?', 'correct': False}, {'text': 'Скільки це є?', 'correct': False}]}, {'source': 'Help me fill out the form.', 'options': [{'text': 'Допоможіть мені заповнити бланк.', 'correct': True}, {'text': 'Допоможіть мене заповнити квитанцію.', 'correct': False}, {'text': 'Допоможіть йому заповнити бланк.', 'correct': False}, {'text': 'Підкажіть мені заповнити бланк.', 'correct': False}]}, {'source': 'The recipient will get the letter.', 'options': [{'text': 'Одержувач отримає лист.', 'correct': True}, {'text': 'Відправник отримає лист.', 'correct': False}, {'text': 'Листоноша отримає посилку.', 'correct': False}, {'text': 'Одержувач надішле лист.', 'correct': False}]}, {'source': 'Thank the worker.', 'options': [{'text': 'Подякуйте працівникові.', 'correct': True}, {'text': 'Подякуйте працівника.', 'correct': False}, {'text': 'Допоможіть працівникові.', 'correct': False}, {'text': 'Покажіть працівникові.', 'correct': False}]}, {'source': 'I need three stamps.', 'options': [{'text': 'Мені потрібні три марки.', 'correct': True}, {'text': 'Я потребую три марки.', 'correct': False}, {'text': 'Мені треба три конверти.', 'correct': False}, {'text': 'Я маю три марки.', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 11 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2192/2000 (raw: 2296)
- **Activities:** ✅ 7/0
- **Density:** ✅ All > 8
- **Unique_types:** ✅ 7/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 42/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ⚠️ 80.1% (target 50-80%, within tolerance (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 414 | Included in Core |
| **Надіслати листа́: Діало́ги на пошті (Sending a Letter: Dialogues at the Post Office)** | ✅ | 581 | Included in Core |
| **Проси́ти, дякувати, допомага́ти: Дава́льний у сфе́рі послуг (Requesting, Thanking, Helping: Dative in Services)** | ✅ | 545 | Included in Core |
| **Написати адресу: Давальний у листува́нні (Writing an Address: Dative in Correspondence)** | ✅ | 483 | Included in Core |
| **Підсумок** | ✅ | 169 | Included in Core |