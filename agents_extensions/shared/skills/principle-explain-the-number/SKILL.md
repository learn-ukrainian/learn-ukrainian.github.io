---
name: principle-explain-the-number
description: Before trusting or reporting a measurement, name its limiter and rule
  out alternate explanations. Use for /principle-explain-the-number.
---

# Explain the number

Before you trust, report, or act on a measured number:

- Ask why it is not twice as good. Name the limiter from a profile or counters taken during a run, then map it to source. A guess from reading the code is not a limiter.
- List what else the number could be measuring, and rule each one out with evidence: errors, skipped or cached work, code that never ran, an untuned side, noise, or a piece too small to matter end to end.
- Keep the run count, the spread, and the limiter with the number.

For a performance number, use `benchmark-checklist`. You skipped this when the evidence has no run count, no spread, or no named limiter, or when the time saved is larger than the time the changed piece took.

Distinct from `principle-prove-it-works`, which checks that an output is real.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
