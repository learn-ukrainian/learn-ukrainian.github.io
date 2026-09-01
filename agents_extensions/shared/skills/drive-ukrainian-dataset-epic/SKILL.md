---
name: drive-ukrainian-dataset-epic
description: Drive the frozen V4 Ukrainian dataset-delivery epic from source intake through a reproducible silver dataset and its gold-upgrade path, with live routing, held-out custody, rights boundaries, and VPS capacity control.
---

# Drive the Ukrainian dataset epic

This is the dataset-specific layer over `$drive-epic`. Load `$drive-epic` first and
follow its orient → route → dispatch → settle → cross-family review → merge →
handoff loop. This skill supplies the V4 contract, role boundaries, data states,
and capacity gates; it does not replace the generic routing, worktree, review,
or merge rules.

## Launch binding

The generic launcher injects only `$drive-epic`. At launch, explicitly load this
skill as well. The driver is accountable for the whole epic: issue disposition,
sequencing, integration, evidence, resource safety, and final residuals. It is
not a passive relay waiting for one model or one human.

The controlling V4 identity is:

```text
outcome_sha256 = 78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20
public_control_issue = #7423
private_operational_board = #622
```

Read the latest hash-bound contract, comments, linked receipts, and native issue
dependencies from both control surfaces. The public issue is the user-facing
charter; the private board carries operational detail. Stale predecessor text is
historical evidence and never silently overrides this identity. If the two
surfaces disagree or one cannot be read, record the discrepancy as unknown and
resolve it before dispatching work that depends on the disputed field.

## Frozen V4 scope

The dataset teaches and evaluates Ukrainian usage while preserving legitimate
variation and historical material. Its fixed pilot denominator is 100 rows:

| Pilot stratum | Slots | Required treatment |
| --- | ---: | --- |
| Standard-correct modern Ukrainian | 15 | Preserve as a positive production control. |
| Modern correction | 15 | Correct only an independently supported modern Ukrainian error/interference. |
| Literary Ukrainian | 15 | Preserve literary register, authorial voice, and context. |
| Dialect or regional Ukrainian | 15 | Preserve the variety, region, and register; do not treat it as an error by default. |
| Archaic or historical Ukrainian | 15 | Preserve period and source form; never modernize automatically. |
| Surzhyk / Ukrainian–Russian contact mixing | 10 | Model contact composition separately from language identity. |
| Russian quotation or interference in Ukrainian context | 10 | Classify the context and span; do not turn this into a general Russian corpus. |
| Abstention / insufficient evidence | 5 | Keep ambiguous or unsupported cases explicit and non-forced. |

The slots sum to 100 and are frozen for this V4 pilot. Do not borrow slots
between strata, add a new language program, or make a coverage gap disappear by
renaming it `not_applicable`.

Dedicated non-Ukrainian Slavic programs are out of scope. Modern Rusyn is not a
target class: a source-attested Rusyn span remains protected or unresolved and
is never silently mapped to a Ukrainian dialect, Russian, or a historical
successor. Historical, archaic, literary, dialectal, quoted, named,
transliterated, and metalinguistic material is not automatically a modern
correction. Script alone never establishes language identity.

The following are also out of scope for this epic: model training or preference
optimization, a general knowledge corpus, claims about model performance,
automatic modernization, source-text publication beyond the admitted rights,
and promotion of model agreement to truth.

## Slot, row, and case identity

Public pilot slot IDs are a source-free stable series, with one source-free
series per frozen stratum. The canonical frozen public-slot manifest is
`data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json`
(`schema_version: dataset_v4_pilot_slot_manifest_v1`). Generate public pilot
slot IDs from its eight `slot_series` entries only: each ID is the manifest's
source-free `id_prefix` followed by its three-digit, zero-padded ordinal,
starting at `start=1`. The frozen series are:

