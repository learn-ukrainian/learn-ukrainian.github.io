---
name: principle-encode-lessons-in-structure
description: Encode a repeated correction as a lint, type, or check instead of another
  prose warning. Use for /principle-encode-lessons-in-structure.
---

# Encode lessons in structure

When the same instruction would be written a second time, encode it so the wrong change fails: one owner in the types, a lint whose message names the replacement, or a test that rejects the bad input and accepts the valid one.

If the fix is structural, ship the structural fix. Another paragraph does not enforce it. Use prose only for a judgment call that cannot be encoded, and include one example of the failure.

Do not weaken an existing check to silence the lesson. New process or policy still needs designated approval. Agent-rule edits belong in `agents_extensions/` and are deployed by the driver.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
