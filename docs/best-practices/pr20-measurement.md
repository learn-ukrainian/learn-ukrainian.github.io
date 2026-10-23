# PR20 measurement protocol

This protocol declares the measurement before the CI admission change takes effect.
The deliverable is measurement machinery and a prospective protocol. It makes no
claim about the performance of future PRs. The measurement author is separate from
the CI change author. The accountable driver obtains exact-head outside-family
review and lands this protocol before switching CI.

## Cohort and success criteria

The baseline is the original frozen last50, not a newly selected sample. Its
`pr-list.json` SHA-256 is
`83b9115d8f86a96991ef0329d4f68bec2877fb2773b5765b4412e985b42e3272`.
The original evidence bundle is
`batch_state/preserved/cto-pr20-design-sol/evidence-84af757156c6422d918cf25ab2a2ae14`.
The source snapshot is `e07077acdacb8b23aea1188e8c45445e0e769aca`.
`methodology.md`, `analyze.py`, and `queue_analysis.py` in that bundle define the
historical reconstruction. The new CLI adapts their timestamp matching,
ordinary median, published review counting, and nearest-rank percentile method.
The original summaries and CSV remain independent replay checks, never inputs
to the calculations.

The original selection was the latest 50 merged PRs from 97 candidates at
retrieval. Preserve all 50 identities, including exceptional cases. The original
merge window is 2026-10-22T23:03:25Z through 2026-10-23T18:06:04Z. Historical
merged-only selection is a baseline limitation, not the prospective rule.

The prospective denominator is the next **50 consecutive non-draft PRs** opened
at or after the actual merge of the frozen CI-change PR. Order by first non-draft
eligibility timestamp, then PR number. A PR opened non-draft is eligible at
`createdAt`. A PR opened as draft is eligible at its first `ready_for_review`
event. Once eligible, later conversion to draft, closing, reopening, head changes,
review rejection, CI failure, cancellation, or failure to merge never removes it.
The census covers all repository PRs, all states, and all authors. There is no
path, author, size, outcome, or base-branch exclusion.

Only these exclusions apply, declared here before observation:

- PRs opened before the effective switch, including existing draft PRs.
- PRs that have never become non-draft by the observation cutoff. They remain
  listed with this reason and can enter on a later eligibility event.
- Eligible PRs beyond the first 50. They remain listed separately.

Unavailable draft history is unresolved selection, not an exclusion. Missing
telemetry, missing runs, open PRs, and closed-unmerged PRs stay explicit. There
are no replacement PRs for unsuccessful outcomes. A missing census page prevents
a complete selection claim. Ties use PR number, never merge order.

The target is ordinary median open-to-merged **at most 20 minutes** across all
50. Report nearest-rank p90, the sorted value at `ceil(0.9*n)`, without
interpolation. No p90 latency target was specified. Report it without inventing
one. All comparisons use unrounded values for decisions; displayed minute
statistics use two decimals. Incomplete cohorts have no passing target verdict.
Observed statistics from available values are labeled separately, with their
known count, unknown count, and original denominator. Unmerged rows carry an
elapsed observation duration, not an invented merge timestamp or a successful
latency. Closed-unmerged rows remain unresolved outcomes.

Compare these guards with the original last50:

| Guard | Measurement |
| --- | --- |
| PR-own-defect ejections | Attributed ejections divided by enqueue events, including reentries |
| Red-main incidents | Distinct evidenced incidents during the stated observation window |
| Review rounds per PR | Mean published task/head/verdict tuples per PR, with median and p90 also reported |
| Queue CI p90 | Final successful associated queue workflow creation to CI Gate completion per PR |

A value above the baseline is reported as a regression. Missing baseline or
prospective attribution makes that comparison `UNKNOWN`. Published markers show
recorded reviews, not independently verified reviewer eligibility or runtime
attestation. The original baseline has no complete red-main census or removal
attribution; absent telemetry cannot establish zero incidents or zero ejections.

Stop when PR-own-defect ejections **exceed 10% of enqueues**, or when any main
break is attributed to this change. Exactly 10% does not meet the ejection stop
threshold. Unknown causes never become PR defects or infrastructure failures by
guesswork. Known defect counts can establish a stop despite other unknown
causes when the enqueue denominator is complete. Missing coverage leaves the
safety status unknown, even without an observed trigger.

