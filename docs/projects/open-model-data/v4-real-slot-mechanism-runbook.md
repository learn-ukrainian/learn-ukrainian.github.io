# V4 real-slot mechanism — runbook (canonical execution/Sources authority)

PR #7662. Implements the operator-approved canonical authority architecture
(Sol advisor packet F2/F3) — see
`batch_state/briefs/v4-real-slot-mechanism-repair-6-approval.md`, the Sol
packet at `batch_state/tasks/v4-real-slot-authority-store-advisor.result`,
and the repair-6 exact-head adjudication at
`batch_state/briefs/v4-real-slot-mechanism-repair-6-adjudication.md`.

Mechanism-only. Production stays exactly **0 complete / 100 residual / 0
emitted** (verified against the checked-in production receipts, not a
fixture — see "Verification"). A13 remains open. No key is provisioned; no
live-DB migration is applied against a real production DSN by this PR.

This runbook describes what is **implemented and tested at this head**.
Everything it does not implement is listed under "Residuals" or "First-real-row
prerequisites" — there is no claim here that every trust-boundary gap is
closed.

## What was approved

Operator decision (repair-6 approval brief): extend the live Fleet Comms
PostgreSQL plane as the single canonical authority for text-free full
execution observations and Sources invocation records. Only execution/
Sources service boundaries may write, with idempotent auditable writes.
Signing credentials are root-owned on Hramatka, caller-inaccessible, under
the existing service account. Production issuers accept opaque IDs only,
resolve observations internally, and bind a fixed/versioned trust-policy
digest throughout. No synthetic production admission.

## 1. Canonical authority store (`scripts/fleet_comms/v4_canonical_authority_store.py`)

Three tables on the existing Fleet Comms plane (pg in production, sqlite
under the default dev/test authority — the same dialect-aware pattern every
other table in this plane uses):

| Table | Key | Written by |
| --- | --- | --- |
| `v4_execution_dispatch_bindings` | `request_id`, unique on `(task_id, run_id, role)` | `RequestExecutor.authorize_v4_execution`, **before** execution, while the request is still `queued` |
| `v4_execution_observations` | `(task_id, run_id, role)` | `RequestExecutor._finalize_capture`, inside the transaction that finalizes the request |
| `v4_sources_invocations` | `invocation_id` | the Sources MCP wire handler, via `record_sources_invocation_from_tool_result` |

**No public function anywhere accepts a caller-built execution-observation
or Sources-invocation record.** Both writers construct the record
themselves from primary evidence. The repair-6 passthroughs
(`ArtifactStore.record_v4_execution_observation`,
`RequestExecutor.record_v4_execution_observation`,
`ArtifactStore.record_v4_sources_invocation`) are **deleted**, and a test
asserts they do not come back.

All writes are idempotent (`INSERT ... DO NOTHING` + verify-by-readback):
a retried identical write is a no-op; a divergent write under the same key
raises `ExecutionObservationConflictError` /
`SourcesInvocationConflictError` / `ExecutionDispatchBindingConflictError`
and leaves the prior evidence untouched.

Migrations: `scripts/fleet_comms/pg_schema.py` v3 + v4,
`scripts/fleet_comms/migrations.py` v8 + v9.

## 2. The real execution writer (`scripts/fleet_comms/request_executor.py`)

The executor is the execution service boundary, split around the execution
itself:

**Before the model runs** — `authorize_v4_execution(*, request_id, task_id,
run_id, role, expected_seat_or_model, row_content_sha256, packet_sha256,
authorship_receipt_sha256=None, rubric_sha256=None)` refuses unless the
request is still `queued`, so a binding can never be minted to describe a
run that already happened. `expected_harness` is derived from the
registry-resolved recipient, not accepted as an argument. There is no
`prompt_sha256` parameter.

**At finalization** — `_build_v4_execution_observation` accepts nothing from
any caller. Each field's provenance:

| Observation field | Derived from |
| --- | --- |
| `completion_state`, `terminal_event_observed`, `process_returncode`, `session_id` | the `ResponseEnvelope` adapter conformance computed from the capture |
| `raw_capture_artifact_id`, `raw_capture_sha256` | the artifact this store actually persisted |
| `seat_or_model` | the provider's own capture events (`model` / `message.model`); refuses unless the events name exactly one model, and that model must equal the frozen binding's expectation |
| `harness` | the registry-resolved recipient, checked against `KNOWN_HARNESS_EXECUTABLES`; never the caller's `adapter=` override |
| `prompt_sha256` | sha256 of the exact request-body bytes this executor durably stored |
| `fleet_receipt_sha256` | a digest over this request's own durable lifecycle projection |
| `verification_tool_ids` | distinct `tool_id`s of canonically recorded successful Sources invocations bound to this `request_id` |
| `verdict` (reviewer) | a `V4-REVIEW-VERDICT: PASS\|FAIL` marker in the model's own output; absent or contradictory markers refuse |
| `task_id`, `run_id`, `role`, `row_content_sha256`, `packet_sha256`, `authorship_receipt_sha256`, `rubric_sha256` | the pre-execution dispatch binding |
| `saw_source_text`, `saw_heldout`, `saw_eligible_unit_ids` | structurally `False` — no argument on this boundary can set any of them true |

