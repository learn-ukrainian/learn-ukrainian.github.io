# Audit Report: M114 — shistdesiatnyky.md
**Level:** B2 | **Module:** M114 | **Phase:** HIST.11 | **Pedagogy:** Not Specified | **Target:** 4000
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-27 23:38:54

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
| 1 | true-false | Проаналізуйте уривок з виступу Василя Стуса та виберіть правильні твердження. | 8 | 8 | ✅ |
| 2 | essay-response | Ваша думка | 1 | 1 | ✅ |
| 3 | comparative-study | Порівняння епох | 1 | 1 | ✅ |
| 4 | true-false | Визначте, чи є твердження правдивими. | 8 | 8 | ✅ |
| 5 | true-false | Виберіть ознаки "шароварщини" | 8 | 8 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 3 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in shistdesiatnyky.yaml: Schema validation error at key '4': {'type': 'true-false', 'items': [{'correct': True, 'statement': 'Зведення української культури лише до танців і вареників'}, {'correct': False, 'statement': 'Глибоке філософське осмислення історії'}, {'correct': True, 'statement': 'Використання спрощених фольклорних образів'}, {'correct': False, 'statement': 'Експерименти з модерними художніми формами'}, {'correct': True, 'statement': 'Виконання пісень лише в розважальному стилі'}, {'correct': False, 'statement': 'Створення інтелектуальної прози та поезії'}, {'correct': True, 'statement': 'Пропаганда образу "смішного малороса"'}, {'correct': False, 'statement': 'Підтримка авангардного мистецтва'}], 'title': 'Виберіть ознаки "шароварщини"', 'instruction': 'Визначте, чи є характеристика ознакою "шароварщини".'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2109/4000 (raw: 2250)
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 3/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 97.1% (target 90-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 9 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Шістдесятники: Голос совісті** | ⚪️ | 104 | Skipped |
| **Читання** | ✅ | 1307 | Included in Core |
| **Первинні джерела** | ✅ | 274 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 256 | Included in Core |
| **Підсумок** | ✅ | 58 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |