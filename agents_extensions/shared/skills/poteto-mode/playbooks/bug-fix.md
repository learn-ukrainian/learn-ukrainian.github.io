# Bug fix

1. Reproduce the defect on the surface the user hits. A unit test that stays green does not prove the bug is absent.
2. Binary-search the cause. Use `../../how/SKILL.md` on the subsystem and `../../why/SKILL.md` when a guard looks historical. Rule hypotheses out with an observation.
3. If the fix crosses a function boundary, sketch it with `../../architect/SKILL.md` first.
4. When a cheap local test exists, write the failing test first (`../../tdd/SKILL.md`).
5. Fix the root cause (`../../principle-fix-root-causes/SKILL.md`). Verify the original reproduction now passes, and run the affected tests.
6. Order the commits so the failing check precedes the fix (`../../principle-sequence-verifiable-units/SKILL.md`).
7. Prepare the update with [opening a PR](opening-a-pr.md) only when the brief allows a pull request.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
