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
11. **BROKEN TOOL AVOIDANCE**: Use `run_shell_command("rg ...")` instead of `search_file_content`.
12. **Typography**: ALWAYS use Ukrainian angular quotes `«...»`.

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
- **Use `process-claude` for seamless invocation** - Claude runs headlessly and responds
- **Always use task_id** - enables session tracking for multi-turn conversations
- **Check inbox at start of session** - Claude may have left messages
- **Sessions are per-task** - same task_id = same conversation context

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