An execution that is not complete, has no observed terminal event, returns
nonzero, has no session identity, whose model is unobservable or disagrees
with the binding, whose harness is not canonical, or (for a reviewer) whose
verdict is unobservable, records **nothing**. The refusal is itself
recorded, text-free, as `v4_execution_observation` in the request's
`invocation_spec_json` (`unbound`, `recorded`, or `refused:<code>`), so an
operator can see why a slot has no admissible evidence.

## 3. Fixed canonical PostgreSQL production resolution

`v4_canonical_authority_store.open_production_authority_store(*, write=False)`
is the one production selector. It has no root, path, DSN, connection or
authority parameter. It refuses with `CanonicalAuthorityUnavailableError`
unless `resolve_authority(StoreId.FLEET_COMMS)` is `pg`, and refuses again
if the plane is unreachable — there is no SQLite/local fallback. Both
`v4_fleet_execution_authority._open_canonical_authority_store` and
`v4_sources_authority._open_canonical_authority_store` delegate to it and
take no arguments; a non-PG or unavailable authority raises before any
signing key is loaded.

A live Monitor check (`fleet_comms: {authority: pg, accessible: true}`) is
the deployed service configuration. A bare SSH shell's SQLite default is
not, and this code now says so by refusing rather than reading it.

## 4. The Sources invocation attester

`record_sources_invocation_from_tool_result` builds the record from the
real call:

- The **identifier is derived from the arguments the tool actually ran on**
  (`verify_word` → `word`, `verify_words`/`vet_vocabulary` → a digest of the
  canonical sorted term list, …). The repair-6 `_v4_evidence_identifier`
  caller field is removed; the server pops and discards a stale one.
- `tool_version` is the running server file's own sha256, not a hard-coded
  `"v1"` and not a caller field.
- `tool_result_sha256` is hashed from the tool's own returned text.
- Every derived term and every claimed lookup id must occur in that result
  **as a delimited token** (bounded by non-word characters), with a minimum
  lookup-id length and no duplicates. This replaces repair-6's bare
  substring test, which accepted an incidental fragment of an unrelated
  word.
- `success` is only ever `True`, and only on a record that passed every
  check. A failed, unsanctioned, empty-result, or unconfirmed call records
  nothing at all.
- `verify_quote` and `verify_source_attribution` are **removed** from the
  sanctioned allowlist: their primary argument is quote/claim text, which
  must never enter a record documented as text-free.

Recording remains best-effort and additive: a recording failure can only
prevent a later attestation, never break the tool call.

## 5. Opaque-ID production issuers

- `v4_fleet_execution_authority.issue_author_execution_receipt(*, task_id, run_id)`
- `v4_fleet_execution_authority.issue_reviewer_execution_receipt(*, task_id, run_id)`
- `v4_sources_authority.issue_verifier_attestation(*, invocation_id)`

Each resolves every other field from the canonical authority, loads the
signing key from fixed Hramatka custody, and binds the pinned production
trust-policy digest. Unknown/ambiguous/nonterminal/failed/unsuccessful
records, and a non-PG or unreachable authority, all refuse **before** the
signing key is loaded. The repair-5 full-keyword signing engine is retained
unchanged as the private `_issue_*_from_evidence` — production never calls
it; only these wrappers and this project's tests do.

## 6. Signing-key custody (`v4_trust_authority.load_production_signing_key`)

Fixed, non-parameterizable path: `/etc/hramatka/v4-signing-keys/<role>.key`
+ `<role>.key_id`. No CLI flag, environment variable, or policy object can
supply a key. Mechanism-only production has nothing provisioned — every
role refuses until the first-real-row PR provisions it. Applied to all
three keyrings (`fleet_execution`, `sources`, `a3`).

## 7. Trust-policy digest pinning, rotation, revocation

`load_production_trust_policy()` — no argument, fixed path, the raw file
bytes' sha256 must be in the code-reviewed
`PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST` (currently one entry: the
checked-in empty v1 policy, `81ce6f7b...`). Rotation: add a new versioned
file + its byte digest in a reviewed PR. Revocation: remove a digest — a
signature over a revoked policy still verifies cryptographically but every
consumer refuses because the `trust_policy_sha256` binding no longer
matches.

Every directly-signed body (fleet-execution author/reviewer receipts, the
Sources verifier attestation, A3's reference-check signature and replay
attestation) carries `trust_policy_sha256` inside the signed,
domain-separated payload. Every corresponding `verify_*` recomputes it from
the exact policy object it was given and refuses on mismatch — this is what
makes cross-chain digest disagreement and receipt policy-digest tampering
refuse even with an otherwise-valid signature.

