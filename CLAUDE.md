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

> **Cross-session Memory (MCP):**
> - Memory server: `@modelcontextprotocol/server-memory` — active after Claude Code restart
> - Storage: `tasks/memory.json` (local knowledge graph)
> - At session start: query memory + Gemini inbox before starting work
> - At session end: save progress summary to memory
> - Tools: `mcp__memory__search_nodes`, `mcp__memory__add_observations`, `mcp__memory__create_entities`

---

## Best Practices Reference

Detailed standards live in `docs/best-practices/`. Read the relevant doc before working in that area.

| Topic | Doc |
|-------|-----|
| Prompt engineering (templates, delimiters, friction) | [`docs/best-practices/prompt-engineering.md`](docs/best-practices/prompt-engineering.md) |
| Context engineering (research, track context, meta health) | [`docs/best-practices/context-engineering.md`](docs/best-practices/context-engineering.md) |
| Code quality (venv, CLI tools, error handling, state) | [`docs/best-practices/code-quality.md`](docs/best-practices/code-quality.md) |
| Module content quality (Ukrainian standards, richness, immersion) | [`docs/best-practices/module-content-quality.md`](docs/best-practices/module-content-quality.md) |
| Agent cooperation (Blue/Gold teams, anti-self-review, comms) | [`docs/best-practices/agent-cooperation.md`](docs/best-practices/agent-cooperation.md) |
| Issue tracking (labels, issue hygiene, cross-session memory) | [`docs/best-practices/issue-tracking.md`](docs/best-practices/issue-tracking.md) |
| Gitflow (commit discipline, message format, what to commit) | [`docs/best-practices/gitflow.md`](docs/best-practices/gitflow.md) |
| Audit standards (gates, thresholds, anti-gaming detection) | [`docs/best-practices/audit-standards.md`](docs/best-practices/audit-standards.md) |
| Vocabulary & activity standards (YAML format, counts, types) | [`docs/best-practices/vocabulary-activity-standards.md`](docs/best-practices/vocabulary-activity-standards.md) |
| Track & level architecture (pedagogy, build chain, CEFR) | [`docs/best-practices/track-architecture.md`](docs/best-practices/track-architecture.md) |

---

## Intellectual Independence

**The user explicitly wants pushback. Do not rubber-stamp ideas.**

- **Challenge bad ideas directly.** If a proposal seems wrong, say so and explain why — don't silently comply then fix it later.
- **Think independently.** Consider second-order effects, edge cases, and alternatives before agreeing.
- **Be brutally honest.** Hedging ("that could work, but...") is fine; false agreement is not.
- **Disagree on substance, not tone.** Push back when you have a real reason. Don't reflexively second-guess obvious decisions — that's noise. Challenge when it matters.
- **Propose the better approach.** When you disagree, come with an alternative, not just a veto.

Examples of when to push back:
- User wants to lower a word target instead of expanding thin content → refuse, explain why it's the wrong fix
- User suggests manual fix instead of automated check → redirect to the scalable solution
- User proposes an API design that will be painful to use → say so and suggest a cleaner shape

---

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
- Use labels (`area:infra`, `area:content`, `priority:high`, `working:claude`)
- Reference issues in commits (e.g., "Fixes #582")

**This expands your memory across sessions. If it's not in a GH issue, it didn't happen.**

→ Full protocol: [`docs/best-practices/issue-tracking.md`](docs/best-practices/issue-tracking.md)

### 9. Anti-Gaming (Review Integrity)

**An LLM must NEVER review its own work.** Self-review produces inflated scores.

- Automated content gates (word count, outline, activities, vocabulary, naturalness) determine pass/fail
- Review gate (Phase D/6) is adversarial feedback only — does NOT block pass
- When review scores don't affect outcomes, there's no incentive to inflate them

→ Full detection rules and thresholds: [`docs/best-practices/audit-standards.md`](docs/best-practices/audit-standards.md)

</critical>

---

## Activity YAML Rules (Critical)

<critical>

YAML files must be a **bare list at root**, NOT wrapped in `activities:`:
```yaml
# CORRECT - bare list
- type: quiz
  title: ...

# WRONG - dictionary wrapper
activities:
  - type: quiz
```

`mark-the-words` format — use `text` + `answers` array (no asterisks):
```yaml
- type: mark-the-words
  text: Гарний день приніс радість у серце.
  answers:
    - день
    - радість
    - серце
```

→ Full schema reference: [`docs/best-practices/vocabulary-activity-standards.md`](docs/best-practices/vocabulary-activity-standards.md) and `docs/ACTIVITY-YAML-REFERENCE.md`

</critical>

---

