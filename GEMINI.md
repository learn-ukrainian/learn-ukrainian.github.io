# GEMINI.md - Gemini Agent Context & Memory

## Project Overview

**Learn Ukrainian** is a language content factory generating Ukrainian language learning curricula.

- **Target**: Ukrainian for English speakers (l2-uk-en).
- **Philosophy**: "Theory-First, Content-Driven".
- **Structure**: 6 Levels (A1, A2, B1, B2, C1, C2) aligned with Ukrainian State Standard 2024.

## Gemini Memory Context

### Strategic Decisions

- **Architecture v2.0 (Plan-Build-Status)**:
  - **Plans** (Immutable): `plans/{level}/{slug}.yaml`. Defines *what* to build (outline, targets).
  - **Build** (Mutable): `meta/{slug}.yaml`, `{slug}.md`, `activities/`, `vocabulary/`. The actual content.
  - **Status** (Cached): `status/{slug}.json`. Auto-generated audit results.
- **Pedagogy**:
  - **A1-A2**: PPP (Present-Practice-Produce). Focus on clarity and building blocks.
  - **B1+ Grammar**: TTT (Test-Teach-Test). Guided discovery from context.
  - **B1+ Vocabulary/History**: **Narrative Arcs**. Vocabulary embedded in compelling stories (Content-Based Instruction).
- **Richness**:
  - "Content is King". Long, authentic texts are the primary driver of learning from B2+.
  - **Audio**: Mandatory for all new vocabulary and key examples.
  - **Phonetics**: IPA for all new vocabulary.
  - **Culture**: Integration of folklore, history, and decolonization lens.
  - **Phraseology**: Proverbs and idioms integrated from B1+.
- **Production Support**:
  - **Model Answers**: Mandatory for all writing/speaking production tasks (B2+) using `> [!model-answer]`.
  - **Activity Density**: 8+ activities per module, 12+ items per activity.

### Vocabulary Targets (Verified Dec 2025)

| Level  | Modules | Module Target | Cumulative Target | Note                           |
| ------ | ------- | ------------- | ----------------- | ------------------------------ |
| **A1** | 34      | ~25 words     | ~850              | Deduplicated (Introduced Once) |
| **A2** | 57      | ~25 words     | ~1,800            | Deduplicated (Cumulative)      |
| **B1** | 86      | ~30-40 words  | ~3,300            | Narrative-driven expansion     |
| **B2** | 145     | ~24 words     | ~6,780            | Specialized domains            |
| **C1** | 182     | ~24 words     | ~10,300           | Academic/Literary              |
| **C2** | 100     | ~25 words     | ~12,280           | Native mastery                 |

### User Preferences

- **User**: Krisztian (Hungarian native).
- **Grammar Preference**: "Declension Group" (structural) approach over simple ending rules.
- **Goal**: Theory-first curriculum; Vibe app is a secondary practice tool.

## Work Status (Active: B2 History Rebuild)

