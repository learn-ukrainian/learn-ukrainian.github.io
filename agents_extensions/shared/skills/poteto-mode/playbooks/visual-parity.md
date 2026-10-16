# Visual parity

1. Capture the baseline screenshots before any migration. Include the states that matter.
2. Do not edit the harness, replace the baseline, or restructure the component to force a diff to pass. If the baseline is wrong, stop and say so.
3. Change one component at a time. Parallel owners need disjoint paths and a driver (`../../swarm/SKILL.md`, `../../principle-separate-before-serializing-shared-state/SKILL.md`).
4. A non-zero image diff is a failure. Investigate the pixels. Do not call a close match a pass.
5. Open a pull request only when the brief allows it, per component or per batch that stays green.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
