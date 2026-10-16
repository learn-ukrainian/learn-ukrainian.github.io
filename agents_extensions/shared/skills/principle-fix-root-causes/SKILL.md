---
name: principle-fix-root-causes
description: Trace a symptom to the first wrong decision and fix it there. Use for
  /principle-fix-root-causes.
---

# Fix root causes

Fix the fault, not only the line where it became visible. A symptom fix hides the evidence and leaves the fault free to surface elsewhere.

1. Reproduce it.
2. Ask why at each step until the answer is a wrong decision in the code, not a consequence of an earlier one.
3. When stuck, read the actual error and the actual state. Do not guess.
4. If the triggering state is legitimate, handle it where it broke. If that state should never exist, a guard there hides the bug. Find what produced it. Retries, swallowed errors, clamped values, and discarded state are the usual hides.
5. After a restart-only failure, suspect persisted state first: config, caches, lock files, serialized records.
6. Fix the pattern, not only the instance.
7. If a workaround needs a long comment, fix the code.

When the deciding fact was hard to see, propose the cheap always-on signal that would have shown it. Do not weaken tests to make the symptom disappear.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
