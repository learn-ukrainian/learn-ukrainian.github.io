# Audit Report: M30 — 30-b21-checkpoint.md
**Level:** B2 | **Module:** M30 | **Phase:** B2.1 | **Pedagogy:** checkpoint | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:11:37

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
| 1 | quiz | Пасивний стан: розпізнавання форм | 16 | 8 | ✅ |
| 2 | match-up | Пасивна форма та типовий регістр | 16 | 8 | ✅ |
| 3 | group-sort | Класифікація пасивних конструкцій | 20 | 14 | ✅ |
| 4 | quiz | Активні дієприкметники: розпізнавання та трансформація | 10 | 8 | ✅ |
| 5 | fill-in | Утворення пасивних дієприкметників | 16 | 8 | ✅ |
| 6 | error-correction | Виправлення помилок у пасивних конструкціях | 12 | 6 | ✅ |
| 7 | quiz | Дієприслівники: утворення та вживання | 10 | 8 | ✅ |
| 8 | unjumble | Побудова складних речень | 16 | 6 | ✅ |
| 9 | group-sort | Класифікація за функціональними стилями | 25 | 14 | ✅ |
| 10 | match-up | Доменна лексика та переклад | 16 | 8 | ✅ |
| 11 | cloze | Доменна лексика у контексті | 16 | 14 | ✅ |
| 12 | cloze | Інтеграційний текст про реформу | 16 | 14 | ✅ |
| 13 | quiz | Вставні слова та конектори | 10 | 8 | ✅ |
| 14 | true-false | Правда чи хибність про регістри | 12 | 8 | ✅ |
| 15 | mark-the-words | Знайдіть пасивні конструкції | 8 | 6 | ✅ |
| 16 | select | Оберіть усі правильні варіанти | 10 | 6 | ✅ |
| 17 | translate | Переклад пасивних конструкцій | 10 | 6 | ✅ |
| 18 | error-correction | Виправлення регістрових помилок | 10 | 6 | ✅ |
| 19 | quiz | Комплексний тест B2.1 | 12 | 8 | ✅ |
| 20 | reading | Текст для аналізу: Контрольна точка: B2.1 Завершення | 3 | 3 | ✅ |
| 21 | essay-response | Письмова відповідь: Контрольна точка: B2.1 Завершення | 1 | 1 | ✅ |

**Summary:**
- Total activities: 21 (target: 15-19) ❌
- Unique types: 13 (minimum: 4) ✅
- Priority types used: 4/4 (cloze, error-correction, fill-in, quiz) ✅
- Required types used: 3/3 (essay-response, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (71% overlap): "Компанія, **що існує** вже двадцять років, розширює діяльність.". Shares significant keywords with sentence at index 15.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-b21-checkpoint.yaml: Schema validation error at key '20': {'type': 'essay-response', 'title': 'Письмова відповідь: Контрольна точка: B2.1 Завершення', 'prompt': 'Напишіть розгорнуту відповідь на тему "Контрольна точка: B2.1 Завершення".\nВикористайте вивчені конструкції та лексику з цього модуля.\nОбсяг: 150-200 слів.\n', 'word_target': 150, 'model_answer': 'Ця тема є надзвичайно актуальною для сучасного мовного середовища.\nВивчені конструкції дозволяють глибше зрозуміти особливості\nукраїнської мови та використовувати їх у професійному контексті.\nВажливо відзначити практичне значення цих знань для щоденного\nспілкування та професійної діяльності.\n'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ✅ 2130/2000 (raw: 2325)
- **Activities:** ✅ 21/15
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 13/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/4
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 8 < 10 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (checkpoint - no gate)
- **Richness:** ✅ 88% (checkpoint)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 88% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 13 | 8 | 100% | 25% | 25.0% |
| review_sections | 30 | 3 | 100% | 20% | 20.0% |
| variety | 0.89 | - | 89% | 15% | 13.4% |
| engagement | 7 | 3 | 100% | 10% | 10.0% |
| cultural | 0 | - | 0% | 10% | 0.0% |
| visual | 16 | 3 | 100% | 10% | 10.0% |
| paragraph_var | 1.00 | - | 100% | 10% | 10.0% |
| **TOTAL** | | | | | **88.3%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 58 | Included in Core |
| **Огляд — Контрольна точка B2.1** | ⚪️ | 88 | Skipped |
| **Навичка 1: Пасивний стан** | ⚪️ | 231 | Skipped |
| **Навичка 2: Дієприкметники** | ⚪️ | 403 | Skipped |
| **Навичка 3: Регістри** | ⚪️ | 439 | Skipped |
| **Навичка 4: Доменна лексика** | ⚪️ | 438 | Skipped |
| **Підсумок та результати** | ✅ | 237 | Included in Core |
| **Підсумок** | ✅ | 236 | Included in Core |