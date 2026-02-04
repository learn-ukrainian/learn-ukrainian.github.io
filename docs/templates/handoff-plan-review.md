# Handoff: Plan Review Template

Use this template for reviewing immutable YAML plans in `plans/` before content generation starts.
This is a high-leverage point - catching issues here prevents costly rework later.

## Usage

```bash
gh issue create \
  --title "review(plans): Level/module plan review - scope" \
  --body-file /tmp/issue-body.md \
  --label "enhancement" \
  --label "curriculum" \
  --label "agent:claude"
```

---

## Template

```markdown
## Overview

**Scope**: [Single plan / Level plans / Track plans]
**Plans to Review**: [Number]
**Review Type**: [Pre-generation / Post-audit / Scheduled]
**Assigned to**: [Claude / Gemini]

## Plans Under Review

| Plan File | Module | Status |
|-----------|--------|--------|
| `plans/{level}/{slug}.yaml` | {num}-{slug} | Pending |
| ... | ... | ... |

## Review Checklist

### Structure Validation
- [ ] All required sections present (title, objectives, outline, vocabulary)
- [ ] `content_outline` has appropriate depth for level
- [ ] Word targets realistic for content scope
- [ ] Subsections map to pedagogical goals

### Vocabulary Validation
- [ ] Vocabulary count appropriate for level
- [ ] No duplicates with previous modules
- [ ] Terms match module theme
- [ ] Lemmas correctly formatted

### Pedagogical Alignment
- [ ] Objectives are measurable (SMART criteria)
- [ ] Progression from simple → complex
- [ ] Skills balance (reading/writing/listening/speaking)
- [ ] Cultural context appropriate for level

### Track-Specific (if applicable)
- [ ] **HIST**: Era-appropriate vocabulary, decolonization perspective
- [ ] **BIO**: Biographical accuracy, legacy framing
- [ ] **LIT**: Literary devices, authentic texts referenced

## Tasks

- [ ] Read each plan file
- [ ] Validate against checklist
- [ ] Document issues found
- [ ] Propose fixes (don't modify plans directly - they're source of truth)
- [ ] Get approval before any plan changes

## Issues Found

| Plan | Section | Issue | Severity | Proposed Fix |
|------|---------|-------|----------|--------------|
| `{slug}.yaml` | vocabulary | Missing key term | High | Add "X" to list |
| ... | ... | ... | ... | ... |

## Definition of Done

- [ ] All plans reviewed against checklist
- [ ] Issues documented with proposed fixes
- [ ] High-severity issues escalated for user decision
- [ ] Ready for content generation

## Related Files

| File | Purpose |
|------|---------|
| `curriculum/l2-uk-en/plans/{level}/` | Plans directory |
| `claude_extensions/quick-ref/{LEVEL}.md` | Level requirements |
| `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` | Richness targets |

## Context

### Review Trigger
[Why reviewing now? New level? Quality issue found? Pre-release?]

### Previous Plan Issues
[Any patterns from past reviews to watch for?]

### Approval Required For
- Any vocabulary additions/removals
- Word target changes
- Outline structure changes
- Objective modifications
```

---

## Important Notes

**Plans are Source of Truth**
- Never modify plans without explicit user approval
- Document proposed changes, don't implement them
- Changes cascade to meta, content, activities

**High-Leverage Review**
- 1 hour here saves 10 hours fixing content later
- Focus on vocabulary and outline - hardest to fix post-generation
