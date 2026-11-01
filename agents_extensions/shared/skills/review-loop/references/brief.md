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

Every brief includes this **Reply format** section, including the literal first two lines
below. This is the single reply-format contract for both reference templates. The reply
starts with those lines as plain text, outside any fence or quotation; the reviewer replaces
the placeholders with one verdict and an integer score. A prose approval or a JSON object
does not replace either line. For `BLOCKED`, the verdict line also names the missing capability.

```text
VERDICT: <APPROVE|REQUEST_CHANGES|BLOCKED>
SCORE: <n>/10 <one-line rationale>
F1 [P0|P1|P2|P3] <path>:<line> <demonstrated failure>. Impact: <impact>. Required behaviour: <behaviour>.
```

The default reply is text only: finding lines and supporting evidence follow the first two
lines, or a statement that there are no findings. No JSON findings block is requested or
added by default.

When the caller needs structured findings, the brief explicitly asks for one fenced `json`
object after the same first two lines and links the exact shape in
[`schemas/code-review-findings.v1.schema.json`](../../../../../schemas/code-review-findings.v1.schema.json).
The reviewer reads that schema at the exact review head and uses its field names, required
fields, allowed values and nested definitions without additions. The brief carries this
repository-relative schema path, or an exact shape generated from that file; it never carries
a hand-written schema copy or merely asks for the format by name. If the reviewer cannot
read the schema, the reply is text-only `BLOCKED` naming `checkout-data`.
The object and verdict line agree. An improvised or malformed findings block is refused even
beside a valid verdict line.

A structured capability-only `BLOCKED` follows the same schema with `uncertain` and no
findings. The recorder's `missing_capabilities` extension and the permitted capabilities are
defined by [the capability-failure policy](policy.md#a-blocked-that-only-lacked-a-capability)
and `scripts/review/verdict_parser.py`; the extension is not a schema field. The literal
verdict and score lines remain required.

Ids are stable: a later round reuses `F1` rather than renaming it. Paths are
repository-relative with line suffixes. The `SCORE` line uses the council's anchored rubric
([decision report](../../drive-epic/references/decision-report.md#council-optional-independent-panel),
"Findings and score"); it never gates a merge. The recorder stores it with the verdict, or
records it as absent when it is missing or malformed, and `scripts/fleet/agent_success.py`
reports it per reviewer and author model.

## Delta rounds (round 2 and later)

Freeze sections 2 to 4 of the template from round 1; do not edit them. Section 1 names:

- the last reviewed head and the new exact head;
- the fix diff between them (`git diff <last reviewed head>..<new head>`);
- the ledger: every open id with its fix evidence, or the author's decline with file:line or
  test evidence;
- the budget state (`round 2 of 3`, or `round 4 of 5` with the open blocker id that justifies it).

The reviewer marks every earlier id `resolved` or `still open: <reason>`, reviews only the
delta scope in [policy](policy.md#delta-scope), and replies in the round 1 reply format,
`SCORE` line included.

## Commands a read-only reviewer can run

The reviewer's worktree is already checked out at the exact head and the base ref is present, so
the brief says no fetch is needed (`git fetch` writes refs and is not a read-only command). A
compound line runs only when every part is read-only, so one denied part denies the whole line
(https://code.claude.com/docs/en/permissions, "Read-only commands"). The brief tells the reviewer
to run read-only git commands one per call (`git rev-parse HEAD`, `git diff <merge-base>..HEAD`,
`git log`), that `gh pr view`, `gh pr diff` and `gh pr checks` are allowed, and that after a
denial it retries once with a simple literal read-only form before it replies BLOCKED.

## Wording that read-only admission accepts

A read-only dispatch refuses a brief in which a sentence or list item starts with a write verb
(#8703). Phrase asks as questions or statements, and quote any brief under review inside a
fenced or `>`-quoted block. Include the verdict and supporting evidence in the result text,
as the template says.