On `STOP`, the accountable driver creates one clean revert PR under normal
independent review, CI, and merge gates. This CLI only reports the trigger.
It never reverts, changes settings, launches jobs, or writes to GitHub.

## Timestamp and evidence definitions

Every ledger row preserves PR number and head SHA. The report hashes every
consumed raw file and lists absent files with null digests. Identical inputs
and the same implementation produce byte-identical output. Output files use
exclusive creation, so a rerun needs a new output path.

| Field | Source and meaning |
| --- | --- |
| `opened`, `merged` | GitHub `createdAt`, `mergedAt`; missing merge remains null |
| `head` | Snapshot `headRefOid`; `head_observed_at` is the snapshot time |
| `head_at` | Evidenced timestamp when that SHA became the PR head, otherwise unknown |
| `commits` | Commit OIDs and committed dates; committed dates do not prove head arrival |
| `pr_admission_green` | Earliest successful `CI Gate` on a listed `pull_request` run for that head, before merge or cutoff |
| `first_verdict` | Earliest published native or marker verdict before merge or cutoff |
| `final_approve` | Latest published approval naming that head before merge or cutoff |
| `admission_approve` | Latest such approval at or before the last enqueue |
| `admission_ready_proxy` | Latest admission approval, PR admission green, and observed successful `Analyze (` checks |
| `enqueues`, `last_enqueue` | All `added_to_merge_queue` events and the last event before merge or cutoff |
| `queue_created` | Creation of the final successful associated queue workflow |
| `queue_gate_completed` | Successful CI Gate completion on that queue candidate SHA |
| `full_green` | That gate completion when recorded pytest shards all succeeded; null for reuse or missing shard evidence |
| `queue_runs` | All associated observed runs, candidate SHAs, refs, jobs, conclusions, and membership evidence |

The admission proxy is comparable to the historical method. It does not certify
keeper eligibility, absence of holds, independent review qualification, or full
test coverage. A lightweight PR admission gate is not full integration proof.
`full_green` describes observed job states, not independent test-file accounting.
Reuse remains explicit and requires separate coverage evidence for product
certification. Queue CI includes reused candidates to match the original method;
all associated unsuccessful and cancelled runs stay in the ledger.

A queue ref identifies its named PR. It does not prove the full membership of a
multi-PR group. An evidenced `groups` entry can supply that membership. Without
it, `membership_complete` is false. Multiple workflow attempts retain their run
IDs; raw job records must include every attempt needed for the observation.
Queue waiting and reconstruction remain in enqueue-to-merged. Signed readiness
intervals stay signed; overlapping review and CI spans are not added.

## Offline input contract

Run `baseline`, `anchor`, or `measure` with
`PROJECT_PYTHON` set to the interpreter prescribed by the task. In a regular
checkout it is `.venv/bin/python`; dispatch worktrees use the shared interpreter.
`--help` lists the commands and exit codes.

Each input directory contains these saved responses:

- `pr-list.json`: a flat PR array with `number`, `createdAt`, `mergedAt`,
  `headRefOid`, `mergeCommit`, and, for next50, `state` and `isDraft`.
- `pr-N.json`: `gh pr view` response with `number`, `comments`, `reviews`,
  `commits`, and `statusCheckRollup`.
- `timeline-N.json`: REST issue timeline, flat or paginated/slurped pages.
- `ci-runs.json`: flat `gh run list` array with `databaseId`, `event`,
  `headSha`, `headBranch`, `createdAt`, `conclusion`, and `status`.
- `queue-run-ID.json`: `gh run view` JSON with `databaseId`, `event`,
  `headSha`, `createdAt`, and `jobs`. Jobs use `name`, `conclusion`,
  `startedAt`, `completedAt`, and `databaseId`.
- `snapshot.json`: required for next50, optional historical supplementation
  for the baseline, with the structure below.

The original baseline membership file is consumed byte for byte. Do not
reformat it, refresh it, or replace authentic IDs with illustrative ones.
`pr-candidates.json` is hashed when available. Baseline source scripts and
methodology remain the original custody references. Missing optional files
produce unknown values; malformed supplied files fail with exit 2.

