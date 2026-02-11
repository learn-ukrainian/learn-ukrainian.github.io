# Audit Report: M98 — mykola-khvylovyi.md
**Level:** C1-BIO | **Module:** M98 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-11 00:44:06

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
| 1 | true-false | Міфи та правда про Хвильового | 5 | 5 | ✅ |
| 2 | authorial-intent | Намір автора: Передсмертна записка | 1 | 1 | ✅ |
| 3 | essay-response | Аналіз трагедії: Ідеаліст у пастці | 1 | 1 | ✅ |
| 4 | comparative-study | Порівняння: Хвильовий та Маяковський | 1 | 1 | ✅ |
| 5 | critical-analysis | Аналіз будинку «Слово» | 1 | 1 | ✅ |
| 6 | reading | Новела «Я (Романтика)» | 3 | 1 | ✅ |

**Summary:**
- Total activities: 6 (target: 3-9) ✅
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 5/6 (authorial-intent, comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[MISSING_RESEARCH]** No research file found for seminar module. Expected: research/mykola-khvylovyi-research.md
  - FIX: Run /full-rebuild c1-bio or /research to create research notes before content generation.
- **[YAML_SCHEMA_VIOLATION]** Schema error in mykola-khvylovyi.yaml: Schema validation error at key '5': {'type': 'reading', 'title': 'Новела «Я (Романтика)»', 'resource': {'type': 'primary_source', 'url': 'https://ukrlib.com.ua/', 'title': 'Микола Хвильовий: Я (Романтика)'}, 'tasks': ['Знайдіть у тексті опис внутрішнього конфлікту чекіста.', 'Як автор використовує слово "запах"?', 'Які символи революції присутні в новелі?']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2236/4000 (raw: 2496)
- **Activities:** ✅ 6/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 6/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ✅ Content-heavy OK (6 activities)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ❌ 92% < 95% min (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ 1/10 (PENDING — awaiting review)

## Richness Details
**Score:** 92% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 7 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 13 | 3 | 100% | 14% | 14.3% |
| cultural | 1 | 4 | 25% | 10% | 2.4% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 28 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **92.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 106 | Included in Core |
| **Вступ** | ✅ | 228 | Included in Core |
| **Біографія** | ⚪️ | 663 | Skipped |
| **Сучасний контекст** | ✅ | 230 | Included in Core |
| **Історичний контекст** | ✅ | 382 | Included in Core |
| **Порівняльний аналіз** | ✅ | 184 | Included in Core |
| **Підсумок** | ✅ | 129 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 203 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 111 | Skipped |