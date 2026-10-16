# Eval

Use this only when the brief orders an evaluation of a prompt or skill change. Do not run an N-implementation arena, and do not spawn parallel product implementations.

1. Write the success rubric (three to six observable checks) for the judge only. Keep those words out of the candidate prompt.
2. The candidate prompt reads like a real request. Do not tell the candidate it is being scored, and do not name the skills under test.
3. One held-out judge, outside the author's model family, scores blinded outputs in one pass. The judge does not see model names.
4. Verify behavior from the artifacts and the checks, not from the candidate's self-report.
5. Read the outputs yourself. If you disagree with the judge, the rubric is ambiguous or the sample is too small. Say so. Do not promote the change on a disagreed score.

Prompt review does not replace exact-head implementation review.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
