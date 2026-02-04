# Audit Report: M103 — berta-rapoport.md
**Level:** C1-BIO | **Module:** M103 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 00:47:56

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
| 1 | true-false | Факти про Берту Рапопорт | 5 | 5 | ✅ |
| 2 | authorial-intent | Намір автора: Маніфест капітанки | 1 | 1 | ✅ |
| 3 | essay-response | Аналіз бар’єрів: Берта Рапопорт | 1 | 1 | ✅ |
| 4 | comparative-study | Порівняння: Рапопорт та Щетиніна | 1 | 1 | ✅ |
| 5 | critical-analysis | Аналіз «Морського забобону» | 1 | 1 | ✅ |
| 6 | reading | Морський статут та етика | 3 | 1 | ✅ |

**Summary:**
- Total activities: 6 (target: 3-9) ✅
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 5/6 (authorial-intent, comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (100% overlap): "Вона назавжди залишиться нашою першою Капітанкою, яка веде Україну крізь тумани історії до берегів с...". Shares significant keywords with sentence at index 57.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in berta-rapoport.yaml: Schema validation error at key '5': {'type': 'reading', 'title': 'Морський статут та етика', 'resource': {'type': 'primary_source', 'url': 'https://zakon.rada.gov.ua/', 'title': 'Кодекс торговельного мореплавства України'}, 'tasks': ['Знайдіть у тексті обов’язки капітана судна.', 'Які терміни використовуються для опису аварійних ситуацій?', 'Поясніть значення слова «фрахтування».']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2060/4000 (raw: 2296)
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
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 7 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.96 | - | 96% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 14 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 114 | Included in Core |
| **Вступ** | ✅ | 235 | Included in Core |
| **Біографія** | ⚪️ | 938 | Skipped |
| **Історичний контекст** | ✅ | 365 | Included in Core |
| **Порівняльний аналіз** | ✅ | 173 | Included in Core |
| **Підсумок** | ✅ | 120 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 115 | Skipped |