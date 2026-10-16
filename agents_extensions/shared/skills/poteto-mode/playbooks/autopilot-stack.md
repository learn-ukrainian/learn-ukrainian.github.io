# Autopilot stack

Build one linear stack for the driver to review and land. Owners do not merge.

1. Each slice reports its tip and its intended parent. Only the driver rebases or retargets a link.
2. Owners push only their own branches.
3. Apply the same per-head tests as [autopilot full](autopilot-full.md). Do not land from this playbook.
4. Once landing starts, nobody writes the chain except the driver's documented retarget after a merge.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
