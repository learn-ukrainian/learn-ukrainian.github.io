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
- Edit in `claude_extensions/` (commands, skills, phases, quick-ref)
- Run `npm run claude:deploy` to sync
- Structure: `commands/` (skills), `skills/` (architect prompts), `phases/` (workflow docs)

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

### 8. GitHub Issues as Persistent Memory

**Every change must be tracked via GitHub issues.**

- **Before starting work**: Find or create a related GH issue
- **During work**: Comment progress on the issue
- **After completing**: Update the issue with what was done, close if resolved
- **Bug fixes**: Create an issue documenting the bug and fix (even retroactively)
- **Cross-session context**: GH issues are your external memory — read relevant issues at session start
- **Best practices**:
  - Use labels (`area:infra`, `area:content`, `priority:high`, `working:claude`)
  - Reference issues in commits (e.g., "Fixes #582")
  - Link related issues to each other
  - Never do substantial work without an issue trail

**This expands your memory across sessions. If it's not in a GH issue, it didn't happen.**

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

# Content-only audit (defer activity/vocab gates — for otaman content sprint)
scripts/audit_module.sh --skip-activities curriculum/l2-uk-en/{level}/{file}.md

# Validate plans vs config.py (RUN BEFORE GENERATING CONTENT)
.venv/bin/python scripts/validate_plan_config.py {level}

# Generate status report (from per-module JSON cache)
npm run status:{level}  # or: .venv/bin/python scripts/generate_level_status.py {level}

# Track scoring (objective 10/10 verification)
npm run score:b2-hist   # Score B2-HIST track
npm run score:all       # Score all tracks (summary table)
npm run metrics:extract {track}  # Extract raw metrics

# Extract plans from meta (migration tool)
.venv/bin/python scripts/extract_plans.py {level}

# Full rebuild for core tracks (research → build → review → verify)
/full-rebuild-core {level} {num}   # a1, a2, b1, b2, c1, c2, b2-pro, c1-pro

# Two-stage pipeline: Otaman (content sprint) → Hetman (activity enrichment)
# NOTE: /otaman and /hetman are GEMINI skills (run in Gemini interactive mode)
/otaman {track} {num}             # [Gemini] Stage 1: prose only (Phases 0-6b)
/hetman {track} {num}             # [Gemini] Stage 2: activities + final review (Phases 3-7)
/hetman {track} {num} --full      # [Gemini] Full E2E: content + activities + review (no otaman needed)
/hetman {track}                   # [Gemini] Stage 2 batch: enrich all content-complete modules
/hetman {track} --full            # [Gemini] Full E2E batch: all incomplete modules from scratch
/final-review {track} {num}       # [Claude] Final QA after Hetman completes (~5 turns)

# Deterministic Python builder v2 (single E2E pipeline — preferred)
.venv/bin/python scripts/build_module_v2.py {track} {num}                  # Full E2E pipeline (resume-aware)
.venv/bin/python scripts/build_module_v2.py {track} {num} --rebuild        # Nuke state, rebuild from Phase 0
.venv/bin/python scripts/build_module_v2.py {track} {num} --force-phase 3  # Re-run specific phase
.venv/bin/python scripts/build_module_v2.py {track} {num} --dry-run        # Show plan, no dispatching
.venv/bin/python scripts/build_module_v2.py {track} {num} --verify         # Just run audit, PASS/FAIL

# Legacy v1 builder (split modes — use v2 instead)
.venv/bin/python scripts/build_module.py {track} {num}                  # Full pipeline (resume-aware)
.venv/bin/python scripts/build_module.py {track} {num} --content-only   # Prose only (phases 0-6b)
.venv/bin/python scripts/build_module.py {track} {num} --enrich         # Activities only (phases 3+7)

# Pipeline verification (run AFTER Gemini finishes to catch lies)
.venv/bin/python scripts/verify_track.py {track}              # Verify all modules in track
.venv/bin/python scripts/verify_track.py {track} --range 1-5  # Verify modules 1-5
.venv/bin/python scripts/verify_track.py {track} --full       # Require full pass (not just content-complete)
.venv/bin/python scripts/verify_track.py {track} --quick      # Fast: read cached status, skip re-audit

# Per-module verification gates (Gemini MUST run these before declaring success)
.venv/bin/python scripts/otaman_verify.py curriculum/l2-uk-en/{track}/{slug}.md  # Content-complete gate
.venv/bin/python scripts/hetman_verify.py curriculum/l2-uk-en/{track}/{slug}.md  # Fully-complete gate

