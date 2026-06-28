# CLAUDE.md - Project Instructions

> **Provider boundary:** Shared repository invariants live in `AGENTS.md`. Claude agents should read `AGENTS.md` plus this Claude-specific file; Codex prompts should not read this file as runtime instructions. Defer shared rules here instead of duplicating stale copies.

> **Mission**: We are building something that doesn't exist — a full Ukrainian language curriculum with decolonized pedagogy, real textbook grounding, RAG-verified vocabulary, and adversarial review. This is a one-of-a-kind project for a great hero nation. Every shortcut degrades what makes it special. Quality is non-negotiable.

> **ALWAYS aim for and research best-practice solutions and practices.** Before implementing or deciding, actively seek the established best practice — web-research current standards, read `docs/best-practices/`, check prior art and idiomatic patterns, consult authoritative sources. Never settle for the first thing that works; choose the well-supported, proven, state-of-the-art approach. This applies to code, pedagogy, linguistics, architecture, and process alike.

> **Project policy — non-commercial, permanent**: This project will not be commercialized. It is and will remain a free, open-source educational resource. Decision recorded 2026-04-19. Implication: dependencies under non-commercial licenses (CC BY-NC, RAIL-NC, etc.) are acceptable as long as the project's non-commercial posture is maintained. No "we might monetize someday" hedging.

> **ALWAYS look for the source of the problem first.** Don't fix symptoms — trace the root cause, understand why it happens, then fix that.

> **BEHAVIORAL RULES** are in `memory/MEMORY.md` — enforced every session. Key: finish the job (no tech debt), stop asking (just do it), test before shipping, use tracking docs, no quality shortcuts, investigate before coding, be honest.

> **NON-NEGOTIABLE RULES** in `.claude/rules/non-negotiable-rules.md` — word count targets are MINIMUMS, all audit gates must pass, no shortcuts.

> **Status**: `curriculum/l2-uk-en/{level}/status/{slug}.json` | Update: `.venv/bin/python scripts/audit_module.py {path}`

> **Cross-session Memory**: Built-in auto-memory at `~/.claude/projects/.../memory/MEMORY.md`. Inter-agent comms via `.venv/bin/python scripts/ai_agent_bridge/__main__.py`; Headroom is also available as the `headroom` MCP server for compressed handoffs, retrieval, stats, and shared proxy memory. Gemini-family work routes through AGY, not Gemini CLI or Gemini Code Assist; see `docs/guardrails/agent-fleet-tooling.md`.

> **Default subagent**: Always use `subagent_type: "curriculum-orchestrator"` when spawning agents for curriculum orchestration work.

---

## Best Practices Reference

Detailed standards in `docs/best-practices/`. Read the relevant doc before working in that area.

