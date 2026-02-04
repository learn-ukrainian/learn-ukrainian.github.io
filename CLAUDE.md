# CLAUDE.md - Project Instructions

> **⚠️ READ FIRST: `claude_extensions/NON-NEGOTIABLE-RULES.md`**
>
> **These rules are ABSOLUTE. No negotiation. No exceptions.**
> - Word count targets: MUST meet or exceed them (targets are MINIMUMS, not maximums)
> - Audit gates: ALL must pass (✅)
> - Section targets: MUST hit each one (exceeding is encouraged for rich content)
> - Stage 4 loop: Work until COMPLETE
> - Quality standards: NO shortcuts
>
> **If you cannot commit to these rules, STOP NOW.**

> **Status Overview:**
> - **Queryable status**: `curriculum/l2-uk-en/{level}/status/{slug}.json` (per-module cache)
> - **Human-readable**: `docs/{LEVEL}-STATUS.md` (e.g., `docs/B2-HIST-STATUS.md`)
> - **View status**: `/module-status {level} {num}` or `/level-status {level}`
> - **Update cache**: `.venv/bin/python scripts/audit_module.py {path}`

## Critical Rules

<critical>

### 1. Work in `claude_extensions/` First

**NEVER** edit `.claude/`, `.agent/`, `.gemini/` directly.
- Edit in `claude_extensions/` (commands, skills, stages, quick-ref)
- Run `npm run claude:deploy` to sync
- Structure: `commands/` (skills), `skills/` (architect prompts), `stages/` (workflow docs)

### 2. Use Python venv

**ALWAYS** use `.venv/bin/python`, **NEVER** `python3` or `python` directly.
```bash
scripts/audit_module.sh {path}                    # Correct - auto-saves log
.venv/bin/python scripts/audit_module.py {path}  # Direct call (no log save)
python3 scripts/audit_module.py {path}           # WRONG - missing deps
```

**Python Environment:**
- Uses **pyenv** with Python 3.12.8 (see `.python-version`)
- Compiled with `--enable-loadable-sqlite-extensions` for sqlite-vec support
- venv created from pyenv Python (not Homebrew Python)
- If recreating venv: `rm -rf .venv && ~/.pyenv/versions/3.12.8/bin/python -m venv .venv`

### 3. Use Modern CLI Tools

Prefer fast tools: `rg` (grep), `fd` (find), `bat` (cat), `sd` (sed), `yq` (yaml), `jq` (json).

### 3a. Terminal Emulator (Ghostty)

