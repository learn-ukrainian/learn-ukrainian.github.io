# Bug autopsy: a merged PR carried two completed same-head rejections that were never recorded (2026-10-13)

## What merged
PR 10502 (#10464, reviewer seats match the reviewer-seat decision: no Claude review through Cursor) merged at 2026-10-13 00:31:22Z as 51a69e70e2 at head 25d2221f28. Two completed exact-head review results for that head, both pinned to 25d2221f28, ended REQUEST_CHANGES and were not recorded on the PR. The formal review finished at 00:02:25Z and the executing supplement at 00:10:09Z:
- formal review `cf-10464d-25d2221f-formal` (gpt-6.1-sol): `docs/best-practices/fleet-role-scorecard.md` still offered a Cursor slug for Opus; the regression check `tests/test_routing_guide_d129.py` missed wrapped instructions and the `--agent=cursor` form and rejected valid guidance.
- executing supplement `cf-10464d-25d2221f-exec` (claude-opus-5-5): the same scorecard row.
The merge queue acted on a recorded APPROVE of the same head from the automatic notifier review (`cf-10502-25d2221f-sol`, recorded at 00:05:07Z). That approval sits between the two completions: the formal rejection had already finished, and the exec rejection finished after the approval was recorded.

## Impact
Documentation and regression-check quality only: resolver and catalog behaviour were not affected. The independence rule was breached in process terms: an approval stood over unrecorded same-head rejections. Fix-forward is a follow-up PR from round `impl-10464-r4-scorecard-and-check`; issue #10464 stays open until it merges.

## Why the keeper could not see them
The merge-queue keeper decides from verdict comments recorded on the PR by the recorder (`record_cf_verdict`). A completed review task is a record in the task ledger (`batch_state/tasks/<id>.json` and `.result`); until a driver runs the recorder, it is invisible to the keeper. The formal rejection finished at 00:02:25Z, before the approval was recorded at 00:05:07Z, so it already existed in the task ledger when that approval was recorded. The exec rejection finished at 00:10:09Z, after the approval was recorded. The driver of this lane recorded the approval and not either rejection, and its own earlier status report (21:57Z) had the same gap in the other direction (it listed only approvals at a head that also had an unanswered rejection). Nothing on the PR or in the queue forced the two sources to agree.

## Contributing causes
- Several independent review tasks at one head (the notifier's automatic review plus two driver-armed reviews) with no single place that lists every completed verdict for that head.
- The enqueue helper reported success from the enqueue exit code; the queue itself ejected the PR three times earlier for the same class of reason and the watcher did not read the queue state.

## Rule (effective now, harness lane; to every lane through the drive-epic review step)
Record every completed exact-head verdict, APPROVE or REQUEST_CHANGES, with `python -m scripts.review.record_cf_verdict --task-id <task> --pr <n>` immediately after the review task ends, before any other action on that PR. Before enqueue, list every `cf-verdict` marker at the head (`gh pr view <n> --json comments`) and confirm no unanswered rejection exists; check the queue state (`scripts/gh_merge_queue_status.py <n> --line`), not the enqueue exit code.

## Structural fix (ordered to the Infra lane under private issue 971 phase 1)
The keeper must read the review-task ledger, not only recorded comments: for the PR head it lists every completed review task pinned to that head (any status, any initiator), refuses to enqueue while any of them is an unrecorded rejection, and records the rejection itself through the supported recorder or alerts the lane. Rejection always wins over any approval at the same head.

## Verification
- AC-01 A fixture with one recorded approval and one completed unrecorded rejection at the same head is refused by the keeper with a typed reason naming the review task.
- AC-02 The same fixture with the rejection recorded stays refused; with the rejection answered by a new head and a fresh exact-head approval it is accepted.
