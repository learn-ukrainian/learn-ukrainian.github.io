# Audit Report: M38 — marko-kropyvnytskyi.md
**Level:** C1 | **Module:** M38 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:15

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
| 1 | quiz | «Життя та сцена Марка Кропивницького» | 12 | 5 | ✅ |
| 2 | fill-in | «Театральна лексика Кропивницького» | 12 | 6 | ✅ |
| 3 | error-correction | «Граматика театрального життя» | 12 | 5 | ✅ |
| 4 | match-up | «Театральний словник» | 12 | 6 | ✅ |
| 5 | select | «Аналіз феномену корифеїв» | 5 | 5 | ✅ |
| 6 | true-false | «Правда про батька театру» | 12 | 5 | ✅ |
| 7 | reading | «Рецензії на вистави корифеїв» | 3 | 1 | ✅ |
| 8 | reading | «Аналіз драми «Дай серцю волю...»» | 3 | 1 | ✅ |
| 9 | essay-response | «Театр як націотворення» | 1 | 1 | ✅ |
| 10 | comparative-study | «Кропивницький та Станіславський» | 1 | 1 | ✅ |
| 11 | critical-analysis | «Відмова імператору» | 1 | 1 | ✅ |
| 12 | unjumble | «Відновлення думок про театр» | 12 | 5 | ✅ |
| 13 | translate | «Театральний переклад» | 12 | 5 | ✅ |
| 14 | mark-the-words | «Пошук театральних професій» | 9 | 5 | ✅ |

**Summary:**
- Total activities: 14 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 5/6 (comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 5/6 (essay-response, fill-in, match-up, quiz, reading) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[MALFORMED_ERROR_CORRECTION]** Error-correction activity '«Граматика театрального життя»' uses placeholder syntax instead of real errors
  - FIX: Convert to proper error-correction format with real error words in sentences, or change to fill-in activity. Found 11/12 items with placeholders/missing errors.
- **[YAML_SCHEMA_VIOLATION]** Schema error in marko-kropyvnytskyi.yaml: Schema validation error at key 'id': 'c1-83-mark-words-1' does not match '^reading-[a-z0-9-]+$'
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 3 violations (minor)

## Gates
- **Words:** ❌ 1914/4000 (raw: 2103)
- **Activities:** ✅ 14/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ⚠️ Too many activities: 14 (target 3-9)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 8 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 12 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 23 | 8 | 100% | 10% | 9.5% |
| legacy | 14 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 68 | Included in Core |
| **Вступ** | ✅ | 242 | Included in Core |
| **Життєпис** | ⚪️ | 759 | Skipped |
| **Внесок** | ⚪️ | 187 | Skipped |
| **Спадщина** | ⚪️ | 370 | Skipped |
| **Порівняльний аналіз** | ✅ | 128 | Included in Core |
| **Підсумок** | ✅ | 73 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 87 | Skipped |
| **Вправи** | ⚪️ | 0 | Skipped |
| **Словник** | ⚪️ | 0 | Skipped |