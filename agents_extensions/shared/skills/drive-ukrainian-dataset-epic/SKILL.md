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

## Row identity and release layers

Assign every pilot slot and every admitted row a deterministic, opaque stable ID
derived from the V4 version, source-unit identity, evidence/span locator, rule or
case key, and role. Never derive an ID from provider order, model output, arrival
time, file position, or a mutable sentence number. A source or case may have
multiple role-specific records, but their lineage must remain explicit.

Use append-only overlays:

- **Silver** is a reproducible, schema-valid, source-traceable row whose
  uncertainty and review state are explicit. It may be produced without a human
  decision when the deterministic source, operation rights, provenance, split,
  and structural checks pass. Human review is optional for silver and improves
  evidence; it is never implied by a model proposal.
- **Gold** is an overlay on the same stable row ID, not a rewrite of silver. It
  requires a source-qualified human adjudication tied to claim-appropriate cited
  evidence, an adjudication receipt, and independent rights, split, provenance,
  lineage, view, and execution-authorization gates. Gold fields are additive and
  auditable; the silver record remains recoverable.

Model proposals, votes, rationales, and unresolved decisions are separate from
both target layers. Exact agreement is recorded as
`MODEL_AGREEMENT_QUARANTINED_NOT_GOLD`; agreement, majority, confidence, or
attestation can never promote a row to gold. A silver row must not be called a
gold target or used to claim `DATASET_READY`.

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
free_bytes, free_inodes
source_input_bytes
persistent_index_and_cache_bytes
retained_output_bytes
active_worktree_bytes
peak_staging_bytes
pending_output_bytes
recovery_copy_bytes
policy_reserve_bytes
required_bytes, required_inodes
parallelism_cap
measurement_method
```

Compute the forecast as:

```text
persistent = source_input + indexes/caches + retained_outputs + worktrees
peak       = persistent + peak_staging + pending_output + recovery_copy
required   = peak + policy_reserve
```

The launch inequality is `free_bytes >= required_bytes` and
`free_inodes >= required_inodes`, with the active operational reserve preserved.
The reserve and parallelism cap come from live capacity policy and measurement,
not a hard-coded quota. If any term is unknown, the forecast is not proven and
scale work does not launch.

Measure high-water usage during the 100-row pilot by stratum and operation.
For scale, extrapolate by homogeneous source/cell class and retain the largest
observed upper bound, including duplicate, rollback, and temporary-file costs;
do not multiply one convenient average across unlike sources. Re-measure after
each new persistent artifact or concurrency change. If capacity is insufficient,
reduce concurrency, finish/reclaim approved temporary outputs, or route to an
already-approved remote lane. Do not delete source evidence or weaken the floor.

## Driver preflight

The driver may start the next phase only after attaching evidence for each item:

1. Both control issues resolve to the exact V4 outcome SHA.
2. The 100 row slots, strata, stable-ID rule, and source/case packet are frozen.
3. The source manifest is unit-complete and every unit has a disposition.
4. The operation-specific rights ledger is present for the operation being run.
5. The split/held-out firewall, leave-one-out matrix, and Cycle007 deny-list are
   sealed before case derivation.
6. Functional role owners, visibility boundaries, and substitution records are
   named; no-self-vote is mechanically checkable.
7. The VPS capacity receipt satisfies the launch inequality and preserves reserve.
8. The live routing/health/capacity signals and exact code/skill gate are fresh.

Missing evidence is `unknown`, not permission to guess. A lane-local source,
rights, evidence, format, capacity, or route problem keeps its affected rows or
cells visible while disjoint safe work proceeds. A global denominator drift,
split leak, Cycle007 contamination, protected-span mutation, or
rights/provenance corruption stops the affected phase and requires a named
disposition.

## Issue-stage ownership and execution

Use the native issue graph, not a recreated checklist. The stable functional
handoff for the open child stages is:

| Stage | Issue | Primary outcome | Functional lead |
| --- | --- | --- | --- |
| Pilot construction | #7430 | The smallest reproducible 100-slot source-derived pilot and residual map. | Candidate builder, with identity/dissent, custody, rights, and capacity stewards. |
| Pilot validation | #7431 | Independent split, integrity, identity, and held-out validation with exact disposition. | Held-out evaluator and consumer reproducer. |
| Coverage-yield scale | #7432 | Add source-backed coverage without changing the frozen denominator or IDs. | Driver plus source/capacity stewards and bounded builder lanes. |
| Consumer certification | #7433 | Reproduction of eligible views and typed release receipt. | Consumer reproducer, rights steward, and driver. |

Before dispatch, freeze the issue packet's denominator slice, owned outputs,
input hashes, hidden boundary, operation rights, acceptance evidence, and
residual owner. Use `$drive-epic` for the generic routing card, worktree,
settling, exact-head cross-family review, merge, cleanup, and handoff mechanics.
Never let a waiting review or capacity check erase the next issue disposition.

## Completion and residual behavior

`SILVER` and `GOLD` describe row overlays, not epic release states. Use only this
release vocabulary:

- `INVENTORIED`: source universe is disposition-complete; blocked and unresolved
  counts remain explicit.
- `PILOT_VALIDATED`: the source-qualified pilot, split firewall, and held-out
  protection/integrity gates pass. This does not mean the full dataset is ready.
- `DATASET_PARTIAL`: reproducible rows exist, but a required source/cell, right,
  adjudication, or integrity condition remains unresolved or blocked.
- `DATASET_READY`: the frozen required denominator is covered with no unresolved
  or blocked required cells, no unknown required rights, no exclusion gaming,
  every target is human-adjudicated and source-traceable, every view is
  split-safe/reproducible, and consumer reproduction passes.
- `BLOCKED`: a named global stop condition prevents safe progress.
- `TRAINING_VALIDATED`: outside this epic and never a completion claim here.

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
