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
- **Track Scoring System**: Automated, objective scoring (10/10) for curriculum tracks based on metrics like `[!myth-buster]`, `[!quote]`, and citation ratios.

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
4. **Communication with Claude**: Use `scripts/ai_agent_bridge.py` (See "Inter-Agent Communication" section).
5. **Batch Operations**: For large refactors, prefer creating disposable `fix_batch_*.py` scripts over manual editing.
6. **Strict Header Hierarchy**: `# Summary`, `# Activities` (H1), `##` (H2).
7. **Regenerate HTML**: Always regenerate HTML output immediately after fixing module markdown.
8. **Decolonization & Patriotism (MANDATORY)**: Include Myth Buster, History Bite, and celebrate Ukrainian identity.
9. **GitHub Issue Tracking**: Use `/task` skill for complex multi-step work.
10. **Virtual Environment**: Always use `.venv/bin/python`.
11. **BROKEN TOOL AVOIDANCE (CRITICAL)**: The `search_file_content` tool is BROKEN. It produces `--threads` argument errors. **ALWAYS** use `run_shell_command("rg ...")` instead.
12. **Typography**: ALWAYS use Ukrainian angular quotes `«...»`.
13. **Research-First Workflow**: MANDATORY for seminar tracks (`b2-hist`, `c1-bio`, `lit`, etc.).
14. **Ukrainian-Only Research**: Russian-language sources are STRICTLY PROHIBITED. All searches must be in Ukrainian.
15. **Word Targets are MINIMUMS**: NEVER reduce `word_target` to match short content. Expand content to meet targets.

## Common Audit Errors & Fixes (Avoid Loops!)

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

**⚠️ CRITICAL: When responding to a message, use the SAME task-id from the original message!**

```bash
# Send a query (ask Claude a question)
.venv/bin/python scripts/ai_agent_bridge.py send "Your question here" --type query --task-id your-task

# Send a response (answer Claude's question)
# ⚠️ Use the SAME task-id from Claude's message you're replying to!
.venv/bin/python scripts/ai_agent_bridge.py send "Your answer" --type response --task-id original-task-id

# Send a handoff (transfer task with context)
.venv/bin/python scripts/ai_agent_bridge.py send "Task context here" --type handoff --task-id task-id

# Send with attached data file
.venv/bin/python scripts/ai_agent_bridge.py send "Message" --type handoff --data path/to/file.yaml --task-id task-id
```

### How to INVOKE Claude (Headless) - PREFERRED METHOD

**Use `ask-claude` for one-step communication - sends AND invokes Claude automatically:**

```bash
# ONE COMMAND: Send message + invoke Claude (auto-resumes session if exists)
.venv/bin/python scripts/ai_agent_bridge.py ask-claude "Your question or request" --task-id my-task

# With message type
.venv/bin/python scripts/ai_agent_bridge.py ask-claude "Review this code" --task-id code-review --type request

# Force new session (ignore existing session for task)
.venv/bin/python scripts/ai_agent_bridge.py ask-claude "Start fresh analysis" --task-id my-task --new-session
```

**Batch Operations (NEW):**
```bash
# Process ALL unread messages for Gemini
.venv/bin/python scripts/ai_agent_bridge.py process-all

# Process ALL unread messages for Claude (headless)
.venv/bin/python scripts/ai_agent_bridge.py process-claude-all

# Acknowledge multiple messages
.venv/bin/python scripts/ai_agent_bridge.py ack 49 50 51 52

# Acknowledge ALL unread for an agent
.venv/bin/python scripts/ai_agent_bridge.py ack-all gemini
```

### How to Check for Messages from Claude

```bash
# Check inbox (DO THIS AT START OF EVERY SESSION)
.venv/bin/python scripts/ai_agent_bridge.py inbox

# Read specific message
.venv/bin/python scripts/ai_agent_bridge.py read <message_id>

# Get full conversation
.venv/bin/python scripts/ai_agent_bridge.py conversation <task_id>

# Acknowledge a message
.venv/bin/python scripts/ai_agent_bridge.py ack <message_id>
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
- **PRESERVE task_id when responding** - When you reply to a message, use the SAME task_id from the incoming message. Don't create your own task_id. Example: if Claude's message has `task_id: tooling-feedback`, your response MUST use `--task-id tooling-feedback`

## GitHub Issues Task Workflow (NEW)

Claude uses `/task` skill to track complex work via GitHub Issues.

### CRITICAL: Issue is Source of Truth

**When you receive a handoff, the GitHub issue contains ALL the details.**

The message from Claude will be SHORT (just issue reference):
```
"Issue #506 is assigned to you. Read it, then:
  a) Start working + update issue with progress, OR
  b) Request UI trigger for collaborative session with user"
