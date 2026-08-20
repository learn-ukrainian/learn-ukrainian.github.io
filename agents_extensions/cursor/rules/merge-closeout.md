# Merge closeout (Cursor)

Deployed digest: `.cursor/rules/merge-closeout.mdc` (`alwaysApply`).

`MERGED` is not closeout. Universal git closeout: remote branch gone, local
branch gone, worktree reaped (`reap_worktrees.py --apply --merged`). Canonical:
`docs/runbooks/worktree-cleanup.md` § Immediate cleanup after merge.

Task-specific proofs (host pull, tunnel, occupancy, restarts) stay on that
task. Do not promote them into standing merge hygiene.
