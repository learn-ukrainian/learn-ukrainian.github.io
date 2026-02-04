# Handoff: Batch Quality Review Template

Use this template when creating issues for large-scale audits or quality reviews across a track or level.

## Usage

```bash
gh issue create \
  --title "review(level): Batch quality review - scope description" \
  --body-file /tmp/issue-body.md \
  --label "enhancement" \
  --label "curriculum" \
  --label "agent:gemini"
```

---

## Template

```markdown
## Overview

**Scope**: [Level / Track / Module range]
**Total Modules**: [Number]
**Review Type**: [Full audit / Sampling / Targeted]
**Assigned to**: [Claude / Gemini / Both]

## Sampling Strategy

### Coverage
| Tier | Modules | Method |
|------|---------|--------|
| Tier 1 | All (100%) | Automated audit scripts |
| Tier 2 | Risk-based | LLM spot-check on flagged modules |
| Tier 3 | ~20% | Stratified sample across phases |

### Selection Criteria for Sampling
- [ ] First/last module of each phase (era-defining)
- [ ] Modules with naturalness < 9.0
- [ ] Modules with sensitive topics
- [ ] Random stratified sample (3 per phase)

### Modules to Review

| # | Module | Phase | Priority | Reason |
|---|--------|-------|----------|--------|
| 1 | `trypillian-civilization` | 1 | High | Era-defining (first) |
| 2 | `syntez-kyivska-rus` | 1 | High | Era-defining (synthesis) |
| 3 | `holodomor` | 5 | High | Sensitive topic |
| ... | ... | ... | ... | ... |

## Tasks

- [ ] Run automated audit on all modules: `npm run status:{level}`
- [ ] Identify modules failing automated gates
- [ ] Deep review era-defining modules (14 total)
- [ ] Spot-check flagged modules (naturalness < 9.0)
- [ ] Review stratified sample
- [ ] Document findings in issue comments
- [ ] Create fix issues for modules needing correction

## Review Dimensions

For each reviewed module, assess:

| Dimension | Weight | Check |
|-----------|--------|-------|
| Narrative flow | 15% | Natural reading experience |
| Decolonization tone | 15% | Ukrainian agency, no Russocentric framing |
| Pedagogical scaffolding | 20% | Activities match objectives |
| Cultural authenticity | 15% | Accurate representation |
| Language quality | 20% | Natural Ukrainian, no calques |
| Technical accuracy | 15% | Facts, dates, names correct |

## Definition of Done

- [ ] All automated audits run
- [ ] Era-defining modules deep-reviewed (14)
- [ ] Stratified sample reviewed (~20 modules)
- [ ] Risk-flagged modules spot-checked
- [ ] Summary report posted as comment
- [ ] Fix issues created for failing modules
- [ ] Track score updated

## Reporting Format

### Per-Module Review Comment
```markdown
### Module: `{slug}`

**Review Type**: [Era-defining / Sample / Risk-flagged]
**Reviewer**: [Claude / Gemini]
**Date**: YYYY-MM-DD

| Dimension | Score | Notes |
|-----------|-------|-------|
| Narrative flow | 8/10 | Good pacing, minor transition issue at H2.3 |
| Decolonization | 9/10 | Strong agency markers |
| Pedagogy | 7/10 | Activity 3 doesn't align with objective 2 |
| ... | ... | ... |

**Overall**: 8.2/10
**Issues Found**: 2
**Recommendation**: [Pass / Minor fixes / Major revision]
```

### Summary Report
```markdown
## Batch Review Summary

**Scope**: B2-HIST | **Modules Reviewed**: 35/140
**Date**: YYYY-MM-DD

### Results by Tier
| Tier | Reviewed | Pass | Minor Fix | Major Fix |
|------|----------|------|-----------|-----------|
| Era-defining | 14 | 12 | 2 | 0 |
| Risk-flagged | 8 | 5 | 2 | 1 |
| Sample | 13 | 11 | 2 | 0 |

### Common Issues
1. [Issue pattern 1] - found in X modules
2. [Issue pattern 2] - found in Y modules

### Fix Issues Created
- #XXX: Module A - [brief description]
- #YYY: Module B - [brief description]

### Track Score Impact
- Before: 9.35/10
- Projected after fixes: 9.6/10
```

## Related Files

| File | Purpose |
|------|---------|
| `docs/{LEVEL}-STATUS.md` | Current level status |
| `scripts/score_track.py` | Track scoring |
| `scripts/scoring/sampling.py` | Sample selection (if exists) |

## Context

### Review Trigger
[Why is this review happening? Scheduled? Issue found? Pre-release?]

### Previous Reviews
- [Date]: [Summary of findings]

### Priority Focus
[Any specific areas of concern to prioritize?]
```

---

## Quick Commands

```bash
# Run full audit
npm run status:{level}

# Score track
npm run score:{track}

# View specific module status
cat curriculum/l2-uk-en/{level}/status/{slug}.json | jq .

# List modules by phase
ls curriculum/l2-uk-en/{level}/*.md | head -20
```
