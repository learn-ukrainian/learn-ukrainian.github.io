---
name: typescript-best-practices
description: Apply type-system discipline while reading or editing TypeScript. Use
  for /typescript-best-practices.
---

# TypeScript best practices

Apply `principle-type-system-discipline` and `principle-boundary-discipline` first. Examples live in [patterns](references/patterns.md).

- Model variants as a discriminated union. Do not use a bag of optional fields for mutually exclusive states.
- Brand primitives that must not mix. Validate once at the boundary.
- Build a type that cannot represent the illegal value. Keep a plain array while every operation on it is total. Strengthen the type when a use site needs a non-null assertion or a cast.
- External data is `unknown` until parsed. Prefer the schema library the package already uses, and infer the type from the schema. Do not add a schema dependency for one guard.
- Do not use `as` to skip a check. Narrow with a discriminant, then `in`, then `typeof` or `instanceof`, then a guard that actually proves the claim. Exhaustiveness assigns the leftover to `never`.
- Prefer `satisfies` when you need to keep literal types.
- Derive from the generated schema type with `Pick`, `Omit`, `Parameters`, `ReturnType`, `Awaited`, or `typeof` before writing a parallel interface.
- Pass an object when argument order is not obvious. Skip that on a measured hot path.
- Do not mock what you can run. No stray `console.log` in shipped code.

These rules do not override a local convention that is already enforced by the package's types and tests.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
