# Codex dispatch — #1682 test_delegate worktree pollution

## Context

`tests/test_delegate.py::test_dispatch_creates_worktree_and_records_it` fails locally if `.worktrees/codex-1383/` exists on disk (orphan dir from a long-dead dispatch, not registered in `git worktree list`). The test asserts `state["worktree_reused"] is False` but dispatch sees the stale dir and treats it as reused → assertion fails.

Two fix options per #1682:
- **Option A (cleaner):** `tmp_path` fixture + `monkeypatch` the worktrees-base directory the harness uses
- **Option B (one-line):** unique task-id per run (e.g. `f"issue-{uuid4().hex[:8]}-smoke"`) AND finalizer cleanup

Pick A if `delegate.py` exposes a clean way to override the worktrees base; otherwise B.

## Worktree

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b codex/1682-test-delegate-isolation .worktrees/codex-1682 origin/main
cd .worktrees/codex-1682
```

## Numbered steps

1. **Verify branch base.** `git log --oneline HEAD..origin/main` should be empty.

2. **Reproduce the failure.**
   ```bash
   mkdir -p .worktrees/codex-1383/data
   .venv/bin/python -m pytest tests/test_delegate.py::test_dispatch_creates_worktree_and_records_it -x
   # Expected: AssertionError on worktree_reused
   rm -rf .worktrees/codex-1383
   .venv/bin/python -m pytest tests/test_delegate.py::test_dispatch_creates_worktree_and_records_it -x
   # Expected: pass
   ```

3. **Inspect `delegate.py`** for how the worktrees base directory is determined. Look for env-var override (e.g. `WORKTREES_BASE`) or function arg. If clean override exists → Option A. If not → Option B.

4. **Implement the fix.**

   **Option A:** In the test, set `monkeypatch.setenv("DELEGATE_WORKTREES_BASE", str(tmp_path))` (or whatever the actual var/arg is) and let pytest's `tmp_path` give an isolated dir per test.

   **Option B:** Replace hardcoded `issue-1383-smoke` with `f"issue-{uuid.uuid4().hex[:8]}-smoke"` AND add a finalizer:
   ```python
   def test_dispatch_creates_worktree_and_records_it(tmp_path):
       task_id = f"issue-{uuid.uuid4().hex[:8]}-smoke"
       try:
           # ... existing test body using task_id ...
       finally:
           shutil.rmtree(f".worktrees/codex-{task_id.split('-')[1]}", ignore_errors=True)
           subprocess.run(["git", "worktree", "prune"], check=False)
   ```

5. **Verify.** Run the test 3 times in a row to check for ordering issues:
   ```bash
   for i in 1 2 3; do .venv/bin/python -m pytest tests/test_delegate.py::test_dispatch_creates_worktree_and_records_it -x || break; done
   ```

6. **Run the full test_delegate suite** to make sure no other test regressed:
   ```bash
   .venv/bin/python -m pytest tests/test_delegate.py -x -q
   ```

7. **Run ruff.** `.venv/bin/ruff check tests/`

8. **Commit.**
   ```
   test(delegate): isolate test_dispatch_creates_worktree from real .worktrees/ dir (#1682)
   ```

9. **Push + PR.**
   ```bash
   git push -u origin codex/1682-test-delegate-isolation
   gh pr create --title "test(delegate): isolate test_dispatch_creates_worktree from real .worktrees/ dir (#1682)" --body "$(cat <<'EOF'
## Summary

Fixes `tests/test_delegate.py::test_dispatch_creates_worktree_and_records_it` flaking on machines where `.worktrees/codex-1383/` exists on disk.

## Approach

<state Option A or Option B + why>

## Verification

- Reproduced the original failure with `mkdir -p .worktrees/codex-1383/data` before run
- Fix passes 3 consecutive runs
- Full `tests/test_delegate.py` suite green
- ruff clean

Closes #1682.
EOF
)"
   ```

10. **Do NOT enable auto-merge.**

## Acceptance criteria

- Test passes regardless of pre-existing `.worktrees/` dirs
- 3 consecutive runs green
- No regression elsewhere in `tests/test_delegate.py`
- ruff clean

## Discipline

- No `--no-verify`
- Reference #1682 in commit message
- Worktree cleanup post-merge by next session
