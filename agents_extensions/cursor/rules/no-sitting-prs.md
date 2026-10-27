# Never leave a PR sitting (Cursor)

Deployed digest: `.cursor/rules/no-sitting-prs.mdc` (`alwaysApply`).

An open pull request this seat owns is unfinished. A driver lands it with the
`full-send` skill, closes it when obsolete, or keeps a same-session fix in
flight, and stays until it merges. A worker never merges or closes: its
terminal state is the `full-stop` hand-off, `READY_TO_MERGE` with protection
verified and handed to the named receiving driver. A status report is not a
stopping point.