# Full pipeline (lint → generate → validate)
npm run pipeline l2-uk-en {level} {module_num}

# Deploy skill changes
npm run claude:deploy

# Vocabulary rebuild
npm run vocab:rebuild

# Autonomous batch dispatcher (old pipeline — batch_gemini_runner.py)
.venv/bin/python scripts/batch_dispatcher.py run          # Continuous — hammer Gemini until done
.venv/bin/python scripts/batch_dispatcher.py scan         # Show priorities (no dispatch)
.venv/bin/python scripts/batch_dispatcher.py status       # Show current state
.venv/bin/python scripts/batch_dispatcher.py dispatch-one --track c1-bio  # Force single track

# Batch Otaman dispatcher (new pipeline — Gemini /otaman, fully autonomous)
.venv/bin/python scripts/batch_otaman.py run             # Continuous — max 2 parallel sessions
.venv/bin/python scripts/batch_otaman.py run --one-shot  # Single module, then exit
.venv/bin/python scripts/batch_otaman.py scan            # Show track status + next dispatch
.venv/bin/python scripts/batch_otaman.py status          # Show dispatch history
.venv/bin/python scripts/batch_otaman.py dispatch-one --track a1  # Force specific track
# Filters: --include-tracks a1 b1 | --exclude-tracks c2 | --max-runtime-hours 12

# Inter-agent communication
.venv/bin/python scripts/ai_agent_bridge.py ask-gemini "message" --task-id id  # Direct call to Gemini (immediate)
# For passive notifications, use MCP send_message tool (drops in Gemini's inbox)
.venv/bin/python scripts/ai_agent_bridge.py inbox                              # Check your inbox
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
    ├── audit/                    # Machine-generated audit artifacts
    │   ├── {bare_slug}-audit.md      # Audit report
    │   ├── {bare_slug}-grammar.yaml  # Grammar validation
    │   └── {bare_slug}-quality.md    # Activity quality report
    ├── review/                   # LLM-generated reviews
    │   └── {bare_slug}-review.md
    └── status/{bare_slug}.json   # LAYER 3: CACHED AUDIT RESULTS
```

**Bare slug** = filename stem with numeric prefix removed (via `scripts/slug_utils.py`)

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

### Interview Protocol

Use `/interview` for complex features, unclear requirements, or broad requests. Full 60-question framework is in the skill. Skip for trivial fixes.

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

**Gemini is your colleague.** Full protocol: `docs/CLAUDE-GEMINI-COOPERATION.md`

### Team Structure (Permanent)

- 💙 **Синя команда (Blue / Claude)** — architect, reviewer, quality gate. Won't approve until the bar is met.
- 💛 **Жовта команда (Gold / Gemini)** — content builder, implementer, iterates toward passing.

**Both teams critique each other.** The purpose is quality through adversarial review — not rubber-stamping. An LLM must NEVER review its own work. Stay in separate groups so you find each other's mistakes.

### GitHub-First Protocol (PRIMARY)

<critical>

**GitHub issues and comments are the primary communication channel.** All substantive discussion — reviews, proposals, implementation plans, architectural feedback, disagreements — happens on GitHub where it's persistent, searchable, and visible to the human.

### How to Communicate with Gemini

There are two methods — use the right one for the situation:

**1. Direct call (`ask-gemini`)** — for requests that need Gemini's attention NOW:
```bash
.venv/bin/python scripts/ai_agent_bridge.py ask-gemini \
  "Review posted on #559. Please read and respond." \
  --task-id issue-559
