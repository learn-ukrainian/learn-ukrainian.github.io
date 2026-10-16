---
name: reflect
description: After a long task, capture a repeated lesson as a structural fix or a
  skill edit. Use for /reflect.
---

# Reflect

After a long task lands, capture what should be true next time. Do not spawn reviewer subagents. Do not treat this note as approval.

1. Use the diff, the checks, and the handoff. Do not mine private transcripts.
2. Ask what failed more than once, what the root cause was, and whether a type, lint, or test can encode it (`principle-encode-lessons-in-structure`).
3. If the lesson is already in a rule or skill, do not add a second copy. If a skill edit is warranted, draft it under `agents_extensions/shared/skills/` and say which failure it prevents.
4. A new process or policy stops for designated approval. The driver reviews and lands the edit.

Summarize the lesson, the enforcement, and anything left unenforced with its owner.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
