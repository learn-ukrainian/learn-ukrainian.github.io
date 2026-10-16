# Hillclimb

One metric, improved until a named predicate is met or the remaining ideas are not worth their cost.

1. Ground the workload with `../../how/SKILL.md`. Name the dimensions that can move the metric.
2. Build the harness, prove it can see a change you expect, then freeze it (`../../principle-build-the-lever/SKILL.md`). Vet it with `../../benchmark-checklist/SKILL.md`.
3. Log each attempt with `../../show-me-your-work/SKILL.md`: hypothesis, change, before, after, tests, keep or revert.
4. One hypothesis per iteration. Name a mechanism, not "try making it faster". Keep a win only when the frozen harness and the tests agree. Revert the rest.
5. After a stall, change the kind of hypothesis before you stop. Do not relax the predicate to meet it.
6. Stack the kept commits in the order they landed. Open a pull request only when the brief allows it.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
