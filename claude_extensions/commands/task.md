# /task - GitHub Issues Workflow for Complex Tasks

<skill>
name: task
description: Manage complex tasks via GitHub Issues. Creates issues, tracks progress, handles handoffs to Gemini, and maintains session state.
arguments: |
  create "Title"           - Create GH issue (NO branch)
  update #N "Progress"     - Add comment, update checkboxes
  close #N                 - Close with summary
  list                     - Show active issues
  handoff #N gemini "msg"  - Hand to Gemini for review
  clear                    - Clear active task without closing
</skill>

## Purpose

Bridge local work with GitHub Issues for complex, multi-step tasks. Provides:
- **Unified tracking** - Single source of truth in GH Issues
- **Phase-based workflow** - Planning → Implementation → Testing → QA
- **Cross-agent collaboration** - Seamless Claude ↔ Gemini handoffs
- **Auto-updates** - Other skills update active task automatically

## When to Use

**Suggest for complex work** (batch, multi-file, research-needed):

```
Claude: "This looks like a complex task (batch processing 5 modules).
         Want me to create a GH issue to track it?"
User: "yes" / "no, just do it"
```

**Triggers:**
- Batch operations (3+ modules)
- Research-first content writing
- Multi-phase work
- Cross-agent collaboration needed
- User requests explicit tracking

**Skip for:**
- Single module fixes
- Quick edits
- Simple queries

## Commands

### /task create "Title"

Creates a GitHub issue with the complex-task template.

```bash
gh issue create --title "Title" --template "complex-task.md" --label "task,working:claude"
```

**Effects:**
- Creates issue with phases template
- Adds `working:claude` label
- Sets `ACTIVE_TASK_ID` (session state)
- **NO branch** (work on main)

**Example:**
```
/task create "Fix C1-BIO M25-M29 word targets"

📋 Created issue #500: "Fix C1-BIO M25-M29 word targets"
   Labels: task, working:claude
   Active task set: #500

   Phase 1: Planning ⬜
   Phase 2: Implementation ⬜
   Phase 3: Testing ⬜
   Phase 4: QA/Review ⬜
```

### /task update #N "Progress"

Adds a progress comment to the issue.

```bash
gh issue comment N --body "Progress update message"
```

**Example:**
```
/task update #500 "Phase 1 complete - approach documented"

📋 Updated #500: Added progress comment
```

### /task close #N

Closes the issue with a summary. Prompts for lessons if errors occurred.

```bash
gh issue close N --comment "Summary message"
```

**Example:**
```
/task close #500 "All modules expanded. Audits pass."

📋 Closed #500
   (No errors occurred - skipping lessons prompt)
   Active task cleared ✅
```

**With errors:**
```
/task close #500 "Completed with fixes"

📋 Closed #500
   ⚠️ Errors occurred during this task.
   Any lessons to capture for tasks/lessons.md?

User: "Never change word_target to match short content"

📋 Added to lessons.md ✅
   Active task cleared
```

### /task list

Shows active/recent issues.

```bash
gh issue list --label "task" --state open --limit 10
```

**Example:**
```
/task list

📋 Active Tasks:
#500 [working:claude] Fix C1-BIO M25-M29 word targets
#498 [review:gemini] B2-HIST naturalness audit
#495 [blocked] C1-BIO research pipeline
```

### /task handoff #N gemini "message"

Transfers task to Gemini. **CRITICAL: Issue is the source of truth, not the message.**

**Pattern (CORRECT):**
```
/task handoff #506 gemini "assigned"

Message sent: "Issue #506 is assigned to you. Read it, then:
  a) Start working + update issue with progress, OR
  b) Request UI trigger for collaborative session with user"
```

**Anti-Pattern (WRONG - DO NOT DO THIS):**
```
/task handoff #506 gemini "Process these 19 modules: ivan-vyhovskyi, bohdan..."
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                          ❌ Duplicates issue content
                          ❌ Errors propagate (wrong word targets, etc.)
                          ❌ Issue becomes redundant
```

**Why this matters:**
- **Single source of truth** - Gemini reads issue, not message
- **No inherited errors** - Gemini checks config.py himself
- **Proper workflow** - Gemini learns to use GitHub issues
- **User monitoring** - Progress visible in GitHub, not buried in broker

**Effects:**
1. Changes label: `working:claude` → `working:gemini`
2. Adds handoff comment with link
3. Sends SHORT message via broker (issue reference only)

**Validation (Claude MUST check):**
- ⚠️ If message > 200 chars: "Message too long. Put details in issue, send only reference."
- ⚠️ If issue doesn't exist: "Issue #N not found. Create it first."
- ⚠️ If issue is closed: "Issue #N is closed. Reopen or create new."

**Implementation:**
```bash
# Update label
gh issue edit N --remove-label "working:claude" --add-label "working:gemini"

# Add handoff comment (brief)
gh issue comment N --body "🔄 Handed off to Gemini"
```

```python
# Send SHORT message (issue reference only)
mcp__message-broker__send_message(
    to="gemini",
    from_llm="claude",
    content="""Issue #N is assigned to you.

Read it at: https://github.com/{repo}/issues/N

Then either:
a) Start working autonomously - update issue with progress as you go
b) Request UI trigger if you want collaborative session with user

Do NOT wait for detailed instructions - the issue has everything.""",
    message_type="handoff",
    task_id="gh-N"
)
```

