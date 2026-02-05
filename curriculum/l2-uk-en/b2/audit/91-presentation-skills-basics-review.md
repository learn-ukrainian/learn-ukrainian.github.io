# Audit Report: M91 — 91-presentation-skills-basics.md
**Level:** B2 | **Module:** M91 | **Phase:** B2.4 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 8/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:10:38

## Configuration
**Type:** B2-skills
**Word Target:** 2000 words
**Activities:** 14-18 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥5 types required
**Priority Types:** cloze, fill-in, quiz, translate
**Required Types:** essay-response, reading, true-false
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥20 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Структура презентації | 16 | 8 | ✅ |
| 2 | match-up | Терміни презентацій | 12 | 8 | ✅ |
| 3 | fill-in | Ключові елементи презентації | 16 | 8 | ✅ |
| 4 | true-false | Перевірка розуміння | 16 | 8 | ✅ |
| 5 | unjumble | Порядок слів | 10 | 6 | ✅ |
| 6 | error-correction | Виправлення помилок | 10 | 6 | ✅ |
| 7 | cloze | Заповніть пропуски | 14 | 14 | ✅ |
| 8 | mark-the-words | Знайдіть ключові терміни | 10 | 6 | ✅ |
| 9 | select | Множинний вибір | 10 | 6 | ✅ |
| 10 | group-sort | Сортування за категоріями | 20 | 14 | ✅ |
| 11 | translate | Переклад термінів | 10 | 6 | ✅ |
| 12 | fill-in | Фрази для сигналізації | 10 | 8 | ✅ |
| 13 | quiz | Типові помилки та їх виправлення | 10 | 8 | ✅ |
| 14 | error-correction | Виправлення помилок у поданні | 8 | 6 | ✅ |
| 15 | reading | Текст для аналізу: Презентації: Основи | 3 | 3 | ✅ |
| 16 | essay-response | Письмова відповідь: Презентації: Основи | 1 | 1 | ✅ |

**Summary:**
- Total activities: 16 (target: 14-18) ✅
- Unique types: 13 (minimum: 5) ✅
- Priority types used: 4/4 (cloze, fill-in, quiz, translate) ✅
- Required types used: 3/3 (essay-response, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[SECTION_ORDER]** Content section '## Практика' appears after end section '# Підсумок'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 91-presentation-skills-basics.yaml: Schema validation error at key '15': {'type': 'essay-response', 'title': 'Письмова відповідь: Презентації: Основи', 'prompt': 'Напишіть розгорнуту відповідь на тему "Презентації: Основи".\nВикористайте вивчені конструкції та лексику з цього модуля.\nОбсяг: 150-200 слів.\n', 'word_target': 150, 'model_answer': 'Ця тема є надзвичайно актуальною для сучасного мовного середовища.\nВивчені конструкції дозволяють глибше зрозуміти особливості\nукраїнської мови та використовувати їх у професійному контексті.\nВажливо відзначити практичне значення цих знань для щоденного\nспілкування та професійної діяльності.\n'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ✅ 2282/2000 (raw: 2360)
- **Activities:** ✅ 16/14
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 13/5 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 5 < 20 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ✅ Content-heavy OK (16 activities)
- **Immersion:** 🇺🇦 99.7% (target 90-100% (skills))
- **Richness:** ✅ 91% (skills)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 8/10 (High)

## Richness Details
**Score:** 91% (minimum: 80%)
**Module Type:** skills

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 33 | 15 | 100% | 26% | 25.5% |
| engagement | 9 | 5 | 100% | 19% | 19.4% |
| variety | 0.98 | - | 98% | 12% | 12.0% |
| cultural | 1 | - | 100% | 12% | 12.2% |
| realworld | 18 | 3 | 100% | 12% | 12.2% |
| visual | 0 | 2 | 0% | 6% | 0.0% |
| paragraph_var | 0.66 | - | 66% | 6% | 4.0% |
| questions | 13 | 4 | 100% | 6% | 6.1% |
| **TOTAL** | | | | | **91.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 62 | Included in Core |
| **Розминка — Що таке ефективна презентація** | ⚪️ | 140 | Skipped |
| **Структура презентації** | ⚪️ | 1863 | Skipped |
| **Підсумок** | ✅ | 164 | Included in Core |
| **Signposting — мовна навігація** | ⚪️ | 53 | Skipped |
| **Візуальні матеріали** | ⚪️ | 0 | Skipped |
| **Техніка виступу — основи** | ⚪️ | 0 | Skipped |
| **Практика** | ⚪️ | 0 | Skipped |