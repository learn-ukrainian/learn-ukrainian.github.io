# Issue Tracking Best Practices

> **Scope:** How to use GitHub issues as persistent cross-session memory and coordination.

---

## Core Principle

**If it's not in a GitHub issue, it didn't happen.**

GH issues are the external memory of this project. Every significant decision, bug, change, and cross-agent handoff must have an issue trail. This is especially critical because Claude and Gemini sessions expire — issues don't.

---

## Label Taxonomy

| Prefix | Labels | Purpose |
|--------|--------|---------|
| `priority:` | `blocking`, `high` | Urgency (no label = normal) |
| `area:` | `infra`, `tooling`, `content`, `docs` | What kind of work |
| `working:` | `claude`, `gemini` | Who's actively working |
| `review:` | `gemini`, `human` | Ready for review |
| `agent:` | `claude`, `gemini` | Preferred assignee |

**Never create labels outside this taxonomy.** Labels are the API for dispatch queries.

---

## When to Create an Issue

Create an issue for:
- Any bug found (even if fixed immediately — document it)
- Any architectural decision
- Any cross-agent handoff
- Any batch job or content sprint
- Any quality standard change
- Any tool or pipeline change

Do NOT create issues for:
- Single-line fixes with no broader pattern
- Personal session notes (use memory instead)

---

## Issue Content Standards

A good issue has:

1. **Title**: `area: brief description` (e.g. `fix: meta sections oversized in 9 modules`)
2. **Problem**: What's wrong, with evidence
3. **Root cause**: Why it happened
4. **Affected modules/files**: Specific list where applicable
5. **Fix**: What was done or what needs doing
6. **Commands**: Exact commands to reproduce/verify

Template for bug reports:
```markdown
## Problem
[What is wrong, with example]

## Root Cause
[Why it happened]

## Affected
[List of modules/files]

## Fix
[What was done or what needs doing]

## Verify
```bash
[exact command to verify fix]
```
```

---

## Commit ↔ Issue Linking

Always reference issues in commits:
```
fix: correct Phase A meta splitting rules (#589)
```

Use:
- `Fixes #N` — auto-closes issue on merge
- `Refs #N` — links without closing
- `Closes #N` — explicit close

---

## Dispatch Queries

Find work using label queries:

```bash
# Critical blockers first
gh issue list --label priority:blocking --state open

# High-priority infrastructure
gh issue list --label priority:high --label area:infra --state open

# Unclaimed work (no working: label)
gh issue list --state open --json number,title,labels \
  --jq '[.[] | select(.labels | map(.name) | all(startswith("working:") | not))] | .[:10]'

# Content work not claimed
gh issue list --label area:content --state open
```

---

## Agent Claim Protocol

**Agents never self-assign.** Only the user or orchestrator assigns work.

1. User assigns → agent claims:
   ```bash
   gh issue edit {N} --add-label "working:claude"
   gh issue comment {N} --body "Starting: [brief plan]"
   ```

2. Agent completes → removes working label:
   ```bash
   gh issue edit {N} --remove-label "working:claude"
   gh issue edit {N} --add-label "review:human"  # or review:gemini
   ```

3. Work done, no review needed:
   ```bash
   gh issue close {N} --comment "Done: [what was done]"
   ```

---

## Cross-Session Memory Pattern

Issues serve as memory because they survive session expiry. Use this pattern:

**Start of session:**
```bash
# What was I working on?
gh issue list --label working:claude --state open
```

**During work:** Comment progress on the issue every significant step.

**End of session:** Comment what was completed, what's next, any blockers.

This means the next Claude session can pick up context from the issue without relying on MCP memory (which may not persist across restarts).

---

## Cross-Agent Handoff

When handing off to Gemini:

```bash
# Post content on the issue
gh issue comment {N} --body "[full review/spec/request]"

# Ping Gemini
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "New task posted on #N. Please read and start." --task-id issue-N
```

Never put the substantive request in the broker message. The issue is the source of truth.

---

## Issue Hygiene

- Close issues when done — don't leave them open indefinitely
- Update issue titles if scope changes
- Link related issues to each other
- Don't create duplicate issues — search first
- Stale `working:` labels (>3 days) should be removed and issue re-triaged
