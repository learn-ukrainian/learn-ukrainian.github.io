# Task Workflow: GitHub Issues for Complex Tasks

> **Quick Start:** Use `/task create "Title"` to start tracking complex work.

## Overview

The `/task` skill bridges local development work with GitHub Issues, providing:

- **Single source of truth** - GitHub Issues (not local files)
- **Phase-based tracking** - Planning → Implementation → Testing → QA
- **Cross-agent collaboration** - Claude ↔ Gemini handoffs
- **Auto-updates** - Skills automatically log progress

## Table of Contents

1. [When to Use](#when-to-use)
2. [Commands Reference](#commands-reference)
3. [Workflow Phases](#workflow-phases)
4. [Full Integration](#full-integration)
5. [Detailed Examples](#detailed-examples)
6. [Gemini Handoff](#gemini-handoff)
7. [Lessons Learned](#lessons-learned)
8. [Labels](#labels)
9. [Design Decisions](#design-decisions)
10. [Troubleshooting](#troubleshooting)
11. [Implementation Guide](#implementation-guide)

---

## When to Use

### Use for Complex Work

| Scenario | Why Track |
|----------|-----------|
| Batch operations (3+ modules) | Multiple files, easy to lose track |
| Research-first content writing | Multi-phase work needs progress logging |
| Multi-phase implementation | Checkpoints help resume after interruption |
| Cross-agent collaboration | Handoffs need clear state |
| Work that might fail | Lessons capture prevents repeat mistakes |

### Skip for Simple Work

| Scenario | Why Skip |
|----------|----------|
| Single module fix | Overhead not worth it |
| Quick edits | Done before you'd create the issue |
| Simple queries | No state to track |
| Trivial bug fixes | < 5 min work |

### Suggestion Pattern

Claude will proactively suggest task tracking:

```
Claude: "This looks like a complex task (batch processing 5 modules).
         Want me to create a GH issue to track it?"
User: "yes" / "no, just do it"
```

**Detection triggers:**
- Keywords: "batch", "all modules", "M1-M10", etc.
- Quantity: 3+ modules mentioned
- Duration indicators: "comprehensive", "thorough audit"
- Research keywords: "research first", "need to investigate"

---

## Commands Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `/task create "Title"` | Create GH issue, set as active | `/task create "Fix C1-BIO word targets"` |
| `/task update #N "msg"` | Add progress comment | `/task update #500 "Phase 1 complete"` |
| `/task close #N` | Close with summary, prompt for lessons | `/task close #500 "All audits pass"` |
| `/task list` | Show active/recent tasks | `/task list` |
| `/task handoff #N gemini "msg"` | Transfer to Gemini | `/task handoff #500 gemini "Review naturalness"` |
| `/task clear` | Clear active task (keep issue open) | `/task clear` |
| `/task` | Show current active task status | `/task` |

### Command Details

#### `/task create "Title"`

Creates a new GitHub issue using the `complex-task.md` template.

**What happens:**
1. Creates issue with phases template
2. Adds labels: `task`, `working:claude`
3. Sets session variable `ACTIVE_TASK_ID`
4. **NO branch created** (work on main)

**Optional labels:**
```
/task create "Fix word targets" --label task:content
/task create "Add new feature" --label task:feature
```

#### `/task update #N "msg"`

Adds a progress comment to the issue.

**Use for:**
- Phase transitions
- Checkpoint documentation
- Blocker notes
- Progress milestones

**Example comments:**
```
/task update #500 "Phase 1 complete: Identified 4 modules under target"
/task update #500 "Blocker: Module 27 meta file missing word_target"
/task update #500 "Expanded M25 from 2100 to 3200 words"
```

#### `/task handoff #N gemini "msg"`

Transfers the task to Gemini for review.

**What happens:**
1. Changes label: `working:claude` → `review:gemini`
2. Adds comment: `@gemini: {message}`
3. Sends broker message with context

**Best practices:**
- Include what to review
- Mention specific concerns
- Link to relevant files

---

## Workflow Phases

### Phase 1: Planning

**Goal:** Understand the problem, document approach.

**Activities:**
- Research/explore codebase
- Read relevant documentation
- Check existing patterns
- Document findings in issue comment
- Get user approval if needed

**Auto-updates from:** `/research`

**Example Phase 1 comment:**
```markdown
## Phase 1: Planning Complete

### Findings
- Modules M25-M29 all under word target
- M25: 2100 words (target 3000)
- M26: 2300 words (target 3000)
- M27: 1900 words (target 3000) - CRITICAL
- M28: 2500 words (target 3000)
- M29: 2200 words (target 3000)

### Approach
1. Expand each module's explanation sections
2. Add more examples for complex concepts
3. Enrich cultural context sections
4. Run audit after each expansion

### User Approval
Proceeding with approach unless redirected.
```

### Phase 2: Implementation

**Goal:** Make the changes on main branch.

**Activities:**
- Implement changes incrementally
- Commit with `#issue` references
- Update progress via comments
- Document any deviations from plan

**Auto-updates from:** `/expand`, `/module`, `/module-fix`

**Example Phase 2 comments:**
```markdown
📝 Expanded M25 to 3150 words
- Added 400 words to grammar explanation
- Added 300 words to cultural context
- Added 2 new example dialogues

📝 Expanded M26 to 3050 words
- Enriched vocabulary practice section
- Added regional variation notes
```

### Phase 3: Testing

**Goal:** Validate the work.

**Activities:**
- Run audits and validation
- Test edge cases
- Document results in comment
- Fix any regressions

**Auto-updates from:** Audit scripts

**Example Phase 3 comment:**
```markdown
## Phase 3: Testing Complete

### Audit Results
| Module | Word Count | Target | Status |
|--------|------------|--------|--------|
| M25 | 3150 | 3000 | ✅ |
| M26 | 3050 | 3000 | ✅ |
| M27 | 3100 | 3000 | ✅ |
| M28 | 3200 | 3000 | ✅ |
| M29 | 3000 | 3000 | ✅ |

### Additional Checks
- [x] Ukrainian grammar validation passed
- [x] Activity counts meet minimums
- [x] No broken references
```

### Phase 4: QA/Review

**Goal:** Quality assurance before completion.

**Activities:**
- Self-review all changes
- Gemini review via `/task handoff`
- Update documentation if needed
- Capture lessons learned

**Auto-updates from:** `/check-gemini`

---

## Full Integration

### Session State

The skill tracks `ACTIVE_TASK_ID` during the session:

- **Set by:** `/task create`
- **Cleared by:** `/task close` or `/task clear`
- **New sessions:** Start with no active task
- **Limit:** One active task at a time

**Check active task:**
```
/task

📋 Active task: #500 "Fix C1-BIO M25-M29 word targets"
   Phase 1: Planning ✅
   Phase 2: Implementation ⬜ (current)
   Phase 3: Testing ⬜
   Phase 4: QA/Review ⬜
```

### Auto-Updates from Other Skills

When `ACTIVE_TASK_ID` is set, other skills automatically update the issue:

| Skill | Auto-Comment Format |
|-------|---------------------|
| `/research` | 📚 Research completed for {topic} |
| `/expand` | 📝 Expanded {file} to {words} words |
| `/module` | 🔧 Module {num} processed: {status} |
| `/module-fix` | 🔨 Fixed {count} issues in {file} |
| `/batch-fix` | 🔧 Batch: {passed}/{total} modules fixed |
| `/check-gemini` | 📬 Gemini response received |

**When no active task:** Skills work normally without GH updates.

### Commit Integration

When committing during an active task:

```
Claude: "Ready to commit. Add (#500) to message?"
User: "yes"
```

**If yes:**
```bash
git commit -m "Expand C1-BIO M25-M29 to meet word targets (#500)"
```

**Benefits:**
- Issue shows linked commits
- Easy to trace changes
- Auditable history

---

## Detailed Examples

### Example 1: Content Expansion Task

```
User: We need to fix word targets for C1-BIO batch 25-29

Claude: "This looks like a complex task (5 modules, expansion needed).
         Want me to create a GH issue to track it?"

User: yes

Claude: /task create "Fix C1-BIO M25-M29 word targets"

📋 Created issue #500: "Fix C1-BIO M25-M29 word targets"
   Labels: task, working:claude
   Active task set: #500

   Phase 1: Planning ⬜
   Phase 2: Implementation ⬜
   Phase 3: Testing ⬜
   Phase 4: QA/Review ⬜

Let me start with Phase 1 - analyzing current state...

[Reads all 5 module files]
[Documents findings in issue comment]

/task update #500 "Phase 1 complete: All modules under target, approach documented"

📋 Updated #500: Added progress comment

Now Phase 2 - expanding modules...

[Runs /expand on M25]
→ Auto-comment: "📝 Expanded M25 to 3150 words"

[Runs /expand on M26]
→ Auto-comment: "📝 Expanded M26 to 3050 words"

[Commits: "Expand M25-M26 (#500)"]

[Continues M27-M29...]

Now Phase 3 - testing...

[Runs audits]
[Documents results in comment]

/task update #500 "Phase 3 complete: All modules pass audit"

Phase 4 - requesting Gemini review...

/task handoff #500 gemini "Review naturalness of expanded content in M25-M29"

📋 Handed off #500 to Gemini
   Labels: task, review:gemini
   Broker message sent

[Gemini reviews → responds via broker]
[Claude picks up with /check-gemini]
→ Auto-comment: "📬 Gemini response received: All content natural, minor suggestions applied"

/task close #500 "All modules expanded, pass audit, Gemini approved"

📋 Closed #500
   Active task cleared ✅
```

### Example 2: Bug Fix Task

```
User: Module 15 is failing audit - investigate and fix

Claude: "This is a single module fix. Track with GH issue?"

User: no, just fix it

[Claude fixes without creating issue]
```

vs.

```
User: B1 modules 10-20 are all failing outline compliance

Claude: "Complex task (11 modules). Create GH issue to track?"

User: yes

Claude: /task create "Fix B1 M10-M20 outline compliance" --label task:fix

[Full workflow with auto-updates...]
```

### Example 3: Research Task with Gemini Collaboration

```
User: Research and write the Danylo Apostol biography module

Claude: "Complex task (research + writing). Create GH issue to track?"

User: yes

Claude: /task create "Write C1-BIO Danylo Apostol module"

Phase 1: Let me ask Gemini to help research while I prepare the structure...

[Sends to Gemini via broker: "Research Danylo Apostol for C1-BIO module"]

Meanwhile, I'll read the plan and meta files...

[/research runs locally → auto-comment to issue]

/check-gemini

📬 Response from Gemini for #501:
   "Research complete: Key dates 1654-1734, last elected hetman,
    Decisive Points 1728, recommended quotes..."

[Auto-comment: "📬 Gemini response received"]

Now writing content with combined research...

[/module runs → auto-comment to issue]

/task handoff #501 gemini "Review naturalness and historical accuracy"

[Gemini reviews...]

/task close #501 "Module complete, 3500 words, passes audit"
```

### Example 4: Resuming After Session Break

```
[New session starts]

User: Continue working on the C1-BIO expansion

Claude: Let me check what's in progress...

/task list

📋 Active Tasks:
#500 [working:claude] Fix C1-BIO M25-M29 word targets
     Last update: Phase 2 in progress, M25-M27 done

I found task #500. Let me read the issue to see where we left off...

[Reads issue comments]

Resuming from M28. Setting active task...

[Session state: ACTIVE_TASK_ID = 500]

Continuing Phase 2...
```

---

## Gemini Handoff

### CRITICAL: Issue is Source of Truth

**The GitHub issue contains ALL task details. The handoff message should be SHORT (issue reference only).**

| Pattern | Status | Why |
|---------|--------|-----|
| Short message + issue reference | ✅ CORRECT | Gemini reads issue, checks configs |
| Full task details in message | ❌ WRONG | Errors propagate, duplication |

### Correct Handoff Pattern

```
/task handoff #506 gemini "assigned"
```

**What Claude sends (SHORT):**
```python
mcp__message-broker__send_message(
    to="gemini",
    from_llm="claude",
    content="""Issue #506 is assigned to you.

Read it at: https://github.com/{repo}/issues/506

Then either:
a) Start working autonomously - update issue with progress as you go
b) Request UI trigger if you want collaborative session with user

Do NOT wait for detailed instructions - the issue has everything.""",
    message_type="handoff",
    task_id="gh-506"
)
```

### Why This Pattern

| Benefit | Explanation |
|---------|-------------|
| **Single source of truth** | Issue has all details, no duplication |
| **No inherited errors** | Gemini checks config.py himself |
| **User monitoring** | Progress visible in GitHub |
| **Proper workflow** | Gemini learns to use issues |

### Anti-Pattern (DO NOT DO)

```
❌ /task handoff #506 gemini "Process these 19 modules: ivan-vyhovskyi, bohdan...
   word target is 3500+, run /module and /review-content-v4 for each..."

   Problems:
   - Duplicates issue content
   - Word target was WRONG (should be 4000, not 3500)
   - Gemini doesn't learn to read issues
   - Errors propagate without correction
```

### Validation Before Handoff

**Claude MUST check:**
- ⚠️ Message > 200 chars? → "Put details in issue, send only reference"
- ⚠️ Issue doesn't exist? → "Issue #N not found. Create it first."
- ⚠️ Issue closed? → "Issue #N is closed. Reopen or create new."

### Gemini's Work Modes

After receiving handoff, Gemini chooses:

1. **Autonomous Mode** (default):
   - Reads issue
   - Checks configs (word targets, etc.)
   - Starts working
   - Updates issue with progress as he goes
   - User monitors via GitHub

2. **Collaborative Mode** (on request):
   - Replies: "Request UI trigger for collaborative session"
   - User invokes Gemini from terminal
   - User watches and helps in real-time

### Gemini Response Flow

```
Gemini reads issue → works → updates issue → sends response:
{
    to: "claude",
    from_llm: "gemini",
    content: "Work complete. See issue #506 for details.",
    message_type: "response",
    task_id: "gh-506"
}

Claude picks up with /check-gemini:
→ Reads message
→ Acknowledges
→ Auto-comments to issue
```

### Progress Tracking (in GitHub issue)

Gemini updates issue as he works:
```bash
gh issue comment 506 --body "✅ ivan-vyhovskyi - /module complete, audit passed"
gh issue comment 506 --body "✅ bohdan-khmelnytskyy - /module complete, audit passed"
gh issue comment 506 --body "⚠️ petro-mohyla - blocked on missing meta file"
```

User can monitor this in real-time via GitHub.

---

## Lessons Learned

### Error Tracking

During task execution, track errors:
- Audit failures
- Validation errors
- Unexpected issues
- Mistakes made

### Lessons Prompt

On `/task close`, if errors occurred:

```
📋 Closed #500
   ⚠️ Errors occurred during this task.
   Any lessons to capture for tasks/lessons.md?

User: "Never change word_target in meta to match short content"

📋 Added to lessons.md ✅
```

### Lessons File Format

```markdown
# tasks/lessons.md

## [2025-02-05] - Content Quality
**Task**: #500 - Fix C1-BIO M25-M29 word targets
**Mistake**: Initially tried changing word_target instead of expanding content
**Correction**: Word targets are minimums, not maximums
**Rule**: Never change word_target to match short content - expand content instead
**Applied**: [Date when successfully avoided]
```

### Why This Matters

- Prevents repeat mistakes
- Builds institutional knowledge
- Reviewed at session start
- Feeds into process improvements

---

## Labels

### Label Categories

**Assignment (mutually exclusive):**
| Label | Color | Purpose |
|-------|-------|---------|
| `working:claude` | #D97706 (orange) | Claude actively working |
| `working:gemini` | #4285F4 (blue) | Gemini actively working |
| `working:unassigned` | #CCCCCC (gray) | Not yet claimed |

**Status:**
| Label | Color | Purpose |
|-------|-------|---------|
| `review:gemini` | #4285F4 (blue) | Ready for Gemini review |
| `review:human` | #7057FF (purple) | Needs human review |
| `blocked` | #B60205 (red) | Waiting on something |

**Type:**
| Label | Color | Purpose |
|-------|-------|---------|
| `task` | #1D76DB (blue) | Base task label |
| `task:content` | #0E8A16 (green) | Content writing task |
| `task:fix` | #FBCA04 (yellow) | Bug fix task |
| `task:feature` | #A2EEEF (cyan) | Feature task |

### Label Transitions

```
Create task:
  → task, working:unassigned

Claude claims:
  working:unassigned → working:claude

Handoff to Gemini:
  working:claude → review:gemini

Gemini done:
  review:gemini → working:claude (if more work)
  review:gemini → (close) (if done)

Blocked:
  + blocked (add, don't replace working label)
```

---

## Design Decisions

### No Branches (For Now)

Work happens on `main` branch:

**Reasons:**
- Multiple agents work in same directory simultaneously
- Branches caused data loss with parallel agents
- Modules are naturally isolated (different files)
- Single human developer (no merge conflicts)

**Future-proof:**
- `--branch` flag designed but disabled
- When team grows, enable branching
- PR workflow ready to activate

### Single Template

One universal `complex-task.md` template covers:
- Content tasks
- Bug fixes
- Features
- Cross-agent work

**Rationale:**
- Simpler to maintain
- Consistent structure
- Phases apply to all work types
- Labels differentiate types

### Lessons on Close Only

Prompt for lessons **only if errors occurred**:

**Benefits:**
- Reduces friction for clean completions
- Captures learnings when they matter
- No annoying prompts on success
- Builds meaningful knowledge base

### Session State (Not Persistent)

Active task is session-only, not persisted:

**Why:**
- Avoids stale state issues
- Forces explicit task resumption
- `/task list` shows what's open
- Clean start each session

---

## Troubleshooting

### Issue Not Found

```
Error: Issue #N not found
```

**Fixes:**
- Verify issue number exists
- Check repo access (`gh auth status`)
- Issue may have been closed/deleted

### Label Doesn't Exist

```
Error: Label 'working:claude' not found
```

**Fix:** Run label creation:
```bash
gh label create "working:claude" --color "D97706" --description "Claude is actively working"
```

### Broker Message Failed

```
Error: Failed to send message to Gemini
```

**Fixes:**
- Check MCP connection: `mcp__message-broker__check_inbox`
- Gemini may be on cooldown (wait 60s)
- Queue message, process later

### Active Task Lost

Session state resets between conversations.

**Recovery:**
```
/task list
→ Find the issue number
→ Manually continue work
→ Reference issue in commits
```

### Permissions Error

```
Error: Resource not accessible by integration
```

**Fix:** Check GitHub token permissions:
```bash
gh auth status
gh auth refresh
```

---

## Implementation Guide

### For Claude (Executing the Skill)

When `/task create` is invoked:

```bash
# 1. Create issue
gh issue create \
  --title "Title here" \
  --template "complex-task.md" \
  --label "task,working:claude"

# 2. Get issue number from output
# 3. Set session state: ACTIVE_TASK_ID = {number}
# 4. Report to user
```

When auto-updating from other skills:

```bash
# Check if active task exists
if [ -n "$ACTIVE_TASK_ID" ]; then
  gh issue comment $ACTIVE_TASK_ID --body "📝 Update message"
fi
```

When `/task handoff` is invoked:

```bash
# 1. Update labels
gh issue edit $N \
  --remove-label "working:claude" \
  --add-label "review:gemini"

# 2. Add comment
gh issue comment $N --body "@gemini: $MESSAGE"

# 3. Send broker message
# (via MCP tool)
```

### For Other Skills (Integration Pattern)

Skills should check for active task and update:

```python
# At end of skill execution:
if ACTIVE_TASK_ID:
    comment = f"📝 {skill_name}: {result_summary}"
    # gh issue comment ACTIVE_TASK_ID --body comment
```

### For Commits

Before committing during active task:

```
Claude: "Ready to commit changes. Add (#500) to message?"
```

If user confirms:
```bash
git commit -m "Commit message (#500)"
```

---

## Related Documentation

- **Skill definition:** `claude_extensions/commands/task.md`
- **Issue template:** `.github/ISSUE_TEMPLATE/complex-task.md`
- **Message broker:** `CLAUDE.md` (Inter-Agent Communication section)
- **Lessons file:** `tasks/lessons.md`
- **Claude-Gemini cooperation:** `docs/CLAUDE-GEMINI-COOPERATION.md`

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    /task Quick Reference                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  /task create "Title"      Create issue, set active          │
│  /task update #N "msg"     Add progress comment              │
│  /task close #N            Close issue, prompt lessons       │
│  /task list                Show open tasks                   │
│  /task handoff #N gemini   Transfer for review               │
│  /task clear               Clear active (keep open)          │
│  /task                     Show current status               │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Phases: Planning → Implementation → Testing → QA            │
├─────────────────────────────────────────────────────────────┤
│  Labels:                                                     │
│    working:claude   Claude working                           │
│    working:gemini   Gemini working                           │
│    review:gemini    Ready for review                         │
│    task:content     Content task                             │
│    task:fix         Bug fix                                  │
│    task:feature     Feature                                  │
└─────────────────────────────────────────────────────────────┘
```
