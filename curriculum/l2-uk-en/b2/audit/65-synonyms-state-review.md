# Audit Report: M65 — 65-synonyms-state.md
**Level:** B2 | **Module:** M65 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-30 21:18:05

## Configuration
**Type:** B2-vocab
**Word Target:** 2000 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** mark-the-words, match-up, quiz, translate
**Required Types:** fill-in-the-blank, reading, true-false
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥35 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | match-up | Знайдіть відтінок стану | 12 | 8 | ✅ |
| 2 | quiz | Оберіть точний стан | 8 | 8 | ✅ |
| 3 | group-sort | Об'єктивне чи Суб'єктивне? | 20 | 14 | ✅ |
| 4 | unjumble | Складіть речення про стан | 8 | 6 | ✅ |
| 5 | cloze | Стан речей | 16 | 14 | ✅ |
| 6 | fill-in | Аналітичний стан | 10 | 8 | ✅ |
| 7 | error-correction | Виправте враження | 8 | 6 | ✅ |
| 8 | translate | Переклад стану | 8 | 6 | ✅ |
| 9 | true-false | Нюанси буття | 8 | 8 | ✅ |
| 10 | select | Всі форми існування | 6 | 6 | ✅ |
| 11 | match-up | Стан та Регістри | 12 | 8 | ✅ |
| 12 | match-up | Стан та Чинники | 12 | 8 | ✅ |
| 13 | quiz | Філософія буття | 8 | 8 | ✅ |
| 14 | select | Складні стани | 6 | 6 | ✅ |
| 15 | essay-response | Творче завдання: Стан моєї душі | 1 | 1 | ✅ |

**Summary:**
- Total activities: 15 (target: 10-14) ❌
- Unique types: 11 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Required types used: 1/3 (true-false) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[INVALID_ACTIVITY_TYPE]** Invalid activity types in activity_hints: ['fill-in-the-blank']. Valid types: ['match-up', 'fill-in', 'quiz', 'true-false', 'group-sort', 'unjumble', 'error-correction', 'anagram', 'select', 'translate', 'cloze', 'mark-the-words', 'reading', 'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent']
  - FIX: Replace invalid types with valid ones from: match-up, fill-in, quiz, true-false, group-sort, unjumble, error-correction, anagram, select, translate, cloze, mark-the-words, reading, essay-response, critical-analysis, comparative-study, authorial-intent
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: Schema validation error at key '13': {'type': 'select', 'title': 'Складні стани', 'instruction': 'Оберіть усі слова, що описують стабільність та гармонію (6 елементів).', 'items': [{'question': 'Які терміни вказують на врівноважений стан? (Оберіть 6)', 'options': [{'text': 'стабільність', 'correct': True}, {'text': 'гармонія', 'correct': True}, {'text': 'рівновага', 'correct': True}, {'text': 'спокій', 'correct': True}, {'text': 'впевненість', 'correct': True}, {'text': 'непохитність', 'correct': True}]}, {'question': "Оберіть синоніми до слова 'становище':", 'options': [{'text': 'положення', 'correct': True}, {'text': 'ситуація', 'correct': True}, {'text': 'обставини', 'correct': True}, {'text': 'мить', 'correct': False}]}, {'question': "Які слова описують 'соціальний стан':", 'options': [{'text': 'престиж', 'correct': True}, {'text': 'авторитет', 'correct': True}, {'text': 'репутація', 'correct': True}, {'text': 'вага', 'correct': False}]}, {'question': "Оберіть слова для опису 'здоров'я':", 'options': [{'text': 'самопочуття', 'correct': True}, {'text': 'тонус', 'correct': True}, {'text': 'бадьорість', 'correct': True}, {'text': 'час', 'correct': False}]}, {'question': "Які слова вказують на 'негативний стан':", 'options': [{'text': 'занепад', 'correct': True}, {'text': 'криза', 'correct': True}, {'text': 'деградація', 'correct': True}, {'text': 'розквіт', 'correct': False}]}, {'question': "Оберіть назви 'психологічних станів':", 'options': [{'text': 'стрес', 'correct': True}, {'text': 'тривога', 'correct': True}, {'text': 'апатія', 'correct': True}, {'text': 'чин', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ✅ 2047/2000 (raw: 2235)
- **Activities:** ✅ 15/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 3 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (vocab))
- **Richness:** ✅ 97% (phraseology)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 10 | 4 | 100% | 25% | 25.0% |
| variety | 0.95 | - | 95% | 17% | 15.8% |
| cultural | 7 | - | 100% | 17% | 16.7% |
| visual | 6 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.79 | - | 79% | 8% | 6.6% |
| examples | 65 | - | 100% | 8% | 8.3% |
| realworld | 5 | - | 100% | 8% | 8.3% |
| questions | 10 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **97.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 80 | Included in Core |
| **Вступ: Глибина українського буття** | ✅ | 100 | Included in Core |
| **Частина 1: Бути — Як ми фіксуємо існування** | ✅ | 232 | Included in Core |
| **Частина 2: Здаватися — Світ через призму нашого сприйняття** | ✅ | 156 | Included in Core |
| **Частина 3: Категорії стану — Від умов до середовища в аналізі** | ✅ | 148 | Included in Core |
| **Частина 4: Стан у дзеркалі української літератури та психології** | ✅ | 79 | Included in Core |
| **Частина 5: Фразеологізми про стан** | ✅ | 221 | Included in Core |
| **Вживання у контексті** | ✅ | 150 | Included in Core |
| **Частина 6: Стан у сучасному світі: Стабільність та Криза** | ✅ | 93 | Included in Core |
| **Частина 7: Буття як цінність** | ✅ | 106 | Included in Core |
| **Частина 8: Стан довкілля та Екологічне Буття** | ✅ | 81 | Included in Core |
| **Частина 9: Історичний Стан: Між Минулим та Майбутнім** | ✅ | 84 | Included in Core |
| **Частина 10: Стан у цифровому просторі та Майбутнє Буття** | ✅ | 95 | Included in Core |
| **Частина 11: Стан спокою у містах Суми та Полтава** | ✅ | 79 | Included in Core |
| **Частина 12: Естетичне Буття в Ужгороді** | ✅ | 185 | Included in Core |
| **Підсумок** | ✅ | 48 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |