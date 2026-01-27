# Audit Report: M35 — marko-vovchok.md

**Level:** C1 | **Module:** M35 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:14

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
| 1 | quiz | «Розуміння біографії Марка Вовчка» | 12 | 5 | ✅ |
| 2 | fill-in | «Літературна лексика Вовчка» | 12 | 6 | ✅ |
| 3 | error-correction | «Граматика в біографії» | 12 | 5 | ✅ |
| 4 | match-up | «Літературні поняття» | 12 | 6 | ✅ |
| 5 | select | «Аналіз стилю Марка Вовчка» | 5 | 5 | ✅ |
| 6 | true-false | «Життя та міфи» | 12 | 5 | ✅ |
| 7 | reading | «Аналіз оповідання «Максим Гримач»» | 3 | 1 | ✅ |
| 8 | reading | «Марко Вовчок у спогадах сучасників» | 3 | 1 | ✅ |
| 9 | essay-response | «Феномен Марка Вовчка» | 1 | 1 | ✅ |
| 10 | comparative-study | «Жіночі голоси епохи: Вовчок та Санд» | 1 | 1 | ✅ |
| 11 | critical-analysis | «Аналіз психологізму «Інститутки»» | 1 | 1 | ✅ |
| 12 | unjumble | «Відновлення думок про письменницю» | 12 | 5 | ✅ |
| 13 | translate | «Словник біографа» | 12 | 5 | ✅ |
| 14 | mark-the-words | «Пошук біографічних фактів» | 10 | 5 | ✅ |
| 15 | true-false | «Літературні погляди» | 12 | 5 | ✅ |

**Summary:**
- Total activities: 15 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 5/6 (comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 5/6 (essay-response, fill-in, match-up, quiz, reading) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in marko-vovchok.yaml: Schema validation error at key 'words': ['«Її»', '«Народні»', '«оповідання»', '«стали»', '«літературною»', '«сенсацією', '»', '«відкривши»', '«світові»', '«трагедію»', '«українського»', '«кріпацтва»', '«очима»', '«жінки.»'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина|Вплив' found: Спадщина, Вплив на європейську літературу
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation

**📝 UPDATE** (severity 5/100)

- 3 violations (minor)

## Gates

- **Words:** ❌ 2035/4000 (raw: 2265)
- **Activities:** ✅ 15/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 15 (target 3-9)
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
