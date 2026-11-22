---
description: An owned open pull request is merged, closed, or being fixed before the session ends
alwaysApply: true
---

# Never leave a PR sitting

An open pull request this seat owns is unfinished.

- A driver lands it with the `full-send` skill (merge gate, enqueue, `merge_closeout --apply`). A briefed worker runs its chain to the end with `full-send`; a worker whose brief says `full-stop`, or anyone holding another driver's PR, hands it over ready to merge and never merges.
- A driver closes it when it is obsolete, and deletes its branch.
- A conflict, a queue kick, red CI, or review changes are work in the same session. Fix them. If the head moves, get a new exact-head review before merge.
- Do not end a session by reporting an open pull request and stopping. "CI is running" and "queued" are not a stopping point. A driver stays until it merges, or until a fix for the failure is in flight. A briefed worker's terminal state is MERGED with closeout; when its brief says `full-stop`, it is the hand-off: `READY_TO_MERGE` with protection verified, handed to the named receiving driver.
