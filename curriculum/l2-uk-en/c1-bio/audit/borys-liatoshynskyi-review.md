# Audit Report: M86 — borys-liatoshynskyi.md

**Level:** C1 | **Module:** M86 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:41

## Configuration

**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** essay-response, fill-in, group-sort, match-up, quiz, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown

| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Розуміння тексту: Життя Бориса Лятошинського | 5 | 5 | ✅ |
| 2 | fill-in | Лексика: Музика та Цензура | 6 | 6 | ✅ |
| 3 | error-correction | Граматика: Біографічні факти | 5 | 5 | ✅ |
| 4 | match-up | Музичний словник | 8 | 6 | ✅ |
| 5 | select | Лінгвістичний аналіз джерел | 5 | 5 | ✅ |
| 6 | group-sort | Життя та творчість Лятошинського | 12 | 1 | ✅ |
| 7 | true-false | Факти про композитора | 5 | 5 | ✅ |
| 8 | authorial-intent | Намір автора: Лист про музику | 1 | 1 | ✅ |
| 9 | essay-response | Аналіз конфлікту: Митець і Влада | 1 | 1 | ✅ |
| 10 | comparative-study | Порівняння: Лятошинський та Шостакович | 1 | 1 | ✅ |
| 11 | critical-analysis | Аналіз музичного модернізму | 1 | 1 | ✅ |
| 12 | translate | Переклад термінів: Музика та Емоції | 5 | 5 | ✅ |
| 13 | reading | Лятошинський про музику | 3 | 1 | ✅ |

**Summary:**
- Total activities: 13 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 6/6 (authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in borys-liatoshynskyi.yaml: Schema validation error at key '12': {'type': 'reading', 'title': 'Лятошинський про музику', 'resource': {'type': 'primary_source', 'url': 'https://elib.nlu.org.ua/', 'title': 'Листи Бориса Лятошинського'}, 'tasks': ['Як композитор описує свій творчий процес?', 'Які слова він використовує для характеристики стану душі?', 'Знайдіть у тексті згадку про критику.']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation

**📝 UPDATE** (severity 35/100)

- 4 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2008/4000 (raw: 2244)
- **Activities:** ✅ 13/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 13 (target 3-9)
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
| primary_sources | 6 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 9 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 22 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 102 | Included in Core |
| **Вступ** | ✅ | 233 | Included in Core |
| **Біографія** | ⚪️ | 633 | Skipped |
| **Сучасний контекст** | ✅ | 165 | Included in Core |
| **Історичний контекст** | ✅ | 313 | Included in Core |
| **Порівняльний аналіз** | ✅ | 162 | Included in Core |
| **Підсумок** | ✅ | 111 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 184 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 105 | Skipped |
