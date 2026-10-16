---
name: principle-boundary-discipline
description: Put validation and error handling at system boundaries and keep business
  logic pure. Use for /principle-boundary-discipline.
---

# Boundary discipline

Validate, narrow, and handle errors where data enters: CLI arguments, config, network, external APIs, and stored blobs. Inside the system, trust typed values and do not re-validate them. Keep business logic in pure functions. Keep the shell thin.

Expose domain concepts, not the boundary's private representation. Do not re-export transport, storage, framework, or wire types. Parse raw input into domain types at the boundary.

Ask: is this value crossing a boundary right now? If not, another check is redundant. Can this be a pure function the shell calls? If yes, extract it.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
