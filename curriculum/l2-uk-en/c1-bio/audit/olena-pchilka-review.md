# Audit Report: M49 — olena-pchilka.md
**Level:** C1-BIO | **Module:** M49 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-04 11:41:42

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
| 1 | essay-response | Критичний аналіз: Виховання еліти | 1 | 1 | ✅ |
| 2 | comparative-study | Мати і Донька | 1 | 1 | ✅ |
| 3 | reading | Спогади про Пчілку | 3 | 1 | ✅ |
| 4 | reading | Стаття про фемінізм | 3 | 1 | ✅ |
| 5 | essay-response | Есе: Інженер душі | 1 | 1 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 3 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in olena-pchilka.yaml: Schema validation error at key '3': {'type': 'reading', 'title': 'Стаття про фемінізм', 'resource': {'type': 'article', 'url': 'https://povaha.org.ua/olena-pchilka-persha-ukrajinska-feministka/', 'title': 'Олена Пчілка — перша українська феміністка?'}, 'tasks': ['Які аргументи наводить автор на користь фемінізму Пчілки?', 'Як вона поєднувала традиційні сімейні цінності з емансипацією?', "Яку роль відіграв альманах 'Перший вінок' у жіночому русі?"]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2037/4000 (raw: 2288)
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 3/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 6 | 4 | 100% | 10% | 9.5% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 23 | 8 | 100% | 10% | 9.5% |
| legacy | 13 | 2 | 100% | 10% | 9.5% |
| variety | 0.95 | - | 95% | 5% | 4.5% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 78 | Included in Core |
| **Вступ** | ✅ | 145 | Included in Core |
| **Життєпис** | ⚪️ | 551 | Skipped |
| **Спадщина** | ⚪️ | 53 | Skipped |
| **Внесок** | ⚪️ | 237 | Skipped |
| **Історичний контекст** | ✅ | 494 | Included in Core |
| **Порівняльний аналіз** | ✅ | 50 | Included in Core |
| **Критичне мислення** | ⚪️ | 76 | Skipped |
| **Есе** | ⚪️ | 35 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 249 | Skipped |
| **Підсумок** | ✅ | 55 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 14 | Skipped |