## 8. Synthetic separation

`v4_a7_private_ledger.construct_completion` has no `allow_synthetic_fixture`
parameter; `evidence_receipt.production_capable` must be `True`
unconditionally. `build_synthetic_fixture_evidence_receipt` does not exist
in production; the test-only builder lives in
`tests/projects/open_model_data/_v4_a7_real_slot_fixture`. The
`v4_a7_private_ledger` CLI exposes no `--trust-policy`.

## Residuals (disclosed; these are NOT closed)

1. **In-process write enforcement stops at the credential boundary.** No
   public API accepts a caller-built observation/invocation record, and the
   private `_persist_*` primitives are only reachable from this module's own
   writers. But Python cannot prevent an in-process caller from importing a
   private symbol. The enforcement the operator approved, and the one that
   actually holds, is that the canonical authority is the live Fleet Comms
   PostgreSQL plane: a process without the service account's plane
   credentials cannot write these tables at all.
2. **Blindness is bound, not independently measured.** `saw_source_text` /
   `saw_heldout` / `saw_eligible_unit_ids` are structurally `False` and
   unsettable, and the exact dispatched bytes are pinned by
   `prompt_sha256`/`packet_sha256`. Whether those bytes contained source
   text is established by the A3 builder-packet receipt, not by this
   boundary re-reading them (which would require the protected corpus).
3. **The Sources `request_id` is caller-declared correlation.** The MCP
   server independently observes the tool id, version, arguments, result
   digest, claims and success, but cannot itself verify which fleet request
   a client says it is serving. `verification_tool_ids` therefore inherits
   that correlation.
4. **The reviewer verdict requires a cooperating reviewer prompt.** The
   verdict is read from a `V4-REVIEW-VERDICT:` marker in the model's own
   output. A reviewer that never emits the marker produces no observation
   (fail-closed), so the first-real-row reviewer packet must instruct it.
5. **Only harnesses in `KNOWN_HARNESS_EXECUTABLES` can be observed.** A
   request resolved to e.g. `grok` or `glm-local` cannot be authorized for a
   V4 slot at all. Widening that set is separate work.
6. **PostgreSQL semantics are exercised through the sqlite-parity path
   only.** The pg-authority tests skip without a live DSN (see
   "Verification"), so the pg dialect branches of the new writers, the pg
   `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` migration and the pg unique
   indexes are covered by ledger/statement review and sqlite parity, not by
   an executed pg run in this PR. The first-real-row PR applies and
   exercises them.
7. **Nothing here is wired to a real V4 dispatch caller yet.** The executable
   integration exists and is tested end to end against a controlled runtime;
   the first-real-row PR provisions credentials, applies the migration, and
   drives a real author/reviewer execution through it.
8. **Sanctioned-tool coverage is deliberately narrow** (seven identifier
   tools). Extending it is additive follow-up.

## First-real-row prerequisites (out of scope for this PR)

1. Apply `scripts/fleet_comms/pg_schema.py` v3 + v4 against the real
   production Postgres DSN (`apply_pg_schema` is idempotent and runs on the
   next non-readonly `ArtifactStore` open once this code is deployed).
   **Deployment ordering matters:** `verify_pg_schema` requires the complete
   known migration set, so between deploying this code and applying v4 every
   *read-only* pg `ArtifactStore` open — including
   `open_production_authority_store()` and the body-free Fleet receipt
   resolvers — fails closed with a schema-drift refusal. Apply the migration
   (one non-readonly open, or an explicit `apply_pg_schema` run) as part of
   the same deploy step, not after it.
2. Provision `/etc/hramatka/v4-signing-keys/{fleet_execution,sources,a3}.key`
   + `.key_id`, root-owned, on the Hramatka host running the attester/A3/
   Sources-server processes. Register the matching public keys under a new
   versioned trust-policy file, add its byte digest to
   `PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST`, land that in a
   code-reviewed PR.
3. Wire the real V4 dispatch caller to call
   `RequestExecutor.authorize_v4_execution` before dispatching each author/
   reviewer run, include the `V4-REVIEW-VERDICT:` instruction in the
   reviewer packet, and pass the `_v4_evidence_*` opt-in bundle from the
   Sources client when gathering real evidence.
4. Only then: generate real task/run/invocation IDs from actual executions,
   issue real receipts, and claim the first nonzero A7 completion after
   private replay and exact-head cross-family review.

## Verification (this head)

See the PR body for the exact commands and their recorded results, including
the count of pg tests skipped for want of a live DSN and the one
pre-existing, order-dependent `tests/fleet_comms/test_cold_start_board.py`
failure that also reproduces at the unmodified parent commit.
