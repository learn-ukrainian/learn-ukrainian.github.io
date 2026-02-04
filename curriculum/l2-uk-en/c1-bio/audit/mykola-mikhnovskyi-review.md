# Audit Report: M71 — mykola-mikhnovskyi.md
**Level:** C1-BIO | **Module:** M71 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-04 11:41:54

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
| 1 | true-false | «Факти та міфи про Міхновського» | 12 | 5 | ✅ |
| 2 | reading | «Юридичний аналіз «Самостійної України»» | 3 | 1 | ✅ |
| 3 | reading | «Постать Міхновського в сучасній історіографії» | 3 | 1 | ✅ |
| 4 | essay-response | «Пророк волі: Спадщина Міхновського» | 1 | 1 | ✅ |
| 5 | comparative-study | «Два шляхи до свободи: Міхновський та Грушевський» | 1 | 1 | ✅ |
| 6 | critical-analysis | «Аналіз юридичної логіки маніфесту» | 1 | 1 | ✅ |
| 7 | true-false | «Політична стратегія Міхновського» | 12 | 5 | ✅ |

**Summary:**
- Total activities: 7 (target: 3-9) ✅
- Unique types: 5 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in mykola-mikhnovskyi.yaml: Schema validation error at key '2': {'type': 'reading', 'title': '«Постать Міхновського в сучасній історіографії»', 'resource': {'type': 'article', 'url': 'https://localhistory.org.ua/texts/statti/mikola-mikhnovskii-pershii-samostiinik/', 'title': '«Микола Міхновський: перший самостійник Наддніпрянщини»'}, 'tasks': ['«Як історики оцінюють конфлікт Міхновського з Винниченком сьогодні?»', '«Які нові факти про смерть діяча наводяться у сучасних дослідженнях?»', '«Знайдіть опис «Десяти заповідей» та проаналізуйте їхній вплив на молодь.»']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ❌ 2160/4000 (raw: 2389)
- **Activities:** ✅ 7/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 5/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ✅ Valid Structure
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
| primary_sources | 14 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 8 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 68 | Included in Core |
| **Вступ** | ✅ | 220 | Included in Core |
| **Життєпис** | ⚪️ | 603 | Skipped |
| **Внесок** | ⚪️ | 327 | Skipped |
| **Спадщина** | ⚪️ | 643 | Skipped |
| **Порівняльний аналіз** | ✅ | 136 | Included in Core |
| **Підсумок** | ✅ | 76 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 87 | Skipped |
| **Вправи** | ⚪️ | 0 | Skipped |
| **Словник** | ⚪️ | 0 | Skipped |