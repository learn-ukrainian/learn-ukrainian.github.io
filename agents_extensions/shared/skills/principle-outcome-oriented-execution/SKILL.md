---
name: principle-outcome-oriented-execution
description: For a planned migration, converge on the end state at named check boundaries.
  Use for /principle-outcome-oriented-execution.
---

# Outcome-oriented execution

For a planned rewrite or migration with explicit phase boundaries, optimize for the verifiable end state. Do not add throwaway compatibility code whose only job is to keep every intermediate commit fully feature-complete.

Intermediate breakage is acceptable only when it is planned, scoped to the task branch, and reversible. Keep checks on the code you are touching. Require the agreed verification at the end of the plan.

Do not leave the shared base broken. Do not use this principle to skip a gate or to expand a one-file fix into a rewrite.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
