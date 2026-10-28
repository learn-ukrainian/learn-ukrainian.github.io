# Review brief for a review-loop round

The section layout of every review brief (target, outcome, threat and input model,
dispositions, reviewer duties, breakers) is the
[review brief template](../../drive-epic/references/review-merge-cleanup.md#review-brief-template-10665).
Use it unchanged. This file lists only what review-loop adds to it.

## Round 1 (full review)

Add to the template's **Target** section:

- the review round (`round 1 of <tier>`), the budget tier and who recorded it;
- the author model of every commit on the branch, the catalog risk and the review profile;
- the base ref and merge-base SHA, so the reviewer reviews `merge-base..exact head`;
- the checks already run, with their results or CI run ids (reviewers do not re-run suites).

Add a **Reply format** section:

```text
VERDICT: <one of APPROVE, REQUEST_CHANGES, or BLOCKED plus the missing capability>
F1 [P0|P1|P2|P3] <path>:<line> <demonstrated failure>. Impact: <impact>. Required behaviour: <behaviour>.
```

Ids are stable: a later round reuses `F1` rather than renaming it. Paths are
repository-relative with line suffixes.

## Delta rounds (round 2 and later)

Freeze sections 2 to 4 of the template from round 1; do not edit them. Section 1 names:

- the last reviewed head and the new exact head;
- the fix diff between them (`git diff <last reviewed head>..<new head>`);
- the ledger: every open id with its fix evidence, or the author's decline with file:line or
  test evidence;
- the budget state (`round 2 of 3`, or `round 4 of 5` with the open blocker id that justifies it).

The reviewer marks every earlier id `resolved` or `still open: <reason>` and reviews only the
delta scope in [policy](policy.md#delta-scope).

## Wording that read-only admission accepts

A read-only dispatch refuses a brief in which a sentence or list item starts with a write verb
(#8703). Phrase asks as questions or statements, and quote any brief under review inside a
fenced or `>`-quoted block. Include the verdict and supporting evidence in the result text,
as the template says.
