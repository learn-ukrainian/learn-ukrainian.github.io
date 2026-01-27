# Audit Report: M58 — 58-synonyms-quality.md

**Level:** B2 | **Module:** M58 | **Phase:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:28:24

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
| 1 | match-up | Знайдіть відповідність (Якість) | 12 | 8 | ✅ |
| 2 | quiz | Оберіть точну оцінку | 8 | 8 | ✅ |
| 3 | group-sort | Градація оцінки | 18 | 14 | ✅ |
| 4 | unjumble | Складіть оцінне речення | 8 | 6 | ✅ |
| 5 | cloze | Відгук про поїздку | 19 | 14 | ✅ |
| 6 | fill-in | Оберіть критерій | 10 | 8 | ✅ |
| 7 | error-correction | Виправте оцінку | 8 | 6 | ✅ |
| 8 | translate | Переклад якості | 8 | 6 | ✅ |
| 9 | true-false | Нюанси оцінки | 8 | 8 | ✅ |
| 10 | select | Всі відтінки досконалості | 6 | 6 | ✅ |
| 11 | match-up | Регістри та Оцінки | 12 | 8 | ✅ |
| 12 | match-up | Антоніми якості | 12 | 8 | ✅ |
| 13 | quiz | Метафорична якість | 8 | 8 | ✅ |
| 14 | essay-response | Творче завдання: Мистецтво оцінки | 1 | 1 | ✅ |
| 15 | select | Соціальна оцінка | 6 | 6 | ✅ |

**Summary:**
- Total activities: 15 (target: 10-14) ❌
- Unique types: 11 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in 58-synonyms-quality.yaml: Schema validation error at key '14': {'type': 'select', 'title': 'Соціальна оцінка', 'instruction': 'Оберіть слова, які описують соціальну значущість явища або людини.', 'items': [{'question': 'Яка лексика вказує на вагу в суспільстві?', 'options': [{'text': 'впливовий', 'correct': True}, {'text': 'авторитетний', 'correct': True}, {'text': 'незначний', 'correct': True}, {'text': 'пересічний', 'correct': True}, {'text': 'видатний', 'correct': True}, {'text': "дріб'язковий", 'correct': True}]}, {'question': "Оберіть синоніми до слова 'відомий':", 'options': [{'text': 'знаменитий', 'correct': True}, {'text': 'публічний', 'correct': True}, {'text': 'популярний', 'correct': True}, {'text': 'таємний', 'correct': False}]}, {'question': 'Які слова описують професійне визнання?', 'options': [{'text': 'кваліфікований', 'correct': True}, {'text': 'досвідчений', 'correct': True}, {'text': 'дилетантський', 'correct': False}, {'text': 'майстерний', 'correct': True}]}, {'question': "Оберіть антоніми до слова 'видатний':", 'options': [{'text': 'пересічний', 'correct': True}, {'text': 'непомітний', 'correct': True}, {'text': 'геніальний', 'correct': False}, {'text': 'звичайний', 'correct': True}]}, {'question': 'Слова для опису етичної якості лідера:', 'options': [{'text': 'справедливий', 'correct': True}, {'text': 'чесний', 'correct': True}, {'text': 'корумпований', 'correct': False}, {'text': 'відповідальний', 'correct': True}]}, {'question': 'Які терміни вказують на високий стандарт якості?', 'options': [{'text': 'еталонний', 'correct': True}, {'text': 'взірцевий', 'correct': True}, {'text': 'посередній', 'correct': False}, {'text': 'зразковий', 'correct': True}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation

**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates

- **Words:** ✅ 1777/1750 (raw: 1981)
- **Activities:** ✅ 15/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 3 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (vocab))
- **Richness:** ❌ 84% < 95% min (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details

**Score:** 84% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 40 | 24 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| dialogues | 0 | 4 | 0% | 15% | 0.0% |
| variety | 0.99 | - | 99% | 10% | 9.9% |
| cultural | 9 | 3 | 100% | 10% | 10.0% |
| realworld | 10 | 3 | 100% | 10% | 10.0% |
| visual | 4 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.89 | - | 89% | 5% | 4.5% |
| questions | 5 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **84.4%** |

### Dryness Flags & Fixes

- ❌ **NO_DIALOGUE**
  - FIX:
    Add 4+ mini-dialogues. Use this exact format:

    **Діалог: [Location in Ukraine]**

    > — [Speaker 1 line with **bolded** grammar examples]
    > — [Speaker 2 response with **bolded** grammar examples]
    > — [Speaker 1 continuation]
    > — [Speaker 2 conclusion]

    Example locations: На Бесарабському ринку, У львівській кав'ярні, В одеському трамваї, На Подолі

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 71 | Included in Core |
| **Вступ** | ✅ | 126 | Included in Core |
| **Фразеологізми та синоніми: Світло позитиву** | ⚪️ | 254 | Skipped |
| **Частина 2: Тіні негативу — Від «поганого» до «жахливого»** | ✅ | 219 | Included in Core |
| **Частина 3: Критерії та Стандарти оцінки** | ✅ | 98 | Included in Core |
| **Частина 4: Якість у дзеркалі української літератури** | ✅ | 102 | Included in Core |
| **Вживання у контексті** | ✅ | 109 | Included in Core |
| **Психологія та емоційний інтелект** | ⚪️ | 333 | Skipped |
| **Частина 7: Динаміка змінної якості у глобальному світі** | ✅ | 129 | Included in Core |
| **Частина 8: Репутація та соціальна оцінка** | ✅ | 96 | Included in Core |
| **Частина 9: Самооцінка та внутрішній стандарт** | ✅ | 78 | Included in Core |
| **Підсумок** | ✅ | 52 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |
