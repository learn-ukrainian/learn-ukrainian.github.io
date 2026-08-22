# Phase 3 Cycle 006 restart amendment v3

Issue: `#6375`

Evaluation cycle: `phase3-v2-1-evaluation-cycle-006`

## Operator-authorized outcome

Certify the frozen Phase 3 correction-protection evaluation by obtaining two
independent labels for every held-out row, resolving every disagreement under
the frozen selector and authorization policy, and proving a final denominator
of exactly 10,159 rows with residual zero.

This restart follows accidental removal of the disposable worktree that held
the first Cycle 006 runtime. It does not authorize a new sample, a denominator
change, label reuse, taxonomy changes, validator changes, or weaker gates.

On 2026-08-21, the operator authorized correction of the ordered identity
commitment after strict source recomputation proved that the v2 value was not
derived from the restored source under the documented algorithm. This v3
amendment supersedes v2 only for that incorrect derived value and its missing
serialization definition. It does not change any source row, identity, order,
count, custody binding, evaluation rule, or completion term.

## Frozen source universe

The sole source is the restored Cycle 005 custody package. Its bindings are:

- custody receipt SHA-256:
  `7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726`
- label manifest SHA-256:
  `b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab`
- ordered lane/packet/row identity commitment:
  `331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419`
- lanes: 40 clean-label packets / 2,000 rows and 164 residual-label
  packets / 8,159 rows
- total: 204 packets / 10,159 rows
- packet size remains 50, except the already-sealed final short packet

The ordered identity commitment is SHA-256 over one canonical UTF-8 JSON array
followed by a single LF byte. The array visits `clean_label` and then
`residual_label`, each with packet indices in ascending one-based order and
rows in their unchanged packet order. Each row is represented as exactly
`[lane, packet_index, row_index, unit_id, unit_sha256]`, where `row_index` is
zero-based. Canonical JSON uses `ensure_ascii=False`, sorted object keys, and
the separators `(",", ":")`. Recomputing that exact stream from the restored
Cycle 005 package yields the frozen value above for 204 packets and 10,159
unique identities. The superseded v2 value
`a5e122efd27678cea5e819764c2c751152f54f5dfcc002455c0270fc396ed05f`
had no source derivation and is not accepted by v3 tooling.

Materialization must preserve lane order, packet order, row order, unit ID,
unit SHA-256, and all source-bearing row fields byte-for-value. The only row
field that may change is `evaluation_cycle_id`, from Cycle 005 to Cycle 006.
Packet and manifest hashes are recomputed for Cycle 006. No Cycle 005 provider
output, label, response, raw capture, adjudication, or resolution is copied.

## Identity-bound Gemini response

Each Gemini provider chunk remains at the frozen maximum of 20 rows. A normal
50-row packet is split 20/20/10; the already-sealed final 9-row packet remains
a single 9-row chunk. No chunk is padded, dropped, or moved. The Gemini response
schema is an object named `labels_by_position` with exactly the ordinal keys
`p01` through `pNN`, `additionalProperties: false`, and one label object per
key. Each ordinal's `unit_id` and `unit_sha256` fields are bound before the call
by single-value enums for that exact source row. Normalization visits the
ordinals in numeric order and emits the unchanged validator envelope
`{"labels":[...]}`. The unchanged Cycle 005 semantic validator then runs on
that normalized value and on the fully reassembled packet.

The private chunk and composed prompt are passed only through a mode-0600
stdin file inside a mode-0700 runtime directory. They never appear in argv,
stdout, controller receipts, terminal markers, provider stops, or public logs.
The runtime directory and stdin file are removed in `finally`.

## Bound Grok response

Grok remains the independent second first-pass labeler and uses the unchanged
Cycle 005 `{"labels":[...]}` response contract. Its schema fixes the exact
label count for the selected packet and the allowed label fields/enums. The
runner then applies the unchanged validator to require the exact source
`unit_id` / `unit_sha256` sequence, identity uniqueness, lane invariants, and
all frozen residual taxonomy, rollup, sufficiency, and 2019-negative-control
rules. Any count, envelope, identity, order, uniqueness, or semantic drift is
terminal; it is never repaired or accepted by the controller.

