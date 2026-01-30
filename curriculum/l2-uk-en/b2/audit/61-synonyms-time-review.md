# Audit Report: M61 — 61-synonyms-time.md
**Level:** B2 | **Module:** M61 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-30 21:18:17

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

**Summary:**
- Total activities: 15 (target: 10-14) ❌
- Unique types: 11 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Required types used: 1/3 (true-false) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[INVALID_ACTIVITY_TYPE]** Invalid activity types in activity_hints: ['fill-in-the-blank']. Valid types: ['match-up', 'fill-in', 'quiz', 'true-false', 'group-sort', 'unjumble', 'error-correction', 'anagram', 'select', 'translate', 'cloze', 'mark-the-words', 'reading', 'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent']
  - FIX: Replace invalid types with valid ones from: match-up, fill-in, quiz, true-false, group-sort, unjumble, error-correction, anagram, select, translate, cloze, mark-the-words, reading, essay-response, critical-analysis, comparative-study, authorial-intent
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: Schema validation error at key '13': {'type': 'select', 'title': 'Масштаби часу', 'instruction': 'Оберіть усі слова, що описують великі часові проміжки (6 елементів).', 'items': [{'question': 'Які терміни позначають історію та вічність? (Оберіть 6)', 'options': [{'text': 'епоха', 'correct': True}, {'text': 'ера', 'correct': True}, {'text': 'століття', 'correct': True}, {'text': 'тисячоліття', 'correct': True}, {'text': 'вічність', 'correct': True}, {'text': 'період', 'correct': True}]}, {'question': 'Оберіть одиниці виміру часу:', 'options': [{'text': 'година', 'correct': True}, {'text': 'хвилина', 'correct': True}, {'text': 'секунда', 'correct': True}, {'text': 'метр', 'correct': False}]}, {'question': 'Які слова описують минуле?', 'options': [{'text': 'колись', 'correct': True}, {'text': 'раніше', 'correct': True}, {'text': 'вчора', 'correct': True}, {'text': 'завтра', 'correct': False}]}, {'question': 'Оберіть характеристики майбутнього:', 'options': [{'text': 'прийдешній', 'correct': True}, {'text': 'наступний', 'correct': True}, {'text': 'майбутній', 'correct': True}, {'text': 'минулий', 'correct': False}]}, {'question': 'Які слова вказують на швидкість?', 'options': [{'text': 'миттєво', 'correct': True}, {'text': 'швидко', 'correct': True}, {'text': 'стрімко', 'correct': True}, {'text': 'повільно', 'correct': False}]}, {'question': 'Оберіть слова, що позначають тривалість:', 'options': [{'text': 'протягом', 'correct': True}, {'text': 'упродовж', 'correct': True}, {'text': 'за', 'correct': True}, {'text': 'через', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ✅ 2176/2000 (raw: 2393)
- **Activities:** ✅ 15/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 9 < 35 (soft target)
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
| engagement | 8 | 4 | 100% | 25% | 25.0% |
| variety | 0.97 | - | 97% | 17% | 16.2% |
| cultural | 4 | - | 100% | 17% | 16.7% |
| visual | 4 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.75 | - | 75% | 8% | 6.2% |
| examples | 52 | - | 100% | 8% | 8.3% |
| realworld | 8 | - | 100% | 8% | 8.3% |
| questions | 7 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **97.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 79 | Included in Core |
| **Вступ: Плин часу в українському просторі** | ✅ | 86 | Included in Core |
| **Частина 1: Теперішній момент — Від «зараз» до «наразі»** | ✅ | 174 | Included in Core |
| **Частина 2: Минуле — Від «щойно» до «вічності»** | ✅ | 124 | Included in Core |
| **Частина 3: Масштаби часу — Від миті до епохи** | ✅ | 103 | Included in Core |
| **Частина 4: Час в українській культурі — «Розстріляне відродження»** | ✅ | 62 | Included in Core |
| **Частина 5: Фразеологізми про час** | ✅ | 207 | Included in Core |
| **Вживання у контексті** | ✅ | 145 | Included in Core |
| **Частина 6: Майбутнє — Від «завтра» до «згодом»** | ✅ | 69 | Included in Core |
| **Частина 7: Час у цифрову епоху** | ✅ | 80 | Included in Core |
| **Частина 8: Час у народній уяві та обрядах** | ✅ | 86 | Included in Core |
| **Частина 9: Історична пам'ять та тяглість поколінь** | ✅ | 86 | Included in Core |
| **Частина 10: Психологія сприйняття часу** | ✅ | 110 | Included in Core |
| **Частина 11: Час у сучасному мистецтві та медіа** | ✅ | 91 | Included in Core |
| **Частина 12: Майбутнє як простір надії та планування** | ✅ | 259 | Included in Core |
| **Частина 14: Час у науковому пізнанні світу** | ✅ | 97 | Included in Core |
| **Частина 15: Сприйняття часу в різних культурах** | ✅ | 161 | Included in Core |
| **Підсумок** | ✅ | 47 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |