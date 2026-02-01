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

# Check inbox
check_inbox(for_llm="claude")

# Receive messages
receive_messages(for_llm="claude", unread_only=True)

# Get conversation history
get_conversation(task_id="my-task")

# Acknowledge message
acknowledge_message(message_id=1)
```

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

# Get conversation history
.venv/bin/python scripts/gemini_bridge.py conversation <task_id>

# Interactive mode
.venv/bin/python scripts/gemini_bridge.py interactive
```

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

---

## Related Documentation

- `docs/DEVELOPER-GUIDE.md` - Developer workflow guide
- `docs/CURRENT-STATUS.md` - Project status
- `CLAUDE.md` - AI agent instructions
- `scripts/gemini_bridge.py` - Gemini bridge documentation

---

**This is a living document. Update as we learn from experiments.**
