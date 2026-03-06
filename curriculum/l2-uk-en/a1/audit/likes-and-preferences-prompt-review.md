# Prompt Engineering Review: likes-and-preferences

**Track:** a1 | **Sequence:** 19
**Pipeline:** v4
**Validate attempts:** 6 (exhausted)
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Summary heading level contradiction | HIGH | phase-2-prompt.md | Output format shows `# Підсумок` (H1) but writing instructions say "each section maps to an H2." Gemini wrote `## Підсумок`. The audit gate flagged `[HEADING_LEVEL] Main section 'Підсумок' uses H2 (##) but spec requires H1 (#)`. This single issue consumed fix attempts 3-6 identically. |
| Fix1 and Fix2 prompts contain NO specific issue | HIGH | validate-fix template | Fix1 and Fix2 prompts say "Fix 1 issue(s)" but list only "Other Audit Failures" with raw `AUDIT FAILED` text and NO specific gate name or violation. Gemini had zero diagnostic information to act on. Two fix attempts were completely wasted. |
| Dative constraint vs module content contradiction | HIGH | placeholders.yaml + phase-A-output.md | LEVEL_CONSTRAINTS says "Dative case FORBIDDEN." But the module teaches "Мені подобається" which is explicitly a Dative construction. Research output acknowledges this but the content prompt does NOT explicitly carve out this exception. |
| Textbook examples irrelevant | LOW | placeholders.yaml | TEXTBOOK_EXAMPLES shows Grade 1 letter exercises -- completely irrelevant for a module about expressing preferences. |
| PERSONA_ROLE ("Food Critic") unexplained | LOW | placeholders.yaml | No guidance on how "Food Critic" persona maps to writing style. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No explicit heading level rule for Summary | Critical -- sole audit failure across 6 fix attempts | Add "Summary = H1 (#)" rule to content prompt |
| Dative exception not stated in content prompt | Medium -- Gemini must infer from research notes that Мені/Тобі are allowed despite the blanket dative ban | Add explicit exception to LEVEL_CONSTRAINTS |
| Fix1-Fix2 contain no specific failure information | Critical -- two fix attempts wasted with zero actionable guidance | Fix prompt generator must extract and include specific gate failures |
| No prior module content injected | Low -- module references prior learning but content prompt provides no text from those modules | Inject a brief "previously taught" summary |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| Summary heading ## vs # -- persisted all 6 fix attempts | template_gap | Output format shows H1 but "each section maps to H2" contradicts. Fix prompts 3-6 stated the fix explicitly but Gemini could not apply it. | Make output format skeleton unambiguous. Add a hard rule in the writing instructions. |
| Fix1-Fix2 empty diagnostics | template_gap | The validate-fix prompt generator did not extract specific gate failures for these early attempts. | Fix the validate-fix template to always include the STRICT GATES table. |
| Dative forms could trigger false audit failures | conflicting_guidance | The blanket "Dative FORBIDDEN" constraint conflicts with the module's core teaching content. | Add module-level constraint overrides to the placeholder system. |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | 6 (exhausted) | `## Підсумок` -> should be `# Підсумок`. Fix1-2 had no diagnostic info (wasted). Fix3-6 stated the fix explicitly but Gemini could not apply it. Escalation also failed. | YES -- content prompt should generate correct heading from the start. Fix1-2 should have contained the specific violation. |

**Key observation:** This module's fix loop is remarkably simple -- a single heading-level change (`##` to `#`) that Gemini failed to make across 6 attempts plus escalation. Root causes: (1) ambiguous content prompt, (2) empty early fix prompts, (3) fix output format using `## {section title}` in delimiters which reinforced the wrong heading level.

## Suggested Template Fixes

### Fix 1: Explicit Summary Heading Level in Output Format (Priority: HIGH)
**Prevents:** The exact issue that consumed all 6 fix attempts on both this module and the-living-verb-i.
**Scope:** Content prompt template, affects all A1 modules.

### Fix 2: Fix Prompt Must Always Include Specific Gate Failures (Priority: HIGH)
**Prevents:** 2 completely wasted fix attempts where Gemini had no diagnostic information.
**Scope:** Validate-fix prompt generator (pipeline code).

### Fix 3: Dative Exception for Preferences Module (Priority: MEDIUM)
**Prevents:** Potential false failures if audit adds dative scanning.
**Scope:** Placeholder injection for modules that teach Dative-as-chunk patterns.

### Fix 4: Fix Output Format Should Not Use ## in Delimiter (Priority: MEDIUM)
**Prevents:** The confusing pattern where the escalation fix format says `## {section title}` inside delimiters.
**Scope:** Escalation fix prompt template.

### Fix 5: Topic-Filtered Textbook Examples (Priority: LOW)
**Prevents:** ~2000 tokens of irrelevant letter-introduction exercises in grammar module prompts.
**Scope:** Pipeline placeholder injection.

## Summary

**Template health:** NEEDS WORK

**Top 3 fixes by leverage:**
1. **Explicit Summary H1 heading rule** -- identical to the-living-verb-i. This single template fix would have prevented the sole audit failure on this module. Cross-module systemic issue.
2. **Fix prompt diagnostic completeness** -- fix1 and fix2 contained ZERO actionable information, wasting 2 of 6 fix attempts.
3. **Fix output delimiter format** -- the escalation prompt's `## {section title}` format likely confused the model into preserving the wrong heading level.
