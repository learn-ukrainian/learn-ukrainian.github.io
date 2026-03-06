# Prompt Engineering Review: leisure-and-hobbies

**Track:** a1 | **Sequence:** 51
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (content: Constraint Enforcement, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Dative ban not explicit enough | HIGH | placeholders.yaml (LEVEL_CONSTRAINTS) | Model generated "Мені" 3 times despite ban. Word list not exhaustive. |
| Sentence length limit poorly enforced | HIGH | placeholders.yaml (LEVEL_CONSTRAINTS) | 8 sentences exceeded 10-word limit (11-14 words). Needs counting examples. |
| Subordinate clause ban incomplete | MEDIUM | placeholders.yaml (LEVEL_CONSTRAINTS) | Model used "А що т..." workaround. |
| PLAN_SECTION_MISSING false positive | MEDIUM | validate-fix1-prompt.md | 5 sections flagged as missing that clearly exist. Tooling bug. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No exhaustive dative form examples | HIGH | Expand ban with noun examples beyond pronouns |
| No sentence-counting worked example | MEDIUM | Add before/after split example |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| validate-fix2: 19 pedagogy violations | template_gap + model_limitation | Dative, sentence length, subordinate clauses | Expand constraint examples |
| validate-fix1: section mismatch | schema_mismatch | False positive from heading matcher | Fix audit tooling |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 2 | Fix1: false positive. Fix2: 19 pedagogical violations (dative, length, subordinate). | YES with stronger constraints |

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Expand dative ban with exhaustive examples (HIGH)
2. Add sentence-counting enforcement with worked examples (HIGH)
3. Fix section-heading matching algorithm (MEDIUM)
