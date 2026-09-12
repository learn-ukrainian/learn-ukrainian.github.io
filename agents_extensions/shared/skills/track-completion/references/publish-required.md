### `PUBLISH_REQUIRED`

Run configured shippability checks and repository pre-submit gates. The strict
integration receipt must later prove `PASS` for MDX drift, source parity,
forward parity, `verify_shippable`, deterministic audits, focused tests,
artifact scope, the `X-Agent` trailer, and forbidden-file checks. Commit with
the required `X-Agent` trailer, open one scoped PR, attach module-build telemetry
when the run built a module, wait for the independent review gate, arm
auto-merge, and monitor through merge. Record the PR and exact merge SHA with
`record-published`; this advances to `INTEGRATION_REQUIRED` and never completes
the run. Then close the issue with evidence, clean the branch/worktree, and
record the strict integration artifact bound to the same PR and merge SHA. A
current PASS with no build or repair may satisfy goal `merge` as
`NO_CHANGE_PASS` without creating an empty PR; goal `deploy` still needs an
exact publication identity.
