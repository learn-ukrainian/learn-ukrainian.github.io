# Shell cwd drift → false observations from relative-path reads

## What broke

The driver's persistent shell cwd silently drifts between Bash calls (a `cd` in
a compound command, a worktree removal, a background task). Subsequent
relative-path reads then execute somewhere other than the primary checkout and
return *plausible but wrong* results — most dangerously, **false negatives**
("0 artifacts", "dir is empty") that read as real state.

Incident log:

- **2026-07-05 (#27):** wrong-cwd `git push` printed "Everything up-to-date"
  while the branch was unpushed.
- **2026-07-07 AM (#29):** 4 cwd-drift incidents in one session; a wrong-cwd
  `ls` read 0 artifacts and nearly caused a bakeoff-matrix false alarm.
- **2026-07-07 PM (#31, ESCAPED):** driver `cd`'d into a dispatch worktree to
  commit, then ran `ls audit/2026-07-06-qg-bakeoff-multirun/` relative — the
  worktree's copy of that dir contains only the git-TRACKED `SCORECARD.md`
  (the ~318 cell JSONs are gitignored → exist only in the primary checkout).
  Concluded "artifacts gone", posted a false resume-state alarm on #4763.
  The user caught it; retracted.

## Why

Two compounding mechanisms:

1. **Shell state is invisible**: nothing in a relative command's output says
   where it ran. `ls` in the wrong place doesn't error — it answers a
   different question, confidently.
2. **Worktrees silently shadow gitignored data**: a worktree has the full
   tracked tree, so paths "exist" and partial reads (e.g. the tracked
   SCORECARD.md) succeed — which *confirms* the wrong mental model while the
   gitignored payload is absent. The trap specifically defeats the "spot-check
   one file" sanity habit.

## Prevention

- **Absolute primary-checkout paths for ALL artifact/data reads** (`ls`,
  `find`, `cat` on `audit/`, `data/`, `.agent/`). Relative paths only for git
  operations that *must* run inside a specific worktree.
- `pwd` (or `pwd &&` prefix) before any relative read whose result feeds a
  conclusion — cheap, and makes the transcript auditable.
- **Negative observations get one independent confirmation** before they leave
  the session (a `find` from `/` root, or a re-read with an absolute path) —
  "X is missing" is a claim about the filesystem, hold it to #M-4.
- Remember the shadow rule: *a worktree is a tracked-only view; gitignored
  data dirs are primary-checkout-only.*

## 2026-07-10 — incidents 4–7, one session (infra lane): the class is chronic, one NEW variant is destructive

**Symptoms (same session, four bites):**
1. `git worktree add` with a relative path while cwd sat in another worktree → new worktree nested INSIDE a stale worktree; a grep then read the stale tree's uncommitted files as if they were main's.
2. `cd <reaped-worktree> 2>/dev/null && git log` — cd failed silently, git log answered from the STALE cwd; looked exactly like a wrong-branch worktree (false alarm, caught by re-running with `git -C <abs>`).
3. **NEW, destructive variant:** `delegate.py dispatch` fired while cwd was a fix worktree → the dispatch wrote its task state/result into THAT worktree's `batch_state/` → the worktree was auto-reaped when its PR merged → the running review's artifacts were destroyed mid-flight (review re-fired; ~5 min + one seat call wasted).
4. Relative `.venv/bin/python` in a background command from a worktree without the venv symlink → instant "No such file or directory"; the stuck until-loop wrapper needed a manual TaskStop.

**Why it recurs:** shell cwd persists across Bash calls and across LONG gaps (watcher notifications interleave other work between beats); every "quick relative command" silently binds to whatever the last `cd` was — possibly minutes and several contexts ago.

**Related guard blindness (same family):** guard-primary-checkout-write resolves relative
write targets against the SESSION cwd, ignoring an in-command `cd` — so a legitimate
worktree write with a relative heredoc target gets blocked (false positive), while the
absolute-path form passes. Same class as #4899 (guard-branch-switch cwd detection).

**Prevention (tightened):**
- Long-running/background commands: FIRST token is `cd /abs/main/root &&` — no exceptions, even for "obviously safe" one-liners.
- `delegate.py dispatch` (and anything writing `batch_state/`) runs ONLY from the main root; a dispatch fired from a worktree writes state into a reapable directory (variant 3).
- Read-only git against another tree: always `git -C /abs/path`, never `cd && git`.
- Never `X 2>/dev/null && Y` where X is a `cd` — a failed cd makes Y lie about its subject.
- Worktree writes from Bash: absolute target paths (also sidesteps the guard FP above).
- Candidate hard fix (follow-up): delegate.py should refuse (or warn + re-root) when invoked with cwd ≠ primary checkout root — deterministically detectable in the runtime.
