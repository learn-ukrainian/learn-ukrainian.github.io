# Audit Report: M59 — 59-synonyms-communication.md
**Level:** B2 | **Module:** M59 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 1750
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:23:40

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
| 1 | match-up | Знайдіть контекст мовлення | 12 | 8 | ✅ |
| 2 | quiz | Оберіть точне дієслово | 8 | 8 | ✅ |
| 3 | group-sort | Рівень офіційності | 18 | 14 | ✅ |
| 4 | unjumble | Складіть речення про діалог | 8 | 6 | ✅ |
| 5 | cloze | Конференція в столиці | 18 | 14 | ✅ |
| 6 | fill-in | Точність запитання | 10 | 8 | ✅ |
| 7 | error-correction | Виправте помилки комунікації | 8 | 6 | ✅ |
| 8 | translate | Переклад спілкування | 8 | 6 | ✅ |
| 9 | true-false | Нюанси діалогу | 8 | 8 | ✅ |
| 10 | select | Всі форми повідомлення | 6 | 6 | ✅ |
| 11 | match-up | Спілкування та Регістри | 12 | 8 | ✅ |
| 12 | match-up | Антоніми спілкування | 12 | 8 | ✅ |
| 13 | quiz | Метафоричне слово | 8 | 8 | ✅ |
| 14 | essay-response | Творче завдання: Сила слова | 1 | 1 | ✅ |
| 15 | select | Професійна комунікація | 6 | 6 | ✅ |

**Summary:**
- Total activities: 15 (target: 10-14) ❌
- Unique types: 11 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 59-synonyms-communication.yaml: Schema validation error at key '14': {'type': 'select', 'title': 'Професійна комунікація', 'instruction': 'Оберіть слова, які доречні в ділових переговорах.', 'items': [{'question': 'Яка лексика пасує для офіційних зустрічей?', 'options': [{'text': 'пропонувати', 'correct': True}, {'text': 'узгоджувати', 'correct': True}, {'text': 'базікати', 'correct': False}, {'text': 'підтверджувати', 'correct': True}, {'text': 'теревенити', 'correct': False}, {'text': 'резюмувати', 'correct': True}]}, {'question': 'Оберіть дієслова для підбиття підсумків:', 'options': [{'text': 'резюмувати', 'correct': True}, {'text': 'підсумовувати', 'correct': True}, {'text': 'базікати', 'correct': False}, {'text': 'висновувати', 'correct': True}]}, {'question': 'Які слова описують процес переконання?', 'options': [{'text': 'аргументувати', 'correct': True}, {'text': 'переконувати', 'correct': True}, {'text': 'обґрунтовувати', 'correct': True}, {'text': 'мовчати', 'correct': False}]}, {'question': 'Оберіть терміни для ділового спілкування:', 'options': [{'text': 'порядок денний', 'correct': True}, {'text': 'протокол', 'correct': True}, {'text': 'регламент', 'correct': True}, {'text': 'плітки', 'correct': False}]}, {'question': 'Які дієслова вказують на офіційне повідомлення?', 'options': [{'text': 'сповіщати', 'correct': True}, {'text': 'інформувати', 'correct': True}, {'text': 'повідомляти', 'correct': True}, {'text': 'шепотіти', 'correct': False}]}, {'question': 'Оберіть форми офіційного звернення:', 'options': [{'text': 'запит', 'correct': True}, {'text': 'заява', 'correct': True}, {'text': 'клопотання', 'correct': True}, {'text': 'балачка', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 1756/1750 (raw: 1921)
- **Activities:** ✅ 15/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 4 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (vocab))
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
| variety | 0.97 | - | 97% | 17% | 16.2% |
| cultural | 4 | - | 100% | 17% | 16.7% |
| visual | 6 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.94 | - | 94% | 8% | 7.8% |
| examples | 31 | - | 100% | 8% | 8.3% |
| realworld | 7 | - | 100% | 8% | 8.3% |
| questions | 8 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **99.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ** | ✅ | 143 | Included in Core |
| **Фразеологізми та синоніми: Передача інформації** | ⚪️ | 516 | Skipped |
| **Культурний код: Форми української комунікації** | ✅ | 200 | Included in Core |
| **Вживання у контексті: Тон, Регістр та Цифровий світ** | ✅ | 233 | Included in Core |
| **Психологія спілкування та Емоційний інтелект** | ⚪️ | 178 | Skipped |
| **Комунікація в історії та літературі** | ⚪️ | 236 | Skipped |
| **Підсумок** | ✅ | 53 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |