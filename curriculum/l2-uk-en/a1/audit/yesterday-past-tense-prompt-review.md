# Prompt Engineering Review: yesterday-past-tense

**Track:** a1 | **Sequence:** 36
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (content: NONE with self-corrections, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Section heading mismatch (cross-module pattern) | HIGH | phase-2-prompt.md | 4 missing plan sections on fix1 |
| Dative case false positive on word fragments | MEDIUM | validate-fix2-prompt.md | "Чолові" and "телеві" misread as dative |
| Sentence length rule catches tables | MEDIUM | phase-2-prompt.md | 20-word and 11-word "sentences" may be table content |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Section heading format | 4 sections missing on fix1 | Inject exact meta titles |
| Metalanguage allowlist | "множина" flagged | Provide allowlist or require English |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| PLAN_SECTION_MISSING x4 | template_gap | Title format mismatch | Inject exact meta titles |
| Dative/sentence false positives | schema_mismatch | Audit parser issues | Fix audit tokenizer |
| Immersion 32.5% LOW | conflicting_guidance | Grammar module vs immersion target | Immersion recipes |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 2 | Section mismatch + audit false positives | PARTIALLY preventable |

## Summary

**Template health:** NEEDS WORK (but best execution of the batch -- only 2 fix attempts)
**Top 3 fixes by leverage:**
1. Inject exact H2 titles from meta
2. Fix audit false positives
3. Add metalanguage allowlist
