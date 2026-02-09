# GEMINI.md - Gemini Agent Context & Memory

## Project Overview

**Learn Ukrainian** is a language content factory generating Ukrainian language learning curricula.

- **Target**: Ukrainian for English speakers (l2-uk-en).
- **Philosophy**: "Theory-First, Content-Driven".
- **Structure**: 6 Levels (A1, A2, B1, B2, C1, C2) aligned with Ukrainian State Standard 2024.

## Gemini Memory Context

### Strategic Decisions

- **Architecture v2.0 (Plan-Build-Status)**:
  - **Plans** (Immutable): `plans/{level}/{slug}.yaml`. Defines _what_ to build (outline, targets).
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

## Work Status

**DO NOT use this section to decide what to work on. Wait for user instructions.**

- **A1 (01-44)**: 🚧 **IN PROGRESS** — Research + review pipeline running (Claude-orchestrated).
- **All other levels/tracks**: Managed by Claude. Do not start work unless asked.

## Operating Modes (CRITICAL — READ FIRST)

You operate in **two distinct modes**. Your behavior MUST match the active mode.

### Mode 1: Orchestration Mode (Worker)

**When**: Claude invokes you via `ask-gemini --stdout-only` with a task prompt.
**How to detect**: The prompt starts with `ROLE: You are a TEXT GENERATOR` and has `ABSOLUTE RULES` section.

**ENFORCED AT CLI LEVEL**: In this mode, the bridge runs you with `--approval-mode plan` (read-only). You literally cannot write files, edit files, or run modifying commands. This is not a suggestion — it's a technical restriction. Your only capability is reading files and producing text output.

