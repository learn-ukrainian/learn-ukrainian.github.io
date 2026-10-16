---
name: principle-subtract-before-you-add
description: Remove dead weight the task owns before adding structure. Use for /principle-subtract-before-you-add.
---

# Subtract before you add

Remove complexity the task owns before you build. Sequence the deletion first, then the new shape, on a simpler base.

- Cut dead code, one-caller wrappers, and redundant checks before polishing.
- Design for observed use, not for speculative edge cases.
- Do not add a validator or parser the contract does not demand.
- When a reference has no remaining caller and no remaining content, delete it rather than leaving a stub.

Do not delete files the task does not own. Do not weaken or delete a test that still checks a behavior. Do not remove a public contract that still has a consumer.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
