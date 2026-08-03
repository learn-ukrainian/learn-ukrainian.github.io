# CLAUDE.md - Project Instructions

> **Provider boundary:** Shared repository invariants live in `AGENTS.md`. Claude agents should read `AGENTS.md` plus this Claude-specific file; Codex prompts should not read this file as runtime instructions. Defer shared rules here instead of duplicating stale copies.

> **Mission**: We are building something that doesn't exist — a full Ukrainian language curriculum with decolonized pedagogy, real textbook grounding, RAG-verified vocabulary, and adversarial review. This is a one-of-a-kind project for a great hero nation. Every shortcut degrades what makes it special. Quality is non-negotiable.

> **ALWAYS aim for and research best-practice solutions and practices.** Before implementing or deciding, actively seek the established best practice — web-research current standards, read `docs/best-practices/`, check prior art and idiomatic patterns, consult authoritative sources. Never settle for the first thing that works; choose the well-supported, proven, state-of-the-art approach. This applies to code, pedagogy, linguistics, architecture, and process alike.

> **Project policy — non-commercial, permanent**: This project will not be commercialized. It is and will remain a free, open-source educational resource. Decision recorded 2026-04-19. Implication: dependencies under non-commercial licenses (CC BY-NC, RAIL-NC, etc.) are acceptable as long as the project's non-commercial posture is maintained. No "we might monetize someday" hedging.

> **ALWAYS look for the source of the problem first.** Don't fix symptoms — trace the root cause, understand why it happens, then fix that.

> **BEHAVIORAL RULES** are in `memory/MEMORY.md` — enforced every session. Key: finish the job (no tech debt), stop asking (just do it), test before shipping, use tracking docs, no quality shortcuts, investigate before coding, be honest.

> **NON-NEGOTIABLE RULES** in `.claude/rules/non-negotiable-rules.md` — word count targets are MINIMUMS, all audit gates must pass, no shortcuts.

> **Status**: `curriculum/l2-uk-en/{level}/status/{slug}.json` | Update: `.venv/bin/python scripts/audit_module.py {path}`

> **Cross-session Memory**: Built-in auto-memory at `~/.claude/projects/.../memory/MEMORY.md`. Inter-agent comms via `.venv/bin/python scripts/ai_agent_bridge/__main__.py`. Gemini-family work routes through AGY, not Gemini CLI or Gemini Code Assist; see `docs/guardrails/agent-fleet-tooling.md`.

> **Default subagent**: Always use `subagent_type: "curriculum-orchestrator"` when spawning agents for curriculum orchestration work.

---

## Operator Contract (binding — loads without tools)

The operator's working contract is `agents_extensions/shared/rules/operator-expectations.md`
(served FIRST at `GET /api/rules`; digests also in `AGENTS.md` and `GEMINI.md` § Operator
Contract). Headless `claude -p` runs may not fetch the API — this digest keeps the contract
in-context regardless: quality over shortcuts · root-cause fixes · git/PR hygiene +
layout A (primary non-bare on main; agents under `.worktrees/dispatch/…`; bare=bug) ·
`X-Agent` trailers · whole-fleet utilization, review gate = independent CROSS-FAMILY
reviewer (discussion ≠ review) · route by model × harness fit · handle limits, NOTE
substitutions · tool-backed claims only; **outcome validity precedes paid execution**
(semantic canary + explicit success/stop criteria; transport/shape/cost are not outcome proof) ·
UK word/stress/morphology facts VESUM/`sources`-verified, never guessed · clean code + current
docs · **max UA immersion EXCEPT A1**
(English scaffolding there is by design; from A2 never raise English) · drive within
approved scope · **no architecture/layout/process decisions without operator or advisor
approval (Fable, Sol; roster may change)** · repo hard gates bind.

---

## Project Research Registry — Orchestrator Duty (binding)

Before every delegated task, classify its functional role, task family, track, and
owned paths. Pass every known dimension through `--research-role`,
`--research-task-family`, `--research-track`, and repeatable
`--research-owned-path`; never infer context from the provider or agent name. A
genuinely generic or unknown task omits all research flags and remains pointer-free.
A surfaced pointer is not proof of consumption, so research claimed as used requires
an attributed record fetch while the task is active. Registry delivery remains
fail-open, but the classification duty is mandatory. Canonical contract and examples:
`agents_extensions/shared/rules/workflow.md` § Project Research Registry.

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

