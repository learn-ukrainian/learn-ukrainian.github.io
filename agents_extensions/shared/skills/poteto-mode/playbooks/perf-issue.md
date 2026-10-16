# Perf issue

1. Capture a baseline and vet it with `../../benchmark-checklist/SKILL.md` before planning. Vet every later number the same way.
2. Ground hypotheses with `../../how/SKILL.md`. Do not claim a ceiling you did not measure (`../../principle-explain-the-number/SKILL.md`).
3. If the fix crosses a function boundary, sketch it with `../../architect/SKILL.md`.
4. Compare before and after on the same surface. Inconclusive stays inconclusive.
5. Cite the measurement in the notes. Open a pull request only when the brief allows it ([opening a PR](opening-a-pr.md)).

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
