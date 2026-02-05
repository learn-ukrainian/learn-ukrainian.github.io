# Audit Report: M94 — olena-stepaniv.md
**Level:** C1-BIO | **Module:** M94 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 12:40:21

## Configuration
**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** essay-response, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | true-false | Факти про Олену Степанів | 5 | 5 | ✅ |
| 2 | authorial-intent | Намір автора: Жінка на війні | 1 | 1 | ✅ |
| 3 | essay-response | Аналіз феномену: Жінка-воїн | 1 | 1 | ✅ |
| 4 | comparative-study | Порівняння: Степанів та Жанна д’Арк | 1 | 1 | ✅ |
| 5 | critical-analysis | Аналіз радянських репресій | 1 | 1 | ✅ |
| 6 | reading | Спогади Олени Степанів | 3 | 1 | ✅ |

**Summary:**
- Total activities: 6 (target: 3-9) ✅
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 5/6 (authorial-intent, comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in olena-stepaniv.yaml: Schema validation error at key '5': {'type': 'reading', 'title': 'Спогади Олени Степанів', 'resource': {'type': 'primary_source', 'url': 'https://elib.nlu.org.ua/', 'title': 'Олена Степанів: Напередодні великих подій'}, 'tasks': ['Знайдіть у тексті опис мотивації вступу до УСС.', 'Які емоції описує авторка перед першим боєм?', 'Випишіть 5 військових термінів, вжитих у тексті.']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2533/4000 (raw: 2815)
- **Activities:** ✅ 6/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 6/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (6 activities)
- **Immersion:** 🇺🇦 99.8% (target 95-100% (biography))
- **Richness:** ❌ 92% < 95% min (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 92% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 14 | 3 | 100% | 14% | 14.3% |
| cultural | 1 | 4 | 25% | 10% | 2.4% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 21 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **92.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 113 | Included in Core |
| **Вступ** | ✅ | 239 | Included in Core |
| **Біографія** | ⚪️ | 742 | Skipped |
| **Сучасний контекст** | ✅ | 241 | Included in Core |
| **Історичний контекст** | ✅ | 458 | Included in Core |
| **Порівняльний аналіз** | ✅ | 224 | Included in Core |
| **Підсумок** | ✅ | 169 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 210 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 137 | Skipped |