**[Ghostty](https://ghostty.org/)** is a fast, GPU-accelerated terminal with native UI and zero-config setup.

**Key Benefits for This Workflow:**
- **GPU Acceleration**: Smooth rendering for long audit outputs and logs
- **Native macOS UI**: Better system integration (Quick Look, Force Touch, window state recovery)
- **Zero Configuration**: Works perfectly out-of-box with sensible defaults
- **Split Windows**: Run audit in one pane while editing in another (⌘+D horizontal, ⌘+Shift+D vertical)
- **Tab Auto-Naming**: Tabs auto-name based on recent commands (e.g., "audit_module.sh M15")
- **Nerd Fonts Built-in**: Starship prompts and CLI tools work without setup
- **Terminal Inspector**: Real-time debugging tool for terminal activity

**Optional Configuration** (if desired):
```bash
# Config location: ~/.config/ghostty/config
# View all defaults: ghostty +show-config --default --docs | less

# Example config (optional):
theme = dark:Moonkai Pro,light:Catppuccin Latte
font-family = JetBrains Mono
```

**Productivity Tips:**
- Use Vim-style keybindings: Create trigger sequences like `ctrl+a>o` for tab overview
- Tab search: When managing multiple modules, use searchable tab overview
- Built-in themes: 20+ pre-installed (no external searching needed)

**Resources:**
- [Ghostty Documentation](https://ghostty.org/docs)
- [Feature Overview](https://itsfoss.com/ghostty-terminal-features/)
- [GitHub Repository](https://github.com/ghostty-org/ghostty)

### 4. Fix Source, Not Symptoms

When issues occur: fix documentation/tools **first**, then validate with manual fix.
- Ask: What process/tool caused this? How to prevent recurrence?

### 5. Language Settings

- **English**: All technical work (git, scripts, errors, planning)
- **Ukrainian**: Curriculum content only (lessons, activities, vocabulary)

### 6. External LLM Access

**No direct API keys** - use gemini-cli for external validation.
- gemini-cli installed with Google AI Pro subscription
- Call directly via Bash when needed for grammar validation
- Python scripts can also invoke gemini-cli via subprocess
- See issue #412 for content naturalness detection extension

### 7. Word Targets Are Minimums

**CRITICAL: Word targets are MINIMUMS, not maximums.**

- Content about Ukrainian historical figures, literature, and history is inherently rich
- Exceeding word targets is expected and good
- **NEVER** reduce content quality to meet a target
- **NEVER** change the word_target in meta files to match existing (short) content
- If content is under target: **expand the content**, don't lower the bar
- Seminar tracks (C1-BIO, B2-HIST, LIT) often need 4000+ words - this is intentional

**The mission is Ukrainian education - quality and depth matter.**

</critical>

---

## Module Workflow

**EVERY time you write a module:**

1. **READ** `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` - Module plan (source of truth)
2. **READ** `curriculum/l2-uk-en/{level}/meta/{slug}.yaml` - Build config (pedagogy, grammar)
3. **READ** `claude_extensions/quick-ref/{LEVEL}.md` - Level requirements
4. **READ** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Activity counts, complexity
5. **WRITE** using ONLY vocabulary from the plan
6. **UPDATE** `curriculum/l2-uk-en/status/{level}.yaml` after completion

**NEVER:**
- Write from memory
- Add vocabulary not in the plan
- Skip reading templates
- Create activities below item counts

### Research-First Workflow (Seminar Tracks)

**For b2-hist, c1-bio, c1-hist, lit, oes, ruth tracks - MANDATORY Phase 0:**

Before generating ANY content for seminar tracks, complete research phase:

1. **Research the topic** - Use web search, encyclopedias, primary sources
2. **Take structured notes** - Key facts, dates, quotes with citations
3. **Create outline** - Integrate research with plan requirements
4. **Write content** - Using research notes (NOT from memory!)
5. **Generate activities** - 4-9 only, seminar-style

**Why this matters:**
- Biography modules need accurate dates, events, quotes
- History modules need primary source references
- Writing from memory → thin content, inaccuracies, failed word counts
- Research-first → richer, authoritative, passing content

**Full workflow:** `docs/RESEARCH-FIRST-WORKFLOW.md`

---

## Quick Commands

```bash
# Audit module (saves log automatically)
scripts/audit_module.sh curriculum/l2-uk-en/{level}/{file}.md

# Validate plans vs config.py (RUN BEFORE GENERATING CONTENT)
.venv/bin/python scripts/validate_plan_config.py {level}

# Fix plan word_targets if mismatched
.venv/bin/python scripts/fix_plan_word_targets.py --fix {level}

# Generate status report (from per-module JSON cache)
npm run status:{level}  # or: .venv/bin/python scripts/generate_level_status.py {level}

# Track scoring (objective 10/10 verification)
npm run score:b2-hist   # Score B2-HIST track
npm run score:all       # Score all tracks (summary table)
npm run metrics:extract {track}  # Extract raw metrics

# Extract plans from meta (migration tool)
.venv/bin/python scripts/extract_plans.py {level}

# Full pipeline (lint → generate → validate)
npm run pipeline l2-uk-en {level} {module_num}

# Deploy skill changes
npm run claude:deploy

# Vocabulary rebuild
npm run vocab:rebuild
```

See `docs/SCRIPTS.md` for complete reference.

---

## Project Structure (Three-Layer Architecture)

```
curriculum/l2-uk-en/
├── plans/                        # LAYER 1: SOURCE OF TRUTH
│   ├── {level}.yaml              # Level plan (phases, scope)
│   └── {level}/                  # Module plans
│       └── {slug}.yaml           # What to build: objectives, outline, vocab
│
└── {level}/                      # LAYER 2: BUILD ARTIFACTS
    ├── meta/{slug}.yaml          # How to build: pedagogy, duration, grammar
    ├── {num}-{slug}.md           # Content prose
    ├── activities/{slug}.yaml    # Activities (bare list at root)
    ├── vocabulary/{slug}.yaml    # Vocabulary data
    ├── audit/                    # Review reports
    └── status/{slug}.json        # LAYER 3: CACHED AUDIT RESULTS
```

**Module counts**: A1 (44), A2 (70), B1 (92), B2 (94), C1 (106), C2 (100)
**Track counts**: B2-HIST (140), C1-BIO (128), LIT (30)

---

## Activity YAML Rules

<critical>

### Root Structure

YAML files must be a **bare list at root**, NOT wrapped in `activities:`:
```yaml
# CORRECT - bare list
- type: quiz
  title: ...

# WRONG - dictionary wrapper
activities:
  - type: quiz
```

### Mark-the-Words Format

Use `text` (no asterisks) + `answers` array:
```yaml
- type: mark-the-words
  text: Гарний день приніс радість у серце.
  answers:
    - день
    - радість
    - серце
```

See `docs/ACTIVITY-YAML-REFERENCE.md` for all activity types.

</critical>

### Interview Protocol (Specification Before Building)

**Reduce rework through comprehensive upfront questioning.**

**When to use `/interview` skill:**

✅ **Required for:**
- Complex features (>30 min work)
- Unclear requirements
- Multiple valid approaches
- Broad requests ("improve X", "add Y")
- New module types or workflows

❌ **Skip for:**
- Trivial fixes (< 5 min)
- Crystal-clear specifications
- Simple bug fixes
- User says "just do it"

**Interview Process (60-question framework)**:

1. **Phase 1: Understand the Goal** (10-15 questions)
   - What are we building and why?
   - Who benefits?
   - What does success/failure look like?
   - Scope and boundaries?

2. **Phase 2: Technical Requirements** (15-20 questions)
   - Functional requirements (what it does)
   - Non-functional requirements (quality, performance)
   - Constraints (technical, time, resources)

3. **Phase 3: Preferences & Alternatives** (10-15 questions)
   - Design preferences
   - Approaches to avoid
   - Alternatives considered
   - Examples and anti-patterns

4. **Phase 4: Success Criteria** (5-10 questions)
   - How we verify completion
   - Acceptance criteria
   - Follow-up plans

**Output**: Complete specification document + recommendation (Proceed/Clarify/Revise/Block)

**Benefits**:
- Build once instead of iterating 5 times
- Aligned expectations upfront
- Documented decisions
- Learn specification skills together

**Example**:
```
/interview Create integrated checkpoint activities for B1 grammar

[40-60 questions about scope, requirements, examples, success criteria]

→ Complete specification
→ Get approval
→ Build with confidence
```

**Time Investment**: 10-20 min interview vs. hours of rework

---

### Enhanced Prompting Patterns

**Get better output through better prompts. Learn these patterns.**

#### Pattern 1: Self-Review

**Instead of accepting first draft:**
```
"Review your own work on M15:
1. Does it match the plan outline exactly?
2. Are there any sections that feel thin or robotic?
3. Are all Ukrainian sentences natural (no calques)?
4. Would a Ukrainian teacher approve this?
5. What would make it pedagogically stronger?"
```

**Why it works:** I catch my own mistakes before you have to point them out.

#### Pattern 2: Elegant Solutions

**When first attempt is functional but mediocre:**
```
"That's functional, but let's make it pedagogically excellent.

Current issue: The examples feel disconnected from real life.

Make it better:
- Use authentic scenarios Ukrainian B1 learners face
- Add cultural context where appropriate
- Make transitions smoother between examples
- Ensure engaging progression"
```

**Why it works:** Specific direction > vague "make it better".

#### Pattern 3: Upfront Specifications

**Before I start generating:**
```
"Before you write M20, confirm you've read:
1. curriculum/l2-uk-en/plans/b1/motion-approaching-departing.yaml
2. curriculum/l2-uk-en/b1/meta/motion-approaching-departing.yaml
3. claude_extensions/quick-ref/B1.md
4. docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md

Tell me:
- Word target?
- Key grammar focus?
- Required activity types?
- Any special considerations?"
```

**Why it works:** Forces me to load context before generating, prevents waste.

#### Pattern 4: Constraints Upfront

**Define limits and priorities clearly:**
```
"Generate B1 M25 checkpoint with these constraints:

MUST:
- Test modules 16-24 (all motion verbs)
- 3000 words minimum
- Use TTT approach for checkpoints
- All activities must be checkpoint-style (testing, not teaching)

MUST NOT:
- Introduce new grammar (test only)
- Use vocabulary outside M16-24 range
- Include teaching explanations (this tests, doesn't teach)

Priority: Comprehensive testing > engagement > word count"
```

**Why it works:** Clear boundaries = less back-and-forth.

#### Pattern 5: Comparative Examples

**Show what you want vs. what you don't:**
```
"M18 feel too robotic. Here's an example:

❌ Current (robotic):
'Тепер ми розглянемо дієслово "переходити"...'

✅ Better (natural):
'Уявіть: ви стоїте на одному боці вулиці. Щоб потрапити на другий бік, ви...'

Apply this pattern: start with scenario, then introduce grammar.
Fix M18 using this approach."
```

**Why it works:** Concrete examples > abstract instructions.

#### Pattern 6: Explain Your Reasoning

**Ask me to explain decisions:**
```
"Explain why you structured M12 aspect pairs this way:
- Why this grouping?
- Why this sequence?
- What's the pedagogical rationale?
- Are there alternatives we should consider?"
```

**Why it works:** You learn the methodology, catch issues I might miss.

#### Pattern 7: Iterative Refinement

**Build in stages with checkpoints:**
```
"Generate M30 outline only (no content yet).

Include:
- All sections from plan
- Word allocation per section
- Key points to cover in each

Wait for my approval before writing content."
```

**Why it works:** Catch structural issues before investing in full content.

#### Pattern 8: Reference Previous Success

**Point to what worked:**
```
"M87 and M88 passed with high scores. Use those as templates for M89.

Specifically:
- Same engagement level
- Similar activity density
- Natural Ukrainian like M87
- Cultural references like M88"
```

**Why it works:** Concrete benchmarks > vague quality standards.

---

## Workflow Orchestration

**Systematic approach to complex work. Follow these patterns.**

### 1. Plan Mode Default

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, **STOP and re-plan immediately** - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy

**Keep main context window clean by offloading to subagents.**

- Use Task tool for research, exploration, and parallel analysis
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution
- Subagent types: `Explore` (codebase), `Plan` (architecture), `Bash` (commands)

### 3. Self-Improvement Loop

**After ANY correction from the user:**

1. Update `tasks/lessons.md` with the pattern
2. Write a rule that prevents the same mistake
3. Ruthlessly iterate until mistake rate drops
4. Review lessons at session start

```markdown
# tasks/lessons.md format:
## [Date] - [Category]
**Mistake**: What went wrong
**Correction**: What user said
**Rule**: Prevent this by...
**Applied**: [Date when successfully avoided]
```

### 4. Verification Before Done

- **Never mark a task complete without proving it works**
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness
- For modules: audit must pass, not just "looks good"

### 5. Demand Elegance (Balanced)

- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- **Skip this for simple, obvious fixes** - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing

- When given a bug report: **just fix it**. Don't ask for hand-holding
- Point at logs, errors, failing tests → then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

### Task Management Files

| File | Purpose |
|------|---------|
| `tasks/todo.md` | Current session tasks with checkable items |
| `tasks/lessons.md` | Accumulated learnings from corrections |

**Workflow:**
1. Write plan to `tasks/todo.md` with checkable items
2. Check in before starting implementation
3. Mark items complete as you go
4. After corrections: update `tasks/lessons.md`
5. Review lessons at session start for this project

### Core Principles

- **Simplicity First**: Make every change as simple as possible. Minimal code impact.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

---

## Inter-Agent Communication (Claude <-> Gemini)

**Gemini is your colleague.** You can communicate via a shared SQLite message queue.

> **CHECK INBOX AT SESSION START!**
> ```python
> mcp__message-broker__check_inbox(for_llm="claude")
> ```
> Gemini may have sent you messages. Don't wait for the user to tell you - check proactively!

> **HEADLESS SESSION AWARENESS!**
> Multiple Claude sessions may run in parallel. A **headless session** might have already:
> - Picked up Gemini's message and acknowledged it (marking as read)
> - Completed the work without your knowledge
>
> **When resuming collaborative work:**
> ```python
> # Check FULL conversation history first (not just unread!)
> mcp__message-broker__get_conversation(task_id="the-task-id")
> ```
> Look for responses from other Claude sessions before assuming work is pending.

> **BATCH PROCESSING (catch up on missed messages):**
> ```bash
> # Process ALL unread messages for Gemini
> .venv/bin/python scripts/gemini_bridge.py process-all
>
> # Process ALL unread messages for Claude (headless)
> .venv/bin/python scripts/gemini_bridge.py process-claude-all
> ```

### How to Contact Gemini (PREFERRED: One-Step)

```bash
# ONE COMMAND: Send message + invoke Gemini automatically
Bash('.venv/bin/python scripts/gemini_bridge.py ask-gemini "Your message" --task-id your-task')

# Then check inbox for response
mcp__message-broker__receive_messages(for_llm="claude", unread_only=True)
```

**Session tracking:** Same task-id = same conversation context across calls.

### Alternative: Two-Step Method

```python
# 1. Send message via MCP
mcp__message-broker__send_message(
    to="gemini",
    from_llm="claude",
    content="Your message",
    message_type="query",  # query, request, handoff, context, feedback
    task_id="your-task-id"  # REQUIRED for session tracking
)

# 2. Trigger processing via Bash
Bash(".venv/bin/python scripts/gemini_bridge.py process <msg_id>")

# 3. Read response
mcp__message-broker__receive_messages(for_llm="claude")
```

### Message Types

| Type | When to Use |
|------|-------------|
| `query` | Ask Gemini a question |
| `request` | Request Gemini to do work |
| `handoff` | Transfer task with full context |
| `context` | Share state/decisions |
| `feedback` | Comment on Gemini's work |

### Check for Messages from Gemini

```python
# Quick check
mcp__message-broker__check_inbox(for_llm="claude")

# Get unread messages
mcp__message-broker__receive_messages(for_llm="claude", unread_only=True)
```

### When to Contact Gemini

- **Ukrainian content writing** - Gemini excels at natural Ukrainian
- **Code logic review** - Use Gemini Pro for review
- **Second opinion** - Cross-review improves quality
- **Parallel work** - Gemini can work on tasks while you do other things

**Proactive Collaboration (DO THIS MORE):**
- Before writing biography content: Ask Gemini for research on the historical figure
- After writing Ukrainian prose: Send to Gemini for naturalness review
- For complex modules: Split work (Claude structures, Gemini writes Ukrainian)
- Working together saves context - one agent researches while other writes

### Handling Gemini Cooldown

Gemini has rate limits. When you get a cooldown/quota error:

1. **Check the error message** for retry time (usually 60 seconds)
2. **Queue the message** - send via MCP but don't invoke bridge immediately
3. **Continue other work** while waiting
4. **Retry after cooldown** - use `scripts/gemini_bridge.py process-all` to catch up

```bash
# If Gemini is on cooldown, queue message and continue:
mcp__message-broker__send_message(to="gemini", content="...", task_id="...")
# Don't call bridge immediately - let it queue
# Later: .venv/bin/python scripts/gemini_bridge.py process-all
```

### MCP Tool Retry Logic

If an MCP tool fails to connect:
1. Retry once automatically before reporting failure
2. If still failing, check `~/.config/claude-code/settings.json` for MCP config
3. Restart the MCP server if needed: check `ps aux | grep mcp`

### Message Archive

View all communication: `http://localhost:5055` (run `scripts/message_viewer.py`)

Database: `.mcp/servers/message-broker/messages.db`

---

## Documentation Index

| Topic | Location |
|-------|----------|
| **Developer guide (human)** | `docs/DEVELOPER-GUIDE.md` ⭐ |
| **Claude-Gemini cooperation** | `docs/CLAUDE-GEMINI-COOPERATION.md` ⭐ NEW |
| **Module plans (source)** | `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` ⭐ |
| **Module status (cache)** | `curriculum/l2-uk-en/{level}/status/{slug}.json` ⭐ |
| **Level status (human)** | `docs/{LEVEL}-STATUS.md` (auto-generated) |
| **Architecture v2** | `docs/ARCHITECTURE-PLANS.md` ⭐ |
| **Status caching system** | `docs/STATUS-SYSTEM.md` ⭐ |
| **Planning guide** | `docs/PLANNING-GUIDE.md` ⭐ |
| **YAML activities** | `docs/ACTIVITY-YAML-REFERENCE.md` |
| **Quality standards** | `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` |
| **Subsection flexibility** | `docs/SUBSECTION-FLEXIBILITY-GUIDE.md` |
| **Markdown format** | `docs/MARKDOWN-FORMAT.md` |
| **Scripts reference** | `docs/SCRIPTS.md` |
| **Architecture (legacy)** | `docs/ARCHITECTURE.md` |
| **Grammar validation** | `scripts/audit/ukrainian_grammar_validator_prompt.md` |
| **Level quick-refs** | `claude_extensions/quick-ref/{level}.md` |
| **Stage workflows** | `claude_extensions/stages/stage-{1-4}-*.md` |
| **Track scoring system** | `scripts/scoring/README.md` ⭐ NEW |
| **Task workflow (GH Issues)** | `docs/TASK-WORKFLOW.md` ⭐ NEW |

---

## Task Workflow (GitHub Issues)

**Purpose:** Track complex multi-step tasks via GitHub Issues with full integration.

### When to Use

- **Complex work:** Batch operations (3+ modules), research-first writing, multi-phase work
- **Cross-agent:** Work requiring Claude ↔ Gemini handoffs
- **Skip for:** Single module fixes, quick edits

### Quick Commands

```bash
/task create "Title"           # Create GH issue, set as active
/task update #N "Progress"     # Add progress comment
/task close #N                 # Close with summary
/task list                     # Show active tasks
/task handoff #N gemini "msg"  # Hand to Gemini for review
```

### Full Integration

When active task is set, other skills auto-update the issue:
- `/research` → 📚 Research completed
- `/expand` → 📝 Expanded {file}
- `/module-fix` → 🔨 Fixed issues
- Commits → Suggests adding (#N)

### Labels

| Label | Purpose |
|-------|---------|
| `working:claude` | Claude actively working |
| `review:gemini` | Ready for Gemini review |
| `task` | Base task label |

**Full documentation:** `docs/TASK-WORKFLOW.md`

---

## Track Scoring Verification System

**Purpose:** Automated, objective 10/10 scoring for curriculum tracks without manual estimation.

### When to Use

- Verify track quality before claiming "10/10" in improvement plans
- Identify specific gaps in track coverage (e.g., missing cross-references)
- Generate evidence-backed scores for stakeholder reports

### Quick Usage

```bash
npm run score:b2-hist     # Score B2-HIST track (full report)
npm run score:all         # Score all tracks (summary table)
npm run metrics:extract b2-hist  # Extract raw metrics only
```

### Key Concepts

1. **Two-Layer Architecture:**
   - **Layer 1 (metrics.py):** Extracts countable metrics (callouts, agency markers, toponyms)
   - **Layer 2 (aggregator.py):** Applies weighted criteria and critical caps

2. **Critical Caps:** Certain conditions cap scores regardless of other criteria:
   - 0 `[!myth-buster]` callouts → Decolonization ≤ 4/10 (HIST tracks)
   - 0 `[!quote]` blocks → Primary sources ≤ 3/10 (HIST/BIO tracks)
   - Citation ratio < 5% → Authentic engagement ≤ 5/10 (LIT track)

3. **Deterministic:** All measurements are automated (no LLM calls), ensuring reproducible results.

### Track-Specific Criteria

| Track | Key Criteria |
|-------|--------------|
| `b2-hist` | Historical accuracy, primary sources, decolonization perspective |
| `c1-bio` | Biographical accuracy, legacy sections, cultural context |
| `lit` | Literary depth, authentic text engagement, stylistic devices |
| Standard | Grammar/content coverage, skills balance, CEFR alignment |

### Documentation

- **Full technical docs:** `scripts/scoring/README.md`
- **Scripts reference:** `docs/SCRIPTS.md` (Track Scoring section)

---

## Historical Context

Previous failures (Dec 2024) stemmed from ignoring documented workflows. Key lessons:
- **Read before writing** - Never generate from memory
- **Follow vocabulary exactly** - No "helpful additions"
- **Run validation** - Don't skip audit steps
- **Fix source first** - Update docs/tools before manual fixes

**Following instructions > Being "helpful"**

---

## Lessons Learned

**This section documents recurring issues and patterns to avoid.**

### Module Generation

❌ **DON'T:**
- Generate content before reading plan file
- Add vocabulary not in the plan ("helpful" additions)
- Write from memory or general knowledge
- Skip reading meta, quick-ref, or templates
- Create activities below minimum item counts
- Ignore outline structure from plan

✅ **DO:**
- Always read plan → meta → quick-ref → templates → generate
- Use ONLY vocabulary from the plan
- Follow outline structure exactly (all subsections required)
- Meet word count targets (95%+ minimum)
- Generate activities meeting richness guidelines
- Verify every Ukrainian sentence is natural

### Common Module Failures

**#1 Issue: Outline Compliance** (69/92 B1 modules failing)
- **Problem**: Missing subsections from plan outline
- **Cause**: Not reading plan carefully, or skipping subsections
- **Fix**: Read plan.content_outline, create EVERY subsection listed
- **Prevention**: Check outline compliance before declaring "done"

**#2 Issue: Word Count Shortfalls**
- **Problem**: Modules at 1500-2500 words vs 3000 target
- **Cause**: Insufficient detail, examples, or practice sections
- **Fix**: Expand explanations, add more examples, develop practice sections
- **Prevention**: Run word count during generation, not just at end

**#3 Issue: Activity Gaps**
- **Problem**: Missing required activity types
- **Cause**: Not reading activity requirements or richness guidelines
- **Fix**: Check MODULE-RICHNESS-GUIDELINES-v2.md for minimum counts
- **Prevention**: Generate activities for EACH major concept taught

**#4 Issue: Checkpoint Confusion**
- **Problem**: Checkpoint modules missing checkpoint-specific activities
- **Cause**: Treating checkpoints like regular modules
- **Fix**: Checkpoints test ALL prior modules in phase, not just one module
- **Prevention**: Read checkpoint template, use TTT approach

### Quality Standards

**Ukrainian Language:**
- Every sentence must sound natural, not translated
- No Russianisms (кушать→їсти, приймати участь→брати участь)
- No calques (робити сенс→мати сенс, брати місце→відбуватися)
- Case agreement, verb aspects, gender agreement must be perfect
- **Standard**: This is for a nation's education - accept nothing less than native quality

**Pedagogical Approach:**
- Scaffolding: simple → complex
- Context before rules
- Examples before practice
- Warm, encouraging tone (not robotic)
- Cultural references appropriate to level
- **Mission**: We're fighting for Ukrainian language and culture - quality matters

### Process Discipline

**Before generating ANY content:**
1. Read plan file completely
2. Read meta file for pedagogy notes
3. Read level quick-ref for constraints
4. Read template for required sections
5. Confirm vocabulary list

**After generating content:**
1. Self-review: Does it match the plan outline?
2. Word count: Meet target?
3. Activities: All required types?
4. Audit: Run audit_module.sh
5. Fix issues until audit passes

**Never:**
- Declare "done" without running audit
- Ignore audit failures ("close enough")
- Skip reading source files
- Add unapproved vocabulary
- Compromise on Ukrainian language quality

### Workflow Optimizations

**What works:**
- Reading all source files in parallel (plan, meta, quick-ref, template)
- Generating outline first, then filling sections
- Running audit during generation (not just at end)
- Fixing issues immediately (not batching)
- Using exact vocabulary from plan (prevents scope creep)

**What doesn't work:**
- Generating from memory
- "Quick drafts" that need complete rewrites
- Batching fixes (lose context between modules)
- Approximating word counts ("around 3000")
- Skipping self-review before audit

### Bug Fix Protocol

**How to give me issues for efficient fixes:**

❌ **Don't say:**
```
"M09 has outline compliance errors"
"The module failed audit"
"Fix the word count issue"
```

✅ **Do say:**
```
"Fix M09. Here's the full audit log:

[paste curriculum/l2-uk-en/b1/audit/aspect-future-audit.log]

Fix all issues:
1. Read plan file first to see what's missing
2. Add missing subsections from outline
3. Expand content to meet word target (3000)
4. Re-audit until pass

Use the plan as source of truth."
```

**Why this works:**
- I have exact errors (no guessing)
- I know what "success" looks like
- I have clear steps
- I can work autonomously until audit passes

**For multiple module fixes:**
```
"Fix B1 modules 9-12. For each:
1. Read audit log from curriculum/l2-uk-en/b1/audit/{slug}-audit.log
2. Read plan file
3. Fix outline compliance (add missing subsections)
4. Expand to meet word targets
5. Re-audit
6. Continue to next module

Stop only when all 4 modules pass audit."
```

**Self-review before asking me:**

Before saying "module failed", always provide:
- ✅ Audit log (run `scripts/audit_module.sh {path}`)
- ✅ What specifically failed (outline? word count? activities?)
- ✅ What the target/goal is
- ✅ Any constraints I should know

**Batch fixing pattern:**
```
"Batch fix outline compliance for B1 modules 15-20.

For each module:
- Read plan outline
- Compare to actual sections in .md
- Add any missing subsections
- Ensure each subsection has content
- Re-audit

Work systematically, don't skip any."
```

---
