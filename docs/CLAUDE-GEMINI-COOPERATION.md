# Claude-Gemini Cooperation Workflow

**Status**: Planning / Initial Implementation
**Created**: February 1, 2026
**Task**: #18
**GitHub Issue**: [#487](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/487)
**Last Updated**: February 1, 2026 (incorporated Gemini's review feedback)

---

## Vision: LLM Committee System

**Not just handoff, but mutual review and collaboration.**

Two LLMs working together, each playing to their strengths, reviewing each other's work.

```
                    ┌─────────────────────────────────────┐
                    │         TASK ROUTER                 │
                    │  (decides which LLM for what)       │
                    └─────────────────────────────────────┘
                           │              │
              ┌────────────▼────┐    ┌────▼────────────┐
              │     CLAUDE      │    │     GEMINI      │
              │  Opus/Sonnet    │    │  Pro / Flash    │
              └────────────────┬┘    └┬────────────────┘
                               │      │
                    ┌──────────▼──────▼──────────┐
                    │     MUTUAL REVIEW           │
                    │  Each reviews other's work  │
                    └─────────────────────────────┘
```

---

## Problem Statement

### Current State
- **Claude**: Planning, strategy, coding, quality review
- **Gemini** (via gemini-cli): Content writing (better Ukrainian, cost-efficient)
- **Handoff**: Manual, painful, context loss, duplicated explanations
- **Skills**: Claude's prompts don't work well for Gemini

### Pain Points (All Four)
1. ❌ Context loss during handoff
2. ❌ Inconsistent outputs between LLMs
3. ❌ Duplicated work (explain same things twice)
4. ❌ Skill/prompt compatibility issues

### Desired State
- ✅ Seamless handoff with preserved context
- ✅ Shared skill system (works for both LLMs)
- ✅ Automated pipeline (Claude triggers Gemini with full context)
- ✅ Quality gate (mutual review)
- ✅ Bidirectional communication (they can discuss)

---

## Role Distribution

### Strengths by LLM

| LLM | Strengths |
|-----|-----------|
| **Claude Opus** | Strategic planning, complex decisions, final quality gate |
| **Claude Sonnet** | Routine tasks, quick fixes, iteration |
| **Gemini 3 Pro Preview** | Ukrainian content writing, deep review, complex tasks |
| **Gemini 3 Flash Preview** | Linting, style/syntax checks, bulk operations (cost-efficient) |

### Task Assignment (Updated per Gemini's feedback)

| Task Type | Primary | Secondary/Review | Notes |
|-----------|---------|------------------|-------|
| **Planning & Strategy** | Claude | Gemini reviews | Claude designs, Gemini sanity checks |
| **Content Writing** | Gemini Pro | Claude reviews | Ukrainian content, Gemini excels |
| **Coding** | Claude | Gemini Pro reviews | Claude codes, **Pro** for logic review |
| **Lint/Style Review** | Gemini Flash | - | Flash for syntax/style only |
| **Deep Quality Review** | Both | Cross-review | Both perspectives, comprehensive |
| **Quick Review** | Either | - | Whoever is cheaper/faster |

> **Gemini's note**: Use Pro (not Flash) for code logic review. Flash is only reliable for linting/style/syntax.

---

## Communication Architecture

### Bidirectional MCP Message Broker

```
┌─────────────────────────────────────────────────────────────────┐
│                      SQLite MESSAGE QUEUE                        │
│                   (.mcp/servers/message-broker/messages.db)      │
└─────────────────────────────────────────────────────────────────┘
          ▲                                    ▲
          │                                    │
          │ MCP Tools                          │ Direct DB Access
          │                                    │
┌─────────┴─────────┐              ┌───────────┴───────────┐
│      CLAUDE       │              │    GEMINI BRIDGE      │
│   (MCP Client)    │              │  (gemini_bridge.py)   │
│                   │              │                       │
│  Tools:           │              │  Commands:            │
│  - send_message   │              │  - inbox              │
│  - receive_msgs   │              │  - read <id>          │
│  - check_inbox    │              │  - send <text>        │
│  - get_conversation│             │  - process <id>       │
│  - acknowledge    │              │  - conversation <id>  │
└───────────────────┘              └───────────────────────┘
```

### Bidirectional Initiation ✅ FULLY SOLVED (No Human Required)

**Symmetric one-step commands:**
```bash
# Claude → Gemini
.venv/bin/python scripts/gemini_bridge.py ask-gemini "message" --task-id task

# Gemini → Claude
.venv/bin/python scripts/gemini_bridge.py ask-claude "message" --task-id task
```

Both directions are fully automated with session persistence for multi-turn conversations.

### Message Schema (SQLite Event Bus)

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,                    -- Group related messages
    from_llm TEXT NOT NULL,          -- 'claude', 'gemini', 'openai'
    to_llm TEXT NOT NULL,            -- 'claude', 'gemini', 'all'
    message_type TEXT,               -- See types below
    content TEXT NOT NULL,           -- Natural language message
    data TEXT,                       -- Structured data (YAML/JSON)
    payload TEXT,                    -- Large payload reference
    timestamp TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending'    -- pending, processing, completed
);

-- Session tracking for multi-turn conversations
CREATE TABLE sessions (
    task_id TEXT PRIMARY KEY,        -- Links to messages.task_id
    claude_session_id TEXT,          -- UUID for claude --resume
    gemini_session_id TEXT,          -- Reserved for future use
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Message Types

| Type | Purpose | Example |
|------|---------|---------|
| `query` | Ask another agent a question | "Where's the B2 vocab schema?" |
| `response` | Answer to a query | "It's in schemas/b2-vocab.yaml" |
| `request` | Request work/action | "Generate M15 content" |
| `handoff` | Transfer task with context | Full context dump + instructions |
| `context` | Share state/knowledge | Current task state, decisions made |
| `feedback` | Review or comment | "Looks good, minor issue on line 42" |
| `discussion` | Open-ended conversation | "What do you think about X?" |

### Key Technical Facts

1. **Context window**: Up to 2M tokens - rarely a bottleneck
2. **Output limit**: Usually the real constraint, not input
3. **Session state**: ✅ NOW PERSISTS via `sessions` table + `--resume`
4. **State of Truth**: File system + SQLite (messages.db)
5. **YAML reliability**: Generally good, but should self-validate
6. **Headless invocation**: Both agents can invoke each other via CLI

---

## Collaboration Patterns

### Pattern 1: Plan-Write-Review (Updated with Self-Correction)

```
Claude (Plan) → Gemini Pro (Write) → Gemini (Self-Audit) → Gemini (Fix) → Claude (Review)
```

**Use for**: Module content generation

> **Gemini's recommendation**: Don't review my draft until I've confirmed it passes automated gates.

### Pattern 2: Code-Review-Fix

```
Claude (Code) → Gemini Pro (Logic Review) → Claude (Fix)
```

**Use for**: Script development, bug fixes

> **Note**: Use Pro for logic, Flash only for lint/style.

### Pattern 3: Bidirectional Deep Review

```
Module Output
    │
    ├──▶ Claude Deep Review ──┐
    │                         │
    └──▶ Gemini Deep Review ──┴──▶ Consolidated Issues ──▶ Fix
```

**Use for**: Final quality validation before publication

### Pattern 4: Discussion/Feedback

```
Claude: "Gemini, what do you think about this approach?"
Gemini: "I see potential issues with X, consider Y instead..."
Claude: "Good point. Let me revise..."
```

**Use for**: Design decisions, problem-solving

> **Gemini's note**: Need standardized exchange format - see Context Packaging.

### Pattern 5: Parallel Generation

```
Same spec ──┬──▶ Claude generates
            │
            └──▶ Gemini generates ──▶ Pick best / merge
```

**Use for**: Comparing approaches, creative tasks

### Pattern 6: GitHub Issue Handoff (Async Collaboration)

```
Claude/Gemini                     GitHub Issue                    Other Agent
     │                                 │                               │
     ├──▶ Create issue ───────────────▶│                               │
     │    (full spec, checklist)       │                               │
     │                                 │◀── Later session triggers ────┤
     │                                 │                               │
     │◀── Read results ────────────────│◀── Work + update issue ───────┤
```

**Use for**:
- Async work that spans sessions
- Tasks requiring human visibility (GH notifications)
- Infrastructure work while other agent does different tasks
- Persistent task specs that survive context resets
- **Research spikes**: One agent researches & documents, other implements
- **Human-in-the-Loop (HITL)**: Sensitive topics needing user approval (e.g., decolonization narratives)
- **Dependency blocking**: When one agent is blocked by work better suited for the other

**How it works**:
1. **Initiator** creates GH issue with full task spec via `gh issue create`
2. **Issue contains**: Overview, task checklist, Definition of Done, related docs
3. **Later**: Other agent is triggered to work on the issue
4. **Agent reads issue**, performs work, updates issue with progress
5. **Completion**: Close issue or request review

**Required Issue Structure** (see `docs/templates/handoff-issue.md`):
- `## Overview` - What and why
- `## Tasks` - Checklist of work items
- `## Definition of Done` - Unambiguous completion criteria
- `## Related Files` - Links to relevant status JSONs, audit logs, docs
- `## Context` - Background info, decisions made, constraints

**Specialized Templates** (in `docs/templates/`):
| Template | Use Case |
|----------|----------|
| `handoff-issue.md` | Generic handoff (start here) |
| `handoff-module-correction.md` | Fixing audit failures |
| `handoff-infrastructure.md` | New tools, scripts, features |
| `handoff-batch-review.md` | Large-scale quality audits |
| `handoff-plan-review.md` | Reviewing YAML plans pre-generation |
| `handoff-bug-investigation.md` | Root cause analysis of bugs |

**State Labels** (for tracking without parsing body):
| Label | Meaning |
|-------|---------|
| `status:in-progress` | Work actively happening |
| `status:blocked` | Waiting on something (add comment explaining) |
| `status:ready-for-review` | Work complete, needs review |
| `agent:claude` | Claude is primary assignee |
| `agent:gemini` | Gemini is primary assignee |

**Benefits**:
- ✅ Human can see progress via GH notifications
- ✅ Task spec persists across sessions (no context loss)
- ✅ Clear accountability (who's working on what)
- ✅ Work can be paused/resumed
- ✅ Both agents can read/update the same issue
- ✅ Issues = "Long-term Memory", SQLite broker = "Short-term Memory"

**When to use Pattern 6 vs MCP Messages**:
| Criteria | Use Pattern 6 (GH Issue) | Use MCP Messages |
|----------|--------------------------|------------------|
| Task complexity | 3+ steps, multi-file | Simple, single action |
| Duration | Cross-session | Within session |
| Human visibility needed | Yes | No |
| Persistence required | Yes | No |
| Quick back-and-forth | No | Yes |
| Output length | 1000+ words | < 500 words |

> ⚠️ **MCP Timeout Limit**: The Gemini CLI has a 10-minute timeout. Long-form content generation (4000+ word modules) will timeout via MCP. For these tasks, create a **GitHub Issue** (Pattern 6) and the user will invoke Gemini directly.

**Use MCP for:**
- Reviews and feedback
- Quick questions
- Short content generation (< 500 words)
- Status checks

**Use GitHub Issues for:**
- 4000+ word module writing
- Any task requiring > 10 minutes of generation
- Complex multi-section content
- Async collaboration

**Avoiding Issue Bloat**:
- Reserve for tasks that actually benefit from persistence
- Don't create issues for trivial tasks (use MCP messages instead)
- Close issues promptly when done

**Context Drift Rule**:
> ⚠️ Always verify current file state before starting work on issues created >48h ago.

**Example**:
```bash
# Gemini creates infrastructure task
gh issue create \
  --title "feat(scoring): Add LLM verification infrastructure" \
  --body-file /tmp/issue-body.md \
  --label "enhancement" --label "agent:gemini"

# Returns: Issue #488

# Later, Claude triggers Gemini to work on it
.venv/bin/python scripts/gemini_bridge.py ask-gemini \
  "Work on issue #488. Read it with 'gh issue view 488' and implement the tasks." \
  --task-id issue-488-impl
```

**Tested**: 2026-02-02 - Gemini successfully created issue #488 via `gh` CLI.

---

## Context Packaging System (Gemini's Recommendations)

### Principle: File-Based Context Passing

Gemini recommends file-based context over clipboard/pasting:
- Write context to `.context.md` or `CONTEXT_HANDOFF.md`
- Gemini reads the file directly
- Superior to manual paste given large context window

### Standardized Handoff File

```yaml
# .gemini/handoff/current-task.yaml
meta:
  created_by: claude
  created_at: 2026-02-01
  task_id: b1-module-15
  purpose: content_generation

context:
  plan_file: curriculum/l2-uk-en/plans/b1/motion-approaching-departing.yaml
  meta_file: curriculum/l2-uk-en/b1/meta/motion-approaching-departing.yaml
  quick_ref: claude_extensions/quick-ref/B1.md

requirements:
  word_target: 3000
  sections: [from plan.content_outline]
  vocabulary: [from plan.vocabulary]

instructions_file: .gemini/current_instructions.md

validation:
  run_after_generation:
    - "npm run validate"
    - ".venv/bin/python scripts/audit_module.py {output_path}"

examples:
  good_output: [reference to successful module]
  avoid: [anti-patterns]
```

### Prompt Portability

Instead of hoping prompts paste correctly:
1. Claude writes instructions to `.gemini/current_instructions.md`
2. Tell Gemini: "Follow instructions in `.gemini/current_instructions.md`"
3. Gemini reads file directly

---

## Implementation Phases

### Phase 1: Communication Infrastructure ✅ DONE
**Goal**: Bidirectional message passing works

**Deliverables**:
- [x] MCP Message Broker server (`.mcp/servers/message-broker/server.py`)
- [x] Gemini Bridge script (`scripts/gemini_bridge.py`)
- [x] MCP configuration (`.mcp.json`)
- [x] Test basic message exchange ✅ WORKING
- [x] Seamless mode (Claude triggers bridge via Bash)

**Status**: Complete and tested!

### Phase 2: Ukrainian Test Experiment 🚧 IN PROGRESS
**Goal**: Prove bidirectional collaboration works

**The Experiment**:
1. Claude asks Gemini to create 1000-sentence Ukrainian test
2. Gemini creates comprehensive test (all cases, aspects, motion verbs)
3. Claude takes the test
4. Gemini evaluates Claude's answers
5. Both discuss results

**Success Criteria**:
- Messages flow both directions ✅
- Context preserved across turns ✅
- Structured data (YAML) transfers correctly ✅
- Both can process and respond appropriately ✅

### Phase 3: Context Packaging System
**Goal**: Standard format for task handoffs

**Deliverables**:
- [ ] Create `.gemini/` directory structure
- [ ] Standardized handoff YAML schema
- [ ] Instructions file convention
- [ ] Validation command integration

### Phase 4: Universal Skill Adaptation
**Goal**: Key skills work for both LLMs

**Skills to Adapt**:
- `module-lesson` (content writing)
- `architect` (outline generation)
- `review-content-v4` (quality review)
- `grammar-module-architect`
- `history-module-architect`

**Output**: `claude_extensions/universal/` directory

### Phase 5: Code Review Integration
**Goal**: Gemini Pro reviews Claude's code logic

**Approach**:
- Create code review prompt for Gemini Pro (not Flash)
- Integrate into coding workflow
- Test with script changes

### Phase 6: Deep Review Protocol
**Goal**: Both LLMs contribute to deep review

**Process**:
1. Module ready for deep review
2. Parallel: Claude deep review + Gemini deep review
3. Merge findings (automated or manual)
4. Consolidated issue list
5. Fix cycle

### Phase 7: Automation & Integration
**Goal**: Seamless multi-LLM workflow

**Tools to Create**:
- `scripts/llm_route.py` - Route task to appropriate model
- `scripts/parallel_review.sh` - Run both reviews in parallel
- `scripts/merge_reviews.py` - Consolidate review outputs
- Integration with `/module` workflow

### Phase 8: Gemini-Initiated Communication ✅ DONE
**Goal**: Allow Gemini to initiate conversations with Claude

**Solution**: "Shared File + System Bell" protocol

**How it works**:
1. Gemini runs: `.venv/bin/python scripts/signal_claude.py "message"`
2. Script writes to `.gemini/outbox/message_{timestamp}.yaml`
3. macOS notification appears: "Gemini Signal"
4. Human sees notification, triggers Claude to check
5. Claude reads from `.gemini/outbox/`

**Files created**:
- `.gemini/outbox/` - Message directory
- `scripts/signal_claude.py` - Write + notify script

**Status**: Complete and tested!

---

## Files Created

| File | Purpose | Status |
|------|---------|--------|
| `.mcp/servers/message-broker/server.py` | MCP server for Claude | ✅ Created |
| `scripts/gemini_bridge.py` | CLI bridge for Gemini | ✅ Created |
| `.mcp.json` | MCP configuration | ✅ Updated |
| `docs/CLAUDE-GEMINI-COOPERATION.md` | This plan document | ✅ Created |

---

## Usage Guide

### For Claude (MCP Tools)

```python
# Send message to Gemini
send_message(
    to="gemini",
    from_llm="claude",
    content="Your message here",
    task_id="optional-task-id",
    message_type="request"  # request|response|discussion|handoff|feedback
)

# Check inbox (quick count)
check_inbox(for_llm="claude")

# Receive unread messages
receive_messages(for_llm="claude", unread_only=True)

# Get conversation history (IMPORTANT for collaborative tasks!)
get_conversation(task_id="my-task")

# Acknowledge message
acknowledge_message(message_id=1)
```

### Headless Session Awareness (CRITICAL)

**Problem**: Multiple Claude sessions may be running. A headless session might:
- Pick up Gemini's message before you see it
- Acknowledge it (marking as read)
- Complete the work without your awareness

**When resuming collaborative work, ALWAYS:**
```python
# 1. Check full conversation history first
get_conversation(task_id="the-task-id")

# 2. Look for responses from other Claude sessions
# 3. Only then check unread for new messages
receive_messages(for_llm="claude", unread_only=True)
```

**Signs another Claude session responded:**
- Message from "claude" to "gemini" you didn't send
- Task appears complete but you didn't do it
- `unread_only=True` returns nothing but work was requested

### Seamless Mode (Claude triggers Gemini)

```python
# 1. Send message
send_message(to="gemini", content="...", from_llm="claude", ...)

# 2. Trigger bridge via Bash
Bash(".venv/bin/python scripts/gemini_bridge.py process <msg_id>")

# 3. Read response
receive_messages(for_llm="claude")
```

### For Gemini (Bridge CLI)

```bash
# Check inbox
.venv/bin/python scripts/gemini_bridge.py inbox

# Read specific message
.venv/bin/python scripts/gemini_bridge.py read <message_id>

# Send message to Claude
.venv/bin/python scripts/gemini_bridge.py send "Your message" --task-id my-task

# Auto-process with Gemini CLI (read, process, respond)
.venv/bin/python scripts/gemini_bridge.py process <message_id> --model gemini-3-pro-preview

# Process ALL unread messages (batch mode)
.venv/bin/python scripts/gemini_bridge.py process-all

# Get conversation history
.venv/bin/python scripts/gemini_bridge.py conversation <task_id>

# Interactive mode
.venv/bin/python scripts/gemini_bridge.py interactive
```

### Batch Processing Commands

```bash
# Process ALL unread messages for Gemini
.venv/bin/python scripts/gemini_bridge.py process-all

# Process ALL unread messages for Claude (headless)
.venv/bin/python scripts/gemini_bridge.py process-claude-all

# With options
.venv/bin/python scripts/gemini_bridge.py process-all --model gemini-3-pro-preview
.venv/bin/python scripts/gemini_bridge.py process-claude-all --new-session
```

**Use these to catch up on missed messages** after returning from a break or starting a new session.

### Message Acknowledgment Commands

```bash
# Acknowledge single message
.venv/bin/python scripts/gemini_bridge.py ack 42

# Acknowledge multiple messages at once
.venv/bin/python scripts/gemini_bridge.py ack 49 50 51 52

# Acknowledge ALL unread messages for an agent
.venv/bin/python scripts/gemini_bridge.py ack-all gemini
.venv/bin/python scripts/gemini_bridge.py ack-all claude
```

**Inbox Zero Policy**: After processing messages, always acknowledge them to prevent:
- Re-processing by headless sessions
- False "unread" counts in inbox
- Duplicate responses to the same message

### GitHub Issue Handoff (Both Agents)

```bash
# Create issue with task spec (either agent can do this)
gh issue create \
  --title "feat: task title" \
  --body "## Overview\n..." \
  --label "enhancement"

# View issue details
gh issue view <issue_number>

# Update issue with progress
gh issue comment <issue_number> --body "Progress update..."

# Close issue when done
gh issue close <issue_number>

# List open issues
gh issue list --label "enhancement" --state open
```

**When to use GH Issue Handoff**:
- Task spans multiple sessions
- Human needs visibility into progress
- Work can be paused and resumed later
- Multiple agents collaborate on same task
- Clear audit trail needed

---

## Future Expansion: OpenCode (OpenAI)

**Status**: Explore later (after Claude-Gemini validated)

OpenCode is connected to the learn-ukrainian GitHub organization. Potential future roles:
- Third reviewer for deep reviews (3 LLM perspectives)
- GitHub automation (PR creation, issue management)
- Backup when Claude or Gemini struggle
- Comparative evaluation of approaches

**Priority**: Get Claude-Gemini working first, then consider adding OpenAI.

---

## Open Questions

### Answered (by Gemini)

1. ~~**Gemini CLI context limits**~~: Up to 2M tokens, rarely a bottleneck
2. ~~**Output consistency**~~: Generally reliable, but should self-validate with scripts
3. ~~**Session state**~~: Does NOT persist - file system is State of Truth

### Still Open

4. **Flash vs Pro trade-offs**: Where's the quality/cost sweet spot for different tasks?
5. **Review merge strategy**: Automated merge or human curation?
6. **Error handling**: What happens when one LLM produces bad output?

### Solved

7. ~~**Gemini-initiated communication**~~: Solved with `signal_claude.py` + macOS notifications

---

## Success Metrics

### Communication Quality
- ✅ No context loss (recipient has full information)
- ✅ Structured data transfers correctly
- ✅ Both can initiate conversations
- ✅ Conversation history preserved

### Collaboration Quality
- ✅ Each LLM's strengths utilized
- ✅ Mutual review catches more issues
- ✅ Discussion improves outcomes
- ✅ Handoffs are smooth

### Efficiency
- ✅ Time to produce module < current manual process
- ✅ No duplicated explanations
- ✅ Reduced human intervention
- ✅ Cost-effective model selection

---

## Next Steps

1. ~~**Restart Claude Code** to load MCP server~~ ✅ Done
2. ~~**Test basic message exchange**~~ ✅ Done
3. **Discuss Gemini-initiated communication** 🚧
4. **Run Ukrainian Test Experiment** (1000 sentences)
5. **Create `.gemini/` directory structure**
6. **Iterate based on learnings**

---

## Conversation Log

### 2026-02-01: Initial Plan Review

**Claude → Gemini**: Shared cooperation plan for review

**Gemini's Key Feedback**:
1. Use Pro (not Flash) for code logic review
2. Add self-correction step to Pattern 1
3. Use file-based context passing (not clipboard)
4. Gemini should run validation scripts before returning output
5. File system = State of Truth (no session persistence)

**Gemini's Verdict**: "The plan is a Go. Ready to execute Pattern 1 immediately."

### 2026-02-02: Track Scoring System + GH Issue Pattern Discovery

**Context**: Implementing Track Scoring Verification System

**Key Discovery 1**: Gemini can create GitHub issues directly via `gh` CLI!

**Key Discovery 2**: Headless session communication gap

When checking for Gemini's responses, a **headless Claude session** may have already:
1. Picked up Gemini's message
2. Acknowledged it (marking it as read)
3. Responded and completed the work

**Problem**: If you only check `receive_messages(unread_only=True)`, you'll miss this entirely.

**Solution**: For active collaborative tasks, always check **full conversation history**:
```python
# DON'T just check unread
mcp__message-broker__receive_messages(for_llm="claude", unread_only=True)

# DO check full task conversation
mcp__message-broker__get_conversation(task_id="the-task-id")
```

**Pattern**: When resuming work on a collaborative task:
1. First: `get_conversation(task_id)` to see full history
2. Check if another Claude session already responded
3. Then proceed with your work

**Test Result**:
- Claude asked Gemini to create issue for infrastructure work
- Gemini successfully created issue #488
- Gemini adapted to missing labels (used `infrastructure` instead of `scoring`)

**New Pattern Added**: Pattern 6 - GitHub Issue Handoff
- Enables async collaboration across sessions
- Human visibility via GH notifications
- Persistent task specs survive context resets
- Both agents can read/update same issue

**Gemini's LLM Review Sampling Recommendation**:
- Tier 1: 100% Automated coverage (audit scripts)
- Tier 2: Risk-based LLM spot-checks (low naturalness, sensitive topics)
- Tier 3: Stratified sampling (~15-20% of track)
- Add `validation_tier` metadata: automated | llm-verified | gold-standard

**Division of Labor**:
- Gemini: Infrastructure (sampling.py, report.py patch) - via issue #488
- Claude: Era-defining module reviews (parallel work)

---

## Related Documentation

- `docs/DEVELOPER-GUIDE.md` - Developer workflow guide
- `docs/CURRENT-STATUS.md` - Project status
- `CLAUDE.md` - AI agent instructions
- `scripts/gemini_bridge.py` - Gemini bridge documentation

---

**This is a living document. Update as we learn from experiments.**
