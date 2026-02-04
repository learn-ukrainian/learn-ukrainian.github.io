# Handoff Issue Template (Generic)

Use this template when creating GitHub issues for agent-to-agent handoffs.

## Usage

```bash
# Copy template, fill in, save to /tmp/issue-body.md, then:
gh issue create \
  --title "type(scope): Brief description" \
  --body-file /tmp/issue-body.md \
  --label "enhancement" \
  --label "agent:gemini"  # or agent:claude
```

---

## Template

```markdown
## Overview

**What**: [One sentence describing the task]
**Why**: [Business/technical reason for this work]
**Assigned to**: [Claude / Gemini / Either]

## Tasks

- [ ] Task 1: Description
- [ ] Task 2: Description
- [ ] Task 3: Description

## Definition of Done

- [ ] All tasks checked off
- [ ] Tests pass (if applicable)
- [ ] Documentation updated (if applicable)
- [ ] Issue commented with summary of changes
- [ ] Ready for review / closed

## Related Files

| File | Purpose |
|------|---------|
| `path/to/file.py` | Main file to modify |
| `path/to/status.json` | Current status |
| `path/to/audit.log` | Error details |

## Context

### Background
[Why is this work needed? What led to this?]

### Decisions Made
- Decision 1: [rationale]
- Decision 2: [rationale]

### Constraints
- [Any limitations or requirements]

### References
- Related issue: #XXX
- Documentation: `docs/FILE.md`
- Plan: `.claude/plans/xxx.md`
```

---

## Labels Reference

| Label | When to Use |
|-------|-------------|
| `agent:claude` | Claude is primary assignee |
| `agent:gemini` | Gemini is primary assignee |
| `status:in-progress` | Work actively happening |
| `status:blocked` | Waiting on something |
| `status:ready-for-review` | Work complete, needs review |
| `enhancement` | New feature or improvement |
| `bug` | Something broken |
| `infrastructure` | Tooling, scripts, CI/CD |
| `curriculum` | Module content work |

---

## Best Practices

1. **Be specific** - Vague tasks lead to wrong implementations
2. **Link files** - Always include paths to relevant files
3. **Define done** - Make completion criteria unambiguous
4. **Update progress** - Comment on the issue as work progresses
5. **Close promptly** - Don't leave issues open unnecessarily
6. **Check freshness** - Verify file state if issue is >48h old
