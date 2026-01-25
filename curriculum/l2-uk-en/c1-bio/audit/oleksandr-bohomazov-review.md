# Audit Report: M69 — oleksandr-bohomazov.md
**Level:** C1 | **Module:** M69 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:27:23

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
| 1 | quiz | «Життя і творчість Олександра Богомазова» | 12 | 5 | ✅ |
| 2 | fill-in | «Словник авангарду» | 12 | 6 | ✅ |
| 3 | error-correction | «Граматика мистецтвознавства» | 12 | 5 | ✅ |
| 4 | match-up | «Терміни авангарду» | 12 | 6 | ✅ |
| 5 | select | «Аналіз творчого методу» | 5 | 5 | ✅ |
| 6 | true-false | «Факти про художника» | 12 | 5 | ✅ |
| 7 | reading | «Маніфест «Живопис та елементи»» | 3 | 1 | ✅ |
| 8 | reading | «Історія порятунку спадщини» | 3 | 1 | ✅ |
| 9 | essay-response | «Український авангард: Втрачене і повернуте» | 1 | 1 | ✅ |
| 10 | comparative-study | «Богомазов та Боччоні» | 1 | 1 | ✅ |
| 11 | critical-analysis | «Аналіз цитати про ритм» | 1 | 1 | ✅ |
| 12 | unjumble | «Відновлення думок про авангард» | 11 | 5 | ✅ |
| 13 | translate | «Мова мистецтвознавства» | 12 | 5 | ✅ |
| 14 | mark-the-words | «Пошук теоретичних понять» | 11 | 5 | ✅ |
| 15 | quiz | «Біографічні деталі» | 5 | 5 | ✅ |
| 16 | true-false | «Міфи про Богомазова» | 12 | 5 | ✅ |
| 17 | translate | «Словник теоретика» | 12 | 5 | ✅ |
| 18 | mark-the-words | «Пошук кольорів та форм» | 11 | 5 | ✅ |

**Summary:**
- Total activities: 18 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 5/6 (comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 5/6 (essay-response, fill-in, match-up, quiz, reading) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[MALFORMED_ERROR_CORRECTION]** Error-correction activity '«Граматика мистецтвознавства»' uses placeholder syntax instead of real errors
  - FIX: Convert to proper error-correction format with real error words in sentences, or change to fill-in activity. Found 11/12 items with placeholders/missing errors.
- **[YAML_SCHEMA_VIOLATION]** Schema error in oleksandr-bohomazov.yaml: Schema validation error at key 'id': 'c1-85-mark-words-1' does not match '^reading-[a-z0-9-]+$'
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 25/100)

- 3 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2398/4000 (raw: 2605)
- **Activities:** ✅ 18/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ⚠️ Too many activities: 18 (target 3-9)
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
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 11 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 11 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 67 | Included in Core |
| **Вступ** | ✅ | 223 | Included in Core |
| **Життєпис** | ⚪️ | 979 | Skipped |
| **Внесок** | ⚪️ | 179 | Skipped |
| **Спадщина** | ⚪️ | 683 | Skipped |
| **Порівняльний аналіз** | ✅ | 105 | Included in Core |
| **Підсумок** | ✅ | 67 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 95 | Skipped |