| Manifest stratum | `id_prefix` | Start | Count | Generated range |
| --- | --- | ---: | ---: | --- |
| `standard_correct` | `v4p-standard-correct` | 1 | 15 | `v4p-standard-correct-001` … `v4p-standard-correct-015` |
| `correction` | `v4p-correction` | 1 | 15 | `v4p-correction-001` … `v4p-correction-015` |
| `literary` | `v4p-literary` | 1 | 15 | `v4p-literary-001` … `v4p-literary-015` |
| `dialect_regional` | `v4p-dialect-regional` | 1 | 15 | `v4p-dialect-regional-001` … `v4p-dialect-regional-015` |
| `archaic_historical` | `v4p-archaic-historical` | 1 | 15 | `v4p-archaic-historical-001` … `v4p-archaic-historical-015` |
| `mixing` | `v4p-mixing` | 1 | 10 | `v4p-mixing-001` … `v4p-mixing-010` |
| `quotation_interference` | `v4p-quotation-interference` | 1 | 10 | `v4p-quotation-interference-001` … `v4p-quotation-interference-010` |
| `abstention` | `v4p-abstention` | 1 | 5 | `v4p-abstention-001` … `v4p-abstention-005` |

These are source-free stable per-stratum series: the prefix is the frozen
manifest stratum label, not a source, text, model, provider, arrival order, or
derived label. Do not invent a global series or substitute a different prefix;
slot IDs stay stable while a slot is unresolved or carries a residual.

After a slot is admitted, derived row and case IDs may bind sources later.
Derive each opaque ID from the V4 version, its public slot ID, source-unit
identity/hash, evidence/span locator, rule or case key, and role. Keep the
lineage from every derived row/case back to its source-free slot. Never derive
an ID from provider order, model output, arrival time, file position, or a
mutable sentence number. A source or case may have multiple role-specific
records, but their lineage must remain explicit.

Use append-only overlays:

- **Silver** is a reproducible, schema-valid, source-traceable row whose
  uncertainty and review state are explicit. It may be produced without a human
  decision when the deterministic source, operation rights, provenance, split,
  and structural checks pass. Silver does not require universal human and model
  agreement. Human review is optional for silver and improves evidence; a model
  hypothesis, proposal, vote, confidence, or agreement cannot independently
  admit a row to silver.
- **Gold** is an overlay on the same stable row ID, not a rewrite of silver. It
  requires a source-qualified human adjudication tied to claim-appropriate cited
  evidence, an adjudication receipt, and independent rights, split, provenance,
  lineage, view, and execution-authorization gates. Gold fields are additive and
  auditable; the silver record remains recoverable.

Model proposals, votes, rationales, and unresolved decisions are separate from
both target layers. Exact agreement is recorded as
`MODEL_AGREEMENT_QUARANTINED_NOT_GOLD`; hypotheses, agreement, majority,
confidence, or attestation can never independently make a row gold. A silver
row must not be called a gold target or used to claim a stronger release state.
Model hypotheses cannot independently admit silver or make gold.

## Functional ownership

The driver assigns these functions in the issue packet and records the live
route and evidence for each assignment. A model or harness label is not a role
identity, and stable skill text must not hard-code one. The same person may hold
several human functions only with a disclosed temporal/visibility firewall; that
does not create institutional independence.

