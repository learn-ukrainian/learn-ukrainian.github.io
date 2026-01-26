# Audit Report: M100 — mekhanizm-teroru.md
**Level:** B2 | **Module:** M100 | **Phase:** HIST.10 | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 10/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:55:14

## Configuration
**Type:** B2-history
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥2 types required
**Priority Types:** comparative-study, critical-analysis, essay-response, reading
**Required Types:** essay-response, match-up, quiz, reading, true-false
**Engagement:** ≥5 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥20 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Перевірка розуміння | 8 | 8 | ✅ |
| 2 | fill-in | Заповніть пропуски | 8 | 8 | ✅ |
| 3 | error-correction | Виправте помилки | 6 | 6 | ✅ |
| 4 | match-up | Встановіть відповідності | 12 | 8 | ✅ |
| 5 | select | Виберіть правильні відповіді | 6 | 6 | ✅ |
| 6 | mark-the-words | Позначте слова | 12 | 6 | ✅ |
| 7 | group-sort | Розподіліть за групами | 24 | 1 | ✅ |
| 8 | unjumble | Складіть речення | 6 | 6 | ✅ |
| 9 | cloze | Текст із пропусками | 16 | 1 | ✅ |
| 10 | true-false | Правда чи неправда | 8 | 8 | ✅ |
| 11 | translate | Переклад | 6 | 6 | ✅ |
| 12 | essay-response | Ваша думка | 1 | 1 | ✅ |
| 13 | comparative-study | Механізми терору | 1 | 1 | ✅ |
| 14 | quiz | Перевірка розуміння | 8 | 8 | ✅ |
| 15 | fill-in | Заповніть пропуски | 8 | 8 | ✅ |

**Summary:**
- Total activities: 15 (target: 3-9) ❌
- Unique types: 13 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 4/5 (essay-response, match-up, quiz, true-false) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in mekhanizm-teroru.yaml: Schema validation error at key '14': {'type': 'fill-in', 'instruction': "Впишіть відсутні географічні назви, пов'язані з історією терору.", 'items': [{'sentence': 'Центром українського культурного життя у 1920-х роках був [___].', 'answer': 'Харків', 'options': ['Харків', 'Київ', 'Львів', 'Полтава']}, {'sentence': 'Соловецький табір особливого призначення розташовувався на [___] морі.', 'answer': 'Білому', 'options': ['Білому', 'Чорному', 'Азовському', 'Каспійському']}, {'sentence': "Масові розстріли соловецьких в'язнів відбувалися в урочищі [___].", 'answer': 'Сандармох', 'options': ['Сандармох', 'Бабин Яр', 'Биківня', 'Куропати']}, {'sentence': 'Урочище Сандармох територіально знаходиться у [___].', 'answer': 'Карелії', 'options': ['Карелії', 'Сибіру', 'Україні', 'Криму']}, {'sentence': 'Будинок [___] у Харкові став місцем мешкання багатьох митців.', 'answer': 'Слово', 'options': ['Слово', 'Праця', 'Воля', 'Перемога']}, {'sentence': 'Микола Хвильовий закликав орієнтуватися на психологічну [___].', 'answer': 'Європу', 'options': ['Європу', 'Азію', 'Америку', 'Африку']}, {'sentence': 'Архіви про репресії були відкриті завдяки дослідникам [___].', 'answer': 'Меморіалу', 'options': ['Меморіалу', 'Партії', 'Армії', 'Цензури']}, {'sentence': 'Сьогодні ми вшановуємо репресованих митців у сучасній незалежній [___].', 'answer': 'Україні', 'options': ['Україні', 'Європі', 'Росії', 'Канаді']}], 'title': 'Заповніть пропуски'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2055/4000 (raw: 2289)
- **Activities:** ✅ 15/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 15 (target 3-9)
- **Immersion:** 🇺🇦 97.0% (target 90-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 10/10 (High)

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 6 | 3 | 100% | 24% | 23.8% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 3 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Розстріляне відродження II: Механізм терору** | ⚪️ | 58 | Skipped |
| **Вступ** | ✅ | 116 | Included in Core |
| **Читання** | ✅ | 1247 | Included in Core |
| **Первинні джерела** | ✅ | 108 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 204 | Included in Core |
| **Підсумок** | ✅ | 212 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |