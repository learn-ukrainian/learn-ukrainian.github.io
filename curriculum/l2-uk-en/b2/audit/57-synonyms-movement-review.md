# Audit Report: M57 — 57-synonyms-movement.md
**Level:** B2 | **Module:** M57 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:50:18

## Configuration
**Type:** B2-vocab
**Word Target:** 2000 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** mark-the-words, match-up, quiz, translate
**Required Types:** fill-in, reading, true-false
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥35 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | match-up | Знайдіть манеру руху | 12 | 8 | ✅ |
| 2 | quiz | Оберіть точний рух | 8 | 8 | ✅ |
| 3 | group-sort | Швидкість та Стихія | 18 | 14 | ✅ |
| 4 | unjumble | Складіть динамічне речення | 8 | 6 | ✅ |
| 5 | cloze | Дорога додому | 19 | 14 | ✅ |
| 6 | fill-in | Манера та Швидкість | 10 | 8 | ✅ |
| 7 | error-correction | Виправте помилки руху | 8 | 6 | ✅ |
| 8 | translate | Перекладіть дію | 8 | 6 | ✅ |
| 9 | true-false | Нюанси руху | 8 | 8 | ✅ |
| 10 | select | Всі відтінки бігу | 6 | 6 | ✅ |
| 11 | match-up | Рух та Його Джерело | 12 | 8 | ✅ |
| 12 | match-up | Антоніми за манерою | 12 | 8 | ✅ |
| 13 | quiz | Метафоричний рух | 8 | 8 | ✅ |
| 14 | essay-response | Творче завдання: Світ у русі | 1 | 1 | ✅ |
| 15 | select | Технічний та Офіційний рух | 6 | 6 | ✅ |
| 16 | reading | Текст для аналізу: Синоніми: Рух і Пересування | 3 | 3 | ✅ |

**Summary:**
- Total activities: 16 (target: 10-14) ❌
- Unique types: 12 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Required types used: 3/3 (fill-in, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 57-synonyms-movement.yaml: Schema validation error at key '14': {'type': 'select', 'title': 'Технічний та Офіційний рух', 'instruction': 'Оберіть слова, які доречні в офіційному або технічному контексті (6+ елементів).', 'items': [{'question': 'Яка лексика пасує для новин або документів?', 'options': [{'text': 'пересуватися', 'correct': True}, {'text': 'транспортувати', 'correct': True}, {'text': 'здійснювати переліт', 'correct': True}, {'text': 'марш', 'correct': True}, {'text': 'міграція', 'correct': True}, {'text': 'експортувати', 'correct': True}]}, {'question': 'Оберіть терміни для опису швидкості:', 'options': [{'text': 'інтенсивність', 'correct': True}, {'text': 'траєкторія', 'correct': True}, {'text': 'прискорення', 'correct': True}, {'text': 'чимчикування', 'correct': False}]}, {'question': 'Які слова описують рух великих груп людей?', 'options': [{'text': 'евакуація', 'correct': True}, {'text': 'переміщення', 'correct': True}, {'text': 'мандрівка', 'correct': False}, {'text': 'похід', 'correct': True}]}, {'question': 'Оберіть слова для опису руху транспорту за розкладом:', 'options': [{'text': 'курсувати', 'correct': True}, {'text': 'прибувати', 'correct': True}, {'text': 'відправлятися', 'correct': True}, {'text': 'летіти', 'correct': False}]}, {'question': 'Які слова вказують на зміну напрямку?', 'options': [{'text': 'маневрувати', 'correct': True}, {'text': 'повертати', 'correct': True}, {'text': 'гальмувати', 'correct': True}, {'text': 'стояти', 'correct': False}]}, {'question': 'Оберіть слова для опису подолання кордонів:', 'options': [{'text': 'перетинати', 'correct': True}, {'text': "в'їжджати", 'correct': True}, {'text': 'виїжджати', 'correct': True}, {'text': 'брести', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ❌ 1826/2000 (raw: 2004)
- **Activities:** ✅ 16/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 6 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 90-100% (vocab))
- **Richness:** ✅ 99% (phraseology)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 7 | 4 | 100% | 25% | 25.0% |
| variety | 0.99 | - | 99% | 17% | 16.5% |
| cultural | 5 | - | 100% | 17% | 16.7% |
| visual | 6 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.98 | - | 98% | 8% | 8.2% |
| examples | 40 | - | 100% | 8% | 8.3% |
| realworld | 5 | - | 100% | 8% | 8.3% |
| questions | 7 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **99.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 92 | Included in Core |
| **Розминка — Як ходити і бігати** | ⚪️ | 665 | Skipped |
| **Walk** | ⚪️ | 469 | Skipped |
| **Run** | ⚪️ | 208 | Skipped |
| **Практика — динамічний опис** | ⚪️ | 380 | Skipped |
| **Підсумок** | ✅ | 12 | Included in Core |