For shared delegation, artifact hygiene, Python invocation, worktree layout, commit trailers, and independent review routing, defer to `AGENTS.md`. Independent review must not be self-review, and internal GPT helper swarms do not satisfy the external gate. Reviews are cross-family (outside the author's model family; discussion does not satisfy the gate). Current external lanes + harness-vs-model reachability: `agents_extensions/shared/rules/model-assignment.md` (served at `/api/rules`); on limit, Claude/Codex budget buckets substitute per `scripts/config/agent_fallback_substitutions.yaml`, other lanes reroute via the harness table — never block on a single lane, always note the substitution. Full protocol: [`agent-cooperation.md`](docs/best-practices/agent-cooperation.md)

> **Fleet roster + when-to-use + no-idle routing (READ to keep lanes busy):** [`docs/best-practices/agent-activity-matrix.md`](docs/best-practices/agent-activity-matrix.md) — §2 roster (current lanes/cost/models) + §2b capacity routing (free lane → next work). Canonical per-task routing rule: `agents_extensions/shared/rules/model-assignment.md` (served at `/api/rules`).

---

## Workflow

- **Plan mode** for any non-trivial task (3+ steps or architectural decisions)
- **Simplicity first**: minimal code impact, find root causes, verify before done

### Claude Code Power Features

| Feature | How | When |
| --- | --- | --- |
| `Monitor` tool | Stream stdout events as notifications | **Build monitoring — NEVER poll with ScheduleWakeup or manual loops.** How-to (command template, `--worktree` requirement, JSONL event fields, Monitor API state queries): see the `build-monitoring` skill. |
| `/effort` | Set model effort dynamically mid-session | Levels `low` / `medium` / `high` / `xhigh` / `max` by TASK TIER. **Tuned for Opus 5** (the Claude lane rotates — re-verify per active model via the `claude-api` skill / release notes; never port the previous model's defaults). `low`: config/typo fixes. `medium`: routine code fixes, dispatch briefs, PR / merge-train babysitting. `high`: **the driving default** — orchestration and epic driving, plus the floor for anything intelligence-sensitive and first-pass code review (find, before verify). `xhigh`: the hard turn inside a drive — content review, plan review, module building, linguistic analysis, adversarial review. `max`: deep architecture, review of record, contested verdicts. **Effort is per-turn — drive at `high` and bump for the one hard turn, then drop back.** `xhigh` is the documented START for coding/agentic work, but the same docs say sweep down from it, and `high` is the API default; driving is mostly routing and dispatch, which does not need the ceiling (user 2026-07-24). `low`/`medium` are unusually strong on Opus 5 — that is the load-spreading headroom, so step down wherever evals hold. **Two Opus 5 gotchas:** thinking-off is valid only at `high` or below (`thinking: disabled` + `xhigh`/`max` is a rejected request), and effort does **not** control response length — see Concise by default below. |
| `--bare` flag | `claude -p "..." --bare` | Scripted calls (agent bridge) — skips hooks/LSP/plugins for speed |
| `worktree.sparsePaths` | Configured in settings.json | Subagent worktrees exclude `node_modules/`, `data/` for speed |
| `effort: xhigh` on skills | Frontmatter in review skills | `content-review`, `plan-review`, `plan-review-seminar`, `batch-review`, `prompt-review` — forces deep analysis. Set `xhigh` 2026-04-21; retained through Opus 5 — Anthropic recommends `xhigh` for coding/review and a minimum of `high` for intelligence-sensitive work. Curriculum/linguistic review stays `xhigh`: these skills judge Ukrainian content, where a miss is a durable learner error. (CODE review is the one place a cheaper first pass is defensible — Opus 5 keeps high precision *and* recall at lower effort — but that is a dispatch-routing choice, not a change to these skills.) |
| `paths:` scoping on rules | Frontmatter in rule files | `ukrainian-linguistics.md` only active for curriculum/orchestration work |

### Concise by default

Keep responses focused, brief, and concise to avoid overwhelming the person. Disclaimers and
caveats stay brief, with most of the response on the main answer; when asked to explain
something, give a high-level summary unless an in-depth one is specifically requested. Lead
with the outcome — the first sentence should answer "what happened" or "what did you find",
with supporting detail after.

Being readable and being concise are different things, and readable matters more. Keep output
short by being selective about what you include — drop details that do not change what the
reader would do next — never by compressing prose into fragments, abbreviations, arrow chains,
or jargon. This does not license terseness that costs clarity (`#0I`: plain language always),
and it never applies to curriculum content, where word targets are MINIMUMS.

The same applies to files written to disk: match the length of a written deliverable to what
the task needs. Do not pad reports or handoffs with filler sections, redundant summaries, or
boilerplate.

**Length is a prompting concern, not an effort concern.** Lowering `/effort` does not reliably
shorten user-facing output on Opus 5 — it changes how much the model thinks, not how much it
writes. Reach for this section, not the effort dial.
