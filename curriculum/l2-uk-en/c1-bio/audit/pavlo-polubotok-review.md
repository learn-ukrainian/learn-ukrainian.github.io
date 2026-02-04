# Audit Report: M29 — pavlo-polubotok.md
**Level:** C1-BIO | **Module:** M29 | **Phase:** C1 | **Pedagogy:** seminar | **Target:** 4000
**Naturalness:** 0/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-04 11:41:31

## Configuration
**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** critical-analysis, essay-response, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## PEDAGOGICAL VIOLATIONS
- **[INVALID_META_YAML]** Meta YAML Schema Violation at 'root': 'activity_hints' is a required property
  - FIX: Correct the YAML structure to match schemas/meta-module.schema.json
- **[HEADING_LEVEL]** Main section 'Підсумок' uses H2 (##) but spec requires H1 (#)
  - FIX: Change '## Підсумок' to '# Підсумок' for top-level TOC compliance
- **[YAML_SCHEMA_VIOLATION]** Schema error in pavlo-polubotok.yaml: Insufficient activities: 0 found, minimum 3 required for C1-BIO
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: biography) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: biography) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 55/100)

- Revision recommended (severity 55/100)
- 7 violations (significant)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ❌ 63/4000 (raw: 94)
- **Activities:** ❌ 0/3
- **Density:** ❌ 0 < 1
- **Unique_types:** ❌ 0/3 types
- **Priority:** ❌ No priority types
- **Engagement:** ❌ 0/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 5 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 3-9)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ❌ 15% < 95% min (biography) - REWRITE needed
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 15% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 0 | 4 | 0% | 19% | 0.0% |
| engagement | 0 | 6 | 0% | 14% | 0.0% |
| quotes | 0 | 3 | 0% | 14% | 0.0% |
| cultural | 1 | 4 | 25% | 10% | 2.4% |
| visual | 0 | 4 | 0% | 10% | 0.0% |
| timeline_markers | 2 | 8 | 25% | 10% | 2.4% |
| legacy | 1 | 2 | 50% | 10% | 4.8% |
| variety | 0.50 | - | 50% | 5% | 2.4% |
| paragraph_var | 0.50 | - | 50% | 5% | 2.4% |
| questions | 1 | 3 | 33% | 5% | 1.6% |
| **TOTAL** | | | | | **15.9%** |

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
- ❌ **NO_QUOTES**
  - FIX:
    Add 2+ direct quotes from the subject. Use this format:
    
    > «[Exact quote from the person]»
    > — *[Person name], [context/year]*
- ❌ **NO_TIMELINE**
  - FIX:
    Add 5+ timeline markers: specific years (1876, 1918), periods (XVIII ст.), sequences (спочатку... потім... нарешті).

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 39 | Included in Core |
| **Вступ** | ✅ | 3 | Included in Core |
| **Життєпис** | ⚪️ | 3 | Skipped |
| **Шлях до влади** | ⚪️ | 3 | Skipped |
| **Протистояння з Малоросійською колегією** | ⚪️ | 3 | Skipped |
| **Ув'язнення та смерть** | ⚪️ | 3 | Skipped |
| **Легенда про скарб** | ⚪️ | 3 | Skipped |
| **Спадщина** | ⚪️ | 3 | Skipped |
| **Підсумок** | ✅ | 3 | Included in Core |