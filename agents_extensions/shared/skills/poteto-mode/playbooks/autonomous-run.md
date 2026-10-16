# Autonomous run

Drive one task to a checkable predicate. This is not permission to merge overnight or to ignore a stop.

1. Write the exit predicate before the first iteration (the named tests pass, the reproduction is gone, the diff matches the brief).
2. Each iteration makes the smallest change the evidence supports, verifies it, and keeps it only if the predicate moved. Revert changes that did not help.
3. Record the iteration with `../../show-me-your-work/SKILL.md`.
4. A plateau is a reason to change approach (`../../principle-attack-the-premise/SKILL.md`), not to lower the bar. A real dead end stops. Report it.
5. Stay inside owned paths. Do not merge, deploy, or take an irreversible action to "finish".

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
