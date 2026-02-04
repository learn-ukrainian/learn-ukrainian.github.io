# Audit Report: M35 — dmytro-bortnyanskyy.md
**Level:** C1-BIO | **Module:** M35 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** None/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-04 11:41:34

## Configuration
**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** critical-analysis, essay-response, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | essay-response | Критичний аналіз: Митець та Імперія | 1 | 1 | ✅ |
| 2 | comparative-study | Порівняння: Бортнянський vs Березовський | 1 | 1 | ✅ |
| 3 | true-false | Факти та інтерпретації | 8 | 5 | ✅ |
| 4 | reading | Аналіз музикознавчого нарису | 3 | 1 | ✅ |
| 5 | reading | Дослідження спадщини | 3 | 1 | ✅ |
| 6 | essay-response | Порівняльне есе: Бортнянський та Березовський | 1 | 1 | ✅ |

**Summary:**
- Total activities: 6 (target: 3-9) ✅
- Unique types: 4 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, reading) ✅
- Required types used: 2/3 (essay-response, reading) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in dmytro-bortnyanskyy.yaml: Schema validation error at key '4': {'type': 'reading', 'title': 'Дослідження спадщини', 'resource': {'type': 'primary_source', 'url': 'https://www.youtube.com/watch?v=R6w6_79VnOQ', 'title': "Дмитро Бортнянський: Концерт №32 'Скажи ми, Господи, кончину мою'"}, 'tasks': ['Прослухайте твір та опишіть його емоційну динаміку, використовуючи лексику модуля.', "Які музичні інструменти (якщо є) ви чуєте? Чому для Бортнянського було важливо саме хорове виконання 'a cappella'?", 'Знайдіть у тексті (або почуйте) ключові слова, що вказують на релігійний зміст твору.']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2073/4000 (raw: 2287)
- **Activities:** ✅ 6/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 4/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (6 activities)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ None/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 6 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 11 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 22 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 13 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 70 | Included in Core |
| **Вступ** | ✅ | 322 | Included in Core |
| **Життєпис** | ⚪️ | 392 | Skipped |
| **Внесок** | ⚪️ | 189 | Skipped |
| **Спадщина** | ⚪️ | 123 | Skipped |
| **Історичний контекст** | ✅ | 327 | Included in Core |
| **Порівняльний аналіз** | ✅ | 126 | Included in Core |
| **Критичне мислення** | ⚪️ | 78 | Skipped |
| **Есе** | ⚪️ | 298 | Skipped |
| **Підсумок** | ✅ | 80 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 68 | Skipped |