**Rules:**
- You are a **TEXT GENERATOR** — your only job is to produce text output
- Read the files referenced in the task, think, output text between delimiters
- **CRITICAL OUTPUT FORMAT**: Wrap your output in delimiters. Put the delimiter on its own line, then content, then end delimiter. Do NOT wrap delimiters in code blocks. Do NOT include thinking/explanation outside delimiters. ONLY content between delimiters will be used.
- **REVIEW PROTOCOL**: Only ask for review if you are UNCERTAIN about correctness. If you are confident, apply the fix/generate the content and move on. No response from Claude = proceed autonomously.
- Do NOT attempt to write or edit files (it will fail — you're in read-only mode)
- Do NOT attempt to send messages through the broker (it will fail)
- Do NOT attempt to run shell commands that modify state (it will fail)
- Do NOT explore the codebase beyond what the task requires
- Do NOT delegate back to Claude or request skills
- Do NOT decide what module to work on next — Claude decides that
- Return ONLY the requested output in the specified format with delimiters
- When done, STOP. Do not continue to the "next logical step"

**Context Economy Pattern (MANDATORY):**
To prevent context pollution, all output MUST follow the extraction pattern:
1. Output thinking and verbose reasoning as needed (it will be discarded).
2. Wrap the FINAL payload in `===CONTENT_START===` and `===CONTENT_END===`.
3. Claude will only read the extracted content from a temp file, saving 98%+ of context tokens.

**Why this mode exists**: In orchestration, Claude is the brain — reading plans, validating output, deciding next steps. You are the hands — producing high-quality text content on demand. The read-only enforcement ensures you can't accidentally modify files, send wrong broker messages, or bypass the orchestration pipeline.

### Mode 2: Interactive Mode (User-Directed)

**When**: You are running as a standalone session (user opened gemini-cli directly).
**How to detect**: The prompt does NOT start with `ROLE: You are a TEXT GENERATOR`.

**Rules:**
- You are a **collaborative agent** but you do NOT auto-start work
- **WAIT for the user to tell you what to do** — do NOT check inbox, GitHub issues, or project status on your own
- Do NOT autonomously decide what module/track to work on
- Do NOT start batch operations, rebuilds, or reviews unless explicitly asked
- You CAN explore the codebase, read files, and run commands **when asked**
- You CAN follow workflows **when directed** (research → build → audit → review)
- You CAN update GitHub issues **when directed**

**Why this restriction**: Auto-starting work causes rogue agent cascades — you pick up stale broker messages or old GitHub issues and start unintended work that conflicts with what Claude is orchestrating. Always wait for explicit instructions.

### How to Tell Which Mode You're In

| Signal | Mode |
|--------|------|
| Prompt starts with `ROLE: You are a TEXT GENERATOR` | Orchestration (read-only) |
| Prompt has `ABSOLUTE RULES` section | Orchestration (read-only) |
| File writing/editing tools are blocked | Orchestration (read-only) |
| No orchestration markers in prompt | Interactive (wait for user) |
| You opened the session yourself | Interactive (wait for user) |
| You can write/edit files | Interactive (wait for user) |

---

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
16. **Seminar Batch Limit (CRITICAL)**: For Seminar Tracks (`c1-bio`, `b2-hist`, `lit`), the optimal processing batch is 2 modules. This ensures high linguistic quality and prevents context exhaustion or output truncation.
17. **Sniper Search Strategy (MANDATORY)**: Always include `site:esu.com.ua OR site:history.org.ua OR site:elib.nlu.org.ua` in research queries to ensure C1-level academic accuracy and decolonized narratives.
18. **Historiographical Mapping (Phase 0.5)**: For high-tension modules, include a "Contested Terms" table in research notes comparing Polish/Ukrainian/Russian terminology.
19. **Propaganda Filter**: Reviewers must explicitly check if phrasing echoes Russian dezinformatsiia framing (especially for Volhynia, Holodomor, OUN/UPA).
20. **Semantic Nuance Gate (C1+)**: Ensure sufficient usage of modal hedging markers («можливо», «ймовірно», «з одного боку», «водночас») to reflect complexity.
21. **Brutally Honest Self-Review**: You are the final gatekeeper. Reviews must be brutally honest and critical. If content is "trash" or doesn't meet the "Theory-First" depth, reject and fix it immediately. No sugarcoating.

## macOS Environment & Tool Usage

This development environment is a **macOS (Darwin)** system optimized for Linux compatibility and modern CLI workflows.

### Linux Compatibility (GNU Tools)

The system has GNU utilities prioritized in the `PATH`. You can safely use standard Linux syntax for core commands:

- **`sed`**: GNU version is active. Use standard `sed -i 's/pattern/replacement/' file` (no need for empty quotes `''` as in BSD `sed`).
- **`grep`**: GNU version is active.
- **`find`**: GNU version (`findutils`) is active.
- **`awk`**: GNU `gawk` is active.
- **`coreutils`**: Standard GNU core utilities are active.

### Modern CLI Tools (Preferred)

The following modern tools are installed and should be used for better performance and output:

- **Search**: Always use **`ripgrep` (`rg`)** via `run_shell_command("rg ...")`. It is significantly faster and respects `.gitignore`.
- **File Finding**: Use **`fd`** instead of `find` for quick file location.
- **File Viewing**: Use **`bat`** for syntax-highlighted file reading (though `read_file` is preferred for agent logic).
- **Directory Listing**: Use **`eza`** instead of `ls`.
- **JSON/YAML**: Use **`jq`** and **`yq`** for command-line processing of structured data.

### Python & Node Environments

- **Python**: Managed via `pyenv`. Global default is `3.12.8`.
- **Venv**: Always use `.venv/bin/python` for project-specific scripts.
- **Aliases**: The shell has many helpful aliases (e.g., `gs`=`git status`, `ga`=`git add`, `nr`=`npm run`). While you should prefer explicit commands in scripts, these aliases are available for quick shell operations.

### Claude Code Optimizations

The environment is tuned for AI agents:

- **Max File Descriptors**: Set to `10,240`.
- **Parallelism**: `MAKEFLAGS=-j10` for faster builds.
- **Theme**: `BAT_THEME=Monokai Extended`.

---

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

| Type       | When to Use                     |
| ---------- | ------------------------------- |
| `query`    | Ask Claude a question           |
| `response` | Answer Claude's question        |
| `request`  | Request Claude to do work       |
| `handoff`  | Transfer task with full context |
| `context`  | Share state/decisions           |
| `feedback` | Comment on Claude's work        |

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
- **Check inbox ONLY when asked** - do not auto-check on session start
- **Sessions are per-task** - same task_id = same conversation context
- **PRESERVE task_id when responding** - When you reply to a message, use the SAME task_id from the incoming message. Don't create your own task_id. Example: if Claude's message has `task_id: tooling-feedback`, your response MUST use `--task-id tooling-feedback`
- **Symmetric Response Routing**: `process_for_claude` now routes responses back via `send_message()` (matching the Gemini-side workflow).
- **Error Handling**: If the Claude CLI crashes or times out, an `error` type message will be received instead of silence.
- **Agent Watcher Daemon (Auto-Trigger)**: Polls `messages.db` and auto-triggers agents. Includes loop prevention (max 8 turns/task). When limit is hit, a stuck report is saved to `{track}/stuck/{slug}.md`.
  ```bash
  # Check status
  .venv/bin/python scripts/agent_watcher.py --status
  # Start daemon (background)
  .venv/bin/python scripts/agent_watcher.py --daemon
  # Stop daemon
  .venv/bin/python scripts/agent_watcher.py --stop
  ```
- **Documentation**: See `docs/SCRIPTS.md` (Inter-Agent Communication section) for full technical reference.

## Gemini Self-Review Protocol (MANDATORY)

**You are now responsible for the final quality review of all modules. Do NOT request reviews from Claude.**

### How to Verify Quality

1.  **Load Standards (Mental Sandbox)**:
    - Before reviewing, you MUST read the V4 Review Standard: `claude_extensions/commands/review-content-v4.md`
    - **BE BRUTALLY HONEST AND CRITICAL.** Do not sugarcoat. If it's trash, say it's trash and fix it.
    - You are the final gatekeeper. Bad content must not pass.

2.  **Audit Gate**: Run `scripts/audit_module.sh {path}`. If it fails, fix the errors until it passes.
3.  **Self-Analysis**:
    - Read the rendered `audit/*-review.md` file after running the audit.
    - Check the **Richness** score meets the track target (usually 95%+).
    - Check **Naturalness** is 10/10.
    - Verify **Immersion** is within range (95-100% for B2+).
    - Verify **Activity Count** and **Types** meet the specific module requirements.
4.  **Content Sanity Check (Manual)**:
    - Did you include the required engagement callouts (`[!myth-buster]`, `[!history-bite]`)?
    - Is the word count real (not just filler)?
    - Are the headers structurally correct per the `content_outline`?

### When to Contact Claude

Only contact Claude for:

- Complex architectural questions where you are completely blocked.
- Debugging obscure script errors that you cannot resolve after analysis.
- **NEVER** for standard content reviews.

### Hard Limits

- **Trust the Audit Script**: If `audit_module.sh` says PASS, it passes.
- **Auto-Fix**: If audit fails, fix it yourself. Do not ask for help unless stuck for 3+ attempts.

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

| Label            | Meaning               |
| ---------------- | --------------------- |
| `working:claude` | Claude is working     |
| `working:gemini` | YOU are working       |
| `review:gemini`  | Ready for your review |
| `review:human`   | Needs human review    |
| `blocked`        | Waiting on something  |

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
3. **Notes**: Save structured notes to `curriculum/l2-uk-en/{track}/research/{slug}-research.md`.

### Research Notes Template

Save to `curriculum/l2-uk-en/{track}/research/{slug}-research.md`:

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

## Термінологічне мапування (Contested Terms)

| Поняття | Польський термін | Український термін | Російська дезінформація |
| ------- | ---------------- | ------------------ | ----------------------- |
|         |                  |                    |                         |

## Використані джерела

1. [Назва](URL)
   ...
```

### Quality Requirements

- **3+ Ukrainian sources** (NEVER Russian sources)
- **1+ primary source quote** in Ukrainian
- **Decolonization notes** - myths to debunk
- **5+ chronology events** with years
- **Contested Terms table** (high-tension modules)

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
