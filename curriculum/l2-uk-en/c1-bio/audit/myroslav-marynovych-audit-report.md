# Audit Report: M138 — myroslav-marynovych.md
**Level:** C1-BIO | **Module:** M138 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-09 23:25:12

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
| 1 | reading | Первинні джерела: Мирослав Маринович про цінності | 3 | 1 | ✅ |
| 2 | reading | Науковий нарис про Українську Гельсінську групу | 3 | 1 | ✅ |
| 3 | true-false | Факти про Мариновича | 5 | 5 | ✅ |
| 4 | essay-response | Творча робота: Уроки Мариновича | 1 | 1 | ✅ |
| 5 | comparative-study | Маринович та сучасність: Порівняння | 1 | 1 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 4 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[MISSING_RESEARCH]** No research file found for seminar module. Expected: research/myroslav-marynovych-research.md
  - FIX: Run /full-rebuild c1-bio or /research to create research notes before content generation.
- **[YAML_SCHEMA_VIOLATION]** Schema error in myroslav-marynovych.yaml: Schema validation error at key '1': {'type': 'reading', 'title': 'Науковий нарис про Українську Гельсінську групу', 'resource': {'type': 'article', 'url': 'https://uinp.gov.ua/informaciyni-materialy/vchytelyam/metodychni-rekomendaciyi/ukrayinska-gelsinska-grupa-pravo-na-pravdu', 'title': 'Українська Гельсінська група: право на правду'}, 'tasks': ['Яка роль Мирослава Мариновича у заснуванні УГГ?', 'Знайдіть у тексті лексику, що описує репресивний апарат СРСР.', 'Як історики оцінюють ненасильницький характер дисидентського опору?']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2102/4000 (raw: 2373)
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 4/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ 1/10 (PENDING — awaiting review)

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