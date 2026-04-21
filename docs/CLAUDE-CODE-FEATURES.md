# Claude Code Features Reference

> Complete inventory of how this project uses Claude Code. Updated 2026-03-26.

---

## Hooks (5 active)

Hooks run automatically on specific events. Configured in `claude_extensions/settings.json`.

| Event | Hook script | Timeout | What it does |
|-------|------------|---------|--------------|
| **SessionStart** | `session-setup.sh` | 10s | Validates environment: venv, env vars, MCP sources server, gemini-cli auth, stale builds, MEMORY.md line count, deploy drift, open GH issues |
| **PreToolUse** (Bash) | `enforce-venv.sh` | 3s | Rewrites bare `python3`/`python` → `.venv/bin/python` before every Bash call |
| **UserPromptSubmit** | `check-gemini-inbox.sh` | 5s | Checks message broker DB for unread Gemini messages, injects alert |
| **PostCompact** | `post-compact.sh` | 10s | After context compaction: restores in-progress modules, open issues, key reminders |
| **FileChanged** (`curriculum/l2-uk-en/**/*.md`) | `auto-audit.sh` | 30s | Auto-runs `audit_module.py` on changed curriculum files (skips orchestration/audit/review) |

All hooks skip in non-interactive mode (`CLAUDE_NON_INTERACTIVE`, `LEARN_UKRAINIAN_PIPELINE`, `GEMINI_SESSION`).

---

## Agent

**curriculum-maintainer** — the default agent for all subagent work.

| Setting | Value |
|---------|-------|
| Tools | `*` (all) |
| Model | `inherit` |
| Initial prompt | Auto-fetches: Monitor API summary, failing modules, open GH issues |

Spawned with `subagent_type: "curriculum-maintainer"`. The `initialPrompt` means every subagent starts with project context automatically.

---

## Skills (6)

All review/analysis skills have `effort: xhigh` — forces deep analysis on Opus 4.7. (Bumped from `high` → `xhigh` on 2026-04-21 after Anthropic noted Opus 4.7 at `high` underperforms prior versions. The 2026-04-06 removal of `effort: high` for token savings was reversed — reviews are where pedagogy quality lives, so cost is justified.)

| Skill | Purpose | Effort |
|-------|---------|--------|
| `/content-review` | Post-build quality review (plan adherence, linguistics, activities) | xhigh |
| `/plan-review` | Review core plans (A1-C2, PRO) using State Standard + textbook RAG + VESUM | xhigh |
| `/plan-review-seminar` | Review seminar plans (HIST, BIO, LIT, etc.) using Wikipedia + Literary RAG | xhigh |
| `/batch-review` | Parallel review across module ranges using subagents | xhigh |
| `/prompt-review` | Find prompt/context engineering problems in orchestration folders | xhigh |
| `/apply-plan-fixes` | Apply fixes from plan review reports with approval workflow | default |

---

## Rules (7)

Rules inject constraints into the agent's context. Some are scoped to specific paths.

| Rule | Scoped to | Always active? |
|------|-----------|----------------|
| `critical-rules.md` | — | Yes |
| `non-negotiable-rules.md` | — | Yes |
| `workflow.md` | — | Yes |
| `pipeline.md` | `scripts/build/**`, `scripts/pipeline/**`, `scripts/audit/**`, `scripts/validate/**`, `curriculum/**/orchestration/**` | Only in pipeline work |
| `activity-yaml.md` | `curriculum/**/*.yaml`, `curriculum/**/*.yml`, `scripts/yaml_activities.py`, `scripts/generate_mdx/**` | Only in activity/YAML work |
| `rag-and-dictionaries.md` | `scripts/**`, `curriculum/**`, `data/**` | Only in curriculum/script work |
| `ukrainian-linguistics.md` | `curriculum/**`, `orchestration/**`, `docs/l2-*/**`, `plans/**` | Only in curriculum/content work |

The `paths:` frontmatter means linguistics rules don't activate when doing pure infrastructure/Python work — saves context.

---

## Settings

### Worktree (for subagents)

```json
"worktree": {
  "sparsePaths": [
    "curriculum/", "scripts/", "docs/", "orchestration/", "plans/",
    "starlight/src/", "claude_extensions/", ".claude/",
    "*.md", "*.yaml", "*.yml", "*.json", "*.py"
  ]
}
```

Subagent worktrees get only the files they need — no `node_modules/`, no `data/`. Much faster clone.

### Other settings

