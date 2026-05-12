# Harness Engineering

> **Vocabulary source:** [OpenAI — "Harness engineering: leveraging Codex in an agent-first world"](https://openai.com/index/harness-engineering/) (Feb 2026, Ryan Lopopolo) and the companion ["An open-source spec for Codex orchestration: Symphony"](https://openai.com/index/open-source-codex-orchestration-symphony/) (Apr 2026).
> **Scope:** Whole-repo scaffolding around agent code production — *not* this project's curriculum-content layer (see caveat at end).
> **Status:** Vocabulary doc. We have been doing harness engineering for ~6 months by trial and error; this doc gives the practice a name and a reference architecture so future agents stop reinventing it.

---

## TL;DR

Prompt engineering optimizes one turn. Context engineering optimizes what the agent sees on this turn. **Harness engineering optimizes the whole environment so every turn succeeds** — code structure, mechanical lints, app legibility, doc layout, merge norms, in-repo knowledge.

The job shifts from *writing code* to *designing the environment in which agents reliably write the code*. Humans steer. Agents execute.

---

## Where it sits

| Term | Optimizes | Time horizon |
|---|---|---|
| Prompt engineering | One model interaction | Seconds |
| Context engineering | What's loaded into the prompt this turn | Minutes |
| **Harness engineering** | **The environment that makes every agent turn succeed** | **Months — codebase-level investment** |

It is *not* "vibe coding." It is the opposite: heavy mechanical structure, strict architectural boundaries, validated invariants. The only thing it removes is human-typed code.

---

## Core principles

### 1. Map, not manual

A 1000-line AGENTS.md fails predictably: context crowded out, "everything important = nothing important," rots fast, mechanically unverifiable. Replace with:

- **AGENTS.md (~100 lines)** = table of contents pointing into a structured `docs/` system of record.
- **`docs/` directory** organized by purpose: design-docs, exec-plans, references/, generated/ (e.g. db-schema), ARCHITECTURE.md, QUALITY_SCORE.md, etc.
- **Progressive disclosure:** agents start at a small stable entry point and are taught where to look next.

**Our equivalent:** `CLAUDE.md` (~100 lines) + `memory/MEMORY.md` (rules, ~150 lines hard-budgeted) + `.claude/rules/_load-via-api.md` + API-served `/api/rules` + structured `docs/best-practices/`, `docs/decisions/`, `docs/session-state/`, `docs/bug-autopsies/`.

### 2. Repo as the only system of record

> *"From the agent's point of view, anything it can't access in-context while running effectively doesn't exist."*

Slack threads, Google Docs, people's heads — invisible. Push everything into versioned in-repo artifacts. The Slack discussion that aligned the team on an architectural pattern is illegible the same way it would be unknown to a new hire joining three months later.

**Our equivalent:** decisions journal (`docs/decisions/`), session handoffs (`docs/session-state/`), in-repo channel history via `ab` bridge, ADRs.

### 3. Enforce invariants, not implementations

> *"You care deeply about boundaries, correctness, and reproducibility. Within those boundaries, you allow teams — or agents — significant freedom in how solutions are expressed."*

- Mechanical linters/structural tests for: architectural layer dependencies, structured logging, naming conventions, file size limits, platform-specific reliability requirements.
- Error messages **inject remediation instructions** into agent context.
- You require boundary parsing — you don't dictate Zod. The agent picks the tool.

**Our equivalent:** `check_decisions.py`, `lint_anti_menu.py`, `lint_agent_trailer.py`, deploy-script-idempotency test, pre-commit ruff, X-Agent commit-trailer guardrail. Each one is "enforce shape, allow autonomy in fill."

### 4. Make the application legible to the agent

When agent code throughput exceeds human review capacity, the new bottleneck is **QA legibility**.

- App bootable per git worktree → agent can launch one instance per change.
- Chrome DevTools Protocol wired into agent runtime → agent can drive UI, screenshot, navigate.
- Ephemeral per-worktree observability stack (logs queryable via LogQL, metrics via PromQL) → prompts like *"ensure service startup completes in under 800ms"* become tractable.

**Our equivalent (partial):** Monitor API (`/api/orient`, `/api/state/*`, `/api/comms/*`, `/api/rules`) for state queries. `mcp__sources__*` for linguistic verification (VESUM, Грінченко, ЕСУМ, СУМ-11). Less invested on the runtime-UI side; the curriculum doesn't ship as an app yet.

### 5. Flip the merge philosophy

> *"In a system where agent throughput far exceeds human attention, corrections are cheap, and waiting is expensive."*

- Minimal blocking merge gates.
- Test flakes addressed with re-runs, not blocks.
- Short-lived PRs.

This would be irresponsible at low throughput. With agents, often the right tradeoff. **Caveat for our project: not for content. See bottom.**

### 6. Continuous garbage collection — encode taste, then enforce continuously

> *"Technical debt is like a high-interest loan: it's almost always better to pay it down continuously in small increments than to let it compound."*

- **Golden principles** — opinionated mechanical rules kept legible to future agent runs (e.g. "prefer shared utility packages over hand-rolled helpers," "validate boundaries; never YOLO-probe data shapes").
- **Recurring doc-gardening / refactor agent** scans for deviations, opens targeted refactor PRs. Most auto-merge in under a minute.
- Pattern: capture human taste once → enforce on every line of code, forever.

**Our equivalent:** bug autopsies (`docs/bug-autopsies/INDEX.md` + categories), MEMORY trim cadence, ADR hygiene flags in SessionStart, session-handoff two-tier policy.

### 7. Boring tech wins

> *"Technologies often described as 'boring' tend to be easier for agents to model due to composability, API stability, and representation in the training set."*

In some cases cheaper to *reimplement* a small utility (their map-with-concurrency vs the p-limit npm package) than work around opaque upstream behavior — because the in-repo version is fully agent-inspectable and tightly integrated with the system's instrumentation.

**Heuristic:** if an external dependency is going to need 200 LOC of glue + workarounds + comments explaining quirks, consider whether 300 LOC of in-house implementation would have been net cheaper to maintain.

---

## Symphony — the orchestration spec built on harness engineering

Symphony is the next step *after* the harness is solid. With the codebase agent-legible, the remaining bottleneck is **human attention switching between many parallel agent sessions**.

Symphony's pivot: stop tracking work via *coding sessions*. Track via **project-management state**. Each open Linear ticket → dedicated agent workspace; ticket becomes terminal → agent stops + workspace cleans.

### What Symphony is and is not

| Is | Is not |
|---|---|
| A scheduler/runner + tracker reader | A workflow engine |
| Polls Linear, spawns per-ticket workspaces | Writes ticket state itself — *agent* does ticket writes via available tooling |
| Hot-reloads its config from `WORKFLOW.md` in the repo | A CI replacement |
| Tracks tokens, detects stalls, retries with backoff | Multi-tenant control plane |
| Long-running daemon | A specific dashboard or UI implementation |

The shipped artifact is *literally* `SPEC.md` (~2,200 lines, RFC-2119 normative language) plus an Elixir reference impl marked "engineering preview." The recommended setup: ask your coding agent to build your own from SPEC.md.

### The in-repo contract: `WORKFLOW.md`

Single file. YAML front matter + Liquid prompt body. Versioned. Hot-reloads. Front-matter keys: `tracker`, `polling`, `workspace`, `hooks`, `agent`, `codex`.

```yaml
tracker:
  kind: linear
  project_slug: "..."
  active_states: [Todo, In Progress, Merging, Rework]
hooks:
  after_create: |
    git clone --depth 1 https://github.com/org/repo .
agent:
  max_concurrent_agents: 10
  max_turns: 20
codex:
  command: codex --config 'model="gpt-5.5"' app-server
  approval_policy: never
  thread_sandbox: workspace-write
```

The prompt body uses Liquid: `{{ issue.identifier }}`, `{{ issue.title }}`, `{% if attempt %}…continuation guidance…{% endif %}`. **Strict mode** — unknown variables fail rendering.

### Lifecycle hooks (portable idea)

- `after_create` — runs once when workspace dir is born. Failure aborts. Typical: `git clone` + deps fetch.
- `before_run` — pre-flight before each agent attempt. Failure aborts attempt.
- `after_run` — post-attempt, success or failure. Logged-only on failure.
- `before_remove` — cleanup before workspace deletion. Logged-only on failure.

These are general-purpose primitives for any dispatched-work scaffold, not Symphony-specific.

### The late lesson worth highlighting

> *"Treating agents as rigid nodes in a state machine doesn't work well. Models get smarter… So we eventually moved toward giving agents **objectives** instead of strict transitions, much like a good manager would assign a goal to a direct report."*

This is the same shift `claude_extensions/rules/goal-driven-runs.md` (#1884) encoded for our `/goal`. Independent convergence on the same pattern.

### Reported impact (their numbers)

- **500% increase in landed PRs** on streams that adopted Symphony.
- Product manager and designer can now file feature requests directly — agents complete them end-to-end without engineering intermediaries on routine work.
- *"It's become trivial to spin up speculative tasks. Try an idea you wouldn't have considered worth a human engineer's time."*

---

## Why this matters for our project

We have already been doing harness engineering for ~6 months. The OpenAI posts give us **vocabulary** and a **reference architecture** for things we evolved by trial and error. Mapping our current state to their pattern:

| Their pattern | Our equivalent today |
|---|---|
| AGENTS.md as table of contents | `CLAUDE.md` + `memory/MEMORY.md` (line-budgeted) + `.claude/rules/_load-via-api.md` + API-served `/api/rules` |
| Structured `docs/` system of record | `docs/best-practices/`, `docs/decisions/`, `docs/session-state/` (two-tier), `docs/bug-autopsies/`, `docs/SCRIPTS.md`, `docs/MONITOR-API.md` |
| Mechanical enforcement / custom lints | `check_decisions.py`, `lint_anti_menu.py`, `lint_agent_trailer.py`, deploy-idempotency test, pre-commit ruff, pre-push X-Agent trailer hook |
| Agent-legible app surfaces | Monitor API for state, `mcp__sources__*` for linguistic verification |
| Per-worktree isolated runs | `delegate.py dispatch --worktree` (mandatory per #M0 dispatch routing) |
| Bug autopsies / continuous GC | `docs/bug-autopsies/INDEX.md`, MEMORY trim cadence, ADR hygiene flags |
| Repo as only state | Decisions, comms, channel history all in-repo or DB-served |
| Multi-agent feedback loops | `ab discuss` channels, dispatch with cross-agent code review |
| Two-tier handoffs | brief.md + .html (epic #1865 item #1, shipped 2026-05-11) |
| Objectives over rigid state transitions | `/goal` rule (#1884, shipped 2026-05-12) |

### Where we deliberately differ from Symphony

Symphony's orchestrator = Linear board → agent (autonomous-continuous pickup). Ours = inline-Claude orchestrator + Monitor API + manual dispatch (event-driven, human-in-loop on every dispatch). That is a real architectural choice, not an accident. Symphony lets PMs/designers file work that agents complete. Ours requires an orchestrator to dispatch each unit.

---

## The critical caveat — why we cannot naively port their model

Their system is built for **software** where:

- Correctness = tests pass + CI green + code review.
- Output is verifiable mechanically.
- Bad output is cheap — revert in the next PR.

Our project is **education** where:

- Correctness = Ukrainian-native linguistic judgment + decolonized pedagogy + textbook grounding.
- Output verification requires expert review + RAG-backed source checks.
- Bad output trains the wrong habits into real learners' foundation; cannot be silently rolled back.

**The 500% PR throughput depends on bad output being cheap.** When bad output costs a learner's first contact with the language, "ship and iterate" is the wrong regime. *5 excellent modules beat 55 mediocre ones.*

### What this means in practice

| Layer | Harness engineering applies? | Notes |
|---|---|---|
| `scripts/` (build, audit, agent runtime, monitoring) | **Yes — aggressively** | Already heavily harnessed. Keep building. |
| CI, lints, deploy infra | **Yes** | Encode every taste rule as code; never as prose alone. |
| `docs/` knowledge base | **Yes** | Already partly there; the two-tier handoff format is exactly the pattern. |
| V7 pipeline (writer/reviewer prompts, gates) | **Yes — carefully** | Quality gates are the harness. Tightening them is harness work. |
| Module content production (`curriculum/`) | **NO — different regime** | Not parallelizable the same way; expert judgment is the bottleneck. Don't confuse "throughput optimization" with "quality optimization." |

### Adoptable patterns to evaluate next

1. **`WORKFLOW.md`-style single-file phase contract.** Our V7 pipeline phases (write, review-dim) are currently spread across `scripts/build/phases/linear-*.md`, `config.py`, and several rule files. A `WORKFLOW.md` per phase with YAML front matter + Liquid-templated prompt body would centralize the contract. Low risk; high clarity. **Candidate experiment.**
2. **Lifecycle hooks (`after_create` / `before_run` / `after_run` / `before_remove`) for dispatched worktrees.** We re-create the same setup boilerplate in every dispatch brief — centralizing into hooks is a clean refactor. **Candidate cleanup.**
3. **GH issue label → autonomous dispatch for a *narrow class* of work.** Specifically: lint hygiene PRs, dependency bumps, doc-gardening, MEMORY trims, autopsy backfills — work where bad output is cheap to revert. **Open decision card:** `docs/decisions/pending/2026-05-12-autonomous-codex-dispatch-narrow-class.md`. Explicitly **not** for module content.

---

## Further reading

- [OpenAI: "Harness engineering: leveraging Codex in an agent-first world"](https://openai.com/index/harness-engineering/) — the seed concept post.
- [OpenAI: "An open-source spec for Codex orchestration: Symphony"](https://openai.com/index/open-source-codex-orchestration-symphony/) — the orchestration follow-up.
- [openai/symphony on GitHub](https://github.com/openai/symphony) — `SPEC.md` (~2,200 lines, RFC-2119) + Elixir reference implementation.
- This project: `claude_extensions/rules/goal-driven-runs.md` — our `/goal` rule, independently convergent on Symphony's "objectives over transitions" lesson.
- This project: `docs/best-practices/agent-cooperation.md` — multi-agent deliberation protocol (`ab discuss`, Decision Card pattern).
- This project: `docs/best-practices/context-engineering.md` — the layer below harness engineering.
