---
name: tdd
description: For a bug with a cheap local check, write the failing test first, then
  the fix. Use for /tdd.
---

# TDD bug fix

Use this when the bug has a cheap local check, or the brief asks for a failing test. Skip it when the only test would be a brittle mock, a slow end-to-end stand-in, or a large unrelated fixture.

1. Name the intended behavior, the current behavior, and the smallest reproduction.
2. Add the narrowest test that would have caught the bug. Encode the requirement, not the current implementation (`principle-test-behavior-not-implementation`).
3. Run it and confirm it fails for the intended reason before editing production code.
4. Make the smallest production change that satisfies the test and nearby contracts.
5. Rerun the test and the affected consumer tests.

If a failing test is impractical, use the closest executable reproduction and say why the test was skipped. Do not weaken an existing assertion to match a wrong implementation. Prefer no new test over a bad one. Do not delete the last check of a behavior.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