| Setting | Value | Why |
|---------|-------|-----|
| `plansDirectory` | `docs/plans` | Plan mode saves to this directory |
| `respectGitignore` | `true` | Don't index gitignored files |
| `agent` | `curriculum-maintainer` | Default agent for the project |
| `acceptEdits` | `true` | Auto-apply edits |
| `yolo` | `true` | Less confirmation prompts |

---

## Slash Commands (built-in)

| Command | When to use |
|---------|-------------|
| `/effort low` | Config changes, typo fixes, file moves |
| `/effort medium` | Code fixes, script updates (default) |
| `/effort high` | Content review, plan review, module building, linguistic analysis |
| `/simplify` | Review changed code for quality — part of pre-commit checklist |

---

## Keyboard Shortcuts

| Shortcut | What |
|----------|------|
| `Ctrl+O` then `/` | **Transcript search** — find previous discussions in long sessions. `n`/`N` to navigate matches. |
| `Ctrl+X Ctrl+E` or `Ctrl+G` | Open external editor for multiline input |
| `Esc` | Cancel current generation |

---

## Deployment Workflow

```
claude_extensions/  ──npm run claude:deploy──►  .claude/ + .agent/
```

1. **Always edit in `claude_extensions/`** — never `.claude/` directly
2. Run `npm run claude:deploy` — lints prompts, shows diff, syncs via rsync
3. Deploy syncs to both `.claude/` (Claude Code) and `.agent/` (Gemini)
4. `session-setup.sh` detects drift and warns if out of sync

---

## MCP Servers

| Server | Port | Purpose |
|--------|------|---------|
| **RAG** | 8766 | VESUM, textbooks, literary sources, dictionaries, Wikipedia |
| **Message Broker** | SQLite (no port) | Claude ↔ Gemini async messaging via `.mcp/servers/message-broker/messages.db` |

Start RAG: `cd .mcp/servers/sources && .venv/bin/python server.py`
Start all services: `./services.sh start`

---

## Agent Bridge (`--bare` optimization)

The `scripts/ai_agent_bridge/_claude.py` uses `--bare` flag for scripted Claude CLI calls when `ANTHROPIC_API_KEY` is set. This skips hooks, LSP, plugin sync, and skill walks — significantly faster for non-interactive calls.

| Condition | Mode |
|-----------|------|
| `ANTHROPIC_API_KEY` set, no session resume | `--bare` (fast) |
| No API key, or resuming session | Normal (full context) |

---

## Phases & Templates

`claude_extensions/phases/` contains 65+ Gemini prompt templates used by the V6 build pipeline:

| Directory | Count | Purpose |
|-----------|-------|---------|
| `calibration/` | 14 | Level-specific calibration (a1, a2, b1, ..., hist, bio, etc.) |
| `claude/` | 1 | `direct-review.md` — Claude's review phase |
| `gemini/` | 65+ | Research, content, activities, fixes, reviews, shared rules |

Shared rules (prefixed `_shared-`) apply across phases: activity rules, content rules, preflight checks, quality dimensions, self-audit.

---

## Quick Reference Docs

`claude_extensions/quick-ref/` — 22 reference documents injected into prompts:

- **By level**: a1, a2, b1, b2, c1, c2
- **By track**: b2-hist, b2-pro, c1-bio, c1-hist, c1-pro, FOLK, LIT, OES, RUTH
- **Technical**: ACTIVITY-SCHEMAS, monitor-api, error-correction-extended, literary-rag

---

## Consultation Queue

`claude_extensions/consultation-queue/` — template change proposals.

When the pipeline's `--consult` flag detects a template-level issue affecting all modules, it writes a YAML proposal here. Human reviews, approves → applies to template, or rejects → deletes file.

---

## Summary: Event Flow

```
Session starts
  └── session-setup.sh → validates env, shows issues

User types message
  └── check-gemini-inbox.sh → alerts on unread Gemini messages

Claude runs Bash command
  └── enforce-venv.sh → rewrites python → .venv/bin/python

Curriculum .md file changes
  └── auto-audit.sh → runs audit_module.py

Context gets compacted (long session)
  └── post-compact.sh → restores modules, issues, reminders

Subagent spawned
  └── curriculum-maintainer initialPrompt → fetches project state
  └── worktree.sparsePaths → fast sparse clone (no node_modules)

Review skill invoked
  └── effort: xhigh → deep analysis mode (Opus 4.7 needs xhigh, not high)
  └── paths: scoping → only relevant rules loaded
```
