# Audit Report: M137 — vasyl-stus.md
**Level:** C1-BIO | **Module:** M137 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-11 00:44:26

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
| 1 | reading | Первинні джерела: Поезія Василя Стуса | 3 | 1 | ✅ |
| 2 | reading | Науковий нарис про «Палімпсести» | 3 | 1 | ✅ |
| 3 | true-false | Трагічний шлях Стуса | 5 | 5 | ✅ |
| 4 | essay-response | Творча робота: Феномен Стуса | 1 | 1 | ✅ |
| 5 | comparative-study | Стус та європейський модернізм: Порівняння | 1 | 1 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 4 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[MISSING_RESEARCH]** No research file found for seminar module. Expected: research/vasyl-stus-research.md
  - FIX: Run /full-rebuild c1-bio or /research to create research notes before content generation.
- **[YAML_SCHEMA_VIOLATION]** Schema error in vasyl-stus.yaml: Schema validation error at key '1': {'type': 'reading', 'title': 'Науковий нарис про «Палімпсести»', 'resource': {'type': 'article', 'url': 'https://stus.center/uk/texts/palimpsesty-vasylya-stusa-v-konteksti-evropeyskogo-modernizmu', 'title': '«Палімпсести» Стуса в контексті європейського модернізму'}, 'tasks': ['Чому збірка Стуса отримала назву «Палімпсести»? Яке символічне значення цього терміна?', "Проаналізуйте зв'язок поезії Стуса з ідеями європейського екзистенціалізму.", 'Які лінгвістичні засоби використовує поет для передачі стану відчуження та внутрішньої свободи?']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2250/4000 (raw: 2550)
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
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ 1/10 (PENDING — awaiting review)

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 11 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 13 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 16 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Вступ** | ✅ | 217 | Included in Core |
| **Біографія** | ⚪️ | 746 | Skipped |
| **Історичний контекст** | ✅ | 223 | Included in Core |
| **Порівняльний аналіз** | ✅ | 207 | Included in Core |
| **Есе** | ⚪️ | 383 | Skipped |
| **Підсумок** | ✅ | 58 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 215 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 129 | Skipped |