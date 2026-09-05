# V4 real-slot mechanism — runbook (native-runner origin)

PR #7662 repair 8. Designated-advisor Sol GO_REPAIR after repair 7 failed
exact-head review: `RequestExecutor.execute_capture` ingests caller captures
and is **not** a V4 execution authority. The only production origin is
`scripts.agent_runtime.runner._execute_invocation_plan` after actual
InvocationPlan isolation, argv resolution, Popen, stream capture, and parse.

Frozen epic outcome SHA-256
`78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20`.
Controls #7423 / pilot #7430. Mechanism only: **0 completed / 100 residual /
0 emitted**, A13 open. No production keys, live PG migrations, corpus, or
first-real-row deployment.

This runbook describes what is **implemented and tested at this head**.
Residuals are listed as residuals. There is no claim that every
trust-boundary gap is closed.

## What repair 8 changes

Repair 6/7 built the canonical Fleet Comms store, opaque-ID issuers, and
Hramatka key custody. Those remain. Repair 8 moves the **writer**:

1. V4 observation writing is removed from `execute_capture` /
   `_finalize_capture`. Generic message-plane capture may remain; it is
   non-authoritative for V4.
2. The native runner accepts an opaque authorization id, resolves the
   authorized prompt internally, atomically claims the exact binding
   immediately before Popen, injects a one-attempt Sources capability, and
   finalizes from that process's actual transported prompt, post-isolation
   argv/executable, stdout/stderr/output artifacts, terminal rc, and parsed
   row or verdict.
3. Authorization is role-specific: `authorize_author_execution(request_id,
   slot_id, expected_seat)` and `authorize_reviewer_execution(request_id,
   authorship_receipt_id, expected_seat)`. No caller row/packet/rubric/
   content hash. Blindness is derived from the validated source-blind prompt
   profile plus the exact transported digest.
4. Sources recording uses existing MCP HTTP Bearer auth. Caller
   `_v4_evidence_*` arguments are discarded. Typed handler outcomes drive
   success and `vesum:`/`sources:` identifiers. Mixed/shadow tools stay
   excluded until they have a typed supporting-claim contract.
5. Production wrappers load `load_production_trust_policy()` internally.
   There is no caller policy argument and no synthetic production toggle.
   Isolated test-policy seams cannot serve production admission.

## 1. Canonical authority store

Tables on the existing Fleet Comms plane (pg in production, sqlite under
the default dev/test authority):

| Table | Key | Written by |
| --- | --- | --- |
| `v4_execution_dispatch_bindings` | `request_id`, unique on `(task_id, run_id, role)` | `authorize_author_execution` / `authorize_reviewer_execution`, while the request is still `queued` |
| `v4_execution_attempts` | `attempt_id` | `claim_v4_runner_execution`, atomically with `queued → running`. Stores only the capability **digest**. |
| `v4_execution_observations` | `(task_id, run_id, role)` | `RequestExecutor.finalize_v4_runner_execution`, called only from the native runner |
| `v4_sources_invocations` | `invocation_id` | Sources MCP HTTP handler via `record_v4_sources_invocation_from_typed_outcome`, joined to a running attempt |
| `v4_authorship_receipts` | `receipt_id` | `persist_v4_authorship_receipt`, so reviewer authorization can resolve an opaque id |

**No public function accepts a caller-built execution observation or
Sources record.** `execute_capture` does not write V4 observations even
when the caller supplies a well-formed capture.

Migrations: `scripts/fleet_comms/pg_schema.py` v5,
`scripts/fleet_comms/migrations.py` v10.

## 2. Native-runner origin

`scripts.agent_runtime.runner.invoke(..., v4_authorization_id=...)`:

1. Resolves the authorized source-blind prompt from the frozen binding
   (`resolve_authorized_prompt`) and uses those bytes as the InvocationPlan
   prompt. The caller's prompt argument is not transported.
2. After final isolation/argv resolution, `claim_v4_runner_execution`
   requires the exact binding and `queued → running`, and mints a
   one-attempt capability. PostgreSQL locks the request row `FOR UPDATE`;
   SQLite uses `BEGIN IMMEDIATE` with the same inside-transaction recheck.
3. The capability is placed in the child environment
   (`V4_SOURCES_ATTEMPT_CAPABILITY`) and stamped onto the existing MCP HTTP
   config (`headers.Authorization` / `bearer_token_env_var`). The plaintext
   token is never stored.
4. After parse (and on failure in `finally`), `_finalize_v4_runner_origin`
   derives one observation from that process. Absent actual-model/session
   telemetry refuses rather than defaulting the requested identity.

Author `row_content_sha256` comes from the structured `V4-AUTHOR-ROW`
output. Reviewer verdict comes from `V4-REVIEW-VERDICT: PASS|FAIL`.
`verification_tool_ids` are resolved by **attempt id**, not request-only
correlation.

## 3. Role-specific authorization

`authorize_author_execution` loads the frozen public slot and A3 packet
receipt, builds `v4-author-source-blind-v1`, and records the prompt digest.
It does not accept a row hash.

