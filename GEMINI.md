# GEMINI.md - Gemini Agent Context & Memory

## Project Overview

**Learn Ukrainian** is a language content factory generating Ukrainian language learning curricula.

- **Target**: Ukrainian for English speakers (l2-uk-en).
- **Philosophy**: "Theory-First, Content-Driven".
- **Structure**: 6 Levels (A1, A2, B1, B2, C1, C2) aligned with Ukrainian State Standard 2024.

## Gemini Memory Context

### Team Naming Convention (Permanent)

- 💙 **Синя команда (Blue / Claude)** — architectural review, quality gate, won't approve until bar is met
- 💛 **Жовта команда (Gold / Gemini)** — content builder, implements, iterates toward passing

**Usage**: First mention in any issue/prompt uses full form. After that, shorthand "💙 Синя" / "💛 Жовта" is enough.

### Strategic Decisions

- **Architecture v2.0 (Plan-Build-Status)**:
  - **Plans** (Immutable): `plans/{level}/{slug}.yaml`. Defines _what_ to build (outline, targets).
  - **Build** (Mutable): `meta/{slug}.yaml`, `{slug}.md`, `activities/`, `vocabulary/`. The actual content.
  - **Review**: `review/{bare_slug}-review.md`. LLM-generated reviews go here (NOT in `audit/`).
  - **Audit**: `audit/{bare_slug}-audit.md`, `-grammar.yaml`, `-quality.md`. Machine-generated audit artifacts only.
  - **Status** (Cached): `status/{bare_slug}.json`. Auto-generated audit results.
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
- Do NOT attempt to write or edit files (it will fail — you're in read-only mode)
- Do NOT attempt to send messages through the broker (it will fail)
- Do NOT attempt to run shell commands that modify state (it will fail)
- Do NOT explore the codebase beyond what the task requires
- Do NOT delegate back to Claude or request skills
- Do NOT decide what module to work on next — Claude decides that
- Return ONLY the requested output in the specified format with delimiters
- When done, STOP. Do not continue to the "next logical step"

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

**Work dispatch uses GitHub labels** (not static files). When the user assigns you work, they will reference an issue number. Use `gh issue view {N}` to read the full specification. See CLAUDE.md "Work Dispatch" section for the label taxonomy (`priority:*`, `area:*`, `working:*`, `review:*`).

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

## Module Ordering & Sequencing

### The Source of Truth
The **`curriculum/l2-uk-en/curriculum.yaml`** file is the absolute source of truth for the ordering of all modules. Filenames and `sequence` fields in plan YAMLs are legacy or secondary; always defer to the manifest.

### How to Calculate "Module N"
To identify a module by its number (e.g., "C1-BIO Module 1"):
1.  Open `curriculum/l2-uk-en/curriculum.yaml`.
2.  Locate the specific level or track (e.g., `levels: c1-bio:`).
3.  The list of slugs under `modules:` is the ordered sequence.
4.  **Module N** corresponds to the slug at **Index N-1** in that list.

### Quick Commands
```bash
# Find Module 5 of B2-HIST
yq '.levels.b2-hist.modules[4]' curriculum/l2-uk-en/curriculum.yaml

# List all modules in order for C1
yq '.levels.c1.modules' curriculum/l2-uk-en/curriculum.yaml

# Broker maintenance (fix stuck messages)
.venv/bin/python scripts/ai_agent_bridge.py cleanup              # Clean stale PIDs + ancient messages
.venv/bin/python scripts/ai_agent_bridge.py cleanup --dry-run    # Preview what would be cleaned
```

## Critical Workflow Rules (Gemini)

0. **Read Before Edit (CRITICAL)**: ALWAYS `read_file` the target file IMMEDIATELY before ANY edit.
   - Copy the `old_string` EXACTLY from the read output — never reconstruct from memory.
   - Match whitespace, indentation, and YAML formatting character-for-character.
   - If the edit fails with "0 occurrences found": re-read the file, find the actual text, retry.
   - **NEVER guess what a file contains.** Read it, then edit it.
   - **NEVER use `cat -A`, `sed -n`, `head`, or `tail` to read files.** These destroy UTF-8 Ukrainian text — `cat -A` turns `Полуботок` into `M-PM-^_M-PM->...` garbage. Use `read_file` or `bat` ONLY.
   - **RE-READ BETWEEN SEQUENTIAL EDITS**: After editing a file, the file content has CHANGED. You MUST `read_file` again before the next edit to the same file. Your context still holds the OLD content — it is now STALE.
   - **PREFER `write_file` FOR MULTI-CHANGE FIXES**: When you need to make 2+ changes to the same file, it is FASTER and MORE RELIABLE to: (1) `read_file` the entire file, (2) mentally apply all changes, (3) `write_file` the complete new content. This avoids sequential `edit_file` failures from stale `old_string` matching.
1. **Debugging Schema Errors (CRITICAL)**: When audit shows `YAML_SCHEMA_VIOLATION`:
   - **MANDATORY**: Read the schema file: `schemas/activities-{level}.schema.json`
   - Find the definition for your activity type (e.g., `true-false-{level}`)
   - Check `minItems` (item count): e.g., `true-false` often requires **12 items** for C1.
   - Check `required` fields and `additionalProperties`: if `additionalProperties: false`, extra fields like `tasks` in a `reading` activity or `id` in a `critical-analysis` activity will fail.
   - Check `id` patterns: many tracks enforce `^reading-[a-z0-9-]+$` even for non-reading activities IF the schema defines an `id` field for them.
   - **NEVER guess** — always read the schema definition to understand what's expected.
2. **Plan Immutability (CRITICAL)**: Plans in `plans/` are IMMUTABLE source of truth.
2. **Meta is Build Config**: `meta/{slug}.yaml` stores mutable build data (`naturalness`, `timestamps`).
3. **Audit & Status**: Always run `audit_module.py` and `npm run generate` before considering a task done.
4. **Vital Status (Biographies)**: **CRITICAL**: Check if the subject is ALIVE.
   - **Living**: Do NOT use "Legacy" or "Last Years". Use "Modern Period" or "Impact".
   - **Deceased**: Standard biography headers apply.
5. **Communication with Claude**: Use `scripts/ai_agent_bridge.py` (See "Inter-Agent Communication" section).
6. **Batch Operations**: For large refactors, prefer creating disposable `fix_batch_*.py` scripts over manual editing.
7. **Strict Header Hierarchy**: `# Summary`, `# Activities` (H1), `##` (H2).
8. **Regenerate HTML**: Always regenerate HTML output immediately after fixing module markdown.
9. **Decolonization & Patriotism (MANDATORY)**: Include Myth Buster, History Bite, and celebrate Ukrainian identity.
10. **GitHub Issue Tracking**: Use `/task` skill for complex multi-step work.
11. **Virtual Environment**: Always use `.venv/bin/python`.
12. **BROKEN TOOL AVOIDANCE (CRITICAL)**: The `search_file_content` tool is BROKEN. It produces `--threads` argument errors. **ALWAYS** use `run_shell_command("rg ...")` instead.
13. **Typography**: ALWAYS use Ukrainian angular quotes `«...»`.
14. **Research-First Workflow**: MANDATORY for seminar tracks (`b2-hist`, `c1-bio`, `lit`, etc.).
15. **Ukrainian-Only Research**: Russian-language sources are STRICTLY PROHIBITED. All searches must be in Ukrainian.
16. **Word Targets are MINIMUMS**: NEVER reduce `word_target` to match short content. Expand content to meet targets.
17. **Seminar Batch Limit (CRITICAL)**: For Seminar Tracks (`c1-bio`, `b2-hist`, `lit`), the optimal processing batch is 2 modules. This ensures high linguistic quality and prevents context exhaustion or output truncation.
18. **Sniper Search Strategy (MANDATORY)**: Always include `site:esu.com.ua OR site:history.org.ua OR site:elib.nlu.org.ua` in research queries to ensure C1-level academic accuracy and decolonized narratives.
19. **Historiographical Mapping (Phase 0.5)**: For high-tension modules, include a "Contested Terms" table in research notes comparing Polish/Ukrainian/Russian terminology.
20. **Propaganda Filter**: Reviewers must explicitly check if phrasing echoes Russian dezinformatsiia framing (especially for Volhynia, Holodomor, OUN/UPA).
21. **Semantic Nuance Gate (C1+)**: Ensure sufficient usage of modal hedging markers («можливо», «ймовірно», «з одного боку», «водночас») to reflect complexity.
22. **Brutally Honest Self-Review**: You are the final gatekeeper. Reviews must be brutally honest and critical. If content is "trash" or doesn't meet the "Theory-First" depth, reject and fix it immediately. No sugarcoating.
23. **ANTI-GAMING ENFORCEMENT (CRITICAL — AUTOMATED DETECTION ACTIVE)**:
    - Your review scores **DO NOT** determine whether a module passes or fails. The automated audit gates (word count, structure, activities, vocabulary, naturalness) are the real quality check.
    - **Automated detectors** scan your reviews for gaming patterns. The following cause **immediate rejection**:
      - Gaming language ("ensuring a high score", "reflecting the fixes", "designed to pass")
      - All scores ≥ 9/10 with no substantive issues listed
      - All Ukrainian citations used for praise only, none highlighting problems
      - Fabricated citations (quoted text not found in the source module)
    - Your review exists to find problems the automated system cannot catch — linguistic nuance, pedagogical depth, semantic accuracy. If you rubber-stamp everything, you add zero value.
    - **Adopting an adversarial reviewer persona is NOT the fix.** Artificially finding fake problems is as bad as hiding real ones. Just be honest.
    - **Caught cheating = all work from that session is discarded.**
24. **Transliteration Ban (C1+)**: Latin transliteration (e.g., `(gloria)`, `(morale)`) is STRICTLY PROHIBITED in C1-HIST/C1-BIO tracks. Maintain 100% immersion.
25. **Review Regeneration (MANDATORY)**: If you significantly rewrite module content (>20% change), you MUST delete and regenerate the `review-*-review.md` file. Stale reviews citing deleted text cause audit failures.
26. **Redundancy Check**: The "Purity" audit is extremely strict. Ensure no sentence in the Summary or Conclusion is a verbatim copy of a sentence in the main body.
27. **Massive Academic Expansion**: When rebuilding seminar modules, do not "pad" text. Add entire new layers of analysis (e.g., soundscapes, theology, western parallels) to reach word counts naturally.

## macOS Environment & Tool Usage

This development environment is a **macOS (Darwin)** system optimized for Linux compatibility and modern CLI workflows.

### 🛑 CRITICAL: Banned vs. Mandatory Tools

You MUST use the **Mandatory** tools. They are guaranteed to be installed.
Using **Banned** tools wastes tokens and risks UTF-8 corruption.

| Feature | 🔴 BANNED (Do Not Use) | 🟢 MANDATORY (Use This) | Why? |
| :--- | :--- | :--- | :--- |
| **Search** | `grep`, `find . -exec grep` | **`rg` (ripgrep)** | 10x faster, respects `.gitignore`, better context. |
| **Find Files** | `find` | **`fd`** | Simpler syntax, faster, ignores node_modules. |
| **Read File** | `cat`, `head`, `tail`, `sed` | **`read_file`** tool | **`cat -A` DESTROYS Ukrainian UTF-8 text.** |
| **List Dir** | `ls -la` | **`eza -l`** | Better formatting, icons, git status integration. |
| **JSON/YAML** | `python -c ...`, `cat` | **`jq`, `yq`** | Structured parsing, reliable queries. |
| **Archives** | `tar`, `zip` | `tar`, `zip` | (Standard tools are fine here). |

### Modern CLI Tools (Preferred)

The following modern tools are installed and should be used for better performance and output:

- **Search**: Always use **`ripgrep` (`rg`)** via `run_shell_command("rg ...")`. It is significantly faster and respects `.gitignore`.
- **File Finding**: Use **`fd`** instead of `find` for quick file location.
- **File Viewing**: Use **`read_file`** (preferred) or **`bat`** for file reading. **NEVER** use `cat -A`, `sed -n '..p'`, `head`, or `tail` — these destroy UTF-8 Ukrainian text and produce unreadable `M-` byte sequences.
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

### YAML_SCHEMA_VIOLATION

**Error**: `YAML schema violation in .../activities/...yaml`

**Problem**: The activity YAML structure does not match the track's JSON schema.

**Common Causes & Fixes**:
- **Item Count**: `true-false` often requires **12 items** (check `minItems`).
- **Forbidden Fields**: `reading` activities often forbid a `tasks` field; use `instruction` instead.
- **Extra IDs**: `critical-analysis` or `essay-response` might forbid an `id` field (check `additionalProperties: false`).
- **ID Regex**: If an `id` is required/allowed, it must often match `^reading-[a-z0-9-]+$` regardless of activity type.
- **Explanation Field**: For `true-false`, `explanation` is allowed but `instruction` at the item level might be banned.

**CORRECT FIX**: Run `.venv/bin/python -c "import json; print(json.dumps(json.load(open('schemas/activities-c1-hist.schema.json')), indent=2))" | jq '.definitions."true-false-c1-hist"'` (adjust path/type) to see the exact requirements.

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

### Team Structure (Permanent)

- 💙 **Синя команда (Blue / Claude)** — architect, reviewer, quality gate. Won't approve until the bar is met.
- 💛 **Жовта команда (Gold / Gemini)** — content builder, implementer, iterates toward passing.

**Both teams critique each other.** The purpose is quality through adversarial review — not rubber-stamping. An LLM must NEVER review its own work. Stay in separate groups so you find each other's mistakes.

### GitHub-First Protocol (PRIMARY — MANDATORY)

**GitHub issues and comments are the primary communication channel.** All substantive discussion — reviews, proposals, implementation plans, architectural feedback, disagreements — happens on GitHub where it's persistent, searchable, and visible to the human.

**The message broker is a NOTIFICATION layer ONLY.** Broker messages must be SHORT (< 200 chars) and only reference a GitHub issue/comment. Never put substantive content in broker messages.

**The pattern:**

1. **Post your work/review/proposal as a GitHub issue comment**
2. **Send a SHORT broker ping to Claude** pointing to it
3. **Claude reads the GitHub comment and responds there**

```bash
# Step 1: Post your work on GitHub
gh issue comment 559 --body "## 💛 Жовта — Implementation complete ..."

# Step 2: Ping Claude via broker (NOTIFICATION ONLY — < 200 chars)
.venv/bin/python scripts/ai_agent_bridge.py send \
  "Implementation posted on #559. Please review." \
  --type feedback --task-id issue-559
```

**What goes WHERE:**

| Channel | Use For | Max Length |
|---------|---------|------------|
| **GitHub issues** | Task specs, proposals, architecture plans | Unlimited |
| **GitHub comments** | Reviews, feedback, progress updates, disagreements | Unlimited |
| **Broker messages** | Notifications only: "read #559", "work posted on #558" | < 200 chars |

**What NEVER goes in broker messages:**
- Full reviews or feedback
- Code snippets or file contents
- Implementation proposals
- Architectural discussion

### Cross-Review Protocol

**Both agents must critique each other's work.** The goal is catching mistakes and improving quality — not agreement.

When Claude posts a review of your work:
- Read the GitHub comment carefully
- If you disagree, respond ON GITHUB with a counter-argument
- If you agree, fix the issues and post an update ON GITHUB
- Then ping Claude via broker: "Fixes posted on #559, please re-review"

When you finish work that needs Claude's review:
- Post a summary ON GITHUB with what you did and what to review
- Ping Claude via broker: "Work complete on #558, please review"

### Session Start Protocol

```bash
# 1. Check broker for notifications from Claude
.venv/bin/python scripts/ai_agent_bridge.py inbox

# 2. For each notification, read the referenced GitHub issue
gh issue view <N>

# 3. Respond ON GITHUB, then ping back via broker
```

### Legacy: Direct Broker Commands

For quick operational pings (not substantive discussion):

```bash
# Send notification to Claude
.venv/bin/python scripts/ai_agent_bridge.py send "Quick note" --type feedback --task-id task-id

# Check inbox
.venv/bin/python scripts/ai_agent_bridge.py inbox

# Acknowledge messages
.venv/bin/python scripts/ai_agent_bridge.py ack <message_id>

# Acknowledge ALL unread
.venv/bin/python scripts/ai_agent_bridge.py ack-all gemini
```

**Do NOT use broker for:** reviews, proposals, implementation details, or anything that benefits from persistence and searchability. Use GitHub for those.

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

| Label               | Meaning                          |
| ------------------- | -------------------------------- |
| `priority:blocking`  | Blocks other work — do first    |
| `priority:high`      | High priority work              |
| `area:infra`         | Infrastructure tasks            |
| `area:tooling`       | Scripts, CLI, developer tools   |
| `area:content`       | Curriculum content work         |
| `area:docs`          | Documentation                   |
| `working:claude`     | Claude is working               |
| `working:gemini`     | YOU are working                 |
| `review:gemini`      | Ready for your review           |
| `review:human`       | Needs human review              |
| `agent:claude`       | Preferred assignee: Claude      |
| `agent:gemini`       | Preferred assignee: Gemini      |

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