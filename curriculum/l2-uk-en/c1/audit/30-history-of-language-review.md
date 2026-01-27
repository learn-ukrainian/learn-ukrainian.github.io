# Audit Report: M30 — 30-history-of-language.md

**Level:** C1 | **Module:** M30 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** None/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:29:13

## Configuration

**Type:** C1-history
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** comparative-study, critical-analysis, essay-response, reading
**Required Types:** cloze, fill-in, group-sort, match-up, quiz, true-false
**Engagement:** ≥6 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥25 words
**Transliteration:** Not allowed

## Activity Breakdown

| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Походження української мови | 8 | 5 | ✅ |
| 2 | match-up | Історичні терміни | 14 | 6 | ✅ |
| 3 | fill-in | Хронологія репресій | 8 | 6 | ✅ |
| 4 | group-sort | Епохи розвитку | 16 | 1 | ✅ |
| 5 | unjumble | Цитата Юрія Шевельова | 6 | 5 | ✅ |
| 6 | mark-the-words | Знайдіть архаїзми | 11 | 5 | ✅ |
| 7 | quiz | Міфи про мову | 8 | 5 | ✅ |
| 8 | essay-response | Сучасне відродження | 1 | 1 | ✅ |
| 9 | fill-in | Радянські міфи | 8 | 6 | ✅ |
| 10 | match-up | Хто це сказав? | 8 | 6 | ✅ |
| 11 | comparative-study | Порівняння указів | 1 | 1 | ✅ |
| 12 | error-correction | Історична правда | 6 | 5 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 9 (minimum: 3) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 4/6 (fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in 30-history-of-language.yaml: Schema validation error at key 'min_words': 100 is less than the minimum of 200
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Аналіз' per template 'c1-module-template.md'
  - FIX: Add '## Аналіз' section as specified in docs/l2-uk-en/templates/c1-module-template.md.md

## Recommendation

**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2004/4000 (raw: 2080)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 9/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9); 1 fill-in with year answers
- **Immersion:** 🇺🇦 98.9% (target 95-100% (history))
- **Richness:** ❌ 76% < 95% min (content)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ None/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 76% (minimum: 95%)
**Module Type:** content

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 1 | 15 | 7% | 25% | 1.8% |
| engagement | 7 | 5 | 100% | 19% | 18.7% |
| variety | 0.99 | - | 99% | 12% | 12.4% |
| cultural | 8 | 4 | 100% | 12% | 12.5% |
| realworld | 5 | 3 | 100% | 12% | 12.5% |
| visual | 7 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 5 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **76.6%** |

### Dryness Flags & Fixes

- ❌ **NO_EXAMPLES**
  - FIX:
    Add 24+ example sentences. Each grammar point needs 3-4 examples showing the pattern in context.

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 41 | Included in Core |
| **Походження та родинні зв'язки** | ⚪️ | 260 | Skipped |
| **Золота доба** | ⚪️ | 151 | Skipped |
| **Деколонізаційний погляд** | ✅ | 237 | Included in Core |
| **Радянська епоха** | ⚪️ | 188 | Skipped |
| **Відродження та Сучасність** | ⚪️ | 235 | Skipped |
| **Первинні джерела** | ✅ | 149 | Included in Core |
| **8. Приклади історичних змін** | ⚪️ | 147 | Skipped |
| **9. Читання: Голос діаспори** | ✅ | 150 | Included in Core |
| **Підсумок** | ✅ | 109 | Included in Core |
| **Історичний контекст: Механізм лінгвоциду** | ✅ | 109 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 107 | Skipped |
| **Історичні постаті** | ⚪️ | 121 | Skipped |
