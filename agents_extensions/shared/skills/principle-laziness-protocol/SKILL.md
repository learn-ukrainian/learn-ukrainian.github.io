---
name: principle-laziness-protocol
description: Make the smallest change that solves the problem and still proves it.
  Use for /principle-laziness-protocol.
---

# Laziness protocol

Put each decision in one place and pass the result on. Make the smallest change that solves the problem and still proves the behavior.

Fewer lines beat unused abstraction. Do not add a layer, a flag, or a threaded signal for a case that does not exist.

This is not a license to skip the root cause, the test, or a gate. Deletion is allowed only for dead code the task owns.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
