# Audit Report: M109 — myroslav-marynovych.md
**Level:** C1 | **Module:** M109 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:51

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
| 1 | reading | Первинні джерела: Мирослав Маринович про цінності | 3 | 1 | ✅ |
| 2 | reading | Науковий нарис про Українську Гельсінську групу | 3 | 1 | ✅ |
| 3 | quiz | Розуміння біографії | 5 | 5 | ✅ |
| 4 | fill-in | Ціннісна лексика | 6 | 6 | ✅ |
| 5 | select | Лінгвістичний аналіз етичного тексту | 5 | 5 | ✅ |
| 6 | error-correction | Граматика в гуманітарному тексті | 5 | 5 | ✅ |
| 7 | match-up | Терміни та поняття духу | 8 | 6 | ✅ |
| 8 | true-false | Факти про Мариновича | 5 | 5 | ✅ |
| 9 | unjumble | Аналіз світоглядних тез | 5 | 5 | ✅ |
| 10 | group-sort | Поняття та сфери діяльності | 12 | 1 | ✅ |
| 11 | cloze | Життєве кредо | 12 | 1 | ✅ |
| 12 | group-sort | Лексика духовного вибору | 12 | 1 | ✅ |
| 13 | essay-response | Творча робота: Уроки Мариновича | 1 | 1 | ✅ |
| 14 | comparative-study | Маринович та сучасність: Порівняння | 1 | 1 | ✅ |

**Summary:**
- Total activities: 14 (target: 3-9) ❌
- Unique types: 12 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in myroslav-marynovych.yaml: Schema validation error at key 'blanks': [{'id': 1, 'answer': 'правозахисник', 'options': ['правозахисник', 'економіст', 'спортсмен', 'фізик']}, {'id': 2, 'answer': 'мислитель', 'options': ['мислитель', 'чиновник', 'актор', 'лікар']}, {'id': 3, 'answer': 'Української Гельсінської групи', 'options': ['Української Гельсінської групи', 'Компартії', 'Профспілки', 'Спілки художників']}, {'id': 4, 'answer': "ув'язнення", 'options': ["ув'язнення", 'відпочинку', 'стажування', 'переїзду']}, {'id': 5, 'answer': 'загартував', 'options': ['загартував', 'втратив', 'забув', 'зрадив']}, {'id': 6, 'answer': 'УКУ', 'options': ['УКУ', 'КДБ', 'заводі', 'банку']}, {'id': 7, 'answer': 'екуменізму', 'options': ['екуменізму', 'атеїзму', 'ізоляціонізму', 'радикалізму']}, {'id': 8, 'answer': 'совість', 'options': ['совість', 'хитрість', 'зброя', 'вигода']}, {'id': 9, 'answer': 'діалогу', 'options': ['діалогу', 'конфлікту', 'байдужості', 'мовчання']}, {'id': 10, 'answer': 'вагу', 'options': ['вагу', 'страх', 'сумнів', 'жарт']}, {'id': 11, 'answer': 'візіонер', 'options': ['візіонер', 'противник', 'глядач', 'учень']}, {'id': 12, 'answer': 'відповідальності', 'options': ['відповідальності', 'втечі', 'гри', 'паніки']}] is too short
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
- **Words:** ❌ 2102/4000 (raw: 2373)
- **Activities:** ✅ 14/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 12/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 14 (target 3-9)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 14 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 27 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 17 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 70 | Included in Core |
| **Вступ** | ✅ | 205 | Included in Core |
| **Життєпис** | ⚪️ | 465 | Skipped |
| **Внесок** | ⚪️ | 104 | Skipped |
| **Сучасний етап** | ⚪️ | 108 | Skipped |
| **Історичний контекст** | ✅ | 248 | Included in Core |
| **Порівняльний аналіз** | ✅ | 174 | Included in Core |
| **Есе** | ⚪️ | 363 | Skipped |
| **Підсумок** | ✅ | 49 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 190 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 126 | Skipped |