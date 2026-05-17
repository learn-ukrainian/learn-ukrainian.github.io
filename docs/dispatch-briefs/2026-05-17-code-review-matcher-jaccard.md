# Dispatch: fix code-review benchmark semantic matcher false negatives (#2047)

## Why this matters

`scripts/audit/code_review_benchmark.py` scores LLM code-review runs.
PR #2043 added semantic matching (category + Jaccard 0.4) but the
2026-05-16 18:55 run on `pr-2025-openai-proxy` STILL scored
opus-4-7/xhigh/native_cli at 0% F1 — despite the model emitting a
verbatim correct finding (`prompt-on-command-line-leak-and-arg-max-dos`
matches gold `arg-max`).

Result: the leaderboard systematically under-rates higher-effort
models that produce verbose, descriptive findings — the harness is
measuring its own matcher's narrowness, not model quality. Mirror of
the #1900 rollout-matcher class of bug.

The gold corpus refresh (#2042) just landed in PR #2075 with widened
ids/aliases. This dispatch fixes the MATCHER itself to honor those
widened aliases AND lower the Jaccard threshold for verbose findings.

## Files

- `scripts/audit/code_review_benchmark.py` — the matcher. Read first;
  understand the current category + location + Jaccard chain before
  editing.
- `audit/code_review_benchmark/gold/*.yaml` (or wherever — see #2042
  for actual paths). DO NOT modify gold — that was #2042's scope.
- `tests/test_code_review_benchmark.py` (if it exists; otherwise
  create alongside the matcher).
- One concrete failing model output to test against:
  `audit/2026-05-17-code-review-benchmark-expansion-2/<path>/claude-opus-4-7/native_cli/xhigh-with_mcp.json`.

## What to do (verifiable steps)

1. **Worktree setup.** You were spawned with `--worktree`; cite
   `git rev-parse --show-toplevel` + `git branch --show-current` raw.

2. **Read the matcher.** Quote the current priority order from
   `code_review_benchmark.py` — specifically the category-match,
   location-match, and Jaccard-threshold logic.

3. **Reproduce the 0% F1.** Load the
   `xhigh-with_mcp.json` for `pr-2025-openai-proxy`, find the
   `prompt-on-command-line-leak-and-arg-max-dos` finding, and run
   the matcher against the gold corpus for that PR. Confirm
   `matched_gold_ids: []`. Quote the matcher's category + location +
   Jaccard scores for the model finding vs gold `arg-max`.

4. **Diagnose WHICH of the 3 hypotheses applies** (issue body lists
   them). The diagnosis must be backed by a quoted snippet of:
   - the model finding's category, location, description
   - the gold finding's category, location, description
   - the matcher's per-pair Jaccard score (instrument it briefly to
     log this)

5. **Pick the fix.** Three options ordered cheapest → most-defensible:
   - **A. Lower Jaccard threshold** from 0.4 → 0.25.
     Cheap. But risks false positives — a finding about "argparse"
     might match a gold about "argument validation" without being
     semantically the same. Quantify by re-running ≥3 other model
     cells and showing F1 doesn't degrade.
   - **B. Use the new gold aliases** from PR #2075's corpus refresh
     so descriptive ids like `prompt-on-command-line-leak-and-arg-max-dos`
     resolve via alias lookup before Jaccard ever runs.
   - **C. LLM-as-judge for borderline cases** (Jaccard in [0.25, 0.4]).
     Heaviest; defer to follow-up unless A+B together are insufficient.

   B is most defensible — the matcher should consume the schema that
   #2042 just shipped. Implement B; only fall back to A if alias
   coverage from #2042 is sparse.

6. **Test.**
   - Add `tests/test_code_review_benchmark.py` (or extend) with a
     parametrized test that runs each of the 3 affected
     opus-xhigh/native_cli cells through the matcher and asserts
     `F1 > 0.0` (or whatever the realistic floor is given the corpus).
   - Run the full pytest subset: `tests/test_code_review*` or similar.

7. **Re-score the 3 affected cells.** Run the benchmark replay against
   the existing raw JSON outputs (no LLM re-call needed; the JSON is
   on disk). Quote the new F1 per cell.

8. **Commit + push + PR.**
   ```
   fix(audit): code-review matcher respects gold aliases (#2047)
   ```
   PR body must include:
   - the diagnosis quote pair (model finding vs gold finding)
   - the chosen fix variant and rationale
   - before/after F1 per cell (3 cells)
   - the new pytest pass summary line
   - `Closes #2047`

## Verifiable claims required in the PR body

Per `docs/best-practices/deterministic-over-hallucination.md`:

| Claim | Evidence |
|---|---|
| "Diagnosis confirmed" | quoted pair of finding records + matcher's per-pair Jaccard |
| "Matcher updated to use aliases" | per-method diff snippet from `code_review_benchmark.py` |
| "F1 improved on 3 cells" | raw 3-cell F1 before/after table |
| "Regression test pinned" | raw pytest output: `N passed in M.MMs` |

## Out of scope

- DO NOT modify gold corpus (audit/code_review_benchmark/gold/) —
  that was PR #2075. Treat it as input.
- DO NOT add new benchmark cases.
- DO NOT re-call the LLMs to regenerate model outputs; replay against
  the existing JSON in audit/2026-05-17-code-review-benchmark-expansion-2/.

## Acceptance

- PR opens with raw evidence
- `Test (pytest)` CI required check passes
- Regression test added covering at least one of the 3 affected cells
- Closes #2047

## Pointers

- Issue: `gh issue view 2047`
- Predecessor PRs: #2043 (initial matcher), #2075 (gold refresh)
- Related: #1900 (rollout-matcher class)
- Trailer: every commit gets `X-Agent: codex/2047-matcher-aliases`
