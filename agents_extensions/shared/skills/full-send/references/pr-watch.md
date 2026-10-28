# Watching a PR through review and CI

Used by `full-send` and `full-stop` between opening the PR and the gate. One supervisor per PR:
the accountable driver's cycle.

`"$PY"` is the primary checkout's interpreter ([delivery](delivery.md#interpreter)).

## Waiting

- Do not write a watcher, polling loop or `sleep` loop, and do not run a second watcher on the
  same PR: every watcher shares one GitHub rate limit.
- Arm waits on the original tasks (`scripts/dispatch.py wait <task> --run-nonce <nonce>`, see
  `review-loop`). Check CI and the queue on each driver cycle:

  ```bash
  gh pr view "$PR" --json state,isDraft,headRefOid,mergeable,mergeStateStatus,autoMergeRequest
  gh pr checks "$PR"
  "$PY" -m scripts.publish read checks --sha "$HEAD_SHA"   # REST, when GraphQL is spent
  "$PY" -m scripts.gh_merge_queue_status "$PR" --json
  ```

- While CI or a review runs, dispatch the next ready item instead of idling (drive-epic §2c).
- An event is news, not a decision: re-check the gate yourself.

## Findings from reviewers and bots

- Act only on checks and comments newer than the latest push.
- Verify each finding against the source before changing code. A real finding goes to the
  authoring lane as a fix; prove the fix before it is pushed.
- Answer a false positive with a written reason through `pr-comments`. Bot or AI review is
  advisory unless it is the reviewer of record.
- Every fix push moves the head: run the `review-loop` delta for it and wait for same-head CI.
- Keep the PR at the size its outcome needs. Decline extras (unneeded guards, rare edges,
  extra compatibility) with a reason and send them as follow-ups.

## Failing CI

- Diagnose from the failed job, or from the pytest JUnit artifact when the run has one
  (drive-epic §7).
- A real failure caused by the diff gets a fix through the authoring lane.
- A failure on code the diff does not touch is a service problem: one evidenced rerun (or one
  re-enqueue after an infrastructure ejection), recorded on the PR first, as rules core P4
  describes. A second failure, a related failure or an unclear cause means stop and report.
- After a base-branch fix, refresh with
  `"$PY" -m scripts.publish pr-update-branch --number "$PR"`, never `run-rerun`.

## The base moves

- Re-check BEHIND and DIRTY before calling the PR ready. Rebase through the authoring lane and
  push with `--force-with-lease=<branch>:<observed head>`; the new head needs a delta review
  and fresh CI.
- When the base conflicts with an approved head A only in generated files, merge the base
  into A, run the files' generators from `scripts/config/generated_paths.yaml`, commit the
  merge and push it. Once its CI is green, run
  `"$PY" scripts/review/record_cf_verdict.py carry-over --pr "$PR" --approved-head "$A"`
  instead of a delta round. A refusal names its reason; any refusal means a normal delta
  round ([policy](../../review-loop/references/policy.md#gate-of-record)).
- If another PR makes this one obsolete, stop and report it with evidence. Closing the PR is
  a driver act; closing an issue is the CTO's.

## Merge-queue kicks

After enqueue, a CI Gate comment on the PR with a run URL means the queue ejected it. Read the
failed jobs, fix or rebase, re-run the exact-head review if the head moved, and re-queue in the
same hour (drive-epic §7).
