# Audit Report: M121 — nezalezhnist-1991.md
**Level:** B2 | **Module:** M121 | **Phase:** HIST.12 | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 10/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-31 13:24:39

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
| 1 | true-false | Визначте правдивість тверджень про Будапештський меморандум. | 10 | 8 | ✅ |
| 2 | true-false | Визначте правдивість тверджень про період 1991-2004 років. | 8 | 8 | ✅ |
| 3 | true-false | Визначте правдивість лінгвістичних тенденцій періоду. | 8 | 8 | ✅ |
| 4 | essay-response | Труднощі становлення нації | 1 | 1 | ✅ |
| 5 | comparative-study | Порівняння президенств | 1 | 1 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 3 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in nezalezhnist-1991.yaml: Schema validation error at key '2': {'type': 'true-false', 'items': [{'statement': 'Велика кількість запозичень з англійської (бізнес, приватизація)', 'correct': True}, {'statement': 'Повернення застарілих слів козацької доби (гетьман, булава)', 'correct': False}, {'statement': "Поява неологізмів, пов'язаних з кризою (кравчучка, купони)", 'correct': True}, {'statement': "Використання виключно церковнослов'янської термінології", 'correct': False}, {'statement': 'Формування нової політичної та юридичної термінології', 'correct': True}, {'statement': 'Перехід на використання латинського алфавіту в медіа', 'correct': False}, {'statement': 'Стрімка українізація всіх сфер життя у 1990-х роках', 'correct': False}, {'statement': 'Поява нових термінів на позначення олігархічних структур', 'correct': True}], 'title': 'Визначте правдивість лінгвістичних тенденцій періоду.', 'instruction': 'Визначте, чи є твердження правдивим.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 1991/4000 (raw: 2170)
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 3/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
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
| primary_sources | 14 | 3 | 100% | 24% | 23.8% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 16 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Україна 1991-2004: Становлення та випробування** | ⚪️ | 97 | Skipped |
| **Вступ** | ✅ | 262 | Included in Core |
| **Читання** | ✅ | 228 | Included in Core |
| **Історичний наратив: Шлях крізь шторм** | ⚪️ | 606 | Skipped |
| **Первинні джерела** | ✅ | 279 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 249 | Included in Core |
| **Порівняльний аналіз** | ✅ | 126 | Included in Core |
| **Підсумок** | ✅ | 73 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 71 | Skipped |