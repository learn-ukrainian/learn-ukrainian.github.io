# Audit Report: M32 — taras-shevchenko.md
**Level:** C1 | **Module:** M32 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:12

## Configuration
**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** essay-response, fill-in, group-sort, match-up, quiz, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Розуміння постаті та її значення | 8 | 5 | ✅ |
| 2 | fill-in | Лексика національного відродження | 8 | 6 | ✅ |
| 3 | match-up | Термінологія боротьби та спадщини | 10 | 6 | ✅ |
| 4 | select | Лінгвістичний аналіз джерела | 6 | 5 | ✅ |
| 5 | error-correction | Граматика в біографічному дискурсі | 7 | 5 | ✅ |
| 6 | group-sort | Деколонізація: Наративи та Контрасти | 14 | 1 | ✅ |
| 7 | essay-response | Критичний аналіз: Шевченко як архітектор волі | 1 | 1 | ✅ |
| 8 | comparative-study | Компаративістика: Шевченко vs Пушкін | 1 | 1 | ✅ |
| 9 | unjumble | Структура пророчого слова | 8 | 5 | ✅ |
| 10 | cloze | Шлях від неволі до пророцтва | 15 | 1 | ✅ |
| 11 | translate | Переклад пророчих тез | 6 | 5 | ✅ |
| 12 | true-false | Факти та візії Шевченка | 8 | 5 | ✅ |
| 13 | reading | Аналіз поетичного маніфесту | 3 | 1 | ✅ |
| 14 | reading | Дослідження біографічного нарису | 3 | 1 | ✅ |
| 15 | essay-response | Філософське есе: Шевченко-деколонізатор | 1 | 1 | ✅ |

**Summary:**
- Total activities: 15 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in taras-shevchenko.yaml: Schema validation error at key '13': {'type': 'reading', 'title': 'Дослідження біографічного нарису', 'resource': {'type': 'article', 'url': 'https://shvydko.com.ua/taras-shevchenko-biografiya/', 'title': 'Тарас Шевченко: Повна біографія та творчість'}, 'tasks': ['Які ключові етапи викупу поета з неволі виділяє автор статті?', "Як у тексті характеризується вплив 'захалявних книжечок' на розвиток української літератури?", 'Знайдіть приклади оцінної лексики, що описує ставлення автора до Кобзаря.']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2018/4000 (raw: 2158)
- **Activities:** ✅ 15/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 15 (target 3-9)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 8 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 28 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 10 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 79 | Included in Core |
| **Вступ** | ✅ | 167 | Included in Core |
| **Життєпис** | ⚪️ | 449 | Skipped |
| **Внесок** | ⚪️ | 430 | Skipped |
| **Історичний контекст** | ✅ | 616 | Included in Core |
| **Порівняльний аналіз** | ✅ | 69 | Included in Core |
| **Критичне мислення** | ⚪️ | 120 | Skipped |
| **Підсумок** | ✅ | 74 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 14 | Skipped |