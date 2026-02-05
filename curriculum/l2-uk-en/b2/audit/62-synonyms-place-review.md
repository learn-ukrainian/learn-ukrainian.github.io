# Audit Report: M62 — 62-synonyms-place.md
**Level:** B2 | **Module:** M62 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:31:49

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
| 1 | match-up | Знайдіть місце | 12 | 8 | ✅ |
| 2 | quiz | Орієнтування у просторі | 8 | 8 | ✅ |
| 3 | group-sort | Статика чи Напрямок? | 20 | 14 | ✅ |
| 4 | unjumble | Складіть просторове речення | 8 | 6 | ✅ |
| 5 | cloze | Шлях мандрівника | 23 | 14 | ✅ |
| 6 | fill-in | Оберіть масштаб простору | 10 | 8 | ✅ |
| 7 | error-correction | Виправте місце | 8 | 6 | ✅ |
| 8 | translate | Переклад простору | 8 | 6 | ✅ |
| 9 | true-false | Нюанси локацій | 8 | 8 | ✅ |
| 10 | select | Всі форми вказівки | 6 | 6 | ✅ |
| 11 | match-up | Простір та Об'єкти | 12 | 8 | ✅ |
| 12 | match-up | Антоніми простору | 12 | 8 | ✅ |
| 13 | quiz | Простір пам'яті | 8 | 8 | ✅ |
| 14 | select | Типи територій | 6 | 6 | ✅ |
| 15 | essay-response | Творче завдання: Мій простір | 1 | 1 | ✅ |
| 16 | reading | Текст для аналізу: Синоніми: Місце та Простір | 3 | 3 | ✅ |

**Summary:**
- Total activities: 16 (target: 10-14) ❌
- Unique types: 12 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Required types used: 3/3 (fill-in, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'ми бачимо,...'.
  - FIX: Vary sentence structure.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 62-synonyms-place.yaml: Schema validation error at key '13': {'type': 'select', 'title': 'Типи територій', 'instruction': 'Оберіть усі слова, що описують масштабні території (6 елементів).', 'items': [{'question': 'Які терміни вказують на великі простори? (Оберіть 6)', 'options': [{'text': 'область', 'correct': True}, {'text': 'територія', 'correct': True}, {'text': 'регіон', 'correct': True}, {'text': 'зона', 'correct': True}, {'text': 'район', 'correct': True}, {'text': 'країна', 'correct': True}]}, {'question': "Оберіть синоніми до слова 'місце':", 'options': [{'text': 'локація', 'correct': True}, {'text': 'точка', 'correct': True}, {'text': 'осередок', 'correct': True}, {'text': 'мить', 'correct': False}]}, {'question': "Які слова позначають 'кордони':", 'options': [{'text': 'межа', 'correct': True}, {'text': 'край', 'correct': True}, {'text': 'кордон', 'correct': True}, {'text': 'центр', 'correct': False}]}, {'question': 'Оберіть слова для опису міського простору:', 'options': [{'text': 'квартал', 'correct': True}, {'text': 'площа', 'correct': True}, {'text': 'майдан', 'correct': True}, {'text': 'ліс', 'correct': False}]}, {'question': "Які слова вказують на 'віддаленість':", 'options': [{'text': 'далеко', 'correct': True}, {'text': 'вдалині', 'correct': True}, {'text': 'на обрії', 'correct': True}, {'text': 'поруч', 'correct': False}]}, {'question': "Оберіть назви 'водних просторів':", 'options': [{'text': 'акваторія', 'correct': True}, {'text': 'плесо', 'correct': True}, {'text': 'гладь', 'correct': True}, {'text': 'гора', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ✅ 2127/2000 (raw: 2212)
- **Activities:** ✅ 16/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 15 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.0% (target 90-100% (vocab))
- **Richness:** ✅ 97% (phraseology)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 8 | 4 | 100% | 25% | 25.0% |
| variety | 0.95 | - | 95% | 17% | 15.8% |
| cultural | 4 | - | 100% | 17% | 16.7% |
| visual | 5 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.78 | - | 78% | 8% | 6.5% |
| examples | 53 | - | 100% | 8% | 8.3% |
| realworld | 4 | - | 100% | 8% | 8.3% |
| questions | 15 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **97.3%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Розминка — Де і куди?** | ⚪️ | 435 | Skipped |
| **Here** | ⚪️ | 598 | Skipped |
| **There** | ⚪️ | 497 | Skipped |
| **Практика — просторовий опис** | ⚪️ | 498 | Skipped |
| **Підсумок** | ✅ | 12 | Included in Core |