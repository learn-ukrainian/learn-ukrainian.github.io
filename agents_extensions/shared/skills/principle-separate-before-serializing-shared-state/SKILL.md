---
name: principle-separate-before-serializing-shared-state
description: Give concurrent actors separate write targets before reaching for a lock.
  Use for /principle-separate-before-serializing-shared-state.
---

# Separate before serializing shared state

When concurrent actors might write the same file, branch, key, or object, ask whether they need that same mutable object.

1. Name the shared mutable state.
2. By default, remove the shared write. Give each actor its own file, key, branch, or directory, and merge only when reading the results. Two writers updating different fields of one JSON file still share a write target.
3. Serialize with a lock, a single writer, or an atomic compare-and-swap only when one shared writer is a real invariant. "We need a lock" is a design smell to check, not the default.

Instructions are not concurrency control. Repository worktrees and branches follow `workflow.md`. Do not invent a second lock or cleanup path.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