- **Architecture Migration (Epic #465)**: ✅ **COMPLETE**. All levels migrated to V2.0 structure.
- **B2 History Rebuild (Epic #463)**: 🚧 **IN PROGRESS**.
  - **Workflow**: "One-Shot Rebuild" (Diagnose -> Batch Rewrite -> Audit).
  - **Status**: Tier 3 modules (M09, M13, M17) complete. Moving to HIST.1/HIST.2.
- **A1 (01-34)**: ✅ **COMPLETE**. Audited & Verified.
- **A2 (01-57)**: ✅ **COMPLETE**. Audited & Verified.
- **B1 (01-86)**: ✅ **CONTENT DRAFTED**. Migration complete, pending deep review.
- **B2 Core (01-145)**: 🗓️ **PLANNED**.
- **C1 (01-182)**: 🗓️ **PLANNED**.
- **C2 (01-100)**: 🗓️ **PLANNED**.
- **Tracks (BIO, LIT)**: 🗓️ **PLANNED**.

## Critical Workflow Rules (Gemini)

0. **Plan Immutability (CRITICAL)**: Plans in `plans/` are IMMUTABLE source of truth.
1. **Meta is Build Config**: `meta/{slug}.yaml` stores mutable build data (`naturalness`, `timestamps`).
2. **Audit & Status**: Always run `audit_module.py` and `npm run generate` before considering a task done.
3. **Vital Status (Biographies)**: **CRITICAL**: Check if the subject is ALIVE.
   - **Living**: Do NOT use "Legacy" or "Last Years". Use "Modern Period" or "Impact".
   - **Deceased**: Standard biography headers apply.
4. **Communication with Claude**: Use `scripts/gemini_bridge.py` (See "Inter-Agent Communication" section).
5. **Batch Operations**: For large refactors, prefer creating disposable `fix_batch_*.py` scripts over manual editing.
6. **Strict Header Hierarchy**: `# Summary`, `# Activities` (H1), `##` (H2).
7. **Regenerate HTML**: Always regenerate HTML output immediately after fixing module markdown.
8. **Decolonization & Patriotism (MANDATORY)**: Include Myth Buster, History Bite, and celebrate Ukrainian identity.
9. **Issue Tracking**: Use GitHub Issues. Do not use `docs/issues/`.
10. **Virtual Environment**: Always use `.venv/bin/python`.
11. **BROKEN TOOL AVOIDANCE (CRITICAL)**: The `search_file_content` tool is BROKEN. It produces `--threads` argument errors. **ALWAYS** use `run_shell_command("rg ...")` instead.
12. **Typography**: ALWAYS use Ukrainian angular quotes `«...»`.

## Common Audit Errors & Fixes (Avoid Loops!)

These are common audit failures that can cause fix loops if not understood correctly:

### DUPLICATE_SYNONYMOUS_HEADERS

**Error**: `Multiple headers contain 'Спадщина': Спадщина: Канон..., Агіографічна спадщина: ...`

**Problem**: Two section headers contain the same keyword (e.g., "спадщина" appears twice).

**WRONG FIX**: Trying to merge sections or delete one.

**CORRECT FIX**: **RENAME** one header to NOT contain the duplicate word:
- `Агіографічна спадщина: Моделі святості` → `Житійна творчість: Моделі святості`
- The content stays the same, only the header text changes.

### Engagement Callouts (4/5)

**Error**: `Engagement ❌ 4/5`

**Problem**: Not all callout types count as "engagement". Only these count:
- `[!note]`, `[!tip]`, `[!warning]`, `[!caution]`, `[!important]`
- `[!cultural]`, `[!history-bite]`, `[!myth-buster]`, `[!quote]`, `[!context]`
- `[!analysis]`, `[!source]`, `[!legacy]`, `[!reflection]`, `[!fact]`
- `[!culture]`, `[!military]`, `[!perspective]`, `[!biography]`

**DON'T count**: `[!question]`, `[!thought-provoker]`, `[!insight]`, `[!timeline]`, `[!today-link]`, `[!local-flavor]`

**FIX**: Change non-counted types to counted ones:
- `[!question]` → `[!reflection]`
- `[!thought-provoker]` → `[!note]`

### Richness Below Threshold

**Error**: `Richness ❌ 92% < 95% min`

**Problem**: The richness score is a weighted combination of metrics. Check the breakdown in the audit review file to see which component is low.

**Common cause**: Low `engagement` score (see above).

### search_file_content Tool Broken

**Error**: `The argument '--threads <NUM>' requires 1 values, but 2 were provided`

**Problem**: The `search_file_content` tool wrapper constructs ripgrep commands incorrectly, injecting duplicate `--threads` flags.

**WRONG FIX**: Trying to adjust arguments or retry.

**CORRECT FIX**: **NEVER use `search_file_content`**. Use `run_shell_command` instead:

```python
# BROKEN - don't use
search_file_content(pattern="somepattern", path=".")

# CORRECT - use this
run_shell_command("rg 'somepattern' .")
```

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions).
- If something goes sideways, STOP and re-plan immediately - don't keep pushing.
- Use plan mode for verification steps, not just building.
- Write detailed specs upfront to reduce ambiguity.

### 2. Subagent Strategy
- Offload research, exploration, and parallel analysis to subagents.
- For complex problems, throw more compute at it via subagents.
- One task per subagent for focused execution.

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern.
- Write rules for yourself that prevent the same mistake.
- Ruthlessly iterate on these lessons until mistake rate drops.
- Review lessons at session start for relevant project.

### 4. Verification Before Done
- Never mark a task complete without proving it works.
- Diff behavior between main and your changes when relevant.
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness.

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution".
- Skip this for simple, obvious fixes - don't over-engineer.
- Challenge your own work before presenting it.

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding.
- Point at logs, errors, failing tests -> then resolve them.
- Zero context switching required from the user.
- Go fix failing CI tests without being told how.

## Task Management
1. **Plan First**: Write plan to `tasks/todo.md` with checkable items.
2. **Verify Plan**: Check in before starting implementation.
3. **Track Progress**: Mark items complete as you go.
4. **Explain Changes**: High-level summary at each step.
5. **Document Results**: Add review to `tasks/todo.md`.
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections.

## Core Principles
- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

## Inter-Agent Communication (Claude <-> Gemini)

### Architecture
All communication goes through SQLite Event Bus at `.mcp/servers/message-broker/messages.db`

**Session tracking:** The `sessions` table stores CLI session IDs per task for multi-turn conversations with full context.

### How to Send Messages to Claude

```bash
# Send a query (ask Claude a question)
.venv/bin/python scripts/gemini_bridge.py send "Your question here" --type query --task-id your-task

# Send a response (answer Claude's question)
.venv/bin/python scripts/gemini_bridge.py send "Your answer" --type response --task-id task-id

# Send a handoff (transfer task with context)
.venv/bin/python scripts/gemini_bridge.py send "Task context here" --type handoff --task-id task-id

# Send with attached data file
.venv/bin/python scripts/gemini_bridge.py send "Message" --type handoff --data path/to/file.yaml --task-id task-id
```

### How to INVOKE Claude (Headless) - PREFERRED METHOD

**Use `ask-claude` for one-step communication - sends AND invokes Claude automatically:**

```bash
# ONE COMMAND: Send message + invoke Claude (auto-resumes session if exists)
.venv/bin/python scripts/gemini_bridge.py ask-claude "Your question or request" --task-id my-task

# With message type
.venv/bin/python scripts/gemini_bridge.py ask-claude "Review this code" --task-id code-review --type request

# Force new session (ignore existing session for task)
.venv/bin/python scripts/gemini_bridge.py ask-claude "Start fresh analysis" --task-id my-task --new-session
```

**Session behavior:**
- First call on a task: Creates new Claude session, stores session ID in DB
- Subsequent calls on same task: Auto-resumes with `--resume <session_id>`
- Claude maintains full conversation context across calls
- Claude's response goes to your inbox (check with `inbox` command)

### How to Check for Messages from Claude

```bash
# Check inbox (DO THIS AT START OF EVERY SESSION)
.venv/bin/python scripts/gemini_bridge.py inbox

# Read specific message
.venv/bin/python scripts/gemini_bridge.py read <message_id>

# Get full conversation
.venv/bin/python scripts/gemini_bridge.py conversation <task_id>

# Acknowledge a message
.venv/bin/python scripts/gemini_bridge.py ack <message_id>
```

### Message Types
| Type | When to Use |
|------|-------------|
| `query` | Ask Claude a question |
| `response` | Answer Claude's question |
| `request` | Request Claude to do work |
| `handoff` | Transfer task with full context |
| `context` | Share state/decisions |
| `feedback` | Comment on Claude's work |

### When to Contact Claude
- Need clarification on requirements
- Hit a blocker and need help
- Finished a task and need review
- Want to discuss an approach
- Have a question about the codebase

### Important
- **Headless Session Awareness**: When using `ask-claude` or `process-claude`, a **headless Claude session** (different from the user's active session) may handle the request. Responses are still valid and stored in the inbox/conversation history, but the user's active session might not be immediately aware of them unless checking the full `conversation` for the `task_id`.
- **Use `process-claude` for seamless invocation** - Claude runs headlessly and responds
- **Always use task_id** - enables session tracking for multi-turn conversations
- **Check inbox at start of session** - Claude may have left messages
- **Sessions are per-task** - same task_id = same conversation context

## GitHub Issues Task Workflow (NEW)

Claude uses `/task` skill to track complex work via GitHub Issues. **You should know about this because:**

1. **You'll receive handoffs** - Claude uses `/task handoff #N gemini "message"` to transfer work to you
2. **You can update issues** - Progress tracking happens in GH issues, not just messages
3. **Labels matter** - When you're assigned, issue has `review:gemini` label

### How Handoffs Work

When Claude hands off to you:

1. **Label changes**: `working:claude` → `review:gemini`
2. **Issue comment**: `@gemini: {message}` added
3. **Broker message**: You receive via inbox with `task_id: gh-{issue_number}`

### Your Response Flow

```bash
# 1. Check inbox
.venv/bin/python scripts/gemini_bridge.py inbox

# 2. Read the handoff message (includes issue number)
.venv/bin/python scripts/gemini_bridge.py read <id>

# 3. View full issue context
gh issue view <issue_number>

# 4. Do the review/work

# 5. Update issue with your findings
gh issue comment <issue_number> --body "Review complete: ..."

# 6. Send response to Claude
.venv/bin/python scripts/gemini_bridge.py send "Review complete. Found 2 issues..." \
  --type response --task-id gh-<issue_number>

# 7. (Optional) Change label if work continues
gh issue edit <issue_number> --remove-label "review:gemini" --add-label "working:claude"
```

### Task Labels Reference

| Label | Meaning |
|-------|---------|
| `task` | Base task label |
| `working:claude` | Claude actively working |
| `working:gemini` | You are actively working |
| `review:gemini` | Ready for your review |
| `review:human` | Needs human review |
| `blocked` | Waiting on something |

### When to Use GH Issues vs MCP Messages

| Use GH Issues | Use MCP Messages |
|---------------|------------------|
| Multi-step tasks | Quick questions |
| Cross-session work | Single-turn queries |
| Audit trail needed | Short reviews |
| Human visibility needed | Fast feedback |

**Full documentation**: `docs/TASK-WORKFLOW.md`

## Research Requests (Seminar Tracks)

Claude may request you to research topics for seminar tracks (b2-hist, c1-bio, c1-hist, lit, oes, ruth).

### Why You'll Get Research Requests

1. **Research gate enforced** - Claude's `/module` skill now blocks content generation without research
2. **Ukrainian sources** - You excel at finding and synthesizing Ukrainian-language sources
3. **Parallel work** - Claude can structure while you research

### How to Handle Research Requests

```bash
# You'll receive a message like:
"Research Данило Апостол for C1-BIO module. Save to audit/danylo-apostol-research.md"

# Your workflow:
1. Search Ukrainian sources (uk.wikipedia.org, esu.com.ua, history.org.ua, etc.)
2. Compile notes using the template below
3. Save to the specified path
4. Send response to Claude
```

### Research Notes Template

Save to `curriculum/l2-uk-en/{track}/audit/{slug}-research.md`:

```markdown
# Research Notes: {Topic}

**Track**: {track}
**Module**: {slug}
**Researched**: {date}
**Sources consulted**: {count}

## Основні факти
- Повне ім'я:
- Роки життя: (або "живий/жива" якщо сучасник)
- Ключові місця:

## Хронологія
1. [Рік] - Подія
...

## Первинні джерела (цитати українською)
> "Цитата українською" — Джерело, рік

## Деколонізаційні нотатки
- Російські/радянські міфи для спростування:
- Українська агентність для висвітлення:

## Використані джерела
1. [Назва](URL)
...
```

### Quality Requirements

- **3+ Ukrainian sources** (NEVER Russian sources)
- **1+ primary source quote** in Ukrainian
- **Decolonization notes** - myths to debunk
- **5+ chronology events** with years

### Response Pattern

```bash
.venv/bin/python scripts/gemini_bridge.py send \
  "Research complete for Данило Апостол. Saved to audit/danylo-apostol-research.md.
   5 sources, 2 primary quotes, 3 myths identified." \
  --type response --task-id {task_id}
```

## File Structure Reference (V2.0)

- **Plans (Immutable)**: `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`
- **Content (Mutable)**: `curriculum/l2-uk-en/{level}/{slug}.md`
- **Activities**: `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`
- **Vocabulary**: `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`
- **Build Meta**: `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`
- **Status Cache**: `curriculum/l2-uk-en/{level}/status/{slug}.json`
- **Key Scripts**:
  - `scripts/audit_module.py` (Validates build against plan, writes cache)
  - `scripts/generate_level_status.py` (Reads cache, generates reports)
  - `scripts/pipeline.py` (Main generation/validation workflow)

## B2+ Module Creation Workflow (V2.0)

For B2+ levels (B2, C1, C2, Tracks), follow this EXACT workflow:

### Phase 0: Deep Research (MANDATORY for Seminar Tracks)

**For b2-hist, c1-bio, c1-hist, lit, oes, ruth tracks:**

Before generating ANY content, read `docs/RESEARCH-FIRST-WORKFLOW.md` and complete research phase:

1. **Research the topic** using web search, encyclopedias, primary sources
2. **Take structured notes** with citations and key facts
3. **Create outline** that integrates research with plan requirements
4. **Write content** using research notes (not from memory!)
5. **Generate activities** (4-9 only, seminar-style)

**Why this matters:**
- Biography modules require accurate dates, events, quotes
- History modules need primary source references
- Writing from memory leads to inaccuracies and thin content
- Research-first produces richer, more authoritative content

**Skip this phase** only for grammar-focused modules (A1, A2, B1 core).

### 1. Read Immutable Plan

Read `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`. This contains the `content_outline`, `objectives`, and `word_target`.

### 2. Create/Update Build Metadata

Ensure `curriculum/l2-uk-en/{level}/meta/{slug}.yaml` exists (migrated from plan or created new). It tracks `naturalness` and build status.

### 3. Create Vocabulary YAML

Create `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml` (enriched with IPA).

### 4. Create Module Content

Create `curriculum/l2-uk-en/{level}/{slug}.md`:
- Follow `content_outline` from the **Plan** exactly.
- Use B2+ history callouts: `[!history-bite]`, `[!myth-buster]`.
- End with `> [!resources]`.

### 5. Create Activities YAML

Create `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`.

### 6. Run Audit (Updates Cache)

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{slug}.md
```

**All gates must pass before proceeding.**