The snapshot schema is `pr20-snapshot.v1`. The following is a structural example,
not collected evidence. Empty arrays and false coverage flags intentionally
assert no coverage. Replace placeholders only with saved source observations.

```json
{
  "schema": "pr20-snapshot.v1",
  "observed_at": "2026-10-23T20:00:00Z",
  "selection_complete": false,
  "selection_evidence": [],
  "timelines_complete": [],
  "reviews_complete": [],
  "runs_complete": false,
  "runs_evidence": [],
  "heads": [],
  "groups": [],
  "removals": [],
  "main_incidents": [],
  "main_coverage": {
    "complete": false,
    "start": null,
    "end": null,
    "evidence": []
  }
}
```

Every `evidence` or `selection_evidence` is a nonempty list of
`{"file": "saved-response.json", "locator": "exact JSON pointer or event identity"}`.
Files must be valid saved JSON inside the input directory. Their digests become
part of the report. References locate evidence; they do not adjudicate causality.
The driver is responsible for the truth and completeness of these declarations:

- `selection_complete` requires an uncapped all-state census covering the switch
  through `observed_at`, with retrieval argv, count, limit, pagination completion,
  and timestamps retained in the referenced JSON receipt. Search indexing delay
  or a reached cap leaves this false until reconciled.
- `timelines_complete` and `reviews_complete` contain PR numbers whose respective
  raw histories are complete through `observed_at`. A file's existence alone
  does not establish prospective completeness.
- `runs_complete` requires a complete CI run census through the cutoff, with
  `runs_evidence` references to its retrieval receipt. Missing or capped run
  listings leave queue CI statistics unknown. Observed run durations remain in
  the ledger. A later successful run with unavailable job data never causes
  selection of an earlier successful run instead.
- `heads` entries contain `pr`, `sha`, `at`, and `evidence` for actual head updates.
- `groups` entries contain `run_id`, all `prs`, and `evidence` of complete group
  membership. Do not infer unlisted members from ref naming.
- `removals` entries contain `pr`, `event_id`, `cause`, and `evidence`.
  Allowed causes are `merged`, `pr_own_defect`, `other`, and `unknown`.
  Normal post-merge removals need classification too. A cancellation or removed
  queue event alone does not establish a PR defect. Attribution must connect
  the removal to failed checks and the responsible change, preserving raw run
  identities and the driver's reason. Duplicate/conflicting attribution remains
  unknown. An absent attribution remains unknown.
- `main_incidents` entries contain distinct `id`, `at`, `cause`, and `evidence`.
  Causes are `change`, `other`, or `unknown`. `main_coverage` covers an explicit
  start/end interval with saved incident/run-census evidence, including evidence
  for a zero count. A known change-attributed break triggers STOP even with
  otherwise incomplete coverage. Never fabricate a clean-main history.

Baseline guard attribution can be supplemented before the declaration without
changing its membership or source responses. The declaration freezes those
input digests too. Later attribution updates require a separately retained
amendment and driver disposition, not silent replacement of the frozen baseline.

## Capture and retain the switch declaration

The effective switch is the CI-change PR's actual GitHub `mergedAt`, with its
merge commit identity. Worker completion, protocol merge, enqueue, wall-clock
capture, and a guessed rollout time are not switch anchors. The premerge
record freezes the exact CI PR number and head while it is still open.

After this protocol has landed and the CI PR head is final, the driver saves its
metadata and creates the declaration **before that CI PR merges**:

```sh
gh pr view "$CI_PR" --repo learn-ukrainian/learn-ukrainian.github.io \
  --json number,createdAt,headRefOid,baseRefName,isDraft,state,mergedAt,mergeCommit \
  > "$EVIDENCE/switch-before.json"
"$PROJECT_PYTHON" -m scripts.ci.pr20_measurement anchor \
  --inputs "$LAST50" --switch-pr "$EVIDENCE/switch-before.json" \
  --observed-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --output "$EVIDENCE/pr20-declaration.json"
sha256sum "$EVIDENCE/pr20-declaration.json"
```

