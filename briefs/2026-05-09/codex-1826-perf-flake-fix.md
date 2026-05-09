# Codex CLI — Fix flaky perf test (#1826)

## TL;DR

`tests/test_playground_api_stability.py::test_playground_primary_endpoints_keep_health_fast` is fail-flaky — fails ~30% of CI runs with budget overruns of 30-100ms. Currently blocking PR #1824 and likely #1829. Three observed failures in 36 hours; one led to a #M-0.5 admin-bypass violation on PR #1813.

Fix per the recommendation in the issue: **relax network-bound budgets to 1.5s, keep `/api/health` at 0.1s, add p95-of-3-runs statistical fixture** to absorb cold-cache.

Full spec: **GH issue #1826** — every AC must be ticked.

---

## Mandatory orientation (#M-4)

1. **`docs/best-practices/deterministic-over-hallucination.md`** — every claim tool-backed.
2. **GH issue #1826** — `gh issue view 1826` — full ACs + recommended fix.
3. **`tests/test_playground_api_stability.py`** — read end-to-end. Identify `endpoint_budget` definitions and per-endpoint loop.
4. **`scripts/api/main.py`, `scripts/api/state_router.py`** (or wherever `/api/state/summary` is defined) — to internalize what's being measured.
5. **#M-0.5 autopsy** in MEMORY (the "PR #1813 admin-bypassed pytest:fail" lesson) — the exact case this fix prevents.

## Verifiable claims this work will produce + the tool

| Claim | Tool | Evidence format |
|---|---|---|
| "Test passes 100x in a row locally" | `for i in {1..100}; do .venv/bin/pytest tests/test_playground_api_stability.py::test_playground_primary_endpoints_keep_health_fast -q --tb=no || echo "FAIL $i"; done` | Quoted output (zero "FAIL" lines) |
| "Health endpoint stays at <0.1s budget" | Same pytest with verbose, grep for `/api/health` | Quoted output |
| "Network-bound endpoints budget = 1.5s" | `grep -nE "endpoint_budget|/api/state/summary|/api/orient" tests/test_playground_api_stability.py` | Quoted source |
| "p95 fixture works — 3 runs, allows 1 outlier" | New test that intentionally triggers a slow path; assert p95 still < budget | Quoted pytest output |
| "Ruff clean" | `.venv/bin/ruff check tests/test_playground_api_stability.py` | Quoted output |

---

## Worktree instructions (mandatory)

Dispatcher creates `.worktrees/dispatch/codex/codex-1826-perf-flake-fix/`. All work there. Branch: `codex/1826-perf-flake-fix`. Base: `origin/main`.

---

## Workflow (numbered)

1. **Worktree setup** verified.
2. **Read the issue** — `gh issue view 1826`. Note all ACs.
3. **Read the test** end-to-end. Identify the budget structure.
4. **Implement the fix:**
   - **Tier the budgets:** `BUDGETS = {'/api/health': 0.1, '/api/state/summary': 1.5, '/api/orient': 1.5, ...}` — health endpoint stays tight; network-bound endpoints get 1.5s. Document each in a comment.
   - **Statistical fixture:** Replace the single-run assertion with: run each endpoint 3 times, assert p95 (i.e., 2 of 3) under budget. One slow tail allowed.
   - **Don't disable the test, don't add `@pytest.mark.skip`.** Per the issue: "stops being a real gate" is option D and rejected.
5. **Tests:**
   - The patched test itself must pass 100x in a row locally (run the loop above).
   - Add a regression test: any new endpoint without an entry in `BUDGETS` fails the test (so new endpoints can't sneak past).
6. **Lint** — `.venv/bin/ruff check tests/test_playground_api_stability.py`.
7. **Commit** — conventional message:
   ```
   fix(test): relax perf-test budgets and add p95 fixture (#1826)

   - /api/health stays at 0.1s (true health probe).
   - Network-bound endpoints (state/summary, orient, etc.) at 1.5s.
   - p95-of-3 statistical fixture absorbs cold-cache outliers.
   - Regression: new endpoints without budget definition fail.

   Closes #1826. Unblocks #1824, #1829, future PRs.

   Co-Authored-By: Codex (gpt-5.5) <noreply@anthropic.com>
   ```
8. **Push** — `git push -u origin codex/1826-perf-flake-fix`.
9. **PR** — `gh pr create` with body referencing #1826 + every AC quoted-evidence-backed per #M-4.
10. **NO auto-merge.** Stop.

---

## What "done" looks like

- All ACs from #1826 ticked with evidence.
- 100/100 local pass.
- Pre-commit clean.
- PR opened, **NOT merged**.

## Escalation

If the budgets don't converge to a workable number (e.g. some endpoint is genuinely 5s+), STOP, post on #1826 with the data + propose a different approach (mock external calls per option B?), exit cleanly.
