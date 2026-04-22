# Codex Brief — #1406 Unify batch_gemini_runner with adapter path

**Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1406
**Task ID:** `codex-1406-batch-gemini-unify`
**Worktree:** `.worktrees/codex-1406-batch-gemini-unify`
**Branch:** `codex/codex-1406-batch-gemini-unify`
**Effort:** xhigh (refactor with subtle env-handling semantics; don't half-do it)

## Why this matters

User has flagged Gemini API-billing leak many times. #1384 Phase 1 closed the adapter path. **The remaining leak is in `scripts/batch_gemini_runner/execution.py`** — two raw `subprocess.run` calls with no `env=` kwarg, inheriting parent env including `GEMINI_API_KEY`. This bypasses the entire env-strip + fallback-ladder + auth-mode-resolution machinery.

Read the issue body in full for the diagnosis. It's all there.

## Worktree instructions (mandatory)

    git worktree add -b codex/codex-1406-batch-gemini-unify .worktrees/codex-1406-batch-gemini-unify
    cd .worktrees/codex-1406-batch-gemini-unify

## Hard prohibitions

1. **DO NOT MERGE the PR yourself.** Open it only.
2. **DO NOT use `gh pr merge` / `--admin` / `gh pr review --approve` for any reason.**
3. **DO NOT touch `scripts/agent_runtime/adapters/gemini.py`.** That's load-bearing for the adapter path which is shipping correctly. This refactor is one-directional: legacy → adapter, not the reverse.
4. **DO NOT change `call_gemini`'s return dict shape.** Downstream code in `batch_gemini_runner` dict-accesses keys (`returncode`, `stdout`, `stderr`, `gemini_json`, `elapsed_ms`). If any of those disappear, downstream silently breaks.
5. **DO NOT branch in the main checkout.**

## Read before coding (mandatory)

- `scripts/batch_gemini_runner/execution.py` — the file you're modifying. Especially `call_gemini` (line 183) and the second subprocess.run at line 357 (find what wraps it).
- `scripts/agent_runtime/runner.py:invoke` — the entry point you'll route through. Look at its signature.
- `scripts/agent_runtime/adapters/gemini.py` — the GeminiAdapter, particularly `build_invocation` and `parse_output`. Understand what you get back from invoke().
- `scripts/ai_llm/fallback.py:run_gemini_fallback_ladder` — what the adapter chains to. Know what the ladder gives you.
- `scripts/batch/batch_dispatcher.py` + `scripts/batch/batch_dispatcher_helpers.py` — confirms the v5 batch path is still wired (or deprecated, in which case AC-4 alternative applies).

## Decision tree (resolve BEFORE coding)

### Question 1: Is the v5 batch dispatcher still live?

Run:
```bash
git log --since="6 months ago" --oneline -- scripts/batch_gemini_runner/ scripts/batch/batch_dispatcher.py | head -20
git log --since="6 months ago" --oneline -- scripts/build/v6_build.py | wc -l
grep -rn "batch_dispatcher\|batch_gemini_runner.py" docs/ 2>/dev/null | grep -v archive | head
```

Compare activity. Plus: ask the user via `ai_agent_bridge ask-claude` if you're unsure.

- **If v5 path is dead** → take the **deprecation route** (AC-4 alternative): add big DEPRECATED banner at top of `scripts/batch_gemini_runner/__init__.py` + `scripts/batch_gemini_runner.py` (the stub) + `scripts/batch/batch_dispatcher.py`. Keep the files in place to avoid breaking imports for any cron jobs but emit a `warnings.warn(DeprecationWarning)`. Document the migration path (use v6_build.py + delegate.py instead). Smaller diff, less risk.
- **If v5 path is live** → take the **route-through-adapter route** (AC-1, AC-2, AC-3 below). Bigger diff, more risk, must preserve `call_gemini` return shape.

Document your decision in the PR body before opening.

## Acceptance criteria (route-through-adapter route)

### AC-1 — Replace both `subprocess.run` calls

`scripts/batch_gemini_runner/execution.py`:

- Line 191 (in `call_gemini`): the main one. Replace with a call through `agent_runtime.runner.invoke()` using the `gemini` agent.
- Line 357 (in whichever function): same treatment.

For each call, you need to:
- Build an invocation via the GeminiAdapter (use `runtime_invoke` since you don't need to construct the adapter manually)
- Pass through the existing prompt, model, timeout, cwd
- Map the `InvokeResult` back to the existing return-dict shape:
  - `returncode` ← from result (0 if success, non-zero on failure)
  - `stdout` ← extracted response text
  - `stderr` ← from result.stderr
  - `gemini_json` ← if Gemini returned `-o json`, parse from stdout (preserve existing logic)
  - `elapsed_ms` ← from result.duration_s × 1000

Preserve `_log_api_usage(track, slug, phase, retry, gemini_json, elapsed_ms)` — pull token counts from the adapter result if available, fall back to existing parsing.

### AC-2 — Inherit fallback ladder behavior

Document in a code comment that batch_gemini_runner now gets:
- Per-rung env-strip
- Auto-fallover on 429 across 6 rungs
- Cooldown awareness

This is the user-facing benefit. Don't bury it.

### AC-3 — Preserve TIMEOUT_SECONDS semantics

The existing code uses `subprocess.TimeoutExpired` to handle hard timeout. The adapter has its own `hard_timeout` mechanism. Make sure:
- If `runtime_invoke` raises `AgentTimeoutError`, return the same shape as the existing `subprocess.TimeoutExpired` handler (lines 223-230, 368-373) — including the negative `returncode: -1` and the formatted timeout stderr message.
- The same `TIMEOUT_SECONDS` value flows through (don't accidentally use the adapter's default).

### AC-4 — Tests

`tests/test_batch_gemini_runner_env.py` (new file):

- **`test_env_stripped_when_oauth_present`**: monkeypatch `~/.gemini/oauth_creds.json` exists, set `GEMINI_API_KEY` in env, invoke `call_gemini` with a mock subprocess that captures the env it received — assert `GEMINI_API_KEY` is NOT in the captured env.
- **`test_env_kept_when_oauth_absent`**: opposite — no OAuth file, set API key, assert API key IS in captured env (legitimate fallback to API mode).
- **`test_explicit_subscription_mode_strips`**: `GEMINI_AUTH_MODE=subscription` set explicitly → env stripped regardless of OAuth file.
- **`test_return_shape_preserved`**: invoke `call_gemini` against a mock subprocess that returns a known JSON payload — assert all 5 dict keys (`returncode`, `stdout`, `stderr`, `gemini_json`, `elapsed_ms`) are present and correctly populated.
- **`test_timeout_returns_existing_shape`**: simulate `AgentTimeoutError` → assert `returncode == -1` and stderr contains `Timeout expired` message.

Use `unittest.mock.patch` on the runner / adapter as needed.

### AC-5 — Verify v5 batch dispatcher boots

Run:
```bash
.venv/bin/python scripts/batch/batch_dispatcher.py --help
```

It must not crash. If it loads, you've preserved the import surface. If it crashes, fix the call-shape mismatch.

If you can identify a lightweight dry-run invocation (look for a `--dry-run` flag or a `--test` mode), run it. Don't fire a real batch — that would burn quota.

### AC-6 — Adversarial review

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
  "Adversarial review: routing batch_gemini_runner.execution through agent_runtime.invoke (#1406). Read the diff. Look for: (1) call-shape regression — any dict key in the return value of call_gemini that disappeared, (2) JSON-output parsing change losing fields downstream code depends on, (3) timeout semantics mismatch (subprocess.TimeoutExpired vs AgentTimeoutError), (4) ladder behavior swallowing errors the old direct-subprocess raised, (5) deprecation banners on dead code missing." \
  --task-id 1406-review
```

Address findings. Document any rejected feedback with rationale in the PR body.

## Workflow

1. Create worktree per worktree instructions
2. Read all 5 files in "Read before coding"
3. Resolve the decision tree (deprecate vs unify) — write a 2-paragraph decision in the PR body draft
4. Implement chosen path: AC-1 → AC-2 → AC-3 → AC-4 → AC-5 (one commit per AC is fine)
5. Run AC-6 adversarial review, address findings, log them in PR body
6. Push, open PR with title appropriate to chosen path:
   - Unify route: `fix(gemini): route batch_gemini_runner through adapter for env-strip + ladder (#1406)`
   - Deprecate route: `chore(gemini): deprecate v5 batch_gemini_runner — superseded by v6 + delegate.py (#1406)`
7. STOP. Do not merge.

## Done when

PR opened, decision documented, all chosen-path ACs green, adversarial review noted, dispatch reports `done`. User merges.
