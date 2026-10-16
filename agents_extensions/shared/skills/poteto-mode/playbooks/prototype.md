# Prototype

A throwaway to make one decision. The output is the decision, not shippable code.

1. Name the decision: layout, interaction, or which behavior is faster or clearer. No decision, no prototype.
2. Build it in scratch, outside production source. Do not add dependencies to the product for a sketch.
3. When comparing alternatives, keep them behind one switch and label them. This is a scratch comparison, not an N-implementation arena and not parallel production branches (`../../principle-exhaust-the-design-space/SKILL.md`).
4. Observe the result on the real surface the decision cares about.
5. Recommend one direction with the tradeoff. Implementation of the winner, if approved and in scope, goes through [feature](feature.md).

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
