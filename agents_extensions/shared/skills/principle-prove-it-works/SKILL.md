---
name: principle-prove-it-works
description: Verify the real artifact before calling work done. Use for /principle-prove-it-works.
---

# Prove it works

Verify the task output by checking the real artifact. Do not infer from a proxy, a self-report, or a clean compile.

- Check process liveness directly, not through a derived flag.
- Read the actual value, not a cached copy.
- When a check fails, suspect the observation method before you suspect the system.

The strongest proof is a deterministic command that a reviewer can rerun, plus the output it printed. Keep that evidence. Commit a long trail only when the brief asks for an auditable record (`show-me-your-work`).

Name what you did not verify. A passing status string is not the behavior.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
