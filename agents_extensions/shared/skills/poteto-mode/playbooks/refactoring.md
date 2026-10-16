# Refactoring

Behavior-preserving. If behavior changes, this is a feature or a bug fix.

1. Pin the contract with `../../how/SKILL.md` and a characterization test or an equivalence check.
2. Name the missing structure (`../../principle-model-the-domain/SKILL.md`). Leave boring local code alone.
3. Subtract dead weight first (`../../principle-subtract-before-you-add/SKILL.md`).
4. Move in small steps that keep the pin green. For an internal API, migrate callers and delete the old path in the same change.
5. Prove the observable behavior is unchanged (`../../principle-prove-it-works/SKILL.md`). The success measure is lower reader load (`../../principle-minimize-reader-load/SKILL.md`). If the diff does not lower it, revert.
6. Order the commits: removal, then reshape. Open a pull request only when the brief allows it.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
