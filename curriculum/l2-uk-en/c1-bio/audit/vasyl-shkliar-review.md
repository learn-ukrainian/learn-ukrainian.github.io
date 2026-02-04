# Audit Report: M131 — vasyl-shkliar.md
**Level:** C1-BIO | **Module:** M131 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 00:48:09

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
| 1 | reading | Первинні джерела: Уривок з роману «Чорний Ворон» | 3 | 1 | ✅ |
| 2 | reading | Літературна критика про феномен Шкляра | 3 | 1 | ✅ |
| 3 | true-false | Факти про творчість Шкляра | 5 | 5 | ✅ |
| 4 | essay-response | Творча робота: Феномен Шкляра | 1 | 1 | ✅ |
| 5 | comparative-study | Шкляр та Сенкевич: Порівняння | 1 | 1 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 4 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in vasyl-shkliar.yaml: Schema validation error at key '1': {'type': 'reading', 'title': 'Літературна критика про феномен Шкляра', 'resource': {'type': 'article', 'url': 'https://litakcent.com/2011/03/04/vasyl-shkljar-i-joho-chorney-voron/', 'title': 'Василь Шкляр і його «Чорний Ворон»'}, 'tasks': ['Чому критики називають цей роман першим українським історичним блокбастером?', 'Як автор статті оцінює вплив книги на масову свідомість українців?', 'Проаналізуйте аргументи щодо історичної достовірності роману.']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2018/4000 (raw: 2263)
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 4/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 9 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 18 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 19 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 74 | Included in Core |
| **Вступ** | ✅ | 189 | Included in Core |
| **Життєпис** | ⚪️ | 479 | Skipped |
| **Внесок** | ⚪️ | 68 | Skipped |
| **Сучасний етап** | ⚪️ | 107 | Skipped |
| **Історичний контекст** | ✅ | 254 | Included in Core |
| **Порівняльний аналіз** | ✅ | 165 | Included in Core |
| **Есе** | ⚪️ | 334 | Skipped |
| **Підсумок** | ✅ | 52 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 186 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |