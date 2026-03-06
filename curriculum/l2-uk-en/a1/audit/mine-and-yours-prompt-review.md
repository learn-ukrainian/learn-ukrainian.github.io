# Prompt Engineering Review: mine-and-yours

**Track:** a1 | **Sequence:** 20
**Pipeline:** v4
**Validate attempts:** 5
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Unreplaced placeholder `{H3_WORD_RANGE}` in content prompt | MEDIUM | phase-2-prompt.md | Line 6 reads "Every H3 gets {H3_WORD_RANGE} words" -- placeholder visible to Gemini rather than resolved value (60-80). Gemini must infer from placeholders.yaml. |
| Section headings mismatch between outline and plan | HIGH | phase-2-prompt.md | Word budget table uses outline titles ("Introduction: Whose is this?") but plan/meta uses different Ukrainian/English dual titles ("Вступ: Чия це річ?"). Gemini wrote English-only headings, causing PLAN_SECTION_MISSING on fix1. |
| Immersion rule unclear for M20 band | MEDIUM | phase-2-prompt.md | Immersion target "25-40%" but content prompt also says to "Write cultural notes, practical sections in Ukrainian first" -- tension between low immersion target and strong Ukrainian-first instruction. Gemini produced 8.4% initially. |
| Imperative constraint mentioned but no positive examples | MEDIUM | phase-2-prompt.md | Prompt says "Before M47, use indirect requests or English for instructions" but gives no examples of what TO write instead of imperatives. Gemini used Прочитайте, Порівняйте, Зверніть -- all imperatives caught in fix5. |
| Textbook examples irrelevant to M20 topic | LOW | phase-2-prompt.md | Grade 1 bukvar examples (letter-sound exercises) have zero relevance to possessive pronouns at M20. Wasted ~100 lines of context. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Section heading format expectation (bilingual H2) | Caused PLAN_SECTION_MISSING on fix1 | Add explicit instruction: "H2 headings MUST match meta content_outline titles exactly" |
| No imperative alternatives list | 3 imperatives survived to fix5 | Add imperative -> replacement patterns table |
| Immersion calculation method | Model produced 8.4% initially, iterated 3 times | Explain calculation and give paragraph-level example |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| PLAN_SECTION_MISSING (fix1) | template_gap | Prompt gives English-only titles but plan expects bilingual | Inject exact H2 titles from meta |
| Immersion 8.4% LOW (fix2-4) | conflicting_guidance | "25-40% Ukrainian" vs "Grammar RULES stay in English" for a grammar module | Provide immersion recipes |
| Imperatives (fix5) | template_gap | Constraint stated abstractly, no alternatives | Add INSTEAD OF / USE table |
| Identical fix prompts (fix2-4) | template_gap | Same fix instructions sent 3 times | Pipeline should track fix deltas |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 5 | Heading mismatch + immersion + imperatives | YES -- 4 of 5 attempts preventable with better prompting |

## Suggested Template Fixes

### Fix 1: Inject exact H2 titles from meta (Priority: HIGH)
### Fix 2: Add imperative alternatives table (Priority: HIGH)
### Fix 3: Provide immersion recipe for grammar modules (Priority: HIGH)
### Fix 4: De-duplicate fix prompts with progress tracking (Priority: HIGH)
### Fix 5: Remove irrelevant textbook examples for M7+ (Priority: MEDIUM)

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Inject exact H2 titles from meta to prevent section heading mismatches
2. Add imperative alternatives table
3. Provide immersion recipes with concrete examples
