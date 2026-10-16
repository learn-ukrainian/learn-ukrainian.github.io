# TypeScript patterns

Short examples for `typescript-best-practices`. Principles stay in `principle-type-system-discipline` and `principle-boundary-discipline`.

## Branded id

```ts
type LessonId = string & { readonly __brand: "LessonId" };

function parseLessonId(input: string): LessonId {
  if (!/^[0-9a-f-]{36}$/i.test(input)) throw new Error("invalid lesson id");
  return input as LessonId;
}
```

The cast is allowed only after the check. Do not invent a second brand field name.

## Discriminated union

```ts
type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; value: string }
  | { kind: "error"; message: string };
```

One discriminant name per family. Each variant's value is unique.

## Constructive and total

```ts
type NonEmpty<T> = [T, ...T[]];

function newest(items: NonEmpty<string>): string {
  return items[0];
}
```

Keep `T[]` when the empty list is a valid input. Strengthen only when the loose type forces a non-null assertion.

## Unknown, then schema

External JSON, messages, and environment values start as `unknown`. Parse with the schema package this module already imports. Infer the type from that schema. A hand-written guard must check every field it claims.

## Exhaustiveness

```ts
function label(state: LoadState): string {
  switch (state.kind) {
    case "loading":
      return "loading";
    case "ready":
      return state.value;
    case "error":
      return state.message;
    default: {
      const leftover: never = state;
      return leftover;
    }
  }
}
```

## Satisfies

```ts
const config = { theme: "dark", cols: 3 } satisfies { theme: string; cols: number };
```

`satisfies` checks the value and keeps the literal types. `as` widens and skips the check.

## Derived types

When a generated module already exports the shape, pick fields from that type. Do not redeclare them.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
