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

For the `ukrainian` profile, identify the contracts in
[`ukrainian-linguistics.md` §8](../../../rules/ukrainian-linguistics.md#ukrainian-linguistic-principles):
Every Ukrainian-profile brief identifies these contracts and their applicability, including level, track, workflow, learner state where relevant, and explicit exceptions.

## Reply format

Every code or infra brief includes this **Reply format** section. It is the reply contract
`verify_review` and the verdict recorder both accept. The reply is one JSON object and
nothing else. The object matches
[`schemas/code-review-findings.v1.schema.json`](../../../../../schemas/code-review-findings.v1.schema.json)
at the exact review head: the reviewer uses that file's field names, required fields,
allowed values and nested definitions, and adds none. `overall` includes `correctness`,
`explanation` and `confidence`. Each finding includes `confidence` and `verbatim` with the
schema's other required fields. `overall.correctness` is `correct` to approve, `incorrect`
to request changes, and `uncertain` for `BLOCKED`.

The brief carries this repository-relative schema path, or an exact shape generated from
that file. It never carries a hand-written schema copy or asks for the format by name
alone. If the reviewer cannot read the schema, the reply is a schema-valid object with
`overall.correctness` of `uncertain`, no findings, and `missing_capabilities` naming
`checkout-data`. A prose approval or a verdict line does not replace the object. An
improvised or malformed findings block is refused even beside a valid verdict line.

A capability-only `BLOCKED` uses `uncertain`, no findings, and `missing_capabilities`.
The recorder's extension and the permitted capabilities are defined by
[the capability-failure policy](policy.md#a-blocked-that-only-lacked-a-capability) and
`scripts/review/verdict_parser.py`. `missing_capabilities` is allowed only where the schema
already allows it.

Ids are stable: a later round reuses `F1` rather than renaming it. Paths are
repository-relative with line suffixes. A `SCORE` line is not part of this reply. The
council's anchored rubric
([decision report](../../drive-epic/references/decision-report.md#council-optional-independent-panel),
"Findings and score") never gates a merge. The recorder stores a score when a reply still
carries a well-formed one, or records it as absent.

A Ukrainian-profile review does not use this object. It returns the
`ukrainian-item-judgments` block named in [ukrainian](ukrainian.md).

## Delta rounds (round 2 and later)

Freeze sections 2 to 4 of the template from round 1; do not edit them. Section 1 names:

- the last reviewed head and the new exact head;
- the fix diff between them (`git diff <last reviewed head>..<new head>`);
- the ledger: every open id with its fix evidence, or the author's decline with file:line or
  test evidence;
- the budget state (`round 2 of 3`, or `round 4 of 5` with the open blocker id that justifies it).

The reviewer marks every earlier id `resolved` or `still open: <reason>`, reviews only the
delta scope in [policy](policy.md#delta-scope), and replies in the round 1 reply format.

## Commands a read-only reviewer can run

The reviewer's worktree is already checked out at the exact head and the base ref is present, so
the brief says no fetch is needed (`git fetch` writes refs and is not a read-only command). A
compound line runs only when every part is read-only, so one denied part denies the whole line
(https://code.claude.com/docs/en/permissions, "Read-only commands"). The brief tells the reviewer
to run read-only git commands one per call (`git rev-parse HEAD`, `git diff <merge-base>..HEAD`,
`git log`), that `gh pr view`, `gh pr diff` and `gh pr checks` are allowed, and that after a
denial it retries once with a simple literal read-only form before it replies BLOCKED.

A review gets a shell and the project interpreter only inside an OS boundary (decision
REVIEW-BOUNDARY-1101, #12378). Today that is a read-only AGY dispatch: it runs in bubblewrap with
a read-only checkout, scratch-only writes and provider-allowlisted egress, so its brief may name
`.venv/bin/python` probes and test files (for example
`.venv/bin/python -m pytest -q -p no:cacheprovider tests/x.py`) and ask for their actual output.
That route has no public internet. Every other route keeps the read-only command set above.

## Wording that read-only admission accepts

A read-only dispatch refuses a brief in which a sentence or list item starts with a write verb
(#8703). Phrase asks as questions or statements, and quote any brief under review inside a
fenced or `>`-quoted block. Include the verdict and supporting evidence in the result text,
as the template says.
