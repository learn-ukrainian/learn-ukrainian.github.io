# V4 real-slot mechanism: packaged parent execution

PR #7662 preserves the A3 seal and frozen public receipts while moving current
execution into `learn_ukrainian_v4_runtime`. The existing protected API parent
owns process launch, capture, parsing, artifact writes and terminalization.

Frozen outcome:
`78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20`.
Controls #7423 and pilot #7430 are unchanged. Default public output remains
**0 completed / 100 residual / 0 emitted; A13 open**.

This is a source-free merge mechanism. Actual protected-unit qualification,
private API integration, deployment and admission enablement belong to A0's
later controlled integration work.

## Package and historical identity

The canonical package lives in `packages/v4-runtime`. Repository scripts adapt
to its modules; they require the declared package dependency. Build/test commands
are in the [package README](../../../packages/v4-runtime/README.md).

The approved fixed resource layout is:

- `provenance/v1/manifest.json`: complete receipt-binding occurrences and their
  raw receipt digests, historical paths/schemas/digests, current successors,
  package version, public commit and relationship.
- `provenance/v1/blobs/sha256/<sealed-sha>.blob`: seventeen exact historical
  implementations, read only for hashing.
- `release_manifest.json`: current product file digests, including the explicit
  data resources, license, empty trust policy and fixed rubric.
- `_build_identity.py`: reproducible byte data binding the actual build commit,
  version, release digest and provenance digest.

The A3 seal digest remains
`d3147b0201d0f358677825ea6700e3e3e81b7e2fad551fe6c4e7b174d402f860`.
Its creator implementation remains
`0691c83969b2312f01f111d2eac98fa6aadb5daa9ce059b7750ca28faf52359d`;
its binding context remains
`1c0d736aa729ba7836ce3b5732a1ef7b3a9fdba71455a30185b76f1c24e3dd0a`.
The current A3 descriptor must reproduce
`b2abbb8e45f60abb098b8976dec7e7f2b4668137f55bfab8eee3999bd65a1928`.

The relationship is `runtime_successor_validating_frozen_receipt`. Current
execution does not claim to execute historical source or to be byte-equivalent
to its creator. Membership, packets and downstream frozen public receipts are
not resealed or rewritten. The strict repository validator still rejects
relocated current code against the original sealed pin.

The package validator reads only fixed built-in resources. It validates the
entire manifest and binding set, rejects unknown/duplicate/missing/extra
mappings and unsafe paths, hashes historical and current resources, and checks
the frozen A3 context and descriptor before private operations.

## Private integration interface

`V4ServiceRuntime(store=..., verifier=..., release_provider=...)` exposes two
route methods:

| Method | Exact canonical UTF-8 body |
| --- | --- |
| `authorize(raw_body, oidc_token=..., github_bearer=...)` | `{"schema":"hramatka-v4-operation-authorize.v1"}` |
| `execute(raw_body, oidc_token=..., github_bearer=...)` | `{"authorization_id":"<43-character opaque id>","schema":"hramatka-v4-operation-execute.v1"}` |

Bodies are at most 1 KiB. Duplicates, extra fields and noncanonical encodings
refuse. Bodies cannot choose a target, role, seat, model, packet, row, rubric,
policy, executable or runtime observation. Authorization selects an already
prepared canonical assignment internally.

The trusted `ActionsVerifier.authenticate` returns `ActionsPrincipal` with:
`repository_id`, `workflow_ref`, `ref`, `subject`, `workflow_sha256`, `run_id`,
`run_attempt`, `check_run_id`, `runner_id`, `runner_group_id`, `runner_label`,
`authz_policy_sha256`, and `jti`. Numeric identifiers must be positive integers;
digests must be lowercase SHA-256. Ownership includes every field except the
one-use JTI. The separate private verifier must perform the approved fresh
OIDC and authoritative GitHub checks. Teacher/review authentication is not a
substitute. Binding this interface to the existing private component remains
A0's integration work.

`VerifiedReleaseProvider.verify(installed_identity)` must run the existing
private vendor verification and return the same current identity plus:

- `wheel_sha256`: digest of the externally verified wheel;
- `wheel_files`: complete wheel file digest map, including distribution metadata.

Current identity includes the full public commit, package version, release and
provenance manifest digests, and the complete installed runtime file digest map.
Opaque author/reviewer receipts bind this outer current identity. It is never
added to the old A3 binding context. The private startup adapter must verify the
vendor/installed chain before importing and exposing the runtime. Public
self-consistency checks do not establish that external anchor.

## Canonical preparation and execution

The existing trusted preparation owner resolves the admitted expression-free
author constraints and fixed assignment. `freeze_semantic_input` records an
immutable snapshot before authorization. Constraints contain only the task
kind, CEFR level, required field names and sanctioned evidence tool names.

Reviewer preparation resolves a verified authorship receipt, the complete row
from the parent's stored capture, the author's constraints and the fixed rubric.
A matching row-text hash alone is insufficient: every authored field and the
constraint set must agree with their canonical origin.

`OperationStore` requires the control role on the canonical Fleet PostgreSQL
connection. Authorization is bounded by the request expiry and five minutes.
Claiming atomically consumes a fresh JTI, binds the exact owner and request,
creates a Sources capability and sets the canonical 1800-second execution
deadline. Request, authorization and attempt identities/deadlines must agree.
Freshness is rechecked using the database clock after ownership locks are held.

