---
name: maintain-verification-skill
description: Correct one drifted verification map with a source check and one live
  pass. Use for /maintain-verification-skill.
---

# Maintain a verification skill

Use this when a verification skill's feature map has drifted from the product. One correction wave, then stop.

Outcomes are only: **clean** (nothing to ship), **changed** (one diff of proven corrections), or **blocked** (say what stopped the pass).

Edit only the map, the harness notes, and the docs that the drift made false. For each feature: confirm it in source, then one live pass on the real path. A row you cannot drive stays blocked, not guessed.

Do not widen the product, add a dependency, or delete a check that still has a caller. The driver reviews and lands the diff. This skill does not approve it.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
