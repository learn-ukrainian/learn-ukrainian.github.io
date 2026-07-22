# Decision: required pytest uses four verified shards

- **Date:** 2026-07-22
- **Decided by:** Sol (`gpt-5.6-sol`, bridge `advise-pytest-ci-speed-sol`, ask #4342 → #4343)
- **Issue:** #5657
- **Status:** active

## Decision

Run the hermetic required pytest selection in four deterministic shards, named
`Test (pytest) [1/4]` through `Test (pytest) [4/4]`. The shared planner collects
the existing `-k "not slow and not website"` selection and its exact ignore and
deselect list, then performs deterministic longest-processing-time assignment
from the latest main-branch duration cache. A cache miss uses equal weights
for the first run and immediately publishes measured durations for the next
run. The fresh-process cache-invalidating pair and the playground wall-clock
smoke remain serial on shard 1.

Every shard uploads its planned node IDs and JUnit result from non-hidden `ci-artifacts/` (not `.ci/`, which upload-artifact skips by default). The aggregate job
rejects missing artifacts, duplicate node IDs, an incomplete partition, or a
JUnit execution count that differs from its plan. On `push` to `main`, it also
combines the four coverage data files and enforces `--cov-fail-under=35` once.
PRs remain coverage-free.

`CI Gate` is the sole stable required check. The four display names are not
branch-protection requirements; `CI Gate` depends on the matrix job and its
artifact verifier, and explicitly rejects failed, cancelled, or skipped pytest
execution when Python changes require it. Fork PRs use the same matrix and only
the ordinary read-only GitHub token—no secret-gated job is introduced.

## Acceptance and rollback

The acceptance measurements are pytest execution p95 at or below seven minutes,
critical-path p95 at or below ten minutes, no selection or coverage regression,
and a slowest shard no more than 25% above the median shard. CI duration logs
are the source of record; any shortfall is documented rather than hidden.

Rollback is a single focused revert that restores the former one-job
`Test (pytest)` implementation and removes the shard artifact aggregation.
The separate follow-up may start pytest concurrently with lint and tune the
torch cache; neither change is part of this decision.

## Follow-up (2026-07-22): lint ∥ pytest

Sol #5657 step 6: after sharding landed, pytest matrix `needs: [changes]` only
so it starts concurrent with lint. `CI Gate` remains the sole required check and
still depends on both `lint` and `test` (plus shard-artifacts). Lint failure no
longer serializes the matrix; it still blocks merge via CI Gate.
