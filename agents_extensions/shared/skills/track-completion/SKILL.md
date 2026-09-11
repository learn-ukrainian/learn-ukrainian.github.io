---
name: track-completion
description: Complete or resume one CORE or seminar module, including plan review, build, repair, independent review, and publication.
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

For a normal BIO module request, this ledger is the one authoritative bounded
module workflow. `$curriculum-lifecycle` may order and acquire the module, but
it must not reproduce this completion policy. `$local-code-review` is reserved
for a code/infra diff and never repeats this learner-content semantic gate.

`$curriculum-lifecycle` hands a target here when the latest canonical result is
`build` or `certify`, plus one narrow class of `prepare` result: the bundle is
built, every current requirement passes, and the only remaining reason is
`PREPARATION_IDENTITY_MISSING` or `PREPARATION_IDENTITY_DRIFT`. `plan`, any
`prepare` with a failed plan/preparation requirement, and reviewed HOLD `stop`
remain outside this skill. One `stop` exception enters here: canonical state
`partial-bundle` with `PARTIAL_LEARNER_BUNDLE` owned by `built_artifact` and no
`PREPARATION_HOLD_ACTIVE`. It follows the existing `PARTIAL_RECOVERY_REQUIRED`
forensic path. Treat every incoming result only as owner routing, never as
caller-supplied build or certification authority. A mixed or unknown stop fails
closed.

For the exception, derive the consumed preparation identity from the latest
`BUILD_RECORDED` event in this authoritative ledger and rerun canonical
readiness with it. Before any post-build review, take the explicit transition:

```bash
.venv/bin/python \
  agents_extensions/shared/skills/track-completion/scripts/track_completion.py \
  request-preparation-rebuild <track/slug> --run-id <id>
```

Continue only from its fresh result: rebuild from `BUILD_REQUIRED`, or preserve
and report `PREPARATION_BLOCKED`. A failed requirement or mixed/unknown
combination fails closed. Do not weaken or bypass this identity-consumption
gate.

## Canonical entry paths

New and existing modules use one lifecycle, not separate completion systems:

- An `UNBUILT` module enters at `PLAN_REVIEW_REQUIRED`, advances through the
  versioned plan/build stages, and then reaches `POST_BUILD_REVIEW_REQUIRED`.
- A complete existing `BUILT` module enters directly at
  `POST_BUILD_REVIEW_REQUIRED`; do not rebuild it merely because it already
  exists. A stale preparation identity routes through the explicit rebuild
  transition before returning to that same gate.
- A `PARTIAL` module enters forensic recovery, records one complete build, and
  then reaches the same post-build gate.

From `POST_BUILD_REVIEW_REQUIRED` onward, every entry path uses the same
versioned scorer, fail-closed categorical disposition, source-hash invalidation,
automated repair loop, independent cross-family review, publication, and
rendered deployment verification. A repair never patches only the review
artifact: record the owning source change and rerun a fresh canonical review.
An unchanged existing module with a current PASS remains idempotent and must not
be rebuilt or republished without a terminal-goal reason.

## Bounded completion contract

The canonical issue #5452 contract is
`contracts/bounded-completion.v1.json`. Its strict contract and run schemas are
`schema/bounded-completion-contract.v1.schema.json` and
`schema/bounded-completion-run.v1.schema.json`. Validate them without invoking a
provider:

```bash
.venv/bin/python \
  agents_extensions/shared/skills/track-completion/scripts/bounded_completion.py \
  validate-contract
```

The canonical engine binds the helper into the durable module ledger when it
prepares and authorizes the first canonical post-build semantic call. It
freezes the exact versioned protocol identity and learner-source hashes for that active run and
enforces one initial semantic review, at most one consolidated learner repair,
and at most one final semantic review. A third review or second repair is
rejected before mutation. A material learner-source change invalidates prior
review evidence, and a final non-PASS exhausts the budget into terminal
`BLOCKED_BUDGET_EXHAUSTED`. Publication requires every canonical quality
dimension to remain at or above `9.0`.

The helper has no provider transport and must never be treated as semantic
review evidence. The durable ledger retains the initial/final review, the
consolidated repair, remaining canonical budgets, terminal disposition, and
any deferred audit-tooling drift. A ledger without `bounded_completion` is
a legacy ledger: its historic reviews remain provisional and it never receives
an inferred bounded history. Quarantine it and create a fresh bounded run
without deleting its evidence:

```bash
.venv/bin/python \
  agents_extensions/shared/skills/track-completion/scripts/track_completion.py \
  migrate-bounded-completion <track/slug> --run-id <legacy-run-id>
.venv/bin/python \
  agents_extensions/shared/skills/track-completion/scripts/track_completion.py \
  restart-bounded-completion <track/slug> --run-id <legacy-run-id> \
  --owner <agent/task>
```

