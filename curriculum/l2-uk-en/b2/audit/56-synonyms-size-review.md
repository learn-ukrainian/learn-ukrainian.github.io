# Audit Report: M56 — 56-synonyms-size.md
**Level:** B2 | **Module:** M56 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-30 21:17:50

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
| 1 | match-up | Знайдіть відповідність | 12 | 8 | ✅ |
| 2 | quiz | Оберіть точний синонім | 8 | 8 | ✅ |
| 3 | group-sort | Велике, Мале чи Параметр? | 19 | 14 | ✅ |
| 4 | unjumble | Складіть речення про масштаб | 8 | 6 | ✅ |
| 5 | cloze | Масштаб української столиці | 17 | 14 | ✅ |
| 6 | fill-in | Виберіть найкращий параметр | 10 | 8 | ✅ |
| 7 | error-correction | Виправте масштабні помилки | 8 | 6 | ✅ |
| 8 | translate | Переклад масштабу | 8 | 6 | ✅ |
| 9 | true-false | Нюанси розміру | 8 | 8 | ✅ |
| 10 | select | Всі варіанти великого | 6 | 6 | ✅ |
| 11 | match-up | Регістри та розміри | 12 | 8 | ✅ |
| 12 | match-up | Параметри та об'єкти | 12 | 8 | ✅ |
| 13 | quiz | Ранжування інтенсивності | 8 | 8 | ✅ |
| 14 | essay-response | Творче завдання: Світ масштабів | 1 | 1 | ✅ |
| 15 | select | Переносне значення | 6 | 6 | ✅ |

**Summary:**
- Total activities: 15 (target: 10-14) ❌
- Unique types: 11 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Required types used: 1/3 (true-false) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[INVALID_ACTIVITY_TYPE]** Invalid activity types in activity_hints: ['fill-in-the-blank']. Valid types: ['match-up', 'fill-in', 'quiz', 'true-false', 'group-sort', 'unjumble', 'error-correction', 'anagram', 'select', 'translate', 'cloze', 'mark-the-words', 'reading', 'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent']
  - FIX: Replace invalid types with valid ones from: match-up, fill-in, quiz, true-false, group-sort, unjumble, error-correction, anagram, select, translate, cloze, mark-the-words, reading, essay-response, critical-analysis, comparative-study, authorial-intent
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-synonyms-size.yaml: Schema validation error at key '14': {'type': 'select', 'title': 'Переносне значення', 'instruction': 'Оберіть випадки, де слова розміру вжиті в переносному значенні (6+ елементів).', 'items': [{'question': 'Де розмір став якістю людини або явища?', 'options': [{'text': 'велика людина', 'correct': True}, {'text': 'широка душа', 'correct': True}, {'text': 'дрібний характер', 'correct': True}, {'text': 'високий будинок', 'correct': False}]}, {'question': 'Які вирази описують інтелектуальний рівень?', 'options': [{'text': 'глибокі знання', 'correct': True}, {'text': 'мілке мислення', 'correct': True}, {'text': 'товста стіна', 'correct': False}, {'text': 'широка дорога', 'correct': False}]}, {'question': 'Оберіть метафори делікатності:', 'options': [{'text': 'тонкий натяк', 'correct': True}, {'text': 'тонкий гумор', 'correct': True}, {'text': 'груба сила', 'correct': False}, {'text': 'товста книга', 'correct': False}]}, {'question': 'Які слова описують соціальну значущість?', 'options': [{'text': 'велика подія', 'correct': True}, {'text': 'незначна особа', 'correct': True}, {'text': 'дрібна справа', 'correct': True}, {'text': 'високий паркан', 'correct': False}]}, {'question': 'Оберіть вирази про обмеженість:', 'options': [{'text': 'вузьке коло', 'correct': True}, {'text': "тісні зв'язки", 'correct': False}, {'text': 'обмежені ресурси', 'correct': True}, {'text': 'широкий простір', 'correct': False}]}, {'question': 'Які слова передають інтенсивність зусиль?', 'options': [{'text': 'колосальна праця', 'correct': True}, {'text': 'величезна відповідальність', 'correct': True}, {'text': 'малий крок', 'correct': False}, {'text': 'дрібний дощ', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ❌ 1835/2000 (raw: 2010)
- **Activities:** ✅ 15/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 6 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.3% (target 90-100% (vocab))
- **Richness:** ✅ 99% (phraseology)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 7 | 4 | 100% | 25% | 25.0% |
| variety | 0.99 | - | 99% | 17% | 16.5% |
| cultural | 5 | - | 100% | 17% | 16.7% |
| visual | 4 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 1.00 | - | 100% | 8% | 8.3% |
| examples | 33 | - | 100% | 8% | 8.3% |
| realworld | 5 | - | 100% | 8% | 8.3% |
| questions | 7 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 83 | Included in Core |
| **Вступ** | ✅ | 161 | Included in Core |
| **Фразеологізми та синоніми розміру** | ⚪️ | 622 | Skipped |
| **Культурний код: Параметри та виміри в українському світогляді** | ✅ | 292 | Included in Core |
| **Мистецтво порівняння та гіперболи в літературі** | ⚪️ | 109 | Skipped |
| **Вживання у контексті: Регістр та Стиль** | ✅ | 175 | Included in Core |
| **Індустріальний масштаб та сучасна урбаністика** | ⚪️ | 211 | Skipped |
| **Підсумок** | ✅ | 72 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |