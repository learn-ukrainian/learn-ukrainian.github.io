# Prompt Engineering Review: must-and-want

**Track:** a1 | **Sequence:** M46
**Pipeline:** v4 (INCOMPLETE -- crashed at research phase)
**Validate attempts:** 0
**Friction reports:** 0

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| N/A -- only research prompt was generated | N/A | phase-A-prompt.md | Standard research prompt template, identical to other modules. No issues detectable in the prompt itself. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Only 4 files exist: completion.md, phase-A-output.md, phase-A-prompt.md, placeholders.yaml | CRITICAL | Pipeline crashed during research. No content, activities, or validation ever ran. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| Gemini CLI "Premature close" error | model_limitation | phase-A-output.md shows: "Gemini CLI error (exit 1): Error when talking to Gemini API... Error: Premature close". This is an infrastructure failure, not a prompt issue. | Not a prompt fix -- gemini-cli retry logic needed |
| completion.md says FAIL with 3129 words (target 1200) | context_gap | The completion.md reports word count of 3129 -- this likely comes from a previous build attempt or stale file, since research phase failed and no content was generated in this run. | Clean up stale state before pipeline restart |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Research | 0 (crashed) | Gemini API connection failure | Not a prompt issue |

## Suggested Template Fixes

### Fix 1: Add pipeline retry for transient API errors (Priority: HIGH)
**Before:** Single attempt, crash on "Premature close"
**After:** Retry gemini-cli up to 3 times on connection errors (exit code 1 with "Premature close" or "DEADLINE_EXCEEDED")
**Applies to:** All pipeline phases using gemini-cli

## Summary

**Template health:** GOOD (prompt itself is fine; failure was infrastructure)
**Top 3 fixes by leverage:**
1. Add gemini-cli retry logic for transient errors -- prevents total pipeline failures
2. Clean stale completion.md/state files before pipeline restart
3. N/A -- insufficient data for further analysis
