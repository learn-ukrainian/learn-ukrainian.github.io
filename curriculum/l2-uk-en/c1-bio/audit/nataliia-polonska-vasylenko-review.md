# Audit Report: M74 — nataliia-polonska-vasylenko.md
**Level:** C1 | **Module:** M74 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:36

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
| 1 | quiz | «Розуміння наукового шляху» | 5 | 5 | ✅ |
| 2 | fill-in | «Академічна та біографічна лексика» | 12 | 6 | ✅ |
| 3 | error-correction | «Граматика наукового тексту» | 8 | 5 | ✅ |
| 4 | match-up | «Академічна термінологія» | 8 | 6 | ✅ |
| 5 | group-sort | «Етапи творчого шляху» | 12 | 1 | ✅ |
| 6 | select | «Лінгвістичний аналіз джерела» | 5 | 5 | ✅ |
| 7 | comparative-study | «Полонська-Василенко vs Грушевський» | 1 | 1 | ✅ |
| 8 | true-false | «Факти про Берегиню правди» | 8 | 5 | ✅ |
| 9 | unjumble | «Тези про історичну пам'ять» | 5 | 5 | ✅ |
| 10 | translate | «Академічний переклад» | 5 | 5 | ✅ |
| 11 | mark-the-words | «Словник історика» | 8 | 5 | ✅ |
| 12 | reading | «Первинне джерело: «Історія України»» | 3 | 1 | ✅ |
| 13 | reading | «Археологія Києва: Софійські розкопки» | 3 | 1 | ✅ |
| 14 | essay-response | «Берегиня історичної пам'яті» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 14 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[MALFORMED_ERROR_CORRECTION]** Error-correction activity '«Граматика наукового тексту»' uses placeholder syntax instead of real errors
  - FIX: Convert to proper error-correction format with real error words in sentences, or change to fill-in activity. Found 7/8 items with placeholders/missing errors.
- **[YAML_SCHEMA_VIOLATION]** Schema error in nataliia-polonska-vasylenko.yaml: Schema validation error at key 'id': 'c1-89-essay-1' does not match '^reading-[a-z0-9-]+$'
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

- 5 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2027/4000 (raw: 2181)
- **Activities:** ✅ 14/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
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
| primary_sources | 6 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 8 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.96 | - | 96% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 16 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 89 | Included in Core |
| **Вступ** | ✅ | 197 | Included in Core |
| **Біографія** | ⚪️ | 1160 | Skipped |
| **Історичний контекст** | ✅ | 187 | Included in Core |
| **Порівняльний аналіз** | ✅ | 183 | Included in Core |
| **Підсумок** | ✅ | 148 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 63 | Skipped |