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
