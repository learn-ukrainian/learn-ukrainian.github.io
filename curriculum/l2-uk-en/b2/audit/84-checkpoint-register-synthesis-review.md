# Audit Report: M84 — 84-checkpoint-register-synthesis.md
**Level:** B2 | **Module:** M84 | **Phase:** B2.4 | **Pedagogy:** Test | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:50:46

## Configuration
**Type:** B2-checkpoint
**Word Target:** 2000 words
**Activities:** 15-19 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** cloze, error-correction, fill-in, quiz
**Required Types:** essay-response, reading, true-false
**Engagement:** ≥4 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥10 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Читання: Розуміння тексту | 10 | 8 | ✅ |
| 2 | quiz | Аудіювання (Симуляція) | 10 | 8 | ✅ |
| 3 | quiz | Граматика: Пасив | 10 | 8 | ✅ |
| 4 | quiz | Граматика: Дієприкметники | 10 | 8 | ✅ |
| 5 | fill-in | Граматика: Вид дієслова | 10 | 8 | ✅ |
| 6 | fill-in | Граматика: Рух | 8 | 8 | ✅ |
| 7 | fill-in | Граматика: Відмінки | 8 | 8 | ✅ |
| 8 | match-up | Лексика: Синоніми | 12 | 8 | ✅ |
| 9 | match-up | Лексика: Ідіоми | 12 | 8 | ✅ |
| 10 | quiz | Лексика: Визначення | 8 | 8 | ✅ |
| 11 | match-up | Історія: Дати | 12 | 8 | ✅ |
| 12 | quiz | Культура: Факти | 8 | 8 | ✅ |
| 13 | group-sort | Письмо: Структура есе | 14 | 14 | ✅ |
| 14 | group-sort | Письмо: Стилі та Реєстри | 15 | 14 | ✅ |
| 15 | quiz | Говоріння (Симуляція) | 8 | 8 | ✅ |
| 16 | error-correction | Виправлення помилок (B2 Final Exam) | 8 | 6 | ✅ |
| 17 | cloze | Філософія вивчення мови | 16 | 14 | ✅ |
| 18 | translate | Фрази для дискусій та дебатів | 6 | 6 | ✅ |
| 19 | select | Вибір правильного дієслова руху | 8 | 6 | ✅ |
| 20 | match-up | Антоніми та відтінки значень | 12 | 8 | ✅ |
| 21 | essay-response | Фінальний звіт: Моє бачення майбутнього України | 1 | 1 | ✅ |
| 22 | reading | Текст для аналізу: Checkpoint: Register Synthesis (Синтез регістрів) | 3 | 3 | ✅ |
| 23 | true-false | Правда чи хибність: Checkpoint: Register Synthesis (Синтез регістрів) | 8 | 8 | ✅ |

**Summary:**
- Total activities: 23 (target: 15-19) ❌
- Unique types: 11 (minimum: 4) ✅
- Priority types used: 4/4 (cloze, error-correction, fill-in, quiz) ✅
- Required types used: 3/3 (essay-response, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 84-checkpoint-register-synthesis.yaml: Schema validation error at key '22': {'type': 'true-false', 'title': 'Правда чи хибність: Checkpoint: Register Synthesis (Синтез регістрів)', 'items': [{'statement': 'Ця тема є важливою для рівня B2.', 'correct': True, 'explanation': 'Так, це є частиною програми B2.'}, {'statement': 'Цей матеріал не потрібен для професійного спілкування.', 'correct': False, 'explanation': 'Навпаки, цей матеріал є необхідним для професійного рівня.'}, {'statement': 'Вивчення цієї теми допомагає розуміти складні тексти.', 'correct': True, 'explanation': 'Правильно, це розширює комунікативну компетенцію.'}, {'statement': 'Ці конструкції використовуються тільки в розмовній мові.', 'correct': False, 'explanation': 'Вони використовуються в різних стилях мовлення.'}, {'statement': 'Для рівня B2 важливо розуміти різні регістри мови.', 'correct': True, 'explanation': 'Так, це є однією з ключових компетенцій B2.'}, {'statement': 'Цю тему можна вивчити без практики.', 'correct': False, 'explanation': 'Практика є необхідною для закріплення матеріалу.'}, {'statement': 'Знання цього матеріалу допомагає на іспиті B2.', 'correct': True, 'explanation': 'Так, це є частиною іспитових завдань.'}, {'statement': 'Ці конструкції існують тільки в українській мові.', 'correct': False, 'explanation': 'Подібні конструкції є в багатьох мовах, але з особливостями.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ❌ 1807/2000 (raw: 1984)
- **Activities:** ✅ 23/15
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/4
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 5 < 10 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 23 (target 15-19)
- **Immersion:** 🇺🇦 99.8% (checkpoint - no gate)
- **Richness:** ✅ 98% (checkpoint)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 98% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 11 | 8 | 100% | 25% | 25.0% |
| review_sections | 25 | 3 | 100% | 20% | 20.0% |
| variety | 0.91 | - | 91% | 15% | 13.7% |
| engagement | 6 | 3 | 100% | 10% | 10.0% |
| cultural | 2 | - | 100% | 10% | 10.0% |
| visual | 10 | 3 | 100% | 10% | 10.0% |
| paragraph_var | 1.00 | - | 100% | 10% | 10.0% |
| **TOTAL** | | | | | **98.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 52 | Included in Core |
| **Огляд — Контрольна точка** | ⚪️ | 84 | Skipped |
| **Навичка 1: Офіційно-діловий регістр** | ⚪️ | 54 | Skipped |
| **Навичка 2: Публіцистичний регістр** | ⚪️ | 285 | Skipped |
| **Навичка 3: Науковий регістр** | ⚪️ | 269 | Skipped |
| **Навичка 4: Перемикання регістрів** | ⚪️ | 320 | Skipped |
| **Навичка 5: Інтеграція регістрів у письмі** | ⚪️ | 253 | Skipped |
| **Підсумок та результати** | ✅ | 490 | Included in Core |