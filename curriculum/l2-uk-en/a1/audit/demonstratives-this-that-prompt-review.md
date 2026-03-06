# Prompt Engineering Review: demonstratives-this-that

**Track:** a1 | **Sequence:** 21
**Pipeline:** v4
**Validate attempts:** 5
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| IPA ban rule catches stage directions | HIGH | phase-2-prompt.md | "[pointing to the counter]" flagged as IPA -- false positive from bracket detection |
| Section heading mismatch (same as M20) | HIGH | phase-2-prompt.md | English-only section titles vs bilingual plan expectation |
| Immersion target conflicting with grammar content | MEDIUM | phase-2-prompt.md | 35-55% target, Gemini produced 25.1% initially |
| Imperative constraint lacks alternatives (same as M20) | MEDIUM | phase-2-prompt.md | Виберіть and Зверніть persisted through multiple fixes |
| Textbook examples irrelevant | LOW | phase-2-prompt.md | Grade 1 letter exercises for M21 demonstratives |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Stage direction format guidance | IPA false positives on fix1 | Add: "Use (parentheses) not [brackets] for stage directions" |
| Vocab-in-content requirement | 12/20 vocab words missing from content | Add explicit requirement to content prompt |
| Locative vs dative distinction in audit | "мові" false positive | Fix audit rule or clarify in prompt |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| PLAN_SECTION_MISSING | template_gap | Same pattern as M20 | Inject exact meta titles |
| IPA false positive | schema_mismatch | Bracket detection too broad | Fix audit or prompt |
| Immersion gap | conflicting_guidance | Grammar module vs immersion target | Provide recipes |
| Imperatives | template_gap | No alternatives | Add table |
| Vocab gap | context_gap | No requirement stated | Add requirement |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 5 | Section mismatch + IPA false positive + immersion + imperatives + vocab gap | YES -- 4 of 5 preventable |

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Inject exact H2 titles from meta (cross-module pattern)
2. Add imperative alternatives table (cross-module pattern)
3. Add vocab-in-content requirement
