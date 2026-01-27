# Audit Report: M130 — syntez-nezalezhnist.md

**Level:** B2 | **Module:** M130 | **Phase:** HIST.12 | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 10/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:55:32

## Configuration

**Type:** B2-history
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥2 types required
**Priority Types:** comparative-study, critical-analysis, essay-response, reading
**Required Types:** essay-response, match-up, quiz, reading
**Engagement:** ≥5 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥20 words
**Transliteration:** Not allowed

## PEDAGOGICAL VIOLATIONS

- **[HEADING_LEVEL]** Main section 'Підсумок' uses H2 (##) but spec requires H1 (#)
  - FIX: Change '## Підсумок' to '# Підсумок' for top-level TOC compliance
- **[YAML_SCHEMA_VIOLATION]** Schema error in syntez-nezalezhnist.yaml: Insufficient activities: 1 found, minimum 5 required for B2-HIST
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.
- **[STATE_STANDARD_LOW_IMMERSION]** Module 130 has 19.7% immersion (target: 90.0%+)
  - FIX: Add more Ukrainian content to reach 90.0%+ immersion

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template.md'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Деколонізаційний погляд' per template 'b2-history-module-template.md'
  - FIX: Add '## Деколонізаційний погляд' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md.md
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!myth-buster]' per template 'b2-history-module-template.md'
  - FIX: Add a `> [!myth-buster]` box as specified in the template. This enhances module quality.
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!history-bite]' per template 'b2-history-module-template.md'
  - FIX: Add a `> [!history-bite]` box as specified in the template. This enhances module quality.
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!quote]' per template 'b2-history-module-template.md'
  - FIX: Add a `> [!quote]` box as specified in the template. This enhances module quality.

## Recommendation

**🔄 REWRITE** (severity 100/100)

- 10 violations (significant)
- Immersion 70% off target (major rebalancing needed)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar
- Activity count below minimum
- Activity density below minimum

## Gates

- **Words:** ❌ 26/4000 (raw: 97)
- **Activities:** ❌ 0/3
- **Density:** ❌ 0 < 1
- **Unique_types:** ❌ 0/2 types
- **Priority:** ❌ No priority types
- **Engagement:** ❌ 0/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 4 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 3-9)
- **Immersion:** ❌ 19.7% LOW (target 90-100% (history))
- **Richness:** ❌ 14% < 95% min (history) - REWRITE needed
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 10/10 (High)

## Richness Details

**Score:** 14% (minimum: 95%)
**Module Type:** history

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 0 | 3 | 0% | 24% | 0.0% |
| engagement | 0 | 6 | 0% | 14% | 0.0% |
| timeline_markers | 2 | 10 | 20% | 14% | 2.9% |
| decolonization | 1 | 2 | 50% | 14% | 7.1% |
| cultural | 0 | 4 | 0% | 10% | 0.0% |
| visual | 0 | 4 | 0% | 10% | 0.0% |
| variety | 0.50 | - | 50% | 5% | 2.4% |
| paragraph_var | 0.50 | - | 50% | 5% | 2.4% |
| questions | 0 | 3 | 0% | 5% | 0.0% |
| **TOTAL** | | | | | **14.8%** |

### Dryness Flags & Fixes

- ❌ **NO_ENGAGEMENT**
  - FIX:
    Add 2+ engagement boxes. Use this exact format:

    > 💡 **Чи знали ви?**
    >
    > [Interesting fact about the grammar/vocabulary topic in Ukrainian]

    > 🇺🇦 **Культурний момент**
    >
    > [Cultural context connecting grammar to Ukrainian life/places]

    > 🌍 **У реальному житті**
    >
    > [Practical scenario where this grammar is used]
- ❌ **NO_PRIMARY_SOURCES**
  - FIX:
    Add 2+ primary source quotes. Use this format:

    > «[Exact quote from historical document]»
    > — *[Source name], [year]*
- ❌ **NO_TIMELINE**
  - FIX:
    Add 5+ timeline markers: specific years (1876, 1918), periods (XVIII ст.), sequences (спочатку... потім... нарешті).

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 14 | Included in Core |
| **Синтез: Незалежна Україна** | ⚪️ | 0 | Skipped |
| **Вступ** | ✅ | 2 | Included in Core |
| **Основний зміст** | ⚪️ | 2 | Skipped |
| **Історичне значення** | ⚪️ | 1 | Skipped |
| **Ключові постаті** | ⚪️ | 2 | Skipped |
| **Первинні джерела** | ✅ | 4 | Included in Core |
| **Підсумок** | ✅ | 1 | Included in Core |
