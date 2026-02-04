# Handoff: Module Correction Template

Use this template when creating issues to fix audit failures or module quality issues.

## Usage

```bash
gh issue create \
  --title "fix(level): Module slug - failing gates" \
  --body-file /tmp/issue-body.md \
  --label "bug" \
  --label "curriculum" \
  --label "agent:gemini"
```

---

## Template

```markdown
## Overview

**Module**: `curriculum/l2-uk-en/{level}/{num}-{slug}.md`
**Level**: [A1/A2/B1/B2/C1/C2/B2-HIST/C1-BIO/etc.]
**Assigned to**: [Claude / Gemini]

## Failing Gates

| Gate | Status | Details |
|------|--------|---------|
| Word Count | :x: FAIL | 2,340 / 3,000 required |
| Outline Compliance | :x: FAIL | Missing: "Practice Exercises" section |
| Activity Count | :white_check_mark: PASS | 45 items |
| Vocabulary | :white_check_mark: PASS | 28 lemmas |

## Tasks

- [ ] Read plan file: `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`
- [ ] Read audit log: `curriculum/l2-uk-en/{level}/audit/{slug}-audit.log`
- [ ] Fix: [specific issue 1]
- [ ] Fix: [specific issue 2]
- [ ] Re-run audit: `scripts/audit_module.sh {path}`
- [ ] Verify all gates pass

## Definition of Done

- [ ] All audit gates show :white_check_mark: PASS
- [ ] Word count meets target (95%+ minimum)
- [ ] All plan outline sections present
- [ ] Status JSON updated with passing status
- [ ] Issue commented with audit output

## Related Files

| File | Purpose |
|------|---------|
| `curriculum/l2-uk-en/{level}/{num}-{slug}.md` | Module content |
| `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` | Source of truth |
| `curriculum/l2-uk-en/{level}/meta/{slug}.yaml` | Build config |
| `curriculum/l2-uk-en/{level}/audit/{slug}-audit.log` | Error details |
| `curriculum/l2-uk-en/{level}/status/{slug}.json` | Cached status |

## Audit Output

```
[Paste full audit output here]
```

## Manual Quality Observations

[Non-automated issues found by reviewer that don't trigger gate failures]

| Location | Observation | Severity |
|----------|-------------|----------|
| H2.3 | Transition between topics feels abrupt | Minor |
| Activity 5 | Instructions unclear | Medium |

## Context

### Root Cause
[Why did this module fail? Missing content? Structural issue?]

### Fix Approach
[How should this be fixed? Expand existing sections? Add new content?]

### Constraints
- Use ONLY vocabulary from plan file
- Follow outline structure exactly
- Maintain existing quality in passing sections
```

---

## Quick Commands

```bash
# Run audit
scripts/audit_module.sh curriculum/l2-uk-en/{level}/{num}-{slug}.md

# View plan
cat curriculum/l2-uk-en/plans/{level}/{slug}.yaml

# Check status
cat curriculum/l2-uk-en/{level}/status/{slug}.json | jq .
```
