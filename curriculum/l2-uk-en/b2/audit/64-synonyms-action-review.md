# Audit Report: M64 — 64-synonyms-action.md
**Level:** B2 | **Module:** M64 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:31:51

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
| 1 | match-up | Знайдіть характер дії | 12 | 8 | ✅ |
| 2 | quiz | Оберіть точну дію | 8 | 8 | ✅ |
| 3 | group-sort | Дія чи Результат? | 20 | 14 | ✅ |
| 4 | unjumble | Складіть дієве речення | 8 | 6 | ✅ |
| 5 | cloze | Проєкт перетворення | 18 | 14 | ✅ |
| 6 | fill-in | Професійне дієслово | 10 | 8 | ✅ |
| 7 | error-correction | Виправте вчинок | 8 | 6 | ✅ |
| 8 | translate | Переклад дії | 8 | 6 | ✅ |
| 9 | true-false | Нюанси чину | 8 | 8 | ✅ |
| 10 | select | Всі форми активності | 6 | 6 | ✅ |
| 11 | match-up | Дія та Регістри | 12 | 8 | ✅ |
| 12 | match-up | Дія та Її Об'єкт | 12 | 8 | ✅ |
| 13 | quiz | Філософія чину | 8 | 8 | ✅ |
| 14 | select | Творча та Технічна Дія | 6 | 6 | ✅ |
| 15 | essay-response | Творче завдання: Людина дії | 1 | 1 | ✅ |
| 16 | reading | Текст для аналізу: Синоніми: Дія та Перетворення | 3 | 3 | ✅ |

**Summary:**
- Total activities: 16 (target: 10-14) ❌
- Unique types: 12 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Required types used: 3/3 (fill-in, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: Schema validation error at key '13': {'type': 'select', 'title': 'Творча та Технічна Дія', 'instruction': 'Оберіть усі слова, що описують складні та інноваційні процеси (6 елементів).', 'items': [{'question': 'Які терміни вказують на модернізацію та розвиток? (Оберіть 6)', 'options': [{'text': 'модернізувати', 'correct': True}, {'text': 'оптимізувати', 'correct': True}, {'text': 'інтегрувати', 'correct': True}, {'text': 'впроваджувати', 'correct': True}, {'text': 'трансформувати', 'correct': True}, {'text': 'удосконалювати', 'correct': True}]}, {'question': "Оберіть синоніми до слова 'створювати':", 'options': [{'text': 'творити', 'correct': True}, {'text': 'засновувати', 'correct': True}, {'text': 'фундадувати', 'correct': True}, {'text': 'руйнувати', 'correct': False}]}, {'question': "Які слова описують 'швидку реакцію':", 'options': [{'text': 'оперативно', 'correct': True}, {'text': 'негайно', 'correct': True}, {'text': 'миттєво', 'correct': True}, {'text': 'повільно', 'correct': False}]}, {'question': 'Оберіть слова для опису професійної дії:', 'options': [{'text': 'кваліфіковано', 'correct': True}, {'text': 'фахово', 'correct': True}, {'text': 'майстерно', 'correct': True}, {'text': 'абияк', 'correct': False}]}, {'question': "Які слова вказують на 'результативність':", 'options': [{'text': 'ефективно', 'correct': True}, {'text': 'продуктивно', 'correct': True}, {'text': 'успішно', 'correct': True}, {'text': 'марно', 'correct': False}]}, {'question': "Оберіть назви 'творчих процесів':", 'options': [{'text': 'натхнення', 'correct': True}, {'text': 'візуалізація', 'correct': True}, {'text': 'репетиція', 'correct': True}, {'text': 'рутина', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 2192/2000 (raw: 2280)
- **Activities:** ✅ 16/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 14 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (vocab))
- **Richness:** ✅ 97% (phraseology)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 9 | 4 | 100% | 25% | 25.0% |
| variety | 0.96 | - | 96% | 17% | 16.0% |
| cultural | 3 | - | 100% | 17% | 16.7% |
| visual | 6 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.80 | - | 80% | 8% | 6.7% |
| examples | 67 | - | 100% | 8% | 8.3% |
| realworld | 8 | - | 100% | 8% | 8.3% |
| questions | 9 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **97.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Розминка — Що значить "робити"?** | ⚪️ | 695 | Skipped |
| **Do/Make** | ⚪️ | 543 | Skipped |
| **Take** | ⚪️ | 408 | Skipped |
| **Практика — дієслова дії** | ⚪️ | 447 | Skipped |
| **Підсумок** | ✅ | 12 | Included in Core |