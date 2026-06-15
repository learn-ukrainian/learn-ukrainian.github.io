# Dispatch — fix #3232 (#M-7 hook) failing test: detached-HEAD fragility

PR #3232 (`codex/hook-pytest-push-1908`) is BLOCKED — `test_stamp_pytest_bash_smoke`
fails. The hook LOGIC is sound (9/10 tests pass); only this one test is environment-fragile.

## Root cause (verified)
`test_stamp_pytest_bash_smoke` reads `git branch --show-current` from `REPO_ROOT` and
expects the stamper to create `learn-uk-pytest.<branch>.stamp`. But in CI (and any
detached-HEAD checkout) `git branch --show-current` returns **empty**, so:
1. the expected marker name becomes `learn-uk-pytest..stamp` (double dot), AND
2. the stamper's `[ -n "$BRANCH" ] || exit 0` guard makes it correctly **bail without
   stamping** (it can't write a per-branch marker with no branch) → the asserted marker
   never exists → test fails.

The stamper's real behavior is CORRECT (Claude always runs on a named branch locally);
the TEST just doesn't control the branch context.

## Fix (test only — do NOT change the hook logic)
Make `test_stamp_pytest_bash_smoke` deterministic: run the stamper inside a **throwaway
git repo on a named branch** so `git branch --show-current` is non-empty and predictable.
e.g. in `tmp_path`: `git init -b testbranch`, set `user.email`/`user.name`, one commit,
then run the stamper with `cwd=<that repo>` and `TMPDIR=tmp_path`, and assert
`(tmp_path / "learn-uk-pytest.testbranch.stamp").exists()`. (Do NOT rely on the outer
repo's branch.)

Optionally add a second assertion that with a detached HEAD (empty branch) the stamper
exits 0 and writes NO marker (lock in the correct bail behavior).

## Steps
1. `--base codex/hook-pytest-push-1908` (this dispatch builds on the PR branch). Confirm `git status`.
2. Fix ONLY `tests/test_guard_push_pytest.py::test_stamp_pytest_bash_smoke`. Do NOT touch
   `stamp-pytest.sh` / `guard-push-pytest.py` / `settings.json`.
3. `.venv/bin/python -m pytest tests/test_guard_push_pytest.py -q` → 10 passed. `ruff check` clean.
4. Commit `fix(test): make pytest-stamp smoke test branch-deterministic (#1908)` + `X-Agent: codex/hook-pytest-push-fix`.
5. `git push origin HEAD:codex/hook-pytest-push-1908` to update PR #3232 in place. NO merge.

## #M-4
Paste the raw `pytest` final line (`10 passed`) and `ruff` final line.
