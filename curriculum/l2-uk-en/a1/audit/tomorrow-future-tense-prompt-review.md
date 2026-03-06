# Prompt Engineering Review: tomorrow-future-tense

**Track:** a1 | **Sequence:** 37
**Pipeline:** v4
**Validate attempts:** 3
**Friction reports:** 2 (content: NONE, activities: NONE)
**Review phase:** YES (2 fix attempts, final PASS)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Instrumental case constraint not prominent enough | HIGH | phase-2-prompt.md | "мною" instrumental slipped through |
| Validate fix prompts empty | MEDIUM | validate-fix1/2-prompt.md | No specific issues listed -- just "AUDIT FAILED" |
| No English calque warnings | HIGH | phase-2-prompt.md | "буду мати" and "робити роботу" calques caught only at review |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| English calque warnings for future tense | Review scored 7/10 Linguistic Accuracy | Add calque table to prompt |
| Orphaned vocabulary detection | 5 unused vocab words | Add vocab-in-content requirement |
| Natural compound future patterns | Gemini defaulted to literal translations | Add natural pattern examples |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| "буду мати" calque | context_gap | Only RU calques listed, not EN calques | Add English calque warnings |
| Empty validate prompts | template_gap | Pipeline failed to extract issues | Fix pipeline issue extraction |
| Instrumental "мною" | template_gap | Case constraints buried | Surface case restrictions prominently |
| Orphaned vocabulary | context_gap | No vocab-in-content requirement | Add requirement |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 3 | 2 empty fix prompts + instrumental case | YES -- 2 wasted calls |
| Review | 2 fixes | Calques + orphaned vocab | YES -- prompt could prevent |

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Add English calque warnings
2. Fix empty validate-fix prompts
3. Add vocab-in-content requirement
