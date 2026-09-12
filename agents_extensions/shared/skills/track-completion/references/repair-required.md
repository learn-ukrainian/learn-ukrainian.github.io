### `REPAIR_REQUIRED`

Use only the returned deterministic owners:

- `built_artifact`: repair learner-facing content/activities/vocabulary/
  resources or their canonical generation source.
- `plan_workflow`: return to the approval-bound versioned plan workflow.
- `audit_tooling`: repair the audit, prompt, policy, schema, reviewer route, or
  evidence tooling. Do not edit curriculum content to satisfy protocol noise.

An ambiguous finding routes to `audit_tooling`; do not guess. After the one
allowed learner-source change, run `record-change` with owner
`built_artifact`; the helper invalidates the initial semantic evidence and
permits the final review only after fresh deterministic verification. A second
learner repair or third semantic review is rejected without ledger mutation
and leaves the terminal disposition `BLOCKED_BUDGET_EXHAUSTED`. Audit-tooling
drift with unchanged learner source is deferred, not repaired inside this run.
Do not run an unchanged-source stability retry in a bounded active run: it
would spend a forbidden semantic call. Preserve the finding and route any
tooling/reviewer concern to a later run; `REVIEWER_INSTABILITY` remains only
for already-recorded contradictory evidence, never as authorization for a
third call.
