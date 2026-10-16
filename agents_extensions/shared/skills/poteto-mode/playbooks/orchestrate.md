# Orchestrate

A multi-day stream belongs to the accountable driver. Follow `../../drive-epic/SKILL.md`. Do not create a second coordinator, lease, message bus, or merge path.

1. Orient from the handoff, the issue, and live queue state.
2. One brief is one shippable outcome, with owned paths and acceptance checks.
3. Dispatch through the existing worktree path. Fan-out uses `../../swarm/SKILL.md` only for disjoint slices.
4. Review, land, and close out under `workflow.md`. The driver does not ask the operator to merge.
5. A standing program that is really one task belongs to [autonomous run](autonomous-run.md), not here.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
