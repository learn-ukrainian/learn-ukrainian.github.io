# Prompt Engineering Review: tomorrow-future-tense

**Track:** a1 | **Sequence:** 37
**Pipeline:** v4
**Validate attempts:** 3
**Friction reports:** 2 (content: NONE, activities: NONE)
**Review phase:** YES (2 fix attempts, final PASS)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Instrumental case constraint not surfaced prominently enough | HIGH | phase-2-prompt.md | Fix3 flagged "мною" (instrumental) -- the LEVEL_CONSTRAINTS say "Instrumental case FORBIDDEN" but Gemini still used it. The constraint is buried in a dense block of text in placeholders.yaml. |
| Validate fix prompts lack specific issue details | MEDIUM | validate-fix1/2-prompt.md | Fix1 and fix2 both say only "Other Audit Failures" with a generic error message, no specific issue listed. The model has no idea what to fix. |
| No guidance on calque avoidance for future tense | HIGH | phase-2-prompt.md | The review found critical calques: "буду мати" (English "will have" calque), "робити багато роботи" (tautological calque). The Russianisms list doesn't cover English calques -- only Russian -> Ukrainian substitutions. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| English calque warning for future tense | Review scored 7/10 Linguistic Accuracy due to "буду мати" calque pattern | Add calque-specific warnings: "NEVER translate 'will have' as 'буду мати' -- use 'у мене буде' or synthetic 'матиму'" |
| Orphaned vocabulary detection | Review found 5 vocab words (сподіватися, мріяти, планувати, пізніше, вихідні) that never appear in text | Add vocab-in-content requirement (same as M21 finding) |
| Natural compound future patterns | Gemini defaulted to literal translations | Add examples of natural "буду + infinitive" patterns vs calques |
| Validate fix prompts missing issue details | Fix1/fix2 had no actionable information | Pipeline should extract and include specific failure reasons |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| "буду мати" calque (review) | context_gap | Russianisms list covers RU->UK but not EN->UK calques | Add English calque warnings per topic (future tense, possession, etc.) |
| "робити роботу" tautology (review) | context_gap | No tautology warnings in prompt | Add common tautology list: "робити роботу -> працювати" |
| Instrumental "мною" (fix3) | template_gap | Constraint buried in dense text | Surface case restrictions more prominently with examples |
| Orphaned vocabulary (review) | context_gap | Same pattern as M21 | Add vocab-in-content requirement |
| Empty validate fix prompts (fix1/fix2) | template_gap | Pipeline sends generic "AUDIT FAILED" without specific issues | Fix pipeline to extract and include deterministic issues |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 3 | fix1: generic audit fail (no specific issue); fix2: generic audit fail (no specific issue); fix3: instrumental "мною" | PARTIALLY -- fix1/fix2 wasted because they had no actionable instructions. fix3 preventable with prominent case restriction. |
| Review | 2 fix attempts | Calques (буду мати), tautology, orphaned vocab | YES -- calque warnings in content prompt would have prevented these. Review was effective and caught real issues. |

**Critical finding:** The validate-fix1 and validate-fix2 prompts for this module contain NO specific issue text -- just "Other Audit Failures" with a generic error link. This is a pipeline bug: the fix prompt generator failed to extract deterministic issues from the audit output, sending Gemini on a blind fix attempt twice. This wastes 2 API calls per module.

**Positive finding:** The review phase (pass 1: factual, pass 2: language) caught genuine quality issues (calques, tautologies, orphaned vocab) that validation alone would miss. This validates the cross-agent review architecture.

## Suggested Template Fixes

### Fix 1: Add English calque warnings for future tense (Priority: HIGH)
**Before:** Only Russian calques listed (кушати -> їсти, etc.)
**After:** Add section:
```
### English Calques (HARD FAIL — sounds unnatural)
| English Pattern | Calque (BAD) | Natural Ukrainian |
|-----------------|-------------|-------------------|
| will have | буду мати | у мене буде / матиму |
| will do work | буду робити роботу | буду працювати |
| will make plans | буду робити плани | буду планувати |
```

### Fix 2: Fix empty validate-fix prompts (Priority: HIGH)
**Before:** "### Other Audit Failures\n```\n AUDIT FAILED (see log)\n```"
**After:** Pipeline must extract ALL deterministic audit failures and list them with specific line numbers and fix instructions. Never send a fix prompt with zero actionable items.

### Fix 3: Add vocab-in-content requirement (Priority: HIGH)
Same as M21 finding. Cross-module pattern.

### Fix 4: Surface case restrictions with examples (Priority: MEDIUM)
**Before:** Dense paragraph of case restrictions in LEVEL_CONSTRAINTS
**After:** Add highlighted table:
```
| Case | Status at A1 | Example of FORBIDDEN usage |
|------|-------------|---------------------------|
| Instrumental | FORBIDDEN | з мно́ю, з дру́гом, -ом/-ою |
| Dative | FORBIDDEN | мені́, тобі́, йому́ |
```

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Add English calque warnings (prevented review FAIL and 2 fix iterations)
2. Fix empty validate-fix prompts (prevented 2 wasted API calls)
3. Add vocab-in-content requirement (cross-module pattern)
