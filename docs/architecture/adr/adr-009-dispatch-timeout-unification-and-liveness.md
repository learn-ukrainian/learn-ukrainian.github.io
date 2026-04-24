# ADR-009: Dispatch `hard_timeout` is a leak guard, not a productivity heuristic

**Status**: Accepted
**Date**: 2026-04-24
**Deciders**: Krisztian, Claude (Opus 4.7), Codex (gpt-5.5), Gemini (3.1-pro-preview)
**Related**:
- #1184 (original stall-detection deletion — root cause)
- #1520 (EPIC: K8s-style composite liveness probes — the long-term replacement)
- `fa8b4ee0c1` (timeout unification commit this ADR codifies)
- Bridge discussion: `ab channel tail architecture --thread 0f94b8c0faf24f158c593f13bcc3d6dd`
- Anthropic 2026-04-23 postmortem + `docs/reports/2026-04-23-anthropic-postmortem-impact.md`

## Context

The agent runtime has two timers for every subprocess dispatch: `hard_timeout` (wall-clock ceiling) and `stall_timeout` (liveness kill). On 2026-04-10 (#1184), stall detection was deleted from the watchdog because its per-CLI signals proved unreliable in four documented ways:

1. Gemini block-buffers stdout when not on a TTY — stdout goes silent for 5+ min during reasoning bursts, looking identical to a hang.
2. Codex moves its primary log location on every CLI version bump (`logs_1.sqlite` → `state_5.sqlite` → `sessions/YYYY/MM/DD/rollout-*.jsonl`).
3. Directory mtime on `sessions/YYYY/MM/DD/` bumps only on child creation, not on child content writes — the signal fires once at startup and goes silent.
4. Every CLI stores live state differently with a different convention.

After #1184, `hard_timeout` became the only kill signal. But the codebase kept its pre-#1184 structure: tight, phase-specific `TIMEOUT_*` constants (300s–900s) each "tuned" for an expected phase duration.

On 2026-04-24 this latent flaw surfaced: `a1/sounds-letters-and-hello` SKELETON failed at 300s on a 51K-char prompt while the model was actively reasoning. The user's critique: *"the timeouts are a pain always. what if it needs more time, and you kill it, because you set some random timeout you think it will be enough, really poor design."*

Investigation found three compounding hidden caps: `_gemini_per_rung_timeout()` clamping at 900s (`scripts/agent_runtime/runner.py:373`), `CASCADE_PER_CALL_MAX_S = 600` (`scripts/batch/batch_gemini_config.py:94`), and `effective_timeout = min(300 + len(prompt)//500, 900)` in the direct fallback path (`scripts/ai_llm/fallback.py:418`). Each was silently overriding caller intent.

## Decision

**`hard_timeout` is a last-resort leak guard for runaway processes. It is NOT a tuning knob for expected phase duration.** All LLM-reasoning dispatches use `_ONE_DAY` (86400s / 24h). Only genuine liveness probes (e.g. `TIMEOUT_REVIEW_GEMINI_PROBE = 300`) use shorter values.

Kill decisions for productive LLM work are the responsibility of **external observability**, not the runtime:

- The `Monitor` tool tailing `v6_build.py` JSONL events (one line per phase).
- `/api/delegate/active` with last-activity timestamps per dispatch.
- Per-CLI session files (`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`, `~/.gemini/tmp/<proj>/chats/session-*.json`, `~/.claude/projects/<proj>/*.jsonl`).

A human or an observability layer consults those signals to decide "this dispatch is stuck." The runtime does not guess.

The eventual replacement for manual observability is a **composite liveness probe** in the K8s style: ANY-mode composition of multiple per-CLI signals with a failure threshold. Tracked as EPIC #1520. Until it lands, the 24h ceiling holds and external observability does the work.

### Concrete surface

```
scripts/batch/batch_gemini_config.py       all TIMEOUT_* for LLM phases → _ONE_DAY
                                           CASCADE_PER_CALL_MAX_S → _ONE_DAY
                                           TIMEOUT_REVIEW_GEMINI_PROBE stays at 300

scripts/agent_runtime/runner.py            _gemini_per_rung_timeout() honors caller
                                           invoke() default hard_timeout = 86400

scripts/ai_llm/fallback.py                 effective_timeout defaults to _ONE_DAY
```

## Alternatives considered

- **Restore the old `stall_timeout` kill in the watchdog** → rejected. The four failure modes documented in #1184 still stand. A single unreliable signal was the original problem; reviving it changes nothing.

- **Per-phase clocks set more generously (5 min, 15 min, 30 min)** → rejected. Same failure shape at a longer horizon. Any specific number is someone's vibe about expected duration, and for LLMs with variable prompt size / reasoning depth, no single number is defensibly right.

- **Expose an opt-in `hard_timeout=None` / "no timeout" mode** → considered, rejected for now. Would strictly dominate the 24h policy for productive work, but leaks subprocess forever if a CLI bug spins infinitely. 24h preserves the leak-guard guarantee at acceptable cost.

- **Restore stall detection AND fix each per-CLI signal** → rejected in scope. This is what the K8s-style composite probe (#1520) does properly. Doing it in-watchdog just resurrects whack-a-mole.

## Consequences

**Positive**:
- Productive LLM reasoning is never killed on a preset clock. The user's repeated critique lands: no more "set a number, hope it works, kill something productive when wrong."
- One named constant (`_ONE_DAY`) replaces scattered 300/600/900 literals across four files.
- Makes the observability layer (Monitor tool, `/api/delegate/active`) a first-class control plane, not a debugging afterthought.

**Negative / risks**:
- A CLI bug that spins a subprocess infinitely now leaks 24h before cleanup. Acceptable: previous state was "leak 5-15 min" but also "kill productive work all the time." Net cost per day is much lower.
- If external observability is down (Monitor API crashed, human asleep), a stuck dispatch runs 24h unattended.
- No structural signal that a specific dispatch is stuck vs. reasoning. Until #1520 lands, the only observability is "did phase N's `module_done` event fire?"

**Neutral / follow-ups**:
- `stall_timeout` is still threaded through runner signatures for backward compat but ignored by `should_kill()`. Clean up in the EPIC that introduces the composite probe (#1520).
- Alignment manifest includes `TIMEOUT_*` values in its hash → manifest hashes change when this file changes, intentionally invalidating cached build state on timeout-policy edits.

## Verification

- **Test**: `grep -nE 'min\(.*hard_timeout.*,.*\d+' scripts/agent_runtime/ scripts/ai_llm/ scripts/batch/` returns no results (no more hidden caps).
- **Monitor**: `/api/delegate/active` already exposes `last_activity` + `started_at` per dispatch. When #1520 Phase 3 lands, this surface extends to probe state.
- **Revisit trigger**: if a real CLI bug causes a 24h-leak incident, OR if #1520 Phase 2 (watchdog integration) ships, this ADR is candidate for supersede. The next ADR should explain which half of "24h ceiling + composite probe" is authoritative.

## History

| Date | Event |
|---|---|
| 2026-04-10 | #1184 deletes stall detection from watchdog |
| 2026-04-23 | Anthropic postmortem; #1472/#1474 pin Opus 4.7 as writer default (earlier architectural fix) |
| 2026-04-24 | `a1/sounds-letters-and-hello` SKELETON fails at 300s; user flags the clock-based design |
| 2026-04-24 | Architecture discussion on bridge thread `0f94b8c0`; Codex and Gemini converge (after round-2 corrections) on this design |
| 2026-04-24 | `fa8b4ee0c1` commits the unification; this ADR codifies it |
| TBD | #1520 Phase 2 lands composite probes → this ADR candidate for supersede |
