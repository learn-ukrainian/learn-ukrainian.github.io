# Audit Report: M125 — sofia-andrukhovych.md

**Level:** C1 | **Module:** M125 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:57:19

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
| 1 | quiz | Біографія та творчість | 5 | 5 | ✅ |
| 2 | match-up | Словник романів | 8 | 6 | ✅ |
| 3 | group-sort | Світи Софії Андрухович | 12 | 1 | ✅ |
| 4 | fill-in | Контекст роману «Фелікс Австрія» | 6 | 6 | ✅ |
| 5 | quiz | Психологічний аналіз | 5 | 5 | ✅ |
| 6 | match-up | Поняття пам'яті | 8 | 6 | ✅ |
| 7 | group-sort | Лексика модуля: Софія Андрухович | 12 | 1 | ✅ |
| 8 | group-sort | Риси прози Андрухович | 12 | 1 | ✅ |
| 9 | quiz | Культурний контекст | 5 | 5 | ✅ |
| 10 | fill-in | Значення творчості | 6 | 6 | ✅ |
| 11 | essay-response | Творча робота: Пастка ілюзій | 1 | 1 | ✅ |
| 12 | comparative-study | Софія Андрухович та Донна Тартт | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in sofia-andrukhovych.yaml: Schema validation error at key '9': {'type': 'fill-in', 'title': 'Значення творчості', 'items': [{'sentence': 'Софія Андрухович довела, що українська література може бути [інтелектуальною] і популярною.', 'answer': 'інтелектуальною', 'options': ['інтелектуальною', 'нудною', 'простою', 'дешевою']}, {'sentence': "Вона майстерно працює з [пам'яттю], заповнюючи білі плями нашої історії.", 'answer': "пам'яттю", 'options': ["пам'яттю", 'грошима', 'фарбами', 'цифрами']}, {'sentence': 'Її романи — це не просто історії, це [реконструкція] втраченого світу.', 'answer': 'реконструкція', 'options': ['реконструкція', 'руйнація', 'копія', 'пародія']}, {'sentence': 'Письменниця не боїться складних тем, таких як [Голокост] і репресії.', 'answer': 'Голокост', 'options': ['Голокост', 'свято', 'весілля', 'подорож']}, {'sentence': 'Вона створила власний літературний [світ], незалежний від слави батька.', 'answer': 'світ', 'options': ['світ', 'дім', 'сад', 'клуб']}, {'sentence': 'Її книги перекладені багатьма мовами і є [обличчям] сучасної України в Європі.', 'answer': 'обличчям', 'options': ['обличчям', 'спиною', 'рукою', 'ногою']}]} is not valid under any of the given schemas
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

- **Words:** ❌ 2014/4000 (raw: 2198)
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
- **Immersion:** 🇺🇦 99.8% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 3 | 4 | 75% | 19% | 14.3% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 5 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 11 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 10 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 24 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.1%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 69 | Included in Core |
| **Вступ** | ✅ | 151 | Included in Core |
| **Життєпис** | ⚪️ | 619 | Skipped |
| **Внесок** | ⚪️ | 55 | Skipped |
| **Сучасний етап** | ⚪️ | 103 | Skipped |
| **Історичний контекст** | ✅ | 305 | Included in Core |
| **Порівняльний аналіз** | ✅ | 161 | Included in Core |
| **Есе** | ⚪️ | 288 | Skipped |
| **Підсумок** | ✅ | 34 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 157 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 72 | Skipped |
