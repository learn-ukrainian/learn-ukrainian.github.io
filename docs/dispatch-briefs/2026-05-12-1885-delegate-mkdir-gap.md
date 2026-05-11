# Codex dispatch brief — `delegate.py` mkdir gap for task_id with agent prefix

> **Issue:** #1885
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/1885-delegate-mkdir-gap/`
> **Base:** `origin/main`
> **Hard timeout:** 1200s (20 min)
> **Silence timeout:** 480s (8 min)
> **Effort:** medium

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. Use absolute paths and `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1885-delegate-mkdir-gap && ...` for every command. Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python` for the venv.

---

## Goal

Fix `delegate.py dispatch` crashing on first dispatch when the `batch_state/tasks/logs/{agent}/` subdir doesn't exist.

### Root cause (verified inline before dispatch)

`scripts/delegate.py:1021-1030`:

```python
log_dir = _TASKS_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)       # creates logs/, NOT logs/codex/
stdout_log = log_dir / f"{task_id}.stdout.log"   # task_id is e.g. "codex/1885-foo"
stderr_log = log_dir / f"{task_id}.stderr.log"
# ...
stdout_fd = open(stdout_log, "ab", ...)  # ← FileNotFoundError if logs/codex/ missing
stderr_fd = open(stderr_log, "ab", ...)
```

When `task_id` contains a `/` (e.g. `codex/1885-foo`), the implicit subdir is not auto-created by the existing `log_dir.mkdir`. Result: orphaned worktree + branch + crashed dispatch (incident 2026-05-11 evening: #1883-hook-trim).

## Numbered steps

1. **Verify worktree base:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1885-delegate-mkdir-gap && git log --oneline -3
   ```
   Quote raw output. Branch must be `codex/1885-delegate-mkdir-gap`.

2. **Read these first:**
   - `scripts/delegate.py:1015-1060` — the open-log block + the Popen block.
   - The block above (~1000-1015) where worktree creation happens. **Verify worktree creation runs BEFORE the log-file open** — that's the side-effect-leak path described in the issue. If worktree creation runs first, the fix must EITHER (a) reorder so log-dir setup runs first, OR (b) wrap the log-open in try/except and clean up the worktree on failure. AC #3 requires one of these.
   - `tests/` for existing `delegate.py` tests (e.g. `tests/test_delegate*.py`) — find the testing convention before adding a new one.

3. **Apply the fix.** Minimum:
   ```python
   stdout_log = log_dir / f"{task_id}.stdout.log"
   stderr_log = log_dir / f"{task_id}.stderr.log"
   # Ensure parent dirs exist — task_id may contain '/' (e.g. "codex/1885-foo"),
   # which makes the log path live in a per-agent subdir that log_dir.mkdir
   # above does NOT cover. Belt-and-suspenders the parent of each log file.
   stdout_log.parent.mkdir(parents=True, exist_ok=True)
   stderr_log.parent.mkdir(parents=True, exist_ok=True)
   stdout_fd = open(stdout_log, "ab", buffering=0)  # noqa: SIM115
   stderr_fd = open(stderr_log, "ab", buffering=0)  # noqa: SIM115
   ```

4. **Address AC #3 (no orphaned worktree on log-setup failure).** Two options — pick ONE based on what's cleaner given the existing code shape:

   - (a) **Reorder.** Move the worktree creation block from above the log-dir setup to AFTER it. Log-dir setup is cheap and fails fast; worktree side-effect happens only when we know the dispatch can proceed.
   - (b) **try/except + cleanup.** Wrap the log-file open in try/except; on failure, call the existing worktree-cleanup helper (find it; if no helper exists, this option is too heavy — pick (a)).

   Document which you picked in the commit body and explain why.

5. **Regression test** (AC #4). Add to whichever delegate-tests file is conventional (mirror the existing pattern). Shape:

   ```python
   def test_dispatch_creates_logs_subdir_for_slashed_task_id(tmp_path, monkeypatch):
       # Synthetic tasks dir with NO codex/ subdir
       # Monkeypatch _TASKS_DIR to tmp_path
       # Dispatch with task_id="codex/test-mkdir-1885"
       # Assert tmp_path/logs/codex/test-mkdir-1885.stdout.log exists OR
       # is opened without FileNotFoundError
       # No real subprocess.Popen needed — mock it; only the path-handling
       # matters for this regression
   ```

   Keep it tight. The point is to lock in the behavior; not exercise the full dispatch.

6. **Run tests:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1885-delegate-mkdir-gap && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -m pytest tests/test_delegate*.py -v 2>&1 | tail -20
   ```
   Quote raw final summary line. Bare "tests pass" is not acceptable per #M-4.

7. **Ruff:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1885-delegate-mkdir-gap && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/delegate.py tests/test_delegate*.py 2>&1 | tail -10
   ```
   Quote raw output.

8. **Commit** with X-Agent trailer:
   ```
   fix(delegate): mkdir parent of stdout/stderr logs for slashed task_id (#1885)

   <2-3 line body — explain the slash-in-task_id failure mode>

   Tests: <quote raw pytest summary>

   X-Agent: codex/1885-delegate-mkdir-gap
   ```

9. **Push + `gh pr create`.** Reference issue with `Closes #1885`. Do NOT auto-merge.

---

## Pre-submit checklist (MANDATORY)

- [ ] `.python-version` / `.yamllint` / `.markdownlint.json` unchanged
- [ ] No `status/*.json` / `audit/*-review.md` / `review/*-review.md` files in diff
- [ ] No `sys.executable` — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertions weakened
- [ ] Every changed file directly related to #1885 (expected: `scripts/delegate.py` + 1 test file)
- [ ] Total files changed ≤ 3
- [ ] Code runs without `NameError` / `KeyError` / `ImportError`
- [ ] X-Agent trailer present

---

## #M-4 deterministic-verification block

| Claim | Tool | Output form |
|---|---|---|
| Branch base | `git log --oneline -3` from worktree | Quote 3 lines |
| Fix applied | `git diff scripts/delegate.py` | Quote the relevant hunk |
| AC #3 path chosen | Prose statement in commit body | Document which option (a or b) and why |
| Test added | `git diff tests/` | Quote the new test name + body |
| Tests pass | `pytest tests/test_delegate*.py` | Quote final summary line raw |
| Ruff clean | `ruff check ...` | Quote raw output |
| Commit + X-Agent trailer | `git log -1 --format=full` | Quote raw |

"I verified X" without quoted tool output is treated as hallucination.

---

## Out of scope

- Refactoring the broader log-path scheme (e.g. moving from `logs/{agent}/{task}.log` to flat `logs/{agent}-{task}.log`). That's a separate design discussion.
- Cleanup of orphaned worktrees from past incidents. Mention but do not fix in this PR.

---

## References

- Issue: https://github.com/krisztiankoos/learn-ukrainian/issues/1885
- Incident: 2026-05-11 evening — `codex/1883-hook-trim` dispatch crashed with `FileNotFoundError`; orphaned worktree had to be `git worktree remove --force`'d
- Workaround applied: `mkdir -p batch_state/tasks/logs/{codex,claude,gemini}` (this fix obsoletes the workaround)
