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
each, so the 100-slot pilot has eight strata.

Dedicated Belarusian, Bulgarian, Macedonian, Serbian, and Montenegrin lanes are
removed. They are not substitutes for Ukrainian evidence. Modern Rusyn is
protected and out of scope: do not silently map it to Ukrainian, Russian, or a
historical Ukrainian stage.

## Release train and data boundary

The first deliverable is **silver**: stable row IDs, provenance/rights metadata,
labels or abstentions, validations, and evaluation eligibility as separately
gated properties. Model agreement can support a silver observation; it never
creates gold. A later, versioned overlay may upgrade individual stable IDs to
gold after its own review and rights gates. No re-numbering or rebuilding of the
silver corpus is implied by that upgrade.

The private, lawfully obtained corpus is used on the VPS for custody, bounded
analysis, and source-family assignment. Public/exportable rows must be
independently authored and non-reconstructive unless the exact source operation
is cleared. Source availability is not a project-wide rights assertion:
retention, local analysis, provider transmission, derivation, training,
publication, and redistribution are independent operations.

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
runtime routing decision and is never embedded in this plan.

| ID | Owner role | Produces | May not do |
| --- | --- | --- | --- |
| A0 | dataset-epic driver | topology, ledger, dispatch, integration receipt | self-review or bypass gates |
| A1 | VPS custody/capacity steward | inventory, forecast, cleanup/floor receipt | expose corpus or change scope |
| A2 | source-admission steward | operation-specific source-family decisions | assign held-out membership alone |
| A3 | split/evaluation firewall steward | sealed source-family and held-out commitment | reveal held-out identities to builders |
| A4 | Ukrainian taxonomy lead | scope/protection taxonomy and abstention rules | modernize protected material |
| A5 | candidate builder | source-free candidate rows and provenance links | create gold or see held-out membership |
| A6 | arena coordinator | blind packets, strict parsing, non-self voting receipt | vote for its own output |
| A7 | dissent/dispute critic | bounded dispute disposition or abstention | erase disagreements |
| A8 | contract validator | schema, quota, lineage, and privacy validation | relabel a failed row |
| A9 | silver release steward | versioned silver manifest and release receipt | claim gold from model agreement |
| A10 | held-out evaluation steward | frozen evaluation report | alter construction after exposure |
| A11 | consumer-certification steward | training/consumer compatibility receipt | waive rights or evaluation gates |
| A12 | independent cross-family reviewer | exact-head review verdict | approve its own implementation |
| A13 | closeout/recovery steward | residual, rollback, and next-lane receipt | hide a stopped denominator |

## Arena and evidence rules

Every arena participant receives the same blind packet and emits one strict,
schema-validated response. A participant cannot vote for its own output.
Invalid output receives one format-only retry; a persistent failure is recorded,
then a bounded substitute or abstention is used without changing the denominator.
The coordinator records routes, families, attempts, exposure, and hashes in
private receipts. No model consensus, however strong, is gold.

Humans are optional for silver. They are useful later for source-qualified gold
overlays or hard disputes, but their absence cannot stop ordinary silver work.

## Driver gates and stop policy

The driver must obtain these in order:

1. A0 binds this V4 hash, #622, #7423, denominator, non-goals, roles, and held-out policy.
2. A1 proves VPS custody/capacity above the hard floor for the next bounded lane.
3. A2 admits a feasible source family for that lane and requested operation.
4. A3 seals the source-family/held-out commitment before builders start.
5. A4–A8 construct and validate silver candidates without source or held-out leakage.
6. A6/A7 settle arena disagreements through non-self voting, substitution, or abstention.
7. A9 freezes the silver release; A10 evaluates it; A11 certifies the allowed consumer view.
8. A12 reviews the exact implementation head independently; A13 publishes residuals and routes the next lane.

Global stop: no feasible path remains for a frozen required stratum, VPS custody
cannot remain above its floor, a privacy firewall is breached, or a required
contract/evaluation gate is invalid. Lane-local stop: one source operation,
provider route, parser attempt, candidate, or source family fails while another
frozen path remains. A stopped lane produces an explicit receipt and preserves
its slots; it never disappears by denominator reduction.

## Completion terms

The epic is ready to drive when the V4 binding, live VPS custody/capacity receipt,
this pilot contract, and sealed A3 commitment are present. The pilot completes
only when all 100 stable slots have a permitted terminal state (silver candidate,
validated abstention, or explicit lane-local residual), exact quotas remain
visible, the held-out evaluation is frozen, and the consumer view has passed its
own rights and certification gates. Final closure reports the achieved count,
denominator, residuals, and next owner.
