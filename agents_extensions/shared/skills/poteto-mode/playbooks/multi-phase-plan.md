# Multi-phase plan

Work that spans phases or stacked pull requests.

1. Name the user-visible outcome, the phases, and the check that ends each phase (`../../principle-sequence-verifiable-units/SKILL.md`).
2. Each phase is one shippable slice. Do not start phase N+1 on a red phase N.
3. The driver orders landing. A worker does not open the stack unless the brief says so.
4. A phase that needs new architecture stops for designated approval before it is built.
5. Record the phase state with `../../show-me-your-work/SKILL.md` when the plan will be reviewed later.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
