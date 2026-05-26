# Dispatch brief — CI gate for MDX-source artifact parity (#2291)

**Agent**: gemini (gemini-3.1-pro-preview)
**Mode**: workspace-write
**Effort**: high
**Branch base**: `origin/main`
**Task ID**: `issue-2291-mdx-source-parity-gate-gemini-2026-05-26`

## Why this matters

PR #2274 shipped a b1/adjectives-comparative module as MDX-only (rendered Starlight artifact) WITHOUT the curriculum/l2-uk-en/b1/adjectives-comparative/ source artifacts. The mismatch was caught manually 2026-05-25 and backfilled via #2293, but the prevent-recurrence piece never landed.

This issue asks for a CI gate that **rejects PRs that change `starlight/src/content/docs/<level>/<slug>.mdx` without a matching change under `curriculum/l2-uk-en/<level>/<slug>/`**. The gate runs as a GitHub Actions workflow + a local pre-commit hook (same script, two surfaces).

## Read first

- `gh issue view 2291` — full issue body + scope notes
- `docs/dispatch-briefs/2026-05-26-a1-m20-anchor-codex.md` §"Anchor must ship FULL source artifacts" — context on the failure mode
- `.github/workflows/ci.yml` — existing CI workflow shape (where to add the new gate)
- `.pre-commit-config.yaml` — local hook pattern (mirror this for the new gate)
- `scripts/audit/` — existing gate scripts (use the conventions established here)
- Recent PR #2293 + #2274 + #2290 — the failure mode + the manual backfill that motivates this gate

## What the gate must do

For each MDX file changed in the PR/commit:

1. Extract `(level, slug)` from the path `starlight/src/content/docs/<level>/<slug>.mdx`
2. Check that AT LEAST ONE file under `curriculum/l2-uk-en/<level>/<slug>/` is also changed in the same commit/PR
3. If MDX changed but no curriculum source file changed: **FAIL** with a clear message naming the missing source dir and the modules affected

For each curriculum source file changed:
- No symmetric requirement (source-only edits ARE allowed — e.g. pre-render edits, plan changes that don't yet re-render). Asymmetric rule.

## Required exemptions

Per the issue body + #2292 close note on #2291:

1. **Legacy tracks**: some seminars (HIST, BIO, LIT) have MDX-only published modules that pre-date the V7 source-artifact contract. Exempt their level paths by allowlist. The allowlist file should be `scripts/audit/mdx_source_parity_legacy_tracks.yaml` with a top-level `legacy_levels:` list.
2. **Bulk MDX regeneration commits**: if a commit changes >50 MDX files AND the commit message contains `[regen-mdx]` or `[bulk-regen]`, allow through. Single-file regen still subject to the rule.
3. **Asset-only diffs**: pure formatting changes in MDX (whitespace, trailing newlines) where the parsed AST is unchanged. Use the existing `mdx_render` parser if available, OR scope this exemption to "diff is purely whitespace per `git diff --check`" and defer the AST check to a follow-up.

## Required steps

1. **Worktree setup**:
   - `git worktree add -b gemini/issue-2291-mdx-source-parity-gate .worktrees/dispatch/gemini/issue-2291-mdx-source-parity-gate-2026-05-26 origin/main`
   - `cd .worktrees/dispatch/gemini/issue-2291-mdx-source-parity-gate-2026-05-26`
   - `ln -s ../../../../.venv .venv` (# venv symlinked)

2. **Read** the existing gate scripts under `scripts/audit/` to match the project's pattern (especially `lint_dispatch_brief.py` which has a similar "loop over changed paths, check rules, report violations" shape).

3. **Implement** `scripts/audit/check_mdx_source_parity.py`:
   - CLI: `--all` (scan whole repo), `--changed-vs-base BASE` (compare against base branch, e.g. main), `--files <list>` (scan explicit files)
   - Returns exit 0 if clean, 1 if violations found, 2 if CLI usage error
   - Output format matching other audit scripts: `path:line: message` or `path: message`
   - Reads `scripts/audit/mdx_source_parity_legacy_tracks.yaml` for the legacy-level allowlist
   - Handles the bulk-regen exemption via env var `MDX_PARITY_BULK_REGEN=1` (CI sets it conditionally)

4. **Create** `scripts/audit/mdx_source_parity_legacy_tracks.yaml` with a starter allowlist + clear comment that the list should shrink as legacy tracks migrate to source-artifact contracts.

5. **Wire as pre-commit hook** in `.pre-commit-config.yaml`:
   - id: `check-mdx-source-parity`
   - Runs only on commits that touch `starlight/src/content/docs/**/*.mdx`
   - Calls the script with `--files <staged-mdx-files>` and the base set to the merge-base with origin/main

6. **Wire as CI workflow** in `.github/workflows/ci.yml`:
   - New job: `mdx-source-parity`
   - Runs on `pull_request` events
   - Checks out the PR diff vs origin/main
   - Calls the script with `--changed-vs-base origin/main`
   - Fail on exit != 0; success otherwise. Mark as REQUIRED in branch protection (follow-up — orchestrator will add).

7. **Tests** at `tests/audit/test_check_mdx_source_parity.py`:
   - Fixture cases: MDX-only diff (should fail), MDX + source diff (pass), source-only diff (pass), legacy-level MDX-only (pass via allowlist), bulk-regen MDX-only with env var (pass), single-file regen without env var (fail), whitespace-only MDX diff (pass per the exemption)
   - At least 7 parametrized tests covering the matrix above

8. **Run tests** (do not use the pytest fail-fast flag — see #1942):
   ```bash
   .venv/bin/pytest tests/audit/test_check_mdx_source_parity.py -v
   .venv/bin/pytest tests/audit/ -q
   .venv/bin/ruff check scripts/audit/check_mdx_source_parity.py tests/audit/
   ```

9. **Smoke-test the pre-commit hook** locally:
   ```bash
   # Stage a deliberate MDX-only diff and try to commit; the hook should reject
   touch starlight/src/content/docs/a1/fake-test.mdx
   echo "fake content" > starlight/src/content/docs/a1/fake-test.mdx
   git add starlight/src/content/docs/a1/fake-test.mdx
   git commit -m "test commit (should fail at gate)"
   # Expect: pre-commit reports `check-mdx-source-parity` failure
   git restore --staged starlight/src/content/docs/a1/fake-test.mdx
   rm starlight/src/content/docs/a1/fake-test.mdx
   ```
   Document the manual smoke result in the PR body.

10. **Commit** with conventional format:
    ```
    feat(ci): reject PRs that ship MDX without matching curriculum source artifacts (#2291)
    ```
    With X-Agent trailer + Co-Authored-By: Gemini 3.1 Pro Preview <noreply@google.com>.

11. **Push + PR**:
    - `git push -u origin gemini/issue-2291-mdx-source-parity-gate`
    - `gh pr create --base main --head gemini/issue-2291-mdx-source-parity-gate --title "..." --body @PR_BODY.md`
    - PR body: closes #2291, explains the gate logic + exemption set + smoke test result, includes raw pytest + ruff output per #M-4.

## Hard constraints

- **No pytest fail-fast flag** (#1942).
- **No bridge calls mid-dispatch** (`ab ask-gemini`, `ab discuss`) — silence-timeout lesson from #2289.
- **Stay in your worktree** for ALL git operations.
- **Legacy-track allowlist** must be a separate YAML file, not hard-coded in the script. Comment in the YAML must state "shrink this list, don't grow it".
- **Asymmetric rule** — source-only edits MUST be allowed. The gate only fires on MDX-without-source, never source-without-MDX.
- **Do NOT auto-merge.** Open the PR for orchestrator review.

## Stop conditions

If during implementation you discover that:

1. The existing CI workflow has a structure that makes adding a new job non-trivial (e.g. requires reorganizing existing jobs) — STOP and file an issue, do NOT refactor unrelated CI structure.
2. The pre-commit framework version in `.pre-commit-config.yaml` doesn't support the hook shape you need — STOP and surface; the orchestrator will decide whether to upgrade pre-commit or simplify the gate.
3. There's overlap between this gate and an existing audit gate — STOP and consolidate via discussion, don't ship two gates that check the same thing.

## Done criteria

- PR opened with the script + YAML + tests + .pre-commit-config + ci.yml changes
- Tests pass (raw output in PR body)
- Ruff clean (raw output)
- Smoke test result included in PR body
- PR body closes #2291

## Estimated cost

- Wall-clock: 1.5-2.5h
- Code change: ~150-300 LOC + ~150-250 LOC tests + ~30 LOC yaml + ~20 LOC ci.yml + ~10 LOC pre-commit-config

## Why gemini-3.1-pro vs agy

- Design judgment: the legacy-track exemption requires curating an allowlist that reflects the current state of the repo (which tracks are legacy MDX-only). Needs reasoning about the curriculum structure.
- Test-matrix construction: 7+ parametrized cases that cover the matrix without over- or under-testing.
- CI wiring: requires understanding existing ci.yml structure + ordering of jobs + which jobs are required vs advisory.

These together push past "small mechanical edit" — gemini-pro is the right tool.
