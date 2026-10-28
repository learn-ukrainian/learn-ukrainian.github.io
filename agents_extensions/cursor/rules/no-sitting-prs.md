# Never leave a PR sitting (Cursor)

Deployed digest: `.cursor/rules/no-sitting-prs.mdc` (`alwaysApply`).

An open pull request this seat owns is unfinished. A driver lands it with the
`full-send` skill, closes it when obsolete, or keeps a same-session fix in
flight, and stays until it merges. A worker runs its chain to the end
(`full-send`: enqueue after the recorded exact-head verdict and green CI, MERGED,
closeout) and never closes a PR it does not own; when its brief says `full-stop`,
its terminal state is the hand-off, `READY_TO_MERGE` with protection verified and
handed to the named receiving driver. A status report is not a stopping point.
