# Dispatch: refresh code-review benchmark gold corpus (#2042)

## Why this matters

`scripts/audit/code_review_benchmark.py` scores LLM code-review runs
against a small gold corpus (3 PR cases). Issue #2047 surfaced that
the **matcher** had false negatives (Codex's lane, separate
dispatch). This dispatch is the **corpus refresh**: review the
existing 3 gold cases against the actual PR diffs, add/adjust
findings so semantically-valid model emissions are represented by the
corpus itself rather than by matcher tolerance.

Keep this work SEPARATE from scorer mechanics. If the gold corpus
itself is right, the matcher work in #2047 has a stable target to aim
at.

## Files

- `scripts/audit/code_review_benchmark.py` — entry point + scoring
  logic + corpus loader. Read only; do NOT modify scorer mechanics.
- `audit/code_review_benchmark/gold/*.yaml` (or `.json`) — the gold
  corpus. Find with `find audit/code_review_benchmark -type f` and
  read each gold case.
- The PR diffs the corpus references — fetch each via
  `gh pr diff <NUMBER>` and compare against the gold findings.

## What to do (verifiable steps)

1. **Worktree setup.** You were spawned with `--worktree`; verify
   `git rev-parse --show-toplevel` + `git branch --show-current` and
   cite the raw output.

2. **Survey corpus.** `find audit/code_review_benchmark -name 'gold*'
   -type f` then `cat` each. Quote the raw output (or paste a summary
   table of {case_id, target_pr, finding_count, finding_ids}).

3. **For each case**, fetch the underlying PR diff:
   ```
   gh pr diff <NUMBER>
   ```
   For each gold finding, verify the diff actually contains the
   issue the finding describes. Note any:
   - **Stale findings** — the PR has been patched and the issue no
     longer exists in the merged form.
   - **Missing semantically-valid findings** — issues a competent
     reviewer would mention that the gold corpus doesn't yet have.
   - **Overly tight finding ids** — short ids like `arg-max` that a
     reasonable model would emit as e.g. `prompt-on-command-line-leak-and-arg-max-dos`
     (the #2047 trigger). Either widen the id or add a `synonyms` /
     `aliases` field that the matcher uses for fuzzy matching. CHECK
     `code_review_benchmark.py` first for what schema fields the
     loader actually consumes — only use fields that ship today.

4. **Refresh.** Edit gold files to:
   - Remove stale findings (each with a one-line comment explaining
     why).
   - Add missing findings (each grounded in a specific diff line —
     cite as `file:line` in the gold YAML/JSON).
   - Adjust ids / aliases per (3).

5. **Run the benchmark to see your work cause an improvement.**
   ```
   cd /Users/krisztiankoos/projects/learn-ukrainian
   # venv symlinked into worktree by delegate.py
   .venv/bin/python scripts/audit/code_review_benchmark.py --help
   # venv symlinked into worktree by delegate.py
   .venv/bin/python scripts/audit/code_review_benchmark.py <args-that-replay-an-existing-cell>
   # then cd back to the worktree to commit the gold edits
   cd -
   ```
   Compare the F1 of one re-scored cell against the pre-refresh
   number. Quote both numbers raw. The new gold should be either
   strictly better (higher F1 on the cell that previously scored low)
   OR explicitly comment-justified why no F1 change is expected
   (e.g. corpus widened to capture findings the model wasn't even
   emitting).

6. **Commit + push + PR.**
   ```
   chore(audit): refresh code-review benchmark gold corpus (#2042)
   ```
   Body includes: per-case summary of changes + raw F1 before/after
   for at least one re-scored cell + `Closes #2042`.

## Verifiable claims required in the PR body

Per `docs/best-practices/deterministic-over-hallucination.md`:

| Claim | Evidence |
|---|---|
| "Reviewed N gold cases against M PRs" | command + cwd + `find` and `gh pr diff` raw outputs |
| "Added K findings, removed L, adjusted P" | per-case diff snippet from `git --no-pager diff audit/code_review_benchmark/gold/` |
| "F1 improved" or "F1 unchanged but corpus widened" | raw before/after F1 numbers from `code_review_benchmark.py` runs |

## Out of scope

- DO NOT touch `scripts/audit/code_review_benchmark.py` (matcher /
  scorer code) — that's #2047, separate dispatch.
- DO NOT change benchmark cell raw responses or any model output files.
- DO NOT add new benchmark cases beyond #2042's stated scope
  (refresh, not expansion).

## Acceptance

- PR opens, body includes raw evidence lines above
- `Test (pytest)` CI required check passes
- Gold corpus files updated; matcher untouched
- Closes #2042

## Pointers

- Issue: `gh issue view 2042`
- Related (DO NOT touch): #2047 (matcher fix), `code_review_benchmark.py`
- Trailer: every commit gets `X-Agent: gemini/2042-codereview-gold-refresh`