## Quick Commands

```bash
# Audit module (saves log automatically)
scripts/audit_module.sh curriculum/l2-uk-en/{level}/{file}.md

# Content-only audit (defer activity/vocab gates)
scripts/audit_module.sh --skip-activities curriculum/l2-uk-en/{level}/{file}.md

# Generate status report
npm run status:{level}  # or: .venv/bin/python scripts/generate_level_status.py {level}

# Track scoring (objective 10/10 verification)
npm run score:b2-hist   # Score B2-HIST track
npm run score:all       # Score all tracks (summary table)

# Deterministic Python builder v3 (hybrid Gemini+Claude — preferred for new builds)
# Gemini: Phase A (research+meta), B (prose). Claude: Phase C (activities), F (final review).
# Model defaults: core tracks → Sonnet; seminar tracks → Opus; Phase F → always Opus.
# All model defaults in scripts/batch_gemini_config.py.
.venv/bin/python scripts/build_module_v3.py {track} {num}                       # Full E2E (4 LLM calls baseline)
.venv/bin/python scripts/build_module_v3.py {track} --all                       # Batch (skips passing)
.venv/bin/python scripts/build_module_v3.py {track} --range 1-20                # Build range
.venv/bin/python scripts/build_module_v3.py {track} --all --research-only       # Pre-seed all research (Phase A only)
.venv/bin/python scripts/build_module_v3.py {track} {num} --rebuild             # Nuke v3 state, restart from Phase A
.venv/bin/python scripts/build_module_v3.py {track} {num} --force-phase B       # Re-run single phase (A/B/C/audit/D/E/F)
.venv/bin/python scripts/build_module_v3.py {track} {num} --no-track-context    # Skip track context injection
.venv/bin/python scripts/build_module_v3.py {track} {num} --final-review        # + Phase F: Claude QA gate
.venv/bin/python scripts/build_module_v3.py {track} {num} --use-claude A        # Phase A via Claude (WebSearch)
.venv/bin/python scripts/build_module_v3.py {track} {num} --use-claude "A C"    # Phases A+C via Claude
.venv/bin/python scripts/build_module_v3.py {track} {num} --claude-model-C claude-opus-4-6   # Override Claude model per phase
.venv/bin/python scripts/build_module_v3.py {track} {num} --claude-model-F claude-sonnet-4-6 # Override Phase F model
# v3 state: state-v3.json (separate from v2's state.json — no conflict)

# Deterministic Python builder v2 (fallback)
.venv/bin/python scripts/build_module_v2.py {track} {num}                  # Full E2E (resume-aware)
.venv/bin/python scripts/build_module_v2.py {track} --all                  # Batch
.venv/bin/python scripts/build_module_v2.py {track} {num} --rebuild        # Nuke ALL state + artifacts
.venv/bin/python scripts/build_module_v2.py {track} {num} --force-phase 3  # Re-run single phase
.venv/bin/python scripts/build_module_v2.py {track} {num} --verify         # Just run audit, PASS/FAIL
.venv/bin/python scripts/build_module_v2.py {track} {num} --final-review   # Phase 9: Claude QA gate

# Pipeline verification (run AFTER Gemini finishes to catch lies)
.venv/bin/python scripts/verify_track.py {track}              # Verify all modules in track
.venv/bin/python scripts/verify_track.py {track} --full       # Require full pass
.venv/bin/python scripts/verify_track.py {track} --quick      # Fast: read cached status

# Gemini skills dispatch
/otaman {track} {num}             # [Gemini] Stage 1: prose only
/hetman {track} {num}             # [Gemini] Stage 2: activities + review
/hetman {track} {num} --full      # [Gemini] Full E2E
/final-review {track} {num}       # [Claude] Final QA after Hetman

# Inter-agent communication
.venv/bin/python scripts/ai_agent_bridge.py ask-gemini "message" --task-id id
.venv/bin/python scripts/ai_agent_bridge.py inbox

# Deploy skill changes
npm run claude:deploy

# Batch Otaman dispatcher
.venv/bin/python scripts/batch_otaman.py run             # Continuous — max 2 parallel sessions
.venv/bin/python scripts/batch_otaman.py scan            # Show track status
```

See `docs/SCRIPTS.md` for complete reference.

---

## Session Start Checklist

> **AT SESSION START:**
> 1. **Load memory** — query what was in progress last session:
>    ```python
>    mcp__memory__search_nodes(query="in progress current session")
>    mcp__memory__search_nodes(query="next session todo")
>    ```
> 2. Check inbox for notifications from Gemini:
>    ```python
>    mcp__message-broker__check_inbox(for_llm="claude")
>    ```
> 3. If unread messages, read them and respond on GitHub
> 4. Begin work based on memory + inbox context

