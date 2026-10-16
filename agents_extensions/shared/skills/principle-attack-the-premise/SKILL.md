---
name: principle-attack-the-premise
description: When two or more fixes that share one premise fail the same gate, test
  that premise before another fix. Use for /principle-attack-the-premise.
---

# Attack the premise

When two or more fixes that share one premise fail the same gate, suspect the premise.

1. Write the premise as the one sentence every failed fix assumed.
2. Test it before the next fix. Find an observation that would differ if the premise were false, and make that observation rerunnable (`principle-build-the-lever`).
3. If the evidence contradicts the premise, look for what the failures share that the premise did not predict. If it confirms the premise, ask the next why (`principle-fix-root-causes`).
4. Remove the condition that always loses, instead of adding a cleanup after it (`principle-laziness-protocol`).

Do not start the next fix until the premise is written down and tested. This questions a fact the current design assumes. A new architecture still needs designated approval (`principle-redesign-from-first-principles`).

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
