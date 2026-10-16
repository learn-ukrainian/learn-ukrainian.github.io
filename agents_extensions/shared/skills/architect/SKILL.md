---
name: architect
description: Sketch types, signatures, and module boundaries before code that crosses
  a function boundary. Use for /architect.
---

# Architect

Sketch the caller's usage, the types, and the module boundaries before filling in code. Do not run an N-implementation arena and do not spawn design subagents.

1. **Ground.** Read how the surrounding system actually works (`how`). If the design changes ownership, also read why the current shape exists (`why`). Skip this only for a genuine greenfield with nothing to integrate.
2. **Sketch two shapes.** Write two structurally different candidates. Screen each one against [design red flags](references/design-red-flags.md). Prefer the shape that hides more complexity behind a smaller public surface. Record the choice in the [rationale template](references/rationale-template.md).
3. **Approval.** If the chosen shape is new architecture, layout, process, or policy, stop for designated approval before code. Otherwise proceed. Pause for a human checkpoint only when the brief asks for one.
4. **Implement against the sketch.** A parameter the sketch did not name is a signal: the sketch was wrong, a requirement was missed, or the implementation overreaches. Say which.
5. **Scrap a wrong shape.** Scrap when the same workaround appears in unrelated places, unrelated edge cases all need special cases, or callers must know internal rules. Re-ground, subtract, and sketch again. Do not bolt fixes onto a shape that cannot hold the requirement (`principle-redesign-from-first-principles`).

Write the caller's usage first. Derive the types from it. Stay inside the brief. This sketch is not the independent review of record.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
