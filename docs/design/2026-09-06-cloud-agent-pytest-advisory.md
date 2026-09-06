# Cloud-agent full pytest advisory

Status: design only; implementation and live qualification remain open. Refs #6977.

## Outcome and fixed policy

An implementer can attach artifact-derived full-suite evidence to the exact
candidate commit, catching failures missed by targeted tests before review churn.
The primary integration is a dispatch-brief acceptance step before push; a
post-push advisory GitHub Check exposes the same result. The secondary use is
advisory evidence during an Actions outage.

The [settled CI plan](../plans/2026-09-02-ci-sweet-spot.md) remains authoritative:
**no cloud-agent merge gate (#6977)**. Agent prose never determines a Check.
No required checks, Gate dependencies, branch protection, merge queue, auto-merge,
or enqueue behavior change. This design does not implement runners, workflows,
cloud jobs, or work for #7768, #6106, #6283, or private #670.

## Evidence baseline and denominator

The [#7113 prototype](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/7113)
is present at repository baseline `3ac1795f5d4cfda10853be0ee184c25dfe72e293`:

- Runner: `scripts/ci/cursor_cloud_full_pytest.sh`.
- Runner blob SHA-256: `4c39a7918bbce7ea88f91317e54c549e0def7b75e967dc01de00599dec3c62df`.
- Planner: `scripts/ci/pytest_shards.py`.
- Trusted controller verifier: `scripts/ci/cursor_cloud_pytest_verify.py`.
- Offline verifier tests: `tests/ci/test_cursor_cloud_pytest_verify.py`.

“Full suite” here means the entire public repository's CI pytest selection,
`not atlas_release and not slow`, across all four shards, including the separate
serial playground probe. It does not mean targeted changed-file tests, the
docs-only selection, every opt-in live integration, or every pytest marker.
Publish the selection, collected node-ID count and digest, skipped/deselected
counts, and serial-probe result with each run. Never label a subset as full.

Before execution, the controller freezes the candidate SHA, trusted runner and
verifier revisions/digests, nonce, build ID, selection and independently collected
node-ID inventory. Supply `--expected-nodeids-file` to the verifier; its optional
API must not become optional for this integration. Collection must use the same
candidate and dependency environment, through trusted collection machinery, not
an inventory supplied by the cloud agent. Shard union must match this anchor
without duplicates or omissions. A changed head or script invalidates the run.

The prototype is not current environment-parity proof. At the baseline above,
`.github/workflows/ci.yml` provisions PostgreSQL, native sandbox dependencies,
the local v4 runtime and generated assets, and uses a dependency installation
recipe different from the prototype. The implementer must reconcile these with
current CI before qualification, including the planner's selection and serial
probe. A sparse checkout cannot establish the full repository denominator.

## Secret-free execution boundary

Source inspection of the current pytest job shows no `secrets.*` references:
checkout disables persisted credentials, dependencies and manifest downloads
are public, and PostgreSQL uses disposable local test credentials. This supports
a secret-free public CI suite; it is not proof of a successful clean cloud run.
Qualification must demonstrate that run with no injected account credentials.

No GitHub tokens, provider keys, production DSNs, private repositories, host
configuration or private transcripts enter the test VM. Local disposable test
credentials are fixtures, not production secrets. Keep `ZNO_LIVE`,
`RUN_BRIDGE_INBOX_INTEGRATION`, and `ENFORCE_LATENCY_ASSERTIONS` unset as in the
prototype. Tests execute with `CI=true` and `GITHUB_ACTIONS=true`. If a required
test needs a real secret, stop qualification and report the dependency; do not
supply the secret, silently skip the test, or claim a full-suite pass.
Only the trusted controller may hold GitHub Check publication credentials.

## Sealed script and artifact contract

The cloud execution acceptance instruction is fixed:

```bash
bash scripts/ci/cursor_cloud_full_pytest.sh \
  --sha <candidate-40hex> --nonce <controller-nonce> --build-id <run-id>
```

Use a clean full checkout at that SHA. The controller pins the approved script
blob before dispatch; the agent cannot substitute commands, patch tests, select
fewer shards, or summarize artifacts into replacement evidence. The prototype
checks HEAD and initial cleanliness, uses four sequential shards, and checks
final cleanliness allowing only `artifacts/<nonce>/`. It makes no GitHub calls.
Its temporary environment is outside the checkout. Host-side project commands
must follow the dispatch interpreter contract; this design does not authorize
running the cloud bootstrap in a worker's shared environment.

Preserve these exact paths under `artifacts/<nonce>/`:

| Path | Required content |
| --- | --- |
| `metadata.json` | `git_head`, `runner_sha256`, `nonce`, nonempty `build_id`, `started_at` |
| `pytest-shard-{1,2,3,4}/plan.json` | Selected-suite and partition metadata |
| `pytest-shard-{1,2,3,4}/test-nodeids.txt` | Assigned node IDs |
| `pytest-shard-{1,2,3,4}/main-junit.xml` | Machine-readable pytest results |
| `pytest-shard-{1,2,3,4}/main.log` | Unedited test output |
| `pytest-shard-{1,2,3,4}/exit_code` | Integer recorded by the runner |
| `pytest-shard-1/playground-junit.xml` | Serial probe result |

Retain the complete bundle, including planner output under `plans/`; do not
commit generated artifacts. Capture the outer process exit status in the
controller's execution receipt even when setup fails before metadata exists.
The current script uses `set +e`, a pytest pipeline through `tee`, and immediate
`$?` capture under `pipefail`: this records pipeline failure, not necessarily
the raw pytest process code if logging also fails. Shard 1 folds serial-probe
failure into `exit_code`; the script exits nonzero on any shard failure or
unallowlisted dirty tree. Preserve that distinction in reporting. An outer
failure or incomplete bundle cannot be overridden by green shard XML.

The trusted controller runs the verifier from its own approved checkout, never
imports verifier code from the candidate, and supplies the expected SHA, runner
SHA-256, nonce, four shards, and anchored node-ID file. Parse its `--json` result
and require consistency with process exit (0 PASS, 1 FAIL, 2 UNKNOWN/INFRA).
The verifier checks provenance, completeness, partition integrity, exit codes
and JUnit failures/errors. A crash, malformed output, timeout or mismatch is
UNKNOWN/INFRA. Model text is never an input to this decision.

The post-push publisher creates **Cloud pytest advisory** on the exact candidate
SHA, with these deterministic conclusions:

| Validated result | GitHub conclusion | Meaning |
| --- | --- | --- |
| PASS and successful outer execution | `success` | Complete anchored selection passed |
| FAIL | `failure` | Test failure, with shard and JUnit evidence |
| UNKNOWN/INFRA or unsuccessful/incomplete execution without valid FAIL | `neutral` | Evidence unavailable or invalid; never green |

Include nonce, SHA, selection/count/digest, verifier reasons and the retained
artifact link in Check output. A stale run stays attached to its original SHA.
No Check publisher exists in this prototype; this table is its implementation
contract. This Check is never required and is never consumed by `CI Gate`.

## Integration, concurrency and outages

The dispatch brief requires invoking the sealed acceptance step after the final
commit and before push when the qualified cloud route is available. Record the
artifact-derived outcome; a red run is evidence for the implementer to fix and
rerun on a new SHA. Availability failures remain explicit residual evidence,
not a push prohibition or a substitute for existing required CI. After push,
the controller publishes the result for that same SHA; it must not rerun merely
to publish. A post-push request may run once if no matching evidence exists.

Cursor Ultra has concurrency **1**, as documented in
`docs/runbooks/cursor-driver.md` and `scripts/config/fleet_communications.yaml`.
The controller admits only one full-suite cloud run at a time across pre-push,
post-push and outage requests. Reuse a matching run; serialize distinct runs
through the existing scheduler. Do not spawn four cloud agents for four shards.
This PR does not dispatch `--agent cursor` or authorize bypassing AppArmor.

Trigger outage fallback only from an operator-confirmed Actions degradation or
observable Actions service/runner unavailability for the requested run. A red
test, CF rejection or pending review is not an outage. Record the triggering
observation and time; use the same sealed contract, not relaxed verification.

The advisory availability path **fails open**: unavailable cloud capacity,
transport or publishing yields explicit UNKNOWN/INFRA (or an unavailable
publication receipt if GitHub itself is down). Evidence validation **fails
closed against PASS**. Existing required Actions checks retain their existing
semantics: this fallback does not unblock a merge while they are unavailable.
On recovery, normal Actions remain authoritative; do not translate cloud green
into an Actions success or add the advisory to required checks.

## Explicit open decision: artifact transport

Cloud VM → controller transport is not implemented by the runner or verifier.
**Operator/designated-advisor GO is required before selecting its architecture.**
Do not invent a bucket, service, VM credential, upload workflow, or API route in
the implement PR. The approval packet must establish retrieval identity, exact
run/SHA binding, completeness, safe extraction, retention/access, failure and
timeout handling, and how untrusted candidate code cannot forge successful
evidence. A self-reported runner hash is not remote execution attestation.

Until this decision is approved and qualified, the sealed-script prototype
provides offline verification mechanics, not trustworthy live end-to-end proof.
No success may be published from agent-pasted JSON or manually reconstructed
artifacts. The existing scheduler and publisher integration must also be shown
to support the stated contract; any new service/process decision requires GO.

## Independent held-out qualification

The implementation author does not choose or certify the held-out red case.
A cross-family reviewer owns a separate disposable public test candidate with a
known unconditional assertion failure outside the targeted-change test set.
Run the complete selection through the actual cloud, approved transport,
trusted verifier and Check publisher. The reviewer verifies that the failing
node is in the anchored inventory, JUnit records its failure, the shard exit
is nonzero, and the exact-head advisory Check is `failure` even if agent prose
claims success. The denominator is the independently collected full selection,
not the one failing fixture. Remove the injected failure only in a new candidate
and repeat to demonstrate green control behavior; never modify the sealed run.

First run the existing verifier tests for red shards, red serial probe and
mutations of runner hash, target SHA, exit code and artifact structure. Extend
implementation tests for missing transport, truncated bundles, omitted nodes,
stale nonce/head, outer failure, publisher failure and one-run concurrency.
Each must fail to produce success. Offline fixtures alone do not satisfy the
live held-out proof. No tests or fixture changes belong in this design PR.

## Ownership, stop policy and completion

The assigned #6977 driver owns scope, sequencing and final disposition. The
implementation worker owns runner parity and controller integration; the
independent cross-family reviewer owns the held-out candidate and exact-head
review; the operator/advisor owns transport and any new architecture approval.
Freeze the implementation brief's SHA-256, these roles, denominator, non-goals,
evaluation and residual policy before dispatch. Re-freeze after material edits.

Remaining implementation delivery is one coherent PR for the advisory outcome:
runner/environment parity, approved transport, trusted verification/publication,
brief integration and offline plus live held-out evidence. It must not be split
merely to deliver disconnected prototypes. Transport approval precedes dependent
implementation; any deployment or newly required credentials need operator GO.
Changing merge policy is outside this design and needs a separate explicit order.

Stop on a secret requirement, missing full inventory, transport authenticity gap,
runner drift, or held-out red reported green. Report the exact SHA, observed
result, expected denominator and residual owner. Never compensate with model
assurance or weaker checks. Design completion means this document is committed,
pushed and linked from one PR referencing #6977. Operational completion requires
the later implementation and independent live qualification; this design does
not close #6977 or establish that cloud execution is operational.
