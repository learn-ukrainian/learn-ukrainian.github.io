# ADR-004: Unified agent runtime — single adapter layer for Claude/Gemini/Codex

**Status**: Accepted
**Date**: 2026-04-10 (landed) / 2026-04-11 (recorded)
**Related**: #1184 (implementation), `scripts/agent_runtime/`, `docs/agent-runtime-guide.md`

## Context

Pre-#1184, each agent CLI (Claude, Gemini, Codex) had its own subprocess spawning code duplicated across three call sites:

- `scripts/ai_agent_bridge/_*.py` — one file per agent, each reimplementing subprocess/timeout/error-handling logic
- `scripts/build/dispatch.py` — another copy specialized for pipeline dispatch
- `scripts/build/build_module_v5.py` — yet another copy for legacy batch runs

Three copies of the same logic meant three places where we fixed the same bug (the stderr pipe backpressure hang, the Codex post-completion thread wait, the gemini stall-detection false positives). When we added usage logging and rate-limit headroom tracking, we had to bolt them onto every copy.

The final straw was a multi-week sequence of hangs where each agent's call path had a DIFFERENT stall/kill semantics. Codex was killed at 180s by dispatch.py but not by _codex.py. Gemini's stall detection fired on reasoning silence that was actually work. Claude's pipe-closing order differed from the other two. Debugging meant reproducing the same hang three different ways.

## Decision

All LLM subprocess calls from every part of the codebase go through a single runtime at `scripts/agent_runtime/`.

**Core types**:
- `AgentAdapter` (Protocol) — each agent implements `build_invocation`, `parse_response`, `liveness_signal_paths`
- `InvocationPlan` — spawnable subprocess description (cmd, env, cwd, stdin, tempfile paths)
- `ParseResult` — normalized response (text, session_id, returncode, stderr_excerpt)
- `runner.invoke(agent, prompt, *, mode, cwd, model, hard_timeout, ...)` — the one public entry point

**Adapters** (`scripts/agent_runtime/adapters/`):
- `claude.py` — wraps `npx @anthropic-ai/claude-code`
- `gemini.py` — wraps `gemini` CLI
- `codex.py` — wraps `codex exec` with `-o <file>` output redirection

**Shared infrastructure**:
- `runner.py` — Popen + watchdog + error translation + usage record
- `watchdog.py` — stderr/stdout streamers + mtime poller + hard-timeout kill
- `usage.py` — per-call JSONL at `batch_state/api_usage/usage_{agent}-{entrypoint}_{date}.jsonl` + `has_headroom()`
- `errors.py` — `AgentStalledError`, `AgentTimeoutError`, `AgentUnavailableError`, `RateLimitedError`
- `registry.py` — agent → adapter mapping

**Call sites all migrated**:
- `scripts/build/dispatch.py` → `_dispatch_via_runtime` / `_dispatch_claude_via_runtime`
- `scripts/ai_agent_bridge/_codex.py`, `_gemini.py`, `_claude.py` → all route through `runner.invoke`
- `scripts/delegate.py` → runs the worker which calls `runner.invoke`

Adding a new agent is now a single-file change: create `scripts/agent_runtime/adapters/<agent>.py` + register in `registry.py`.

## Alternatives considered

- **Keep per-agent files, share helpers via a utilities module** → rejected: we tried this twice. Each time the helpers drifted because per-agent quirks (Codex `-o` flag, Gemini session files, Claude `--exclude-dynamic-system-prompt-sections`) leaked into the helpers and corrupted the shared layer.
- **One giant `dispatch` function with agent-specific if/else** → rejected: worse than per-file duplication because every agent quirk becomes a branch in the same function. Unreadable after 3 agents.
- **Subprocess library abstraction** (e.g. shelling out via `subprocess.run` everywhere) → rejected: the hard problems are NOT subprocess spawn — they're stderr backpressure, stall detection, session recovery, and rate-limit classification. A subprocess library doesn't help with any of those.

## Consequences

**Positive**:
- ONE place to fix subprocess bugs. The stderr pipe backpressure fix, the Codex post-completion hang detector, and the hard-timeout kill logic all live in `watchdog.py` and benefit every agent.
- Usage logging is automatic. Every `runner.invoke` call produces a usage JSONL record without the caller doing anything.
- Rate-limit headroom tracking is cross-agent. `has_headroom("codex", "gpt-5.5")` works identically for `("gemini", "gemini-3.1-pro-preview")` or any new adapter.
- Adding a new agent (future Codex version, Claude 5, etc.) is one-file work.
- The 80-test `tests/test_agent_runtime.py` suite covers the runtime itself; each adapter has targeted tests for its parse logic.

**Negative / risks**:
- The runtime is the single point of failure for ALL agent dispatch. A bug in `runner.py` breaks every pipeline + bridge call simultaneously. Mitigated by (a) extensive test coverage, (b) the `AgentUnavailableError` classification that lets callers degrade gracefully, (c) the stderr backpressure fix that eliminated the biggest class of runtime hangs.
- The adapter interface needs to stay backward-compatible as new agents join. Changing `AgentAdapter` signatures requires updating 3+ adapters. Mitigated by `getattr`-based optional methods (`check_early_reap` is the precedent — added after the Protocol was frozen).
- The runtime doesn't know about pipeline-specific retries (writer retry cascade, review round limits). Those stay in `scripts/build/v6_build.py::step_write_with_retry` and similar. The runtime provides the primitives; the pipeline composes them.

**Neutral / follow-ups**:
- Documentation: `docs/agent-runtime-guide.md` is the onboarding read for anyone touching `scripts/agent_runtime/`.
- Historical incidents: the autopsies in `docs/bug-autopsies/runtime.md` (if/when written) document the specific hangs this runtime was built to prevent.

## Verification

- `tests/test_agent_runtime.py` — 80+ unit + integration tests covering every adapter + the shared runner
- `tests/test_dispatch.py` — pipeline-side integration tests ensuring `dispatch_agent` routes correctly
- `tests/test_codex_bridge.py` — bridge-side tests for `process_for_codex` headroom + rate-limit behavior
- Live smoke: `scripts/delegate.py dispatch --agent codex` + `delegate.py wait` end-to-end works for real issues (validated in sessions 2026-04-10 / 04-11 — closed issues #1166, #1169, #1162, #1180, #1148, #1171, #1183, #1186 via delegation)
