# Audit Report: M92 — zunr.md
**Level:** B2 | **Module:** M92 | **Phase:** B2 | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 22:23:22

## Configuration
**Type:** B2-history
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥2 types required
**Priority Types:** comparative-study, critical-analysis, essay-response, reading
**Required Types:** essay-response, reading
**Engagement:** ≥5 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥20 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Факти про Революцію | 8 | 8 | ✅ |
| 2 | match-up | Чотири Універсали | 12 | 8 | ✅ |
| 3 | cloze | Акт Злуки | 18 | 1 | ✅ |
| 4 | match-up | Хронологія подій | 12 | 8 | ✅ |
| 5 | true-false | Правда чи міф? | 8 | 8 | ✅ |
| 6 | group-sort | Політики, війська та вороги | 20 | 1 | ✅ |
| 7 | select | Синоніми та визначення | 6 | 6 | ✅ |
| 8 | mark-the-words | Знайдіть політичні терміни | 10 | 6 | ✅ |
| 9 | cloze | Граматика: Пасивний стан (Revision) | 16 | 1 | ✅ |
| 10 | match-up | Словник: Визначення | 12 | 8 | ✅ |
| 11 | quiz | Підсумок | 8 | 8 | ✅ |
| 12 | match-up | Географія Революції | 12 | 8 | ✅ |
| 13 | essay-response | Есей: Уроки УНР | 1 | 1 | ✅ |
| 14 | comparative-study | Порівняння: УНР і ЗУНР | 1 | 1 | ✅ |

**Summary:**
- Total activities: 14 (target: 3-9) ❌
- Unique types: 9 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in zunr.yaml: Schema validation error at key '6': {'type': 'select', 'title': 'Синоніми та визначення', 'instruction': 'Оберіть правильний варіант.', 'items': [{'question': "Синонім до слова 'Держава':", 'options': [{'text': 'Країна', 'correct': True}, {'text': 'Місто', 'correct': False}, {'text': 'Село', 'correct': False}, {'text': 'Вулиця', 'correct': False}]}, {'question': "Синонім до слова 'Злука':", 'options': [{'text': "Об'єднання", 'correct': True}, {'text': 'Війна', 'correct': False}, {'text': 'Сварка', 'correct': False}, {'text': 'Розподіл', 'correct': False}]}, {'question': "Синонім до слова 'Боротьба':", 'options': [{'text': 'Битва', 'correct': True}, {'text': 'Сон', 'correct': False}, {'text': 'Обід', 'correct': False}, {'text': 'Гра', 'correct': False}]}, {'question': "Що таке 'Автономія'?", 'options': [{'text': 'Самоврядування', 'correct': True}, {'text': 'Повна залежність', 'correct': False}, {'text': 'Рабство', 'correct': False}, {'text': 'Диктатура', 'correct': False}]}, {'question': "Що таке 'Суверенітет'?", 'options': [{'text': 'Незалежність влади', 'correct': True}, {'text': 'Багатство', 'correct': False}, {'text': 'Велике військо', 'correct': False}, {'text': 'Красивий прапор', 'correct': False}]}, {'question': "Що таке 'Дипломатія'?", 'options': [{'text': 'Переговори', 'correct': True}, {'text': 'Війна', 'correct': False}, {'text': 'Торгівля', 'correct': False}, {'text': 'Спорт', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2113/4000 (raw: 2276)
- **Activities:** ✅ 14/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 9/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 14 (target 3-9); 1 cloze with year blanks
- **Immersion:** 🇺🇦 95.4% (target 90-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 10 | 4 | 100% | 10% | 9.5% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 7 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **УНР і ЗУНР: Мрія про Соборність** | ⚪️ | 0 | Skipped |
| **Вступ** | ✅ | 90 | Included in Core |
| **Чотири Універсали: шлях до свободи** | ⚪️ | 74 | Skipped |
| **Первинні джерела** | ✅ | 25 | Included in Core |
| **Крути: бій за майбутнє** | ⚪️ | 96 | Skipped |
| **Читання** | ✅ | 202 | Included in Core |
| **Гетьманат і Директорія** | ⚪️ | 137 | Skipped |
| **Культурний фронт: Гроші, Тризуб і Щедрик** | ✅ | 195 | Included in Core |
| **Символи держави: Тризуб і Прапор** | ⚪️ | 156 | Skipped |
| **Махновщина: Третя сила** | ⚪️ | 89 | Skipped |
| **Холодний Яр: Фортеця волі** | ⚪️ | 76 | Skipped |
| **Зимові походи: Лицарі абсурду** | ⚪️ | 91 | Skipped |
| **Акт Злуки: об'єднання земель** | ⚪️ | 121 | Skipped |
| **Трагедія «Трикутника смерті»** | ⚪️ | 111 | Skipped |
| **Еміграція: Збереження Держави** | ⚪️ | 131 | Skipped |
| **Деколонізаційний погляд** | ✅ | 58 | Included in Core |
| **Жінки в Революції: Невидимі герої** | ⚪️ | 153 | Skipped |
| **Культура опору: Поезія в окопах** | ✅ | 118 | Included in Core |
| **Підсумок** | ✅ | 80 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |