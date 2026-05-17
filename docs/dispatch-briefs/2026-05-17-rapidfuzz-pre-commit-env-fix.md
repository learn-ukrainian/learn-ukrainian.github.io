# Dispatch: fix pre-commit hook env divergence (rapidfuzz import) (#2059)

## Why this matters

`MEMORY.md #M-7` says "pytest locally before push to main" (hard rule).
The pre-commit hook chain is designed to enforce this. But the hook
**fails inside its subshell** while the same test **passes when run
directly** with the same Python interpreter. That false failure
forced every commit in PR #2055 + the entire 2026-05-17 night
cascade (#2060/#2061/#2062/#2063/#2068/#2069/#2070) to use
`--no-verify`, which silently disables the safety net.

Read `gh issue view 2059` for full diagnosis. Summary:

- Inside the hook subshell: `ModuleNotFoundError: No module named 'rapidfuzz'`
# venv symlinked into worktree by delegate.py
- Outside: `.venv/bin/python -c "import rapidfuzz"` → `3.10.1`
- Same Python, same `.venv`, different result.

The hook isolates each entry in a sanitized subshell. Most likely
cause: `PYTHONPATH` / `VIRTUAL_ENV` / `PATH` gets stripped, or
pre-commit's own venv shadow takes precedence over `.venv/`.

## Files

- `.pre-commit-config.yaml` — the canonical hook configuration. Each
  hook entry has `language` + `entry` + optional `language_version` and
  `additional_dependencies`.
- `.git/hooks/pre-commit` (generated; don't edit directly — regenerated
  by `pre-commit install`).
- `requirements-lock.txt` — pinned dependencies including rapidfuzz==3.10.1.
- Any hook source script that imports `rapidfuzz` — find with
  `grep -rln "import rapidfuzz" scripts/`.

## What to do (verifiable steps)

1. **Worktree setup.** You were spawned with `--worktree`; verify
   `git rev-parse --show-toplevel` and `git branch --show-current` and
   cite the raw output. All edits stay inside that worktree.

2. **Reproduce.** From the worktree, run the failing hook directly:
   ```bash
   .git/hooks/pre-commit  # see what fails
   ```
   # venv symlinked into worktree by delegate.py
   Then run the offending entry's command directly with `.venv/bin/python`.
   Paste the raw outputs side-by-side.

3. **Diagnose.** Likely culprits, check in order:
   - **a.** Pre-commit's `language: python` creates an isolated venv at
     `~/.cache/pre-commit/repo<hash>/py_env-*/` and runs hooks inside
     IT, not `.venv`. Look at `.pre-commit-config.yaml` for the
     `language` of the failing hook. If it's `python`, you need to
     either:
       * Add `rapidfuzz` to that hook's `additional_dependencies`
         (cleanest if the hook is project-owned and small), OR
       * Switch the hook's `language` to `system` and have it call
         # venv symlinked into worktree by delegate.py
         `.venv/bin/python -m pytest ...` directly (correct for hooks
         that already depend on the project's full lockfile).
   - **b.** `PYTHONPATH` / `VIRTUAL_ENV` env-var stripping. Run the
     hook with `set -x` to see the env.
   - **c.** A stale pre-commit cache that pre-dates the rapidfuzz pin.
     `pre-commit clean && pre-commit install --install-hooks` rebuilds.

4. **Pick the fix.** Most defensible options:
   - **A.** For project-pytest hooks: set `language: system` so they
     use `.venv` directly (matches MEMORY #M-7's intent: pytest with
     the real lockfile).
   - **B.** For lint hooks that need rapidfuzz: add it to
     `additional_dependencies` in `.pre-commit-config.yaml`.

   Quote the exact diff in the PR body.

5. **Verify.**
   ```bash
   # Trigger a fake commit to exercise the hook chain
   touch /tmp/sentinel
   git add /tmp/sentinel 2>/dev/null || true  # may fail, that's fine
   git commit --allow-empty -m 'test(hook): pre-commit invocation probe'
   ```
   (Or use `pre-commit run --all-files --hook-stage commit` if that
   reproduces the failing hook directly.)
   The hook chain MUST pass without `--no-verify`. Paste raw output.

6. **Commit.** Conventional message:
   ```
   fix(hooks): pre-commit env divergence — rapidfuzz import in hook subshell (#2059)
   ```
   Body includes the diagnosis (which of 3a/3b/3c was the actual
   cause), the chosen fix, and the verify-step output. Closing line:
   `Closes #2059`.

7. **Push + open PR.** `git push -u origin {branch}` then
   `gh pr create`. Title mirrors commit subject.

## Verifiable claims required in the PR body

Per `docs/best-practices/deterministic-over-hallucination.md`:

| Claim | Evidence |
|---|---|
| "Pre-commit chain now passes WITHOUT `--no-verify`" | raw output of a real commit (or `pre-commit run --all-files`) that exits 0 |
| "rapidfuzz importable in hook subshell" | raw output of the previously-failing hook entry, run from the worktree, showing the import succeeding |
| "Diagnosis confirmed" | the actual env-divergence cause — e.g. "pre-commit's isolated venv lacks rapidfuzz; switched hook to `language: system`" — backed by `cat .pre-commit-config.yaml | grep -A 3 <hook-id>` raw output |

## Out of scope

- Don't fix #2057 (Dagger venv silent-fail) here — separate dispatch
  is in flight already on branch `codex/2057-dagger-pre-push-fix`.
- Don't disable any hook to make the failure go away. If a hook is
  genuinely broken-by-design, file a follow-up issue instead of
  silently deleting it from the config.
- Don't touch the GHA workflow — same root cause path, different
  environment.

## Acceptance

- PR opens, body includes the raw evidence lines above
- `Test (pytest)` CI required check passes
- Real commit from the worktree succeeds without `--no-verify`
- Closes #2059

## Pointers

- Issue: `gh issue view 2059`
- Predecessor brief: `docs/session-state/2026-05-17-russianism-judge-evidence-layer-handoff.md` § "Open blocker"
- Trailer: every commit gets `X-Agent: codex/2059-rapidfuzz-pre-commit-fix`
