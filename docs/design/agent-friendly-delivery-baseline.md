---
version: 1
status: specification
epic: 9737
issue: 9738
plan: docs/plans/agent-friendly-delivery.md
evaluator: scripts/ci/delivery_baseline.py
---

# Agent-friendly delivery baseline specification

This document states which timestamps, cohorts, exclusions and unknowns a before/after delivery comparison under program #9737 may use. It qualifies the timing map in [the versioned plan](../plans/agent-friendly-delivery.md) (source lines 92–108). It does not measure anything, set a speed target or gate any repair.

The offline evaluator `scripts/ci/delivery_baseline.py` applies these rules to an authored cohort file and returns a verdict per stratum. Its tests (`tests/ci/test_delivery_baseline.py`) replay synthetic fixtures in `tests/fixtures/delivery_baseline/`. Existing tools report spans but cannot apply these rules. `scripts.ci.ci_timings` and `collect_stream_bottleneck_metrics` in `scripts/fleet_comms/efficiency_metrics.py` have no definition of a delivered outcome, no per-stratum floor, no union of overlapping spans and no inconclusive verdict. `ci_timings.compute_metric_stats` also reports an empty sample as `0.0`, which this specification forbids.

## 1. Kinds of time

| Kind | Meaning | Not to be read as |
| --- | --- | --- |
| `worker_wall` | Wall-clock span of one recorded execution: a dispatch task or a reviewer task | Active coding or thinking time |
| `check_wall` | Wall-clock span of one CI check run or job, from its start to its completion | Total CI time when several checks run at once |
| `queue_delay` | Time between a recorded request and the recorded start of service: a runner job waiting for a runner, or a PR waiting in the merge queue | Any gap inferred from approval, chat or a later event |
| `elapsed` | Coarse span between two canonical events of different owners, for example issue creation to dispatch | Work time, or time attributable to one owner |
| missing | No canonical start and end pair exists for this record | Zero, fast or green |

A span is **qualified** only if both endpoints are values of the canonical field pair registered for its stage and kind (§2). It is **unknown** if an endpoint is absent or unparseable, if it lacks a timezone, if it ends before it starts, or if it comes from any other source. A stage with no canonical pair at all is **unqualified**. File modification times, chat transcripts, agent narration and dashboard windows are never sources. Unknown and unqualified values are reported as `null` together with a reason. They are never replaced by zero and never shown as passing.

## 2. Stage-to-field inventory

"Owner" is the module that writes or reads the field today. "Task record" means `batch_state/tasks/<task-id>.json`, written by `scripts/delegate.py`. "Lifecycle ledger" means a `task-lifecycle.v1` ledger owned by `scripts/orchestration/task_lifecycle.py`; its GitHub reads go through `scripts/orchestration/task_closeout.py`.

