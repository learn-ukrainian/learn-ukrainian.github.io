---
name: principle-foundational-thinking
description: Choose data structures and shared-state rules before writing logic. Use
  for /principle-foundational-thinking.
---

# Foundational thinking

Get the data shape right before the logic. Define the core types, trace the access patterns, and pick structures that match the dominant paths.

Structural choices protect later options. Code-level choices protect simplicity: repeat three similar lines rather than invent an abstraction, prefer explicit over clever, and test behavior rather than line counts.

Before actors share state, ask what happens if another actor writes it at the same time. If the answer is not "nothing", do not share it (`principle-separate-before-serializing-shared-state`).

Build scaffold that every later phase needs before the features: shared types, the check, the lint. Remove dead code first (`principle-subtract-before-you-add`). Each increment should land one coherent abstraction or deepen one that exists.

New architecture still needs designated approval. This principle chooses the shape inside approved scope.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
