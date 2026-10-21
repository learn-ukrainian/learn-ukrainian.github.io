---
name: local-code-review
description: Review an exact local, commit, branch, or PR code/infra target with independent review and behavior proof; excludes learner semantics.
argument-hint: "[local | commit <sha> | branch <branch> <base> | pr <number>]"
---

# Closeout Review: $ARGUMENTS

This skill supports only `code` and `infra` review profiles. A normal BIO
learner-content request routes to `$curriculum-lifecycle` (or directly to
`$track-completion` for one module), which owns the single bounded
`$post-build-review` gate. `resolve-reviewer` fails before route selection for
any learner-content semantic profile or domain. Do not duplicate post-build
semantic review here.

Use the explicit target in `$ARGUMENTS`: `local`, `commit <sha>`,
`branch <branch> <base>`, or `pr <number>`. The checklist below owns target
semantics, scope freezing, non-mutating checks, cross-family reviewer
resolution, finding adjudication, and separate behavior proof. A clean
working tree never substitutes for reviewing a requested commit or PR.

For the review of record, use `scripts/review/record_cf_verdict.py` after the
toolful review settles. It posts a PR comment bound to the exact head, with
model/family/harness provenance. GitHub rejects an API approval review when the
shared bot identity also authored the PR (`gh pr review --approve` uses that API).
Post the verdict as a PR comment bound to the reviewed head SHA, not as an
approval review. The comment must still come from an independent cross-family
reviewer; a shared posting identity does not establish independence. See
`workflow.md` § Merge policy.

Red-team exception (`workflow.md` § Merge policy), for code review only:
only when no eligible outside-family reviewer exists, resolve with
`closeout_cli resolve-reviewer --review-mode red_team`, dispatch a
separate review task with `delegate.py dispatch --review-mode red_team
--prompt-file <file>` whose prompt text names a red team, then publish
with `record_cf_verdict.py --review-mode red_team --red-team-prompt
<file>`. The author's task stays refused, and so does every canonical
concrete model that authored a commit on the branch, on any harness; a
review is refused with a typed error only when no validated author model
exists; unknown historical authors stay recorded as UNKNOWN, and
`--review-author-model` only adds a model to compare against: it never
overwrites recorded task evidence, and a conflict with validated
evidence is refused; seats whose own code is under review stay excluded
as usual; the reviewer always runs as a separate fresh-session review
task, and a different model of the same family may serve, subject to
qualification and the risk floor, only as same-family dissent, never as
cross-family independence. A red-team publication or dispatch is also
refused when a recorded verdict from a non-red-team review for the same
exact head is CHANGES_REQUESTED or BLOCKED, or when such a review of
that head is still in flight. The tools refuse a missing or non-red-team
prompt, a prompt changed after admission, a non-review dispatch, and a
red-team dispatch while an eligible outside-family reviewer exists (the
resolver then selects that reviewer instead). The verdict is labelled
`review_mode=red_team`; it never replaces cross-family clearance when an
outside-family reviewer is available.

## Execute

Read and follow [`local-code-review-checklist.md`](local-code-review-checklist.md)
in full. It drives `.venv/bin/python -m scripts.review.closeout_cli` for every
step that has a deterministic answer (target resolution, scope-baseline
freeze and breakers, reviewer resolution, findings adjudication) and tells
you exactly what to reason about yourself. Do not re-run test suites that the
PR's CI runs; review the diff, run at most the specific tests that reproduce
a finding you are checking, and cite CI run ids for suite results.

The review rules bind every round (#10665): the round-1 brief freezes the
outcome, the threat and input model and the dispositions (checklist Step 2);
findings are one per input class, each with a reproducer (Step 4); blocking
follows the stated contract, existing invariants on the change's paths and
regressions against main, verdicts are proportional, and a missing required
capability is INCONCLUSIVE, which still blocks (Step 5); exact-head CI that
answers the execution questions is valid evidence, a capability note is not a
verdict, and new tests name their defect class (Step 5); the breakers are
unchanged (Step 6).

## Output

Print a structured report to the conversation (the checklist's Step 8 gives
the exact shape). Do NOT write a file unless specifically asked.
