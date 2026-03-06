# Prompt Engineering Review: at-the-restaurant

**Track:** a1 | **Sequence:** 53
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Dative case generated despite ban | HIGH | LEVEL_CONSTRAINTS | "вам" (3x), "мові" (1x) produced despite explicit ban |
| Instrumental case generated | HIGH | LEVEL_CONSTRAINTS | "з офіціантом" uses banned Instrumental |
| Subordinate clauses generated | HIGH | LEVEL_CONSTRAINTS | 4 subordinate clause violations (що, коли, якщо) |
| Sentence length violations | HIGH | LEVEL_CONSTRAINTS | 6 sentences exceeded 10-word limit |
| Russianisms: давайте + perfective | HIGH | SHARED_CONTENT_RULES | "давайте попрактикуємо/подивимося" are unlisted calques |
| Section balance: 51% in one section | MEDIUM | phase-2-prompt.md | No max-per-section constraint |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Russianisms table incomplete | HIGH | Add "давайте + perf" pattern |
| Grammar constraints as wall of text | HIGH | Restructure as numbered rules |
| No section balance cap | MEDIUM | Add 40% max per section |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| 17 pedagogical violations | template_gap + model_limitation | Constraints present but format ineffective | Numbered rules with examples |
| Russianisms | template_gap | Pattern not in table | Expand table |
| Section bloat | template_gap | No balance enforcement | Add cap |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 2 | Fix1: Russianisms + heading mismatch. Fix2: 17 pedagogical violations. | YES with restructured constraints |

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Restructure LEVEL_CONSTRAINTS as numbered rules with examples (HIGH)
2. Expand Russianisms table (HIGH)
3. Add section balance cap (MEDIUM)