The complete Grok prompt and private packet are written to a mode-0600 stdin
file within a mode-0700 runtime directory and delivered through stdin only.
They never appear in argv, stdout, controller receipts, terminal markers,
provider stops, or public logs, and the runtime directory is removed in
`finally`. Resumption accepts only an immutable labels/receipt/raw-manifest
triple whose hashes, source packet binding, exact model, family, harness,
cycle, lane, packet index, row count, and identity commitment all verify.

## Retry and stop policy

One structural retry is permitted only when attempt 1 has no extractable,
schema-valid result. A schema-valid result that fails identity or semantic
validation is terminal and receives no second provider call. Provider nonzero,
execution failure, package/prompt binding drift, identity drift, partial seals,
attempt ceiling, or a pre-existing provider stop are terminal. The first stop
is written atomically and blocks all later paid or adjudication stages.

Every text-free terminal attempt marker carries one `failure_code` from this
exact closed set of 18 values:

1. `stream_json_invalid`
2. `terminal_result_count_drift`
3. `structured_output_envelope_drift`
4. `ordinal_key_drift`
5. `ordinal_identity_binding_drift`
6. `label_json_invalid`
7. `label_count_or_envelope_drift`
8. `identity_or_order_drift`
9. `identity_uniqueness_drift`
10. `clean_label_schema_drift`
11. `clean_label_invariant_drift`
12. `residual_label_schema_drift`
13. `residual_phenomenon_drift`
14. `residual_scored_decision_insufficiency`
15. `residual_2019_positive_forbidden`
16. `residual_taxonomy_order_or_uniqueness_drift`
17. `residual_primary_or_rollup_drift`
18. `residual_null_rollup_drift`

Unknown failures are coerced to the closest closed transport/binding failure;
exception text and private values are never persisted.

## Custody and durability

Private held-out data and provider outputs stay local. VPS workers may receive
only public code, synthetic fixtures, tests, and review briefs. The live Cycle
006 package must be placed outside disposable Git worktrees under a mode-0700
operator-owned runtime root. Before the first private provider call, the
materialized package, public code hashes, reviews, and preflight receipt must
have a fresh hash-verified Google Drive backup. Runtime seals are resumable and
must be backed up incrementally without exposing packet or label contents.

## Roles and independence

- Accountable root: scope, sequence, text-free monitoring, integration, and
  final disposition; it does not inspect private packet or provider bodies.
- Ukrainian source-authority reviewer: verifies preservation of the frozen
  source and linguistic/evaluation contract.
- Independent scope/circularity reviewer: verifies no reroll, leakage, reuse,
  denominator drift, or circular adjudication.
- Implementation authors: public tooling and synthetic proofs only.
- Independent cross-family reviewer: exact-byte pre-call review of all paid
  execution modules and proofs.
- Gemini and Grok: independent first-pass labelers.
- Fresh selector adjudicator: sees only bound dual-label candidates for
  disagreements and cannot author arbitrary third labels.
- Operator or designated advisor: resolves only explicitly emitted unresolved
  requests, selecting an existing authorized candidate.

## Pre-call gates

No private provider call is allowed until all are true:

1. This amendment's SHA-256 is frozen.
2. Source-authority and independent scope/circularity reviews approve this
   exact amendment.
3. Materialization proves exactly 204 packets / 10,159 rows, unchanged ordered
   identity commitment, no copied provider artifacts, mode 0700/0600 custody,
   and transactional rollback.
4. Synthetic proofs cover every closed failure-code family, identity omission,
   substitution, duplication and reordering, structural retry success,
   semantic no-retry, provider-stop idempotence, partial seal refusal, runtime
   cleanup, and private-value absence from argv/stdout/receipts.
5. An exact-byte independent cross-family review approves the materializer,
   Gemini runner, controller, tests, and public canary.
6. A public-only 20-position canary succeeds with exact positional binding.
7. A text-free preflight binds all reviewed hashes and the fresh durable backup
   receipt.

## Completion terms

Certification requires all 204 packets and all 10,159 rows to have two valid,
independently sealed first-pass labels; deterministic comparison over the full
denominator; fresh selector adjudication for every disagreement; authorized
candidate-only resolution for every emitted unresolved request; zero missing,
invalid, partial, duplicate, unbound, or unresolved rows; zero active provider
runtime directories; no provider stop; and final text-free receipts that bind
the exact code, manifests, reviews, outputs, denominator, and residual zero.

No merge, publication, training-data release, threshold change, or policy
change is authorized by this amendment.
