# Audit Report: M63 — 63-synonyms-quantity.md
**Level:** B2 | **Module:** M63 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:50:24

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
| 1 | match-up | Знайдіть точну міру | 12 | 8 | ✅ |
| 2 | quiz | Оберіть масштаб | 8 | 8 | ✅ |
| 3 | group-sort | Багато чи Мало? | 20 | 14 | ✅ |
| 4 | unjumble | Складіть кількісне речення | 8 | 6 | ✅ |
| 5 | cloze | Звіт з ярмарку | 17 | 14 | ✅ |
| 6 | fill-in | Офіційна міра | 10 | 8 | ✅ |
| 7 | error-correction | Виправте кількість | 8 | 6 | ✅ |
| 8 | translate | Переклад міри | 8 | 6 | ✅ |
| 9 | true-false | Нюанси кількості | 8 | 8 | ✅ |
| 10 | select | Всі відтінки багатоманітності | 6 | 6 | ✅ |
| 11 | match-up | Регістри та Кількість | 12 | 8 | ✅ |
| 12 | match-up | Кількість та Об'єкти | 12 | 8 | ✅ |
| 13 | quiz | Кількість у житті | 8 | 8 | ✅ |
| 14 | select | Кількісна етика | 6 | 6 | ✅ |
| 15 | essay-response | Творче завдання: Масштаб моїх планів | 1 | 1 | ✅ |
| 16 | reading | Текст для аналізу: Синоніми: Кількість та Міра | 3 | 3 | ✅ |

**Summary:**
- Total activities: 16 (target: 10-14) ❌
- Unique types: 12 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Required types used: 3/3 (fill-in, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: Schema validation error at key '13': {'type': 'select', 'title': 'Кількісна етика', 'instruction': 'Оберіть усі слова, що позначають позитивний підхід до ресурсів (6 елементів).', 'items': [{'question': 'Які терміни вказують на розумне споживання? (Оберіть 6)', 'options': [{'text': 'ощадливий', 'correct': True}, {'text': 'раціональний', 'correct': True}, {'text': 'виважений', 'correct': True}, {'text': 'оптимальний', 'correct': True}, {'text': 'щедрий', 'correct': True}, {'text': 'поміркований', 'correct': True}]}, {'question': "Оберіть синоніми до слова 'достатньо':", 'options': [{'text': 'доволі', 'correct': True}, {'text': 'вдосталь', 'correct': True}, {'text': 'вистачить', 'correct': True}, {'text': 'замало', 'correct': False}]}, {'question': "Які слова описують 'надлишок':", 'options': [{'text': 'надмір', 'correct': True}, {'text': 'забагато', 'correct': True}, {'text': 'перебір', 'correct': True}, {'text': 'дефіцит', 'correct': False}]}, {'question': 'Оберіть слова для опису великих фінансів:', 'options': [{'text': 'капітал', 'correct': True}, {'text': 'бюджет', 'correct': True}, {'text': 'інвестиції', 'correct': True}, {'text': 'копійка', 'correct': False}]}, {'question': "Які слова вказують на 'важливість внеску':", 'options': [{'text': 'вагомий', 'correct': True}, {'text': 'суттєвий', 'correct': True}, {'text': 'значний', 'correct': True}, {'text': 'мізерний', 'correct': False}]}, {'question': "Оберіть назви 'масштабних процесів':", 'options': [{'text': 'глобальний', 'correct': True}, {'text': 'колосальний', 'correct': True}, {'text': 'масштабний', 'correct': True}, {'text': 'точковий', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ❌ 1794/2000 (raw: 1885)
- **Activities:** ✅ 16/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 9 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (vocab))
- **Richness:** ✅ 98% (phraseology)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 7 | 4 | 100% | 25% | 25.0% |
| variety | 0.99 | - | 99% | 17% | 16.5% |
| cultural | 2 | - | 100% | 17% | 16.7% |
| visual | 4 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.87 | - | 87% | 8% | 7.3% |
| examples | 56 | - | 100% | 8% | 8.3% |
| realworld | 6 | - | 100% | 8% | 8.3% |
| questions | 8 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **98.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 69 | Included in Core |
| **Розминка — Багато чи мало?** | ⚪️ | 378 | Skipped |
| **Much/Many** | ⚪️ | 554 | Skipped |
| **Few/Little** | ⚪️ | 339 | Skipped |
| **Практика — опис кількості** | ⚪️ | 442 | Skipped |
| **Підсумок** | ✅ | 12 | Included in Core |