`authorize_reviewer_execution` resolves the authorship receipt and the
fixed rubric (`data/projects/open_model_data/trust/v4_review_rubric_v1.txt`)
internally and builds `v4-reviewer-source-blind-v1`.

Blindness flags are the result of `blindness_from_prompt_profile`: the
profile must be one of the two source-blind profiles and the transported
digest must equal the authorized digest. They are not independently
hard-coded `False` on a caller-ingest path.

## 4. Sources typed recording

`.mcp/servers/sources/server.py`:

- `_v4_evidence_*` keys are popped and ignored.
- HTTP middleware resolves `Authorization: Bearer` to a running attempt.
  Missing Authorization is ordinary curriculum traffic (no V4 recording).
  Unknown, foreign, stale, or terminal tokens fail closed (401).
- Sanctioned handlers (`verify_word`, `verify_words`, `verify_lemma`,
  `verify_stress`, `check_modern_form`) return `(prose, typed_outcome)`.
  `CallToolResult.structured_content` carries the typed outcome.
- `success` is true only for disposition `supported` with server-derived
  `vesum:`/`sources:` identifiers. Invalid input, not found, ambiguous,
  negative, and partial lists are `success=false`. `vet_vocabulary` and
  `check_russian_shadow` are Sol-approved exclusions from positive V4
  evidence until they have a typed supporting-claim contract.
- `issue_verifier_attestation(invocation_id=...)` joins the invocation to
  the terminal **author** observation for the row hash. There is no caller
  row-hash argument.

## 5. Fixed production policy resolver

`load_production_trust_policy()` takes no arguments. Production wrappers
(`construct_completion`, `verify_private_replay`, `build_authorship_receipt`,
`build_review_receipt`, `build_verifier_receipt`, `build_evidence_receipt`,
and their integrity validators) load it internally. `trust_policy_sha256`
is bound through signed bodies, authorship/review receipts, private and
public A7 completions, and A8 completions when present.

The checked-in production policy file is empty. Its digest stays on the
allowlist; an empty keyring refuses every production-capable receipt.
Test-only policy seams (`installed_fixture_policy`, monkeypatched loaders)
cannot serve production admission. Key revocation / allowlist removal
invalidates a previous chain.

Crypto helpers (`verify_author_execution_receipt`,
`verify_reviewer_execution_receipt`, `verify_verifier_attestation`) still
take an explicit `trust_policy` because they are verification engines, not
production admission wrappers.

## Residuals (honest)

1. **No production keys, no live DSN, no first real row.** Mechanism-only.
   The first-real-row PR owns provisioning, live migration, and a real
   author/reviewer exercise. Required executable-writer integration is
   **not** deferred there — it is in this PR and tested against fixture
   executables/backends at the lowest IO edge.
2. **Adapters without structured actual-model/session telemetry are
   ineligible.** The runner refuses rather than defaulting requested
   identity. Widening that set is separate work.
3. **Reviewer verdict requires a cooperating reviewer prompt.** The
   source-blind profile instructs `V4-REVIEW-VERDICT: PASS|FAIL`. A
   reviewer that never emits the marker produces no observation.
4. **Only harnesses in `KNOWN_HARNESS_EXECUTABLES` can be authorized.**
5. **PostgreSQL dialect is exercised by an owned ephemeral UTF-8 cluster
   in the two-connection race test**, not against a live production DSN.
   Applying v5 to the real Fleet Comms DSN remains a deploy step.
6. **Signed text-free A3 replay remains the approved alternative to a raw
   callback.** A3 packet/reference-check authenticity is unchanged.
7. **Root-owned caller-inaccessible signing under the existing service
   account**, with operator rotation/revocation, remains approved and
   unimplemented at this head (no key files are provisioned).

## First-real-row prerequisites (out of scope)

1. Apply `pg_schema.py` v5 against the real Fleet Comms PostgreSQL DSN as
   part of the same deploy step that ships this code.
2. Provision `/etc/hramatka/v4-signing-keys/{fleet_execution,sources,a3}.key`
   + `.key_id`, register public keys in a new versioned trust-policy file,
   and add its digest to `PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST`.
3. Wire the real V4 dispatch caller to `authorize_author_execution` /
   `authorize_reviewer_execution` and `runner.invoke(...,
   v4_authorization_id=...)`. Do not call `execute_capture` as a V4 origin.
   Do not pass `_v4_evidence_*` correlation arguments.
4. Only then: generate real task/run/invocation IDs from actual executions
   and claim the first nonzero A7 completion after private replay and
   exact-head cross-family review.

## Verification (this head)

See the PR body for the exact commands and recorded results. Progress
criterion: one boundary-to-boundary positive source-free path (service
authorize/claim → real runner → real Sources HTTP on a typed fixture
backend → runner-owned observation → opaque issuers → construct/replay
→ A7/A8) plus the six accepted P1 adversarial repros. Fixtures substitute
executable, VESUM backend, and custody roots at the lowest IO edge. They
do not insert canonical observation rows, fake terminal observations,
replace the runtime writer/authorization/resolvers, or add a test-only
admission bypass.
