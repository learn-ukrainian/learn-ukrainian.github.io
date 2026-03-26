# CLAUDE.md - Project Instructions

> **Mission**: We are building something that doesn't exist — a full Ukrainian language curriculum with decolonized pedagogy, real textbook grounding, RAG-verified vocabulary, and adversarial review. This is a one-of-a-kind project for a great hero nation. Every shortcut degrades what makes it special. Quality is non-negotiable.

> **ALWAYS look for the source of the problem first.** Don't fix symptoms — trace the root cause, understand why it happens, then fix that.

> **BEHAVIORAL RULES** are in `memory/MEMORY.md` — enforced every session. Key: finish the job (no tech debt), stop asking (just do it), test before shipping, use tracking docs, no quality shortcuts, investigate before coding, be honest.

> **NON-NEGOTIABLE RULES** in `.claude/rules/non-negotiable-rules.md` — word count targets are MINIMUMS, all audit gates must pass, no shortcuts.

> **Status**: `curriculum/l2-uk-en/{level}/status/{slug}.json` | Update: `.venv/bin/python scripts/audit_module.py {path}`

> **Cross-session Memory**: Built-in auto-memory at `~/.claude/projects/.../memory/MEMORY.md`. Inter-agent comms via `scripts/ai_agent_bridge/__main__.py` (not MCP).

> **Default subagent**: Always use `subagent_type: "curriculum-maintainer"` when spawning agents for curriculum work.

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

## Reference Docs

- **Commands & scripts**: [`docs/SCRIPTS.md`](docs/SCRIPTS.md)
- **Project structure & tracks**: [`docs/best-practices/track-architecture.md`](docs/best-practices/track-architecture.md)
- **Monitoring API**: [`docs/MONITOR-API.md`](docs/MONITOR-API.md)
- **Workstreams & priorities**: [`docs/WORKSTREAMS.md`](docs/WORKSTREAMS.md)
- **Module manifest**: `curriculum/l2-uk-en/curriculum.yaml` — source of truth for module ordering and slug mapping
- **Build pipeline**: `.venv/bin/python scripts/build/v6_build.py {level} {num} [--step {step}] [--writer {gemini|claude}]`

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

### Claude Code Power Features

| Feature | How | When |
|---------|-----|------|
| `/effort` | Set model effort dynamically mid-session | `low`: config/typo fixes. `medium`: code fixes (default). `high`: content review, plan review, module building, linguistic analysis |
| Transcript search | `Ctrl+O` then `/` to search, `n`/`N` to navigate | Finding previous discussions in long sessions |
| `--bare` flag | `claude -p "..." --bare` | Scripted calls (agent bridge) — skips hooks/LSP/plugins for speed |
| `worktree.sparsePaths` | Configured in settings.json | Subagent worktrees exclude `node_modules/`, `data/` for speed |
| `PostCompact` hook | Auto-runs after context compaction | Restores current task, open issues, key reminders |
| `FileChanged` hook | Auto-runs when `curriculum/**/*.md` changes | Triggers audit on module file edits |
| `effort: high` on skills | Frontmatter in review skills | `content-review`, `plan-review`, `plan-review-seminar`, `batch-review`, `prompt-review` |
| `paths:` scoping on rules | Frontmatter in rule files | `ukrainian-linguistics.md` only active for curriculum/orchestration work |