> **AT SESSION END** (or when switching context):
> Update memory with what was done and what's next:
> ```python
> mcp__memory__add_observations(observations=[{
>     "entityName": "current-session",
>     "contents": ["Did: X. In progress: Y. Next session: Z."]
> }])
> ```

---

## Project Structure

```
curriculum/l2-uk-en/
├── plans/                        # LAYER 1: SOURCE OF TRUTH
│   └── {level}/{slug}.yaml       # What to build: objectives, outline, vocab
│
└── {level}/                      # LAYER 2: BUILD ARTIFACTS
    ├── meta/{slug}.yaml          # How to build: pedagogy, duration, grammar
    ├── {num}-{slug}.md           # Content prose
    ├── activities/{slug}.yaml    # Activities (bare list at root)
    ├── vocabulary/{slug}.yaml    # Vocabulary data
    ├── review/{bare_slug}-review.md
    ├── audit/{bare_slug}-audit.md
    └── status/{bare_slug}.json   # LAYER 3: CACHED AUDIT RESULTS
```

**Module counts**: A1 (44), A2 (71), B1 (94), B2 (95), C1 (109), C2 (101)
**Track counts**: B2-HIST (140), C1-BIO (172), C1-HIST (136), B2-PRO (40), C1-PRO (50), LIT (218), OES (100), RUTH (100)

→ Full track architecture and pedagogy models: [`docs/best-practices/track-architecture.md`](docs/best-practices/track-architecture.md)

---

## Monitoring API (http://localhost:8765)

FastAPI server — always running. Use `curl` for instant status instead of running scripts.
Full reference: [`docs/MONITOR-API.md`](docs/MONITOR-API.md)

```bash
# Session start — one call to know project state
curl -s http://localhost:8765/api/state/summary | python3 -m json.tool

# What's building right now
curl -s http://localhost:8765/api/batch/active

# v3 pipeline state for a specific track
curl -s http://localhost:8765/api/state/pipeline/c1-hist | python3 -m json.tool

# What's ready to build next (Phase A done, Phase B not started)
curl -s http://localhost:8765/api/state/ready-to-build | python3 -m json.tool

# Failing/weak modules in a track
curl -s "http://localhost:8765/api/state/weak-points?track=c1-bio" | python3 -m json.tool

# Critical issues across all tracks
curl -s "http://localhost:8765/api/state/issues?severity=critical" | python3 -m json.tool

# Pass/fail all tracks
curl -s http://localhost:8765/api/blue/live-status
```

---

## Inter-Agent Communication

**Gemini is your colleague.** Full protocol: [`docs/best-practices/agent-cooperation.md`](docs/best-practices/agent-cooperation.md)

- 💙 **Blue / Claude** — architect, reviewer, quality gate
- 💛 **Gold / Gemini** — content builder, implementer

**GitHub issues are the primary communication channel.** Bridge messages are SHORT references only (< 200 chars).

```bash
# Dispatch to Gemini (immediate)
.venv/bin/python scripts/ai_agent_bridge.py ask-gemini \
  "Review posted on #559. Please read and respond." --task-id issue-559

# Passive notification (Gemini reads at session start)
mcp__message-broker__send_message(to="gemini", content="FYI: See #559.", from_llm="claude")
```

---

## Workflow Orchestration

### Plan Mode Default

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, **STOP and re-plan immediately** - don't keep pushing

### Task Management Files

| File | Purpose |
|------|---------|
| `tasks/todo.md` | Current session tasks with checkable items |
| `tasks/lessons.md` | Accumulated learnings from corrections |

### Self-Improvement Loop

After ANY correction from the user: update `tasks/lessons.md` with the pattern and a rule to prevent recurrence.

### Core Principles

- **Simplicity First**: Make every change as simple as possible. Minimal code impact.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Verify Before Done**: Never mark a task complete without proving it works. For modules: audit must pass.

---

## Common Failure Modes

- **Outline compliance**: Create EVERY subsection from `plan.content_outline` — #1 cause of audit failures
- **Word count shortfalls**: Expand explanations/examples to meet target — never lower the bar
- **Activity gaps**: Check `MODULE-RICHNESS-GUIDELINES-v2.md` for minimum counts per concept
- **YAML errors**: Strings with colons must be quoted in plan YAML files

→ Full audit thresholds and gate details: [`docs/best-practices/audit-standards.md`](docs/best-practices/audit-standards.md)
→ Ukrainian language quality standards: [`docs/best-practices/module-content-quality.md`](docs/best-practices/module-content-quality.md)
