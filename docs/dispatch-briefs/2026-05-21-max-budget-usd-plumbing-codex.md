# Dispatch brief — `--max-budget-usd` plumbing for `delegate.py` (Claude lane only)

**Agent**: codex (gpt-5.5, xhigh)
**Mode**: danger
**Worktree**: `.worktrees/codex-max-budget-usd-2026-05-21` (REQUIRED — per `delegate-must-use-worktree.md`)
**Task ID**: `max-budget-usd-2026-05-21`
**Created**: 2026-05-21

## Why

Background: MEMORY #M0 was softened today (2026-05-21) from "no `delegate.py --agent claude` after 2026-06-15" to "quota-conditional after 2026-06-15." Dispatched Claude competes with the user's interactive seat for the same Claude Code weekly cap. To make dispatched Claude survivable post-6/15 we need a hard $$ cap per dispatch — `claude --max-budget-usd N.NN` exists at the CLI level (verified: `claude --help | grep budget` returns `--max-budget-usd <amount>  Maximum dollar amount to spend on API calls (only works with --print)`), but `delegate.py` has no plumbing for it.

Reference for the X-post pattern that prompted this gap-close: `docs/session-state/2026-05-21-morning-gemini-042-alignment-and-deepseek-viability.md` (the next session-state file will reference this brief).

## What

Add `--max-budget-usd` end-to-end through the dispatch path. Mirror the existing `--silence-timeout` / `--hard-timeout` plumbing exactly — same touch points, same persistence, same telemetry surface, same default-off semantics.

### Touch points (use `git grep -n silence_timeout scripts/delegate.py` as the template)

1. **`scripts/delegate.py`**:
   - Add `--max-budget-usd` (float) argparse on both `dispatch` and `_worker` subcommands.
   - Default: `None` (off — preserves current behavior).
   - Thread through the parent → worker subprocess args (the `"--silence-timeout", str(silence_timeout)` line near 1041-1042 is the pattern).
   - Persist into `tasks/{task_id}.json` state alongside the timeout fields.
   - Surface in the `Examples` and `Timeouts` help text in the dispatch subparser docstring (currently lines ~1500-1520).
   - Include in any telemetry record (look for `dispatch_silence_timeout` near 838 — same shape).

2. **`scripts/agent_runtime/adapters/claude.py`**:
   - In `build_invocation`, when `tool_config` (or a new dedicated kwarg — your choice, justify the shape in the diff) contains a non-None `max_budget_usd`, append `--max-budget-usd <value>` to the CLI args list.
   - Only emit the flag when `--print` mode is active (verified: `claude --help` says "only works with --print"). The adapter always uses `-p`-equivalent so this is a no-op constraint, but document it inline.

3. **Other adapters** (`codex.py`, `gemini.py`, `hermes_deepseek.py`, `hermes_grok.py`, `hermes_qwen.py`, `agy.py`):
   - Accept the value (do not error on it) but **ignore** — those CLIs have no USD budget concept.
   - Log a one-line WARN at adapter init when `max_budget_usd` is set on a non-Claude dispatch: `non-claude adapter X ignoring max_budget_usd=Y; use hard-timeout/silence-timeout instead`. Use the existing `_logger` pattern in each adapter.

4. **Tests** (`tests/`):
   - Add a unit test that `delegate.py dispatch --agent claude --max-budget-usd 0.50 ...` propagates `--max-budget-usd 0.50` into the claude adapter's invocation plan.
   - Add a unit test that the same flag on `--agent codex` does NOT show up in codex's CLI args.
   - Add a unit test that omitting the flag leaves both adapters unchanged (regression guard).

5. **Documentation** (`docs/agent-runtime-guide.md` if it documents adapter flags; otherwise skip — do not invent docs).

## Don't

- Don't change adapter behavior beyond Claude.
- Don't make `--max-budget-usd` required.
- Don't gate it on date — softening of #M0 was today's decision; this flag is purely opt-in until the user wants it enforced.
- Don't change `silence_timeout` / `hard_timeout` semantics.
- Don't add a `default = 5.00` or any non-None default — None means "no cap" and that's the current behavior.

## Verification before commit

```
.venv/bin/ruff check scripts/delegate.py scripts/agent_runtime/adapters/
.venv/bin/pytest tests/ -k 'delegate or claude_adapter or budget' -v --tb=short
```

All green required before commit. Per `#M-7` in `memory/MEMORY.md`: pre-commit hook is not a test run.

## Commit + PR shape

- **Branch**: `feat/max-budget-usd-plumbing-2026-05-21`
- **Single commit** with conventional message: `feat(delegate): thread --max-budget-usd through to claude adapter`
- **PR title**: `feat(delegate): thread --max-budget-usd to claude adapter (gap-close from zodchiii review)`
- **PR body**: explain the MEMORY #M0 softening context (2-3 lines), cite this brief, link the touch points.
- **Do NOT auto-merge.** Orchestrator (Claude) reviews and merges after `gh pr checks {N} --watch` passes.

## Steps (mandatory per dispatch-brief checklist)

1. `git worktree add -B feat/max-budget-usd-plumbing-2026-05-21 .worktrees/codex-max-budget-usd-2026-05-21 origin/main`
2. Implement the 5 touch points above.
3. Run verification commands.
4. Single conventional commit.
5. `git push -u origin feat/max-budget-usd-plumbing-2026-05-21`
6. `gh pr create --title ... --body ...` (NO auto-merge).
7. Report task done.

## Anti-fabrication (per #M-4)

Every claim of "tests pass" / "ruff clean" / "PR opened" in the final report MUST be backed by literal command output (cmd + cwd + raw last lines). A bare "all green" with no transcript is invalid.
