# Audit Report: M91 — vasyl-vyshyvanyi.md
**Level:** C1 | **Module:** M91 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-01 23:29:43

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
| 1 | true-false | Факти про «українського принца» | 5 | 5 | ✅ |
| 2 | authorial-intent | Намір автора: Лист до Шептицького | 1 | 1 | ✅ |
| 3 | essay-response | Аналіз феномену: Ідентичність за вибором | 1 | 1 | ✅ |
| 4 | comparative-study | Порівняння: Вишиваний та Скоропадський | 1 | 1 | ✅ |
| 5 | critical-analysis | Аналіз шпигунської справи | 1 | 1 | ✅ |
| 6 | reading | Поезія Василя Вишиваного | 3 | 1 | ✅ |

**Summary:**
- Total activities: 6 (target: 3-9) ✅
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 5/6 (authorial-intent, comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in vasyl-vyshyvanyi.yaml: Schema validation error at key '5': {'type': 'reading', 'title': 'Поезія Василя Вишиваного', 'resource': {'type': 'primary_source', 'url': 'https://elib.nlu.org.ua/', 'title': 'Василь Вишиваний: Минають дні'}, 'tasks': ['Знайдіть у віршах епітети, що описують Україну.', 'Як поет використовує звертання до свого народу?', 'Проаналізуйте вживання дієслів минулого часу в контексті ностальгії.']} is not valid under any of the given schemas
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
- **Words:** ❌ 2091/4000 (raw: 2345)
- **Activities:** ✅ 6/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 6/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (6 activities)
- **Immersion:** 🇺🇦 99.8% (target 95-100% (biography))
- **Richness:** ✅ 100% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 100% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 9 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 11 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 13 | 2 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 14 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 92 | Included in Core |
| **Вступ** | ✅ | 280 | Included in Core |
| **Біографія** | ⚪️ | 979 | Skipped |
| **Історичний контекст** | ✅ | 334 | Included in Core |
| **Порівняльний аналіз** | ✅ | 161 | Included in Core |
| **Підсумок** | ✅ | 129 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 116 | Skipped |