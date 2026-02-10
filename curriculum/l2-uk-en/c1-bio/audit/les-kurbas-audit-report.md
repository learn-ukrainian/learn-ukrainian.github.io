# Audit Report: M86 — les-kurbas.md
**Level:** C1-BIO | **Module:** M86 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-09 23:24:45

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
| 1 | true-false | Факти про життя Леся Курбаса | 5 | 5 | ✅ |
| 2 | authorial-intent | Намір автора: Сповідь режисера | 1 | 1 | ✅ |
| 3 | essay-response | Аналіз спадщини: Курбас і модерна Україна | 1 | 1 | ✅ |
| 4 | comparative-study | Порівняння: Курбас vs Брехт | 1 | 1 | ✅ |
| 5 | critical-analysis | Аналіз трагедії Сандармоху | 1 | 1 | ✅ |
| 6 | reading | Маніфести «Березоля» | 3 | 1 | ✅ |

**Summary:**
- Total activities: 6 (target: 3-9) ✅
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 5/6 (authorial-intent, comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[MISSING_RESEARCH]** No research file found for seminar module. Expected: research/les-kurbas-research.md
  - FIX: Run /full-rebuild c1-bio or /research to create research notes before content generation.
- **[YAML_SCHEMA_VIOLATION]** Schema error in les-kurbas.yaml: Schema validation error at key '5': {'type': 'reading', 'title': 'Маніфести «Березоля»', 'resource': {'type': 'primary_source', 'url': 'https://elib.nlu.org.ua/', 'title': 'Лесь Курбас: Програма Березіль'}, 'tasks': ['Знайдіть у тексті маніфесту слова, що означають «рух» та «зміну».', 'Який відмінок використовується для означення мети театру?', 'Поясніть термін «інтелектуалізація» за текстом.']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2050/4000 (raw: 2292)
- **Activities:** ✅ 6/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 6/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ✅ Content-heavy OK (6 activities)
- **Immersion:** 🇺🇦 99.7% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ 1/10 (PENDING — awaiting review)

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 102 | Included in Core |
| **Вступ** | ✅ | 256 | Included in Core |
| **Біографія** | ⚪️ | 1063 | Skipped |
| **Історичний контекст** | ✅ | 231 | Included in Core |
| **Порівняльний аналіз** | ✅ | 146 | Included in Core |
| **Підсумок** | ✅ | 150 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 102 | Skipped |