| Stage | Kind | Start field | End field | Owner | Status and limits |
| --- | --- | --- | --- | --- | --- |
| Intake | `elapsed` | GitHub issue `createdAt` | First linked dispatch task `started_at` | GitHub; `scripts/delegate.py` | Qualified only if the task is linked to the issue through the lifecycle ledger `identity.github_issue_number`. This span does not separate readiness work from waiting. |
| Onboarding | — | — | — | Session capsule `generated_at` and canary `checked_at` are point observations | **Unqualified.** No paired start and end fields exist. |
| Capacity | — | — | — | Routing selection and admission | **Unqualified.** The task record writes `started_at` at admission (`admitted_at`) or at worktree reservation (`reserved_at`). No field records when the worker process actually started. Admission delay therefore cannot be measured. Deriving it as `finished_at − started_at − duration_s` assumes endpoints that no field records, so it is not allowed. |
| Authoring | `worker_wall` | Task `started_at` | Task `finished_at` | `scripts/delegate.py` | Qualified. The span includes the admission hold and any checks run inside the task. The task record field `duration_s` (worker monotonic runtime) may be reported next to this span, but it is a duration without endpoints and is never merged into a union. |
| Verification/review | `worker_wall` | Reviewer task `started_at` | Reviewer task `finished_at` | `scripts/delegate.py` | Qualified only if the reviewer task is linked to the reviewed PR head, through `pinned_head` or `review_attempt`. |
| Verification/review | `elapsed` | Fleet `formal_review_jobs.created_at` | Fleet `github_publications.published_at` | `scripts/fleet_comms/migrations.py` schema; read by `collect_stream_bottleneck_metrics` (span `formal_cf_publication`) | Qualified. This is request-to-publication time, not reviewer execution time. Lifecycle evidence `recorded_at` is a single point and never a duration. |
| CI/landing | `check_wall` | Check run `startedAt` | Check run `completedAt` | GitHub `statusCheckRollup` via `task_closeout.project_closeout_checks`; Actions job `started_at`/`completed_at` via `scripts/ci/ci_timings.py` | Qualified per check. Concurrent checks overlap (§3). |
| CI/landing | `queue_delay` | Actions job `created_at` | Actions job `started_at` | `scripts/ci/ci_timings.py` (`job_queue_wait_minutes`) | Qualified. This is runner wait only. |
| CI/landing | `queue_delay` | GitHub timeline `AddedToMergeQueueEvent.createdAt` | PR `mergedAt` | GitHub GraphQL timeline | The field pair is canonical, but no repository module collects the historical enqueue event yet. Until a cohort supplies it, merge-queue delay is **unknown**. The `ci_timings` time-in-queue (first `merge_group` run `created_at` to the landing run `updated_at`) is a lower bound that omits scheduling before the first run. It is reported separately and never substituted for this metric. |
| CI/landing | `elapsed` | PR `createdAt` | PR `mergedAt` | GitHub; `task_closeout` reads `mergedAt` | Qualified PR lifetime. |
| CI/landing | `elapsed` | Fleet `github_publications.published_at` | PR `mergedAt` | `collect_stream_bottleneck_metrics` (span `gate_to_merge`) | Qualified gate-to-merge time. |
| Recovery/closeout | `elapsed` | Failed attempt task `finished_at` | Retry attempt task `started_at` | `scripts/delegate.py` | Qualified only if both attempts carry one canonical identity, such as the same lifecycle id or review id. Otherwise unknown. |
| Recovery/closeout | `elapsed` | PR `mergedAt` | Lifecycle `observation_receipts[].observed_at` of the first `CLEANED_UP` receipt | `task_lifecycle.reconcile` | Qualified only as an upper bound on time from merge to observed cleanup. A receipt's arrival time is not the duration of the cleanup operation, which is **unqualified**. |

The evaluator's `CANONICAL_SPANS` registry encodes exactly this table. A change to either one needs the other to change in the same commit.

## 3. Overlap rule

Spans that overlap in time are never added together. For each record, stage and kind, the evaluator reports two things. The first is the per-span durations. The second is the length of the union of the intervals, where overlapping time counts once (`union_s`). Two 10-minute check runs that overlap by 5 minutes give 15 minutes, not 20. A record's end-to-end elapsed time is never the sum of its stage spans. Stage spans that overlap each other, such as authoring that includes checks, are reported per stage only.

## 4. Cohorts, strata and exclusions

- **Source.** Cohort members come from canonical task records and GitHub PR, check and merge history. Lifecycle ledgers are acceptance evidence where they exist. They are not an unbiased before group, and the two completed pilot ledgers are coverage examples only.
- **Freeze before comparison.** Membership, arm (`before` or `after`), stratum, matched setup and the definition of delivered are fixed in the cohort file before any timing is read. The report records the cohort's `input_sha256`. Changing membership after seeing timings creates a new cohort with a new digest.
- **Strata.** The six representative cases from #9737 are `launcher_repair`, `provider_runtime_failure`, `routine_product_change`, `architecture_change`, `ukrainian_content` and `long_epic_resume`. A record outside them (for example a CI/test repair) is excluded with the reason `outside_frozen_strata`. It is still listed in the report.
- **Matched setup.** Each record carries `matched_setup`, for example the required-check set and review profile. If delivered records in a stratum carry more than one setup value across the two arms, the comparison is `inconclusive` (`incomparable_setup`).
- **Explicit exclusions.** Dry runs, duplicate attempts of one outcome and records that cannot be read are excluded with a stated reason and listed. They are never silently dropped.
- **Denominators.** Each stratum and arm reports its members, its delivered count and a count of each not-delivered reason.

