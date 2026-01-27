# Audit Report: M72 — petro-bolbochan.md

**Level:** C1 | **Module:** M72 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:34

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
| 1 | quiz | «Розуміння військової звитяги» | 5 | 5 | ✅ |
| 2 | fill-in | «Військова та державницька лексика» | 12 | 6 | ✅ |
| 3 | error-correction | «Граматика у військовому репортажі» | 8 | 5 | ✅ |
| 4 | match-up | «Військова термінологія» | 8 | 6 | ✅ |
| 5 | group-sort | «Хронологія та логіка подій» | 12 | 1 | ✅ |
| 6 | select | «Лінгвістичний аналіз промови» | 5 | 5 | ✅ |
| 7 | comparative-study | «Болбочан vs Омелянович-Павленко» | 1 | 1 | ✅ |
| 8 | true-false | «Герой чи Заколотник?» | 8 | 5 | ✅ |
| 9 | unjumble | «Відновлення наказів полковника» | 5 | 5 | ✅ |
| 10 | translate | «Мова штабних документів» | 5 | 5 | ✅ |
| 11 | mark-the-words | «Словник полководця» | 9 | 5 | ✅ |
| 12 | reading | «Первинне джерело: Спогади про Кримський похід» | 3 | 1 | ✅ |
| 13 | reading | «Військовий аналіз операції» | 3 | 1 | ✅ |
| 14 | essay-response | «Болбочан: Тріумф стратегії та Трагедія політики» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 14 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[MALFORMED_ERROR_CORRECTION]** Error-correction activity '«Граматика у військовому репортажі»' uses placeholder syntax instead of real errors
  - FIX: Convert to proper error-correction format with real error words in sentences, or change to fill-in activity. Found 7/8 items with placeholders/missing errors.
- **[YAML_SCHEMA_VIOLATION]** Schema error in petro-bolbochan.yaml: Schema validation error at key 'id': 'c1-88-essay-1' does not match '^reading-[a-z0-9-]+$'
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

- **Words:** ❌ 2136/4000 (raw: 2275)
- **Activities:** ✅ 14/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ⚠️ Too many activities: 14 (target 3-9)
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
| primary_sources | 6 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 11 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 11 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 84 | Included in Core |
| **Вступ** | ✅ | 232 | Included in Core |
| **Біографія** | ⚪️ | 997 | Skipped |
| **Історичний контекст** | ✅ | 468 | Included in Core |
| **Порівняльний аналіз** | ✅ | 142 | Included in Core |
| **Підсумок** | ✅ | 127 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 86 | Skipped |