| Topic | Doc |
| --- | --- |
| **V7 design + corpus (READ FIRST before any module / writer-prompt work)** | [`v7-design-and-corpus.md`](docs/best-practices/v7-design-and-corpus.md) |
| **ULP presentation pattern (READ before any A1/A2 build — Anna Ohoiko's 7 practices + S1→S6 progression)** | [`ulp-presentation-pattern.md`](docs/best-practices/ulp-presentation-pattern.md) |
| Prompt engineering | [`prompt-engineering.md`](docs/best-practices/prompt-engineering.md) |
| Context engineering | [`context-engineering.md`](docs/best-practices/context-engineering.md) |
| Code quality | [`code-quality.md`](docs/best-practices/code-quality.md) |
| Module content quality | [`module-content-quality.md`](docs/best-practices/module-content-quality.md) |
| Agent cooperation | [`agent-cooperation.md`](docs/best-practices/agent-cooperation.md) |
| Issue tracking | [`issue-tracking.md`](docs/best-practices/issue-tracking.md) |
| Gitflow | [`gitflow.md`](docs/best-practices/gitflow.md) |
| Git hygiene (dirty-tree policy) | [`git-hygiene.md`](docs/best-practices/git-hygiene.md) |
| Audit standards | [`audit-standards.md`](docs/best-practices/audit-standards.md) |
| Vocabulary & activities | [`vocabulary-activity-standards.md`](docs/best-practices/vocabulary-activity-standards.md) |
| Activity pedagogy (level→type matrix) | [`activity-pedagogy.md`](docs/best-practices/activity-pedagogy.md) |
| Track architecture | [`track-architecture.md`](docs/best-practices/track-architecture.md) |
| Harness engineering | [`harness-engineering.md`](docs/best-practices/harness-engineering.md) |
| Dialogue situations | [`dialogue-situations.md`](docs/best-practices/dialogue-situations.md) |

---

## Reference Docs

- **Corpus inventory (what source material we have)**: [`docs/corpus-inventory.md`](docs/corpus-inventory.md) — `data/sources.db` tables + live counts, literary breakdown, the local-vs-GoogleDrive build architecture, and the safe recipe to add content. READ before asking the user for material or deciding to scrape.
- **Commands & scripts**: [`docs/SCRIPTS.md`](docs/SCRIPTS.md)
- **Agent runtime**: [`docs/agent-runtime-guide.md`](docs/agent-runtime-guide.md) — universal adapter layer for all agent CLI invocations. READ BEFORE touching `scripts/agent_runtime/`.
- **Project structure & tracks**: [`docs/best-practices/track-architecture.md`](docs/best-practices/track-architecture.md)
- **Monitoring API**: [`docs/MONITOR-API.md`](docs/MONITOR-API.md)
- **Workstreams & priorities**: [`docs/WORKSTREAMS.md`](docs/WORKSTREAMS.md)
- **Module manifest**: `curriculum/l2-uk-en/curriculum.yaml` — source of truth for module ordering and slug mapping
- **Build pipeline**: `.venv/bin/python scripts/build/v7_build.py {level} {slug} --worktree [--writer {claude-tools|gemini-tools|codex-tools}]`
- **Decision journal**: [`docs/decisions/`](docs/decisions/) — architectural decisions with expiry dates. Check: `.venv/bin/python scripts/check_decisions.py`

---

## Tracks

- **l2-uk-en**: Ukrainian for English speakers (A1→C2 + seminars). Main track.
- **l2-uk-direct**: L1-agnostic Ukrainian (A1→B2). Separate schemas, no English. See `docs/l2-uk-direct/`.

---

## Inter-Agent Communication

For shared delegation, artifact hygiene, Python invocation, worktree layout, commit trailers, and independent review routing, defer to `AGENTS.md`. Independent review must not be self-review, and internal GPT helper swarms do not satisfy the external gate. Current external lanes: Hermes -> DeepSeek 4 Pro; Agy -> Gemini models and Claude Opus 4.6 when available; Cursor -> non-Codex models including Composer 2.5. If Claude main provider is unavailable before Monday, June 29, 2026 09:00 Budapest local time, do not block on Claude; use another independent non-Codex route. Full protocol: [`agent-cooperation.md`](docs/best-practices/agent-cooperation.md)

> **Fleet roster + when-to-use + no-idle routing (READ to keep lanes busy):** [`docs/best-practices/agent-activity-matrix.md`](docs/best-practices/agent-activity-matrix.md) — §2 roster (current lanes/cost/models) + §2b capacity routing (free lane → next work). Canonical per-task routing rule: `agents_extensions/shared/rules/model-assignment.md` (served at `/api/rules`).

### Headroom

Headroom runs locally at `http://127.0.0.1:8787`; MCP is exposed at
the `headroom` stdio server via `headroom mcp serve`. Use
`headroom_compress` before sharing logs, search results, tool outputs, or
handoffs over roughly 200 lines / 20 KB; pass the hash plus a short summary,
and retrieve the original only when needed. Check health with
`curl -s http://127.0.0.1:8787/health`; start it with
`headroom install start --profile default` if it is down. Do not run
`headroom learn --apply` unless explicitly requested because it rewrites agent
instruction files. Do not treat Headroom memory as factual authority for
curriculum content.

---

## Workflow

- **Plan mode** for any non-trivial task (3+ steps or architectural decisions)
- **Simplicity first**: minimal code impact, find root causes, verify before done

### Claude Code Power Features

| Feature | How | When |
| --- | --- | --- |
| `Monitor` tool | Stream stdout events as notifications | **Build monitoring.** Agents may run V7 builds during autonomous orchestration (per user direction 2026-05-13) — always pass `--worktree`. Filter JSONL events with `grep --line-buffered '^{\"event\"'`. See below. |
| `/effort` | Set model effort dynamically mid-session | Levels: `low` / `medium` / `high` / `xhigh` / `max`. `low`: config/typo fixes. `medium`: code fixes. `high`: **Opus 4.8 default** — most intelligence-sensitive work. `xhigh`: coding/agentic, content review, plan review, module building, linguistic analysis — Anthropic's explicit override for coding on 4.8. Effort matters MORE on 4.8 than prior Opus, so **sweep `medium`/`high`/`xhigh` per route** rather than defaulting to `xhigh` everywhere. `max`: deep architecture / adversarial reviews where correctness outweighs cost. |
| Transcript search | `Ctrl+O` then `/` to search, `n`/`N` to navigate | Finding previous discussions in long sessions |
| `--bare` flag | `claude -p "..." --bare` | Scripted calls (agent bridge) — skips hooks/LSP/plugins for speed |
| `worktree.sparsePaths` | Configured in settings.json | Subagent worktrees exclude `node_modules/`, `data/` for speed |
| `PostCompact` hook | Auto-runs after context compaction | Restores current task, open issues, key reminders |
| `FileChanged` hook | Auto-runs when `curriculum/**/*.md` changes | Triggers audit on module file edits |
| `effort: xhigh` on skills | Frontmatter in review skills | `content-review`, `plan-review`, `plan-review-seminar`, `batch-review`, `prompt-review` — forces deep analysis. Set `xhigh` 2026-04-21; retained for Opus 4.8 — Anthropic recommends `xhigh` for coding/review and a minimum of `high` for intelligence-sensitive work. |
| `paths:` scoping on rules | Frontmatter in rule files | `ukrainian-linguistics.md` only active for curriculum/orchestration work |

### Build Monitoring (MANDATORY)

**NEVER poll builds with ScheduleWakeup or manual loops.** Use the `Monitor` tool:

Agents may run V7 builds during autonomous orchestration — always pass `--worktree` (PR #1952) so the build runs in `.worktrees/builds/{level}-{slug}-{stamp}/` and main stays clean.

```
Monitor(
    command=".venv/bin/python -u scripts/build/v7_build.py {level} {slug} 2>&1 | grep --line-buffered '^{\"event\"'",
    description="V7 build events for {level}/{slug}",
    persistent=True,
    timeout_ms=3600000
)
```

`v7_build.py` emits JSONL events from the wrapper and `linear_pipeline.py`: single-module lifecycle notifications such as `phase_done`, `review_score`, and `module_done`; writer/reviewer telemetry such as `writer_cot_emit`, `writer_tool_call`, `writer_end_gate`, `writer_tool_theatre`, `phase_writer_summary`, `mcp_config_resolved`, `reviewer_dim_evidence`, `reviewer_audit_call`, and `phase_review_summary`; and correction diagnostics `writer_correction_unparseable`, `reviewer_fixes_unparseable`, `reviewer_fixes_anchor_unmatched`. Each line becomes a notification — zero polling overhead.

For state queries without running builds, use the Monitor API (`docs/MONITOR-API.md`):
- Track health: `/api/state/track-health/a1`
- Failing modules: `/api/state/failing?track=a2`
- Build status: `/api/state/build-status/a1`
