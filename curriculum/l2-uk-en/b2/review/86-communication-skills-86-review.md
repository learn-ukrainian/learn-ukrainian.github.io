# Audit Report: M86 — 86-communication-skills-86.md

**Level:** B2 | **Module:** M86 | **Phase:** B2.4 | **Pedagogy:** CBI | **Target:** 4000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS

- **[COMPLEXITY]** quiz 'Placeholder' has 0 items (minimum: 8)
  - FIX: Add more items. B2 quiz requires at least 8 items.
- **[HEADING_LEVEL]** Main section 'Підсумок' uses H2 (##) but spec requires H1 (#)
  - FIX: Change '## Підсумок' to '# Підсумок' for top-level TOC compliance
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-communication-skills-86.yaml: Insufficient activities: 1 found, minimum 10 required for B2
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.
- **[STATE_STANDARD_LOW_IMMERSION]** Module 86 has 0.0% immersion (target: 90.0%+)
  - FIX: Add more Ukrainian content to reach 90.0%+ immersion

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення' per template 'b2-module-template.md'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b2-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Потрібно більше практики?' per template 'b2-module-template.md'
  - FIX: Add '## Потрібно більше практики?' section as specified in docs/l2-uk-en/templates/b2-module-template.md.md

## Recommendation

**🔄 REWRITE** (severity 95/100)

- 8 violations (significant)
- Immersion 90% off target (major rebalancing needed)
- Activity count below minimum
- Activity density below minimum

## Gates

- **Words:** ❌ 3/4000
- **Activities:** ❌ 1/3
- **Density:** ❌ 1 < 1
- **Unique_types:** ❌ 1/2 types
- **Priority:** ❌ No priority types
- **Engagement:** ❌ 0/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 5 violations
- **Content_heavy:** ⚠️ Too few activities: 1 (target 3-10)
- **Immersion:** ❌ 0.0% LOW (target 90-100% (history))
- **Richness:** ❌ 9% < 95% min (content) - REWRITE needed
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 9% (minimum: 95%)
**Module Type:** content

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 0 | 15 | 0% | 25% | 0.0% |
| engagement | 0 | 5 | 0% | 19% | 0.0% |
| variety | 0.50 | - | 50% | 12% | 6.2% |
| cultural | 0 | 4 | 0% | 12% | 0.0% |
| realworld | 0 | 3 | 0% | 12% | 0.0% |
| visual | 0 | 4 | 0% | 6% | 0.0% |
| paragraph_var | 0.50 | - | 50% | 6% | 3.1% |
| questions | 0 | 4 | 0% | 6% | 0.0% |
| **TOTAL** | | | | | **9.4%** |

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
- ❌ **NO_EXAMPLES**
  - FIX:
    Add 24+ example sentences. Each grammar point needs 3-4 examples showing the pattern in context.
- ❌ **ABSTRACT_ONLY**
  - FIX:
    Add 3+ real-world boxes. Use this exact format:

    > 🌍 **У реальному житті**
    >
    > [Specific scenario: "На співбесіді...", "У магазині...", "На вокзалі..."]
    > [Example sentence showing grammar in that context]
- ❌ **NO_CULTURAL_ANCHOR**
  - FIX:
    Add 3+ cultural references. Use this exact format:

    > 🇺🇦 **Культурний момент**
    >
    > [Reference to Ukrainian place (Київ, Львів, Одеса, Карпати), tradition, or custom]
    > [How it connects to the grammar/vocabulary being taught]
    > [Example sentence using the grammar with cultural context]

## Low Density Activities

| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Placeholder | quiz | 0 | 8 | Add 8 more items |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Вступ** | ⚪️ | 1 | Skipped |
| **Основний зміст** | ⚪️ | 1 | Skipped |
| **Підсумок** | ✅ | 1 | Included in Core |
