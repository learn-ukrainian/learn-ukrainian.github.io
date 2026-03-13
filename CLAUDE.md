# CLAUDE.md - Project Instructions

> **Mission**: We are building something that doesn't exist — a full Ukrainian language curriculum with decolonized pedagogy, real textbook grounding, RAG-verified vocabulary, and adversarial review. This is a one-of-a-kind project for a great hero nation. Every shortcut degrades what makes it special. Quality is non-negotiable.

> **ALWAYS look for the source of the problem first.** Don't fix symptoms — trace the root cause, understand why it happens, then fix that.

> **NON-NEGOTIABLE RULES** auto-loaded from `claude_extensions/rules/non-negotiable-rules.md` (deployed to `.claude/rules/`) — word count targets are MINIMUMS, all audit gates must pass, no shortcuts.

> **Status**: `curriculum/l2-uk-en/{level}/status/{slug}.json` | Update: `.venv/bin/python scripts/audit_module.py {path}`

> **Cross-session Memory**: Built-in auto-memory at `~/.claude/projects/.../memory/MEMORY.md`. Inter-agent comms via `scripts/ai_agent_bridge/__main__.py` (not MCP).

---

## How We Work (Mandatory Workflow)

<critical>

Every task follows this workflow. No exceptions for non-trivial changes.

1. **Create GH issue** — describe the problem, draft a plan
2. **Adversarial review of plan** — send to Gemini, incorporate feedback
3. **Finalize ACs** — update issue with concrete acceptance criteria
4. **Implement** — work through ACs one by one
5. **Verify all ACs** — every AC checked and documented on the issue
6. **Adversarial review of implementation** — send code to Gemini, fix findings
7. **Close** — only when all ACs pass and review is clean

**Skip plan review** (step 2) only for trivial changes (< 50 lines, config/typo fixes).

**Adversarial review command** (steps 2 & 6). Always use `--model gemini-3.1-pro-preview`. Document findings on the GH issue.
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Adversarial review for #NNN. Read {path}." \
  --task-id issue-NNN --model gemini-3.1-pro-preview
```

**Why**: GH issues are persistent memory. Without them, context is lost between sessions and work gets repeated or silently broken.

**Issue discipline (coding issues)**:
- **Never leave half-done.** If you open it, finish it. If you can't finish it now, document exactly where you stopped and what remains.
- **Never close unless ALL acceptance criteria are verified.** Partial completion = still open.
- **Aim to fully resolve and close.** Open issues are debt. Minimize them aggressively.
- **The human manages content generation issues.** Claude owns coding/infrastructure issues. But proactively remind when it's time to start building a new track or batch — initiative is welcome.

**Proactive issue hygiene**: At the start of each session, check open coding issues. Prioritize, resolve, close — don't let them go stale.

</critical>

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

**Pipeline v5** (`build_module_v5.py`) — the ONLY pipeline:
- research → discover → content → validate → [review] → activities → mdx
- **v4 and v3 are RETIRED.** Do not use `build_module.py`.
- **Gemini** builds: research, discover, content, activities
- **Claude** reviews: review phase (cross-agent adversarial, max 2 fix attempts)
- **Lexical sandbox**: VESUM-validated word bank (runs inline during content/validate, not a separate phase) — injected via `{LEXICAL_SANDBOX}`
- **Validate**: morphological validator + Russicism detection + agreement checking
- Discover is non-blocking — failures don't halt the pipeline.
- Model defaults: `scripts/batch_gemini_config.py` | Review default: `claude-opus-4-6`
- Build: `.venv/bin/python scripts/build_module_v5.py {track} {num} [--rebuild] [--restart-from {phase}]`

**An LLM must NEVER review its own work.** Gemini builds → Claude reviews. Enforced by `SELF_REVIEW_DETECTED` audit gate.

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

### 3. Language Settings
**English**: all technical work. **Ukrainian**: curriculum content only.

### 4. External LLM Access
Use `gemini-cli` (Google AI Pro subscription). No direct API keys.

### 5. Word Targets Are Minimums
**NEVER** reduce content or change `word_target` to match short content. Expand the content instead.

### 6. GitHub Issues as Persistent Memory
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

## Reference Docs

- **Commands & scripts**: [`docs/SCRIPTS.md`](docs/SCRIPTS.md)
- **Project structure & tracks**: [`docs/best-practices/track-architecture.md`](docs/best-practices/track-architecture.md)
- **Monitoring API**: [`docs/MONITOR-API.md`](docs/MONITOR-API.md)
- **Workstreams & priorities**: [`docs/WORKSTREAMS.md`](docs/WORKSTREAMS.md)
- **Module manifest**: `curriculum/l2-uk-en/curriculum.yaml` — source of truth for module ordering and slug mapping
- **Build pipeline**: `.venv/bin/python scripts/build_module_v5.py {level} {seq} [--review] [--restart-from {phase}] [--force-phase {phase}]`

---

## RAG Tools (MCP)

Ukrainian language verification and textbook content search:
- `mcp__rag__verify_word` / `mcp__rag__verify_lemma` — VESUM morphological dictionary (415K lemmas)
- `mcp__rag__search_text` — textbook content search (1.2K+ chunks)
- `mcp__rag__search_images` — textbook image search (10K+ images)
- `mcp__rag__search_literary` — primary literary sources (chronicles, poetry, legal texts)

---

## Tracks

- **l2-uk-en**: Ukrainian for English speakers (A1→C2 + seminars). Main track.
- **l2-uk-direct**: L1-agnostic Ukrainian (A1→B2). Separate schemas, no English. See `docs/l2-uk-direct/`.

---

## Inter-Agent Communication

**Gemini is your colleague.** Claude = architect/reviewer, Gemini = content builder. Full protocol: [`agent-cooperation.md`](docs/best-practices/agent-cooperation.md)

---

## Workflow

- **Plan mode** for any non-trivial task (3+ steps or architectural decisions)
- **Simplicity first**: minimal code impact, find root causes, verify before done