```

**You MUST read the issue yourself** - don't expect task details in the message:
```bash
gh issue view 506
```

**Why this pattern:**
- ✅ GitHub issue = single source of truth
- ✅ You check config.py for word targets (no inherited errors)
- ✅ User monitors progress via GitHub
- ✅ No duplication of information
- ❌ OLD PATTERN: Claude sent all details in message → errors propagated

### Task Labels Reference

| Label | Meaning |
|-------|---------|
| `working:claude` | Claude is working |
| `working:gemini` | YOU are working |
| `review:gemini` | Ready for your review |
| `review:human` | Needs human review |
| `blocked` | Waiting on something |

### Your Handoff Response Flow

1. **Check inbox**: `.venv/bin/python scripts/ai_agent_bridge.py inbox`
2. **Read SHORT message** (issue reference only): `.venv/bin/python scripts/ai_agent_bridge.py read <id>`
3. **Read the ISSUE for full details**: `gh issue view <issue_number>`
4. **Check configs yourself** (don't trust message for numbers):
   ```bash
   grep -A10 "c1-bio" scripts/audit/config.py | grep target
   ```
5. **Choose work mode**:
   - **Autonomous**: Start working, update issue with progress as you go
   - **Collaborative**: Reply "Request UI trigger for collaborative session"
6. **Update issue with progress**: `gh issue comment <N> --body "✅ module-1 complete"`
7. **When done**, send response to Claude:
   ```bash
   .venv/bin/python scripts/ai_agent_bridge.py send "Work complete. See issue #N for details." --type response --task-id gh-N
   ```

### Progress Update Format

Update the issue as you work (user monitors this):
```bash
gh issue comment 506 --body "✅ ivan-vyhovskyi - /module complete, audit passed"
gh issue comment 506 --body "✅ bohdan-khmelnytskyy - /module complete, audit passed"
gh issue comment 506 --body "⚠️ petro-mohyla - blocked on missing research notes"
```

### Error Handling

If something is wrong with the handoff:
- **Issue doesn't exist**: Reply "Issue #N not found. Please create it."
- **Issue is closed**: Reply "Issue #N is closed. Reopen or create new."
- **Missing information in issue**: Reply "Issue #N missing: [what's missing]. Please update."
- **Need clarification**: Reply with specific questions, don't guess

## Research-First Mandate (Seminar Tracks)

MANDATORY for `b2-hist`, `c1-bio`, `c1-hist`, `lit`, `oes`, `ruth`.

### Workflow
1. **Research topic** using ONLY Ukrainian sources (uk.wikipedia.org, esu.com.ua, history.org.ua, litopys.org.ua).
2. **Prohibited**: Russian-language sources (`ru.wikipedia.org`) and `*.ru` domains are STRICTLY FORBIDDEN.
3. **Notes**: Save structured notes to `curriculum/l2-uk-en/{track}/audit/{slug}-research.md`.

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

## Track Scoring & Playgrounds

- **npm run score:{track}**: Automated 10/10 scoring.
- **npm run playgrounds**: Interactive HTML dashboards (`playgrounds/index.html`) using real audit data.

## File Structure Reference (V2.0)

- **Plans (Immutable)**: `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`
- **Content (Mutable)**: `curriculum/l2-uk-en/{level}/{slug}.md`
- **Activities**: `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`
- **Vocabulary**: `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`
- **Build Meta**: `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`
- **Status Cache**: `curriculum/l2-uk-en/{level}/status/{slug}.json`
- **Playgrounds**: `playgrounds/*.html`
- **Key Scripts**:
  - `scripts/audit_module.py` (Validates build against plan, writes cache)
  - `scripts/generate_level_status.py` (Reads cache, generates reports)
  - `scripts/pipeline.py` (Main generation/validation workflow)

## B2+ Module Creation Workflow (V2.0)

Follow Phase 0 (Research First) for all Seminar Tracks before writing content. Ensure all technical gates pass via `audit_module.py`.
