---
name: track-completion
description: Complete one active Ukrainian curriculum module through a canonical CORE-or-seminar workflow. Use for built modules that need the versioned post-build gate, unbuilt modules that need plan review and V7 construction before that gate, interrupted module completion runs that must resume from a durable ledger, or non-PASS modules that need root-cause repair, fresh review, independent cross-family review, and publication.
---

# Track completion

Operate on exactly one `track/slug`. Keep the operator prompt short:

```text
Use $track-completion for bio/example-slug.
```

Use this skill as the mutating outer workflow. Compose `$post-build-review` as
the only readiness gate; keep every post-build-review invocation read-only.
Never run legacy LLM-QG, a separate deterministic audit, or a legacy content
review as an operator completion gate.

## Start or resume

1. Preserve the legacy parity boundary documented below. Post-build review v3
   owns semantic readiness; the outer skill owns lifecycle and persistence.
2. Satisfy repository issue, stream, worktree, research-classification, and
   pending-decision preflight before mutation. Work in the existing scoped
   issue worktree; do not ask V7 to create another worktree.
3. Inspect the target:

   ```bash
   .venv/bin/python \
     agents_extensions/shared/skills/track-completion/scripts/track_completion.py \
     inspect <track/slug>
   ```

4. Start a new ledger or resume the exact recorded run. Record the model family
   that will author each later build or repair; do not guess it:

   ```bash
   .venv/bin/python \
     agents_extensions/shared/skills/track-completion/scripts/track_completion.py \
     start <track/slug> --owner <agent/task>
   ```

   Preserve the returned `run_id` and `ledger_path`. The ledger is durable,
   gitignored runtime state shared across worktrees. A live per-module lease
   rejects concurrent operators. Use `resume --run-id <id>` after interruption;
   never mint a replacement run merely to bypass a lease or stale evidence.

## Follow the returned state

### `PLAN_REVIEW_REQUIRED`

Run every configured deterministic plan-validation command. Then use the
configured family skill: `$plan-review` for CORE or `$plan-review-seminar` for
seminars. Generated reports may exist locally but must not enter the PR.

Record `PASS` or `REVISE` with `record-plan-review`. For `REVISE`, use
`$apply-plan-fixes`; structural or semantic plan edits remain approval-bound
and must follow plan versioning. After an approved plan change, use
`record-change --owner-kind plan_workflow`, then re-review the plan.

### `PARTIAL_RECOVERY_REQUIRED`

Do not delete or overwrite partial artifacts automatically. Diagnose why a
unique built content target is absent or ambiguous. Preserve forensic build
evidence, repair the build/source workflow, and use the configured V7 command
with `--no-resume` when any build input changed. Record a successful complete
bundle with `record-build`.

### `BUILD_REQUIRED`

Run the configured V7 command from the current issue worktree without
`--worktree`. Use `--no-resume` after plan, source, prompt, policy, or build
input changes; V7 artifact-existence resume is not canonical completion
freshness. Record the actual writer/repair author family with `record-build`.

### `POST_BUILD_REVIEW_REQUIRED`

Read and follow `$post-build-review` completely for the same target. Allocate a
new invocation directory every time. Do not repair, normalize, or retry inside
that invocation. Record its exact result:

```bash
.venv/bin/python \
  agents_extensions/shared/skills/track-completion/scripts/track_completion.py \
  record-review <track/slug> --run-id <id> --result <result_path>
```

The helper rejects target/source drift and validates the canonical result.
Never substitute `llm_qg.json`, SQLite, a score, or a generated audit report.

### `REPAIR_REQUIRED`

Use only the returned deterministic owners:

- `built_artifact`: repair learner-facing content/activities/vocabulary/
  resources or their canonical generation source.
- `plan_workflow`: return to the approval-bound versioned plan workflow.
- `audit_tooling`: repair the audit, prompt, policy, schema, reviewer route, or
  evidence tooling. Do not edit curriculum content to satisfy protocol noise.

An ambiguous finding routes to `audit_tooling`; do not guess. After a real
change, run `record-change` with the matching owner and author family. The
helper requires an identity change and returns to a fresh post-build review.
If a non-PASS finding is suspected reviewer noise, do not mutate content first:
run one distinct review with the exact same reviewer identity and record it
using `record-review --stability-check`. A material flip enters
`REVIEWER_INSTABILITY`; a stable result returns the same repair route.

### `REVIEWER_INSTABILITY`

Stop content mutation. Preserve both review results. Identical source, config,
protocol, prompt, and reviewer identity with a different material finding or
disposition fingerprint is reviewer/tooling instability. Adjudicate the route,
prompt, evidence access, or reviewer. Record either a real `audit_tooling`
change with `record-change` or a no-source-change route adjudication with
`record-instability-adjudication`; the next review must use a materially
different reviewer identity or the same unstable identity will stop again.
Never average results or rewrite content to chase the flip.

### `INDEPENDENT_REVIEW_REQUIRED`

Send the final diff to one reviewer outside every recorded machine author
family. Internal same-family subagents do not satisfy this gate. Record the
reviewer family, exact evidence artifact, and `PASS`. Resolve requested changes,
record `CHANGES_REQUESTED` with its deterministic `--owner-kind`, resolve the
repair, and rerun post-build review before trying again.

### `PUBLISH_REQUIRED`

Run configured shippability checks and repository pre-submit gates. Commit with
the required `X-Agent` trailer, open one scoped PR, attach module-build telemetry
when the run built a module, wait for the independent review gate, arm
auto-merge, monitor through merge, close the issue with evidence, and clean the
branch/worktree. Record the PR and merge SHA with `record-published` before
cleanup. A current PASS with no build or repair completes as `NO_CHANGE_PASS`
without creating an empty PR.

## Invariants

- Process one module and one ledger lease at a time.
- Treat any unrecorded identity drift as stale evidence.
- Require fresh hashes and a fresh post-build result after every mutation.
- Preserve previously passing deterministic behavior; fix regressions before
  continuing.
- Keep ledgers, leases, review packets/results, generated reports, status,
  audit, review, and telemetry runtime files out of the PR.
- Keep track differences in
  [config/track-completion.v1.yaml](config/track-completion.v1.yaml); do not add
  track-name branches to the state-machine script.

## Legacy parity boundary

The repository-backed feature audit has these binding dispositions:

| Capability | Completion disposition |
| --- | --- |
| Pedagogical, naturalness, decolonization, engagement, tone; scaffolding/leakage canaries; Ukrainian/factual/decolonization/media evidence | ABSORB into post-build prompt v3, schema, strict normalizer, and regression tests |
| Deterministic surface/activity/vocabulary/resource/route/size checks | ABSORB through post-build preparation; never invoke separately |
| Author lineage, repairability, freshness, bounded correction, and stability | REPLACE with ledger identities, deterministic owners, fresh review, and `REVIEWER_INSTABILITY` |
| Numeric scores, warning demotion, parser salvage, merged retries, score sidecars, DB/mtime readiness, same-route median independence | REJECT |
| Canary calibration, cost/circuit experiments, deep-read evaluation, and V7's internal LLM-QG while it remains | RETAIN-EVAL only; none can complete the outer state machine |

Before deprecating separate operator invocation, tests must prove current and
historical schema validation, exact five-dimension coverage, core/seminar
canaries, legacy-artifact non-authority, instability detection, and built plus
unbuilt CORE/seminar resolution.
