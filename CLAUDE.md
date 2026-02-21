# CLAUDE.md - Project Instructions

> **READ FIRST: `claude_extensions/NON-NEGOTIABLE-RULES.md`** — word count targets are MINIMUMS, all audit gates must pass, no shortcuts.

> **Status**: `curriculum/l2-uk-en/{level}/status/{slug}.json` | View: `/module-status {level} {num}` | Update: `.venv/bin/python scripts/audit_module.py {path}`

> **Cross-session Memory** (MCP `memory` server): `mcp__memory__search_nodes`, `mcp__memory__create_entities`, `mcp__memory__add_observations` | Storage: `tasks/memory.json` | NOT the same as `mcp__message-broker__*` (that's for Gemini comms)

---

## Best Practices Reference

Detailed standards in `docs/best-practices/`. Read the relevant doc before working in that area.

| Topic | Doc |
|-------|-----|
| Prompt engineering | [`prompt-engineering.md`](docs/best-practices/prompt-engineering.md) |
| Context engineering | [`context-engineering.md`](docs/best-practices/context-engineering.md) |
| Code quality | [`code-quality.md`](docs/best-practices/code-quality.md) |
| Module content quality | [`module-content-quality.md`](docs/best-practices/module-content-quality.md) |
| Agent cooperation | [`agent-cooperation.md`](docs/best-practices/agent-cooperation.md) |
| Issue tracking | [`issue-tracking.md`](docs/best-practices/issue-tracking.md) |
| Gitflow | [`gitflow.md`](docs/best-practices/gitflow.md) |
| Audit standards | [`audit-standards.md`](docs/best-practices/audit-standards.md) |
| Vocabulary & activities | [`vocabulary-activity-standards.md`](docs/best-practices/vocabulary-activity-standards.md) |
| Track architecture | [`track-architecture.md`](docs/best-practices/track-architecture.md) |

---

## Intellectual Independence

**The user explicitly wants pushback. Do not rubber-stamp ideas.**

- Challenge bad ideas directly — don't silently comply then fix later
- Think independently — consider second-order effects and alternatives before agreeing
- Propose the better approach when you disagree, not just a veto
- Push back when it matters; don't reflexively second-guess obvious decisions

---

## Pipeline Architecture

<critical>

**Cross-agent build pipeline (v3):**
- **Gemini** builds: Phase A (research+meta), Phase B (prose), Phase C (activities+vocab)
- **Claude** reviews: Phase D (cross-agent adversarial review, max 3 attempts)
- **Phase F** (optional): final QA gate, agent-selectable (`--final-review-agent claude|gemini`)
- Phase D exhaustion = module marked `needs-rebuild` (no escalation back to Gemini)
- Model defaults: `scripts/batch_gemini_config.py` | Phase D default: `claude-opus-4-6`

**An LLM must NEVER review its own work.** Gemini builds → Claude reviews. Enforced by `SELF_REVIEW_DETECTED` audit gate.

</critical>

---

## Adversarial Review Protocol

<critical>

**Before implementing non-trivial features:** send plan to Gemini Pro for adversarial review. After implementation, send code for post-implementation review. Always use `--model gemini-3.1-pro-preview`. Document on the GH issue.

```bash
.venv/bin/python scripts/ai_agent_bridge.py ask-gemini \
  "Adversarial review for #NNN. Read {path}." \
  --task-id issue-NNN --model gemini-3.1-pro-preview
```

</critical>

---

## Critical Rules

<critical>

### 1. Work in `claude_extensions/` First
**NEVER** edit `.claude/`, `.agent/`, `.gemini/` directly. Edit in `claude_extensions/`, run `npm run claude:deploy` to sync.

### 2. Use Python venv
**ALWAYS** `.venv/bin/python`, **NEVER** `python3` or `python` directly.
- pyenv Python 3.12.8 with `--enable-loadable-sqlite-extensions`
- Recreate: `rm -rf .venv && ~/.pyenv/versions/3.12.8/bin/python -m venv .venv`

### 3. Fix Source, Not Symptoms
Fix documentation/tools first, then validate. Ask: what process caused this? How to prevent recurrence?

### 4. Language Settings
**English**: all technical work. **Ukrainian**: curriculum content only.

### 5. External LLM Access
Use `gemini-cli` (Google AI Pro subscription). No direct API keys.

### 6. Word Targets Are Minimums
**NEVER** reduce content or change `word_target` to match short content. Expand the content instead.

### 7. GitHub Issues as Persistent Memory
Every change tracked via GH issues. Before work: find/create issue. After: update/close. Reference in commits. Full protocol: [`issue-tracking.md`](docs/best-practices/issue-tracking.md)

</critical>

---

## Activity YAML Rules

<critical>

Bare list at root (NOT `activities:` wrapper). Full schema: [`vocabulary-activity-standards.md`](docs/best-practices/vocabulary-activity-standards.md) and `docs/ACTIVITY-YAML-REFERENCE.md`

```yaml
# CORRECT                    # WRONG
- type: quiz                 activities:
  title: ...                   - type: quiz
```

</critical>

---

## Quick Commands

```bash
# Build (v3 — preferred)
.venv/bin/python scripts/build_module_v3.py {track} {num}          # Full E2E
.venv/bin/python scripts/build_module_v3.py {track} --all          # Batch (skips passing)
.venv/bin/python scripts/build_module_v3.py {track} {num} --rebuild              # Nuke + restart
.venv/bin/python scripts/build_module_v3.py {track} {num} --force-phase B        # Re-run single phase
.venv/bin/python scripts/build_module_v3.py {track} {num} --final-review         # + Phase F QA gate

# Audit
scripts/audit_module.sh curriculum/l2-uk-en/{level}/{file}.md      # With log
scripts/audit_module.sh --skip-activities {path}                   # Content-only

# Verify track
.venv/bin/python scripts/verify_track.py {track} --full

# Deploy skill changes
npm run claude:deploy
```

See `docs/SCRIPTS.md` for complete reference (v2 fallback, model overrides, batch dispatch, scoring).

---

## Session Checklist

**Start:** `curl -s http://localhost:8765/api/state/summary | python3 -m json.tool` → load memory (`mcp__memory__search_nodes`) → check Gemini inbox (`mcp__message-broker__check_inbox`)

**End:** Save session to memory graph → optionally run `scripts/session_end.sh`

---

## Project Structure

```
curriculum/l2-uk-en/
├── plans/{level}/{slug}.yaml          # SOURCE OF TRUTH (what to build)
└── {level}/
    ├── meta/{slug}.yaml               # Build config (pedagogy, duration)
    ├── {slug}.md                      # Content prose
    ├── activities/{slug}.yaml         # Activities (bare list)
    ├── vocabulary/{slug}.yaml         # Vocabulary
    ├── review/{slug}-review.md        # Phase D review
    ├── audit/{slug}-audit.md          # Audit report
    └── status/{slug}.json             # Cached audit results
```

**Core levels**: A1 (44), A2 (71), B1 (94), B2 (95), C1 (109), C2 (101)
**Tracks**: B2-HIST (140), C1-BIO (172), C1-HIST (136), B2-PRO (40), C1-PRO (50), LIT (218), OES (100), RUTH (100)

---

## Monitoring API

FastAPI at `http://localhost:8765`. Full reference: [`docs/MONITOR-API.md`](docs/MONITOR-API.md)

```bash
curl -s http://localhost:8765/api/state/summary | python3 -m json.tool    # Project overview
curl -s http://localhost:8765/api/state/module/a1/9 | python3 -m json.tool # Module deep-dive
curl -s http://localhost:8765/api/blue/live-status                         # Pass/fail all tracks
```

---

## Inter-Agent Communication

**Gemini is your colleague.** Full protocol: [`agent-cooperation.md`](docs/best-practices/agent-cooperation.md)

- Claude = architect, reviewer, quality gate | Gemini = content builder
- GitHub issues are primary channel. Bridge messages < 200 chars.

```bash
.venv/bin/python scripts/ai_agent_bridge.py ask-gemini "See #559." --task-id issue-559
```

---

## Workflow

- **Plan mode** for any non-trivial task (3+ steps or architectural decisions)
- **Self-improvement**: after any user correction, update `tasks/lessons.md`
- **Simplicity first**: minimal code impact, find root causes, verify before done
