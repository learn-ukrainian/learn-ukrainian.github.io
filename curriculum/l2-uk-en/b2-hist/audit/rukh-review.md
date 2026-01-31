# Audit Report: M120 — rukh.md
**Level:** B2 | **Module:** M120 | **Phase:** HIST.12 | **Pedagogy:** CBI | **Target:** 4000
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-31 13:57:06

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
| 1 | reading | Програма Руху | 0 | 1 | ❌ |
| 2 | critical-analysis | Верифікація фактів: Рух | 1 | 1 | ✅ |
| 3 | essay-response | Есе: Феномен Руху | 1 | 1 | ✅ |
| 4 | comparative-study | Рух vs Солідарність | 1 | 1 | ✅ |
| 5 | true-false | Історія Руху | 3 | 8 | ❌ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 5 (minimum: 2) ✅
- Priority types used: 4/4 (comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 2

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** reading 'Програма Руху' has 0 items (minimum: 1)
  - FIX: Add more items. B2 reading requires at least 1 items.
- **[COMPLEXITY]** true-false 'Історія Руху' has 3 items (minimum: 8)
  - FIX: Add more items. B2 true-false requires at least 8 items.
- **[YAML_SCHEMA_VIOLATION]** Schema error in rukh.yaml: Schema validation error at key '4': {'type': 'true-false', 'title': 'Історія Руху', 'items': [{'statement': 'Гаслом Руху було «За нашу і вашу свободу».', 'explanation': 'Це традиційне гасло дисидентів, яке підкреслювало демократичний характер руху.', 'correct': True}, {'statement': 'Рух виступав за збереження СРСР.', 'explanation': 'У 1990 році Рух офіційно змінив програму, проголосивши мету — повну державну незалежність України.', 'correct': False}, {'statement': 'Шахтарі Донбасу підтримували Рух у 1989-1990 роках.', 'explanation': 'Страйкові комітети співпрацювали з Рухом, вимагаючи не лише зарплат, а й політичних змін.', 'correct': True}], 'instruction': 'Визначте, чи твердження правильне.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 3 violations (minor)
- Activity density below minimum

## Gates
- **Words:** ❌ 731/4000 (raw: 780)
- **Activities:** ✅ 5/3
- **Density:** ❌ 2 < 1
- **Unique_types:** ✅ 5/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 5/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 20/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 99.7% (target 90-100% (history))
- **Richness:** ❌ 94% < 95% min (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 94% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 6 | 3 | 100% | 24% | 23.8% |
| engagement | 5 | 6 | 83% | 14% | 11.9% |
| timeline_markers | 24 | 10 | 100% | 14% | 14.3% |
| decolonization | 11 | 2 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 5 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 0.86 | - | 86% | 5% | 4.1% |
| questions | 4 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **94.5%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Програма Руху | reading | 0 | 1 | Add 1 more items |
| Історія Руху | true-false | 3 | 8 | Add 5 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 43 | Included in Core |
| **Вступ: Перебудова в Україні** | ✅ | 87 | Included in Core |
| **Основні події: Історія Народного Руху** | ⚪️ | 248 | Skipped |
| **Первинні джерела** | ✅ | 111 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 110 | Included in Core |
| **Підсумок: Спадщина Руху** | ✅ | 132 | Included in Core |