The parent builds the fixed bwrap plan after capability creation. The child gets
an empty filesystem with only pinned runtime files, an isolated PID/proc view,
its selected provider credential and Sources-only configuration. Claude carries
the Sources URL and the literal `Bearer ${V4_SOURCES_ATTEMPT_CAPABILITY}`
placeholder in its MCP argv; the installed CLI expands that placeholder from
the child-only environment at request time. The actual capability is never in
argv, the prompt or normal logs. Codex carries its isolated Sources
configuration in argv, the capability in its designated environment variable,
and the prompt on stdin. The fixture’s placeholder check is not an installed
Claude compatibility proof; validate the installed config path separately with
a source-free, no-provider CLI probe. Unqualified adapters or missing actual
model/session/terminal evidence refuse.

The same parent captures and parses the child output. It checks request/attempt
correlation before artifacts or observations are written, rechecks ownership,
expiry, policy and release identity, and terminalizes in the canonical
transaction. The legacy runner's PG claim and caller-fact finalization paths
are retired. Generic message-plane capture remains non-authoritative for V4.

## Sources and scoped privileges

The schema includes `v4_operation_authorizations`, `v4_operation_jtis`, attempt
deadlines and immutable semantic snapshots. The existing migration owner applies
PG schema version 6 during controlled deployment; this task does not apply it to
a live database.

| Principal | Authority |
| --- | --- |
| `hramatka_v4_control_writer` | Canonical control DML and Sources observation reads; no Sources invocation insert/execute authority |
| `hramatka_v4_sources_writer` | EXECUTE on the fixed Sources stored operation; no direct V4 table DML |
| Generic Fleet/worker roles | No V4 table grants or signing credentials |

The Sources stored operation locks the attempt, checks request/authorization
ownership and expiry, assigns the invocation identity and ordinal, and records
the typed result. Its lock ordering is tested against terminalization in both
orders using independent PG connections and observed database lock waits.

Sanctioned tools are `verify_word`, `verify_words`, `verify_lemma`,
`verify_stress` and `check_modern_form`. Evidence identifiers bind the actual
lexical supporting records and a known source/tool version. Invalid input,
not-found, ambiguous, negative and partial results remain unsuccessful.
Ordinary unauthenticated Sources traffic creates no V4 evidence; a presented
invalid or expired capability refuses. There are no shared MCP configuration
edits or unrelated child MCPs.

Opaque Sources issuance joins a successful invocation to its actual terminal
author observation. Execution and Sources issuers check that the execution's
captured policy is still active before accessing signing keys.

## Policy, custody and switches

Both `HRAMATKA_V4_EXECUTION_ENABLED` and `HRAMATKA_V4_ADMISSION_ENABLED` default
to OFF. Admission construction requires the admission switch and active keys.
The shipped trust policy remains empty. A7–A13 validation, positive construction,
aggregation and replay resolve the fixed active policy. Current positive
records require matching top-level and completion policy bindings. Frozen empty
receipts retain their original bytes and absence of the newer field.

The current schema envelope adds only the policy digest; sealed schema resource
bytes remain preserved. Existing shape and semantic checks remain active.
Unsigned synthetic replay evidence and unresolved opaque authority IDs refuse.
Signed text-free A3 replay attestation remains the approved alternative to a raw
reference callback.

Fixed credential locations use the existing private systemd credential
namespaces: control DSN, selected provider credential, actual-unit
qualification and `v4-signing-keys/{fleet_execution,sources,a3}.key` plus
`.key_id` under the API unit; Sources has its separate scoped DSN under its own
unit. The public
`packaging/systemd/learn-ukrainian-sources.service` intentionally supplies no
deployment-specific OS account or credential path. Before a private deployment
enables it, an existing private drop-in must set the protected service account
and group, the Sources DSN `LoadCredential` binding, and the
`InaccessiblePaths` entries for the API credential namespace and signing-key
root. Those bindings are private deployment obligations, not public-template
defaults. No new service, OS account, general writer or key-custody plane is
introduced.

Readiness also requires package integrity, a pinned child profile, actual-unit
qualification and scoped credentials. The shipped child profile is unqualified.
No production canary or enablement is implied by an isolated bwrap test.

## Evidence and remaining ownership

The tests distinguish unmodified release-wheel proofs from coherent synthetic
trust-resource fixtures. Synthetic wheels are visibly marked as fixtures and
are never deployment evidence. Resource/key fixtures do not replace the parent
runner, parser, finalizer, authentication implementation or canonical observation
writer. Public mechanism tests below the private authentication adapter do not
claim end-to-end private authentication qualification.

Source-free checks cover frozen provenance and fixed-salt invariance, manifest
and resource tampering, parent-owned process capture, input-consuming valid and
structurally defective cases, real Sources HTTP, scoped PG roles/interleavings,
opaque issuance and private replay. Exact commands, elapsed times and final
results are reported with delivery; task logs and build artifacts are not product
files and are not committed.

The minimal shared helper closure preserves the existing family-resolution,
agent-identity, transport-contract and PG-schema behavior needed by runtime
attesters. Repository `model_families`/`agent_identity` adapters share those
canonical definitions; reviewer resolution and thread handoff import only the
required family/known-harness helpers. Inventory orchestration stays in its
original module; the package shares only the required source-type constant.

A0 owns independent cross-family review at the exact head, required same-head CI,
merge and worktree cleanup, then private endpoint/PG/vendor binding, actual-unit
canaries and the first real row/full epic. There is no claim of completed private
API deployment, live grants/migrations, provider execution or admission
turn-on in this public change.