| Function | Owns | Must not do |
| --- | --- | --- |
| Accountable epic driver | Scope, queue, dependency order, integration, readiness, capacity, residuals, and final disposition. | Hide a gap behind a status word, shrink the denominator, or make an unrecorded route choice. |
| Source-admission steward | Source inventory, immutable unit IDs/hashes, acquisition evidence, source dispositions, and later-addition policy. | Infer a licence or permission from official availability, or publish protected source text. |
| Rights-capability steward | Per-source, per-operation capability ledger and evidence locator. | Treat rights as one global yes/no gate or attempt an unknown operation. |
| Custody/split steward | Source-identity groups, near-duplicate policy, held-out membership, temporal firewall, and access controls. | Expose held-out text, labels, locators, fingerprints, or neighbours to builders. |
| Identity lead | Language identity, variety, period, region, register, contact composition, context role, and protection state. | Use script as identity proof or convert protected variation to an error. |
| Independent dissent reviewer | A label-blind, author-blind second view of identity and protection decisions. | See the first proposal, builder output, prestige/order, or held-out material before recording dissent. |
| Locked-dispute critic | A bounded review of exact disagreements and evidence sufficiency. | Vote on its own proposal or resolve an evidence gap by majority. |
| Candidate builder | Deterministic case/row construction after the identity join, with provenance and split checks. | Author gold, inspect held-out material, or silently rewrite source surfaces. |
| Optional silver reviewer | Structural and linguistic quality review of silver rows, with findings attached to stable IDs. | Turn an optional review into a gold claim or delete unresolved rows. |
| Source-qualified gold adjudicator | Human evidence-bound adjudication for a specific atomic claim and cited source. | Adjudicate without qualification/evidence, approve its own proposal, or generalize one decision to a class. |
| Capacity/custody operator | Remote data residency, byte/inode inventory, high-water forecast, reserve, and safe temporary-output retention. | Copy the corpus to the Mac, launch past measured capacity, or delete source data as a shortcut. |
| Held-out evaluator | Independent evaluation of the frozen withheld partition and leakage/integrity checks. | Reveal held-out membership or labels to a builder or reuse construction derivatives. |
| Consumer reproducer | Rebuilds the declared views from the frozen manifest and verifies hashes, row lineage, and eligibility. | Accept a row count or model agreement as reproduction proof. |
| Cross-family PR reviewer | Exact-head independent review of consequential code or skill changes. | Self-review, same-family review, or replace the semantic dataset gate. |

Role ownership is functional even when a lane is substituted. Before each
dispatch, use the live routing rules, catalog, capacity, and health signals
required by `$drive-epic`; record the selected route, alternatives, and reason.
If live routing is unavailable, treat it as unknown and continue only with safe
deterministic work whose route is not material. Never invent an available seat,
quota, health state, or reviewer identity.

## A0–A13 stage ownership

Use this exact ownership map in every issue packet and handoff:

| Stage | Accountable ownership | Boundary |
| --- | --- | --- |
| `A0` | Accountable driver | Epic scope, order, integration, gates, residuals, and disposition. |
| `A1` | VPS custody/capacity | Remote residency, custody controls, byte/inode measurements, and high-water reserve. |
| `A2` | Source inventory/admission/rights by operation | Unit-complete inventory, admission decisions, and the per-operation rights ledger. |
| `A3` | Heldout/source-family split | Source-family grouping, held-out seal, leakage firewall, and access boundary. |
| `A4` | Deterministic extraction | Reproducible source-unit/span extraction with immutable input and output hashes. |
| `A5` | Expression-free evidence enrichment | Evidence metadata and annotations without emitting protected source expressions. |
| `A6` | Blind arena | Label-blind, author-blind proposals and leave-one-out scoring packets. |
| `A7` | Independent original-row factory | Source-derived original rows/cases with independent construction and lineage. |
| `A8` | Admission/assembly | Admitted slice assembly, schema checks, residual attachment, and append-only views. |
| `A9` | Evaluation/scorer/manifest/consumer reproduction | Held-out scoring, manifest/hash checks, and consumer view rebuild. |
| `A10` | Pilot review with independent Ukrainian + exact-head CF gates | Ukrainian-language pilot review plus exact-head cross-family review gates. |
| `A11` | Silver release | Typed silver receipt and release of rows that pass deterministic admission checks. |
| `A12` | Later gold overlays | Source-qualified human adjudication overlays on stable silver row IDs. |
| `A13` | Cleanup | Approved temporary-output cleanup and receipt-backed closeout after disposition. |

There is one accountable lead per stage, and producers and reviewers are
separated. A substituted lane inherits the stage boundary but cannot collapse
the producer/reviewer separation or claim another stage's outcome.

The exact ownership sequence is: A0 accountable driver; A1 VPS custody/capacity;
A2 source inventory/admission/rights by operation; A3 heldout/source-family
split; A4 deterministic extraction; A5 expression-free evidence enrichment; A6
blind arena; A7 independent original-row factory; A8 admission/assembly; A9
evaluation/scorer/manifest/consumer reproduction; A10 pilot review with
independent Ukrainian + exact-head CF gates; A11 silver release; A12 later gold
overlays; A13 cleanup.