## 5. Delivered

A record counts as delivered only if it has all of the following:

1. **Linked outcome:** an issue number and a PR number.
2. **Review of record:** an `APPROVE` verdict from a family different from the author's family, on the merged head SHA. Otherwise the reason is `no_review_of_record`, `review_not_independent` or `review_not_exact_head`.
3. **Merge:** a `mergedAt` value and a merged head SHA.
4. **Cleanup:** a lifecycle `CLEANED_UP` observation, or an equivalent `scripts.orchestration.merge_closeout` proof. Either is entered in the cohort as `cleanup.state: CLEANED_UP` with its `observed_at`.

A task with status `done`, a receipt file, an open or queued PR, or a green dashboard is not delivered.

## 6. Comparison rule

- The comparison unit is one stratum and one metric (`stage.kind`). Strata are never pooled. A claim about a pooled or unnamed group is rejected (`not_a_single_frozen_stratum`).
- **Floor.** Each arm needs at least five delivered records within that stratum. Five per arm counted across strata does not meet the floor for any one stratum. The floor is a coverage minimum, not statistical power, and it does not guarantee significance.
- **Completeness.** Every delivered record in both arms must have a qualified value for the metric. Any unknown, unqualified or missing value makes that metric `inconclusive`, because dropping such records could bias the comparison.
- **Outputs.** A `reportable` metric reports `n`, minimum, median and maximum per arm. It names no winner. A claim about a reportable metric is `admissible`, meaning only that the distribution may be reported. Every other claim is `rejected` (`comparison_inconclusive`).
- **Repair admission.** The floor and these verdicts never gate repair admission. Correctness-qualified repairs ship under their normal issue gates while the baseline accumulates (plan source line 108).
- **Speed claims.** No fleet delivery-speed claim is made outside Phase 3 of the plan.

## 7. Evaluator input and fixtures

Input schema `delivery-baseline-input.v1` has two fields. `records[]` holds each record's `task_id`, `arm`, `stratum`, `matched_setup`, `outcome`, `review_of_record`, `merge`, `cleanup`, optional `exclusion` and `spans[]`. Each span carries `stage`, `kind`, `start_field`, `end_field`, `start` and `end`. The optional `claims[]` lists `{stratum, metric}` pairs. Run it with:

```bash
.venv/bin/python -m scripts.ci.delivery_baseline <cohort.json>
```

The evaluator exits 0 with a `delivery-baseline-report.v1` JSON document, or exits 2 on malformed input. It reads no task store, GitHub or Fleet database. Extracting canonical values into a cohort file is a separate, later step, and it must not commit real task records or telemetry.

| Fixture | What it proves |
| --- | --- |
| `canonical_linked.json` | A canonical task with a linked PR, check run, runner wait and PR lifetime gives qualified spans |
| `unknown_span.json` | A missing endpoint and a non-canonical (`file.mtime`) source give `unknown` with `null`. Onboarding gives `unqualified`. The comparison is `inconclusive` |
| `overlapping_spans.json` | Overlapping check runs give a 900-second union with per-span values of 600 seconds each, never a 1,200-second sum |
| `not_delivered.json` | Unlinked, unmerged, unreviewed, self-reviewed, stale-head and uncleaned records are not delivered. Out-of-strata and dry-run records are excluded |
| `stratum_floor.json` | 11 delivered per arm pooled, but 5/1 and 1/5 within two strata, makes both of those strata `inconclusive`. A stratum with 5 per arm is `reportable`. Claims on inconclusive or pooled comparisons are rejected |

All fixtures are synthetic: invented task ids, PR numbers and SHAs, and no real records. The independent reviewer selects its own held-out controls.
