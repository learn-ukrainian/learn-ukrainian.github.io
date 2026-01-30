# Audit Report: M49 — borys-hrinchenko.md
**Level:** C1 | **Module:** M49 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-30 21:15:15

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
| 1 | true-false | Історична правда про Бориса Грінченка | 8 | 5 | ✅ |
| 2 | comparative-study | Грінченко та Даль - Два полюси лексикографії | 1 | 1 | ✅ |
| 3 | reading | Дослідження Словника Грінченка | 3 | 1 | ✅ |
| 4 | reading | Просвітницька публіцистика вченого | 3 | 1 | ✅ |
| 5 | critical-analysis | Деконструкція імперського міфу про мову | 1 | 1 | ✅ |
| 6 | authorial-intent | Наміри Грінченка у статті про вчителя | 1 | 1 | ✅ |
| 7 | essay-response | «Мова як фортеця нації: Спадщина Бориса Грінченка» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 7 (target: 3-9) ✅
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 5/6 (authorial-intent, comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in borys-hrinchenko.yaml: Schema validation error at key '3': {'type': 'reading', 'title': 'Просвітницька публіцистика вченого', 'resource': {'type': 'primary_source', 'url': 'https://shron1.chtyvo.org.ua/Hrinchenko_Borys/Lysty_z_Ukrainy_Naddniprianskoi.pdf', 'title': '«Борис Грінченко: «Листи з України Наддніпрянської»»'}, 'tasks': ['«Проаналізуйте гостроту критики, яку Грінченко спрямовує проти байдужої інтелігенції.»', '«Випишіть 5-7 термінів, що описують стан тогочасної освіти та культури в підросійській Україні.»', '«Який заклик до дії формулює автор у заключній частині своїх листів?»']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина|Вплив' found: Спадщина, Вплив на сучасників
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 1917/4000 (raw: 2163)
- **Activities:** ✅ 7/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 6/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (7 activities)
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
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 14 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 27 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 73 | Included in Core |
| **Вступ** | ✅ | 193 | Included in Core |
| **Життєпис** | ⚪️ | 328 | Skipped |
| **Внесок** | ⚪️ | 635 | Skipped |
| **Спадщина** | ⚪️ | 174 | Skipped |
| **Історичний контекст** | ✅ | 302 | Included in Core |
| **Порівняльний аналіз** | ✅ | 129 | Included in Core |
| **Підсумок** | ✅ | 67 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 16 | Skipped |