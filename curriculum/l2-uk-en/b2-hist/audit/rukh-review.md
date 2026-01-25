# Audit Report: M120 — rukh.md
**Level:** B2 | **Module:** M120 | **Phase:** HIST.12 | **Pedagogy:** Not Specified | **Target:** 4000
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 20:24:53

## Configuration
**Type:** B2-history
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥2 types required
**Priority Types:** comparative-study, critical-analysis, essay-response, reading
**Required Types:** essay-response, reading
**Engagement:** ≥5 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥20 words
**Transliteration:** Not allowed

## PEDAGOGICAL VIOLATIONS
- **[HEADING_LEVEL]** Main section 'Підсумок' uses H2 (##) but spec requires H1 (#)
  - FIX: Change '## Підсумок' to '# Підсумок' for top-level TOC compliance
- **[YAML_SCHEMA_VIOLATION]** Schema error in rukh.yaml: Insufficient activities: 1 found, minimum 5 required for B2-HIST
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.
- **[STATE_STANDARD_LOW_IMMERSION]** Module 120 has 20.5% immersion (target: 90.0%+)
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
- **Words:** ❌ 27/4000 (raw: 103)
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
- **Immersion:** ❌ 20.5% LOW (target 90-100% (history))
- **Richness:** ❌ 7% < 95% min (grammar) - REWRITE needed
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 7% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 0 | 24 | 0% | 20% | 0.0% |
| engagement | 0 | 5 | 0% | 15% | 0.0% |
| dialogues | 0 | 4 | 0% | 15% | 0.0% |
| variety | 0.50 | - | 50% | 10% | 5.0% |
| cultural | 0 | 3 | 0% | 10% | 0.0% |
| realworld | 0 | 3 | 0% | 10% | 0.0% |
| visual | 0 | 3 | 0% | 5% | 0.0% |
| paragraph_var | 0.50 | - | 50% | 5% | 2.5% |
| questions | 0 | 5 | 0% | 5% | 0.0% |
| proverbs | 0 | 1 | 0% | 5% | 0.0% |
| **TOTAL** | | | | | **7.5%** |

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
- ❌ **NO_DIALOGUE**
  - FIX:
    Add 4+ mini-dialogues. Use this exact format:
    
    **Діалог: [Location in Ukraine]**
    
    > — [Speaker 1 line with **bolded** grammar examples]
    > — [Speaker 2 response with **bolded** grammar examples]
    > — [Speaker 1 continuation]
    > — [Speaker 2 conclusion]
    
    Example locations: На Бесарабському ринку, У львівській кав'ярні, В одеському трамваї, На Подолі
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
- ❌ **NO_PROVERBS**
  - FIX:
    Add 1+ Ukrainian proverb. Use this format:
    
    Українці кажу|ть: «[Proverb in Ukrainian]»
    
    Зверніть увагу: **[word]** — [aspect] вид, бо [explanation why this aspect is used].
    
    Example: «Не кажи гоп, поки не перескочиш» — **перескочиш** is perfective because it's about the result.
- ❌ **NO_CULTURAL_ANCHOR**
  - FIX:
    Add 3+ cultural references. Use this exact format:
    
    > 🇺🇦 **Культурний момент**
    >
    > [Reference to Ukrainian place (Київ, Львів, Одеса, Карпати), tradition, or custom]
    > [How it connects to the grammar/vocabulary being taught]
    > [Example sentence using the grammar with cultural context]

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 15 | Included in Core |
| **Рух: Народний рух України** | ⚪️ | 0 | Skipped |
| **Вступ** | ✅ | 2 | Included in Core |
| **Основний зміст** | ⚪️ | 2 | Skipped |
| **Історичне значення** | ⚪️ | 1 | Skipped |
| **Ключові постаті** | ⚪️ | 2 | Skipped |
| **Первинні джерела** | ✅ | 4 | Included in Core |
| **Підсумок** | ✅ | 1 | Included in Core |