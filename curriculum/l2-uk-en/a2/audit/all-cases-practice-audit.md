# Audit Report: M37 — all-cases-practice.md
**Level:** A2 | **Module:** M37 | **Phase:** A2.5 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:04:41

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
| 1 | quiz |  | 8 | 8 | ✅ |
| 2 | fill-in |  | 8 | 8 | ✅ |
| 3 | match-up |  | 8 | 8 | ✅ |
| 4 | error-correction |  | 7 | 6 | ✅ |

**Summary:**
- Total activities: 4 (target: 0-4) ✅
- Unique types: 4 (minimum: 0) ✅
- Priority types used: 4/15 (error-correction, fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** Sentence too long for A2: 16 words (max 15)
  - FIX: Break into shorter sentences. First 5 words: 'Зараз вони сидять удома ють...'
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q1 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q2 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q3 prompt length 3 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q4 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q5 prompt length 2 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q8 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in all-cases-practice.yaml: Schema validation error at key '3': {'id': 'error-correction-cases', 'type': 'error-correction', 'instruction': 'Знайдіть і виправте помилку у відмінку', 'items': [{'sentence': 'Я допомагаю пацієнт знайти аптеку.', 'error': 'пацієнт', 'correction': 'пацієнту', 'error_type': 'word', 'options': ['пацієнта', 'пацієнту', 'пацієнтом', 'пацієнті'], 'explanation': 'Дієслово «допомагати» вимагає давального відмінка (кому?).'}, {'sentence': 'У нас на вечірці було багато гості.', 'error': 'гості', 'correction': 'гостей', 'error_type': 'word', 'options': ['гості', 'гостей', 'гостям', 'гостями'], 'explanation': 'Після слова «багато» використовуємо родовий відмінок множини (кого/чого?).'}, {'sentence': 'Ми довго милувалися Карпати.', 'error': 'Карпати', 'correction': 'Карпатами', 'error_type': 'word', 'options': ['Карпат', 'Карпатам', 'Карпатами', 'Карпатах'], 'explanation': 'Дієслово «милуватися» вимагає орудного відмінка (ким/чим?).'}, {'sentence': 'Хворий чекає на лікаря у лікарня.', 'error': 'лікарня', 'correction': 'лікарні', 'error_type': 'word', 'options': ['лікарню', 'лікарні', 'лікарнею', 'лікарнях'], 'explanation': 'Прийменник «у» (де?) вимагає місцевого відмінка (на/у кому/чому?).'}, {'sentence': 'Лікар, випишіть мені рецепт!', 'error': 'Лікар', 'correction': 'Лікарю', 'error_type': 'word', 'options': ['Лікаря', 'Лікарю', 'Лікареві', 'Лікарем'], 'explanation': 'При звертанні потрібно використовувати кличний відмінок.'}, {'sentence': 'У пацієнта немає температура.', 'error': 'температура', 'correction': 'температури', 'error_type': 'word', 'options': ['температура', 'температуру', 'температури', 'температурою'], 'explanation': 'При запереченні (немає) використовується родовий відмінок (кого/чого?).'}, {'sentence': 'Оксана організовує вечірка для друзів.', 'error': 'вечірка', 'correction': 'вечірку', 'error_type': 'word', 'options': ['вечірка', 'вечірки', 'вечірку', 'вечіркою'], 'explanation': 'Прямий додаток (що організовує?) стоїть у знахідному відмінку (кого/що?).'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 70/100)

- Revision recommended (severity 70/100)
- 8 violations (significant)
- Immersion 12% off target
- Structure issue: Missing '## Summary'

## Gates
- **Words:** ✅ 2506/2000 (raw: 2604)
- **Activities:** ✅ 4/0
- **Density:** ✅ All > 8
- **Unique_types:** ✅ 4/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 47/1
- **Structure:** ❌ Missing '## Summary'
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ❌ 38.2% LOW (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 777 | Included in Core |
| **Діалог 2: У лікарні** | ✅ | 650 | Included in Core |
| **Діалог 3: Подорож Україною** | ✅ | 606 | Included in Core |
| **Самоперевірка: Знайди помилку** | ✅ | 473 | Included in Core |