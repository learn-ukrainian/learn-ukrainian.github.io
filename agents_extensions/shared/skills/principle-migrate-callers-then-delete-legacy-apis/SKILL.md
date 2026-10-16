---
name: principle-migrate-callers-then-delete-legacy-apis
description: Migrate internal callers and delete the old API in the same change. Use
  for /principle-migrate-callers-then-delete-legacy-apis.
---

# Migrate callers, then delete the old API

When no external consumer depends on the old internal API, migrate every caller and delete the old API in the same change. A compatibility layer that nobody needs becomes permanent debt.

Update tests to the new observable contract. Replace a test that only pins pre-refactor internals with a behavior test. Do not drop the last check of a behavior, and do not delete files the task does not own.

Skip this when an external contract still requires the old surface. Say so, and keep one path (`principle-minimize-reader-load`).

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
