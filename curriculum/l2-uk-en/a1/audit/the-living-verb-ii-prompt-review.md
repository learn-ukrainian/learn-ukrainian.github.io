# Prompt Engineering Review: the-living-verb-ii

**Track:** a1 | **Sequence:** 16
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (both NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Section title mismatch between plan and content | HIGH | validate-fix1-prompt.md | Fix prompt reports 4 missing plan sections, but the content has equivalent sections with slightly different titles. "Моделі та мутації" (plan) vs "Моделі та закінчення" (content). This is a fuzzy matching problem, not actually missing content. |
| Content redundancy detector over-sensitive | MEDIUM | validate-fix2-prompt.md | Fix2 flags "88% overlap" for "Now, we are ready to explore the second major family of Ukrainian action words" -- a thematic reintroduction, not true redundancy. The detector treats keyword overlap as semantic overlap. |
| Immersion initially too low (13.3%) | HIGH | validate-fix2-prompt.md | First attempt had 13.3% Ukrainian, well below 25-40% target. Content phase produced heavily English-scaffolded prose with insufficient Ukrainian examples. |
| VESUM false negatives for verb endings | MEDIUM | screen-result.json | 21 VESUM misses including morpheme fragments (-ать, -иш, -ить, -имо, -ите) and incorrect conjugation forms (говориєш, любю, пию, сидю, ходю, платю, роблу, робю, їсю, їджу). The incorrect forms are pedagogical examples of common mistakes, but they fail VESUM verification. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No guidance on presenting incorrect forms as teaching examples | Incorrect forms (говориєш, сидю, ходю) fail VESUM but are intentional pedagogical examples of common mistakes | Add VESUM exception mechanism for explicitly marked incorrect forms in "common mistakes" sections |
| Section title fuzzy matching too strict | 4 sections flagged as "missing" when they exist with minor title variations | Improve section title matching algorithm (normalize before comparison) |
| Low immersion on first pass | Required fix round 2 | Add minimum Ukrainian density check to content phase before validation |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| Section title mismatch | schema_mismatch | Plan and content have equivalent sections with minor title differences | Improve section matching: normalize Unicode, strip parentheticals, fuzzy match |
| Low immersion (13.3%) | template_gap | Content prompt doesn't enforce minimum Ukrainian density during generation | Add immersion self-check: "Verify at least 25% of your content is Ukrainian text" |
| Content redundancy false positive | schema_mismatch | Keyword overlap detector too aggressive for thematic reintroductions | Adjust redundancy threshold or exclude H2 section openers |
| VESUM failures on intentional incorrect forms | template_gap | No mechanism to mark pedagogical incorrect examples | Add `<!-- INTENTIONAL_ERROR: ... -->` markup for teaching common mistakes |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 2 | Fix1: section title mismatch (rewrite headings). Fix2: low immersion + redundancy flag | PARTIALLY -- title matching improvement prevents Fix1; immersion self-check prevents Fix2 |

## Suggested Template Fixes

### Fix 1: Section Title Fuzzy Matching (Priority: HIGH)
Normalize plan section titles and content H2 headings before comparison. Strip parenthetical translations, normalize Unicode. Match on slugified versions.

### Fix 2: Immersion Self-Check in Content Prompt (Priority: HIGH)
Add to pre-submission checks: "Count Ukrainian words vs total words. If Ukrainian is less than 25%, add more Ukrainian example sentences with translations."

### Fix 3: VESUM Exception for Pedagogical Errors (Priority: MEDIUM)
Add mechanism to mark intentionally incorrect forms (common mistakes being taught) so they don't fail VESUM. Use HTML comment markup: `<!-- INCORRECT_FORM: говориєш (teaching common error) -->`.

### Fix 4: Redundancy Detector Calibration (Priority: LOW)
Exclude H2/H3 section openers from redundancy detection, or raise threshold from 88% to 95%.

## Summary

**Template health:** GOOD
**Top 3 fixes by leverage:**
1. Section title fuzzy matching (prevents false "missing section" errors across all modules)
2. Immersion self-check in content prompt (prevents low-immersion fix rounds)
3. VESUM exception for pedagogical error examples (prevents false VESUM failures in error-teaching modules)
