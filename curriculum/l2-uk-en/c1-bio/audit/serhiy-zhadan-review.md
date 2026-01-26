# Audit Report: M123 — serhiy-zhadan.md
**Level:** C1 | **Module:** M123 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:57:18

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
| 1 | quiz | Біографія та діяльність Сергія Жадана | 5 | 5 | ✅ |
| 2 | match-up | Лексика війни та міста | 8 | 6 | ✅ |
| 3 | group-sort | Світи Сергія Жадана | 12 | 1 | ✅ |
| 4 | fill-in | Контекст роману «Інтернат» | 6 | 6 | ✅ |
| 5 | quiz | Стиль та теми | 5 | 5 | ✅ |
| 6 | match-up | Синоніми та антоніми | 8 | 6 | ✅ |
| 7 | group-sort | Лексика модуля: Сергій Жадан | 12 | 1 | ✅ |
| 8 | group-sort | Ролі Жадана | 12 | 1 | ✅ |
| 9 | quiz | Громадянська позиція | 5 | 5 | ✅ |
| 10 | fill-in | Музична діяльність | 6 | 6 | ✅ |
| 11 | essay-response | Творча робота: Поет на війні | 1 | 1 | ✅ |
| 12 | comparative-study | Сергій Жадан та Чарльз Буковскі | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in serhiy-zhadan.yaml: Schema validation error at key '9': {'type': 'fill-in', 'title': 'Музична діяльність', 'items': [{'sentence': 'Гурт «Жадан і [Собаки]» виконує музику в стилі ска-панк.', 'answer': 'Собаки', 'options': ['Собаки', 'Коти', 'Вовки', 'Птахи']}, {'sentence': 'Музика допомагає донести [поезію] до ширшої молодіжної аудиторії.', 'answer': 'поезію', 'options': ['поезію', 'прозу', 'новини', 'рекламу']}, {'sentence': "На концертах Жадан створює неймовірну [енергетику], яка об'єднує зал.", 'answer': 'енергетику', 'options': ['енергетику', 'тишу', 'нудьгу', 'паніку']}, {'sentence': 'Пісні гурту часто мають гостросоціальний та [сатиричний] характер.', 'answer': 'сатиричний', 'options': ['сатиричний', 'ліричний', 'сумний', 'дитячий']}, {'sentence': 'Під час війни музиканти дають концерти в [метро] та бомбосховищах.', 'answer': 'метро', 'options': ['метро', 'театрі', 'цирку', 'лісі']}, {'sentence': 'Жадан доводить, що українська культура може бути [драйвовою] і сучасною.', 'answer': 'драйвовою', 'options': ['драйвовою', 'нудною', 'старою', 'тихою']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[FORBIDDEN_HEADER_TONE]** Header '## Сучасний етап' is inappropriate for a deceased person. Use '## Останні роки' instead.
  - FIX: Rename '## Сучасний етап' to '## Останні роки' to maintain correct biographical tone.
- ❌ **[FORBIDDEN_HEADER_TONE]** Header '## Вплив' is inappropriate for a deceased person. Use '## Спадщина' instead.
  - FIX: Rename '## Вплив' to '## Спадщина' to maintain correct biographical tone.

## Recommendation
**📝 UPDATE** (severity 25/100)

- 3 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 1954/4000 (raw: 2223)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 6/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 8 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 18 | 8 | 100% | 10% | 9.5% |
| legacy | 14 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 18 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Вступ** | ✅ | 166 | Included in Core |
| **Життєпис** | ⚪️ | 405 | Skipped |
| **Внесок** | ⚪️ | 50 | Skipped |
| **Сучасний етап** | ⚪️ | 101 | Skipped |
| **Історичний контекст** | ✅ | 383 | Included in Core |
| **Порівняльний аналіз** | ✅ | 182 | Included in Core |
| **Есе** | ⚪️ | 315 | Skipped |
| **Підсумок** | ✅ | 31 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 152 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 97 | Skipped |