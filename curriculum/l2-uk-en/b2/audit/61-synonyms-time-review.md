# Audit Report: M61 — 61-synonyms-time.md
**Level:** B2 | **Module:** M61 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:31:48

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
| 1 | match-up | Знайдіть часовий відтінок | 12 | 8 | ✅ |
| 2 | quiz | Точність моменту | 8 | 8 | ✅ |
| 3 | group-sort | Шкала часу | 21 | 14 | ✅ |
| 4 | unjumble | Складіть часове речення | 8 | 6 | ✅ |
| 5 | cloze | Ритм історії | 24 | 14 | ✅ |
| 6 | fill-in | Оберіть часову одиницю | 10 | 8 | ✅ |
| 7 | error-correction | Виправте час | 8 | 6 | ✅ |
| 8 | translate | Переклад термінів часу | 8 | 6 | ✅ |
| 9 | true-false | Нюанси тривалості | 8 | 8 | ✅ |
| 10 | select | Теперішній час | 6 | 6 | ✅ |
| 11 | match-up | Регістри та Час | 12 | 8 | ✅ |
| 12 | match-up | Час та Події | 12 | 8 | ✅ |
| 13 | quiz | Час у мистецтві | 8 | 8 | ✅ |
| 14 | select | Масштаби часу | 6 | 6 | ✅ |
| 15 | essay-response | Творче завдання: Мій час | 1 | 1 | ✅ |
| 16 | reading | Текст для аналізу: Синоніми: Час та Періоди | 3 | 3 | ✅ |

**Summary:**
- Total activities: 16 (target: 10-14) ❌
- Unique types: 12 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Required types used: 3/3 (fill-in, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: Schema validation error at key '13': {'type': 'select', 'title': 'Масштаби часу', 'instruction': 'Оберіть усі слова, що описують великі часові проміжки (6 елементів).', 'items': [{'question': 'Які терміни позначають історію та вічність? (Оберіть 6)', 'options': [{'text': 'епоха', 'correct': True}, {'text': 'ера', 'correct': True}, {'text': 'століття', 'correct': True}, {'text': 'тисячоліття', 'correct': True}, {'text': 'вічність', 'correct': True}, {'text': 'період', 'correct': True}]}, {'question': 'Оберіть одиниці виміру часу:', 'options': [{'text': 'година', 'correct': True}, {'text': 'хвилина', 'correct': True}, {'text': 'секунда', 'correct': True}, {'text': 'метр', 'correct': False}]}, {'question': 'Які слова описують минуле?', 'options': [{'text': 'колись', 'correct': True}, {'text': 'раніше', 'correct': True}, {'text': 'вчора', 'correct': True}, {'text': 'завтра', 'correct': False}]}, {'question': 'Оберіть характеристики майбутнього:', 'options': [{'text': 'прийдешній', 'correct': True}, {'text': 'наступний', 'correct': True}, {'text': 'майбутній', 'correct': True}, {'text': 'минулий', 'correct': False}]}, {'question': 'Які слова вказують на швидкість?', 'options': [{'text': 'миттєво', 'correct': True}, {'text': 'швидко', 'correct': True}, {'text': 'стрімко', 'correct': True}, {'text': 'повільно', 'correct': False}]}, {'question': 'Оберіть слова, що позначають тривалість:', 'options': [{'text': 'протягом', 'correct': True}, {'text': 'упродовж', 'correct': True}, {'text': 'за', 'correct': True}, {'text': 'через', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 2188/2000 (raw: 2288)
- **Activities:** ✅ 16/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 9 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (vocab))
- **Richness:** ✅ 96% (phraseology)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 8 | 4 | 100% | 25% | 25.0% |
| variety | 0.95 | - | 95% | 17% | 15.8% |
| cultural | 4 | - | 100% | 17% | 16.7% |
| visual | 4 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.73 | - | 73% | 8% | 6.1% |
| examples | 51 | - | 100% | 8% | 8.3% |
| realworld | 8 | - | 100% | 8% | 8.3% |
| questions | 6 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **96.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 79 | Included in Core |
| **Розминка — Нюанси часу** | ⚪️ | 487 | Skipped |
| **Now** | ⚪️ | 483 | Skipped |
| **Before** | ⚪️ | 362 | Skipped |
| **Практика — часові вирази в контексті** | ✅ | 765 | Included in Core |
| **Підсумок** | ✅ | 12 | Included in Core |