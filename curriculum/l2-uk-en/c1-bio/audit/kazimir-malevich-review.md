# Audit Report: M76 — kazimir-malevich.md
**Level:** C1-BIO | **Module:** M76 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-08 23:14:02

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
| 1 | true-false | «Історична правда про Малевича» | 12 | 5 | ✅ |
| 2 | reading | «Філософія супрематизму: Першоджерела» | 3 | 1 | ✅ |
| 3 | reading | «Українське коріння Малевича: Дослідження» | 3 | 1 | ✅ |
| 4 | essay-response | «Колумб нескінченності: Спадщина Малевича» | 1 | 1 | ✅ |
| 5 | comparative-study | «Два шляхи модернізму: Малевич та Пікассо» | 1 | 1 | ✅ |
| 6 | critical-analysis | «Аналіз метафори «Невода предметності»» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 6 (target: 3-9) ✅
- Unique types: 5 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[MISSING_RESEARCH]** No research file found for seminar module. Expected: research/kazimir-malevich-research.md
  - FIX: Run /full-rebuild c1-bio or /research to create research notes before content generation.
- **[YAML_SCHEMA_VIOLATION]** Schema error in kazimir-malevich.yaml: Schema validation error at key '2': {'type': 'reading', 'title': '«Українське коріння Малевича: Дослідження»', 'resource': {'type': 'article', 'url': 'https://localhistory.org.ua/texts/statti/malevich-ukrayinskii-khudozhnik/', 'title': '«Казимір Малевич: Як українське село породило світовий авангард»'}, 'tasks': ['«Які саме дитячі спогади Малевича про українські села наводяться у статті?»', '«Як історики пояснюють вибір художником саме «української» ідентичності в анкетах?»', '«Знайдіть опис київського періоду роботи Малевича. Які проекти він не встиг реалізувати?»']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ❌ 2006/4000 (raw: 2235)
- **Activities:** ✅ 6/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 5/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ✅ Content-heavy OK (6 activities)
- **Immersion:** 🇺🇦 99.8% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ 1/10 (PENDING — awaiting review)

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 8 | 6 | 100% | 14% | 14.3% |
| quotes | 14 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 11 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 79 | Included in Core |
| **Вступ** | ✅ | 241 | Included in Core |
| **Життєпис** | ⚪️ | 740 | Skipped |
| **Внесок** | ⚪️ | 179 | Skipped |
| **Спадщина** | ⚪️ | 477 | Skipped |
| **Порівняльний аналіз** | ✅ | 115 | Included in Core |
| **Підсумок** | ✅ | 72 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 103 | Skipped |
| **Вправи** | ⚪️ | 0 | Skipped |
| **Словник** | ⚪️ | 0 | Skipped |