**Example (correct):**
```
/task handoff #506 gemini "assigned"

📋 Handed off #506 to Gemini
   Labels: task, working:gemini
   Message: "Issue #506 is assigned to you. Read it..."

   ✅ Short message (issue reference only)
   ✅ Gemini will read issue for details
```

**Gemini's response options:**
1. **Autonomous work**: Start immediately, update issue with progress
2. **Request UI**: "I'd like to work on this with user present. Please trigger me from UI."

### /task clear

Clears the active task without closing the issue.

**Example:**
```
/task clear

📋 Active task cleared (was #500)
   Issue #500 remains open
```

## Session State

The skill tracks `ACTIVE_TASK_ID` during the session:

- Set by `/task create`
- Cleared by `/task close` or `/task clear`
- New sessions start with no active task
- One active task at a time

**Check active task:**
```
/task

📋 Active task: #500 "Fix C1-BIO M25-M29 word targets"
   Phase 1: Planning ✅
   Phase 2: Implementation ⬜ (current)
   ...
```

## Full Integration: Auto-Updates

When `ACTIVE_TASK_ID` is set, other skills auto-update the issue:

| Skill | Auto-Update |
|-------|-------------|
| `/research` | "📚 Research completed for {topic}" |
| `/expand` | "📝 Expanded {file} to {words} words" |
| `/module` | "🔧 Module {num} processed: {status}" |
| `/module-fix` | "🔨 Fixed {count} issues in {file}" |
| `/batch-fix` | "🔧 Batch: {passed}/{total} modules fixed" |
| `/check-gemini` | "📬 Gemini response received" |
| `git commit` | Suggests: "Add (#N) to commit message?" |

**When no active task:** Skills work normally without GH updates.

**Implementation pattern for other skills:**
```python
# At end of skill execution:
if ACTIVE_TASK_ID:
    gh issue comment ACTIVE_TASK_ID --body "📝 Skill result summary"
```

## Commit Integration

When committing during an active task:

```
Claude: "Ready to commit. Add (#500) to message?"
User: "yes" / "no"

# If yes:
git commit -m "Fix word targets for C1-BIO M25-M29 (#500)"
```

## Labels

Create these labels if they don't exist:

```bash
# Assignment (mutually exclusive)
gh label create "working:claude" --color "D97706" --description "Claude is actively working"
gh label create "working:gemini" --color "4285F4" --description "Gemini is actively working"
gh label create "working:unassigned" --color "CCCCCC" --description "Not yet claimed"

# Status
gh label create "review:gemini" --color "4285F4" --description "Ready for Gemini review"
gh label create "review:human" --color "7057FF" --description "Needs human review"
gh label create "blocked" --color "B60205" --description "Waiting on something"

# Type
gh label create "task" --color "1D76DB" --description "Tracked task"
gh label create "task:content" --color "0E8A16" --description "Content writing/expansion"
gh label create "task:fix" --color "FBCA04" --description "Bug fix"
gh label create "task:feature" --color "A2EEEF" --description "New feature"
```

## Example Full Workflow

```
User: We need to fix word targets for C1-BIO batch 25-29

Claude: "This looks like a complex task (4 modules, research needed).
         Want me to create a GH issue to track it?"

User: yes

Claude: /task create "Fix C1-BIO M25-M29 word targets"

📋 Created issue #500: "Fix C1-BIO M25-M29 word targets"
   Label: working:claude
   Active task set: #500

   Phase 1: Planning ⬜
   Phase 2: Implementation ⬜
   Phase 3: Testing ⬜
   Phase 4: QA/Review ⬜

Starting Phase 1: Research...

[/research runs → auto-comment added to #500]
[Commit: "Add (#500)?" → user: "yes"]

Claude: /task update #500 "Phase 1 complete"

📋 Updated #500: ✅ Phase 1

[/expand runs on each module → auto-comments to #500]

Claude: /task handoff #500 gemini "Review naturalness"

📋 Handed off #500 to Gemini
   Label changed: review:gemini
   Broker message sent

[Gemini reviews, responds via broker]

Claude: /task close #500 "All modules expanded. Audits pass."

📋 Closed #500
   Active task cleared ✅
```

## Gemini Response Flow

After handoff, Gemini responds via broker:

```python
# Gemini sends:
mcp__message-broker__send_message(
    to="claude",
    from_llm="gemini",
    content="Review complete. Found 2 issues: ...",
    message_type="response",
    task_id="gh-500"
)
```

Claude picks up with `/check-gemini`:

```
📬 Response from Gemini for #500:
   "Review complete. Found 2 issues: ..."

   [Auto-comment added to #500]
```

## Error Tracking

Track errors during task execution:

- Count failures during the session
- On `/task close`, if errors > 0, prompt for lessons
- Lessons saved to `tasks/lessons.md`

```markdown
# tasks/lessons.md format:
## [Date] - [Category]
**Task**: #500 - Fix C1-BIO M25-M29 word targets
**Mistake**: Changed word_target instead of expanding content
**Correction**: Word targets are minimums, not maximums
**Rule**: Never change word_target to match short content - expand content instead
```

## Future Enhancement

When humans join the team, add `--branch` flag:

```
/task create "Feature X" --branch
  → Creates issue
  → Creates branch task/feature-x
  → Sets up PR workflow
```

Disabled by default until team grows.
