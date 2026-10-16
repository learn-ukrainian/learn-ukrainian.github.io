# Shipping

Driver only. A worker does not run this playbook.

1. Verify each pull request independently at its current head. Green CI alone does not authorize a merge. Exact-head cross-family approval has to be on that head (`workflow.md`, `../../local-code-review/SKILL.md`).
2. Land only the contiguous verified run from the bottom. Stop at the first pull request that lacks approval or green CI on its current head.
3. A moved head voids both gates. Re-obtain them. Do not merge a stale verdict.
4. The driver enqueues through the repository merge path. Do not use an upstream merge script, an admin bypass, or `--auto`.
5. After merge, confirm the SHA and follow the documented cleanup. Do not delete a branch before GitHub shows it merged.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
