---
name: principle-sequence-verifiable-units
description: Split work into units that each end in a check, and verify each before
  the next. Use for /principle-sequence-verifiable-units.
---

# Sequence work into verifiable units

Order work as small units that each end in a state you can check. Do not start the next unit on a broken base.

Each unit is a before, one change, and a check. When a lever does the edits, run the per-unit check anyway.

Order commits so a reviewer can replay the argument: a failing check, then the fix, or a removal, then the reshape. Opening a pull request and landing it follow `agents_extensions/shared/rules/workflow.md`. A worker does not open or merge a pull request unless the brief says so.

Pair this with `principle-prove-it-works` for a real check and `principle-build-the-lever` for a cheap one.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