The restart moves prior reviews, certification records, publication/QG records,
and identities into non-authoritative archival ledger storage.

## Start or resume

1. Preserve the legacy parity boundary documented below. The current versioned
   post-build review owns semantic readiness; the outer skill owns lifecycle
   and persistence.
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
     start <track/slug> --owner <agent/task> \
     --terminal-goal <merge|certify|deploy>
   ```

   Preserve the returned `run_id` and `ledger_path`. The ledger is durable,
   gitignored runtime state shared across worktrees. A live per-module lease
   rejects concurrent operators. Use `resume --run-id <id>` after interruption;
   never mint a replacement run merely to bypass a lease or stale evidence.
   If review tooling changes while the run is active and learner hashes are
   unchanged, record it with `record-change --owner-kind audit_tooling`. The
   engine classifies it as `AUDIT_TOOLING_DEFERRED` and queues it for a later
   run: it does not reopen this run, consume either bounded budget, or make
   frozen evidence current under the new tooling.
   A legacy ledger without a goal is non-authoritative. Migrate it with explicit
   intent:

   ```bash
   .venv/bin/python \
     agents_extensions/shared/skills/track-completion/scripts/track_completion.py \
     migrate-terminal-goal <track/slug> --run-id <legacy-run-id> \
     --terminal-goal <merge|certify|deploy>
   ```

   A `PBR_PASS_QG_PENDING` migration must also supply `--pr <number>` and
   `--merge-sha <40-character-sha>`. Never infer a goal from historical cursor
   state.

   The deterministic module resume command is:

   ```bash
   .venv/bin/python agents_extensions/shared/skills/track-completion/scripts/track_completion.py \
     resume <track/slug> --run-id <id>
   ```

## Follow the returned state

Read only the reference for the state returned by the canonical engine. After
a transition, load its new state reference before acting. Never select a state
from caller claims or skip a gate. All command/resource paths are repository-
root or skill-root paths as written; do not resolve them under `references/`.

| Returned state | Required reference |
| --- | --- |
| `PLAN_REVIEW_REQUIRED` | [Procedure](references/plan-review-required.md) |
| `PARTIAL_RECOVERY_REQUIRED` | [Procedure](references/partial-recovery-required.md) |
| `BUILD_REQUIRED` | [Procedure](references/build-required.md) |
| `POST_BUILD_REVIEW_REQUIRED` | [Procedure](references/post-build-review-required.md) |
| `REPAIR_REQUIRED` | [Procedure](references/repair-required.md) |
| `REVIEWER_INSTABILITY` | [Procedure](references/reviewer-instability.md) |
| `INDEPENDENT_REVIEW_REQUIRED` | [Procedure](references/independent-review-required.md) |
| `BLOCKED_BUDGET_EXHAUSTED` | [Procedure](references/blocked-budget-exhausted.md) |
| `PUBLISH_REQUIRED` | [Procedure](references/publish-required.md) |
| `INTEGRATION_REQUIRED` | [Procedure](references/integration-required.md) |
| `AWAITING_PRODUCTION_QG_ARMING` | [Procedure](references/awaiting-production-qg-arming.md) |
| `PRODUCTION_QG_REQUIRED` | [Procedure](references/production-qg-required.md) |
| `DEPLOYMENT_REQUIRED` | [Procedure](references/deployment-required.md) |

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
| Pedagogical, naturalness, decolonization, engagement, tone; scaffolding/leakage canaries; Ukrainian/factual/decolonization/media evidence | ABSORB into post-build prompt v4, schema, strict normalizer, and regression tests |
| Deterministic surface/activity/vocabulary/resource/route/size checks | ABSORB through post-build preparation; never invoke separately |
| Author lineage, repairability, freshness, bounded correction, and stability | REPLACE with ledger identities, deterministic owners, fresh review, and `REVIEWER_INSTABILITY` |
| Schema-bound, evidence-backed in-result diagnostic dimension scores and a reporting-only minimum | ACCEPT; categorical semantic and deterministic gates remain authoritative, with `PASS` calibrated to `9.0+` per dimension |
| Numeric averages, score sidecars, a minimum-score shortcut around categorical evidence, warning demotion, parser salvage, merged retries, DB/mtime readiness, same-route median independence | REJECT |
| Canary calibration, cost/circuit experiments, deep-read evaluation, and V7's internal LLM-QG while it remains | RETAIN-EVAL only; none can complete the outer state machine |

Before deprecating separate operator invocation, tests must prove current and
historical schema validation, exact five-dimension coverage, core/seminar
canaries, legacy-artifact non-authority, instability detection, and built plus
unbuilt CORE/seminar resolution.
