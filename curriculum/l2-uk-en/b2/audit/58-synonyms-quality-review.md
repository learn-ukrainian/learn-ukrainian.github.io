# Audit Report: M58 — 58-synonyms-quality.md
**Level:** B2 | **Module:** M58 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:35:31

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
| 16 | reading | Текст для аналізу: Синоніми: Якість та Оцінка | 3 | 3 | ✅ |

**Summary:**
- Total activities: 16 (target: 10-14) ❌
- Unique types: 12 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Required types used: 3/3 (fill-in, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 58-synonyms-quality.yaml: Schema validation error at key '14': {'type': 'select', 'title': 'Соціальна оцінка', 'instruction': 'Оберіть слова, які описують соціальну значущість явища або людини.', 'items': [{'question': 'Яка лексика вказує на вагу в суспільстві?', 'options': [{'text': 'впливовий', 'correct': True}, {'text': 'авторитетний', 'correct': True}, {'text': 'незначний', 'correct': True}, {'text': 'пересічний', 'correct': True}, {'text': 'видатний', 'correct': True}, {'text': "дріб'язковий", 'correct': True}]}, {'question': "Оберіть синоніми до слова 'відомий':", 'options': [{'text': 'знаменитий', 'correct': True}, {'text': 'публічний', 'correct': True}, {'text': 'популярний', 'correct': True}, {'text': 'таємний', 'correct': False}]}, {'question': 'Які слова описують професійне визнання?', 'options': [{'text': 'кваліфікований', 'correct': True}, {'text': 'досвідчений', 'correct': True}, {'text': 'дилетантський', 'correct': False}, {'text': 'майстерний', 'correct': True}]}, {'question': "Оберіть антоніми до слова 'видатний':", 'options': [{'text': 'пересічний', 'correct': True}, {'text': 'непомітний', 'correct': True}, {'text': 'геніальний', 'correct': False}, {'text': 'звичайний', 'correct': True}]}, {'question': 'Слова для опису етичної якості лідера:', 'options': [{'text': 'справедливий', 'correct': True}, {'text': 'чесний', 'correct': True}, {'text': 'корумпований', 'correct': False}, {'text': 'відповідальний', 'correct': True}]}, {'question': 'Які терміни вказують на високий стандарт якості?', 'options': [{'text': 'еталонний', 'correct': True}, {'text': 'взірцевий', 'correct': True}, {'text': 'посередній', 'correct': False}, {'text': 'зразковий', 'correct': True}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ❌ 1789/2000 (raw: 1940)
- **Activities:** ✅ 16/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 3 < 35 (soft target)
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
| engagement | 9 | 4 | 100% | 25% | 25.0% |
| variety | 0.98 | - | 98% | 17% | 16.3% |
| cultural | 9 | - | 100% | 17% | 16.7% |
| visual | 4 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.85 | - | 85% | 8% | 7.1% |
| examples | 53 | - | 100% | 8% | 8.3% |
| realworld | 10 | - | 100% | 8% | 8.3% |
| questions | 5 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **98.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 71 | Included in Core |
| **Розминка — Добре чи погано?** | ⚪️ | 380 | Skipped |
| **Good** | ⚪️ | 419 | Skipped |
| **Bad** | ⚪️ | 571 | Skipped |
| **Практика — оцінювання в тексті** | ✅ | 336 | Included in Core |
| **Підсумок** | ✅ | 12 | Included in Core |