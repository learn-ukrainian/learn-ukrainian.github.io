# Codex Brief — #1404 delegate.py rate-limit misclassification

**Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1404
**Task ID:** `codex-1404-rate-limit-bug`
**Worktree:** `.worktrees/codex-1404-rate-limit-bug`
**Branch:** `codex/codex-1404-rate-limit-bug`
**Effort:** medium

## Why this matters

The 2026-04-22 dispatch `claude-1370-writer-harden` completed successfully (5 commits → PR #1401 merged), but `delegate.py` reported `status: rate_limited`. Wasted ~10 min of next-session triage investigating a non-issue. Causes confusion + breaks downstream automation that branches on dispatch exit code.

## Worktree instructions (mandatory)

    git worktree add -b codex/codex-1404-rate-limit-bug .worktrees/codex-1404-rate-limit-bug
    cd .worktrees/codex-1404-rate-limit-bug

DO NOT branch in main checkout.

## Hard prohibitions

1. **DO NOT MERGE the PR yourself.** Open it only.
2. **DO NOT use `gh pr merge` / `--admin` / `gh pr review --approve`.**
3. **DO NOT change `delegate.py`'s public CLI** — only the rate-limit detection internals.
4. **DO NOT delete the rate-limit detection entirely.** Real rate limits must still be flagged.

## Diagnosis (do not skip — read code first)

Per #1404, the failure looks like:
- `scripts/delegate.py:307` reads `rate_limited = result.rate_limited` from the runtime adapter
- Adapter is in `scripts/agent_runtime/adapters/` — most likely the Claude adapter parses subprocess output for "rate limit" substring
- The dispatch's response text contained `"claude/claude-opus-4-7 rate limited: Done."` as its OWN PREFIX (the adapter prepended a warning notice and ALSO classified the task as rate-limited)
- Real-world: Claude Code can emit a soft warning about approaching rate limits without actually stopping work. The adapter is conflating "warning seen" with "task killed by rate limit."

Read these before coding:
- `scripts/delegate.py:286-348` (status classification)
- `scripts/agent_runtime/adapters/` (find the file with rate-limit detection)
- `scripts/agent_runtime/result.py` (the result type with `rate_limited` field)
- `batch_state/tasks/claude-1370-writer-harden.json` (concrete failing case — preserve if helpful for test fixture)

## Acceptance criteria

### AC-1 — Replace substring-match with structured signal

Choose ONE of these (in preference order):

- **(a) Exit-code based** — Claude Code's CLI returns a specific non-zero exit code when killed by rate limit. Verify the exit code by running `claude --help` and inspecting docs (or `claude -p "echo test" --bare; echo $?`). Use this code as the only true positive for rate-limit classification.
- **(b) Structured JSON output** — if `--output-format json` is in use anywhere, parse the structured signal from there.
- **(c) Stderr-only substring match** — narrowest fallback. The "rate limit" string must appear in *stderr only*, not stdout, not the response text.

Document in a code comment why the chosen heuristic is correct.

### AC-2 — Add 2 regression tests

`tests/test_agent_runtime_rate_limit.py`:

- **Test 1 (false positive defense):** Adapter receives a subprocess that exits 0 with response text containing the string `"rate limited"` (e.g., as part of the user task discussing rate limits, or as part of a previously-emitted soft warning). Result: `rate_limited == False`, `done == True`.
- **Test 2 (true positive preservation):** Adapter receives a subprocess that exits with the actual rate-limit exit code (or whatever signal AC-1 picks). Result: `rate_limited == True`.

### AC-3 — Re-classify the historical case

The `batch_state/tasks/claude-1370-writer-harden.json` task should classify as `done` under the new logic. Add a one-shot script `scripts/maintenance/reclassify_dispatch_status.py` that:
- Walks `batch_state/tasks/*.json`
- For each task with `status == "rate_limited"`, re-runs the classification logic against the saved stderr/stdout/exit code if available
- Updates the JSON in-place if the new classification is `done`
- Logs what changed

Run it once in this PR. Commit the resulting state changes (if any). The script stays for future use.

### AC-4 — Document

Add a brief note in `docs/MONITOR-API.md` or `docs/best-practices/agent-cooperation.md` (whichever covers dispatch lifecycle) explaining the rate-limit classification rule. One paragraph max.

### AC-5 — Adversarial review

Before opening the final PR:
- `.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude "Adversarial review of #1404 rate-limit fix. Read the diff. Look for: (1) the new heuristic missing real rate-limit cases that the old substring-match caught, (2) fragility tied to the specific Claude Code version (we run 2.1.117), (3) the reclassify script silently destroying historical evidence, (4) test coverage gaps." --task-id 1404-review`
- Address findings.

## Reference

- Issue: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1404
- Concrete failing case: `batch_state/tasks/claude-1370-writer-harden.json`
- Related incident: #1403 (agent merge autonomy — same dispatch, different incident)
- Related: #1396 / PR #1397 (effort wiring, recently shipped, uses same adapter layer)

## Workflow

1. Create worktree
2. Read `scripts/delegate.py:286-348` + `scripts/agent_runtime/adapters/` + `result.py` BEFORE coding
3. Pick AC-1 strategy and document why
4. Implement AC-1, AC-2, AC-3, AC-4 (one commit per AC is fine)
5. Run AC-5 adversarial review, address findings
6. Push, open PR with title `fix(delegate): correct rate-limit misclassification on completed dispatches (#1404)`
7. STOP. Do not merge.

## Done when

PR opened, regression tests pass locally, historical reclassify script ran and any updates committed, adversarial review noted, dispatch reports `done`.
