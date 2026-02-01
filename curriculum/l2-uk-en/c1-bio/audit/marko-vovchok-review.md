# Audit Report: M37 — marko-vovchok.md
**Level:** C1 | **Module:** M37 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-01 23:29:20

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
| 1 | true-false | «Життя та міфи» | 12 | 5 | ✅ |
| 2 | reading | «Аналіз оповідання «Максим Гримач»» | 3 | 1 | ✅ |
| 3 | reading | «Марко Вовчок у спогадах сучасників» | 3 | 1 | ✅ |
| 4 | essay-response | «Феномен Марка Вовчка» | 1 | 1 | ✅ |
| 5 | comparative-study | «Жіночі голоси епохи: Вовчок та Санд» | 1 | 1 | ✅ |
| 6 | critical-analysis | «Аналіз психологізму «Інститутки»» | 1 | 1 | ✅ |
| 7 | true-false | «Літературні погляди» | 12 | 5 | ✅ |

**Summary:**
- Total activities: 7 (target: 3-9) ✅
- Unique types: 5 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in marko-vovchok.yaml: Schema validation error at key '2': {'type': 'reading', 'title': '«Марко Вовчок у спогадах сучасників»', 'resource': {'type': 'article', 'url': 'https://localhistory.org.ua/texts/statti/marko-vovchok-fatalna-zhinka-ukrayinskoyi-literaturi/', 'title': '«Марко Вовчок: фатальна жінка української літератури»'}, 'tasks': ['«Як описують зовнішність та характер письменниці її знайомі?»', '«Які нові деталі про її стосунки з Пантелеймоном Кулішем наводяться?»', '«Чому її називали «мовчазним сфінксом»?»']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина|Вплив' found: Вплив на європейську літературу, Спадщина
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 5/100)

- 3 violations (minor)

## Gates
- **Words:** ❌ 2035/4000 (raw: 2265)
- **Activities:** ✅ 7/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 5/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (7 activities)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
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
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 6 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 12 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 14 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 70 | Included in Core |
| **Вступ** | ✅ | 202 | Included in Core |
| **Життєпис** | ⚪️ | 979 | Skipped |
| **Внесок** | ⚪️ | 168 | Skipped |
| **Спадщина** | ⚪️ | 348 | Skipped |
| **Порівняльний аналіз** | ✅ | 115 | Included in Core |
| **Підсумок** | ✅ | 59 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 94 | Skipped |
| **Вправи** | ⚪️ | 0 | Skipped |
| **Словник** | ⚪️ | 0 | Skipped |