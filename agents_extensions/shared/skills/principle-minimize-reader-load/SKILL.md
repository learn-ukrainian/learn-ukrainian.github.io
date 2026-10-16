---
name: principle-minimize-reader-load
description: Reduce layers to trace and state a reader must remember. Use for /principle-minimize-reader-load.
---

# Minimize reader load

Maintainability is the work a reader does to answer "where does X come from?" and "what can change X?". Track layers to trace, and state the reader must hold. Line count is only a proxy.

- Collapse a wrapper with one caller, an adapter with no second implementation, and a pass-through that repeats the same arguments.
- A layer must change the abstraction. If it does not, inline it.
- Prefer a small interface that hides a real decision over a wide one that forces the reader to learn the implementation too.
- Prefer pure functions, locals over fields, and derived values over synced copies.
- Name an invariant at the boundary once.

Add a layer or a piece of state only when it removes at least as much reader load elsewhere.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
