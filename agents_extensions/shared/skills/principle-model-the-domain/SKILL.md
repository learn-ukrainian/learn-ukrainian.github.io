---
name: principle-model-the-domain
description: Encode the domain in a data structure so invalid states cannot be represented.
  Use for /principle-model-the-domain.
---

# Model the domain

Encode the domain in a structure instead of scattering it across conditionals. Choosing the structure at write time is cheap.

Reach for a state machine instead of synced booleans, a typed model instead of loose parameters, a table or discriminated union instead of branches copied across files, or a reducer instead of ad hoc mutation. Group a module around one body of knowledge, not around the order load, validate, transform, save.

Do not force an abstraction. Boring local code stays when it is already clear. The sign you skipped this is a new feature that adds one more branch to an existing chain, or a second boolean that must stay in sync with the first.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
