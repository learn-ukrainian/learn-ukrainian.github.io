# V4 real-slot mechanism — repair 6 runbook (canonical authority store)

PR #7662. Repairs the two accepted trust-boundary blockers (Sol advisor
packet F2/F3) against operator-approved architecture — see
`batch_state/briefs/v4-real-slot-mechanism-repair-6-approval.md` and the
Sol packet at `batch_state/tasks/v4-real-slot-authority-store-advisor.result`.

Mechanism-only. Production stays exactly **0 complete / 100 residual / 0
emitted** after this repair (verified against the checked-in production
receipts, not a fixture — see "Verification" below). A13 remains open. No
key is provisioned; no live-DB migration is applied against a real
production DSN by this PR.

## What was approved

Operator decision (repair-6 approval brief): extend the live Fleet Comms
PostgreSQL plane as the single canonical authority for text-free full
execution observations and Sources invocation records. Only execution/
Sources service boundaries may write, with idempotent auditable writes.
Signing credentials are root-owned on Hramatka, caller-inaccessible, under
the existing service account. Production issuers accept opaque IDs only,
resolve observations internally, and bind a fixed/versioned trust-policy
digest throughout. No synthetic production admission.

## What this repair implements

### 1. Canonical authority store (`scripts/fleet_comms/v4_canonical_authority_store.py`)

Two new tables on the existing Fleet Comms plane (pg in production, sqlite
under the default dev/test authority — same dialect-aware pattern every
other table in this plane already uses):

- `v4_execution_observations` — keyed `(task_id, run_id, role)`. Written
  only via `ArtifactStore.record_v4_execution_observation`/
  `RequestExecutor.record_v4_execution_observation` (the sanctioned
  execution-boundary call site: call only after a request has already been
  finalized `CompletionState.COMPLETE` by `RequestExecutor.execute_capture`).
- `v4_sources_invocations` — keyed `invocation_id`. Written only by the
  Sources MCP wire handler (`.mcp/servers/sources/server.py`,
  `_record_v4_verifier_invocation`), which independently re-checks the
  caller's claimed identifier/lookup-ids are actually substrings of the
  tool's own genuine result text before recording — an "invocation
  attester", never a passthrough recorder (mirrors the fleet-execution
  attester pattern from repair 5).

Both writers are idempotent (`INSERT ... DO NOTHING` + verify-by-readback):
a retried identical write is a no-op; a divergent write under the same key
raises `ExecutionObservationConflictError`/`SourcesInvocationConflictError`.
Migrations: `scripts/fleet_comms/pg_schema.py` v3,
`scripts/fleet_comms/migrations.py` v8.

### 2. Opaque-ID production issuers

- `v4_fleet_execution_authority.issue_author_execution_receipt(*, task_id, run_id)`
- `v4_fleet_execution_authority.issue_reviewer_execution_receipt(*, task_id, run_id)`
- `v4_sources_authority.issue_verifier_attestation(*, invocation_id)`

Each resolves every other field (task state, envelope, role observation /
Sources invocation fields) from the canonical store, loads the signing key
from fixed Hramatka custody, and binds the pinned production trust-policy
digest — never from a caller-supplied argument. Unknown/ambiguous/
nonterminal/failed/unsuccessful canonical records refuse **before** the
signing key is ever loaded. The prior repair-5 full-keyword signing engine
is retained unchanged as the private `_issue_*_from_evidence` — production
never calls it; only these wrappers and this project's own tests do.

### 3. Signing-key custody (`v4_trust_authority.load_production_signing_key`)

Fixed, non-parameterizable path: `/etc/hramatka/v4-signing-keys/<role>.key`
+ `<role>.key_id`. No CLI flag, environment variable, or policy object can
supply a key. Mechanism-only production has nothing provisioned here yet —
every role refuses until the first-real-row PR provisions it. Applied to
all three keyrings (`fleet_execution`, `sources`, `a3` — see
`v4_a3_reference_check.sign_reference_check_receipt`/`issue_replay_
attestation`, which now take no `signing_key_hex`/`signer_key_id` argument
either, for the identical custody reason even though A3 itself still needs
its own private reference material).

### 4. Trust-policy digest pinning, rotation, revocation

`v4_trust_authority.load_production_trust_policy()` — no argument, fixed
path, the raw file bytes' sha256 must be in the code-reviewed
`PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST` (currently one entry: the
checked-in empty v1 policy, `81ce6f7b...`). Rotation: add a new versioned
file + its byte digest in a reviewed PR. Revocation: remove a digest from
the allowlist — a signature over a revoked policy's content still verifies
cryptographically but every consumer refuses because `trust_policy_sha256`
binding (below) no longer matches.