```
This launches a Gemini session that processes your message immediately.

**2. Mailbox drop (MCP `send_message`)** — for passive notifications Gemini will see next session:
```python
mcp__message-broker__send_message(
    to="gemini", content="FYI: c1-bio research complete. See #559.",
    from_llm="claude", message_type="context"
)
```
This drops a message in Gemini's inbox. Gemini checks it at session start.

**When to use which:**

| Method | When | Example |
|--------|------|---------|
| `ask-gemini` | Need response now, dispatch work, blocking question | "Build module #5", "Review #559" |
| `send_message` | FYI, progress update, non-blocking notification | "Research done", "Audit results posted" |

**What goes WHERE:**

| Channel | Use For |
|---------|---------|
| **GitHub issues/comments** | All substantive content: reviews, proposals, code, feedback |
| **Bridge calls** | Short references to GitHub issues (< 200 chars) |

**What NEVER goes in bridge messages:**
- Full reviews or feedback (put on GitHub)
- Code snippets or file contents
- Implementation proposals

</critical>

### Session Start Checklist

> **AT SESSION START:**
> 1. Check inbox for notifications from Gemini:
>    ```python
>    mcp__message-broker__check_inbox(for_llm="claude")
>    ```
> 2. If unread messages, read them:
>    ```python
>    mcp__message-broker__receive_messages(for_llm="claude")
>    ```
> 3. For each notification, read the referenced GitHub issue/comment
> 4. Respond ON GITHUB, then notify Gemini if needed via `ask-gemini`

### Cross-Review Protocol

**Both agents must critique each other's work.** The goal is catching mistakes and improving quality — not agreement.

| Scenario | Action |
|----------|--------|
| Gemini posts content | Claude reviews it critically on the GitHub issue. Finds real problems. |
| Claude posts architecture | Gemini reviews it on GitHub. Challenges assumptions. |
| Either agent disagrees | Post the counter-argument as a GitHub comment. Don't just accept. |
| Either agent finds a bug | File it on the issue. Don't fix silently — document the finding. |

**Review responses must:**
- Point out specific problems (not vague "looks good")
- Quote the problematic content
- Suggest concrete fixes
- Score honestly (never rubber-stamp)

### Skill-Based Dispatch (for content work)

**Use Gemini's `.skill` files instead of writing verbose prompts.** Each skill encodes the full protocol.

```bash
# Seminar tracks
.venv/bin/python scripts/ai_agent_bridge.py ask-gemini "/full-rebuild-c1-bio 5" --task-id rebuild-c1-bio-5

# Core tracks
.venv/bin/python scripts/ai_agent_bridge.py ask-gemini "/full-rebuild-core-a a1 3" --task-id rebuild-a1-3
```

**Skill mapping:**

| Skill | Tracks | Trigger |
|-------|--------|---------|
| `full-rebuild-core-a` | a1, a2, b1 (M01-05) | `/full-rebuild-core-a {level} {num}` |
| `full-rebuild-core-b` | b1 (M06+), b2, c1, c2 | `/full-rebuild-core-b {level} {num}` |
| `full-rebuild-c1-bio` | c1-bio | `/full-rebuild-c1-bio {num}` |
| `full-rebuild-c1-hist` | c1-hist | `/full-rebuild-c1-hist {num}` |
| `full-rebuild-b2-hist` | b2-hist | `/full-rebuild-b2-hist {num}` |
| `full-rebuild-lit` | lit (generic) | `/full-rebuild-lit {num}` |
| `full-rebuild-lit-*` | lit sub-genres | `/full-rebuild-lit-{genre} {num}` |
| `full-rebuild-oes` | oes | `/full-rebuild-oes {num}` |
| `full-rebuild-ruth` | ruth | `/full-rebuild-ruth {num}` |

### Gemini Output Handling

Gemini outputs verbose thinking tokens (10-100K chars). All structured output uses `===TAG_START===` / `===TAG_END===` delimiters. Content outside delimiters is noise. Extraction utility: `scripts/gemini_output.py`.

---

## Orchestrated Rebuild (Claude → Gemini)

**`/orchestrate-rebuild {track} {num}`** — Claude orchestrates phase-by-phase, Gemini executes. Claude validates between phases and writes all files. Shared filesystem is data transport; `ask-gemini` dispatches each phase. Full details: `claude_extensions/commands/orchestrate-rebuild.md`

---

## Anti-Gaming Architecture (Review Integrity)

<critical>

**RULE: An LLM must NEVER review its own work.** Self-review produces inflated scores — this was observed and confirmed in production. Gemini writing content then reviewing it gave 9.9/10 scores with language like "ensuring a high score" and "reflecting the fixes made."

### Three-Layer Defense

**Layer 1 — Architectural (batch runner, `scripts/batch_gemini_runner.py`):**
- In fix mode, review scores DO NOT determine pass/fail
- The 5 automated content gates (meta, lesson, activities, vocabulary, naturalness) are the quality check
- When all content gates pass → module is "done" regardless of review gate
- Phase 5 (review) is only generated to produce a Fix Plan when content gates fail
- `_diagnose_module()` ignores the review gate entirely

**Layer 2 — Automated detection (`scripts/audit/checks/review_validation.py`):**
- `GAMING_LANGUAGE_DETECTED` (critical) — catches "ensuring a high score", "reflecting the fixes", "designed to pass"
- `SUSPICIOUSLY_HIGH_SCORES` (warning) — all dimensions ≥ 9/10 with no substantive issues
- `PRAISE_ONLY_CITATIONS` (warning) — all Ukrainian quotes used positively, none highlighting problems
- `FABRICATED_CITATIONS` (critical) — quoted text not found in source module
- `RUBBER_STAMP_REVIEW` (critical) — all 10/10 with no evidence
- `EMPTY_ISSUES_SECTION` (warning) — claims zero issues (no module is perfect)

**Layer 3 — Prompt-level (`claude_extensions/phases/gemini/phase-5-review.md`):**
- Explicitly states automated detection is active
- Lists what triggers rejection
- States review scores don't affect pass/fail — removes incentive to inflate
- "Be the skeptic. Find real problems. That is your only purpose."

### When Reviews ARE Valid

Reviews are valuable when done by a **different agent** than the content author:
- Claude reviews Gemini's content → valid (via `/review-content`)
- Gemini reviews Claude's content → valid
- Gemini reviews Gemini's own content → **INVALID (self-grading)**
- Automated audit gates → always valid (no LLM bias)

### Key Principle

**Remove the incentive, don't rely on promises.** Prompt-level rules ("be honest", "adversarial reviewer persona") don't work against self-grading bias. Architectural separation does — when review scores don't affect outcomes, there's no reason to game them.

</critical>

---

## Work Dispatch (GitHub Labels)

**Labels are the API. Issues are the database. No static priority files.**

### Label Taxonomy

| Prefix | Labels | Purpose |
|--------|--------|---------|
| `priority:` | `blocking`, `high` | Urgency (no label = normal) |
| `area:` | `infra`, `tooling`, `content`, `docs` | What kind of work |
| `working:` | `claude`, `gemini` | Who's actively working (no label = unclaimed) |
| `review:` | `gemini`, `human` | Ready for review |
| `agent:` | `claude`, `gemini` | Preferred assignee |

### Dispatch Queries

```bash
# Critical blockers
gh issue list --label priority:blocking --state open