## Independence and no-self-vote contract

All identity and case proposals use label-blind packets. Preserve authorship and
ordering metadata for audit, but hide it from independent reviewers until their
own outputs are sealed. For every voting or scoring matrix:

1. The diagonal is forbidden: an agent or human cannot score, vote for, or
   approve its own proposal.
2. A judge does not receive its own prior output as an anonymous candidate.
3. Aggregation counts only leave-one-out views; missing independent views are
   recorded, not filled with a duplicate.
4. Disagreement enters the locked-dispute path and then human adjudication or
   abstention. It is never forced into a majority label.

If the required independent view is unavailable, set an explicit residual for
that row/cell and continue safe structural or silver work. Do not claim
consensus, gold, or a passed held-out gate from a single seat.

## Operation-specific rights

The rights ledger is keyed by source unit and operation. Track at least:
retention, deterministic local analysis, transmission to an external model or
service, derivation of annotations/examples, training use, publication, and
redistribution. Each capability has its own evidence, scope, and value
(`allowed`, `denied`, `unknown`, or `scope_bound`). Official or public
availability proves none of these capabilities by itself.

An unknown or denied capability blocks only the affected operation. Do not send
content where transmission is not allowed, do not derive where derivation is
not allowed, and do not publish or train where those capabilities are not
allowed. Keep the source unit, row/cell, and reason denominator-visible while
safe operations continue. No skill instruction is legal advice; preserve the
source evidence and escalate only the exact unresolved operation.

## VPS-first custody and capacity forecast

Protected source payloads, intermediate material, prompts/outputs containing
protected text, generated datasets, and data-producing worktrees stay on the
designated remote VPS. The Mac driver keeps only text-free receipts and control
metadata. A driver must not solve a capacity problem by copying the corpus to
the Mac or by creating an untracked second worktree.

Before any data-producing dispatch, write a text-free capacity receipt with these
measured fields:

```text
measured_at
total_bytes, used_bytes
free_bytes, free_inodes
source_input_bytes
persistent_index_and_cache_bytes
retained_output_bytes
active_worktree_bytes
active_worktree_growth_bytes
peak_staging_bytes
pending_output_bytes
recovery_copy_bytes
incremental_peak_bytes, incremental_peak_inodes
policy_reserve_bytes
policy_reserve_inodes
required_bytes, required_inodes
parallelism_cap
measurement_method
```

