# Audit Report: M116 — halyna-pahutyak.md
**Level:** C1 | **Module:** M116 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:27:46

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
| 1 | quiz | Життя та філософія Галини Пагутяк | 5 | 5 | ✅ |
| 2 | match-up | Літературознавча та філософська лексика | 8 | 6 | ✅ |
| 3 | group-sort | Особливості художнього світу Пагутяк | 12 | 1 | ✅ |
| 4 | fill-in | Контекст роману «Слуга з Добромиля» | 6 | 6 | ✅ |
| 5 | quiz | Аналіз стилю та символіки | 5 | 5 | ✅ |
| 6 | match-up | Синоніми та поняття модуля | 8 | 6 | ✅ |
| 7 | group-sort | Діяльність та погляди Пагутяк | 12 | 1 | ✅ |
| 8 | fill-in | Естетика та місія письменниці | 6 | 6 | ✅ |
| 9 | quiz | Роль Галичини у творчості | 5 | 5 | ✅ |
| 10 | group-sort | Лексика модуля: Галина Пагутяк | 12 | 1 | ✅ |
| 11 | essay-response | Творча робота: Прірва та Пам'ять | 1 | 1 | ✅ |
| 12 | comparative-study | Галина Пагутяк та латиноамериканський магічний реалізм | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in halyna-pahutyak.yaml: Schema validation error at key '7': {'type': 'fill-in', 'title': 'Естетика та місія письменниці', 'items': [{'sentence': 'Творчість Пагутяк є прикладом повернення до власних метафізичних [джерел].', 'answer': 'джерел', 'options': ['джерел', 'ілюзій', 'проблем', 'схем']}, {'sentence': 'Вона вчить читача не боятися [самотності], бо саме в ній народжується свобода.', 'answer': 'самотності', 'options': ['самотності', 'натовпу', 'влади', 'злиднів']}, {'sentence': 'Для неї література — це не спосіб розваги, а інструмент порятунку [душі] від байдужості.', 'answer': 'душі', 'options': ['душі', 'тіла', 'гаманця', 'рейтингу']}, {'sentence': 'Авторка сприймає природу як [сакральний] простір, де кожна істота має значення.', 'answer': 'сакральний', 'options': ['сакральний', 'технічний', 'пустий', 'небезпечний']}, {'sentence': 'Її проза допомагає долати імперські [шаблони] та будувати власну ідентичність.', 'answer': 'шаблони', 'options': ['шаблони', 'будинки', 'дороги', 'парки']}, {'sentence': 'Пагутяк залишається «голосом [совісті]» у питаннях відповідальності людини перед вічністю.', 'answer': 'совісті', 'options': ['совісті', 'влади', 'грошей', 'реклами']}]} is not valid under any of the given schemas
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
- **Words:** ❌ 2112/4000 (raw: 2324)
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
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 5 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 11 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 8 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 19 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 68 | Included in Core |
| **Вступ** | ✅ | 178 | Included in Core |
| **Життєпис** | ⚪️ | 625 | Skipped |
| **Внесок** | ⚪️ | 56 | Skipped |
| **Сучасний етап** | ⚪️ | 122 | Skipped |
| **Історичний контекст** | ✅ | 222 | Included in Core |
| **Порівняльний аналіз** | ✅ | 158 | Included in Core |
| **Есе** | ⚪️ | 356 | Skipped |
| **Підсумок** | ✅ | 43 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 168 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 116 | Skipped |