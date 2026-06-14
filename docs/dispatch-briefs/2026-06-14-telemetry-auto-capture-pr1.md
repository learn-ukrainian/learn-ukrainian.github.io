# Dispatch: auto-telemetry PR1 — central emitter + correlation IDs + dispatch event (#3153)

Implements the **MVP central hook** of #3153 only. Defer module-build events, API/data-model
changes, reconciler, and prompt-fallback to follow-up PRs — do NOT build them here.

## Orchestrator-verified grounding (build on this, don't rebuild)
- `scripts/agent_runtime/usage.py` ALREADY writes exactly one JSONL per `runner.invoke()` to
  `batch_state/api_usage/usage_<agent>-<entrypoint>_YYYY-MM-DD.jsonl` via atomic `os.write()` O_APPEND
  (concurrent-safe). Reuse this write pattern; extend its record, don't replace it.
- `scripts/agent_runtime/telemetry.py` ALREADY EXISTS as the model/effort/CLI-version *resolver*
  (`resolve_invocation_telemetry`, `resolve_dispatch_start_telemetry`). **Do NOT add the event emitter
  there — name collision.** New emitter goes to `scripts/telemetry/emit.py`.
- `scripts/delegate.py` ALREADY writes terminal task state (`status`, `result_file`, duration, a JSONL
  payload). PR1 emits a telemetry event from that terminal path.

## Scope (PR1 only)
1. **Emitter `scripts/telemetry/emit.py`** — `emit_event(event_type: str, payload: dict, *, run_id: str | None = None) -> None`:
   - Writes ONE versioned JSONL line (`{schema_version, ts, event_type, run_id, session_id, source, **payload}`)
     to `batch_state/telemetry/events/YYYY-MM-DD.jsonl` using the SAME atomic O_APPEND pattern as `usage.py`.
   - **NO network. No API POST.** JSONL is the durable source of truth; API posting is a LATER PR (reconciler).
   - **Never raises** — wrap the whole body; on any error log at debug and return. Telemetry must never fail
     a build/dispatch/review.
   - Honors `LU_TELEMETRY_DISABLED=1` (no-op) and a recursion guard so emitting can't re-trigger emitting.
   - Helpers `current_run_id()` / `current_session_id()` read `LU_RUN_ID`/`LU_SESSION_ID` env; mint a stable
     id if absent and export it so children inherit.
2. **Correlation IDs in `runner.py`** — stamp `run_id`, `session_id`, and optional context env
   (`LU_TELEMETRY_LEVEL/SLUG/TRACK/SOURCE`) into the EXISTING `usage.py` usage record fields. Ensure these
   env vars propagate to child agent subprocesses. No prompt changes.
3. **Cost/token module `scripts/telemetry/pricing.py`** (the money-visibility root-cause fix — see below):
   - `compute_cost(model: str | None, tokens: int | None, *, agent: str | None = None) -> CostResult`
     returning `{cost_usd: float | None, billing_model: str, provenance: str}`.
   - `billing_model` ∈ {`per_token`, `subscription`, `unknown`}; `provenance` ∈ {`priced`, `no_tokens`,
     `no_price`, `subscription`}. **Never fabricate a price or a token count.** `cost_usd` is `None` unless
     we have BOTH a real token count AND a citable per-token price for that model id.
   - Pricing data lives in a small committed config table (`scripts/config/model_pricing.yaml`) keyed on
     model id, each entry citing its source in a comment. **Seed ONLY models with a known, citable published
     price** (e.g. metered API models like deepseek/codex-API where applicable). Subscription/unmetered lanes
     (claude-Code seat, gemini/agy unmetered sub) → `billing_model: subscription`, `cost_usd: null`,
     `provenance: subscription` — that "amortized, not per-call" fact IS the honest money answer, not a guess.
     Unknown models → `billing_model: unknown`, `provenance: no_price`, `cost_usd: null`.
4. **Dispatch event in `delegate.py`** — at the terminal-state write, call
   `emit_event("dispatch", {task_id, agent, model, effort, branch, worktree, status, duration_s,
   result_file, prompt_chars, response_chars, tokens, cost_usd, billing_model, cost_provenance})`.
   - `tokens` comes from the EXISTING usage record's `tokens` field (already `parse.tokens` where the adapter
     populates it; `null` otherwise — do NOT invent it).
   - `cost_usd`/`billing_model`/`cost_provenance` come from `pricing.compute_cost(model, tokens, agent=agent)`.
   - Best-effort; a telemetry failure must not change dispatch exit behavior. Derive participant count from
     dispatch state if cheap; otherwise omit (do NOT fabricate `swarm_used`).

