# Guardrail lifecycle

Use this contract for a new material guardrail that blocks work, mutates repository state,
depends on the network, changes merge authorization, or adds always-loaded instructions.
Ordinary tests and narrow validators are not required to complete this process. Existing
guardrails are assessed when touched; there is no blanket historical retrofit.

## Proposal card

Before implementation, record a compact card on the owning issue or PR:

1. **Failure prevented:** the concrete incident or falsifiable failure mode.
2. **Enforcement point:** why this is the narrowest reliable place to enforce it.
3. **Owner:** the path, team, or issue responsible for maintenance.
4. **False-positive budget:** the measurable blocking/error rate that triggers review.
5. **Escape path:** a logged operator recovery route that cannot silently become the default.
6. **Proof:** one expected pass and one deliberate failure exercised at the real boundary.
7. **Sunset:** the replacement condition, deletion criterion, or review date.

## Design constraints

- Prefer server-side enforcement for shared authorization and local enforcement for local
  secrets, checkout containment, and other failures the server cannot observe.
- Do not silently rewrite user commands or mutate checkout state unless the state is
  repository-fatal, the recovery is exact and bounded, and an explicit doctor path exists.
- A replacement must block the same UI, API, and command-line path before the old control is
  removed. A planned replacement is not proof.
- Network failure must not block unrelated local work unless failing open would create the
  specific high-impact failure named in the proposal card.
- Default to annotation or shadow measurement when a new classifier would otherwise remove
  an existing gate.

## Closeout

Record deterministic checks, independent review where required, and source-blind behavior
proof. Compare observed false positives with the budget. Delete a redundant guardrail when
its replacement proof and sunset criterion are satisfied; do not keep dual enforcement
indefinitely for reassurance.
