# DECISION REQUIRED — Should we adopt Symphony-style autonomous dispatch for a narrow class of work?

**Status:** PROPOSED (orchestrator-surfaced, awaiting user signoff)
**Surfaced:** 2026-05-12 night, after digesting [`docs/best-practices/harness-engineering.md`](../../best-practices/harness-engineering.md)
**Source:** OpenAI's Symphony post + spec; user-pointed reading 2026-05-12
**Scope:** GH issue triage flow + a new dispatch path. **Does NOT touch:** module content production, V7 pipeline, writer-selection. Decision is independent of and does not invalidate any in-flight orchestration work.

---

## What's being proposed

Add a **narrow autonomous-dispatch lane** for routine mechanical work: GH issues with a specific label (`agent:codex-autonomous` proposed) get picked up by a Symphony-style poller that dispatches Codex into a worktree, lets it work end-to-end, and either lands a PR or escalates.

**Crucially scoped** to work classes where bad output is *cheap to revert*:

- Dependency bumps (dependabot-equivalent triage).
- Lint hygiene PRs (`ruff`, `markdownlint`, `yamllint` cleanups).
- Doc-gardening: stale link fix-up, ADR expiry checks, dead-section pruning in `docs/`.
- Autopsy backlog (e.g. #1896 — secret-leak follow-ups).
- MEMORY trim passes when budget is exceeded.
- Schema drift checks (`requirements-lock.txt` regeneration after `pip-tools` lands per #1634).
- Bug autopsy backfills.

**Explicitly out of scope:**

- Module content (`curriculum/`).
- Writer/reviewer prompt iteration (V7 pipeline).
- Adversarial code review (those stay in the inline-Claude + `ab discuss` flow).
- Security-sensitive changes.
- Any work that touches `claude_extensions/rules/` deploy invariants without an explicit human-written brief.

---

## Why this might be worth doing

1. **Compound rate of small-fix shipping.** We already merge ~3-5 small PRs/day on average. A larger share could happen without me being in the steering chair on each dispatch decision. The session of 2026-05-12 shipped 2 PRs + 8 commits — comparable activity could happen overnight without an active session.
2. **Frees inline-Claude for what it's actually good at.** Adversarial review, hard-bug debugging, linguistic verification, orchestration decisions. Not "write the dependabot triage PR."
3. **Validates the autonomous loop on safe territory first.** Before we ever consider autonomous dispatch for higher-stakes work, we'd want empirical signal on how Codex behaves in the absence of an inline orchestrator. Lint/deps/docs are the right "training wheels" class.
4. **Aligns with #M-6 (drive don't defer).** Removes a class of work from my queue entirely.

## Why this might NOT be worth doing

1. **We don't have the volume to need it yet.** Symphony's 500% PR claim depends on a workload where queue depth was the bottleneck. Our actual P0 bottleneck is module-content quality, not "too many lint PRs."
2. **Codex weekly burn is finite.** Autonomous dispatch on every-label match could blow the weekly budget on doc-gardening if not capped. Per-day cap + budget guard would be required.
3. **Worktree storage + cleanup.** Symphony spins workspaces per-issue. We'd need workspace GC on a cadence (their `before_remove` hook).
4. **Quality drift in mechanical work.** Even "safe" work classes can mask real bugs (e.g. a `ruff` autofix that breaks a docstring matched by a test). Without inline review, drift accumulates silently between human-checked windows.
5. **Hard rule conflict.** CLAUDE.md says *"agents do not invoke v7_build.py themselves."* If autonomous dispatch ever crosses into a class that triggers a V7 build (e.g. a lint fix in `scripts/build/`), the contract gets ambiguous. Clear scope boundary required.

---

## Options

### Option A — Adopt narrow lane, hard-capped

1. Ship a small poller: `scripts/orchestration/autonomous_dispatch.py`, polls GH every N minutes for issues labeled `agent:codex-autonomous`.
2. Spawns Codex via `delegate.py dispatch --agent codex --mode danger --worktree` with the issue body as the brief.
3. **Hard caps:** max 3 autonomous dispatches/day. Total weekly Codex budget guard via `gh api` or `/api/delegate/active`. Auto-disable if any dispatched PR fails CI 3× in a row.
4. **Hard scope:** label is the gate. Issues without the label are NEVER picked up. Orchestrator (me) adds the label only on issues that fit the narrow class.
5. **Hard kill switch:** environment variable or `.claude/rules/_autonomous-disabled` file disables the poller globally for incident response.
6. Iterate based on 2 weeks of measured signal.

### Option B — Don't adopt; manual dispatch remains

The orchestrator (me) keeps deciding what to dispatch. Symphony's pattern is *interesting* but our workload doesn't have the queue depth that makes it net-positive. Re-evaluate in 3 months when we have higher mechanical-work volume.

### Option C — Adopt only a *manual-trigger* version

Add a `/autonomous {issue}` slash command or similar that lets me (or the user) one-shot a Codex dispatch with the brief auto-generated from the issue body. No polling, no autonomous pickup. This is closer to ergonomic improvement than to Symphony's architectural shift.

---

## Orchestrator recommendation

**Option A, hard-capped, 2-week pilot.**

Reasoning:
1. Symphony's "speculative tasks become trivial" claim is the most interesting effect, and we can't measure it without trying it. The 3/day cap + label gate keeps total downside bounded at ~21 PRs/week and a Codex budget hit we can quantify.
2. Backlog issues that would benefit (#1896 follow-ups, ADR hygiene, MEMORY trim, doc-link cleanup) have been sitting un-touched for weeks because they don't justify orchestrator attention. Autonomous lane could drain that.
3. Two weeks of signal is enough to either ratify, tune scope, or kill. Reversible.

**If Option A:** the implementation itself is a Symphony-style minimal scaffold. It is NOT inviting the full Symphony Elixir runtime; we'd write a ~200-LOC Python poller using Codex via `delegate.py`. SPEC.md is the reference architecture, not the dependency.

---

## What this looks like concretely

**One-time setup:**

- Create the GH label `agent:codex-autonomous`.
- Write `scripts/orchestration/autonomous_dispatch.py` (~200 LOC, polls every 15 min during designated hours).
- Add `agent.autonomous.daily_cap`, `agent.autonomous.window`, `agent.autonomous.enabled` config to a new `WORKFLOW.md` (Symphony-style — one file, YAML front matter).
- Add a kill-switch hook in `.claude/rules/`.

**Per labeled issue:**

1. Poller sees label.
2. Generates brief from issue body using a fixed template (cwd warning, numbered steps, evidence requirements, anti-fabrication preamble per `deterministic-over-hallucination.md`).
3. Dispatches Codex with `--mode danger --worktree --silence-timeout 1800`.
4. Codex works to completion, pushes branch, opens PR, comments on the issue.
5. Poller reconciles: if PR has `symphony` label and CI green → auto-merge after 24h (or human-merge if I'm awake).
6. If CI red or stalls → marks issue with `agent:codex-needs-orchestrator`, removes auto-label, re-queues for human attention.

**Symphony parity:** none of this needs Linear. GH issues + labels are the state machine.

---

## Awaiting

User signoff:

- **`go A`** — adopt narrow lane, 2-week pilot, scope as specified above.
- **`go A with adjustments: ...`** — adopt with named modifications (different cap, different scope, etc.).
- **`go B`** — don't adopt; keep manual dispatch.
- **`go C`** — adopt manual-trigger version only (no polling).
- **`wait`** — defer; revisit in N weeks.

If `go A`: filing as an EPIC issue with sub-tasks for the poller, the label, the WORKFLOW.md, the kill-switch, and the 2-week review checkpoint.

---

## Predecessor links

- [`docs/best-practices/harness-engineering.md`](../../best-practices/harness-engineering.md) — the vocabulary doc; this Decision Card is the practical follow-on.
- [`claude_extensions/rules/goal-driven-runs.md`](../../../claude_extensions/rules/goal-driven-runs.md) — `/goal` rule (#1884), which is the per-task version of what autonomous dispatch would be at the orchestration layer.
- [OpenAI Symphony repo](https://github.com/openai/symphony) — the reference architecture.