`EVIDENCE` is the driver's durable evidence directory. `LAST50` is the preserved
baseline directory. The driver deposits the declaration and its SHA-256 in the
existing durable evidence/receipt store before allowing the CI merge. Exclusive
creation protects against accidental overwrite; the external digest receipt
provides tamper evidence. The driver retains the original raw switch response,
exact committed source, script/protocol digests, baseline manifest, and this protocol.
The command refuses an uncommitted script or protocol.
No generated measurement artifact belongs in Git.

A changed CI head invalidates the declaration. A changed script or protocol
requires a new reviewed declaration before switching. Do not overwrite the old
record. If CI merged before declaration capture, the pre-switch prerequisite
failed; a retrospective declaration cannot repair it.

After confirmed merge, save the same `gh pr view` projection as
`switch-merged.json`. `measure` checks that its PR/head match the declaration,
that it is merged, and that actual `mergedAt` follows declaration capture.
The driver also verifies that the protocol commit was on main before the CI
merge. A raw response is evidence of GitHub state, not permission to switch.

## Acquire and replay raw observations

Acquisition uses existing read-only project-supported commands. The CLI itself
has no network path. Save responses in a fresh observation directory, retain
command receipts and acquisition failures, and never replace an earlier snapshot.

```sh
gh pr list --repo learn-ukrainian/learn-ukrainian.github.io --state all \
  --search "created:>=$SWITCH_DATE" --limit 1000 \
  --json number,createdAt,mergedAt,headRefOid,mergeCommit,state,isDraft \
  > "$NEXT50/pr-list.json"
gh run list --repo learn-ukrainian/learn-ukrainian.github.io --workflow ci.yml \
  --created ">=$SWITCH_DATE" --limit 1000 \
  --json databaseId,event,headSha,headBranch,createdAt,conclusion,status \
  > "$NEXT50/ci-runs.json"
gh pr view "$N" --repo learn-ukrainian/learn-ukrainian.github.io \
  --json number,comments,reviews,commits,statusCheckRollup > "$NEXT50/pr-$N.json"
"$PROJECT_PYTHON" -m scripts.publish read timeline \
  --repo learn-ukrainian/learn-ukrainian.github.io --number "$N" \
  --paginate --slurp > "$NEXT50/timeline-$N.json"
gh run view "$RUN_ID" --repo learn-ukrainian/learn-ukrainian.github.io \
  --json databaseId,event,headSha,createdAt,jobs > "$NEXT50/queue-run-$RUN_ID.json"
```

`SWITCH_DATE` is the UTC date of actual CI merge. Exact timestamp filtering is
performed offline. Retrieve every candidate's timeline, including drafts and
closed PRs, and every associated queue run, including unsuccessful runs. Preserve
full run conclusions in `ci-runs.json`; the detailed view supplies job evidence.
Retrieve complete group membership, removal causes, head-update receipts, and
main-incident evidence through existing approved read paths when available.
Missing or capped results remain incomplete. Do not bypass read guards, download
restricted logs by another route, or start CI jobs to fill gaps.

Once acquisition ends, `observed_at` is a conservative UTC cutoff through which
the declared histories are complete, not a substituted timestamp for any event.
This may require finishing retrieval after the cutoff. Keep failed-command
receipts as evidence of unknown telemetry. Run offline replay with new output
filenames:

```sh
"$PROJECT_PYTHON" -m scripts.ci.pr20_measurement baseline \
  --inputs "$LAST50" --output "$EVIDENCE/last50-replay.json"
"$PROJECT_PYTHON" -m scripts.ci.pr20_measurement measure \
  --inputs "$NEXT50" --baseline "$LAST50" \
  --anchor "$EVIDENCE/pr20-declaration.json" \
  --switch-receipt "$EVIDENCE/switch-merged.json" \
  --output "$EVIDENCE/next50-observation.json"
```

Exit 0 means an artifact was written, including `UNKNOWN`, `FAIL`, and `STOP`
results. Exit 2 means invalid/unavailable input or an existing output; no verdict
is available. Read `median_20min`, `comparison`, `guardrails`, unknown counts,
selection status, and every unmerged row. Report denominator 50 throughout.
Future observation, source attribution gaps, exact-head independent review,
landing, and any revert disposition remain the accountable driver's work.

GitHub documents distinct PR and merge-group events and candidate construction
in [Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)
and [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#merge_group).
These explain event identities; saved repository evidence supplies measured values.