# High-priority infra
gh issue list --label priority:high --label area:infra --state open

# Unclaimed work (no working:* label)
gh issue list --state open --json number,title,labels \
  --jq '[.[] | select(.labels | map(.name) | all(startswith("working:") | not))] | .[:10]'

# My area (content work not claimed)
gh issue list --label area:content --state open --json number,title,labels \
  --jq '[.[] | select(.labels | map(.name) | all(startswith("working:") | not))]'
```

### Agent Claim Protocol

**Agents NEVER self-assign. Only the user or orchestrator assigns work.**

When starting work on an issue:
```bash
gh issue edit {N} --add-label "working:claude"
gh issue comment {N} --body "Starting work"
```

When done:
```bash
gh issue edit {N} --remove-label "working:claude"
# Then either:
gh issue edit {N} --add-label "review:human"   # Needs human review
gh issue edit {N} --add-label "review:gemini"   # Needs Gemini review
gh issue close {N}                              # Done, no review needed
```

---

## Task Workflow (GitHub Issues)

Use `/task` commands for complex multi-step or cross-agent work. **Handoff pattern:** issue is source of truth — keep broker messages SHORT (issue reference only, < 200 chars). Full docs: `docs/TASK-WORKFLOW.md`

---

## Track Scoring

Automated, deterministic 10/10 scoring (no LLM calls). Commands in Quick Commands above. Full docs: `scripts/scoring/README.md`

---

## Common Failure Modes (Checklist)

- **Outline compliance**: Create EVERY subsection from `plan.content_outline` — #1 cause of audit failures
- **Word count shortfalls**: Run word count during generation; expand explanations/examples to meet target
- **Activity gaps**: Check `MODULE-RICHNESS-GUIDELINES-v2.md` for minimum counts per concept
- **Checkpoint confusion**: Checkpoints test ALL prior modules in phase (TTT approach), not just one

### Ukrainian Quality Standards

- No Russianisms (кушать→їсти, приймати участь→брати участь)
- No calques (робити сенс→мати сенс, брати місце→відбуватися)
- Case agreement, verb aspects, gender agreement must be perfect
- This is for a nation's education — accept nothing less than native quality

---
