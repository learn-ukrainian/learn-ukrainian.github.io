# Audit Report: M110 — heo-shkurupii.md
**Level:** C1-BIO | **Module:** M110 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 0/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 00:47:59

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
- **[YAML_SCHEMA_VIOLATION]** Schema error in heo-shkurupii.yaml: Insufficient activities: 0 found, minimum 3 required for C1-BIO
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: biography) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: biography) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.
- **[STATE_STANDARD_LOW_IMMERSION]** Module 110 has 4.3% immersion (target: 90.0%+)
  - FIX: Add more Ukrainian content to reach 90.0%+ immersion

## Recommendation
**🔄 REWRITE** (severity 80/100)

- 4 violations (moderate)
- Immersion 91% off target (major rebalancing needed)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ❌ 9/4000 (raw: 161)
- **Activities:** ❌ 0/3
- **Density:** ❌ 0 < 1
- **Unique_types:** ❌ 0/3 types
- **Priority:** ❌ No priority types
- **Engagement:** ❌ 1/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 3-9)
- **Immersion:** ❌ 4.3% LOW (target 95-100% (biography))
- **Richness:** ❌ 11% < 95% min (biography) - REWRITE needed
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 11% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 0 | 4 | 0% | 19% | 0.0% |
| engagement | 1 | 6 | 17% | 14% | 2.4% |
| quotes | 0 | 3 | 0% | 14% | 0.0% |
| cultural | 0 | 4 | 0% | 10% | 0.0% |
| visual | 0 | 4 | 0% | 10% | 0.0% |
| timeline_markers | 1 | 8 | 12% | 10% | 1.1% |
| legacy | 0 | 2 | 0% | 10% | 0.0% |
| variety | 0.93 | - | 93% | 5% | 4.4% |
| paragraph_var | 0.43 | - | 43% | 5% | 2.0% |
| questions | 1 | 3 | 33% | 5% | 1.6% |
| **TOTAL** | | | | | **11.6%** |

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
- ❌ **NO_LEGACY_DISCUSSION**
  - FIX:
    Address this issue to improve richness score
- ❌ **NO_TIMELINE**
  - FIX:
    Add 5+ timeline markers: specific years (1876, 1918), periods (XVIII ст.), sequences (спочатку... потім... нарешті).

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Тест** | ⚪️ | 0 | Skipped |
| **Пояснення** | ⚪️ | 7 | Skipped |
| **Практика** | ⚪️ | 0 | Skipped |
| **Діалоги** | ✅ | 2 | Included in Core |
| **Підсумок** | ✅ | 0 | Included in Core |