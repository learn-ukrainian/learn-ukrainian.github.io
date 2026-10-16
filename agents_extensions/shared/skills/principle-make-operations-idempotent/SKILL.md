---
name: principle-make-operations-idempotent
description: Design commands and loops so a retry or a crash converges to the same
  end state. Use for /principle-make-operations-idempotent.
---

# Make operations idempotent

Every state-changing step should answer: what happens if this runs twice, and what happens if the previous run crashed halfway?

Read the current state, compare it with the goal, and apply only the difference. A repeat then finds nothing left to do.

Anything a run leaves behind (a lock, a temporary file, a half-written record, a claimed job) must be recognizable as stale by the next run, including after a crash at any step. Prefer write-to-temp then rename, or compare by content rather than creation order.

If the outcome depends on whatever debris the last run left, add a reconciliation step. Do not invent a second cleanup path for repository worktrees. Use the documented reaper (`workflow.md`).

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
