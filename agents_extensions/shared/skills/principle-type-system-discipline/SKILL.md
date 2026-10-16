---
name: principle-type-system-discipline
description: Make illegal states unrepresentable and parse external data at the boundary.
  Use for /principle-type-system-discipline.
---

# Type system discipline

Make the type checker reject impossible states, mixed-up primitives, and unhandled variants. Prefer a shape that cannot be constructed wrong over another handler.

- Brand primitives that must not be interchangeable. Validate once at creation.
- Treat external data as untyped until a parse at the boundary returns a domain type (`principle-boundary-discipline`).
- Derive types from the schema that already owns the shape. Do not hand-write a parallel copy.
- Exhaust variants so a new case fails the build.

For TypeScript syntax, use `typescript-best-practices`. Do not add a schema library for a single guard. Use the one the package already depends on.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
