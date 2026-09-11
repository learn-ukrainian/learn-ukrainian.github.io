### `PLAN_REVIEW_REQUIRED`

Run every configured deterministic plan-validation command. Then use the
configured family skill: `$plan-review` for CORE or `$plan-review-seminar` for
seminars. Generated reports may exist locally but must not enter the PR.

Record `PASS` or `REVISE` with `record-plan-review`. For `REVISE`, use
`$apply-plan-fixes`; structural or semantic plan edits remain approval-bound
and must follow plan versioning. After an approved plan change, use
`record-change --owner-kind plan_workflow`, then re-review the plan.
