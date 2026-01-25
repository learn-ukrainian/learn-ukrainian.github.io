# Audit Report: M62 — 62-synonyms-place.md
**Level:** B2 | **Module:** M62 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 1750
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:23:42

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

**Summary:**
- Total activities: 15 (target: 10-14) ❌
- Unique types: 11 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
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
- **Words:** ✅ 2115/1750 (raw: 2329)
- **Activities:** ✅ 15/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
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
| paragraph_var | 0.79 | - | 79% | 8% | 6.6% |
| examples | 54 | - | 100% | 8% | 8.3% |
| realworld | 4 | - | 100% | 8% | 8.3% |
| questions | 15 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **97.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ: Карта українського простору** | ✅ | 97 | Included in Core |
| **Частина 1: Тут і Там — Магія вказівки** | ✅ | 153 | Included in Core |
| **Частина 2: Відстань та Близькість** | ✅ | 79 | Included in Core |
| **Частина 3: Простір та Локації — Від точки до території** | ✅ | 106 | Included in Core |
| **Частина 4: Простір в українській культурі — Шацькі озера** | ✅ | 65 | Included in Core |
| **Частина 5: Фразеологізми про простір** | ✅ | 244 | Included in Core |
| **Вживання у контексті** | ✅ | 155 | Included in Core |
| **Частина 6: Напрямок руху — Від «сюди» до «кудись»** | ✅ | 63 | Included in Core |
| **Частина 7: Простір у цифрову епоху** | ✅ | 71 | Included in Core |
| **Частина 8: Концепція дому в українському світогляді** | ✅ | 100 | Included in Core |
| **Частина 9: Ландшафт як доля — Гори, Степ та Море** | ✅ | 91 | Included in Core |
| **Частина 10: Простір майбутнього — Урбаністика та Екологія** | ✅ | 98 | Included in Core |
| **Частина 11: Простір пам'яті та меморіальна лексика** | ✅ | 208 | Included in Core |
| **Частина 12: Простір у художній візії та мистецтві** | ✅ | 81 | Included in Core |
| **Частина 13: Геометрія українського міста: Від майдану до дворика** | ✅ | 81 | Included in Core |
| **Частина 14: Психологія рідного місця: Дім та Оселя** | ✅ | 96 | Included in Core |
| **Частина 15: Простір як виклик та можливість** | ✅ | 82 | Included in Core |
| **Підсумок** | ✅ | 48 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |