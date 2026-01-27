# Audit Report: M63 — 63-synonyms-quantity.md

**Level:** B2 | **Module:** M63 | **Phase:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:28:27

## Configuration

**Type:** B2-vocab
**Word Target:** 1750 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** mark-the-words, match-up, quiz, translate
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

**Summary:**
- Total activities: 15 (target: 10-14) ❌
- Unique types: 11 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: Schema validation error at key '13': {'type': 'select', 'title': 'Кількісна етика', 'instruction': 'Оберіть усі слова, що позначають позитивний підхід до ресурсів (6 елементів).', 'items': [{'question': 'Які терміни вказують на розумне споживання? (Оберіть 6)', 'options': [{'text': 'ощадливий', 'correct': True}, {'text': 'раціональний', 'correct': True}, {'text': 'виважений', 'correct': True}, {'text': 'оптимальний', 'correct': True}, {'text': 'щедрий', 'correct': True}, {'text': 'поміркований', 'correct': True}]}, {'question': "Оберіть синоніми до слова 'достатньо':", 'options': [{'text': 'доволі', 'correct': True}, {'text': 'вдосталь', 'correct': True}, {'text': 'вистачить', 'correct': True}, {'text': 'замало', 'correct': False}]}, {'question': "Які слова описують 'надлишок':", 'options': [{'text': 'надмір', 'correct': True}, {'text': 'забагато', 'correct': True}, {'text': 'перебір', 'correct': True}, {'text': 'дефіцит', 'correct': False}]}, {'question': 'Оберіть слова для опису великих фінансів:', 'options': [{'text': 'капітал', 'correct': True}, {'text': 'бюджет', 'correct': True}, {'text': 'інвестиції', 'correct': True}, {'text': 'копійка', 'correct': False}]}, {'question': "Які слова вказують на 'важливість внеску':", 'options': [{'text': 'вагомий', 'correct': True}, {'text': 'суттєвий', 'correct': True}, {'text': 'значний', 'correct': True}, {'text': 'мізерний', 'correct': False}]}, {'question': "Оберіть назви 'масштабних процесів':", 'options': [{'text': 'глобальний', 'correct': True}, {'text': 'колосальний', 'correct': True}, {'text': 'масштабний', 'correct': True}, {'text': 'точковий', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation

**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates

- **Words:** ✅ 1784/1750 (raw: 1937)
- **Activities:** ✅ 15/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 9 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 90-100% (vocab))
- **Richness:** ✅ 95% (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details

**Score:** 95% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 57 | 24 | 100% | 20% | 20.0% |
| engagement | 7 | 5 | 100% | 15% | 15.0% |
| dialogues | 5 | 4 | 100% | 15% | 15.0% |
| variety | 0.99 | - | 99% | 10% | 9.9% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 6 | 3 | 100% | 10% | 10.0% |
| visual | 4 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.88 | - | 88% | 5% | 4.4% |
| questions | 8 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.0%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 69 | Included in Core |
| **Вступ: Масштаби українського життя** | ✅ | 98 | Included in Core |
| **Частина 1: Океан багатоманітності — Від «багато» до «безлічі»** | ✅ | 280 | Included in Core |
| **Частина 2: Острів недостатності — Від «мало» до «декількох»** | ✅ | 253 | Included in Core |
| **Частина 3: Параметри вимірювання та Аналіз обсягів у професійній мові** | ✅ | 166 | Included in Core |
| **Частина 4: Кількість у дзеркалі української історії та культури** | ✅ | 135 | Included in Core |
| **Частина 5: Фразеологізми про кількість** | ✅ | 198 | Included in Core |
| **Вживання у контексті** | ✅ | 141 | Included in Core |
| **Частина 6: Психологія сприйняття кількості та баланс у житті** | ✅ | 138 | Included in Core |
| **Частина 7: Формування культури свідомого достатку** | ✅ | 144 | Included in Core |
| **Підсумок** | ✅ | 52 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |
