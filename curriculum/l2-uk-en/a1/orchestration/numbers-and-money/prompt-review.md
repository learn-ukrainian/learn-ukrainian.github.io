# Prompt Engineering Review: numbers-and-money

**Track:** a1 | **Sequence:** 22
**Pipeline:** v4
**Validate attempts:** 0 (pipeline incomplete -- stopped after content phase)
**Friction reports:** 1 (content: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Textbook examples irrelevant (same as M20/M21) | LOW | phase-2-prompt.md | Grade 1 bukvar table of contents and letter exercises injected for M22 numbers module. Zero pedagogical overlap. |
| Unreplaced placeholder `{H3_WORD_RANGE}` (same as M20) | MEDIUM | phase-2-prompt.md | Line 6 still shows raw placeholder text |
| No section word budget table visible | MEDIUM | phase-2-prompt.md | The phase-2-prompt.md was only read to line 50; the full prompt likely has budgets but they may suffer the same English-only title mismatch as M20/M21 |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Pipeline incomplete -- no activities or validation | Cannot assess fix loop patterns | Module needs completion |
| No phase-C output files | Activities phase started but no output captured | Check if pipeline crashed or timed out |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| Content friction: NONE | n/a | Gemini reported no friction during content generation | n/a |
| Pipeline halt after content | unknown | State shows v4-content complete but no v4-activities or v4-validate | Investigate pipeline failure |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 0 | Pipeline did not reach validation | N/A |

## Suggested Template Fixes

### Fix 1: Same cross-module fixes as M20/M21 (Priority: HIGH)
The same template is used across all A1 modules, so all issues identified in M20 and M21 apply here:
- Inject exact H2 titles from meta
- Add imperative alternatives table
- Remove irrelevant textbook examples for M7+
- Add immersion recipe

### Fix 2: Investigate pipeline halt (Priority: HIGH)
The phase-C-prompt.md exists but no phase-C output files were generated. The state-v4.json shows only research, discover, and content complete. The activities phase may have failed silently.

## Summary

**Template health:** NEEDS WORK (same template issues as M20/M21, plus pipeline incomplete)
**Top 3 fixes by leverage:**
1. Complete the pipeline run for this module
2. Apply cross-module template fixes (H2 titles, imperatives, immersion recipes)
3. Remove irrelevant textbook examples
