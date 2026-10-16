---
name: principle-test-behavior-not-implementation
description: Assert what callers can observe, so the test fails when behavior breaks
  and survives an internal reshape. Use for /principle-test-behavior-not-implementation.
---

# Test behavior, not implementation

A test claims what users of the code can observe: return values, errors, state they can read back, and effects outside the code such as a request sent or a row written. Implementation is what they cannot see: private helpers, call order, and which internal collaborator did the work.

Judge a test against two edits:

- Break the behavior (wrong value, skipped effect, doubled effect). If the test still passes, it proves nothing.
- Change only the internals. If the test fails, it is pinned to the implementation.

Keep a test that catches the first edit and survives the second. Drive the code through the caller's interface. Derive the expected value from the requirement, not from a run of the code under test.

Replace a test that does neither. Do not delete the last check of a behavior. An effect a neighboring service can observe is behavior. A call to an internal helper is not.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