Every directly-signed body in this mechanism (fleet-execution author/
reviewer receipts, the Sources verifier attestation, A3's reference-check
signature and replay attestation) now carries `trust_policy_sha256` inside
the signed, domain-separated payload — `v4_trust_authority.trust_policy_
sha256(policy)` (canonical-JSON digest, distinct from the file-byte digest
used only for the production allowlist gate). Every corresponding
`verify_*` recomputes this from the exact `trust_policy` object it was
given and refuses on any mismatch — this is what makes "cross-chain digest
disagreement" and "receipt policy-digest tampering" refuse even with an
otherwise-valid signature. A7's downstream receipts (authorship/review/
evidence/private-entry/public-completion) do not carry a second, separate
copy of this field — they embed the already-signed artifacts whole, so the
binding is inherited transitively through the same recompute/verify chain
that already re-derives everything else in private replay. Adding a
redundant plaintext copy at every wrapper layer was scoped out of this
repair as non-load-bearing (see "Residual scope" below).

### 5. Synthetic separation

`v4_a7_private_ledger.construct_completion` no longer accepts
`allow_synthetic_fixture` at all — `evidence_receipt.production_capable`
must be `True` unconditionally. `v4_a7_evidence_binder.build_synthetic_
fixture_evidence_receipt` no longer exists in production; the test-only
builder moved to `tests/projects/open_model_data/_v4_a7_real_slot_fixture
.build_synthetic_fixture_evidence_receipt`. The CLI in `v4_a7_private_
ledger.main` no longer exposes `--trust-policy`.

## First-real-row prerequisites (out of scope for this PR)

1. Apply `scripts/fleet_comms/pg_schema.py`'s v3 migration against the real
   production Postgres DSN (`apply_pg_schema` is idempotent — safe to run
   any time; it happens automatically on the next non-readonly
   `ArtifactStore` open once code from this PR is deployed).
2. Provision `/etc/hramatka/v4-signing-keys/{fleet_execution,sources,a3}.key`
   + `.key_id`, root-owned, on the Hramatka host running the real
   attester/A3/Sources-server processes. Register the matching public keys
   under a new versioned trust-policy file, add its byte digest to
   `PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST`, land that in a
   code-reviewed PR.
3. Wire a real V4 dispatch caller to call `RequestExecutor.record_v4_
   execution_observation` after confirming a genuine terminal author/
   reviewer execution, and wire the Sources MCP client side to pass the
   `_v4_evidence_*` opt-in bundle when gathering real evidence.
4. Only then: generate real task/run/invocation IDs from actual executions,
   issue real receipts, and claim the first nonzero A7 completion after
   private replay and exact-head cross-family review.

## Residual scope (disclosed, not a trust-boundary gap)

- The Sources MCP wire handler's evidentiary recording only activates for
  the small, explicit `_V4_SANCTIONED_VERIFIER_TOOLS` allowlist (the
  `verify_*`/`check_*`/`vet_vocabulary` identifier-verification tools) —
  free-text search tools are not wired, since their result shape can't be
  meaningfully policed by the substring-presence check. Extending coverage
  to more tools is additive follow-up work, not a repair-6 blocker.
- `trust_policy_sha256` is bound inside every directly-signed payload (see
  §4) rather than duplicated as a second plaintext field on every A7/A8/A9
  downstream wrapper receipt — those receipts' own integrity/replay checks
  already re-verify the embedded signed artifacts in full.

## Verification (this repair, exact head)

```
.venv/bin/python -m pytest tests/projects/open_model_data/ -q
# 732 passed

.venv/bin/python -m pytest tests/fleet_comms/ -q
# 43 passed, 28 skipped (pg-authority tests skip without a live DSN)

.venv/bin/python -m pytest tests/test_mcp_sources_server.py tests/test_mcp_sources_privacy_logging.py tests/test_mcp_sources_identity_integration.py tests/test_mcp_sources_streamable_http.py -q
# 84 passed, 11 skipped
```

Bounded aggregate proof against the real checked-in production receipts
(no private inputs, no test fixtures):

```python
a7.validate_receipt_independently(a7_receipt, ROOT)   # a7_completions = 0
a8.validate_receipt_independently(a8_receipt, ROOT)   # a8_completions = 0
a9.validate_receipt_independently(a9_receipt, ROOT)   # a9_completions = 0, a9_residuals = 100
# A13 status: A13_CLEANUP_RECOVERY_WIRED_TEXT_FREE_NO_STRONGER_RELEASE_STATE_CLAIM
```