## Money-visibility: WHY $0.000 everywhere (orchestrator-verified root cause — fix the cause, not the symptom)
Two distinct causes, confirmed 2026-06-14 (commands run, raw output in handoff):
- **Cause A — no cost compute (PR1 fixes this):** `grep -rn -i 'price|cost_usd|per_token' scripts/` finds
  ZERO cost-computation code; the only `usd` hits are `--max-budget-usd` (a dispatch *cap*, not a spend).
  So even records where `tokens` is populated show `$0.000` because tokens are never multiplied by a price.
  PR1's `pricing.py` + `cost_usd` field closes this — dollars appear wherever a token count already exists.
- **Cause B — partial token extraction (PR2, NOT this PR):** `grep -n 'tokens=' runner.py` shows only 2 of
  11 result paths set `tokens=parse.tokens`; the other 9 hardcode `tokens=None` (result.py documents this as
  deliberate "populated opportunistically"). So many agents never report tokens, so cost stays `null` for
  them even after PR1. Closing this means per-adapter response parsing — correctly its own PR (see below).

## Explicitly OUT of PR1 (do not implement)
- Module-build instrumentation, `/api/telemetry/agent-sessions`, DB schema changes, `reconcile.py`,
  prompt-fallback block. Leave TODO references to #3153 where the seams are.
- **PR2 (named, do NOT start here):** Close Cause B — extract token counts in the 9 `runner.py` result
  paths that currently hardcode `tokens=None`, per-adapter, from each CLI's reported usage where it exposes
  it. File a follow-up issue/brief referencing #3153 + these line numbers; leave a `# TODO(#3153 PR2)`
  marker at each `tokens=None` site so the gap is closed deliberately, not silently.

## Tests
- emitter: writes durable JSONL; swallows a forced write/serialize error and still returns None;
  honors `LU_TELEMETRY_DISABLED`; recursion guard holds.
- runner: a fake invoke records `run_id`/`session_id` in the usage record without touching the prompt.
- delegate: a fake-runner dispatch emits exactly one terminal `dispatch` event with status+duration AND
  the cost fields (`cost_usd`, `billing_model`, `cost_provenance`) present.
- pricing: priced model + real tokens → `cost_usd` non-null, `provenance=priced`; tokens `None` →
  `cost_usd=None`, `provenance=no_tokens`; unknown model → `provenance=no_price`; subscription lane →
  `billing_model=subscription`, `cost_usd=None`, `provenance=subscription`. Assert NO fabricated dollar
  value is ever returned without both a token count and a table price.
- contract: emit path makes NO network call (assert no requests/socket on the hot path).

## Numbered steps
1. `cd /Users/krisztiankoos/projects/learn-ukrainian && git fetch origin`. You are in a worktree from
   `origin/main` (delegate `--worktree`).
2. Implement scope 1–4. Read `usage.py` first and mirror its atomic-write + path conventions. For scope 3
   read `scripts/agent_runtime/result.py` (the `tokens` contract) before seeding prices, and leave the
   `# TODO(#3153 PR2)` markers at each `runner.py` `tokens=None` site (do NOT change those sites here).
3. `.venv/bin/python -m pytest tests/ -k "telemetry or usage or delegate or pricing" -q` → paste summary.
4. `.venv/bin/ruff check scripts/ tests/` → paste `All checks passed!`.
5. Confirm NO runtime artifacts staged: `git status --short` must show no `batch_state/` or
   `data/telemetry/` files (they are gitignored local state).
6. Commit: `feat(telemetry): central JSONL emitter + correlation IDs + dispatch event (PR1 of #3153)`.
7. `git push -u origin <branch>`; `gh pr create` referencing #3153 (note: PR1/4). NO auto-merge.

## Evidence (#M-4 — command + cwd + raw output per claim)
- tests pass: pytest summary line; lint: ruff final line; clean tree: `git status --short` (no artifacts);
  pushed: `git push` + `git log -1 --oneline`; PR: `gh pr view --json url`.
Unproven "did X" without command+output is treated as fabrication.
