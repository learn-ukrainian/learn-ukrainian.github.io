# Audit Report: M119 — shliakh-nezalezhnosti.md
**Level:** B2 | **Module:** M119 | **Phase:** HIST.12 | **Pedagogy:** CBI | **Target:** 4000
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
| 1 | reading | Акт проголошення незалежності | 0 | 1 | ❌ |
| 2 | critical-analysis | Верифікація фактів: Незалежність | 1 | 1 | ✅ |
| 3 | essay-response | Есе: Роль референдуму | 1 | 1 | ✅ |
| 4 | comparative-study | 1918 vs 1991 | 1 | 1 | ✅ |
| 5 | true-false | Події 1991 року | 3 | 8 | ❌ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 5 (minimum: 2) ✅
- Priority types used: 4/4 (comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 2

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** reading 'Акт проголошення незалежності' has 0 items (minimum: 1)
  - FIX: Add more items. B2 reading requires at least 1 items.
- **[COMPLEXITY]** true-false 'Події 1991 року' has 3 items (minimum: 8)
  - FIX: Add more items. B2 true-false requires at least 8 items.
- **[YAML_SCHEMA_VIOLATION]** Schema error in shliakh-nezalezhnosti.yaml: Schema validation error at key '4': {'type': 'true-false', 'title': 'Події 1991 року', 'items': [{'statement': 'Студентська «Революція на граніті» відбулася вже після проголошення незалежності.', 'explanation': 'Вона відбулася у жовтні 1990 року і стала каталізатором змін, що привели до незалежності.', 'correct': False}, {'statement': '«Живий ланцюг» простягнувся від Києва до Донецька.', 'explanation': "Він з'єднав Київ та Львів (і Івано-Франківськ), символізуючи злуку УНР і ЗУНР.", 'correct': False}, {'statement': 'Леонід Кравчук балотувався на пост президента як кандидат від Народного Руху.', 'explanation': "Кравчук був колишнім комуністом і йшов як незалежний кандидат (фактично від номенклатури); кандидатом від Руху був В'ячеслав Чорновіл.", 'correct': False}], 'instruction': 'Визначте, чи твердження правильне.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 3 violations (minor)
- Activity density below minimum

## Gates
- **Words:** ❌ 1140/4000 (raw: 1211)
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
- **Immersion:** 🇺🇦 98.2% (target 90-100% (history))
- **Richness:** ✅ 97% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 3 | 100% | 24% | 23.8% |
| engagement | 5 | 6 | 83% | 14% | 11.9% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| variety | 0.96 | - | 96% | 5% | 4.6% |
| paragraph_var | 0.99 | - | 99% | 5% | 4.7% |
| questions | 4 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.3%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Акт проголошення незалежності | reading | 0 | 1 | Add 1 more items |
| Події 1991 року | true-false | 3 | 8 | Add 5 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 36 | Included in Core |
| **Вступ: Крах імперії** | ✅ | 122 | Included in Core |
| **Основні події: Шлях до незалежності** | ⚪️ | 574 | Skipped |
| **Первинні джерела** | ✅ | 124 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 153 | Included in Core |
| **Підсумок: Нова держава** | ✅ | 131 | Included in Core |