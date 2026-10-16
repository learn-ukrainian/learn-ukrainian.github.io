---
name: principle-redesign-from-first-principles
description: When a new requirement does not fit, sketch the shape you would have
  built from the start. Use for /principle-redesign-from-first-principles.
---

# Redesign from first principles

Do not bolt a new requirement onto a shape that cannot hold it. Read the affected code. Ask what you would build if this requirement had been there from the start. Then deliver that shape in verifiable increments, and update the types, docs, and callers the change actually owns.

This questions the design. `principle-attack-the-premise` questions a fact the design assumes.

If the sketch is new architecture, layout, process, or policy, stop for designated approval before implementing it. Inside approved scope, prefer the smaller shape (`principle-subtract-before-you-add`).

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
