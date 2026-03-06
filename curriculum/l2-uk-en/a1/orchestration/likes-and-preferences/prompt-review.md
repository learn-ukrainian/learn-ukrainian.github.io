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
| Dative constraint vs module content contradiction | HIGH | placeholders.yaml + phase-A-output.md | LEVEL_CONSTRAINTS says "Dative case FORBIDDEN." But the module teaches "Мені подобається" which is explicitly a Dative construction. Research output acknowledges this ("Мені and Тобі are introduced as lexical chunks to bypass the A1 Dative restriction"). The content prompt does NOT explicitly carve out this exception, creating a tension the model must resolve silently. |
| Textbook examples irrelevant | LOW | placeholders.yaml | TEXTBOOK_EXAMPLES shows Grade 1 letter exercises (Й, В) — completely irrelevant for a module about expressing preferences. Wasted prompt tokens. |
| PERSONA_ROLE ("Food Critic") unexplained | LOW | placeholders.yaml | No guidance on how "Food Critic" persona maps to writing style for a preferences module. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No explicit heading level rule for Summary | Critical — sole audit failure across 6 fix attempts | Add "Summary = H1 (#)" rule to content prompt |
| Dative exception not stated in content prompt | Medium — Gemini must infer from research notes that Мені/Тобі are allowed despite the blanket dative ban | Add explicit exception: "Мені and Тобі are allowed as lexical chunks. Do not explain the Dative paradigm." |
| Fix1-Fix2 contain no specific failure information | Critical — two fix attempts wasted with zero actionable guidance | Fix prompt generator must extract and include specific gate failures, not just raw error text |
| No prior module content injected | Low — module references prior learning (M15 verbs, M18 questions) but the content prompt provides no text from those modules | Inject a brief "previously taught" summary for grammar modules that build on prior modules |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| Summary heading ## vs # — persisted all 6 fix attempts | template_gap | Output format shows H1 but "each section maps to H2" contradicts. Fix prompts 3-6 stated the fix explicitly but Gemini could not apply it (likely because the escalation prompt includes the full content which still has ##). | Make output format skeleton unambiguous. Add a hard rule in the writing instructions. |
| Fix1-Fix2 empty diagnostics | template_gap | The validate-fix prompt generator did not extract specific gate failures for these early attempts. Only "AUDIT FAILED" raw text was included. | Fix the validate-fix template to always include the STRICT GATES table and specific violation details. |
| Dative forms could trigger false audit failures | conflicting_guidance | The blanket "Dative FORBIDDEN" constraint conflicts with the module's core teaching content (Мені подобається). If the audit ever adds dative scanning, this module would auto-fail. | Add module-level constraint overrides to the placeholder system. |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | 6 (exhausted) | `## Підсумок` -> should be `# Підсумок`. Fix1-2 had no diagnostic info (wasted). Fix3-6 stated the fix explicitly but Gemini could not apply it. Escalation prompt also failed. | YES — content prompt should generate correct heading from the start. Additionally, fix1-2 should have contained the specific violation. |

**Key observation:** This module's fix loop is remarkably simple — a single heading-level change (`##` to `#`) that Gemini failed to make across 6 attempts plus escalation. The root causes are:
1. The content prompt generated the wrong heading level due to ambiguous instructions.
2. Fix1-2 gave Gemini no information about what was wrong.
3. Fix3-6 and escalation gave clear instructions, but the model still failed — possibly because the fix output format asks for `## {section title}` in the delimiter block, which may have confused the model into keeping `##`.

## Suggested Template Fixes

### Fix 1: Explicit Summary Heading Level in Output Format (Priority: HIGH)
**Prevents:** The exact issue that consumed all 6 fix attempts on both this module and the-living-verb-i.
**Scope:** Content prompt template, affects all A1 modules.
**Template file:** Content prompt output format section.

**Before:**
```
## {Section 1}
...
# Підсумок
```

**After:**
```
## {Section 1}
...

<!-- AUDIT REQUIREMENT: Summary section MUST use H1 (#), not H2 (##). -->
# Підсумок
```

Plus in writing instructions: "**Heading rule:** Content sections = `## H2`. Summary/Підсумок = `# H1`. Audit auto-fails on `## Summary` or `## Підсумок`."

### Fix 2: Fix Prompt Must Always Include Specific Gate Failures (Priority: HIGH)
**Prevents:** 2 completely wasted fix attempts (fix1, fix2) where Gemini had no diagnostic information.
**Scope:** Validate-fix prompt generator (pipeline code).
**Template file:** Pipeline validate-fix logic.

The fix prompt generator must:
1. Always include the STRICT GATES table from the audit output.
2. Always include specific `PEDAGOGICAL VIOLATIONS FOUND` details.
3. Never emit a fix prompt with only raw "AUDIT FAILED" text.

### Fix 3: Dative Exception for Preferences Module (Priority: MEDIUM)
**Prevents:** Potential false failures if audit adds dative scanning.
**Scope:** Placeholder injection for modules that teach Dative-as-chunk patterns.
**Template file:** Placeholder generation / LEVEL_CONSTRAINTS.

Add to LEVEL_CONSTRAINTS when module teaches подобатися:
```
Exception: Мені, тобі, йому, їй are allowed as LEXICAL CHUNKS in modules
that teach "подобатися". Do NOT explain the full Dative paradigm.
```

### Fix 4: Fix Output Format Should Not Use ## in Delimiter (Priority: MEDIUM)
**Prevents:** The confusing pattern where the escalation fix format says `## {section title}` inside delimiters, possibly causing the model to keep the `##` heading level.
**Scope:** Escalation fix prompt template.
**Template file:** validate-escalation-prompt template.

**Before:**
```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

**After:**
```
===SECTION_FIX_START===
{exact heading with correct # level}
{fixed section content}
===SECTION_FIX_END===
```

### Fix 5: Topic-Filtered Textbook Examples (Priority: LOW)
**Prevents:** ~2000 tokens of irrelevant letter-introduction exercises in grammar module prompts.
**Scope:** Pipeline placeholder injection.
**Template file:** Placeholder generation code.

Same as the-living-verb-i review: filter TEXTBOOK_EXAMPLES by module type.

## Summary

**Template health:** NEEDS WORK

**Top 3 fixes by leverage:**
1. **Explicit Summary H1 heading rule** — identical to the-living-verb-i. This single template fix would have prevented the sole audit failure on this module. Cross-module systemic issue affecting at minimum 2 modules (likely all A1 builds).
2. **Fix prompt diagnostic completeness** — fix1 and fix2 contained ZERO actionable information, wasting 2 of 6 fix attempts. The pipeline's fix-prompt generator must always extract and present specific gate failures.
3. **Fix output delimiter format** — the escalation prompt's `## {section title}` format likely confused the model into preserving the wrong heading level.
