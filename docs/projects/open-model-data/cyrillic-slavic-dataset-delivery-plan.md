# Cyrillic-Slavic Ukrainian dataset delivery plan — V4

## Controlling contract and history

This is the operational control packet for the Ukrainian dataset-delivery epic.
Its controlling outcome is SHA-256
`78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20`.
The private coordination board is [#622](https://github.com/learn-ukrainian/learn-ukrainian-infra-private/issues/622);
the public delivery epic is [#7423](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7423).

V2 and V3 are retained as historical predecessor evidence only. They do not set
the current scope, release policy, rights disposition, pilot denominator, or
driver route. A conflicting predecessor instruction is superseded by this V4
packet and the hash-bound private board decision.

## Product outcome

Build a Ukrainian language-quality dataset and held-out evaluation harness that
helps language models recognize, preserve, and produce Ukrainian accurately.
It does not attempt to teach a complete vernacular, reconstruct a book, or turn
protected varieties into modern-standard errors.

The seven product scopes are:

1. modern Standard Ukrainian control: correct production and source-backed correction;
2. literary Ukrainian;
3. living Ukrainian dialect and regional varieties;
4. archaic, historical, and bookish Ukrainian;
5. Surzhyk and Ukrainian–Russian mixing;
6. Russian quotation and interference in Ukrainian context; and
7. evidence-insufficient or unsafe cases, represented by abstention.

The first scope has two separate pilot strata because correct production and
correction have different behavior. The remaining six scopes have one stratum
each, so the 100-slot pilot has eight strata. Dedicated Belarusian, Bulgarian,
Macedonian, Serbian, and Montenegrin lanes are removed. Modern Rusyn is
protected and out of scope: do not silently map it to Ukrainian, Russian, or a
historical Ukrainian stage.

## Release train and data boundary

The first deliverable is **silver**: stable row IDs, provenance/rights metadata,
labels or abstentions, validations, and evaluation eligibility as separately
gated properties. Models provide hypotheses only. Model agreement does not admit
silver and never creates gold. A later, versioned overlay may upgrade individual
stable IDs to gold after its own review and rights gates. No re-numbering or
rebuilding of the silver corpus is implied by that upgrade.

The private, lawfully obtained corpus is used on the VPS for custody, bounded
analysis, and source-family assignment. Public/exportable rows must be
independently authored and non-reconstructive unless the exact source operation
is cleared. Retention, local analysis, provider transmission, derivation,
training, publication, and redistribution are independent operations.

An unresolved operation blocks only that source-operation lane. It remains
visible in its lane receipt and cannot silently shrink the denominator. It is a
global stop only if it prevents every feasible source family for a frozen required
stratum.

## Custody, capacity, and privacy gates

All corpus handling, candidate construction, validation runs, and driver
worktrees are VPS-first. The Mac is coordination-only and must not receive a
corpus copy or long-lived dispatch worktree. Before each lane starts, A1 records
the current free space, its forecast, a cleanup budget, the hard floor, and the
data/derivative locations. A lane may start only when its forecast plus cleanup
reserve stays above that floor; failure is lane-local unless it makes every
remaining required lane infeasible.

The public pilot-slot manifest is deliberately expression-free. It has no source
text, source locator, source identity, document identity, provider prompt/output,
label, correction, or held-out membership. Those sealed details are created only
by A2/A3 in private custody after the gates below are satisfied.

## Frozen pilot entry contract

`data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json`
defines 100 stable slot IDs by deterministic series:

| Stratum | Slots |
| --- | ---: |
| standard-correct | 15 |
| correction | 15 |
| literary | 15 |
| dialect-regional | 15 |
| archaic-historical | 15 |
| mixing | 10 |
| quotation-interference | 10 |
| abstention | 5 |

Before any builder receives an item, A3 must create a separate sealed commitment
that assigns source families and nonzero held-out groups without exposing held-out
membership to builders. Slot-to-source assignment is an A2/A3 private artifact,
not a guess in the public manifest. A construction change after held-out exposure
invalidates the affected evaluation version.

## Functional roles and handoffs

The driver assigns an accountable lead to every role; model/provider choice is a
runtime routing decision and is never embedded in this plan. The role map is
fixed for this epic:

| ID | Owner role | Produces | May not do |
| --- | --- | --- | --- |
| A0 | scope and accountable lead | scope/denominator ledger and route | bypass gates or self-review |
| A1 | custody steward | VPS inventory, capacity, cleanup/floor receipt | expose corpus or change scope |
| A2 | source inventory and admission steward | source-family and operation decision | assign held-out membership alone |
| A3 | held-out steward | sealed source-family and held-out commitment | reveal held-out identities to builders |
| A4 | deterministic extraction steward | reproducible source-free extraction packet | improvise source assignment |
| A5 | evidence-enrichment steward | provenance/evidence joins and uncertainty flags | modernize protected material |
| A6 | safe-arena steward | blind packet, strict parser, non-self vote receipt | vote for its own output |
| A7 | original-row factory steward | independently authored candidate rows | see held-out membership or create gold |
| A8 | admission and assembly steward | validated silver assembly receipt | waive contract/privacy gates |
| A9 | evaluation-package steward | frozen held-out evaluation package | alter construction after exposure |
| A10 | pilot-review steward | pilot review disposition and residuals | hide unresolved required slots |
| A11 | training-ready release steward | permitted silver consumer release | waive rights/evaluation gates |
| A12 | later-gold-overlay steward | separately versioned gold-upgrade overlay | infer gold from model agreement |
| A13 | cleanup and recovery steward | cleanup, rollback, and next-lane receipt | hide a stopped denominator |

Independent cross-family review is a gate on the exact implementation head; it
is not A12 and cannot be replaced by the authoring family.

## Arena and evidence rules

Every arena participant receives the same blind packet and emits one strict,
schema-validated response. A participant cannot vote for its own output.
Invalid output receives one format-only retry; a persistent failure is recorded,
then a bounded substitute or abstention is used without changing the denominator.
The coordinator records routes, families, attempts, exposure, and hashes in
private receipts. Models provide hypotheses only: agreement does not admit
silver and does not create gold. Humans are optional for silver and may later
support source-qualified gold overlays or hard disputes.

## Completion vocabulary and stop policy

The only V4 completion vocabulary is:

- `ARENA_SLICE_READY`
- `EVAL_ARTIFACT_READY`
- `TRAINING_READY_SILVER`
- `TRAINING_READY_GOLD_SUBSET`
- `GOLD_UPGRADE_READY`
- `BLOCKED_WITH_RESIDUALS`

`BLOCKED_WITH_RESIDUALS` settles a bounded packet and records its unresolved
slots, denominator, cause, owner, and next route. It is not successful pilot
completion. An unresolved required slot cannot satisfy `EVAL_ARTIFACT_READY` or
`TRAINING_READY_SILVER`; those successful states require every required slot in
the frozen denominator to have passed its applicable admission, privacy, rights,
and evaluation gates. `TRAINING_READY_GOLD_SUBSET` is limited to rows actually
promoted by a later gold overlay. `GOLD_UPGRADE_READY` means an overlay may be
reviewed, not that gold already exists.

The driver obtains gates in order:

1. A0 binds this V4 hash, #622, #7423, denominator, non-goals, roles, and held-out policy.
2. A1 proves VPS custody/capacity above the hard floor for the next bounded lane.
3. A2 admits a feasible source family for that lane and requested operation.
4. A3 seals the source-family/held-out commitment before A4–A7 begin.
5. A4/A5 create deterministic, evidence-enriched packets; A6/A7 construct safely.
6. A8 admits and assembles only rows that pass all silver gates.
7. A9 packages evaluation; A10 reviews the pilot; A11 releases only a training-ready silver view.
8. A12 handles later gold overlays; independent cross-family review gates every exact implementation head; A13 closes or recovers the lane.

Global stop: no feasible path remains for a frozen required stratum, VPS custody
cannot remain above its floor, a privacy firewall is breached, or a required
contract/evaluation gate is invalid. Lane-local stop: one source operation,
provider route, parser attempt, candidate, or source family fails while another
frozen path remains. A stopped lane produces `BLOCKED_WITH_RESIDUALS` and
preserves its slots; it never disappears by denominator reduction.

## Completion terms

`READY_TO_DRIVE` is an orchestration state, not a construction state. It requires
the V4 binding, the validator on `main`, live VPS reachability and capacity for
the pilot, this frozen slot contract, and the A0–A13 role map. It does not require
source inventory, source admission, or sealed held-out membership.

`PRE_BUILDER` begins after `READY_TO_DRIVE`: A1/A2 produce the custody and
source-admission receipts, then A3 seals the source-family and held-out commitment
before any A4–A7 builder work begins.

The pilot succeeds only when all required slots satisfy the frozen denominator and gates, the held-out
evaluation is frozen as `EVAL_ARTIFACT_READY`, and the permitted consumer view is
`TRAINING_READY_SILVER`. Any unresolved required slot leaves the pilot in
`BLOCKED_WITH_RESIDUALS`, with its exact residual and next owner reported.