Treat `total_bytes`, `used_bytes`, and `free_bytes` as one measured filesystem
snapshot (`total_bytes = used_bytes + free_bytes`, within the measurement
method's rounding). Existing source inputs, indexes/caches, retained outputs,
and active worktrees are already resident in `used_bytes` and are reflected in
`free_bytes`; retain their individual fields for reconciliation, but do not add
them again to the launch requirement. In particular, do not double-count
retained bytes already included in used/free.

Compute only the new work's high-water forecast as:

```text
incremental_peak_bytes = active_worktree_growth_bytes + peak_staging_bytes
                        + pending_output_bytes + recovery_copy_bytes
required_bytes         = incremental_peak_bytes + policy_reserve_bytes
```

The launch inequalities are, equivalently:

```text
free_bytes  >= incremental_peak_bytes + policy_reserve_bytes
total_bytes >= used_bytes + incremental_peak_bytes + policy_reserve_bytes
```

In short: `free >= incremental peak + reserve`, or `total >= used +
incremental peak + reserve`.

and `free_inodes >= incremental_peak_inodes + policy_reserve_inodes`, with the
active operational reserve preserved. The reserve and parallelism cap come from
live capacity policy and measurement, not a hard-coded quota. If any term is
unknown, the forecast is not proven and scale work does not launch.

Do not add `retained_output_bytes`, `source_input_bytes`, or
`persistent_index_and_cache_bytes` to `incremental_peak_bytes` when those bytes
are already included in the measured `used_bytes`/`free_bytes` snapshot. If a
planned artifact is not yet resident, count it once as an incremental term.

Measure high-water usage during the 100-row pilot by stratum and operation.
For scale, extrapolate by homogeneous source/cell class and retain the largest
observed upper bound, including duplicate, rollback, and temporary-file costs;
do not multiply one convenient average across unlike sources. Re-measure after
each new persistent artifact or concurrency change. If capacity is insufficient,
reduce concurrency, finish/reclaim approved temporary outputs, or route to an
already-approved remote lane. Do not delete source evidence or weaken the floor.

## Split readiness gates

These are gate labels, not release states. Evaluate them in order and attach a
typed receipt for each one:

- `READY_TO_DRIVE` requires the V4 contract and validator to pass on **main and
  VPS**, verified VPS reachability, measured capacity for the 100-row pilot,
  the frozen public slot contract, and the complete functional role map.
- After `READY_TO_DRIVE`, the `A1/A2` custody-and-inventory prerequisite must
  pass: A1 proves VPS custody/capacity and A2 proves source inventory, admission,
  and rights by operation.
- `PRE_BUILDER` requires the admitted slice plus a sealed A3 held-out/source-
  family split and its access firewall.
- `PRE_SCALE` requires pilot high-water measurements, full-scale capacity
  evidence, and source-inventory reconciliation against the admitted slice.

If a gate is missing, dispatch its named prerequisite and keep the affected
rows/cells visible; a missing prerequisite is not a global block. Use
`BLOCKED_WITH_RESIDUALS` only when a named global stop condition remains after
the safe prerequisite work is dispatched.

The gate sequence is `READY_TO_DRIVE` → A1/A2 custody/inventory →
`PRE_BUILDER` → `PRE_SCALE`; do not skip a missing prerequisite or turn it into
a global block.

## Driver preflight

Preflight is gate-specific, not an all-at-once checklist. Evidence for a later
gate must not be required to enter an earlier gate, and each dispatch reevaluates
only the gate that it is about to cross.

`READY_TO_DRIVE` has exactly these five checks:

1. the V4 contract and validator pass on **main and VPS**;
2. VPS reachability is verified;
3. measured capacity satisfies the 100-row pilot high-water requirement;
4. the frozen public slot contract is bound to the canonical slot manifest;
5. the complete functional role map is present.

The `A1/A2` prerequisite is evaluated before `PRE_BUILDER`: A1 supplies the
VPS custody/capacity receipt, and A2 supplies the source inventory, admission,
and rights-by-operation receipt. Do not require A2 evidence to enter
`READY_TO_DRIVE`.

`PRE_BUILDER` is evaluated only immediately before builder dispatch. It requires
the admitted slice plus the sealed A3 heldout/source-family split and access
firewall. Do not require heldout evidence to enter `READY_TO_DRIVE`; heldout
evidence is a builder prerequisite, not a global preflight item.

`PRE_SCALE` is evaluated only before scale dispatch. It requires pilot
high-water measurements, full-scale capacity evidence, and source-inventory
reconciliation against the admitted slice. Do not pull these scale-only checks
back into `READY_TO_DRIVE` or `PRE_BUILDER`.

At every dispatch, independently recheck and receipt the live routing,
health/capacity signals, and exact code/skill head; a stale route or head never
silently satisfies a gate. Missing evidence is `unknown`, not permission to
guess. A missing gate dispatches its named prerequisite and keeps affected
rows/cells visible; it is not a global block. A global denominator drift, split
leak, Cycle007 contamination, protected-span mutation, or rights/provenance
corruption still stops the affected phase and requires a named disposition.

## Issue-stage ownership and execution

Use the native issue graph, not a recreated checklist. The stable functional
handoff for the open child stages is:

| Stage | Issue | Primary outcome | Functional lead |
| --- | --- | --- | --- |
| Pilot construction | #7430 | The smallest reproducible 100-slot source-derived pilot and residual map. | A10 pilot-review lead (accountable); A4-A8 producers separated. |
| Pilot validation | #7431 | Independent split, integrity, identity, and held-out validation with exact disposition. | A9 heldout/evaluation lead (accountable); independent A10 review. |
| Coverage-yield scale | #7432 | Add source-backed coverage without changing the frozen denominator or IDs. | A8 scale/admission-assembly lead (accountable); A1/A2/A4/A5/A7 producers. |
| Consumer certification | #7433 | Reproduction of eligible views and typed release receipt. | A11 silver-release lead (accountable); separate A9 reproducer and A10 reviewer. |

Each issue has exactly one accountable lead: #7430 is accountable to the A10
pilot-review lead, #7431 to the A9 heldout/evaluation lead, #7432 to the A8
scale/admission-assembly lead, and #7433 to the A11 silver-release lead.
Producers and reviewers named after the semicolon remain separate from that
accountability.

Before dispatch, freeze the issue packet's denominator slice, owned outputs,
input hashes, hidden boundary, operation rights, acceptance evidence, and
residual owner. Use `$drive-epic` for the generic routing card, worktree,
settling, exact-head cross-family review, merge, cleanup, and handoff mechanics.
Never let a waiting review or capacity check erase the next issue disposition.

## Completion and residual behavior

`SILVER` and `GOLD` describe row overlays, not epic release states. Use only
this V4 release vocabulary:

- `ARENA_SLICE_READY`: the frozen source-free slot slice, role map, and
  label-blind arena packet are ready; this is not a truth or training claim.
- `EVAL_ARTIFACT_READY`: the independent held-out partition, scorer, manifest,
  and integrity/reproduction artifact are sealed and ready for evaluation.
- `TRAINING_READY_SILVER`: deterministic source, rights-by-operation,
  provenance, split, schema, and structural checks admit a reproducible silver
  view. It does not require universal human and model agreement; hypotheses,
  proposals, votes, confidence, and agreement cannot independently admit silver.
- `TRAINING_READY_GOLD_SUBSET`: only the explicitly identified subset with
  source-qualified human adjudication, cited evidence, independent rights,
  split, lineage, view, and execution-authorization gates is eligible for a
  gold training view; all other rows remain silver or residual.
- `GOLD_UPGRADE_READY`: stable silver rows have a bounded, source-qualified
  later-adjudication path and append-only overlay plan; this state does not
  assert that a gold overlay has been granted.
- `BLOCKED_WITH_RESIDUALS`: a named global stop condition remains after safe
  prerequisite dispatch; typed residuals stay denominator-visible with an owner
  and next action. A missing lane-local gate uses its prerequisite dispatch,
  not this state.

Every residual record contains a stable row/cell or source-unit ID, stage,
reason code, owner role, next action, retryability, and latest evidence digest;
public receipts contain metadata, not source text. Typical reason codes include
`rights_unknown`, `rights_denied`, `source_incomplete`,
`evidence_insufficient`, `identity_ambiguous`, `independence_unavailable`,
`human_adjudication_missing`, `coverage_blocked`, `capacity_insufficient`,
`split_leakage`, and `validator_failure`.

Residual rows remain in the denominator and retain their stable IDs. Do not drop
them, relabel them as N/A without evidence, silently substitute another source,
or retry forever. A retry is allowed only when its reason is retryable and the
new attempt is recorded. Human absence is not a global blocker for silver;
missing source-qualified adjudication remains an exact gold residual. Close a
stage only when its receipt gives the counts, evidence, next owner, and typed
release state, with no unexplained remainder.

## Launch prompt

At the start of a driver session, apply this short binding prompt after loading
`$drive-epic` and this skill:

> Drive the V4 Ukrainian dataset epic under outcome SHA
> `78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20`.
> Treat public #7423 and private #622 as the paired control surfaces. Preserve
> the frozen 100-row denominator and all Ukrainian literary, dialectal,
> archaic/historical, contact-mixing, quotation/interference, and abstention
> distinctions. Assign functional roles, enforce leave-one-out/no-self-vote,
> keep model agreement quarantined from gold, and use append-only silver-to-gold
> overlays. Run the VPS custody/capacity forecast and operation-specific rights
> preflight before every data-producing phase. Query live routing before every
> dispatch or review. Keep every residual typed, denominator-visible, and owned;
> do not invent authority, shrink scope, or claim a stronger release state than
> the evidence proves.
