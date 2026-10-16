# Feature

1. Read the subsystem (`../../how/SKILL.md`).
2. Name the data shape (`../../principle-model-the-domain/SKILL.md`). Sketch boundaries with `../../architect/SKILL.md` when the change crosses a function.
3. Write the acceptance check before the code (`../../principle-prove-it-works/SKILL.md`).
4. Implement inside owned paths. Verify on the surface the user touches. An inconclusive or wrong-surface run is not a pass.
5. If the design is contested, read it with `../../interrogate/SKILL.md` before asking for review. That reading is not approval.
6. Sequence commits (`../../principle-sequence-verifiable-units/SKILL.md`). Open a pull request only when the brief allows it ([opening a PR](opening-a-pr.md)).

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
