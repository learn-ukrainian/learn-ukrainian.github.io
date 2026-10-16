---
name: principle-build-the-lever
description: For non-trivial work, build the rerunnable tool or check that does or
  proves the job. Use for /principle-build-the-lever.
---

# Build the lever

When the work is not a couple of obvious edits, build the smallest script, codemod, generator, or check that does the job the same way every time. A reviewer should rerun that artifact instead of redoing the work by hand.

Do the first unit by hand to learn the recipe, then build the tool. Rerun it on that unit and diff it against the hand-done result. Make it safe to run twice (`principle-make-operations-idempotent`).

Prefer one deterministic pass over fan-out. A worker does not spawn delegates to hand-apply what a script can do. Commit the lever when the work outlives the session and the brief owns that path. If you cite this principle and the diff has no rerunnable check, you did not apply it.

This is the check for the work in front of you. A recurring lesson becomes a lint or type instead (`principle-encode-lessons-in-structure`).

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
